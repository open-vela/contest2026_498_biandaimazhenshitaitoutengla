#!/bin/bash
# 给车上的 AMCL 设初始位姿（地图系，弧度）
#   用法: bash set_initial_pose.sh <x> <y> <yaw_rad> [域号=2]
source /opt/ros/humble/setup.bash
source /home/ubuntu/third_party_ros2/third_party_ws/install/setup.bash 2>/dev/null
source /home/ubuntu/ros2_ws/install/setup.bash 2>/dev/null
export ROS_DOMAIN_ID="${4:-2}"
export ROS_LOCALHOST_ONLY=0
export FASTRTPS_DEFAULT_PROFILES_FILE=/home/ubuntu/shared/fastdds_udp_only.xml

x="${1:?x}"; y="${2:?y}"; yaw="${3:?yaw_rad}"
python3 /home/ubuntu/shared/publish_initial_pose.py "$x" "$y" "$yaw"

echo "--- 3 秒后的 AMCL 位姿 ---"
timeout 8 ros2 topic echo /amcl_pose --field pose.pose.position --once 2>&1 | head -6
echo "--- map -> odom ---"
timeout 6 ros2 run tf2_ros tf2_echo map odom 2>&1 | sed -n '4,7p'
