"""ROS integration test in domains 94/95, which contain no real robot nodes."""

import json
import math
import os
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import rclpy
from geometry_msgs.msg import Twist
from rclpy.context import Context
from rclpy.executors import SingleThreadedExecutor
from ros_robot_controller_msgs.msg import MotorsState
from std_msgs.msg import String


def main():
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="formation-command-test-") as temp:
        config = Path(temp) / "config.json"
        lease = Path(temp) / "lease.json"
        config.write_text('{"hardware_output_enabled":true}')
        bridge = subprocess.Popen([
            sys.executable, str(root / "command_bridge.py"), "--robot", "robot1",
            "--local-domain", "95", "--fleet-domain", "94",
            "--config", str(config), "--lease", str(lease),
        ], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        fleet_context, local_context = Context(), Context()
        rclpy.init(context=fleet_context, domain_id=94)
        rclpy.init(context=local_context, domain_id=95)
        agent = rclpy.create_node("formation_agent_robot1", context=fleet_context)
        observer = rclpy.create_node("command_test_observer", context=local_context)
        driver = rclpy.create_node("odom_publisher", context=local_context)
        command_pub = agent.create_publisher(Twist, "/robot1/controller/cmd_vel", 10)
        status_pub = agent.create_publisher(String, "/formation/agent_status", 10)
        conflict_pub = observer.create_publisher(Twist, "/controller/cmd_vel", 10)
        driver.create_publisher(MotorsState, "/ros_robot_controller/set_motor", 10)
        outputs = []
        statuses = []
        observer.create_subscription(Twist, "/cmd_vel", lambda msg: outputs.append((time.monotonic(), msg.linear.x, msg.linear.y, msg.angular.z)), 10)
        agent.create_subscription(String, "/robot1/formation/command_bridge_status", lambda msg: statuses.append(json.loads(msg.data)), 10)
        fleet_executor = SingleThreadedExecutor(context=fleet_context)
        local_executor = SingleThreadedExecutor(context=local_context)
        fleet_executor.add_node(agent)
        local_executor.add_node(observer)
        local_executor.add_node(driver)

        def spin(seconds, publish=False):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                if publish:
                    cmd = Twist()
                    cmd.linear.x = 0.4
                    cmd.angular.z = 0.8
                    command_pub.publish(cmd)
                    status = String()
                    status.data = json.dumps({"robot_id": "robot1", "experiment_id": "isolated-test", "safe": True, "reason": "tracking"})
                    status_pub.publish(status)
                fleet_executor.spin_once(timeout_sec=0.025)
                local_executor.spin_once(timeout_sec=0.025)

        def arm():
            lease.write_text(json.dumps({"robot": "robot1", "id": str(uuid.uuid4()), "expires_mono": time.monotonic() + 5.0}))

        try:
            spin(3.5, publish=True)
            unarmed_outputs = len(outputs)
            arm()
            spin(1.2, publish=True)
            active_phase_status = statuses[-1] if statuses else None
            moving = [item for item in outputs if abs(item[1]) > 1e-4]
            before_timeout = len(outputs)
            spin(0.8, publish=False)
            watchdog_zero = any(abs(item[1]) < 1e-9 for item in outputs[before_timeout:])
            arm()
            spin(1.2, publish=True)
            conflict_pub.publish(Twist())
            spin(1.2, publish=True)
            conflict_latched = any(item.get("reason") == "competing_controller" for item in statuses[-3:])
            result = {
                "ok": unarmed_outputs == 0 and bool(moving) and watchdog_zero and conflict_latched,
                "unarmed_outputs": unarmed_outputs,
                "moving_output_count": len(moving),
                "active_phase_status": active_phase_status,
                "peak_linear_mps": round(max((math.hypot(item[1], item[2]) for item in moving), default=0.0), 4),
                "peak_yaw_radps": round(max((abs(item[3]) for item in moving), default=0.0), 4),
                "watchdog_zero": watchdog_zero,
                "conflict_latched": conflict_latched,
                "last_status": statuses[-1] if statuses else None,
                "bridge_exit_code": bridge.poll(),
                "bridge_output": bridge.stdout.read() if bridge.poll() is not None else None,
            }
            print(json.dumps(result, indent=2), flush=True)
            return 0 if result["ok"] else 2
        finally:
            bridge.terminate()
            try:
                bridge.wait(timeout=3)
            except subprocess.TimeoutExpired:
                bridge.kill()
                bridge.wait()
            fleet_executor.remove_node(agent)
            local_executor.remove_node(observer)
            local_executor.remove_node(driver)
            agent.destroy_node()
            observer.destroy_node()
            driver.destroy_node()
            rclpy.shutdown(context=fleet_context)
            rclpy.shutdown(context=local_context)


if __name__ == "__main__":
    raise SystemExit(main())
