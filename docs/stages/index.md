# Stages

The build is chopped into six stages, each ending with something you can *see* the rover do. Every stage gets its own page with goals, notes, wiring, and the inevitable things that went wrong.

<div class="htc-grid" markdown>
<div class="htc-card" markdown>
<span class="htc-card__num">1</span>

### [Chassis & motor control](stage-1-chassis.md)

ROS 2 talks JSON to the stock ESP32 firmware over Wi-Fi HTTP and UART. `HORACE LIVES` on the OLED and keyboard teleop verified.

<span class="htc-badge htc-badge--done">Done</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">2</span>

### [LiDAR bring-up](stage-2-lidar.md)

LD19 scans hit `/scan`; slam_toolbox draws the first map.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">3</span>

### [Binocular depth](stage-3-depth.md)

`95 × 20 mm` stereo camera (`80.0 mm` baseline) housed in a 3D-printable retro visor + 90° bracket mount with Mini-USB strain relief.

<span class="htc-badge htc-badge--progress">In progress · CAD ready</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">4</span>

### [Sensor fusion](stage-4-fusion.md)

An EKF fuses IMU and wheel odometry into one believable pose.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">5</span>

### [Full SLAM](stage-5-slam.md)

RTAB-Map combines LiDAR and vision into a persistent map.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>

<div class="htc-card" markdown>
<span class="htc-card__num">6</span>

### [Autonomy](stage-6-autonomy.md)

Nav2 goal following on the maps from stage 5.

<span class="htc-badge htc-badge--planned">Planned</span>
</div>
</div>

!!! note "How stages work"
    A stage is **Done** when its demo runs end-to-end and the page shows the proof (video, rosbag, map screenshot). Until then it wears its yellow or cream badge with pride.
