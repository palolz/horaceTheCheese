"""Pure protocol and transport helpers for the Waveshare WAVE ROVER ESP32."""

from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def twist_to_wheel_commands(
    linear_x: float,
    angular_z: float,
    speed_scale: float = 1.0,
    turn_gain: float = 0.25,
    max_wheel_cmd: float = 0.5,
) -> Tuple[float, float]:
    """Convert ROS 2 Twist (linear.x, angular.z) into WAVE ROVER L/R speeds in [-0.5, 0.5]."""
    left = linear_x * speed_scale - angular_z * turn_gain
    right = linear_x * speed_scale + angular_z * turn_gain
    left = round(clamp(left, -max_wheel_cmd, max_wheel_cmd), 3)
    right = round(clamp(right, -max_wheel_cmd, max_wheel_cmd), 3)
    # Eliminate -0.0
    if left == 0.0:
        left = 0.0
    if right == 0.0:
        right = 0.0
    return left, right


def make_speed_cmd(left: float, right: float) -> Dict[str, Any]:
    """T=1: direct left/right wheel speed command in [-0.5, 0.5]."""
    return {"T": 1, "L": left, "R": right}


def make_stop_cmd() -> Dict[str, Any]:
    """T=1 with L=0, R=0 immediately stops both motor channels."""
    return {"T": 1, "L": 0, "R": 0}


def make_oled_cmd(line_num: int, text: str) -> Dict[str, Any]:
    """T=3: write a custom text line (0..3) to the rover's OLED screen."""
    return {"T": 3, "lineNum": int(clamp(line_num, 0, 3)), "Text": str(text)}


def make_oled_restore_cmd() -> Dict[str, Any]:
    """T=-3: restore the default Waveshare status display on the OLED."""
    return {"T": -3}


def make_imu_query_cmd() -> Dict[str, Any]:
    """T=126: fetch IMU orientation/acceleration/gyro telemetry."""
    return {"T": 126}


def make_chassis_info_query_cmd() -> Dict[str, Any]:
    """T=130: fetch chassis battery voltage and status telemetry."""
    return {"T": 130}


def parse_oled_string(raw: str) -> Dict[str, Any]:
    """Parse an OLED topic string ('reset'/'clear', '2:HELLO', or 'HORACE LIVES') into a command."""
    stripped = raw.strip()
    if not stripped or stripped.lower() in {"reset", "clear", "default", "-3"}:
        return make_oled_restore_cmd()
    if ":" in stripped and stripped.split(":", 1)[0].isdigit():
        line_str, text = stripped.split(":", 1)
        return make_oled_cmd(int(line_str), text)
    return make_oled_cmd(0, stripped)


def euler_deg_to_quaternion(roll_deg: float, pitch_deg: float, yaw_deg: float) -> Tuple[float, float, float, float]:
    """Convert Euler angles (degrees) to quaternion (x, y, z, w)."""
    roll = math.radians(roll_deg)
    pitch = math.radians(pitch_deg)
    yaw = math.radians(yaw_deg)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    return x, y, z, w


class HttpRoverTransport:
    """HTTP transport talking to `http://<host>/js?json=...`."""

    def __init__(self, host: str = "192.168.4.1", port: int = 80, timeout: float = 0.4) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    @property
    def base_url(self) -> str:
        if self.port == 80:
            return f"http://{self.host}/js"
        return f"http://{self.host}:{self.port}/js"

    def send_command(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        compact = json.dumps(payload, separators=(",", ":"))
        encoded = urllib.parse.quote(compact, safe='{},:"')
        url = f"{self.base_url}?json={encoded}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace").strip()
            if not body:
                return None
            try:
                parsed = json.loads(body)
                return parsed if isinstance(parsed, dict) else {"raw": body}
            except json.JSONDecodeError:
                return {"raw": body}

    def close(self) -> None:
        pass


class SerialRoverTransport:
    """UART / USB-serial transport sending newline-delimited JSON to the ESP32."""

    def __init__(self, port: str = "/dev/cu.usbserial-0001", baudrate: int = 115200, timeout: float = 0.1) -> None:
        import serial  # Lazy import so HTTP mode works even without pyserial

        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)

    def send_command(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        line = json.dumps(payload, separators=(",", ":")) + "\n"
        self._serial.write(line.encode("utf-8"))
        self._serial.flush()
        if payload.get("T") in (126, 130):
            raw = self._serial.readline().decode("utf-8", errors="replace").strip()
            if raw:
                try:
                    parsed = json.loads(raw)
                    return parsed if isinstance(parsed, dict) else {"raw": raw}
                except json.JSONDecodeError:
                    return {"raw": raw}
        return None

    def close(self) -> None:
        if getattr(self, "_serial", None) is not None and self._serial.is_open:
            self._serial.close()
