#!/usr/bin/env python3
"""Render src/*.list into client-specific rule files and reject unsafe rules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}
BROAD = {
    "google.com",
    "googleapis.com",
    "gstatic.com",
    "googleusercontent.com",
    "clients.google.com",
    "clients6.google.com",
    "apis.google.com",
    "google",
    "goog",
}


def parse(path: Path) -> list[tuple[str, str | None]]:
    rules: list[tuple[str, str]] = []
    items: list[tuple[str, str | None]] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            items.append(("comment", line))
            continue
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 2 or parts[0] not in TYPES or not parts[1]:
            raise SystemExit(f"{path}:{lineno}: 只允许 DOMAIN 或 DOMAIN-SUFFIX，且不能带策略: {raw}")
        kind, value = parts
        if any(char in value for char in " /\\:*") or value.startswith(".") or ".." in value:
            raise SystemExit(f"{path}:{lineno}: 域名不合法: {value}")
        labels = value.split(".")
        if len(labels) < 2 or any(not label or not label.replace("-", "").isalnum() for label in labels):
            raise SystemExit(f"{path}:{lineno}: 域名不合法: {value}")
        if value in BROAD:
            raise SystemExit(f"{path}:{lineno}: 拒绝过宽规则: {value}")
        rules.append((kind, value))
        items.append(("rule", f"{kind},{value}"))
    seen: set[str] = set()
    for kind, value in rules:
        key = f"{kind},{value}"
        if key in seen:
            raise SystemExit(f"{path}: 重复规则: {key}")
        seen.add(key)
        if kind == "DOMAIN-SUFFIX":
            for earlier_kind, earlier in rules:
                if earlier != value and value.endswith("." + earlier) and earlier_kind == "DOMAIN-SUFFIX":
                    raise SystemExit(f"{path}: {value} 已被更宽的 DOMAIN-SUFFIX,{earlier} 覆盖")
    return items


def render_loon(name: str, items: list[tuple[str, str | None]]) -> str:
    body = "\n".join(text for _, text in items if text is not None)
    return (
        "# 由 src/"
        + name
        + " 生成，不要直接改这个文件。\n"
        + "# 每行不写策略。策略写在 Loon 的 [Remote Rule] 订阅行上。\n"
        + body
        + "\n"
    )


def render_clash(name: str, items: list[tuple[str, str | None]]) -> str:
    lines = [
        "# 由 src/" + name + " 生成，不要直接改这个文件。",
        "# Clash Meta rule-provider: behavior: classical, format: yaml",
        "payload:",
    ]
    for kind, text in items:
        if kind == "comment" and text:
            lines.append("  " + text)
        elif kind == "rule" and text:
            lines.append(f"  - {text}")
    return "\n".join(lines) + "\n"


def main() -> None:
    sources = sorted(SRC.glob("*.list"))
    if not sources:
        raise SystemExit("src 下没有 .list")
    for source in sources:
        items = parse(source)
        rule_count = sum(1 for kind, _ in items if kind == "rule")
        (ROOT / "loon").mkdir(exist_ok=True)
        (ROOT / "clash").mkdir(exist_ok=True)
        (ROOT / "loon" / source.name).write_text(render_loon(source.name, items), encoding="utf-8")
        (ROOT / "clash" / source.with_suffix(".yaml").name).write_text(
            render_clash(source.name, items), encoding="utf-8"
        )
        print(f"{source.name}: {rule_count} 条")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
