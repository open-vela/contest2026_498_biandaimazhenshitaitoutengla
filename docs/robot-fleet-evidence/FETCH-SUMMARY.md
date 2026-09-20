# 小车代码抓取记录（2026-09-20）

## 连接方式
- 主机：DESKTOP-88IQK8S，本机以太网 192.168.1.103/24
- 小车：192.168.1.201 ~ 192.168.1.204（robot1 ~ robot4），SSH 用户 pi，密码认证
- 免交互方式：`SSH_ASKPASS=<askpass.cmd> SSH_ASKPASS_REQUIRE=force` + 系统自带 OpenSSH（paramiko 装不上，pip 走代理失败）
- 抓取脚本：`context.sh`（base64 下发执行）；打包脚本产物见 `robots/robotN/cf-robotN.tgz`

## 落盘内容
| 车 | 压缩包 | 解包文件数 | formation_lab(.py) | 主机 scripts/ |
|---|---|---|---|---|
| robot1 | cf-robot1.tgz 500 KB | 259 | 22 | 25 |
| robot2 | cf-robot2.tgz 421 KB | 255 | 21 | 22 |
| robot3 | cf-robot3.tgz 389 KB | 234 | 21 | 22 |
| robot4 | cf-robot4.tgz 1.07 MB | 679 | 21 | 27 |

sha256（下载后已校验一致）：
- robot1 b34e23264bb9176f664e2637eaa623e3b18c61c10d2ed0e80a15c7f207b7f30a
- robot2 7b1ec61ada3ce5b083a916ba3c87951997c826f99a123ccac958bac77a6572e9
- robot3 debb97efdc390e923641f1d9691bda291ab34d2860bb4d234404821677d942f0
- robot4 583d1f4acd27700331440688274a6f7414931fc8abba87563892057591f843bc

目录结构（每台车）：
- `unpacked/host-opt/openvela-formation/` — 主机侧：scripts(25)、maps(classroom)、backups(安装快照)
- `unpacked/container-opt-openvela-formation/` — 容器侧：formation_lab、config/mentorpi.json、maps、state(空)、backups
- `unpacked/shared/` — 挂载卷 /home/pi/docker/tmp = /home/ubuntu/shared
- `unpacked/units/` — 6 个 systemd 单元文件
- `inventory.txt` — 首次盘点（系统/网络/容器/单元/差异搜索）
- `deployment-context.txt` — 二次采集（约 14 万字符）：docker inspect、单元全文、journalctl、state、bashrc、crontab

## 关键结论
1. **容器是 stock `ros:humble`**（`tail -f /dev/null`，Privileged，NetworkMode host，无 Dockerfile/compose）——不是自建镜像。
2. `/home/pi/docker/src/` 是 **Hiwonder 厂商教程源码**（in.py=第13章智能入库, out.py, sorting.py, exchange.py, pallezting.py, lane_detect.py, self_driving.py，作者 Aiden），**属于第三方**，不进仓。
3. 编队运行时的真实位置：容器 `/opt/openvela-formation/formation_lab/`，21~22 个 .py（agent/command_bridge/command_gate/fleet_bridge/fleet_endpoint/formation_planner/reconfiguration_*/scan_localizer/auto_localize/mentorpi_agent/second_order/laplacian/simulator/server/cli/mission_gateway/llm_stub/formation_once + isolated_command_test(仅robot1)）。
4. 四台车 formation_lab 代码一致，仅两处差异：`reconfiguration_ros.py`（robot1 与 2/3/4 不同）、`isolated_command_test.py`（仅 robot1）。
5. 地图只有一张：`classroom.pgm/yaml`（共享）。
6. 网关端口只有 **8765**（formation_lab/server.py 默认端口，仿真 Lab），**没有 8125/8766**。

## 负面结论（重要）
在四台车上全盘搜索以下文件 → **0 命中**：
`vcmd.py`、`nlp_parse.py`、`ros_car.py`、`formation_voice_bridge.py`、`voice-assistant.service`、`wakeword.py`、`voice_text.jsonl`、`speech-bridge.py`

=> 小车上是 **ROS2 编队运行时 + 部署脚本**，不含清单要求的 **M1 语音层 / Windows 网关（8125/8766）**。这些文件不在车上，需从别处补齐。

## 安全提醒
- `unpacked/shared/.ssh/id_rsa` 是放在共享目录里的**私钥**，属于不该进仓的内容。
- 抓取时临时写入过公钥 `codex-fetch-20260920` 到四台车 pi 用户的 authorized_keys（该公钥认证被服务器拒绝，实际未生效），**已于本次任务结束时从四台车删除**，并清掉了临时备份文件。