#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给车队的 systemd 启动脚本加上统一的 DDS profile 环境变量。

涉及 /opt/openvela-formation/scripts/ 下的：
    run_fleet_bridge.sh      车队数据桥（读只读）
    run_command_bridge.sh    指令桥（受 lease 管控）
    run_formation_agent.sh   编队 agent

做法：在 "docker exec" 之后插入 --env FASTRTPS_DEFAULT_PROFILES_FILE=...，
这样 profile 会传进容器（只设 systemd 的 Environment= 是传不进去的）。

在车上用 sudo 跑：sudo python3 patch_fleet_scripts.py
"""
from __future__ import annotations

import pathlib
import shutil
import sys

SCRIPTS = pathlib.Path("/opt/openvela-formation/scripts")
FILES = ["run_fleet_bridge.sh", "run_command_bridge.sh", "run_formation_agent.sh"]
ENV = "--env FASTRTPS_DEFAULT_PROFILES_FILE=/home/ubuntu/shared/fleet_udp_unicast.xml"


def main() -> int:
    changed = 0
    for name in FILES:
        path = SCRIPTS / name
        if not path.is_file():
            print("找不到 %s，跳过" % path)
            continue
        text = path.read_text(encoding="utf-8")
        if "FASTRTPS_DEFAULT_PROFILES_FILE" in text:
            print("跳过（已加过）：%s" % name)
            continue
        if "docker exec" not in text:
            print("✗ %s 里没有 docker exec，跳过" % name)
            continue
        shutil.copy2(path, str(path) + ".bak-unicast")
        path.write_text(text.replace("docker exec", "docker exec " + ENV, 1),
                        encoding="utf-8")
        print("已加：%s" % name)
        changed += 1
    print("共修改 %d 个脚本" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
