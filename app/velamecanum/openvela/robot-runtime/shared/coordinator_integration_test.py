from __future__ import annotations

import json
import math
import os
import subprocess
import sys
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
    base["hardware_output_enabled"] = True
    base["mission_protocol"] = {
        "max_duration_s": 10.0,
        "min_deadline_lead_s": 0.2,
        "prepare_timeout_s": 2.0,
        "state_path": "/tmp/coordinator-integration-{robot_id}.json",
    }
    base["limits"]["arena_half_extent_m"] = 10.0
    config_path = Path("/tmp/coordinator-integration-config.json")
    config_path.write_text(json.dumps(base))
    for robot_id in ROBOT_IDS:
        Path(f"/tmp/coordinator-integration-{robot_id}.json").unlink(missing_ok=True)

    rclpy.init()
    node = rclpy.create_node("coordinator_integration_test")
    positions = {
        "robot1": (-0.4, -0.4),
        "robot2": (-0.4, 0.4),
        "robot3": (0.4, 0.4),
        "robot4": (0.4, -0.4),
    }
    pose_pubs = {
        robot: node.create_publisher(PoseWithCovarianceStamped, base["robots"][robot]["pose_topic"], 10)
        for robot in ROBOT_IDS
    }
    odom_pubs = {
        robot: node.create_publisher(Odometry, base["robots"][robot]["odom_topic"], 10)
        for robot in ROBOT_IDS
    }
    scan_pubs = {
        robot: node.create_publisher(LaserScan, base["robots"][robot]["scan_topic"], qos_profile_sensor_data)
        for robot in ROBOT_IDS
    }
    bridge_pubs = {
        robot: node.create_publisher(String, f"/{robot}/formation/command_bridge_status", 10)
        for robot in ROBOT_IDS
    }
    acknowledgements: list[dict] = []
    commands: dict[str, list[tuple[float, float, float, float]]] = {robot: [] for robot in ROBOT_IDS}
    subscriptions = [
        node.create_subscription(
            String,
            base["mission_ack_topic"],
            lambda msg: acknowledgements.append(json.loads(msg.data)),
            10,
        )
    ]

    def command_callback(robot_id: str):
        def callback(message: Twist) -> None:
            commands[robot_id].append((time.monotonic(), message.linear.x, message.linear.y, message.angular.z))

        return callback

    for robot_id in ROBOT_IDS:
        subscriptions.append(
            node.create_subscription(
                Twist,
                base["robots"][robot_id]["cmd_vel_topic"],
                command_callback(robot_id),
                10,
            )
        )

    def publish_inputs() -> None:
        stamp = node.get_clock().now().to_msg()
        for robot_id, (x, y) in positions.items():
            pose = PoseWithCovarianceStamped()
            pose.header.stamp = stamp
            pose.header.frame_id = "map"
            pose.pose.pose.position.x = x
            pose.pose.pose.position.y = y
            pose.pose.pose.orientation.w = 1.0
            pose.pose.covariance[0] = 0.01
            pose.pose.covariance[7] = 0.01
            pose.pose.covariance[35] = 0.01
            pose_pubs[robot_id].publish(pose)
            odom = Odometry()
            odom.header.stamp = stamp
            odom_pubs[robot_id].publish(odom)
            scan = LaserScan()
            scan.header.stamp = stamp
            scan.header.frame_id = f"{robot_id}/lidar_frame"
            scan.angle_min = -math.pi
            scan.angle_max = math.pi
            scan.angle_increment = 2.0 * math.pi / 360.0
            scan.range_min = 0.05
            scan.range_max = 12.0
            scan.ranges = [2.0] * 360
            scan_pubs[robot_id].publish(scan)
            bridge = String()
            bridge.data = json.dumps({"robot": robot_id, "armed": True, "forwarding": False, "reason": "armed_idle"})
            bridge_pubs[robot_id].publish(bridge)

    def pump(seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            publish_inputs()
            rclpy.spin_once(node, timeout_sec=0.02)
            time.sleep(0.03)

    env = dict(os.environ)
    env["PYTHONPATH"] = "/opt/openvela-formation:" + env.get("PYTHONPATH", "")
    agents = [
        subprocess.Popen(
            [sys.executable, "-m", "formation_lab.mentorpi_agent", "--robot-id", robot_id, "--config", str(config_path)],
            env=env,
        )
        for robot_id in ROBOT_IDS
    ]
    coordinator = None
    try:
        pump(1.8)
        coordinator = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "formation_lab.formation_once",
                "--config",
                str(config_path),
                "--distance-m",
                "0.2",
                "--duration-s",
                "3.0",
                "--execute",
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 10.0
        while coordinator.poll() is None and time.monotonic() < deadline:
            pump(0.1)
        if coordinator.poll() is None:
            coordinator.terminate()
            raise AssertionError("coordinator timed out")
        stdout, stderr = coordinator.communicate(timeout=2)
        assert coordinator.returncode == 0, (stdout, stderr, acknowledgements)
        assert '"result": "committed"' in stdout, stdout
        committed_at = time.monotonic()
        pump(0.6)
        pump(0.8)
        for robot_id in ROBOT_IDS:
            assert any(abs(x) + abs(y) + abs(w) > 1e-4 for t, x, y, w in commands[robot_id] if t >= committed_at)
        pump(3.0)
        for robot_id in ROBOT_IDS:
            recent = commands[robot_id][-5:]
            assert recent and all(abs(x) + abs(y) + abs(w) <= 1e-6 for _, x, y, w in recent), (robot_id, recent)
    finally:
        if coordinator is not None and coordinator.poll() is None:
            coordinator.terminate()
        for process in agents:
            process.terminate()
        for process in agents:
            process.wait(timeout=5)
        del subscriptions
        node.destroy_node()
        rclpy.shutdown()
    print("coordinator_integration_ok")


if __name__ == "__main__":
    main()
