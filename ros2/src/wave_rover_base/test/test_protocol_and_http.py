"""Unit and local mock HTTP server integration tests for wave_rover_base."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import time
import urllib.parse

from geometry_msgs.msg import Twist
import rclpy

from wave_rover_base.protocol import (
    HttpRoverTransport,
    make_oled_cmd,
    make_oled_restore_cmd,
    make_speed_cmd,
    make_stop_cmd,
    parse_oled_string,
    twist_to_wheel_commands,
)
from wave_rover_base.rover_bridge_node import WaveRoverBridgeNode


class _MockRoverHandler(BaseHTTPRequestHandler):
    received_commands = []

    def do_GET(self):  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        raw_json = qs.get("json", ["{}"])[0]
        cmd = json.loads(raw_json)
        self.__class__.received_commands.append(cmd)

        if cmd.get("T") == 126:
            body = json.dumps({"T": 126, "r": 1.2, "p": -0.5, "y": 90.0, "ax": 0.0, "ay": 0.0, "az": 9.81})
        elif cmd.get("T") == 130:
            body = json.dumps({"T": 130, "v": 12.39})
        else:
            body = json.dumps({"status": "ok", "echo": cmd})

        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):  # noqa: A002
        pass


def test_twist_to_wheel_commands():
    # Straight forward
    assert twist_to_wheel_commands(0.5, 0.0, speed_scale=0.5, turn_gain=0.25) == (0.25, 0.25)
    # In-place left turn (angular_z > 0 -> right wheel forward, left wheel backward)
    assert twist_to_wheel_commands(0.0, 1.0, speed_scale=0.5, turn_gain=0.25) == (-0.25, 0.25)
    # Clamping to [-0.5, 0.5]
    assert twist_to_wheel_commands(2.0, 0.0, speed_scale=1.0, turn_gain=0.25) == (0.5, 0.5)
    assert twist_to_wheel_commands(-2.0, 0.0, speed_scale=1.0, turn_gain=0.25) == (-0.5, -0.5)


def test_oled_helpers():
    assert make_oled_cmd(0, "HORACE LIVES") == {"T": 3, "lineNum": 0, "Text": "HORACE LIVES"}
    assert make_oled_restore_cmd() == {"T": -3}
    assert parse_oled_string("HORACE LIVES") == {"T": 3, "lineNum": 0, "Text": "HORACE LIVES"}
    assert parse_oled_string("2:V: 12.39") == {"T": 3, "lineNum": 2, "Text": "V: 12.39"}
    assert parse_oled_string("reset") == {"T": -3}
    assert make_stop_cmd() == {"T": 1, "L": 0, "R": 0}
    assert make_speed_cmd(0.25, 0.25) == {"T": 1, "L": 0.25, "R": 0.25}


def test_end_to_end_ros2_node_with_mock_esp32():
    _MockRoverHandler.received_commands = []
    server = HTTPServer(("127.0.0.1", 0), _MockRoverHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    if not rclpy.ok():
        rclpy.init()
    try:
        from rclpy.parameter import Parameter

        # Spin up WaveRoverBridgeNode pointed at mock ESP32 HTTP server
        # Setting oled_text="HORACE LIVES" verifies startup T:3 OLED command
        node = WaveRoverBridgeNode(
            parameter_overrides=[
                Parameter("transport", Parameter.Type.STRING, "http"),
                Parameter("host", Parameter.Type.STRING, "127.0.0.1"),
                Parameter("http_port", Parameter.Type.INTEGER, port),
                Parameter("watchdog_timeout_sec", Parameter.Type.DOUBLE, 0.2),
                Parameter("oled_text", Parameter.Type.STRING, "HORACE LIVES"),
            ]
        )

        # Simulate incoming /cmd_vel forward command (linear.x = 0.5 -> L=0.25, R=0.25)
        twist = Twist()
        twist.linear.x = 0.5
        twist.angular.z = 0.0
        node._on_cmd_vel(twist)

        # Trigger 10 Hz heartbeat timer while command is fresh
        node._on_cmd_timer()

        # Trigger telemetry poll (T:126 IMU and T:130 battery)
        node._on_telemetry_timer()

        # Wait past watchdog timeout and trigger timer to verify automatic stop (T:1, L:0, R:0)
        time.sleep(0.25)
        node._on_cmd_timer()

        # Verify reset_oled service handler sends T:-3
        from std_srvs.srv import Trigger

        node._on_reset_oled(Trigger.Request(), Trigger.Response())
        node.stop_rover()

        cmds = _MockRoverHandler.received_commands
        assert {"T": 3, "lineNum": 0, "Text": "HORACE LIVES"} in cmds
        assert {"T": 1, "L": 0.25, "R": 0.25} in cmds
        assert {"T": 126} in cmds
        assert {"T": 130} in cmds
        assert {"T": 1, "L": 0, "R": 0} in cmds
        assert {"T": -3} in cmds
    finally:
        server.shutdown()
        server.server_close()

