# Architecture

Three computers, three jobs. The ESP32 drives motors and reads the IMU. The onboard host board runs the ROS 2 stack. The Mac watches, visualizes, and occasionally shouts `cmd_vel` over WiFi.

## System overview

```mermaid
flowchart LR
    subgraph ROVER["🚗 WAVE ROVER (192.168.4.1 / UART)"]
        subgraph ESP["ESP32 · stock Waveshare firmware"]
            IMU["9-axis IMU + 3S battery monitor"]
            OLED["OLED status / T:3 text"]
            MOTORS["4× DC motors"]
        end
        subgraph HOST["Mac (Stage 1 Wi-Fi) / Onboard host (UART) · ROS 2 Jazzy"]
            BASE["wave_rover_base<br/>HTTP + Serial JSON bridge"]
            LIDAR["LD19 / D500 driver<br/>/scan"]
            CAM["stereo camera driver<br/>depth + /points"]
            EKF["robot_localization<br/>EKF"]
            SLAM["slam_toolbox → RTAB-Map"]
            NAV["Nav2"]
        end
    end
    subgraph MAC["Operator · ROS 2 tools"]
        VIZ["Foxglove / RViz"]
        TELEOP["teleop_twist_keyboard"]
    end

    MOTORS <-->|"T:1 JSON (HTTP or UART)"| BASE
    OLED <-->|"T:3 / T:-3"| BASE
    IMU -->|"T:126 / T:130"| BASE
    BASE -->|"/imu/data_raw + /battery_state"| EKF
    LIDAR --> SLAM
    CAM --> SLAM
    EKF -->|"/odometry/filtered"| SLAM
    EKF --> NAV
    SLAM --> NAV
    NAV -->|"/cmd_vel"| BASE
    TELEOP -->|"/cmd_vel"| BASE
    HOST <-.->|"topics over WiFi"| VIZ
```

## Frame tree (tf2)

A classic REP-105 tree. `map` is the SLAM-anchored world frame; `odom` drifts smoothly; `base_link` is the rover; sensors hang off it with measured static transforms.

```mermaid
flowchart TB
    MAP["map"] -->|SLAM / localization| ODOM["odom"]
    ODOM -->|"EKF (robot_localization)"| BASELINK["base_link"]
    BASELINK -->|static: mast offset| LASER["laser (LD19)"]
    BASELINK -->|static: front mount| CAMLEFT["camera_left"]
    BASELINK -->|static: front mount| CAMRIGHT["camera_right"]
    BASELINK -->|from ESP32| IMUFRAME["imu_link"]
```

## Design rules

- **The ESP32 is a motor controller, nothing more.** Stock firmware, JSON commands in, telemetry out. No re-flashing unless a stage truly needs it.
- **All smarts live in ROS 2 Jazzy** on the onboard host board: drivers, EKF, SLAM, Nav2.
- **The Mac is a spectator with a remote.** Visualization and teleop over WiFi; the rover must keep doing sensible things if WiFi drops.
- **Frames are measured, not guessed.** Every `static_transform` in `wave_rover_description` comes off a ruler or calipers.
