#!/bin/bash
# 检查车上建图节点：是否在发 /map、是否在发 map->odom
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID="${1:-2}"
export ROS_LOCALHOST_ONLY=0
export FASTRTPS_DEFAULT_PROFILES_FILE=/home/ubuntu/shared/fastdds_udp_only.xml

echo "--- 节点数 ---"
timeout 12 ros2 node list 2>/dev/null | grep -cE "map_server"
timeout 12 ros2 node list 2>/dev/null | grep -cE "amcl"
echo "--- /map 头部 ---"
timeout 12 ros2 topic echo /map --field info 2>&1 | head -12
echo "--- map -> odom ---"
timeout 10 ros2 run tf2_ros tf2_echo map odom 2>&1 | head -12
