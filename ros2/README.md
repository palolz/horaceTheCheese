# ros2/ — horaceTheCheese ROS 2 Jazzy workspace

This is the ROS 2 Jazzy workspace for **horaceTheCheese**, supporting both offboard Wi-Fi HTTP control (`GET http://192.168.4.1/js?json=...` on the rover's `UGV` hotspot or station IP) and direct UART/USB serial (`115200` baud newline-delimited JSON).

## Packages

| Package | Status | Purpose |
| --- | --- | --- |
| `wave_rover_base` | **Done (Stage 1)** | Dual-transport (`http` + `serial`) bridge to the ESP32: `/cmd_vel` → `{"T":1,"L":...,"R":...}` at 10 Hz with 0.5 s watchdog auto-stop; `T:126` / `T:130` telemetry → `/imu/data_raw` + `/battery_state`; `T:3` / `T:-3` OLED control |
| `wave_rover_bringup` | **Done (Stage 1)** | Launch file (`rover.launch.py`) and default parameter config (`wave_rover.yaml`) |
| `wave_rover_description` | Planned (Stage 2–3) | URDF/xacro model: chassis, wheels, mast, measured sensor frames (`laser`, `camera_left/right`, `imu_link`) |

## Build & run

```bash
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate ros_jazzy
cd ros2
colcon build
source install/setup.bash

# Launch over Wi-Fi HTTP (default: rover AP at 192.168.4.1)
ros2 launch wave_rover_bringup rover.launch.py transport:=http host:=192.168.4.1

# Or launch over USB/UART serial
ros2 launch wave_rover_bringup rover.launch.py transport:=serial port:=/dev/cu.usbserial-0001 baudrate:=115200
```

In a second terminal, drive with `teleop_twist_keyboard`:

```bash
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate ros_jazzy
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Run tests (no rover Wi-Fi connection required)

```bash
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate ros_jazzy
cd ros2
source install/setup.bash
pytest src/wave_rover_base/test/test_protocol_and_http.py -v
```

