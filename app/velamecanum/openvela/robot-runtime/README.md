# 车端部署快照（现场版本）

本目录是 **2026-09-20 从四台实车（192.168.1.201–204）直接抓取的实际部署内容**，
按车上的绝对路径原样摆放，用于证明仓库代码与现场运行版本一致。

抓取方式：SSH 登录 `pi@192.168.1.201..204`，打包主机 `/opt/openvela-formation`、
容器 `MentorPi:/opt/openvela-formation`、共享目录与 `/etc/systemd/system` 下的单元文件，
回落本地后逐文件 sha256 校验。

## 目录

```
robot-runtime/
├── container/opt/openvela-formation/     # 容器 MentorPi (ros:humble) 内
│   ├── formation_lab/                    #   ROS 2 编队运行时（22 个模块）
│   │   └── variants/robot1/              #   robot1 上与他车不同的副本
│   └── config/mentorpi.json              #   编队参数与四车话题表
├── host/opt/openvela-formation/          # 主机 (Debian 12, 用户 pi)
│   ├── maps/classroom.{pgm,yaml}         #   共享地图
│   └── scripts/                          #   19 个 systemd 启动/停止脚本
├── host/etc/systemd/system/              # 6 个 systemd 单元
└── shared/                               # 容器 /home/ubuntu/shared = 主机 /home/pi/docker/tmp
```

## 编队角色

| 车 | 角色 | 独有的脚本 / 单元 |
|---|---|---|
| robot1 | 协调者 | `fleet_ntp.py`、`fleet-ntp.service`、`run_reconfiguration_coordinator.sh`、`formation-reconfiguration.service` |
| robot2/3/4 | 跟随者 | — |

`isolated_command_test.py` 仅 robot1 有（在域 94/95，无真实机器人节点的隔离环境跑指令桥测试）。
`run_localization_vendor_domain.sh` 在 robot1、robot4 上有，robot2/3 缺。
`reconfiguration_ros.py` 的 robot1 版本与他车不同，另存 `formation_lab/variants/robot1/`。

## 运行链路

1. `cmd-vel-watchdog.service` 常驻，指令停发即刹停。
2. 每台车在自己的**隔离厂商域**内跑 AMCL/EKF 定位与雷达。
3. `fleet-bridge@.service` 起 `fleet_bridge.py`：把隔离域里的位姿/里程计/雷达/TF
   **前缀化后只读转发**进车队域。它不桥任何指令、服务或动作话题，自身开不动车。
4. `formation-command-bridge@.service` 起 `command_bridge.py`：受 lease 管控的指令桥，
   只有拿到控制权时才把轨迹发布到本车 `cmd_vel`；`arm_/disarm_command_bridge.sh` 授予/收回。
5. `formation-agent@.service` 起编队 agent，`fleet-ntp.service` 在 robot1 上统一四车时钟。
6. `formation-reconfiguration.service` 在 robot1 上协调队形重配置。

## 与仓库其他目录的关系

- 本目录是**现场快照**，用于版本一致性核验。
- 可读性更好的整理版、回归测试与发布包工具在
  `app/velamecanum/outputs/formation-kit/`。
- 部署安装脚本与 systemd 服务在 `app/velamecanum/openvela/deploy/`。
- 建图/定位/运动测试的 ROS 2 包在 `app/velamecanum/openvela/ros2_ws/`。
- 仿真与 CLI 在 `app/velamecanum/openvela/formation_lab/`。
- 四车逐文件一致性核验见 `docs/robot-fleet-evidence/per-car-hashes.txt`。

## 未纳入

厂商镜像自带的教程源码（`/home/pi/docker/src/in.py`、`out.py`、`sorting.py` 等）、
Hiwonder 的环境变量文件（`.robotrc`、`.typerc`）、现场运行日志、备份目录、
共享目录中的 SSH 私钥，均不属于本作品代码，未纳入。