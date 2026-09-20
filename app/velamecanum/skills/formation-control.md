---
name: formation-control
description: 指挥四台 MentorPi M1 麦克纳姆轮小车组成指定队形并执行前进、转弯、恢复队形与安全停止。当用户提到编队、队形、方阵、一字排开、队列、集合、圆形队形、菱形队形、三角形队形、恢复队形、停止编队、四车协同前进时使用本技能。
---

# formation-control

## 一、这个技能做什么

把用户的口语化指令转成一次受控的四车编队任务：选择队形 → 检查场地与安全边界 →
下发任务 → 跟踪进度 → 汇报结果或停止。

执行动作统一走 openvela 端的 `formation_control` 工具，工具会把请求以 JSON 通过
HTTP POST 转发给本地编队服务，再由四台小车上的路线跟踪与安全保护程序完成运动。

## 二、能力与安全边界

| 项目 | 允许取值 |
| --- | --- |
| action | `start` / `status` / `stop` / `reset` / `capabilities` |
| formation | `square` / `line` / `circle` / `diamond` / `triangle` |
| control_mode | `anchored`（默认）/ `laplacian` / `second_order` |
| spacing_m | `0.35` – `2.5` |
| duration_s | `1` – `300` |
| 最小车间距离 | `0.30 m`（低于此值必须停止） |
| 车端速度/加速度上限 | `0.875 m/s` / `2.0 m/s²` |

超出上表的参数会被工具直接以 `unsafe_spacing`、`unsafe_duration`、
`invalid_formation`、`invalid_control_mode` 拒绝，不要尝试绕过。

## 三、调用方式

单个 JSON 对象，交给 `formation_control` 工具：

```json
{"action": "start", "formation": "square", "spacing_m": 0.5, "control_mode": "anchored"}
```

- 只是想知道支持什么：`{"action": "capabilities"}`
- 查看当前任务：`{"action": "status"}`
- 立即停下：`{"action": "stop"}`
- 回到初始位置并复位状态：`{"action": "reset"}`

## 四、执行步骤

1. **确认意图**：用户说的队形要映射到 `square` / `line` / `circle` / `diamond` / `triangle`；
   用户没说间距时用 `0.5 m`。
2. **先查后动**：先发 `{"action": "capabilities"}` 和 `{"action": "status"}`，
   确认没有正在执行的任务。
3. **参数检查**：间距落在 `0.35–2.5` 之间、时长不超过 `300 s`，否则向用户复述可用范围。
4. **下发任务**：发送 `start` 请求。
5. **跟踪**：轮询 `status`，任务完成时汇报位置误差、朝向误差和最小车间距离。
6. **收尾**：任务结束后确认已停止；一旦出现车间距离过小、定位丢失或通信中断，
   立刻 `stop` 并如实说明原因。

## 五、主动场景

本技能配合 ai_agent 的主动任务使用：

- **完成主动汇报**：任务返回 `FORMATION_COMPLETE` 后，不等用户询问就播报
  最大位置误差、最大朝向误差和最小车间距离。
- **阈值主动告警**：轮询中发现最小车间距离低于 `0.30 m`，立即 `stop` 并告警。
- **中断主动播报**：路线心跳中断（约 2 秒未收到轨迹心跳，车端会自动停止）后，
  主动说明"已自动停止"以及停下时的队形状态。
- **定时巡检**：按预设时间主动执行一次 `status`，报告四车服务与定位状态。

## 六、演示记录

> 待补：录制或截取一次完整对话（用户一句话 → Agent 选技能 → 下发任务 →
> 主动汇报结果），保存到 `docs/` 并在根 README 中引用。

## 七、相关文件

- `openvela/ai_agent/src/tools/tool_formation.c` —— 工具实现与参数校验
- `openvela/ai_agent/src/tools/tool_registry.c` —— 工具注册
- `outputs/formation-kit/run_autonomous_formation.py` —— 任务控制与误差报告
- `docs/ACCEPTANCE-STATUS.md` —— 现场验收数据