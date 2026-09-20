#!/usr/bin/env bash
set -euo pipefail

source /etc/default/openvela-formation

# Localization consumes high-rate scan and TF data.  Keep it in this robot's
# isolated vendor domain; fleet_bridge forwards only the namespaced result and
# prefixed TF into the shared fleet domain.
#
# 2026-09-17：加 FASTRTPS_DEFAULT_PROFILES_FILE —— 容器里 /dev/shm 累积 200+
# 个 fastrtps_* 段之后，lifecycle_manager 调 map_server 的服务会直接失败
# （日志："Failed to change state for node: map_server"），地图加载成功但
# 节点激活不了。走 UDP-only 传输即可稳定激活。
exec docker exec \
  --user "$MENTORPI_CONTAINER_USER" \
  --workdir "$MENTORPI_CONTAINER_HOME" \
  --env ROS_DOMAIN_ID="$VENDOR_ROS_DOMAIN_ID" \
  --env ROS_LOCALHOST_ONLY="$ROS_LOCALHOST_ONLY" \
  --env MENTORPI_VENDOR_WS="$MENTORPI_VENDOR_WS" \
  --env MAP_YAML="$MAP_YAML" \
  --env FASTRTPS_DEFAULT_PROFILES_FILE=/home/ubuntu/shared/fastdds_udp_only.xml \
  "$MENTORPI_CONTAINER" /bin/bash -lc '
    set -eo pipefail
    source /opt/ros/humble/setup.bash
    if [ -f /home/ubuntu/third_party_ros2/third_party_ws/install/setup.bash ]; then
      source /home/ubuntu/third_party_ros2/third_party_ws/install/setup.bash
    fi
    source "$MENTORPI_VENDOR_WS/install/setup.bash"
    test -f "$MAP_YAML"
    exec ros2 launch mentorpi_formation_bringup localization.launch.py \
      map:="$MAP_YAML" \
      scan_topic:=scan_raw \
      odom_frame:=odom \
      base_frame:=base_footprint
  '
