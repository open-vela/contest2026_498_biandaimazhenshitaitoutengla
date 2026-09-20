#!/bin/bash
# 让车上 AMCL 做全局定位（丢掉当前位姿，在整个地图上重新撒粒子）
#   用法: bash reinit_global.sh <domain>
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID="${1:-2}"
export ROS_LOCALHOST_ONLY=0
export FASTRTPS_DEFAULT_PROFILES_FILE=/home/ubuntu/shared/fastdds_udp_only.xml
timeout 12 ros2 service call /reinitialize_global_localization \
  std_srvs/srv/Empty "{}" 2>&1 | tail -3
