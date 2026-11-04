# Stage 1 · Chassis & motor control <span class="htc-badge htc-badge--planned">Planned</span>

Get the WAVE ROVER driving under ROS 2. The onboard ESP32 keeps its stock Waveshare firmware and stays purely in charge of motor control; the host board sends it JSON motor commands over a UART serial link.

## Goals

- [ ] Host board wired to the ESP32's UART header (3.3 V logic — check levels!)
- [ ] `wave_rover_base` node publishing JSON velocity commands (`{"T":13,"X":...,"Z":...}`) to the serial port
- [ ] `/cmd_vel` → JSON translation, so any standard ROS 2 teleop works
- [ ] Wheel odometry and 9-axis IMU feedback parsed from the ESP32's JSON telemetry
- [ ] Keyboard teleop demo: `ros2 run teleop_twist_keyboard teleop_twist_keyboard`

## The plan

1. Confirm the UART pins and baud rate in the [Waveshare WAVE ROVER wiki](https://www.waveshare.com/wiki/WAVE_ROVER).
2. Write a small serial bridge node (`wave_rover_base`) that owns the port both ways: commands out, telemetry in.
3. Publish `/odom` + `/imu/data_raw` and broadcast `odom → base_link` over tf2.
4. Tune, then drive in circles on purpose. Record everything for the build log.

## Done when

The rover drives a commanded square using only `cmd_vel`, and RViz shows odometry roughly matching the tape measure.

!!! note "Why keep the stock firmware?"
    Waveshare's firmware already handles motor PID, IMU readout, and a simple JSON command set. Re-flashing the ESP32 is a trap we can fall into later if we ever need to — stage 1 is about driving, not embedded development.
