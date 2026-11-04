# ros2/ — horaceTheCheese ROS 2 workspace

This will become the ROS 2 (Jazzy) workspace that runs on the rover's onboard host board. No code yet — packages land stage by stage, as documented on the [site](https://palolz.github.io/horaceTheCheese/).

## Planned packages

| Package | Arrives in | Purpose |
| --- | --- | --- |
| `wave_rover_base` | Stage 1 | Serial bridge to the ESP32: `/cmd_vel` → JSON motor commands over UART; telemetry → `/odom` + `/imu/data_raw` |
| `wave_rover_description` | Stage 1–3 | URDF/xacro model: chassis, wheels, mast, measured sensor frames (`laser`, `camera_left/right`, `imu_link`) |
| `wave_rover_bringup` | Stage 1+ | Launch files and configs tying drivers, EKF, SLAM, and Nav2 together per stage |

## Layout (target)

```
ros2/
└── src/
    ├── wave_rover_base/
    ├── wave_rover_description/
    └── wave_rover_bringup/
```

Build (once packages exist):

```bash
cd ros2
colcon build
source install/setup.bash
ros2 launch wave_rover_bringup rover.launch.py
```

The ESP32 keeps its stock Waveshare firmware; this workspace never touches it. See the [architecture page](https://palolz.github.io/horaceTheCheese/architecture/) for the full picture.
