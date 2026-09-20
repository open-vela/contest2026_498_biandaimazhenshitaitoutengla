# VelaMecanum——语音导演式多车编队交互系统

> 2026 首届 openvela AI 硬件开发者大赛 · 队伍 `contest2026_498` · 赛道：AI 硬件产品创新

## 一、作品简介

VelaMecanum 是面向四台 MentorPi M1 麦克纳姆轮小车的 openvela AI 硬件控制作品。系统包含 openvela 端的 `formation_control` 工具、本机任务控制程序、ROS 2 车端代理、定位与地图处理、编队规划、轨迹跟踪、安全许可、通信中断停止、仿真测试和现场验收记录。

作品支持方阵、横排、三角形、圆形与菱形队形，支持同步运动、顺序调整、闭合路线、共同朝向控制与队形恢复。现场任务已经完成方阵前进、转弯和单车脱离后的队形恢复验收。

## 二、选题方向

**AI 硬件产品创新**。作品基于 openvela + ai_agent，把任务级自然语言指令变成四台真实移动硬件的协同动作：openvela 端由 ai_agent 选择技能并调用 `formation_control` 工具，本机控制程序完成任务检查、路线规划与安全许可，四台小车分别完成分布式路线跟踪与安全保护。

## 三、应用场景

**用户故事**：实验室或展厅里负责四台编队小车的人，希望用一句话完成任务编排，而不是手写脚本、逐台改参数。

- 场景一：演示前说一句"摆成方阵，间距半米，前进到场地中间再转个弯"，Agent 选择 `formation-control` 技能，检查场地与安全边界后下发任务，四车同步完成动作。
- 场景二：演示途中一台小车被人为挪走，系统检测到偏差后由其余三车配合完成队形恢复，并向操作者主动汇报误差。
- 场景三：每次任务结束后不需要追问，直接得到本次任务的位置误差、朝向误差和最小车间距离。

## 四、功能清单

- 四车方阵、横排、三角形、圆形和菱形目标位置规划。
- 四车同步运动与顺序位置调整。
- 方阵保持、直线前进、90° 转弯和转弯后的共同朝向控制。
- 根据当前地图检查路线、场地边界与障碍物（A* + 地图线段安全判定）。
- 车间距离保护，最小允许距离为 0.30 m。
- 雷达路线保护、定位状态检查、通信中断停止和控制权超时释放。
- openvela 端 `formation_control` 工具：`start` / `status` / `stop` / `reset` / `capabilities`，带参数合法性校验。
- 自定义 Skill `formation-control`，把口语化指令映射为受控任务。
- 一键安装、只读预检、本地仿真、现场任务和停止状态验收入口。
- 任务完成后生成位置误差、朝向误差和最小车间距离记录。

## 五、技术实现

**openvela / ai_agent 侧**

- `formation_control` 工具把任务级 JSON 请求转发给本机编队服务，实现在
  `app/velamecanum/openvela/ai_agent/src/tools/tool_formation.c`，
  注册在 `tool_registry.c`。
- 工具在转发前做安全校验：`action` 只接受 `start`/`status`/`stop`/`reset`/`capabilities`；
  `formation` 只接受 `square`/`line`/`triangle`/`circle`/`diamond`；`control_mode` 只接受
  `anchored`/`laplacian`/`second_order`；`spacing_m` 限定 0.35–2.5，
  `duration_s` 限定 1–300，越界直接拒绝。
- 自定义 Skill `formation-control` 描述"什么场景该调用、怎么调用、出错怎么办"，
  见 `app/velamecanum/skills/formation-control.md`。

**本机与车端**

- ROS 2 车端包 `mentorpi_formation_bringup`：AMCL/EKF 定位、雷达保护、
  多机器人命名空间、地图保存与初始位姿设置。
- 车端路线跟踪使用 0.28 m 前视距离，连续通过拐角并减少局部降速。
- 控制权采用短期许可 + 命令桥（command bridge）机制，四车确认许可后才发布完整轨迹。
- 轨迹心跳中断约 2 秒后车端自主停止。
- openvela 板级配置片段见 `app/velamecanum/openvela/generated/formation.config`。

## 六、目录结构

- `app/velamecanum/` —— 作品代码（应用形态），由仓库 manifest 映射到
  `packages/demos/contest2026_498_velamecanum`。
  - `Makefile` / `Make.defs` / `Kconfig` / `CMakeLists.txt` / `velamecanum_main.c` —— openvela 端应用入口骨架。
  - `skills/formation-control.md` —— ai_agent 自定义 Skill。
  - `openvela/ai_agent/` —— `formation_control` 工具源码与工具注册。
  - `openvela/formation_lab/` —— 本地验证环境（编队仿真、CLI、HTTP 服务）。
  - `openvela/ros2_ws/` —— 车端建图、定位与运动测试包。
  - `openvela/deploy/` —— 车端 systemd 服务与部署脚本。
  - `openvela/robot-runtime/` —— 2026-09-20 从四台实车抓取的部署快照（容器 `formation_lab` 运行时、`config/mentorpi.json`、主机 `scripts/`、systemd 单元、`shared/` 运维工具），用于版本一致性核验。
  - `openvela/history/formation-dev-prototype/` —— 早期原型留档（`formation_lab/tests/` 与 `ros2_ws` 测试），保留开发过程可追溯。
  - `outputs/formation-kit/` —— 当前四车任务控制包、planner、车端 agent、地图资料、回归测试与现场任务记录。
  - `work/` —— 部署、诊断、定位检查、网络核验与验收工具。
- `docs/` —— 代码索引、验收状态、测试结果、仓库移交说明与四车实车取证记录（`docs/robot-fleet-evidence/`）。
- `logs/yu-baixi/` —— AI Coding 原始会话日志与清单（`manifest.json` 与 `raw/codex/<MM-DD>/rollout-*.jsonl`，入库前已脱敏）。
- `README.md` —— 本文件。

## 七、运行方式

### 1. Windows 本地仿真与自动测试

安装 Python 3.9 或更高版本，在 PowerShell 中进入控制程序目录：

```powershell
cd app/velamecanum/outputs/formation-kit
& .\run_formation.cmd square --spacing 0.5 --simulate
& .\test_local.cmd
```

运行入口会在 `app/velamecanum/work/.venv/` 创建本地 Python 环境并安装
`requirements-control.txt` 中的依赖。

### 2. openvela 构建

`app/velamecanum` 已由 manifest 软链到 openvela 工作树的
`packages/demos/contest2026_498_velamecanum`。在 openvela 工作区根目录用
`build.sh` 构建对应板级配置，并通过 `menuconfig` 打开
`LVX_USE_DEMO_CONTEST2026_498_VELAMECANUM` 即可编译本应用：

```bash
./build.sh <board-config-path> menuconfig
./build.sh <board-config-path> -j8
```

`formation_control` 工具位于 `packages/ai_agent`，其新增源文件与开关见
`app/velamecanum/openvela/ai_agent/`。

### 3. Formation Lab 本地运行

```bash
cd app/velamecanum/openvela/formation_lab
PYTHONPATH=. python3 -m formation_lab.server
```

服务启动后可以访问 `http://127.0.0.1:8765/`。

### 4. ROS 2 与小车部署

ROS 2 包位于 `app/velamecanum/openvela/ros2_ws/src/mentorpi_formation_bringup/`，
车端部署文件位于 `app/velamecanum/openvela/deploy/`，现场控制包位于
`app/velamecanum/outputs/formation-kit/`。

现场运行前需要准备四台小车的 SSH 连接信息，并完成地图、AMCL、雷达、
ROS 2 topic、TF、agent 服务与 command bridge 服务检查。现场部署凭据由操作者
运行时输入，不随仓库保存。

只读预检：

```powershell
cd app/velamecanum/outputs/formation-kit
& .\run_formation.cmd square --spacing 0.5 --check-only
```

正式方阵任务：

```powershell
& .\run_formation.cmd square --spacing 0.5
```

同步运动任务：

```powershell
& .\run_synchronized_formation.cmd square --spacing 0.5
```

闭合路线任务：

```powershell
& .\run_formation_lap.cmd --formation triangle --spacing 0.5 --laps 1 --bounds -2.6 2.6 -1.8 2.6
```

## 八、AI Coding 使用说明

本作品使用 Codex 参与需求理解、openvela 工程调查、控制方案设计、代码编写、
ROS 2 接口核对、定位与网络诊断、仿真测试、现场运行分析、安全停止流程、
发布包检查和文档编写。

AI 协作帮助项目形成了可重复执行的检查工具和验收流程，并持续核对四车服务状态、
许可状态、地图数据、路线安全、位置误差、车间距离与任务完成状态。

导出的会话日志位于 `logs/yu-baixi/`。

## 九、Skill 与主动能力

- Skill：`app/velamecanum/skills/formation-control.md`
- 主动能力：任务完成后主动汇报位置误差、朝向误差与最小车间距离；最小车间距离
  低于 0.30 m 或路线心跳中断时主动停止并告警；按预设时间主动巡检四车状态。

## 十、验收结果

- 方阵前进与转弯任务状态：`FORMATION_COMPLETE`。
- 最大位置误差：`0.0424 m`。
- 最大朝向误差：`0.0125 rad`，约 `0.72°`。
- 最小车间距离：`0.4917 m`。
- robot1 脱离后的方阵恢复任务状态：`FORMATION_COMPLETE`。
- 本地自动测试：13 项通过（`docs/TEST-RESULTS.md`）。
- 安装包清单：50 个文件通过校验。
- 停止状态验收：`STATIONARY_ACCEPTANCE_OK`。

现场记录见 `app/velamecanum/outputs/formation-kit/mission-reports/` 与
`docs/ACCEPTANCE-STATUS.md`。