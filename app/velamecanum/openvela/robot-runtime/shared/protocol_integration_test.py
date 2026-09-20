from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


ROBOT_IDS = ("robot1", "robot2", "robot3", "robot4")


def main() -> None:
    base = json.loads(Path("/opt/openvela-formation/config/mentorpi.json").read_text())
    state_path = Path("/tmp/formation-protocol-integration-state.json")
    state_path.unlink(missing_ok=True)
    base["hardware_output_enabled"] = True
    base["mission_protocol"] = {
        "max_duration_s": 10.0,
        "min_deadline_lead_s": 0.2,
        "prepare_timeout_s": 0.7,
        "state_path": str(state_path),
    }
    base["limits"]["arena_half_extent_m"] = 10.0
    config_path = Path("/tmp/formation-protocol-integration-config.json")
    config_path.write_text(json.dumps(base))

    rclpy.init()
    node = rclpy.create_node("formation_protocol_integration_test")
    mission_pub = node.create_publisher(String, base["mission_topic"], 10)
    pose_pubs = {
        robot: node.create_publisher(PoseWithCovarianceStamped, base["robots"][robot]["pose_topic"], 10)
        for robot in ROBOT_IDS
    }
    odom_pubs = {
        robot: node.create_publisher(Odometry, base["robots"][robot]["odom_topic"], 10)
        for robot in ROBOT_IDS
    }
    scan_pub = node.create_publisher(
        LaserScan,
        base["robots"]["robot1"]["scan_topic"],
        qos_profile_sensor_data,
    )
    acks: list[dict] = []
    commands: list[tuple[float, float, float, float]] = []
    node.create_subscription(String, base["mission_ack_topic"], lambda msg: acks.append(json.loads(msg.data)), 10)
    node.create_subscription(
        Twist,
        base["robots"]["robot1"]["cmd_vel_topic"],
        lambda msg: commands.append((time.monotonic(), msg.linear.x, msg.linear.y, msg.angular.z)),
        10,
    )

    positions = {
        "robot1": (-0.4, -0.4),
        "robot2": (-0.4, 0.4),
        "robot3": (0.4, 0.4),
        "robot4": (0.4, -0.4),
    }

    def publish_sensors() -> None:
        stamp = node.get_clock().now().to_msg()
        for robot, (x, y) in positions.items():
            pose = PoseWithCovarianceStamped()
            pose.header.stamp = stamp
            pose.header.frame_id = "map"
            pose.pose.pose.position.x = x
            pose.pose.pose.position.y = y
            pose.pose.pose.orientation.w = 1.0
            pose.pose.covariance[0] = 0.01
            pose.pose.covariance[7] = 0.01
            pose.pose.covariance[35] = 0.01
            pose_pubs[robot].publish(pose)
            odom = Odometry()
            odom.header.stamp = stamp
            odom_pubs[robot].publish(odom)
        scan = LaserScan()
        scan.header.stamp = stamp
        scan.header.frame_id = "robot1/lidar_frame"
        scan.angle_min = -math.pi
        scan.angle_max = math.pi
        scan.angle_increment = 2.0 * math.pi / 360.0
        scan.range_min = 0.05
        scan.range_max = 12.0
        scan.ranges = [2.0] * 360
        scan_pub.publish(scan)

    def pump(seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            publish_sensors()
            rclpy.spin_once(node, timeout_sec=0.02)
            time.sleep(0.03)

    def publish_mission(payload: dict) -> None:
        message = String()
        message.data = json.dumps(payload, separators=(",", ":"))
        mission_pub.publish(message)

    def wait_ack(experiment_id: str, phase: str, accepted: bool, timeout: float = 3.0) -> dict:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            pump(0.1)
            for item in acks:
                if item.get("experiment_id") == experiment_id and item.get("phase") == phase and item.get("accepted") is accepted:
                    return item
        raise AssertionError(f"missing ack {experiment_id=} {phase=} {accepted=}; got {acks}")

    def start_agent() -> subprocess.Popen:
        env = dict(os.environ)
        env["PYTHONPATH"] = "/opt/openvela-formation:" + env.get("PYTHONPATH", "")
        return subprocess.Popen(
            [
                sys.executable,
                "-m",
                "formation_lab.mentorpi_agent",
                "--robot-id",
                "robot1",
                "--config",
                str(config_path),
            ],
            env=env,
        )

    common = {
        "enabled": True,
        "formation": "square",
        "spacing_m": 0.8,
        "center_x": 0.2,
        "center_y": 0.0,
        "heading_rad": 0.0,
        "control_mode": "anchored",
    }
    agent = start_agent()
    try:
        pump(1.5)
        legacy = dict(common, experiment_id="legacy-unsafe", deadline_unix_s=time.time() + 3.0)
        publish_mission(legacy)
        rejected = wait_ack("legacy-unsafe", "invalid", False)
        assert rejected["reason"] == "two_phase_protocol_required"

        mission = dict(common, experiment_id="two-phase-001", deadline_unix_s=time.time() + 3.0)
        publish_mission(dict(mission, phase="prepare"))
        wait_ack("two-phase-001", "prepare", True)
        prepared_at = time.monotonic()
        pump(0.3)
        assert not any(abs(x) + abs(y) + abs(w) > 1e-6 for t, x, y, w in commands if t >= prepared_at)

        publish_mission(dict(mission, phase="commit"))
        wait_ack("two-phase-001", "commit", True)
        committed_at = time.monotonic()
        pump(0.8)
        assert any(abs(x) + abs(y) + abs(w) > 1e-4 for t, x, y, w in commands if t >= committed_at)

        wait_ack("two-phase-001", "deadline", True, timeout=5.0)
        deadline_seen = time.monotonic()
        pump(0.3)
        assert commands and all(abs(x) + abs(y) + abs(w) <= 1e-6 for t, x, y, w in commands if t >= deadline_seen)
    finally:
        agent.terminate()
        agent.wait(timeout=5)

    acks.clear()
    agent = start_agent()
    try:
        pump(1.2)
        replay = dict(common, experiment_id="two-phase-001", deadline_unix_s=time.time() + 3.0, phase="prepare")
        publish_mission(replay)
        rejected = wait_ack("two-phase-001", "prepare", False)
        assert rejected["reason"] == "experiment_id_retired"
    finally:
        agent.terminate()
        agent.wait(timeout=5)
        node.destroy_node()
        rclpy.shutdown()

    print("protocol_integration_ok")


if __name__ == "__main__":
    main()
