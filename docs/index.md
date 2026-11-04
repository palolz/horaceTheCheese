---
hide:
  - toc
---

<div class="htc-hero" markdown>
<div class="htc-hero__text" markdown>
<span class="htc-kicker">A WAVE ROVER × ROS 2 project</span>

# A little rover that maps the world.

horaceTheCheese is a documented robotics build: a Waveshare WAVE ROVER 4WD chassis, a ROS 2 control stack, an LD19 LiDAR, and a binocular depth camera — all the way from first motor spin to full SLAM and autonomy.

[See the stages](stages/index.md){ .htc-btn .htc-btn--red }
[Architecture](architecture.md){ .htc-btn }
[Build log](build-log.md){ .htc-btn .htc-btn--yellow }

</div>
<div class="htc-hero__art" markdown>
![horace the rover — red body, black wheels, binocular eyes, blue LiDAR on a yellow mast](assets/rover.svg)
</div>
</div>

## The six stages

<div class="htc-grid" markdown>
<div class="htc-card" markdown>
<span class="htc-card__num">1</span>

### Chassis & motor control

ROS 2 ↔ ESP32 JSON bridge over UART. Keyboard teleop. First spin.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">2</span>

### LiDAR bring-up

LD19 publishing `/scan`. First 2D map with slam_toolbox.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">3</span>

### Binocular depth

Stereo camera streaming depth images and point clouds over WiFi.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">4</span>

### Sensor fusion

robot_localization EKF fusing IMU and wheel odometry.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">5</span>

### Full SLAM

RTAB-Map fusing LiDAR and vision into one live map.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">6</span>

### Autonomy

Nav2 goal following. Point at the map; horace goes there.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>
</div>

## The cast

| Piece | Role | Status |
| --- | --- | --- |
| WAVE ROVER 4WD chassis | Motors + ESP32 running stock Waveshare firmware | On hand |
| LD19 LiDAR | 2D scans for SLAM | Ordered |
| Binocular stereo camera | Depth images + point clouds | Ordered |
| Onboard host board | Runs the ROS 2 Jazzy stack | TBD |

Full shopping list lives on the [Hardware & BOM](hardware.md) page.
