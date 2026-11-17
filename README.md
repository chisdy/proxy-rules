# proxy-rules

按客户端分开的规则库。同一份名单放在 `src/`，再生成给各客户端直接订阅的文件。

| 目录 | 谁来用 | 当前文件 |
|---|---|---|
| `src/` | 维护时改这里 | `google-gemini.list` |
| `loon/` | Loon 远程规则 | `google-gemini.list` |
| `clash/` | Clash Meta 规则集 | `google-gemini.yaml` |

改完 `src/` 后运行：

```bash
python3 scripts/render.py
```

脚本会检查语法、重复、被更宽后缀盖住的条目，并拒绝 `google.com`、`googleapis.com`、`gstatic.com`、`apis.google.com`、`clients6.google.com` 这种共享后缀。

## Google AI Studio 与 Gemini

`src/google-gemini.list` 只覆盖这两个产品自己的主机，共 26 条。包括：

- 网站：`aistudio.google.com`、`gemini.google.com`、`gemini.app.google`，以及旧名 `makersuite.google.com`、`bard.google.com`、`ai.studio`
- AI Studio 接口：`alkalimakersuite-pa.clients6.google.com`、`webchannel-alkalimakersuite-pa.clients6.google.com`、`alkalimakersuiteapplets.pa.clients6.google.com`、`aisandbox-pa.googleapis.com`
- Gemini API：`generativelanguage.googleapis.com`
- Gemini 网页接口和 `gemini.gstatic.com`
- Gmail / 文档 / 云端硬盘里的 Gemini 侧边栏
- `deepmind.com`、`deepmind.google`

登录用的 `accounts.google.com`、全站静态资源 `www.gstatic.com`、通用的 `apis.google.com` 不在这里。它们也服务于搜索、邮箱和地图。NotebookLM、Jules、Colab、Antigravity、Gemini Code Assist 也不在这套规则里。

主机名来自 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) 的 `data/google-deepmind`（MIT），只取了 AI Studio 和 Gemini 相关段落。版权声明见 `NOTICE`。2026-11-17 用 `1.1.1.1` / `8.8.8.8` 逐条核对过，这些主机都有真实解析记录。

## Loon

在 `[Remote Rule]` 增加一行。策略名换成你自己的策略组；和现有配置一样走默认代理时用 `Available`。

```ini
https://raw.githubusercontent.com/chisdy/proxy-rules/main/loon/google-gemini.list, policy=Available, tag=Gemini, enabled=true
```

在 Loon 界面里添加时，URL 框只填裸地址，不要把 `, policy=...` 一起贴进去。列表里的每一行不写策略。

`raw.githubusercontent.com` 拉不到时，只换前缀：

```text
https://cdn.jsdelivr.net/gh/chisdy/proxy-rules@main/loon/google-gemini.list
```

## Clash Meta

```yaml
rule-providers:
  google-gemini:
    type: http
    behavior: classical
    format: yaml
    url: https://raw.githubusercontent.com/chisdy/proxy-rules/main/clash/google-gemini.yaml
    path: ./ruleset/google-gemini.yaml
    interval: 86400

rules:
  - RULE-SET,google-gemini,PROXY
```

`PROXY` 换成你的策略组名。这条要写在兜底规则 `MATCH` 之前。
