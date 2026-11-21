#!/usr/bin/env python3
"""Parametric 3D-printable LiDAR + Breakout Board + Radxa ZERO 3W Tower Mount generator.

Generates support-free, watertight STL files in `cad/lidar_mount/`:
  1. `horace_lidar_sbc_tower.stl` — 1-piece support-free 3-tier open-arch tower:
       - Tier 1 (Z = 0.0..5.0 mm): Expansion-plate base (33.5×33.5 mm / 34.0×34.0 mm 4× M3 square
         + 49.0 mm C-to-C rear/side holes) + Radxa ZERO 3W bay (65.0×30.0×10.3 mm, 57.0–58.0 ×
         22.0–23.0 mm corner hole slots, 6.0 mm GPIO pin clearance, outward USB-C ports).
       - Tier 2 (Z = 16.0..26.5 mm): Press-fit / snap-in mezzanine cradle for the 40.0×20.0×8.0 mm
         LiDAR USB-to-UART breakout board (no screw holes required; open front Micro-USB port
         and open rear 4-pin LiDAR header, plus side USB cable loop guide arches).
       - Tier 3 (Z = 30.0 mm): LDROBOT D500 (STL-19P) LiDAR platform raising the 22.2 mm stationary
         base to Z = 30.0..52.2 mm and the 12.8 mm rotating optical turret to Z = 52.2..65.0 mm
         (+6.7 mm above the 45.5 mm front stereo camera casing; +13.5 mm at the Z = 59.0 mm beam plane!).
  2. `horace_lidar_tower_base.stl` & `horace_lidar_tower_top.stl` — Optional 2-piece bolt-together
     split at Z = 16.0 mm (connected via 2× M3 heat-set inserts at X = ±19.5 mm, Y = +2.0 mm).
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Tuple

import manifold3d as mf
import numpy as np
import trimesh


@dataclass
class LidarTowerParams:
    # --- 1. WAVE ROVER Expansion Plate Mounting Holes (Z = 0.0 mm deck) ---
    deck_square_min: float = 33.5        # mm user-measured central 4-hole square C-to-C
    deck_square_dxf: float = 34.0        # mm factory DXF central 4-hole square C-to-C
    deck_square_half: float = 16.875     # mm (+-16.875 mm = 33.75 mm center; slots span 33.0..34.5 mm)
    deck_wide_span: float = 49.0         # mm C-to-C wide/rear mounting holes (X = +-24.50 mm)
    deck_rear_hole_y: float = -32.75     # mm rear Ø2.6/M2.5 holes at X = +-24.50 mm flanking GPIO window
    camera_top_z: float = 45.5           # mm max height of front stereo camera casing above deck

    # --- 2. LDROBOT D500 (STL-19P) LiDAR (Mounted at Z = +30.0 mm) ---
    lidar_deck_z: float = 30.0           # mm platform Z height (places turret at Z = 52.2..65.0 mm!)
    lidar_base_size: float = 38.5        # mm square stationary body (38.5 x 38.5 mm)
    lidar_base_height: float = 22.2      # mm height of stationary base below rotating turret
    lidar_turret_dia: float = 35.3       # mm diameter of upper rotating optical turret
    lidar_turret_height: float = 12.8    # mm height of rotating optical turret (total LiDAR = 35.0 mm)
    lidar_beam_offset_z: float = 29.0    # mm optical laser plane above LiDAR bottom (Z = 59.0 mm!)
    lidar_front_ear_y: float = 23.30     # mm front ear hole (+19.25 + 4.05 mm forward of front wall)
    lidar_side_ear_x: float = 21.95      # mm side ear slot center (43.9 mm C-to-C; slot spans 42.5..45.4 mm)
    lidar_side_ear_y: float = -8.65      # mm side ear Y (-19.25 + 10.60 mm forward of rear edge)

    # --- 3. LiDAR Breakout Board (40.0 x 20.0 x 8.0 mm, Press-Fit Cradle) ---
    brk_length: float = 40.0             # mm board length along Y
    brk_width: float = 20.0              # mm board width along X
    brk_thickness: float = 1.6           # mm PCB FR4 thickness
    brk_max_height: float = 8.0          # mm total component height including 4-pin & Micro-USB
    brk_pocket_len: float = 40.6         # mm press-fit cradle length (0.3 mm/end clearance)
    brk_pocket_wid: float = 20.3         # mm press-fit cradle width (snug with 0.25 mm crush ribs)
    brk_seat_z: float = 18.8             # mm Z height of PCB underside seating ledges in mezzanine

    # --- 4. Radxa ZERO 3W Host SBC (65.0 x 30.0 x 10.3 mm, Rear Lower Deck) ---
    sbc_length: float = 65.0             # mm PCB length along X (64.0-65.0 mm)
    sbc_width: float = 30.0              # mm PCB width along Y
    sbc_total_height: float = 10.3       # mm max thickness including 6.0 mm GPIO pins
    sbc_gpio_pin_len: float = 6.0        # mm 40-pin header pin protrusion
    sbc_center_y: float = -26.0          # mm Y center of Radxa ZERO 3W on rear deck
    sbc_hole_x_min: float = 57.0         # mm user-measured long-side C-to-C hole spacing
    sbc_hole_x_max: float = 58.0         # mm nominal Pi Zero long-side C-to-C hole spacing
    sbc_hole_y_min: float = 22.0         # mm user-measured short-side C-to-C hole spacing
    sbc_hole_y_max: float = 23.0         # mm nominal Pi Zero short-side C-to-C hole spacing
    sbc_standoff_z: float = 5.2          # mm top of Radxa ZERO 3W corner standoffs

    # --- 5. Fasteners & Heat-Set Threaded Inserts ---
    m3_insert_dia: float = 4.0           # mm M3 brass heat-set insert melt bore
    m3_insert_depth: float = 6.0         # mm M3 insert depth
    m3_clear_dia: float = 3.4            # mm M3 screw clearance
    m2_insert_dia: float = 3.2           # mm M2 / M2.5 brass heat-set insert melt bore
    m2_insert_depth: float = 4.5         # mm M2 insert depth
    m2_clear_dia: float = 2.6            # mm M2 / M2.5 screw clearance


def rounded_rect_prism(
    width: float,
    height: float,
    depth: float,
    radius: float,
    center_xy: Tuple[float, float] = (0.0, 0.0),
    z0: float = 0.0,
    segments: int = 48,
) -> mf.Manifold:
    """Create an extruded rounded rectangle in X-Y from z=z0 to z=z0+depth."""
    r = max(0.05, min(radius, width * 0.49, height * 0.49))
    cx, cy = center_xy
    dx = width * 0.5 - r
    dy = height * 0.5 - r
    pts = []
    corners = [
        (cx + dx, cy + dy, 0.0),
        (cx - dx, cy + dy, math.pi * 0.5),
        (cx - dx, cy - dy, math.pi),
        (cx + dx, cy - dy, math.pi * 1.5),
    ]
    n_corner = max(4, segments // 4)
    for ox, oy, a0 in corners:
        for i in range(n_corner):
            ang = a0 + (math.pi * 0.5) * (i / n_corner)
            pts.append([ox + r * math.cos(ang), oy + r * math.sin(ang)])
    cross = mf.CrossSection([np.array(pts, dtype=np.float32)])
    return mf.Manifold.extrude(cross, depth).translate([0.0, 0.0, z0])


def cylinder_z(
    dia: float,
    depth: float,
    cx: float = 0.0,
    cy: float = 0.0,
    z0: float = 0.0,
    segments: int = 48,
) -> mf.Manifold:
    """Create a cylinder along Z from z=z0 to z=z0+depth centered at (cx, cy)."""
    r = dia * 0.5
    return mf.Manifold.cylinder(depth, r, r, segments).translate([cx, cy, z0])


def stadium_slot_z(
    slot_width: float,
    slot_height: float,
    depth: float,
    cx: float = 0.0,
    cy: float = 0.0,
    z0: float = 0.0,
    segments: int = 36,
) -> mf.Manifold:
    """Create a stadium/oblong slot in X-Y extruded along Z."""
    return rounded_rect_prism(
        width=slot_width,
        height=slot_height,
        depth=depth,
        radius=min(slot_width, slot_height) * 0.49,
        center_xy=(cx, cy),
        z0=z0,
        segments=segments,
    )


def blind_insert_bore_from_top_z(
    bore_dia: float,
    depth: float,
    z_top: float,
    cx: float,
    cy: float,
    chamfer_extra: float = 0.7,
    chamfer_depth: float = 0.5,
    segments: int = 48,
) -> mf.Manifold:
    """Blind heat-set insert bore opening at z=z_top going down (-Z) by `depth`."""
    r_bore = bore_dia * 0.5
    r_chamfer = (bore_dia + chamfer_extra) * 0.5
    z_bot = z_top - depth
    main_cyl = mf.Manifold.cylinder(depth + 0.05, r_bore, r_bore, segments).translate([cx, cy, z_bot])
    lead_in = mf.Manifold.cylinder(
        chamfer_depth + 0.05, r_bore, r_chamfer, segments
    ).translate([cx, cy, z_top - chamfer_depth])
    bottom_cone = mf.Manifold.cylinder(
        r_bore * 0.75, 0.2, r_bore, segments
    ).translate([cx, cy, z_bot - r_bore * 0.75 + 0.02])
    return main_cyl + lead_in + bottom_cone


def build_lidar_sbc_tower(p: LidarTowerParams) -> tuple[mf.Manifold, mf.Manifold, mf.Manifold]:
    """Build `horace_lidar_sbc_tower.stl` (1-piece) plus 2-piece split (`base` + `top` at Z=16.0mm)."""

    # =========================================================================
    # TIER 1 (Z = 0.0 .. 16.0 mm): EXPANSION PLATE BASE + RADXA ZERO 3W DECK
    # =========================================================================
    base_plate_h = 3.6  # solid structural base frame thickness (z = 0.0 to 3.6 mm)

    # 1a. Central expansion-plate mounting frame spanning the 33.5x33.5 / 34x34 mm square
    #     and the X = +-24.50 mm (49.0 mm) side slots (Y = -20.5 to +22.5 mm, X = -28.5 to +28.5 mm)
    central_frame = rounded_rect_prism(
        width=57.0,
        height=43.0,
        depth=base_plate_h,
        radius=4.5,
        center_xy=(0.0, 1.0),
        z0=0.0,
    )

    # 1b. Rear Radxa ZERO 3W mounting frame (Y = -41.5 to -10.5 mm, X = -33.5 to +33.5 mm = 67.0 mm wide)
    sbc_frame = rounded_rect_prism(
        width=67.0,
        height=31.0,
        depth=base_plate_h,
        radius=4.2,
        center_xy=(0.0, p.sbc_center_y),
        z0=0.0,
    )
    tower = central_frame + sbc_frame

    # Add reinforced Ø8.5 mm bosses at the 4 central square holes (X = +-16.875, Y = +-16.875 mm)
    for sx in (-p.deck_square_half, +p.deck_square_half):
        for sy in (-p.deck_square_half, +p.deck_square_half):
            tower = tower + cylinder_z(dia=8.8, depth=base_plate_h + 1.0, cx=sx, cy=sy, z0=0.0)

    # Add reinforced Ø8.2 mm bosses at the 49.0 mm C-to-C deck holes (X = +-24.50 mm, Y = +2.0 & -32.75 mm)
    for wx in (-24.50, +24.50):
        for wy in (+2.0, p.deck_rear_hole_y):
            tower = tower + cylinder_z(dia=8.2, depth=base_plate_h + 0.8, cx=wx, cy=wy, z0=0.0)

    # 1c. 4x Radxa ZERO 3W Corner Standoff Pillars (Z = 0.0 to 5.2 mm)
    #     Centered at X = +-28.75 mm (57.5 mm) and Y = -26.0 +- 11.25 mm (-37.25 and -14.75 mm = 22.5 mm)
    #     so both 57x22 mm and 58x23 mm board hole patterns align cleanly!
    sbc_hx = 0.25 * (p.sbc_hole_x_min + p.sbc_hole_x_max)  # 28.75 mm (57.5 mm C-to-C)
    sbc_hy = 0.25 * (p.sbc_hole_y_min + p.sbc_hole_y_max)  # 11.25 mm (22.5 mm C-to-C)
    for bx in (-sbc_hx, +sbc_hx):
        for by in (p.sbc_center_y - sbc_hy, p.sbc_center_y + sbc_hy):
            tower = tower + rounded_rect_prism(
                width=8.6,
                height=8.2,
                depth=p.sbc_standoff_z,
                radius=2.8,
                center_xy=(bx, by),
                z0=0.0,
            )

    # 1d. Cut out weight-relief & ventilation/GPIO windows in the lower base plate:
    #     - Central ventilation & wire pass-through window (22.0 x 24.0 mm at X=0, Y=+2.0)
    center_win = rounded_rect_prism(
        width=22.0,
        height=24.0,
        depth=10.0,
        radius=3.0,
        center_xy=(0.0, 2.0),
        z0=-1.0,
    )
    #     - Rear Radxa ZERO 3W under-board airflow + downward 40-pin GPIO clearance window
    #       (46.0 x 22.0 mm centered at X=0, Y=-26.0 mm — aligns directly over the expansion plate's
    #       rear rectangular cutout so 6.0 mm downward GPIO pins or jumper wires pass straight through!)
    sbc_win = rounded_rect_prism(
        width=46.0,
        height=22.0,
        depth=10.0,
        radius=3.0,
        center_xy=(0.0, p.sbc_center_y),
        z0=-1.0,
    )
    tower = tower - center_win - sbc_win

    # =========================================================================
    # TIER 2 & 3 RISER PILLARS, CABLE LOOP ARCHES & MEZZANINE (Z = 0.0 .. 30.0 mm)
    # =========================================================================
    # Keep the lower riser pillars strictly at Y = -9.2 to +20.2 mm (ahead of the Radxa ZERO 3W's
    # Y = -41.0..-11.0 mm envelope!), then corbel rearward at 45 deg above Z = 16.0 mm (above the
    # Radxa ZERO 3W's Z = 5.2..15.5 mm height) to support the rear of the LiDAR and breakout cradle!
    for sign in (-1.0, +1.0):
        # Lower pillar (Y = -9.2..+20.2 mm, Z = 0.0..30.0 mm) — clears Radxa ZERO 3W (Y <= -11.0 mm) completely!
        pillar_main = rounded_rect_prism(
            width=7.6,
            height=29.4,
            depth=p.lidar_deck_z,
            radius=2.2,
            center_xy=(sign * 19.6, 5.5),
            z0=0.0,
        )
        # Upper 45-deg rear corbel (Z = 16.0..30.0 mm, extending rearward from Y = -9.2 to -19.5 mm above the SBC)
        pillar_corbel = (
            rounded_rect_prism(width=7.6, height=29.4, depth=0.2, radius=2.2, center_xy=(sign * 19.6, 5.5), z0=16.0)
            + rounded_rect_prism(width=7.6, height=39.7, depth=4.0, radius=2.2, center_xy=(sign * 19.6, 0.35), z0=26.0)
        ).hull()
        tower = tower + pillar_main + pillar_corbel

        # Integrated side USB Cable Loop Guide Arch on outer face of each pillar (X = +-23.0..+-28.8 mm,
        # Y = -4.0..+10.0 mm, Z = 5.0..16.0 mm) with a smooth rounded cable channel and a
        # 2.2 mm snap-in side entry gap so the Camera Mini-USB cable and Breakout Micro-USB cable
        # loop around smoothly into the Radxa ZERO 3W's rear USB-C ports!
        clip_outer = rounded_rect_prism(
            width=6.8,
            height=13.0,
            depth=11.0,
            radius=2.2,
            center_xy=(sign * 25.2, 3.0),
            z0=5.0,
        )
        clip_hole = rounded_rect_prism(
            width=4.4,
            height=17.0,
            depth=6.6,
            radius=1.8,
            center_xy=(sign * 25.4, 3.0),
            z0=7.2,
        )
        clip_slot = rounded_rect_prism(
            width=4.0,
            height=17.0,
            depth=2.2,
            radius=0.5,
            center_xy=(sign * 28.0, 3.0),
            z0=9.4,
        )
        tower = tower + (clip_outer - clip_hole - clip_slot)

        # Carve a 45-deg vaulted side ventilation & screw-access window through each pillar
        # (Y = -4.5..+11.5 mm, Z = 4.2..14.8 mm)
        win_bot = rounded_rect_prism(
            width=12.0,
            height=15.0,
            depth=5.2,
            radius=1.5,
            center_xy=(sign * 19.6, 3.5),
            z0=4.2,
        )
        win_top = rounded_rect_prism(
            width=12.0,
            height=4.0,
            depth=0.2,
            radius=1.0,
            center_xy=(sign * 19.6, 3.5),
            z0=14.8,
        )
        tower = tower - (win_bot + win_top).hull()

    # =========================================================================
    # TIER 2 (Z = 16.0 .. 27.5 mm): PRESS-FIT MEZZANINE FOR 40x20x8mm BREAKOUT BOARD
    # =========================================================================
    # Bridges between the left and right pillars at Z = 16.2..26.4 mm using a 45-deg self-supporting
    # vaulted underside (at Y = -9.2..+20.2 mm from Z = 11.5..16.4 mm, and corbeled rearward to Y = -19.8 mm
    # above Z = 16.2 mm) so the entire mezzanine prints 100% support-free and clears the Radxa ZERO 3W!
    mez_outer = (
        rounded_rect_prism(width=36.0, height=30.0, depth=0.2, radius=2.5, center_xy=(0.0, 5.5), z0=16.2)
        + rounded_rect_prism(width=36.0, height=41.2, depth=7.2, radius=2.5, center_xy=(0.0, 0.5), z0=19.2)
    ).hull()
    # 45-deg self-supporting support gussets under the mezzanine side ledges (Y = -9.2..+20.2 mm, Z = 11.2 to 16.4 mm)
    mez_under_support = (
        rounded_rect_prism(width=41.0, height=29.4, depth=0.2, radius=2.0, center_xy=(0.0, 5.5), z0=11.2)
        + rounded_rect_prism(width=30.0, height=29.4, depth=0.2, radius=2.0, center_xy=(0.0, 5.5), z0=16.4)
    ).hull()
    tower = tower + mez_outer + mez_under_support

    # Cut out the central under-arch below Z = 16.2 mm (with a 45-deg vaulted ceiling peaking at Z = 17.8 mm)
    # so the lower tunnel (X = -15.8..+15.8 mm) prints with zero horizontal bridges!
    arch_bot = rounded_rect_prism(
        width=31.6,
        height=46.0,
        depth=10.5,
        radius=1.5,
        center_xy=(0.0, 0.5),
        z0=-0.1,
    )
    arch_top = rounded_rect_prism(
        width=16.4,
        height=46.0,
        depth=0.2,
        radius=1.0,
        center_xy=(0.0, 0.5),
        z0=17.8,
    )
    tower = tower - (arch_bot + arch_top).hull()

    # Cut out the Press-Fit Cradle Pocket for the 40.0 x 20.0 x 8.0 mm LiDAR Breakout Board:
    # - Under-PCB solder/pin relief trough (16.4 mm wide in X, open all the way through Y, Z = 16.0..19.2 mm)
    brk_under_trough = rounded_rect_prism(
        width=16.4,
        height=46.0,
        depth=3.5,
        radius=1.0,
        center_xy=(0.0, 0.5),
        z0=16.0,
    )
    # - Main 40.6 x 20.3 mm PCB + component cradle (X = -10.15..+10.15 mm, Y = -19.8..+20.8 mm, Z = 18.8..27.2 mm)
    #   Seats the 20.0 mm wide PCB on two 1.95 mm wide side ledges at Z = 18.8 mm!
    brk_pocket = rounded_rect_prism(
        width=p.brk_pocket_wid,
        height=p.brk_pocket_len,
        depth=8.6,
        radius=0.8,
        center_xy=(0.0, 0.5),
        z0=p.brk_seat_z,
    )
    # - Open front Micro-USB plug & rear 4-pin LiDAR header end channels (15.6 mm wide in X, Z = 18.4..27.2 mm)
    #   Leaves 2.35 mm end stops at X = +-7.8..+-10.15 mm so the 40.0 mm board is captive in Y!
    brk_end_openings = rounded_rect_prism(
        width=15.6,
        height=46.0,
        depth=8.8,
        radius=1.0,
        center_xy=(0.0, 0.5),
        z0=p.brk_seat_z - 0.4,
    )
    tower = tower - brk_under_trough - brk_pocket - brk_end_openings

    # Add 4x Press-Fit Crush Ribs + Snap-Fit Top Retention Nibs along the X = +-10.15 mm cradle walls:
    # - At Y = -12.0 and +13.0 mm, two 0.5 mm chamfered top retention nibs at Z = 20.6..21.8 mm
    #   click over the top of the 1.6 mm PCB (Z = 18.8..20.4 mm) to hold it securely without screws!
    for sign in (-1.0, +1.0):
        for ny in (-12.0, +13.0):
            nib = (
                rounded_rect_prism(width=1.2, height=4.8, depth=0.2, radius=0.3, center_xy=(sign * 9.85, ny), z0=21.1)
                + rounded_rect_prism(width=0.4, height=4.8, depth=1.6, radius=0.15, center_xy=(sign * 10.2, ny), z0=20.4)
            ).hull()
            tower = tower + nib

    # =========================================================================
    # TIER 3 (Z = 26.0 .. 32.2 mm): LDROBOT D500 (STL-19P) LIDAR PLATFORM
    # =========================================================================
    # Top platform at Z = 26.2..30.0 mm with a 45-deg vaulted underside over the breakout cradle
    lidar_plate = rounded_rect_prism(
        width=45.0,
        height=43.0,
        depth=4.0,
        radius=4.0,
        center_xy=(0.0, 0.5),
        z0=p.lidar_deck_z - 4.0,
    )
    # Front ear boss (X = 0.0 mm, Y = +23.30 mm, Ø9.6 mm boss + 45-deg support gusset underneath)
    front_ear_boss = (
        cylinder_z(dia=9.6, depth=4.0, cx=0.0, cy=p.lidar_front_ear_y, z0=p.lidar_deck_z - 4.0)
        + cylinder_z(dia=9.6, depth=0.2, cx=0.0, cy=p.lidar_front_ear_y, z0=p.lidar_deck_z - 4.0)
        + cylinder_z(dia=6.0, depth=0.2, cx=0.0, cy=18.5, z0=p.lidar_deck_z - 8.5)
    ).hull()

    # Left & Right rear-side ear bosses (X = +-21.95 mm, Y = -8.65 mm, stadium bosses covering X = +-18..+-26.5 mm)
    side_ear_bosses = mf.Manifold()
    for sign in (-1.0, +1.0):
        sb = (
            rounded_rect_prism(width=11.0, height=9.6, depth=4.0, radius=3.5, center_xy=(sign * p.lidar_side_ear_x, p.lidar_side_ear_y), z0=p.lidar_deck_z - 4.0)
            + rounded_rect_prism(width=6.0, height=9.6, depth=0.2, radius=2.0, center_xy=(sign * 19.5, p.lidar_side_ear_y), z0=p.lidar_deck_z - 8.0)
        ).hull()
        side_ear_bosses = side_ear_bosses + sb

    # Self-centering 2.0 mm tall corner alignment rim around the 38.5 x 38.5 mm LiDAR square base
    # (inner pocket = 39.1 x 39.1 mm = 0.3 mm/side clearance; open on rear and at the 3 ear positions)
    rim_outer = rounded_rect_prism(
        width=43.5,
        height=42.5,
        depth=2.0,
        radius=3.2,
        center_xy=(0.0, 0.0),
        z0=p.lidar_deck_z,
    )
    rim_inner = rounded_rect_prism(
        width=p.lidar_base_size + 0.6,
        height=p.lidar_base_size + 0.6,
        depth=3.0,
        radius=1.0,
        center_xy=(0.0, 0.0),
        z0=p.lidar_deck_z - 0.2,
    )
    # Clear the 3 ear tabs and rear 4-pin LiDAR connector through the alignment rim
    rim_front_cut = rounded_rect_prism(width=14.0, height=12.0, depth=3.0, radius=1.0, center_xy=(0.0, 20.0), z0=p.lidar_deck_z - 0.2)
    rim_rear_cut = rounded_rect_prism(width=28.0, height=12.0, depth=3.0, radius=1.0, center_xy=(0.0, -20.0), z0=p.lidar_deck_z - 0.2)
    rim_side_cut = rounded_rect_prism(width=52.0, height=13.0, depth=3.0, radius=1.0, center_xy=(0.0, p.lidar_side_ear_y), z0=p.lidar_deck_z - 0.2)
    lidar_rim = rim_outer - rim_inner - rim_front_cut - rim_rear_cut - rim_side_cut

    tower = tower + lidar_plate + front_ear_boss + side_ear_bosses + lidar_rim

    # Re-cut the 45-deg vaulted ceiling of the Breakout Board mezzanine (Z = 24.5..27.4 mm) so the
    # underside of the Z = 30.0 mm LiDAR platform is 100% self-supporting at <= 45 deg!
    mez_vault_base = rounded_rect_prism(
        width=p.brk_pocket_wid,
        height=46.0,
        depth=6.2,
        radius=0.8,
        center_xy=(0.0, 0.5),
        z0=p.brk_seat_z,
    )
    mez_vault_top = rounded_rect_prism(
        width=14.5,
        height=46.0,
        depth=0.2,
        radius=0.8,
        center_xy=(0.0, 0.5),
        z0=27.4,
    )
    tower = tower - (mez_vault_base + mez_vault_top).hull()

    # =========================================================================
    # DRILL ALL MOUNTING SLOTS & HEAT-SET INSERT BORES
    # =========================================================================
    # A. 4x Central Square Expansion-Plate Mounting Slots (X = +-16.875, Y = +-16.875 mm)
    #    4.2 x 3.5 mm stadium through-slots + Ø6.8 mm counterbores so M3 screws fit both 33.5x33.5 & 34.0x34.0 mm!
    for sx in (-p.deck_square_half, +p.deck_square_half):
        for sy in (-p.deck_square_half, +p.deck_square_half):
            tower = tower - stadium_slot_z(slot_width=4.3, slot_height=4.3, depth=12.0, cx=sx, cy=sy, z0=-1.0)
            tower = tower - cylinder_z(dia=6.8, depth=14.0, cx=sx, cy=sy, z0=3.2)

    # B. 4x Wide 49.0 mm C-to-C Expansion-Plate Mounting Slots (X = +-24.50 mm, Y = +2.0 & -32.75 mm)
    for wx in (-24.50, +24.50):
        for wy in (+2.0, p.deck_rear_hole_y):
            tower = tower - stadium_slot_z(slot_width=3.4, slot_height=4.8, depth=12.0, cx=wx, cy=wy, z0=-1.0)
            tower = tower - cylinder_z(dia=6.2, depth=10.0, cx=wx, cy=wy, z0=3.0)

    # C. 4x Radxa ZERO 3W Corner Mounting Bosses (X = +-28.75 mm, Y = -26.0 +- 11.25 mm)
    #    Top Ø3.2 x 4.2 mm M2 heat-set insert bore + through 3.6 x 2.6 mm oblong slot for 57-58 x 22-23 mm!
    for bx in (-sbc_hx, +sbc_hx):
        for by in (p.sbc_center_y - sbc_hy, p.sbc_center_y + sbc_hy):
            tower = tower - blind_insert_bore_from_top_z(
                bore_dia=p.m2_insert_dia,
                depth=4.0,
                z_top=p.sbc_standoff_z,
                cx=bx,
                cy=by,
            )
            tower = tower - stadium_slot_z(slot_width=3.6, slot_height=3.2, depth=10.0, cx=bx, cy=by, z0=-1.0)

    # D. 3x LDROBOT D500 LiDAR Mounting Ear Holes/Slots at Z = 30.0 mm:
    #    - Front Ear (X = 0.0, Y = +23.30 mm): Ø3.2 mm M2 heat-set insert bore + Ø2.6 mm through-slot
    tower = tower - blind_insert_bore_from_top_z(
        bore_dia=p.m2_insert_dia,
        depth=3.6,
        z_top=p.lidar_deck_z,
        cx=0.0,
        cy=p.lidar_front_ear_y,
    )
    tower = tower - stadium_slot_z(slot_width=2.8, slot_height=3.8, depth=10.0, cx=0.0, cy=p.lidar_front_ear_y, z0=p.lidar_deck_z - 6.0)

    #    - Left & Right Side Ears (X = +-21.95 mm, Y = -8.65 mm):
    #      5.4 x 2.8 mm horizontal stadium through-slots (spans X = +-19.9..+-24.0 mm = 39.8..48.0 mm,
    #      covering both 42.69 mm CAD and 45.0 mm user-measured C-to-C!) + M2 insert bore at X = +-22.5 mm!
    for sign in (-1.0, +1.0):
        tower = tower - stadium_slot_z(
            slot_width=5.4,
            slot_height=2.9,
            depth=10.0,
            cx=sign * p.lidar_side_ear_x,
            cy=p.lidar_side_ear_y,
            z0=p.lidar_deck_z - 6.0,
        )
        tower = tower - blind_insert_bore_from_top_z(
            bore_dia=p.m2_insert_dia,
            depth=3.4,
            z_top=p.lidar_deck_z,
            cx=sign * 22.50,
            cy=p.lidar_side_ear_y,
        )

    # =========================================================================
    # CREATE OPTIONAL 2-PIECE BOLT-TOGETHER SPLIT AT Z = 16.0 mm
    # =========================================================================
    split_z = 16.0
    lower_clip = rounded_rect_prism(width=120.0, height=120.0, depth=split_z, radius=2.0, center_xy=(0.0, -5.0), z0=0.0)
    upper_clip = rounded_rect_prism(width=120.0, height=120.0, depth=40.0, radius=2.0, center_xy=(0.0, -5.0), z0=split_z)

    tower_base = tower ^ lower_clip
    tower_top = (tower ^ upper_clip).translate([0.0, 0.0, -split_z])

    # Add 2x M3 heat-set insert bores in tower_base (at X = +-19.6, Y = +0.5 mm, Z = 16.0 mm)
    # and matching Ø3.4 mm M3 through-bores in tower_top so the 2-piece version bolts together if desired
    for sign in (-1.0, +1.0):
        tower_base = tower_base - blind_insert_bore_from_top_z(
            bore_dia=p.m3_insert_dia,
            depth=6.0,
            z_top=split_z,
            cx=sign * 19.6,
            cy=0.5,
        )

    return tower, tower_base, tower_top


def manifold_to_trimesh(m: mf.Manifold) -> trimesh.Trimesh:
    mesh_data = m.to_mesh()
    verts = np.array(mesh_data.vert_properties[:, :3], dtype=np.float64)
    faces = np.array(mesh_data.tri_verts, dtype=np.int64)
    return trimesh.Trimesh(vertices=verts, faces=faces, process=True)


def generate_all(out_dir: Path, params: LidarTowerParams) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    tower_solid, base_solid, top_solid = build_lidar_sbc_tower(params)
    specs = [
        ("horace_lidar_sbc_tower.stl", tower_solid),
        ("horace_lidar_tower_base.stl", base_solid),
        ("horace_lidar_tower_top.stl", top_solid),
    ]
    summary = {"parameters_mm": asdict(params), "files": {}}
    for filename, solid in specs:
        mesh = manifold_to_trimesh(solid)
        stl_path = out_dir / filename
        mesh.export(stl_path)
        extents = mesh.extents.round(2).tolist()
        summary["files"][filename] = {
            "path": str(stl_path),
            "watertight": bool(mesh.is_watertight),
            "bounding_box_mm": extents,
            "volume_cm3": round(float(mesh.volume) / 1000.0, 2),
            "triangles": int(len(mesh.faces)),
        }
        print(
            f"[OK] {filename:28s} | watertight={mesh.is_watertight} | "
            f"bbox={extents[0]:.1f}x{extents[1]:.1f}x{extents[2]:.1f} mm | "
            f"vol={mesh.volume/1000.0:.2f} cm^3 | tris={len(mesh.faces)}"
        )

    meta_path = out_dir / "lidar_tower_dimensions.json"
    meta_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--lidar-deck-z", type=float, default=30.0, help="LiDAR platform elevation above deck (mm)")
    args = parser.parse_args()

    params = LidarTowerParams(lidar_deck_z=args.lidar_deck_z)
    generate_all(args.out_dir, params)


if __name__ == "__main__":
    main()
