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

    # --- 2. LDROBOT D500 (STL-19P) LiDAR (Mounted at Z = +35.0 mm) ---
    lidar_deck_z: float = 35.0           # mm platform Z height (places turret at Z = 57.2..70.0 mm!)
    lidar_deck_thickness: float = 4.2    # mm solid top deck thickness (Z = 30.8..35.0 mm; zero downward hang!)
    lidar_base_size: float = 38.5        # mm square stationary body (38.5 x 38.5 mm)
    lidar_base_height: float = 22.2      # mm height of stationary base below rotating turret
    lidar_turret_dia: float = 35.3       # mm diameter of upper rotating optical turret
    lidar_turret_height: float = 12.8    # mm height of rotating optical turret (total LiDAR = 35.0 mm)
    lidar_beam_offset_z: float = 29.0    # mm optical laser plane above LiDAR bottom (Z = 64.0 mm!)
    lidar_front_ear_y: float = 23.30     # mm front ear hole (+19.25 + 4.05 mm forward of front wall)
    lidar_side_ear_x: float = 21.95      # mm side ear slot center (43.9 mm C-to-C; slot spans 42.5..45.4 mm)
    lidar_side_ear_y: float = -8.65      # mm side ear Y (-19.25 + 10.60 mm forward of rear edge)

    # --- 3. LiDAR Breakout Board (40.0 x 20.0 x 8.0 mm, Press-Fit Cradle) ---
    brk_length: float = 40.0             # mm board length along Y
    brk_width: float = 20.0              # mm board width along X
    brk_thickness: float = 1.6           # mm PCB FR4 thickness
    brk_max_height: float = 8.0          # mm total component height including 4-pin & Micro-USB
    brk_pocket_len: float = 40.6         # mm press-fit cradle length (0.3 mm/end clearance)
    brk_pocket_wid: float = 20.3         # mm press-fit cradle width (snug with 2.05 mm side ledges)
    brk_seat_z: float = 17.0             # mm Z height of PCB underside seating ledges (13.8mm clearance to Z=30.8mm roof!)
    usb_channel_floor_z: float = 13.5    # mm floor of central 16.2mm USB plug channel (17.3mm total vertical plug window!)

    # --- 4. Radxa ZERO 3W Host SBC (65.0 x 30.0 x 10.3 mm, Rear Open-Sky Deck) ---
    sbc_length: float = 65.0             # mm PCB length along X (64.0-65.0 mm)
    sbc_width: float = 30.0              # mm PCB width along Y
    sbc_total_height: float = 10.3       # mm max thickness including 6.0 mm GPIO pins
    sbc_gpio_pin_len: float = 6.0        # mm 40-pin header pin protrusion
    sbc_center_y: float = -50.5          # mm Y center of Radxa ZERO 3W (Y = -65.5..-35.5 mm, 100% behind bridge!)
    sbc_hole_x_min: float = 57.0         # mm user-measured long-side C-to-C hole spacing
    sbc_hole_x_max: float = 58.0         # mm nominal Pi Zero long-side C-to-C hole spacing
    sbc_hole_y_min: float = 22.0         # mm user-measured short-side C-to-C hole spacing
    sbc_hole_y_max: float = 23.0         # mm nominal Pi Zero short-side C-to-C hole spacing
    sbc_standoff_z: float = 5.6          # mm top of Radxa ZERO 3W corner standoffs

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
    """Build `horace_lidar_sbc_tower.stl` v2 (1-piece structure) plus 2-piece split (`base` + `top` at Z=12.5mm)."""

    # =========================================================================
    # TIER 1 (Z = 0.0 .. 5.6 mm): EXPANSION PLATE BASE + REAR RADXA ZERO 3W DECK
    # =========================================================================
    base_plate_h = 4.4  # sturdy 4.4 mm structural base frame thickness (z = 0.0 to 4.4 mm)

    # 1a. Central expansion-plate mounting frame spanning the 33.5x33.5 / 34x34 mm square
    #     and the X = +-24.50 mm (49.0 mm) side/rear holes (Y = -36.5 to +22.5 mm, X = -28.5 to +28.5 mm)
    central_frame = rounded_rect_prism(
        width=57.0,
        height=59.0,
        depth=base_plate_h,
        radius=4.5,
        center_xy=(0.0, -7.0),
        z0=0.0,
    )

    # 1b. Rear Radxa ZERO 3W mounting frame (Y = -66.5 to -34.5 mm, X = -33.5 to +33.5 mm = 67.0 mm wide)
    #     Positioned at sbc_center_y = -50.5 mm so the entire Radxa ZERO 3W (Y = -65.5..-35.5 mm) and its
    #     40-pin GPIO header (Y = -39.25 mm) sit >14 mm behind the LiDAR bridge with 100% open sky above!
    sbc_frame = rounded_rect_prism(
        width=67.0,
        height=32.0,
        depth=base_plate_h,
        radius=4.2,
        center_xy=(0.0, p.sbc_center_y),
        z0=0.0,
    )
    tower = central_frame + sbc_frame

    # Add reinforced Ø8.8 mm bosses at the 4 central square holes (X = +-16.875, Y = +-16.875 mm)
    for sx in (-p.deck_square_half, +p.deck_square_half):
        for sy in (-p.deck_square_half, +p.deck_square_half):
            tower = tower + cylinder_z(dia=8.8, depth=base_plate_h + 0.6, cx=sx, cy=sy, z0=0.0)

    # Add reinforced Ø8.4 mm bosses at the 49.0 mm C-to-C deck holes (X = +-24.50 mm, Y = +2.0 & -32.75 mm)
    for wx in (-24.50, +24.50):
        for wy in (+2.0, p.deck_rear_hole_y):
            tower = tower + cylinder_z(dia=8.4, depth=base_plate_h + 0.6, cx=wx, cy=wy, z0=0.0)

    # 1c. 4x Radxa ZERO 3W Corner Standoff Pillars (Z = 0.0 to 5.6 mm)
    #     Centered at X = +-28.75 mm (57.5 mm) and Y = -50.5 +- 11.25 mm (-61.75 and -39.25 mm = 22.5 mm)
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
    #     - Central ventilation window (22.0 x 24.0 mm at X=0, Y=+1.0)
    center_win = rounded_rect_prism(
        width=22.0,
        height=24.0,
        depth=10.0,
        radius=3.0,
        center_xy=(0.0, 1.0),
        z0=-1.0,
    )
    #     - Mid-bridge weight-relief & wire pass-through window (30.0 x 12.0 mm at X=0, Y=-26.5 mm,
    #       aligned directly over the expansion plate's rear rectangular GPIO cutout!)
    mid_win = rounded_rect_prism(
        width=30.0,
        height=12.0,
        depth=10.0,
        radius=2.5,
        center_xy=(0.0, -26.5),
        z0=-1.0,
    )
    #     - Rear Radxa ZERO 3W under-board airflow window (46.0 x 21.0 mm centered at X=0, Y=-50.5 mm)
    sbc_win = rounded_rect_prism(
        width=46.0,
        height=21.0,
        depth=10.0,
        radius=3.0,
        center_xy=(0.0, p.sbc_center_y),
        z0=-1.0,
    )
    #     - Left-edge microSD card slot recess (X = -34.0..-19.0 mm, Y = -57.0..-44.0 mm, Z = 2.4..6.0 mm)
    #       so the underside microSD holder on the Radxa ZERO 3W has full clearance and card access!
    sd_recess = rounded_rect_prism(
        width=16.0,
        height=13.0,
        depth=4.0,
        radius=1.5,
        center_xy=(-27.0, p.sbc_center_y),
        z0=2.4,
    )
    tower = tower - center_win - mid_win - sbc_win - sd_recess

    # =========================================================================
    # TIER 2 & 3 RISER PILLARS (Z = 0.0 .. 35.0 mm — FLUSH SIDES, ZERO SIDE CLIPS!)
    # =========================================================================
    # Keep the lower riser pillars at Y = -12.5..+13.5 mm (between the Y = +-16.875 mm central square M3 holes
    # so all 4 central M3 bolts have open vertical screwdriver access!), then corbel forward & rearward at 45 deg
    # above Z = 13.0 mm to support the full length of the Breakout Mezzanine and Z = 35.0 mm LiDAR platform!
    deck_bot_z = p.lidar_deck_z - p.lidar_deck_thickness  # 30.8 mm
    for sign in (-1.0, +1.0):
        # Lower pillar (X = +-15.8..+-23.4 mm, Y = -12.5..+13.5 mm, Z = 0.0..35.0 mm) — 100% flush outer walls!
        pillar_main = rounded_rect_prism(
            width=7.6,
            height=26.0,
            depth=p.lidar_deck_z,
            radius=2.2,
            center_xy=(sign * 19.6, 0.5),
            z0=0.0,
        )
        # Upper 45-deg Y-corbel (rising from Y = -12.5..+13.5 mm at Z = 13.0 mm out to Y = -20.5..+21.5 mm at Z = 21.0..35.0 mm)
        pillar_corbel = (
            rounded_rect_prism(width=7.6, height=26.0, depth=0.2, radius=2.2, center_xy=(sign * 19.6, 0.5), z0=13.0)
            + rounded_rect_prism(width=7.6, height=42.0, depth=14.0, radius=2.2, center_xy=(sign * 19.6, 0.5), z0=21.0)
        ).hull()
        tower = tower + pillar_main + pillar_corbel

        # Carve a 45-deg vaulted side ventilation window through the lower pillar (Y = -5.5..+6.5 mm, Z = 4.4..12.0 mm)
        win_bot = rounded_rect_prism(
            width=12.0,
            height=12.0,
            depth=3.6,
            radius=1.5,
            center_xy=(sign * 19.6, 0.5),
            z0=4.4,
        )
        win_top = rounded_rect_prism(
            width=12.0,
            height=4.0,
            depth=0.2,
            radius=1.0,
            center_xy=(sign * 19.6, 0.5),
            z0=12.0,
        )
        tower = tower - (win_bot + win_top).hull()

    # =========================================================================
    # TIER 2 (Z = 11.5 .. 30.8 mm): PRESS-FIT MEZZANINE & DOUBLED USB PLUG CHANNEL
    # =========================================================================
    # Bridges between the left and right pillars with a solid floor at Z = 11.5..13.5 mm (supported by a
    # 45-deg vaulted lower arch from Z = 5.5..11.5 mm), PCB seating ledges at Z = 17.0 mm, and a huge
    # 16.2 mm wide x 17.3 mm tall USB plug & cable clearance tunnel (Z = 13.5..30.8 mm)!
    mez_outer = (
        rounded_rect_prism(width=36.0, height=26.0, depth=0.2, radius=2.5, center_xy=(0.0, 0.5), z0=11.5)
        + rounded_rect_prism(width=36.0, height=42.0, depth=13.8, radius=2.5, center_xy=(0.0, 0.5), z0=17.0)
    ).hull()
    mez_under_support = (
        rounded_rect_prism(width=42.0, height=26.0, depth=0.2, radius=2.0, center_xy=(0.0, 0.5), z0=6.5)
        + rounded_rect_prism(width=31.0, height=26.0, depth=0.2, radius=2.0, center_xy=(0.0, 0.5), z0=12.0)
    ).hull()
    tower = tower + mez_outer + mez_under_support

    # Cut out the central under-arch below the mezzanine floor (Z = 0.0..11.5 mm, 45-deg vaulted roof)
    arch_bot = rounded_rect_prism(
        width=31.6,
        height=48.0,
        depth=5.8,
        radius=1.5,
        center_xy=(0.0, 0.5),
        z0=-0.1,
    )
    arch_top = rounded_rect_prism(
        width=16.0,
        height=48.0,
        depth=0.2,
        radius=1.0,
        center_xy=(0.0, 0.5),
        z0=11.5,
    )
    tower = tower - (arch_bot + arch_top).hull()

    # =========================================================================
    # TIER 3 (Z = 30.8 .. 35.0 mm): LDROBOT D500 (STL-19P) LIDAR PLATFORM
    # =========================================================================
    # Top platform at Z = 30.8..35.0 mm (4.2 mm thick).
    # CRITICAL: Front ear boss (X = 0.0, Y = +23.30 mm) is supported laterally within Z = 30.8..35.0 mm
    # and by left/right side corbels at |X| >= 8.5 mm so NOTHING hangs below Z = 30.8 mm in the central
    # X = -8.5..+8.5 mm USB plug/breakout corridor!
    lidar_plate = rounded_rect_prism(
        width=45.0,
        height=43.0,
        depth=p.lidar_deck_thickness,
        radius=4.0,
        center_xy=(0.0, 0.5),
        z0=deck_bot_z,
    )
    # Front ear lobe in X-Y strictly within Z = 30.8..35.0 mm (zero downward protrusion below Z = 30.8 mm!)
    front_ear_lobe = (
        cylinder_z(dia=10.4, depth=p.lidar_deck_thickness, cx=0.0, cy=p.lidar_front_ear_y, z0=deck_bot_z)
        + rounded_rect_prism(width=24.0, height=8.0, depth=p.lidar_deck_thickness, radius=3.0, center_xy=(0.0, 19.0), z0=deck_bot_z)
    ).hull()

    # Left & Right forward corbels at |X| = 8.5..21.0 mm (outside the 16.2 mm central USB channel!)
    # rising at 45 deg from Y = +21.0 mm (Z = 27.0 mm) to Y = +24.8 mm (Z = 30.8 mm) to support the front lobe
    front_side_corbels = mf.Manifold()
    for sign in (-1.0, +1.0):
        fsc = (
            rounded_rect_prism(width=9.5, height=3.0, depth=0.2, radius=1.5, center_xy=(sign * 13.5, 19.5), z0=26.8)
            + rounded_rect_prism(width=9.5, height=7.0, depth=p.lidar_deck_thickness, radius=1.5, center_xy=(sign * 13.5, 21.5), z0=deck_bot_z)
        ).hull()
        front_side_corbels = front_side_corbels + fsc

    # Left & Right rear-side ear bosses (X = +-21.95 mm, Y = -8.65 mm, stadium bosses with 45-deg lower corbels)
    side_ear_bosses = mf.Manifold()
    for sign in (-1.0, +1.0):
        sb = (
            rounded_rect_prism(width=11.0, height=9.6, depth=p.lidar_deck_thickness, radius=3.5, center_xy=(sign * p.lidar_side_ear_x, p.lidar_side_ear_y), z0=deck_bot_z)
            + rounded_rect_prism(width=6.0, height=9.6, depth=0.2, radius=2.0, center_xy=(sign * 19.5, p.lidar_side_ear_y), z0=deck_bot_z - 4.0)
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
    rim_front_cut = rounded_rect_prism(width=14.0, height=12.0, depth=3.0, radius=1.0, center_xy=(0.0, 20.0), z0=p.lidar_deck_z - 0.2)
    rim_rear_cut = rounded_rect_prism(width=28.0, height=12.0, depth=3.0, radius=1.0, center_xy=(0.0, -20.0), z0=p.lidar_deck_z - 0.2)
    rim_side_cut = rounded_rect_prism(width=52.0, height=13.0, depth=3.0, radius=1.0, center_xy=(0.0, p.lidar_side_ear_y), z0=p.lidar_deck_z - 0.2)
    lidar_rim = rim_outer - rim_inner - rim_front_cut - rim_rear_cut - rim_side_cut

    tower = tower + lidar_plate + front_ear_lobe + front_side_corbels + side_ear_bosses + lidar_rim

    # =========================================================================
    # CUT OUT DOUBLED BREAKOUT CRADLE & CONTINUOUS 17.5mm USB PLUG WINDOW
    # =========================================================================
    # 1. Continuous 16.2 mm wide central USB plug & under-PCB tunnel (X = -8.1..+8.1 mm, Y = -30..+32 mm,
    #    from Z = 13.5 mm all the way up to Z = 30.8..31.4 mm):
    #    - Gives 3.5 mm clearance below the Z = 17.0 mm PCB seat for thick USB plug overmolds,
    #    - Gives 13.8..14.4 mm clearance above the Z = 17.0 mm PCB seat (17.3..17.9 mm total vertical window!),
    #    - Leaves zero material hanging below Z = 30.8 mm anywhere in X = -8.1..+8.1 mm!
    usb_tunnel_main = rounded_rect_prism(
        width=16.2,
        height=64.0,
        depth=deck_bot_z - p.usb_channel_floor_z,  # 17.3 mm tall (Z = 13.5..30.8 mm)
        radius=1.0,
        center_xy=(0.0, 1.0),
        z0=p.usb_channel_floor_z,
    )
    usb_tunnel_peak = rounded_rect_prism(
        width=14.6,
        height=64.0,
        depth=0.2,
        radius=0.8,
        center_xy=(0.0, 1.0),
        z0=deck_bot_z + 0.5,  # shallow 45-deg bevel to Z = 31.3 mm
    )
    tower = tower - (usb_tunnel_main + usb_tunnel_peak).hull()

    # 2. Main 40.6 x 20.3 mm Breakout Board Pocket (X = -10.15..+10.15 mm, Y = -19.8..+20.8 mm, Z = 17.0..28.8 mm)
    #    Seats the 20.0 mm wide PCB on two 2.025 mm wide side ledges at Z = 17.0 mm, while the 4 corner end-stops
    #    at X = +-8.1..+-10.15 mm (Y < -19.8 mm and Y > +20.8 mm) lock the 40.0 mm board in Y!
    brk_pocket_box = rounded_rect_prism(
        width=p.brk_pocket_wid,
        height=p.brk_pocket_len,
        depth=11.8,  # Z = 17.0..28.8 mm
        radius=0.8,
        center_xy=(0.0, 0.5),
        z0=p.brk_seat_z,
    )
    brk_pocket_roof = rounded_rect_prism(
        width=16.2,
        height=p.brk_pocket_len,
        depth=0.2,
        radius=0.8,
        center_xy=(0.0, 0.5),
        z0=deck_bot_z,  # 45-deg side transition from X = +-10.15 (Z=28.8) to X = +-8.1 (Z=30.8)
    )
    tower = tower - (brk_pocket_box + brk_pocket_roof).hull()

    # 3. Above Z = 22.0 mm (above the 5.0 mm tall corner Y-stops at Z = 17.0..22.0 mm), widen the front & rear
    #    end openings to the full 20.3 mm pocket width (Z = 22.0..30.8 mm) so extra-wide USB plugs also clear!
    upper_end_relief_box = rounded_rect_prism(
        width=p.brk_pocket_wid,
        height=64.0,
        depth=6.8,  # Z = 22.0..28.8 mm
        radius=0.8,
        center_xy=(0.0, 1.0),
        z0=p.brk_seat_z + 5.0,
    )
    upper_end_relief_roof = rounded_rect_prism(
        width=16.2,
        height=64.0,
        depth=0.2,
        radius=0.8,
        center_xy=(0.0, 1.0),
        z0=deck_bot_z,
    )
    tower = tower - (upper_end_relief_box + upper_end_relief_roof).hull()

    # 4. Add 4x Snap-Fit Top Retention Nibs along the X = +-10.15 mm cradle walls (at Y = -12.0 & +13.0 mm):
    #    Click over the top of the 1.6 mm PCB (Z = 17.0..18.6 mm) at Z = 18.6..20.0 mm without screws!
    for sign in (-1.0, +1.0):
        for ny in (-12.0, +13.0):
            nib = (
                rounded_rect_prism(width=1.2, height=4.8, depth=0.2, radius=0.3, center_xy=(sign * 9.85, ny), z0=19.3)
                + rounded_rect_prism(width=0.4, height=4.8, depth=1.6, radius=0.15, center_xy=(sign * 10.2, ny), z0=18.6)
            ).hull()
            tower = tower + nib

    # =========================================================================
    # DRILL ALL MOUNTING SLOTS & HEAT-SET INSERT BORES
    # =========================================================================
    # A. 4x Central Square Expansion-Plate Mounting Slots (X = +-16.875, Y = +-16.875 mm)
    #    4.3 x 4.3 mm stadium through-slots + Ø6.8 mm counterbores (100% open above Z = 3.6 mm!)
    for sx in (-p.deck_square_half, +p.deck_square_half):
        for sy in (-p.deck_square_half, +p.deck_square_half):
            tower = tower - stadium_slot_z(slot_width=4.3, slot_height=4.3, depth=12.0, cx=sx, cy=sy, z0=-1.0)
            tower = tower - cylinder_z(dia=6.8, depth=10.0, cx=sx, cy=sy, z0=3.6)

    # B. 4x Wide 49.0 mm C-to-C Expansion-Plate Mounting Slots (X = +-24.50 mm, Y = +2.0 & -32.75 mm)
    for wx in (-24.50, +24.50):
        for wy in (+2.0, p.deck_rear_hole_y):
            tower = tower - stadium_slot_z(slot_width=3.4, slot_height=4.8, depth=12.0, cx=wx, cy=wy, z0=-1.0)
            tower = tower - cylinder_z(dia=6.4, depth=10.0, cx=wx, cy=wy, z0=3.4)

    # C. 4x Radxa ZERO 3W Corner Mounting Bosses (X = +-28.75 mm, Y = -50.5 +- 11.25 mm)
    #    Top Ø3.2 x 4.2 mm M2 heat-set insert bore + through 3.6 x 3.2 mm oblong slot for 57-58 x 22-23 mm!
    for bx in (-sbc_hx, +sbc_hx):
        for by in (p.sbc_center_y - sbc_hy, p.sbc_center_y + sbc_hy):
            tower = tower - blind_insert_bore_from_top_z(
                bore_dia=p.m2_insert_dia,
                depth=4.2,
                z_top=p.sbc_standoff_z,
                cx=bx,
                cy=by,
            )
            tower = tower - stadium_slot_z(slot_width=3.6, slot_height=3.2, depth=10.0, cx=bx, cy=by, z0=-1.0)

    # D. 3x LDROBOT D500 LiDAR Mounting Ear Holes/Slots at Z = 35.0 mm:
    #    - Front Ear (X = 0.0, Y = +23.30 mm): Blind Ø3.2 mm M2 heat-set insert bore (depth 3.0 mm, bottom at Z = 31.6 mm)
    #      + Ø2.6 mm through-bore so NOTHING hangs below the Z = 30.8 mm bridge ceiling!
    tower = tower - blind_insert_bore_from_top_z(
        bore_dia=p.m2_insert_dia,
        depth=3.0,
        z_top=p.lidar_deck_z,
        cx=0.0,
        cy=p.lidar_front_ear_y,
    )
    tower = tower - cylinder_z(dia=2.6, depth=6.0, cx=0.0, cy=p.lidar_front_ear_y, z0=deck_bot_z - 0.5)

    #    - Left & Right Side Ears (X = +-21.95 mm, Y = -8.65 mm):
    #      5.4 x 2.9 mm horizontal stadium through-slots (covering both 42.69 mm CAD and 45.0 mm user-measured C-to-C!)
    #      + M2 insert bore at X = +-22.5 mm!
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
    # CREATE OPTIONAL 2-PIECE BOLT-TOGETHER SPLIT AT Z = 12.0 mm (1 BODY EACH!)
    # =========================================================================
    # Splitting at Z = 12.0 mm (inside the continuous mezzanine floor Z = 11.5..13.5 mm) guarantees
    # that both `tower_base` and `tower_top` are 1 single connected watertight solid body!
    split_z = 12.0
    lower_clip = rounded_rect_prism(width=140.0, height=160.0, depth=split_z, radius=2.0, center_xy=(0.0, -20.0), z0=0.0)
    upper_clip = rounded_rect_prism(width=140.0, height=160.0, depth=40.0, radius=2.0, center_xy=(0.0, -20.0), z0=split_z)

    tower_base = tower ^ lower_clip
    tower_top = (tower ^ upper_clip).translate([0.0, 0.0, -split_z])

    # Add 2x M3 heat-set insert bores in tower_base (at X = +-19.6, Y = +9.5 mm, Z = 12.0 mm)
    for sign in (-1.0, +1.0):
        tower_base = tower_base - blind_insert_bore_from_top_z(
            bore_dia=p.m3_insert_dia,
            depth=6.0,
            z_top=split_z,
            cx=sign * 19.6,
            cy=9.5,
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
        bodies = mesh.split(only_watertight=False)
        body_count = len(bodies)
        stl_path = out_dir / filename
        mesh.export(stl_path)
        extents = mesh.extents.round(2).tolist()
        summary["files"][filename] = {
            "path": str(stl_path),
            "watertight": bool(mesh.is_watertight),
            "body_count": int(body_count),
            "bounding_box_mm": extents,
            "volume_cm3": round(float(mesh.volume) / 1000.0, 2),
            "triangles": int(len(mesh.faces)),
        }
        print(
            f"[OK] {filename:28s} | watertight={mesh.is_watertight} | bodies={body_count} | "
            f"bbox={extents[0]:.1f}x{extents[1]:.1f}x{extents[2]:.1f} mm | "
            f"vol={mesh.volume/1000.0:.2f} cm^3 | tris={len(mesh.faces)}"
        )
        assert mesh.is_watertight, f"{filename} is not watertight!"
        assert body_count == 1, f"{filename} split into {body_count} bodies (expected 1)!"

    meta_path = out_dir / "lidar_tower_dimensions.json"
    meta_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--lidar-deck-z", type=float, default=35.0, help="LiDAR platform elevation above deck (mm)")
    args = parser.parse_args()

    params = LidarTowerParams(lidar_deck_z=args.lidar_deck_z)
    generate_all(args.out_dir, params)


if __name__ == "__main__":
    main()
