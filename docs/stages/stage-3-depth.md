# Stage 3 · Binocular depth <span class="htc-badge htc-badge--planned">Planned</span>

Give horace its eyes: a binocular (stereo) camera computing depth onboard, streaming images and point clouds to the Mac over WiFi.

## Goals

- [ ] Stereo camera mounted front and center — the rover's two "eyes"
- [ ] Camera driver publishing rectified left/right images, camera info, and a depth image
- [ ] `depth_image_proc` producing a colored point cloud on `/points`
- [ ] Streams viewable live in Foxglove / RViz on the Mac over WiFi
- [ ] Bandwidth measured and throttled (WiFi is the shared road everything drives on)

## The plan

1. Bench-test the camera on the host board: calibration, rectification, first depth image.
2. Mount on the chassis front; measure the offset into `base_link → camera_link`.
3. Tune resolution/rate until the stream is smooth without choking teleop or scans.
4. Screenshot the first point cloud of something appropriately dramatic (a chair).

## Done when

Foxglove shows a live, colored point cloud while the rover is being teleoperated — with no dropped `/cmd_vel` hiccups.

!!! note "Eyes before brains"
    Stage 3 only *produces* depth data. Fusing it into maps is stage 5's job. Keeping data production and consumption in separate stages keeps every failure easy to point at.
