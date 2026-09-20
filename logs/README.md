# logs/ — AI Coding 日志目录

存放你在开发中与 AI 工具的对话日志，和作品代码一并提交。

> 本仓 `logs/` 下的会话日志由大赛日志归集工具在 openvela 工作区内自动写出，不手工编辑。

## 目录结构

```text
logs/
└── <github_login>/              # 你的 GitHub 用户名，一人一目录
    ├── manifest.json            # 会话清单
    └── <date>/                  # 日期 YYYY-MM-DD
        └── <tool>__<sid>.jsonl  # 一个会话一个文件（工具名与 session id 用 __ 连接）
```

- `<tool>`：`claude-code` / `opencode` / `codex` / `kiro`
- 每个 `.jsonl` 每行一个事件，由组委会提供的日志归集工具导出，**只提交 JSONL 本身**。

导出与提交的完整步骤、字段定义见[《AI Coding 日志归集与提交手册》](https://github.com/open-vela/docs/blob/dev-ai-contest-2026/zh-cn/contest_2026/ai_coding_log_guide.md)。

---

## 本仓的实际情况（队伍 contest2026_498）

上面是组委会提供的默认结构。本作品全程使用 **Codex** 开发：

- 大赛日志归集工具实测对 Codex rollout 导出为 **0 事件**（命令成功退出、无输出、无报错），
  无法产出 `<tool>__<sid>.jsonl` 规范文件；
- 经与主办方确认，一直使用其他 AI 工具、没有符合要求的日志时不必强行转换，
  **直接提交原始对话即可**。

因此本仓改为提交 Codex 的原始会话记录，位置：

```text
logs/yu-baixi/
├── README.md
├── manifest.json                                       # 41 个会话清单（字段同官方 manifest.json）
└── raw/codex/<MM-DD>/rollout-<时间戳>-<会话 id>.jsonl   # 41 个会话
```

原始会话中现场调试用到的 SSH 口令与私钥片段已在入库前脱敏，
详见 `logs/yu-baixi/README.md`。