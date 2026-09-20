#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 formation_lab/mentorpi_agent.py 的位姿解包 bug。

现象：agent 一启动就崩
    ValueError: too many values to unpack (expected 5)
    at current_observation():  x, y, yaw, localization_ok, _ = pose_entry

原因：poses[...] 实际存的是 6 元组
    (x, y, yaw, localization_ok, 接收时刻monotonic, 消息时间戳unix)
    而这里只解包 5 个。

顺带修第二处：agent 订阅 /robotN/odom 用的是默认 QoS（RELIABLE），而
fleet_bridge 用 qos_profile_sensor_data（BEST_EFFORT）发布，日志里会刷
    "offering incompatible QoS. No messages will be received from it"
即速度反馈根本收不到。改成 sensor-data QoS 与桥上一致。

在车的容器里跑：python3 /home/ubuntu/shared/patch_agent.py
"""
from __future__ import annotations

import pathlib
import shutil
import sys
import time

PATH = pathlib.Path("/opt/openvela-formation/formation_lab/mentorpi_agent.py")

FIXES = [
    # (说明, 原文, 新文)
    ("位姿元组按 6 元解包",
     "        x, y, yaw, localization_ok, _ = pose_entry",
     "        x, y, yaw, localization_ok, _, _ = pose_entry"),
    ("odom 订阅改用 sensor-data QoS（与 fleet_bridge 一致）",
     '            str(mapping[observed_id]["odom_topic"]),\n'
     "            make_odom_callback(observed_id),\n"
     "            10,\n",
     '            str(mapping[observed_id]["odom_topic"]),\n'
     "            make_odom_callback(observed_id),\n"
     "            qos_profile_sensor_data,\n"),
]


def main() -> int:
    src = PATH.read_text(encoding="utf-8")
    changes = []
    for name, old, new in FIXES:
        if new in src:
            print("跳过（已修）：%s" % name)
            continue
        count = src.count(old)
        if count != 1:
            print("✗ %s：匹配到 %d 处（预期 1 处），跳过，请人工确认" % (name, count))
            continue
        src = src.replace(old, new)
        changes.append(name)
    if not changes:
        print("没有需要改的地方")
        return 0
    backup = PATH.with_name(PATH.name + ".bak-agentfix-" + time.strftime("%Y%m%d%H%M%S"))
    shutil.copy2(PATH, backup)
    PATH.write_text(src, encoding="utf-8")
    print("已修复 %d 处（备份 %s）：%s" % (len(changes), backup.name, "；".join(changes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
