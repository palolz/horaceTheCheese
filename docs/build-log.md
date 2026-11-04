# Build log

Reverse-chronological diary of the build. Newest entry on top.

---

## 2026-11-04 — Stage 1 bring-up: `HORACE LIVES` & first wheel spin <span class="htc-badge htc-badge--done">Done</span>

Horace is officially alive, talking to ROS 2 Jazzy, and spinning all four wheels on command.

<div class="htc-photo-grid">
  <figure class="htc-photo">
    <img src="../assets/hardware/horace-bench-d500.jpg" alt="Horace on the workbench with expansion deck and LDROBOT D500 LiDAR kit">
    <figcaption>Horace on the bench with its metal mounting deck and the LDROBOT D500 LiDAR Kit box ready in the background.</figcaption>
  </figure>
  <figure class="htc-photo">
    <img src="../assets/hardware/oled-ap-ugv.jpg" alt="OLED screen showing AP:UGV, ST: OFF, MAC:XX:XX:XX:XX:XX:XX, V:12.39">
    <figcaption>Mystery solved: newer Waveshare firmware boots SSID <code>UGV</code> (not <code>WAVE_ROVER</code>), showing <code>V:12.39</code> on the 3S pack.</figcaption>
  </figure>
</div>

**What happened:**

- **ROS 2 Jazzy on Apple Silicon:** Installed Miniforge + RoboStack (`robostack-jazzy`) natively on `osx-arm64` (`ros-jazzy-ros-base`, `ros-jazzy-teleop-twist-keyboard`, `colcon-common-extensions`).
- **Cracked the Wi-Fi SSID Plot Twist:** Scanning for `WAVE_ROVER` came up empty because newer General Driver for Robots firmware broadcasts **`AP:UGV`** (`192.168.4.1`, MAC `XX:XX:XX:XX:XX:XX`, battery `12.39 V`), which was right there on the OLED the whole time.
- **Verified HTTP JSON Control & First Motion:**
    - Sent `GET http://192.168.4.1/js?json={"T":3,"lineNum":0,"Text":"HORACE LIVES"}` → `HTTP/1.1 200 OK` and printed `HORACE LIVES` across line 0 of the OLED.
    - Sent `{"T":1,"L":0.25,"R":0.25}` → spun both left and right wheel pairs forward smoothly, followed by `{"T":1,"L":0,"R":0}` to stop and `{"T":-3}` to restore the status OLED.
- **Documented the UniFi Wi-Fi 7 (`T:404`) Gotcha:** The ESP32's 2.4 GHz radio won't associate with a WPA3 / PMF-enabled Wi-Fi 7 SSID; station mode requires a 2.4 GHz WPA2-PSK SSID with PMF disabled.
- **Built `wave_rover_base` + `wave_rover_bringup`:** Implemented the dual-transport (`transport:=http` and `transport:=serial`) ROS 2 bridge in `ros2/src/`, complete with a 10 Hz heartbeat stream (keeping the ESP32's 3-second watchdog alive), a 0.5 s `/cmd_vel` watchdog auto-stop, `T:126` / `T:130` telemetry polling, and `T:3` / `T:-3` OLED control, verified against an automated mock-ESP32 HTTP test suite.

**Next up:** Stage 2 — unboxing that **LDROBOT D500 LiDAR Kit** sitting on the bench, bolting down the metal expansion plate, and streaming `/scan` into `slam_toolbox`.

---

## 2026-11-04 — The scaffold <span class="htc-badge htc-badge--done">Done</span>

The site you're reading is the first artifact of the project: a MkDocs Material build with a custom "late seventies toy" theme — cream paper, soft-black ink, primary red/blue/yellow, chunky borders, and hard offset shadows.

**What happened:**

- Scaffolded the full site: home, six stage pages, architecture, hardware/BOM, and this build log.
- Drew the brand artwork as flat SVG: the red rover with black wheels, binocular eyes, and a blue LiDAR on a yellow mast, plus the cheese-wedge mark.
- Wired Mermaid diagram support for the architecture pages.
- Set up GitHub Actions to deploy to GitHub Pages on every push to `main`.

**Next up:** stage 1 — the ESP32 serial bridge and first motor spins, as soon as the onboard host board lands.
