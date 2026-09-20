# app/velamecanum（应用形态）

映射到 openvela `packages/demos/contest2026_498_velamecanum`
（见仓库根目录的 `contest2026_498_biandaimazhenshitaitoutengla.xml`）。

## 目录

- `Makefile` / `Make.defs` / `Kconfig` / `CMakeLists.txt` / `velamecanum_main.c`
  —— openvela 端应用入口骨架，Kconfig 选项为
  `LVX_USE_DEMO_CONTEST2026_498_VELAMECANUM`（`default n`，需在 `menuconfig` 中开启）。
- `skills/` —— 本作品的 ai_agent 自定义 Skill（Markdown）。
- `openvela/` —— openvela 端资料：`ai_agent` 的 `formation_control` 工具源码、
  `formation_lab` 本地验证环境、`ros2_ws` 车端建图与定位包、`deploy/` 车端部署文件、
  `generated/formation.config` 板级配置片段。
- `outputs/formation-kit/` —— 当前四车任务控制包：正式运行入口、编队规划、
  车端路线跟踪、地图资料、回归测试与现场任务记录。
- `work/` —— 部署、诊断、定位检查、网络核验与验收工具。

根目录 `README.md` 提供完整运行步骤与验收数据。