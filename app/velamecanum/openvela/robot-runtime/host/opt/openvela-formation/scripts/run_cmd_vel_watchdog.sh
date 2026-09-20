#!/usr/bin/env bash
# 在车的容器里启动 cmd_vel 看门狗（systemd 用）
set -euo pipefail
source /etc/default/openvela-formation

exec docker exec \
  --user "$MENTORPI_CONTAINER_USER" \
  --env ROS_DOMAIN_ID="$VENDOR_ROS_DOMAIN_ID" \
  --env ROS_LOCALHOST_ONLY="$ROS_LOCALHOST_ONLY" \
  "$MENTORPI_CONTAINER" /bin/bash -lc '
    source /opt/ros/humble/setup.bash
    if [ -f /home/ubuntu/ros2_ws/install/setup.bash ]; then
      source /home/ubuntu/ros2_ws/install/setup.bash
    fi
    exec python3 /home/ubuntu/shared/cmd_vel_watchdog.py
  '
