# 提交说明

- 目标仓库：`contest2026_498_biandaimazhenshitaitoutengla`，分支 `dev-ai-contest-2026`。
- 作品代码在 `app/velamecanum/`，经仓库 manifest
  （`contest2026_498_biandaimazhenshitaitoutengla.xml`）映射到 openvela 工作树的
  `packages/demos/contest2026_498_velamecanum`。
- AI Coding 日志在 `logs/yu-baixi/`：本作品全程使用 Codex，日志归集工具对 Codex rollout 导出为 0 事件，经主办方确认后改为提交原始会话（`manifest.json` + `raw/codex/<MM-DD>/rollout-*.jsonl`），入库前已完成口令与私钥片段脱敏。
- 组委会提供的 `.github/` 与 `openvela.xml` 保留；示例骨架（`app/hello_app/`、`quickapp/hello_quickapp/`、`board/contest_board/`）与示例日志（`logs/your-github-login/`）已删除，`contest2026_498_biandaimazhenshitaitoutengla.xml` 中的 linkfile 已改为 `app/velamecanum`。

## 可编译部分

`app/velamecanum/` 下的 `Makefile`、`Make.defs`、`Kconfig`、`CMakeLists.txt`、
`velamecanum_main.c` 构成 openvela 端应用骨架，Kconfig 选项为
`LVX_USE_DEMO_CONTEST2026_498_VELAMECANUM`（`default n`，需在 `menuconfig` 中开启）。

`formation_control` 工具属于公共仓 `packages/ai_agent` 的改动，
本仓 `openvela/ai_agent/` 保存对应的源文件与开关，按大赛流程以独立 PR 提交到
`packages_ai_agent` 的 `dev-ai-contest-2026` 分支。

## 未包含的内容

本仓不包含 SSH 私钥、登录口令、本机 Python 环境、缓存文件、完整 openvela
公共源码与重复的外部参考仓库。车端连接凭据在运行现场由操作者输入。