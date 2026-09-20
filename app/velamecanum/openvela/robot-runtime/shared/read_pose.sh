#!/bin/bash
# 读一次 AMCL 位姿（位置 + 协方差对角），判断定位是否收敛
#   用法: bash read_pose.sh <domain>
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID="${1:-2}"
export ROS_LOCALHOST_ONLY=0
export FASTRTPS_DEFAULT_PROFILES_FILE=/home/ubuntu/shared/fastdds_udp_only.xml
timeout 12 ros2 topic echo /amcl_pose --once 2>/dev/null | head -30
