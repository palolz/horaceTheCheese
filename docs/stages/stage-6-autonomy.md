# Stage 6 · Autonomy <span class="htc-badge htc-badge--planned">Planned</span>

Point at the map, and horace goes there. Nav2 goal following on the maps built in stage 5.

## Goals

- [ ] Nav2 stack up: planner, controller, costmaps, behaviors
- [ ] Localization against the saved RTAB-Map map
- [ ] "2D Goal Pose" in RViz / Foxglove sends the rover across the room
- [ ] Obstacle avoidance using live LiDAR + depth data in the local costmap
- [ ] A filmed end-to-end demo: map → click goal → rover drives there unaided

## The plan

1. Bring up Nav2 in simulation-shaped config first, then retarget to the real robot.
2. Tune the local/global costmaps for a small, fast 4WD rover.
3. Iterate on controller parameters until motion is smooth, not apologetic.
4. Film the demo. Take the rest of the day off.

## Done when

From a cold boot: load the map, click a goal on the other side of the room, and the rover plans and drives there without a single keyboard touch.

!!! note "The point of the whole project"
    Every earlier stage exists to make this one boring. If stage 6 feels uneventful, stages 1–5 did their job.
