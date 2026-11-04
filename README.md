# horaceTheCheese 🧀

**A WAVE ROVER × ROS 2 project — a little rover that maps the world.**

<p align="center">
  <img src="docs/assets/rover.svg" alt="horace the rover — red body, black wheels, binocular eyes, blue LiDAR on a yellow mast" width="360">
</p>

[![Docs](https://img.shields.io/badge/docs-palolz.github.io%2FhoraceTheCheese-2B5FAB?style=for-the-badge&logo=materialformkdocs&logoColor=white)](https://palolz.github.io/horaceTheCheese/)
[![Deploy](https://github.com/palolz/horaceTheCheese/actions/workflows/deploy.yml/badge.svg)](https://github.com/palolz/horaceTheCheese/actions/workflows/deploy.yml)
[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-E4402A?style=for-the-badge&logo=ros&logoColor=white)](https://docs.ros.org/en/jazzy/)

horaceTheCheese is a documented robotics build: a [Waveshare WAVE ROVER](https://www.waveshare.com/wiki/WAVE_ROVER) 4WD chassis, a ROS 2 Jazzy control stack, an LD19 LiDAR, and a binocular depth camera — all the way from first motor spin to full SLAM and autonomy. The ESP32 onboard stays on its stock firmware and is used purely for motor control; everything else runs in ROS 2 on an onboard host board, with a Mac watching over WiFi.

📖 **Full documentation, stage notes, and build log: [palolz.github.io/horaceTheCheese](https://palolz.github.io/horaceTheCheese/)**

## The six-stage roadmap

| # | Stage | What "done" looks like |
| --- | --- | --- |
| 1 | **Chassis & motor control** | ROS 2 ↔ ESP32 JSON bridge over UART; keyboard teleop drives a commanded square |
| 2 | **LiDAR bring-up** | LD19 publishing `/scan`; first 2D map with slam_toolbox |
| 3 | **Binocular depth** | Stereo camera streaming depth images + point clouds over WiFi |
| 4 | **Sensor fusion** | `robot_localization` EKF fusing IMU + wheel odometry, drift measured and tamed |
| 5 | **Full SLAM** | RTAB-Map fusing LiDAR + vision into a persistent, loop-closing map |
| 6 | **Autonomy** | Nav2 goal following: click the map, the rover drives there |

## Repo layout

```
docs/   MkDocs documentation site (the GitHub Pages source)
ros2/   ROS 2 workspace skeleton — packages arrive with each stage
```

## Design language

Simple, elegant, primary colors, retro — like a late seventies toy. Warm cream `#F6EFE2`, soft-black ink `#211D15`, red `#E4402A`, blue `#2B5FAB`, yellow `#F2B417`. Fredoka for headings, Space Grotesk for body, Space Mono for labels.
