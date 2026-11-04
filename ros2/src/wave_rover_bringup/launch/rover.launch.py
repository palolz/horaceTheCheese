"""Launch wave_rover_base with HTTP (Wi-Fi AP / STA) or Serial UART transport."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "transport",
                default_value="http",
                description="Transport mode: 'http' (Wi-Fi GET /js?json=...) or 'serial' (UART JSON)",
            ),
            DeclareLaunchArgument(
                "host",
                default_value="192.168.4.1",
                description="WAVE ROVER IP address when transport:=http (192.168.4.1 on UGV AP)",
            ),
            DeclareLaunchArgument(
                "http_port",
                default_value="80",
                description="HTTP port on the WAVE ROVER ESP32 (default 80)",
            ),
            DeclareLaunchArgument(
                "port",
                default_value="/dev/cu.usbserial-0001",
                description="Serial device path when transport:=serial",
            ),
            DeclareLaunchArgument(
                "baudrate",
                default_value="115200",
                description="Serial baudrate when transport:=serial (default 115200)",
            ),
            DeclareLaunchArgument(
                "speed_scale",
                default_value="0.5",
                description="Scale factor mapping Twist linear.x (m/s) to T:1 wheel command [-0.5, 0.5]",
            ),
            DeclareLaunchArgument(
                "turn_gain",
                default_value="0.25",
                description="Differential steering gain mapping Twist angular.z (rad/s) to wheel delta",
            ),
            DeclareLaunchArgument(
                "oled_text",
                default_value="HORACE LIVES",
                description="Initial text written to OLED line 0 on startup (empty string to skip)",
            ),
            Node(
                package="wave_rover_base",
                executable="rover_bridge",
                name="wave_rover_base",
                output="screen",
                parameters=[
                    {
                        "transport": LaunchConfiguration("transport"),
                        "host": LaunchConfiguration("host"),
                        "http_port": LaunchConfiguration("http_port"),
                        "port": LaunchConfiguration("port"),
                        "baudrate": LaunchConfiguration("baudrate"),
                        "speed_scale": LaunchConfiguration("speed_scale"),
                        "turn_gain": LaunchConfiguration("turn_gain"),
                        "oled_text": LaunchConfiguration("oled_text"),
                    }
                ],
            ),
        ]
    )
