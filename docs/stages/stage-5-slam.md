# Stage 5 · Full SLAM <span class="htc-badge htc-badge--planned">Planned</span>

The big one: RTAB-Map fusing the LD19's laser scans and the stereo camera's depth into a single, persistent, loop-closing map — running on fused odometry from stage 4.

## Goals

- [ ] RTAB-Map running with LiDAR + stereo depth + EKF odometry as inputs
- [ ] Loop closure working on a revisited room
- [ ] 2D occupancy grid + 3D map cloud both published
- [ ] A saved, reloadable map of the test space
- [ ] The money shot: map, cloud, and rover pose all live in Foxglove

## The plan

1. Start from the stage 2 slam_toolbox setup and swap in RTAB-Map incrementally: LiDAR-only first.
2. Add the stereo depth stream; watch loop closures light up on revisit.
3. Tune memory management so the host board doesn't melt on longer runs.
4. Save the map, restart, and verify localization against the saved map.

## Done when

The rover maps a multi-room space, closes at least one loop, and can relocalize into the saved map after a reboot.

!!! note "Why RTAB-Map?"
    It is built exactly for this combination: LiDAR + RGB-D/stereo + external odometry, with appearance-based loop closure, and it plays well with Nav2 in stage 6.
