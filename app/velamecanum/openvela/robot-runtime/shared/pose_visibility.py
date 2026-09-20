#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""可见性矩阵：本机能收到多少个 robotN 的位姿/速度（域 42）。

    python3 pose_visibility.py [秒数]

在每台车上各跑一次，就能看出车队域的连通情况。
"""
from __future__ import annotations

import sys
import time

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry

SECS = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
ROBOTS = ["robot1", "robot2", "robot3", "robot4"]

rclpy.init()
node = rclpy.create_node("codex_visibility")
pose_count = {r: 0 for r in ROBOTS}
odom_count = {r: 0 for r in ROBOTS}


def mk_pose(rid):
    def cb(_msg):
        pose_count[rid] += 1
    return cb


def mk_odom(rid):
    def cb(_msg):
        odom_count[rid] += 1
    return cb


for r in ROBOTS:
    node.create_subscription(PoseWithCovarianceStamped, "/%s/amcl_pose" % r, mk_pose(r), 10)
    node.create_subscription(Odometry, "/%s/odom" % r, mk_odom(r), 10)

t0 = time.time()
while time.time() - t0 < SECS:
    rclpy.spin_once(node, timeout_sec=0.2)

print("本机(%s) %.0f 秒内收到的消息数：" % (node.get_namespace(), SECS))
for r in ROBOTS:
    print("   %s  位姿 %5d 条   速度 %5d 条" % (r, pose_count[r], odom_count[r]))
node.destroy_node()
rclpy.shutdown()
