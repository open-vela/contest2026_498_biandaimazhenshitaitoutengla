# logs/yu-baixi — AI Coding 原始会话

本目录保存本作品开发过程中使用的 AI 编程工具的**原始会话记录**。

## 为什么是原始格式

本作品的开发全程使用 Codex（非 `claude-code` / `opencode` 等组委会已适配的工具）。
实测大赛日志归集工具对 Codex rollout 的导出结果为 0 事件（命令成功退出、无输出、无报错），
无法产出符合 `logs/<login>/<date>/<tool>__<sid>.jsonl` 规范的会话文件。

经与主办方确认：一直使用其他 AI 工具、没有符合要求的日志时不必强行转换，
**直接提交原始对话即可**。因此本目录按工具的原始格式提交，不做二次加工。

## 目录结构

```text
logs/yu-baixi/
├── README.md
├── manifest.json
└── raw/
    └── codex/
        ├── 09-14/  rollout-<时间戳>-<会话 id>.jsonl
        ├── 09-15/
        ├── ...
        └── 09-19/
```

- 共 41 个会话文件，按会话开始日期分目录，文件名沿用 Codex 原生命名。
- `manifest.json` 为 41 个会话的清单，字段与组委会 `manifest.json` 一致（`session_id` / `tool` / `started_at` / `last_event_at` / `event_count` / `file_path` / `collection_mode` / `health`），其中 `collection_mode` 取 `raw`、`file_path` 指向本目录下的原始会话文件。
- 每个文件为 JSONL，每行一个事件（`session_meta` / `event_msg` / `response_item` 等）。
- 覆盖范围：openvela 原型、ROS 2 小车控制、四车编队、现场调试、发布整理。

## 提交前的脱敏

原始会话里含有现场调试时用到的凭据，入库前已做两处替换：

| 内容 | 出现次数 | 替换为 |
|---|---:|---|
| 小车 SSH 登录口令 | 2401 | `[REDACTED-PASSWORD]` |
| 私钥内容片段 | 12 | `[REDACTED-PRIVATE-KEY]` |

替换只针对上述两类字符串，会话其余内容（工具调用、命令、输出、思考过程）保持原样。
替换后每个文件逐行 JSON 校验通过。

> 与 `docs/SUBMISSION.md` 中"本仓不包含 SSH 私钥、登录口令"的声明一致。