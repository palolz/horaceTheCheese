"""ROS 2 Jazzy bridge node for the Waveshare WAVE ROVER (HTTP and UART JSON)."""

from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, Optional

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from sensor_msgs.msg import BatteryState, Imu
from std_msgs.msg import String
from std_srvs.srv import Trigger

from wave_rover_base.protocol import (
    HttpRoverTransport,
    SerialRoverTransport,
    euler_deg_to_quaternion,
    make_chassis_info_query_cmd,
    make_imu_query_cmd,
    make_oled_cmd,
    make_oled_restore_cmd,
    make_speed_cmd,
    make_stop_cmd,
    parse_oled_string,
    twist_to_wheel_commands,
)


class WaveRoverBridgeNode(Node):
    """Bridges ROS 2 /cmd_vel, telemetry, and OLED control to the WAVE ROVER ESP32."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__("wave_rover_base", **kwargs)

        # Transport parameters
        self.declare_parameter("transport", "http")
        self.declare_parameter("host", "192.168.4.1")
        self.declare_parameter("http_port", 80)
        self.declare_parameter("http_timeout", 0.4)
        self.declare_parameter("port", "/dev/cu.usbserial-0001")
        self.declare_parameter("baudrate", 115200)

        # Control & safety parameters
        self.declare_parameter("speed_scale", 0.5)
        self.declare_parameter("turn_gain", 0.25)
        self.declare_parameter("max_wheel_cmd", 0.5)
        self.declare_parameter("cmd_rate_hz", 10.0)
        self.declare_parameter("watchdog_timeout_sec", 0.5)
        self.declare_parameter("telemetry_rate_hz", 2.0)
        self.declare_parameter("oled_text", "")

        self.transport_mode = str(self.get_parameter("transport").value).lower()
        self.speed_scale = float(self.get_parameter("speed_scale").value)
        self.turn_gain = float(self.get_parameter("turn_gain").value)
        self.max_wheel_cmd = float(self.get_parameter("max_wheel_cmd").value)
        self.cmd_rate_hz = float(self.get_parameter("cmd_rate_hz").value)
        self.watchdog_timeout_sec = float(self.get_parameter("watchdog_timeout_sec").value)
        self.telemetry_rate_hz = float(self.get_parameter("telemetry_rate_hz").value)

        self.transport = self._create_transport()

        # State tracking for 10 Hz heartbeat and 0.5 s watchdog
        self._target_left: float = 0.0
        self._target_right: float = 0.0
        self._last_cmd_time: Optional[rclpy.time.Time] = None
        self._is_stopped: bool = True

        # Publishers
        self.imu_pub = self.create_publisher(Imu, "/imu/data_raw", 10)
        self.battery_pub = self.create_publisher(BatteryState, "/battery_state", 10)
        self.telemetry_raw_pub = self.create_publisher(String, "/rover/telemetry_raw", 10)

        # Subscribers
        self.cmd_vel_sub = self.create_subscription(Twist, "/cmd_vel", self._on_cmd_vel, 10)
        self.oled_sub = self.create_subscription(String, "/rover/oled_text", self._on_oled_text, 10)

        # Services
        self.reset_oled_srv = self.create_service(Trigger, "/rover/reset_oled", self._on_reset_oled)
        self.estop_srv = self.create_service(Trigger, "/rover/emergency_stop", self._on_emergency_stop)

        # Dynamic parameter callback (supports `ros2 param set /wave_rover_base oled_text "HORACE LIVES"`)
        self.add_on_set_parameters_callback(self._on_parameters_set)

        # Optional initial OLED greeting
        initial_oled = str(self.get_parameter("oled_text").value).strip()
        if initial_oled:
            self._safe_send(parse_oled_string(initial_oled))

        # Timers: 10 Hz motor stream + watchdog, and telemetry poller
        cmd_period = 1.0 / max(self.cmd_rate_hz, 1.0)
        self.cmd_timer = self.create_timer(cmd_period, self._on_cmd_timer)

        if self.telemetry_rate_hz > 0.0:
            tel_period = 1.0 / self.telemetry_rate_hz
            self.telemetry_timer = self.create_timer(tel_period, self._on_telemetry_timer)
        else:
            self.telemetry_timer = None

        self.get_logger().info(
            f"wave_rover_base ready (transport={self.transport_mode}, "
            f"rate={self.cmd_rate_hz:.1f}Hz, watchdog={self.watchdog_timeout_sec:.2f}s)"
        )

    def _create_transport(self):
        if self.transport_mode == "http":
            host = str(self.get_parameter("host").value)
            http_port = int(self.get_parameter("http_port").value)
            timeout = float(self.get_parameter("http_timeout").value)
            self.get_logger().info(f"Using HTTP transport -> http://{host}:{http_port}/js?json=...")
            return HttpRoverTransport(host=host, port=http_port, timeout=timeout)
        if self.transport_mode == "serial":
            port = str(self.get_parameter("port").value)
            baudrate = int(self.get_parameter("baudrate").value)
            self.get_logger().info(f"Using Serial UART transport -> {port} @ {baudrate} baud")
            return SerialRoverTransport(port=port, baudrate=baudrate)
        raise ValueError(f"Unsupported transport '{self.transport_mode}'; expected 'http' or 'serial'")

    def _safe_send(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            return self.transport.send_command(payload)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warning(
                f"Transport error sending {payload}: {exc}",
                throttle_duration_sec=2.0,
            )
            return None

    def _on_cmd_vel(self, msg: Twist) -> None:
        left, right = twist_to_wheel_commands(
            linear_x=msg.linear.x,
            angular_z=msg.angular.z,
            speed_scale=self.speed_scale,
            turn_gain=self.turn_gain,
            max_wheel_cmd=self.max_wheel_cmd,
        )
        self._target_left = left
        self._target_right = right
        self._last_cmd_time = self.get_clock().now()
        self._is_stopped = (left == 0.0 and right == 0.0)
        self._safe_send(make_speed_cmd(left, right))

    def _on_cmd_timer(self) -> None:
        if self._last_cmd_time is None:
            return

        elapsed = (self.get_clock().now() - self._last_cmd_time).nanoseconds * 1e-9
        if elapsed > self.watchdog_timeout_sec:
            if not self._is_stopped:
                self.get_logger().info(
                    f"/cmd_vel watchdog timeout ({elapsed:.2f}s > {self.watchdog_timeout_sec:.2f}s) -> stopping motors"
                )
                self._target_left = 0.0
                self._target_right = 0.0
                self._is_stopped = True
                self._safe_send(make_stop_cmd())
            return

        # Keep streaming active command at 10 Hz so the ESP32 3-second heartbeat stays alive
        if not self._is_stopped:
            self._safe_send(make_speed_cmd(self._target_left, self._target_right))

    def _on_telemetry_timer(self) -> None:
        imu_data = self._safe_send(make_imu_query_cmd())
        if isinstance(imu_data, dict):
            self._publish_imu(imu_data)

        chassis_data = self._safe_send(make_chassis_info_query_cmd())
        if isinstance(chassis_data, dict):
            self._publish_battery(chassis_data)

        if imu_data or chassis_data:
            raw_msg = String()
            raw_msg.data = json.dumps({"imu": imu_data, "chassis": chassis_data})
            self.telemetry_raw_pub.publish(raw_msg)

    def _publish_imu(self, data: Dict[str, Any]) -> None:
        if not any(k in data for k in ("r", "p", "y", "ax", "ay", "az", "gx", "gy", "gz")):
            return
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"

        roll = float(data.get("r", 0.0))
        pitch = float(data.get("p", 0.0))
        yaw = float(data.get("y", 0.0))
        qx, qy, qz, qw = euler_deg_to_quaternion(roll, pitch, yaw)
        msg.orientation.x = qx
        msg.orientation.y = qy
        msg.orientation.z = qz
        msg.orientation.w = qw

        # Convert deg/s -> rad/s and mG/g -> m/s^2 if present
        msg.angular_velocity.x = math.radians(float(data.get("gx", 0.0)))
        msg.angular_velocity.y = math.radians(float(data.get("gy", 0.0)))
        msg.angular_velocity.z = math.radians(float(data.get("gz", 0.0)))

        msg.linear_acceleration.x = float(data.get("ax", 0.0))
        msg.linear_acceleration.y = float(data.get("ay", 0.0))
        msg.linear_acceleration.z = float(data.get("az", 0.0))
        self.imu_pub.publish(msg)

    def _publish_battery(self, data: Dict[str, Any]) -> None:
        voltage = data.get("v", data.get("V"))
        if voltage is None:
            return
        msg = BatteryState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.voltage = float(voltage)
        msg.present = True
        self.battery_pub.publish(msg)

    def _on_oled_text(self, msg: String) -> None:
        cmd = parse_oled_string(msg.data)
        self._safe_send(cmd)

    def _on_reset_oled(self, _request: Trigger.Request, response: Trigger.Response) -> Trigger.Response:
        self._safe_send(make_oled_restore_cmd())
        response.success = True
        response.message = "Restored default OLED status screen (T:-3)"
        return response

    def _on_emergency_stop(self, _request: Trigger.Request, response: Trigger.Response) -> Trigger.Response:
        self._target_left = 0.0
        self._target_right = 0.0
        self._is_stopped = True
        self._safe_send(make_stop_cmd())
        response.success = True
        response.message = "Sent emergency stop (T:1, L:0, R:0)"
        return response

    def _on_parameters_set(self, params) -> SetParametersResult:
        for param in params:
            if param.name == "oled_text":
                cmd = parse_oled_string(str(param.value))
                self._safe_send(cmd)
            elif param.name == "speed_scale":
                self.speed_scale = float(param.value)
            elif param.name == "turn_gain":
                self.turn_gain = float(param.value)
        return SetParametersResult(successful=True)

    def stop_rover(self) -> None:
        """Send an immediate zero-speed command before shutting down."""
        self._target_left = 0.0
        self._target_right = 0.0
        self._is_stopped = True
        try:
            self.transport.send_command(make_stop_cmd())
        except Exception:  # noqa: BLE001
            pass
        finally:
            self.transport.close()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = WaveRoverBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_rover()
        os._exit(0)



if __name__ == "__main__":
    main()
