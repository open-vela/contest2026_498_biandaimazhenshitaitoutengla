#!/usr/bin/env python3
"""Read-only bridge from one isolated MentorPi ROS domain to the fleet domain.

No command, service, or action topic is bridged. The bridge cannot drive a car.
"""

from __future__ import annotations

import argparse
import copy
import json
import signal
import time
from collections import deque


def prefixed(robot: str, frame: str) -> str:
    frame = frame.lstrip("/")
    if not frame or frame == "map" or frame.startswith(robot + "/"):
        return frame
    return f"{robot}/{frame}"


def scan_frame(robot: str, frame: str) -> str:
    """Normalize the MentorPi lidar alias before adding the robot prefix."""
    frame = frame.lstrip("/")
    if frame == "laser_frame":
        frame = "lidar_frame"
    return prefixed(robot, frame)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--robot", required=True, choices=[f"robot{i}" for i in range(1, 5)])
    parser.add_argument("--local-domain", required=True, type=int)
    parser.add_argument("--fleet-domain", required=True, type=int)
    args = parser.parse_args()
    if args.local_domain == args.fleet_domain:
        parser.error("local and fleet domains must differ")

    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from nav_msgs.msg import Odometry
    from rclpy.context import Context
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan
    from std_msgs.msg import String
    from tf2_msgs.msg import TFMessage

    local_context, fleet_context = Context(), Context()
    rclpy.init(context=local_context, domain_id=args.local_domain)
    rclpy.init(context=fleet_context, domain_id=args.fleet_domain)
    local = rclpy.create_node(f"fleet_source_{args.robot}", context=local_context)
    fleet = rclpy.create_node(f"fleet_bridge_{args.robot}", context=fleet_context)

    tf_static_qos = QoSProfile(
        depth=100,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
        reliability=ReliabilityPolicy.RELIABLE,
    )
    publishers = {
        "odom": fleet.create_publisher(Odometry, f"/{args.robot}/odom", qos_profile_sensor_data),
        "scan": fleet.create_publisher(LaserScan, f"/{args.robot}/scan_raw", qos_profile_sensor_data),
        "pose": fleet.create_publisher(PoseWithCovarianceStamped, f"/{args.robot}/amcl_pose", qos_profile_sensor_data),
        "tf": fleet.create_publisher(TFMessage, "/tf", 100),
        "tf_static": fleet.create_publisher(TFMessage, "/tf_static", tf_static_qos),
    }
    heartbeat = fleet.create_publisher(String, f"/{args.robot}/fleet/heartbeat", 10)
    peers_pub = fleet.create_publisher(String, f"/{args.robot}/fleet/peers", 10)
    queues = {key: deque(maxlen=100 if key.startswith("tf") else 2) for key in publishers}
    last_local = {key: 0.0 for key in publishers}
    last_peer: dict[str, float] = {}

    def receive(key: str):
        def callback(message):
            queues[key].append(copy.deepcopy(message))
            last_local[key] = time.monotonic()
        return callback

    local.create_subscription(Odometry, "/odom", receive("odom"), qos_profile_sensor_data)
    local.create_subscription(LaserScan, "/scan_raw", receive("scan"), qos_profile_sensor_data)
    local.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", receive("pose"), 10)
    local.create_subscription(TFMessage, "/tf", receive("tf"), 100)
    local.create_subscription(TFMessage, "/tf_static", receive("tf_static"), tf_static_qos)

    def peer_callback(robot: str):
        def callback(message: String):
            try:
                if json.loads(message.data).get("robot") == robot:
                    last_peer[robot] = time.monotonic()
            except (ValueError, TypeError):
                pass
        return callback

    for robot in (f"robot{i}" for i in range(1, 5)):
        if robot != args.robot:
            fleet.create_subscription(String, f"/{robot}/fleet/heartbeat", peer_callback(robot), 10)

    def flush() -> None:
        for key, items in queues.items():
            if not items:
                continue

            if key.startswith("tf"):
                # ROS publishers often emit many tiny TF messages.  Forwarding
                # every sample separately creates excessive Wi-Fi packet and
                # reliable-delivery overhead across four robots.  Keep the
                # newest transform for each frame pair and publish one batch per
                # 50 ms bridge cycle.
                latest = {}
                while items:
                    msg = items.popleft()
                    for transform in msg.transforms:
                        transform.header.frame_id = prefixed(args.robot, transform.header.frame_id)
                        transform.child_frame_id = prefixed(args.robot, transform.child_frame_id)
                        latest[(transform.header.frame_id, transform.child_frame_id)] = transform
                if latest:
                    batched = TFMessage()
                    batched.transforms = list(latest.values())
                    publishers[key].publish(batched)
                continue

            # Downsample state topics to the newest sample in this 50 ms cycle.
            # Scan is 10 Hz in practice, while odom remains a fresh 20 Hz feed.
            msg = items.pop()
            items.clear()
            if key == "odom":
                msg.header.frame_id = prefixed(args.robot, msg.header.frame_id)
                msg.child_frame_id = prefixed(args.robot, msg.child_frame_id)
            elif key == "scan":
                msg.header.frame_id = scan_frame(args.robot, msg.header.frame_id)
            elif key == "pose":
                msg.header.frame_id = prefixed(args.robot, msg.header.frame_id)
            publishers[key].publish(msg)

    def status() -> None:
        now = time.monotonic()
        hb = String()
        hb.data = json.dumps({"robot": args.robot, "local_domain": args.local_domain,
                              "fleet_domain": args.fleet_domain})
        heartbeat.publish(hb)
        peers = String()
        peers.data = json.dumps({"robot": args.robot,
                                 "peers": {name: round(now - seen, 2)
                                           for name, seen in last_peer.items() if now - seen < 3},
                                 "local": {name: round(now - seen, 2)
                                           for name, seen in last_local.items() if seen and now - seen < 3}})
        peers_pub.publish(peers)

    fleet.create_timer(0.05, flush)
    fleet.create_timer(1.0, status)
    local_executor = SingleThreadedExecutor(context=local_context)
    fleet_executor = SingleThreadedExecutor(context=fleet_context)
    local_executor.add_node(local)
    fleet_executor.add_node(fleet)
    stop = False

    def request_stop(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    print(f"fleet bridge {args.robot}: local={args.local_domain} fleet={args.fleet_domain}", flush=True)
    try:
        while not stop:
            # spin_once handles at most one ready callback.  Blocking for 50 ms
            # in each context capped the bridge at roughly 10 callbacks/s while
            # odom, scan, and TF together routinely exceed 80 callbacks/s.  Poll
            # both contexts without blocking and yield briefly to keep latency
            # bounded without busy-spinning a CPU core.
            local_executor.spin_once(timeout_sec=0.0)
            fleet_executor.spin_once(timeout_sec=0.0)
            time.sleep(0.001)
    finally:
        local_executor.remove_node(local)
        fleet_executor.remove_node(fleet)
        local.destroy_node()
        fleet.destroy_node()
        rclpy.shutdown(context=local_context)
        rclpy.shutdown(context=fleet_context)


if __name__ == "__main__":
    main()

# BEST_EFFORT pose tuning: amcl_pose is a lossy-link stream, not a control message.
