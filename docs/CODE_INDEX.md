# 代码索引

仓库根目录为参赛专属仓 `contest2026_498_biandaimazhenshitaitoutengla`，
作品代码统一放在 `app/velamecanum/`，由 manifest 映射到 openvela 工作树的
`packages/demos/contest2026_498_velamecanum`。

## openvela 端

- `openvela/ai_agent/src/tools/tool_formation.c`、`tool_formation.h`：`formation_control` 工具实现。
- `openvela/ai_agent/src/tools/tool_registry.c`：工具注册。
- `openvela/ai_agent/Kconfig`、`CMakeLists.txt`、`defconfig`：组件开关与源文件清单。
- `openvela/generated/formation.config`：板级配置片段。
- `skills/formation-control.md`：ai_agent 自定义 Skill。
- `velamecanum_main.c`：openvela 端应用入口（能力查询与使用说明）。

## 本地验证环境

- `openvela/formation_lab/`：编队仿真、CLI 与 HTTP 服务（`python3 -m formation_lab.server`）。
- `openvela/ros2_ws/src/mentorpi_formation_bringup/`：车端建图、定位与运动测试包。
- `openvela/deploy/`：车端 systemd 服务与部署脚本。
- `openvela/robot-runtime/`：2026-09-20 从四台实车抓取的部署快照（容器 `formation_lab` 运行时、`config/mentorpi.json`、主机 `scripts/`、systemd 单元、`shared/` 运维工具）。用于版本一致性核验，详见该目录 `README.md`。
- `openvela/history/formation-dev-prototype/`：早期原型留档（`formation_lab/tests/`、`ros2_ws` 测试与 `ARCHITECTURE.md`），仅作开发过程追溯，不是当前发布路径。

## 当前发布包

目录：`outputs/formation-kit`

这里保存正式运行入口、当前 planner、车端 agent、fleet endpoint、自动定位代码、
地图资料、回归测试和发布包工具。后续功能修改以此目录为准。

## 部署与诊断

目录：`work`

- `deploy_*.py`：车端部署与版本更新。
- `audit_*.py`、`inspect_*.py`、`verify_*.py`：服务、进程、版本和网络核验。
- `count_udp_*.py`、`run_udp_attribution.py`：UDP 数据量分析。
- `fetch_*.py`、`gather_robot_data.py`：读取车端配置和资料。
- `agent-stop-fix/`：systemd 停止流程文件。
- `agent-network-audit/`：部署与核验记录。
- `audit_after_teammate/`：四车源码、DDS 配置和检查结果。
- `control_sources/`：基础控制代码资料。
- `robot_data/`：地图、位姿和激光扫描资料。
- `keys/`：车端固定主机密钥的存放位置说明（私钥不入库）。
- `.venv/`、`formation-venv/`：本机 Python 环境（不入库）。

## 常用命令

在仓库根目录执行：

运行全部本地检查：

```powershell
& "app/velamecanum/outputs/formation-kit/test_local.cmd"
```

运行四车只读预检：

```powershell
& "app/velamecanum/outputs/formation-kit/run_formation.cmd" square --spacing 0.5 --check-only
```

运行正式方阵任务：

```powershell
& "app/velamecanum/outputs/formation-kit/run_formation.cmd" square --spacing 0.5
```

运行本地同步运动模式的四车预检：

```powershell
& "app/velamecanum/outputs/formation-kit/run_formation.cmd" square --spacing 0.5 --motion-mode synchronized --check-only
```

同步运动入口：

```powershell
& "app/velamecanum/outputs/formation-kit/run_synchronized_formation.cmd" square --spacing 0.5
```