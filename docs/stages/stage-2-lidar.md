# Stage 2 · LiDAR bring-up <span class="htc-badge htc-badge--planned">Planned</span>

Mount the **LDROBOT D500 LiDAR Kit (LD19)** — already waiting in its box on the workbench — onto the metal expansion deck, spin it up, and turn sweeps of laser dots into the first 2D map of the room.

## Goals

- [ ] LD19 wired to the host board (USB-UART adapter or direct UART, 3.3 V logic)
- [ ] `ld19` driver node publishing `sensor_msgs/LaserScan` on `/scan`
- [ ] `base_link → laser` static transform in the URDF / tf2 tree
- [ ] slam_toolbox (async mode) building a map live in RViz
- [ ] First saved map of a real room, screenshotted for the build log

## The plan

1. Verify the LD19's scan rate and range on the bench before it ever touches the rover.
2. Bring up the driver, check `/scan` in RViz, walk the room with the sensor in hand.
3. Bolt it to the mast, measure the exact offset, encode it in `wave_rover_description`.
4. Run slam_toolbox alongside stage 1 teleop and drive the first mapping loop.

## Done when

Driving a loop around the room produces a closed, recognizable map in RViz — and the loop actually closes.

!!! warning "Watch the center of gravity"
    The mast puts mass up high. Printed brackets are fine, but the rover should stay polite at full throttle until the mount is proven.
