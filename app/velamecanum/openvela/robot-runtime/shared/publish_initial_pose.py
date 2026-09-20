#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给根命名空间下的 AMCL 发布初始位姿（带时间戳）。

     python3 publish_initial_pose.py <x> <y> <yaw_rad>

为什么不直接用 ros2 topic pub：命令行发的消息 stamp 是 0，AMCL 会当成过期
数据丢掉；这里用节点时钟打时间戳，并连发三次。
"""
from __future__ import annotations

import math
import sys
import time

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped


def main() -> int:
    x, y, yaw = (float(v) for v in sys.argv[1:4])
    rclpy.init()
    node = rclpy.create_node("codex_set_initial_pose")
    pub = node.create_publisher(PoseWithCovarianceStamped, "/initialpose", 10)

    t0 = time.time()
    while pub.get_subscription_count() == 0 and time.time() - t0 < 8.0:
        rclpy.spin_once(node, timeout_sec=0.1)
    subs = pub.get_subscription_count()

    msg = PoseWithCovarianceStamped()
    msg.header.frame_id = "map"
    msg.pose.pose.position.x = x
    msg.pose.pose.position.y = y
    msg.pose.pose.orientation.z = math.sin(yaw * 0.5)
    msg.pose.pose.orientation.w = math.cos(yaw * 0.5)
    msg.pose.covariance[0] = 0.04
    msg.pose.covariance[7] = 0.04
    msg.pose.covariance[35] = 0.07

    for _ in range(3):
        msg.header.stamp = node.get_clock().now().to_msg()
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.2)

    print("已发布初始位姿 x=%.3f y=%.3f yaw=%.3f rad（AMCL 订阅者 %d 个）"
          % (x, y, yaw, subs))
    node.destroy_node()
    rclpy.shutdown()
    return 0 if subs else 2


if __name__ == "__main__":
    sys.exit(main())
