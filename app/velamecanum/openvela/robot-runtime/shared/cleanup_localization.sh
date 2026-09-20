#!/bin/bash
# 清理容器里残留/重复的定位实例。
#
# 为什么需要：每次重启定位服务时，旧 launch 的子进程（map_server/amcl/
# lifecycle_manager）不一定跟着退出，容器里会累积好几组同名节点。DDS 里
# 同名节点一多，lifecycle_manager 的服务调用就可能打到"错的"那份上，日志
# 表现为 "Failed to change state for node: map_server"，地图加载成功却
# 激活不了。实测车 1 累积了 4 组。
#
# 用法（在车的容器里执行）: bash /home/ubuntu/shared/cleanup_localization.sh
pkill -9 -f nav2_map_server 2>/dev/null
pkill -9 -f nav2_amcl 2>/dev/null
pkill -9 -f nav2_lifecycle_manager 2>/dev/null
pkill -9 -f "mentorpi_formation_bringup localization.launch.py" 2>/dev/null
sleep 2
left=$(pgrep -fc "nav2_map_server|nav2_amcl|nav2_lifecycle_manager" 2>/dev/null || true)
echo "清理完成，剩余定位进程：${left:-0}"
