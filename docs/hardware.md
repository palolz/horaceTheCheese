# Hardware & BOM

Everything the rover is (or will be) made of. Prices and links get filled in as parts arrive and are benched.

| Part | Role | Source / model | Status |
| --- | --- | --- | --- |
| WAVE ROVER 4WD chassis | Motors, encoders, ESP32, 9-axis IMU, battery | [Waveshare WAVE ROVER](https://www.waveshare.com/wiki/WAVE_ROVER) | <span class="htc-badge htc-badge--done">On hand</span> |
| LD19 LiDAR | 360° 2D scans for SLAM | LDROBOT LD19 | <span class="htc-badge htc-badge--progress">Ordered</span> |
| Binocular stereo camera | Depth images + point clouds | TBD (unit ordered) | <span class="htc-badge htc-badge--progress">Ordered</span> |
| Onboard host board | Runs the ROS 2 Jazzy stack | TBD — one is coming | <span class="htc-badge htc-badge--planned">TBD</span> |
| LiDAR mast + mounts | Yellow mast, printed brackets | 3D-printed, designed in-house | <span class="htc-badge htc-badge--planned">Planned</span> |

## Notes

- **Logic levels:** the ESP32 and the LD19 both speak 3.3 V UART. Level shifting (if the host board's UART is 5 V-tolerant only) goes here once confirmed.
- **Power budget:** host board + LiDAR + camera all sip from the rover's battery. Measured draw per component will land in this table after stage 1.
- **WiFi:** all offboard traffic (Foxglove/RViz, teleop) rides the rover's WiFi link — bandwidth notes accumulate in [stage 3](stages/stage-3-depth.md).

!!! note "Host board TBD"
    The onboard computer hasn't been picked publicly yet. Requirements so far: runs ROS 2 Jazzy comfortably, has enough USB/UART for LiDAR + camera + ESP32, and fits the chassis. This page updates the moment it lands.
