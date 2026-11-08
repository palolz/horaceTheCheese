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

### [Chassis & motor control](stages/stage-1-chassis.md)

ROS 2 ↔ ESP32 JSON bridge over Wi-Fi HTTP & UART. `HORACE LIVES` on the OLED, keyboard teleop, and first wheel spin.

<span class="htc-badge htc-badge--done">Done</span>
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
| WAVE ROVER 4WD chassis | Motors + ESP32 running stock Waveshare firmware (`AP:UGV`, `12.39 V`) | <span class="htc-badge htc-badge--done">Done · Rolling</span> |
| LDROBOT D500 LiDAR Kit (LD19) | 360° 2D laser scans for SLAM | <span class="htc-badge htc-badge--done">On hand</span> |
| Raspberry Pi Zero-class board | Compact Linux companion spotted on the bench | <span class="htc-badge htc-badge--done">On hand</span> |
| Binocular stereo camera | Depth images + point clouds | <span class="htc-badge htc-badge--progress">Ordered</span> |

Full shopping list and real workbench photos live on the [Hardware & BOM](hardware.md) page.

