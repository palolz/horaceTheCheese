# Stage 4 · Sensor fusion <span class="htc-badge htc-badge--planned">Planned</span>

One believable answer to "where am I?" — an Extended Kalman Filter fusing the ESP32's 9-axis IMU with wheel odometry via `robot_localization`.

## Goals

- [ ] `ekf_node` (robot_localization) fusing `/imu/data_raw` + wheel odometry
- [ ] Sensible `odom → base_link` transform with bounded drift
- [ ] Covariances set from *measured* noise, not wishful thinking
- [ ] A repeatable drift test: drive a fixed pattern, compare EKF pose vs. raw odometry

## The plan

1. Characterize the IMU and wheel odometry on their own (bias, noise, scale).
2. Configure the EKF: which fields fuse, which get rejected, frame by frame.
3. Drive test patterns and iterate until the fused estimate beats either source alone.
4. Document the final config and the before/after numbers.

## Done when

A 5-minute teleop drive ends with the EKF's pose visibly closer to reality than raw wheel odometry — quantified in the build log.

!!! warning "Garbage in, gospel out"
    An EKF will happily fuse wrong data with great confidence. Stage 4 exists so that when SLAM leans on odometry later, the odometry deserves the trust.
