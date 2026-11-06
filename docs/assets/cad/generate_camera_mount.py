#!/usr/bin/env python3
"""Parametric 3D-printable stereo camera enclosure & mount generator for horaceTheCheese.

Generates three support-free, watertight STL files in `cad/camera_mount/`:
  1. `horace_cam_back_mount.stl` — Rear PCB cradle + WAVE ROVER 90-deg expansion plate
     bracket (with anti-rotation notch keys & M2 nut traps) + Mini-USB strain-relief clamp
  2. `horace_cam_front_visor.stl` — Front protective cover + retro binocular lens bezels
     + sun-visor brow
  3. `horace_cam_usb_shim.stl` — Parametric snap-in Mini-USB plug overmold collar insert

All dimensions are extracted from:
  - Official Waveshare Expansion Plate CAD (`WAVE ROVER-EP DXF.dxf`)
  - High-resolution workbench calibration photos on the 5x5 mm metric grid
    (`P1044915.JPG`, `P1044916.JPG`, `P1044926.JPG`, `P1044927.JPG`, `P1044928.JPG`)
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
class CameraMountParams:
    # --- 1. Stereo Camera PCB & Optics (measured from 5x5 mm grid photos) ---
    pcb_width: float = 95.0            # mm (measured 95.0-95.4 mm across P1044926/P1044927)
    pcb_height: float = 20.0           # mm (4.0 cm to 6.0 cm on grid = 4 x 5 mm squares)
    pcb_thickness: float = 1.6         # mm (standard FR4)
    pcb_clearance: float = 0.5         # mm per side pocket clearance -> 96.0 x 21.0 mm cavity

    lens_baseline: float = 80.0        # mm center-to-center (X = -40.0 and +40.0 mm)
    lens_base_size: float = 14.0       # mm square M12 lens holder base on PCB
    lens_barrel_dia: float = 14.0      # mm cylindrical M12 barrel OD
    lens_cap_dia: float = 15.0         # mm translucent dust cap OD
    lens_visor_bore_dia: float = 16.6  # mm visor opening (clears barrel + dust cap)
    lens_total_protrusion: float = 19.0  # mm above PCB front face (with cap)

    # PCB M2 mounting hole locations relative to PCB center (0, 0)
    hole_outer_x: float = 46.0         # mm (+-46.0 mm = 92.0 mm C-to-C)
    hole_inner_outer_x: float = 26.1   # mm (+-26.1 mm = 52.2 mm C-to-C, flanking ribbons)
    hole_inner_inner_x: float = 22.1   # mm (+-22.1 mm = 44.2 mm C-to-C, flanking ribbons)
    hole_y: float = 8.5                # mm (+-8.5 mm = 17.0 mm vertical C-to-C)
    pcb_m2_hole_dia: float = 2.0       # mm M2 pilot/through hole in bosses

    # --- 2. WAVE ROVER Expansion Plate 90° Front Bracket (from DXF + P1044916) ---
    tab_thickness: float = 2.0         # mm sheet metal thickness (DXF: 54.163 - 52.163 = 2.00 mm)
    tab_width: float = 44.88           # mm upturned tab width (DXF: -22.441 to +22.442 mm)
    tab_height_above_deck: float = 19.63  # mm above top face of main plate
    tab_top_bar_height: float = 4.22   # mm height of upper crossbar above central window
    tab_hole_spacing_min: float = 20.0 # mm grid measurement (25 mm to 45 mm lines)
    tab_hole_spacing_dxf: float = 21.0 # mm DXF measurement (+-10.500 mm)
    tab_hole_dia: float = 2.4          # mm M2 clearance slot height
    tab_notch_inner_x: float = 5.89    # mm DXF inner edge of half-square notch
    tab_notch_outer_x: float = 9.01    # mm DXF outer edge of half-square notch
    tab_window_width: float = 25.75    # mm DXF central U-window width (+-12.877 mm)
    tab_window_height: float = 8.10    # mm DXF central U-window flat vertical height

    # --- 3. Mini-USB Receptacle & Strain-Relief Plug Holder ---
    usb_port_width: float = 7.0        # mm Mini-USB receptacle width at X = 0
    usb_bay_inner_width: float = 13.0  # mm max overmold width in clamp bay (without shim)
    usb_bay_inner_depth: float = 9.0   # mm max overmold depth in clamp bay (without shim)
    usb_clamp_length: float = 16.0     # mm vertical length of strain-relief collar below shell
    usb_plug_width: float = 10.2       # mm default Mini-USB plug overmold width (for shim)
    usb_plug_depth: float = 7.0        # mm default Mini-USB plug overmold depth (for shim)
    usb_cable_dia: float = 4.5         # mm round USB cable neck diameter (for shim)

    # --- 4. Enclosure Shell & Retro Visor Styling ---
    wall_thickness: float = 2.5        # mm perimeter wall
    corner_radius: float = 4.2         # mm outer rounded corner radius
    back_thickness: float = 5.0        # mm z=0 (rear face) to z=5.0 (PCB rear support plane)
    pcb_recess_depth: float = 1.8      # mm SMD clearance pocket behind PCB (z=3.2 to 5.0)
    shell_front_z: float = 8.2         # mm top of rear shell perimeter walls (cradles 1.6mm PCB)


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
    prism = mf.Manifold.extrude(cross, depth)
    return prism.translate([0.0, 0.0, z0])


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
    cyl = mf.Manifold.cylinder(depth, r, r, segments)
    return cyl.translate([cx, cy, z0])


def stadium_slot_z(
    slot_width: float,
    slot_height: float,
    depth: float,
    cx: float = 0.0,
    cy: float = 0.0,
    z0: float = 0.0,
    segments: int = 36,
) -> mf.Manifold:
    """Create a horizontal stadium/oblong slot along X extruded in Z."""
    return rounded_rect_prism(
        width=slot_width,
        height=slot_height,
        depth=depth,
        radius=min(slot_width, slot_height) * 0.49,
        center_xy=(cx, cy),
        z0=z0,
        segments=segments,
    )


def hex_nut_prism_z(
    flat_to_flat: float,
    depth: float,
    cx: float = 0.0,
    cy: float = 0.0,
    z0: float = 0.0,
) -> mf.Manifold:
    """Create a regular hexagon nut trap along Z with given across-flats width."""
    r_circum = flat_to_flat / math.sqrt(3.0)
    pts = [
        [cx + r_circum * math.cos(i * math.pi / 3.0), cy + r_circum * math.sin(i * math.pi / 3.0)]
        for i in range(6)
    ]
    cross = mf.CrossSection([np.array(pts, dtype=np.float32)])
    return mf.Manifold.extrude(cross, depth).translate([0.0, 0.0, z0])


def build_back_mount(p: CameraMountParams) -> mf.Manifold:
    """Build `horace_cam_back_mount.stl` (Print flat on Z=0 with zero supports)."""
    cav_w = p.pcb_width + 2.0 * p.pcb_clearance   # 96.0 mm
    cav_h = p.pcb_height + 2.0 * p.pcb_clearance  # 21.0 mm
    outer_w = cav_w + 2.0 * p.wall_thickness      # 101.0 mm
    outer_h = cav_h + 2.0 * p.wall_thickness      # 26.0 mm

    # 1. Main rear enclosure body (z = 0.0 to shell_front_z = 8.2 mm)
    body = rounded_rect_prism(
        width=outer_w,
        height=outer_h,
        depth=p.shell_front_z,
        radius=p.corner_radius,
        center_xy=(0.0, 0.0),
        z0=0.0,
    )

    # 2. Integrated Mini-USB strain-relief collar extending below bottom wall (y = -13.0 to -29.0 mm)
    clamp_outer_w = p.usb_bay_inner_width + 6.0  # 19.0 mm
    clamp_y_top = -outer_h * 0.5 + 1.0           # overlaps bottom wall by 1.0 mm
    clamp_y_bot = -outer_h * 0.5 - p.usb_clamp_length
    clamp_h = clamp_y_top - clamp_y_bot
    clamp_yc = 0.5 * (clamp_y_top + clamp_y_bot)
    clamp_z_top = p.back_thickness + p.pcb_thickness + p.usb_bay_inner_depth + 2.2  # 17.8 mm

    usb_collar = rounded_rect_prism(
        width=clamp_outer_w,
        height=clamp_h,
        depth=clamp_z_top,
        radius=2.8,
        center_xy=(0.0, clamp_yc),
        z0=0.0,
    )

    # M3 pinch-clamp ears on the lower USB collar (x = -13.5..+13.5 mm, y = -23.5..-16.5 mm, z = 5.0..16.5 mm)
    ear_w = clamp_outer_w + 8.0  # 27.0 mm across ears
    ear_h = 7.2
    ear_yc = clamp_yc - 1.0
    pinch_ears = rounded_rect_prism(
        width=ear_w,
        height=ear_h,
        depth=11.0,
        radius=2.2,
        center_xy=(0.0, ear_yc),
        z0=5.5,
    )
    body = body + usb_collar + pinch_ears

    # 3. Cut out the PCB cradle cavity (z = p.back_thickness [5.0] to shell_front_z + 1)
    pcb_pocket = rounded_rect_prism(
        width=cav_w,
        height=cav_h,
        depth=p.shell_front_z - p.back_thickness + 1.0,
        radius=1.2,
        center_xy=(0.0, 0.0),
        z0=p.back_thickness,
    )
    body = body - pcb_pocket

    # 4. Cut out the deeper rear SMD clearance pocket (z = 3.2 to 5.0 mm) leaving a 1.2 mm perimeter ledge
    smd_pocket = rounded_rect_prism(
        width=p.pcb_width - 2.4,
        height=p.pcb_height - 2.4,
        depth=p.pcb_recess_depth + 0.5,
        radius=1.5,
        center_xy=(0.0, 0.0),
        z0=p.back_thickness - p.pcb_recess_depth,
    )
    body = body - smd_pocket

    # 5. Add the 8 M2 PCB support bosses rising from z=3.2 to z=5.0 mm (plus 1.2mm locator lip for inner holes)
    boss_coords = [
        (-p.hole_outer_x, +p.hole_y),
        (+p.hole_outer_x, +p.hole_y),
        (-p.hole_outer_x, -p.hole_y),
        (+p.hole_outer_x, -p.hole_y),
        (-p.hole_inner_inner_x, +p.hole_y),
        (+p.hole_inner_inner_x, +p.hole_y),
        (-p.hole_inner_inner_x, -p.hole_y),
        (+p.hole_inner_inner_x, -p.hole_y),
    ]
    for bx, by in boss_coords:
        body = body + cylinder_z(dia=5.0, depth=p.pcb_recess_depth, cx=bx, cy=by, z0=p.back_thickness - p.pcb_recess_depth)

    # Also add support pads at the second inner hole pair (+-26.1 mm)
    for bx in (-p.hole_inner_outer_x, +p.hole_inner_outer_x):
        for by in (-p.hole_y, +p.hole_y):
            body = body + cylinder_z(dia=4.6, depth=p.pcb_recess_depth, cx=bx, cy=by, z0=p.back_thickness - p.pcb_recess_depth)

    # Drill M2 pilot/through holes + rear hex nut traps in the 8 main PCB bosses
    for bx, by in boss_coords:
        body = body - cylinder_z(dia=p.pcb_m2_hole_dia, depth=p.shell_front_z + 2.0, cx=bx, cy=by, z0=-0.5)
        body = body - hex_nut_prism_z(flat_to_flat=4.3, depth=1.8, cx=bx, cy=by, z0=-0.01)

    # 6. Carve the Mini-USB plug tunnel & receptacle passage
    # Receptacle neck from PCB (y = -13.5..-9.0, z = 4.8..12.5)
    usb_neck = rounded_rect_prism(
        width=p.usb_port_width + 3.0,
        height=7.0,
        depth=8.2,
        radius=1.0,
        center_xy=(0.0, -cav_h * 0.5),
        z0=4.8,
    )
    # Main overmold bay inside the lower collar (13.0 x 9.0 mm, z = 5.6..14.6 mm)
    usb_bay_z0 = p.back_thickness + 0.6
    usb_bay = rounded_rect_prism(
        width=p.usb_bay_inner_width,
        height=clamp_h + 4.0,
        depth=p.usb_bay_inner_depth,
        radius=1.6,
        center_xy=(0.0, clamp_yc),
        z0=usb_bay_z0,
    )
    # Shim retention side grooves inside USB bay (14.2 mm wide x 3.0 mm tall at z = 8.6..11.6 mm)
    shim_groove = rounded_rect_prism(
        width=p.usb_bay_inner_width + 1.4,
        height=clamp_h - 3.0,
        depth=3.0,
        radius=0.8,
        center_xy=(0.0, clamp_yc - 0.5),
        z0=usb_bay_z0 + 3.0,
    )
    # Front flex slit (1.8 mm wide) through front of collar so M3 screw or zip-tie can pinch the plug
    flex_slit = rounded_rect_prism(
        width=1.8,
        height=clamp_h + 2.0,
        depth=6.0,
        radius=0.4,
        center_xy=(0.0, clamp_yc - 1.0),
        z0=usb_bay_z0 + p.usb_bay_inner_depth - 1.0,
    )
    body = body - usb_neck - usb_bay - shim_groove - flex_slit

    # M3 horizontal pinch bolt hole (along X at y = ear_yc, z = 11.0 mm) + hex nut trap on right ear
    m3_cyl = cylinder_z(dia=3.3, depth=ear_w + 4.0, cx=0.0, cy=0.0, z0=-0.5 * (ear_w + 4.0))
    # Rotate cylinder from Z axis to X axis (90 deg around Y)
    m3_bolt = m3_cyl.rotate([0.0, 90.0, 0.0]).translate([0.0, ear_yc, 11.0])
    m3_nut = (
        hex_nut_prism_z(flat_to_flat=5.7, depth=3.0, cx=0.0, cy=0.0, z0=0.0)
        .rotate([0.0, 90.0, 0.0])
        .translate([ear_w * 0.5 - 2.5, ear_yc, 11.0])
    )
    body = body - m3_bolt - m3_nut

    # Zip-tie channel wrapping around the USB collar at y = clamp_yc + 3.2 mm (4.2 mm tall groove)
    ziptie_y = clamp_yc + 3.2
    zip_left = rounded_rect_prism(width=2.0, height=4.2, depth=clamp_z_top + 1.0, radius=0.5, center_xy=(-clamp_outer_w * 0.5 + 0.6, ziptie_y), z0=-0.5)
    zip_right = rounded_rect_prism(width=2.0, height=4.2, depth=clamp_z_top + 1.0, radius=0.5, center_xy=(+clamp_outer_w * 0.5 - 0.6, ziptie_y), z0=-0.5)
    zip_front = rounded_rect_prism(width=clamp_outer_w + 2.0, height=4.2, depth=1.8, radius=0.5, center_xy=(0.0, ziptie_y), z0=clamp_z_top - 1.4)
    zip_back_tunnel = rounded_rect_prism(width=clamp_outer_w + 2.0, height=4.2, depth=2.0, radius=0.5, center_xy=(0.0, ziptie_y), z0=2.2)
    body = body - zip_left - zip_right - zip_front - zip_back_tunnel

    # 7. WAVE ROVER Expansion Plate 90° Upturned Bracket Interface on Rear Face (z = 0.0 .. 2.1 mm)
    # We recess a 2.10 mm deep seat for the 44.88 mm wide x 4.22 mm tall top crossbar of the upturned metal tab
    # at y = -5.6 mm to -1.2 mm, WHILE LEAVING the two anti-rotation keys (at X = +-7.45 mm) and the lower
    # U-window boss (X = -12.5..+12.5 mm) proud at z = 0.0 so they lock into the metal tab's square notches!
    seat_w = p.tab_width + 0.52       # 45.40 mm (hugs 44.88 mm metal tab with 0.26 mm clearance per side)
    seat_depth = p.tab_thickness + 0.10  # 2.10 mm deep into z=0..5.0 backplate
    crossbar_y_top = -1.2             # top edge of upturned metal tab butts against this ledge
    crossbar_y_bot = -5.5             # 4.3 mm tall crossbar seat

    # Carve the top crossbar seat (y = -5.5 to -1.2 mm, x = -22.7 to +22.7 mm, z = 0 to 2.1 mm)
    crossbar_seat = rounded_rect_prism(
        width=seat_w,
        height=crossbar_y_top - crossbar_y_bot,
        depth=seat_depth + 0.02,
        radius=0.8,
        center_xy=(0.0, 0.5 * (crossbar_y_top + crossbar_y_bot)),
        z0=-0.01,
    )
    # Carve the two side leg seats below the crossbar (x = -22.7..-13.0 and +13.0..+22.7 mm, y = -29.0..-5.0 mm)
    leg_w = (seat_w - (p.tab_window_width + 0.25)) * 0.5
    leg_x_center = 0.5 * (seat_w * 0.5 + (p.tab_window_width + 0.25) * 0.5)
    left_leg_seat = rounded_rect_prism(
        width=leg_w,
        height=24.0,
        depth=seat_depth + 0.02,
        radius=0.6,
        center_xy=(-leg_x_center, -17.0),
        z0=-0.01,
    )
    right_leg_seat = rounded_rect_prism(
        width=leg_w,
        height=24.0,
        depth=seat_depth + 0.02,
        radius=0.6,
        center_xy=(+leg_x_center, -17.0),
        z0=-0.01,
    )
    body = body - crossbar_seat - left_leg_seat - right_leg_seat

    # Add back the TWO ANTI-ROTATION KEYS that drop into the upturned tab's two "half-square" notches!
    # DXF notch bounds: X = +-5.89 to +-9.01 mm (width = 3.12 mm, center = +-7.45 mm).
    # We make each key 2.70 mm wide x 2.60 mm tall, extending from the lower window up into the notch at z = 0.0..2.10 mm!
    key_xc = 0.5 * (p.tab_notch_inner_x + p.tab_notch_outer_x)  # 7.45 mm
    key_w = (p.tab_notch_outer_x - p.tab_notch_inner_x) - 0.42  # 2.70 mm
    for sign in (-1.0, +1.0):
        anti_rot_key = rounded_rect_prism(
            width=key_w,
            height=3.0,
            depth=seat_depth,
            radius=0.5,
            center_xy=(sign * key_xc, crossbar_y_bot + 0.9),
            z0=0.0,
        )
        body = body + anti_rot_key

    # Drill the two M2/M2.5 mounting slots through the crossbar seat (centered at X = +-10.25 mm, Y = -3.35 mm)
    # Slot width = 3.5 mm covers both 20.0 mm grid spacing (X=+-10.0) and 21.0 mm DXF spacing (X=+-10.5)!
    bolt_y = 0.5 * (crossbar_y_top + crossbar_y_bot)
    bolt_xc = 0.25 * (p.tab_hole_spacing_min + p.tab_hole_spacing_dxf)  # 10.25 mm
    for sign in (-1.0, +1.0):
        slot = stadium_slot_z(
            slot_width=3.5,
            slot_height=p.tab_hole_dia,
            depth=p.back_thickness + 2.0,
            cx=sign * bolt_xc,
            cy=bolt_y,
            z0=-0.5,
        )
        # Captive M2 hex nut pocket on the inside of the backplate (z = 3.2..5.2 mm)
        nut_pocket = rounded_rect_prism(
            width=5.2,
            height=4.5,
            depth=2.2,
            radius=0.6,
            center_xy=(sign * bolt_xc, bolt_y),
            z0=p.back_thickness - 1.9,
        )
        body = body - slot - nut_pocket

    return body


def build_front_visor(p: CameraMountParams) -> mf.Manifold:
    """Build `horace_cam_front_visor.stl` (Print flat on Z=0 back face with zero supports)."""
    cav_w = p.pcb_width + 2.0 * p.pcb_clearance   # 96.0 mm
    cav_h = p.pcb_height + 2.0 * p.pcb_clearance  # 21.0 mm
    outer_w = cav_w + 2.0 * p.wall_thickness      # 101.0 mm
    outer_h = cav_h + 2.0 * p.wall_thickness      # 26.0 mm

    visor_plate_h = 8.5  # main visor body thickness (z = 0 to 8.5 mm)

    # 1. Main visor body
    visor = rounded_rect_prism(
        width=outer_w,
        height=outer_h,
        depth=visor_plate_h,
        radius=p.corner_radius,
        center_xy=(0.0, 0.0),
        z0=0.0,
    )

    # 2. Raised binocular lens turrets at X = -40.0 and +40.0 mm (z = 0 to 13.5 mm)
    turret_od = p.lens_visor_bore_dia + 5.4  # 22.0 mm OD
    turret_h = 13.5
    for lx in (-p.lens_baseline * 0.5, +p.lens_baseline * 0.5):
        visor = visor + cylinder_z(dia=turret_od, depth=turret_h, cx=lx, cy=0.0, z0=0.0, segments=64)

    # 3. Retro 70s sun-visor brow along the upper edge (y = +8.5 to +13.0 mm, z = 0 to 14.5 mm)
    brow_depth = 14.5
    top_brow = rounded_rect_prism(
        width=outer_w,
        height=4.2,
        depth=brow_depth,
        radius=2.0,
        center_xy=(0.0, outer_h * 0.5 - 2.1),
        z0=0.0,
    )
    # Trim brow ends inside outer shell footprint
    outer_clip = rounded_rect_prism(
        width=outer_w,
        height=outer_h,
        depth=20.0,
        radius=p.corner_radius,
        center_xy=(0.0, 0.0),
        z0=0.0,
    )
    visor = visor + (top_brow ^ outer_clip)

    # 4. Cut out inner electronics & FFC ribbon protection chamber (z = 0 to 6.5 mm, x = -31.5 to +31.5 mm)
    ribbon_chamber = rounded_rect_prism(
        width=63.0,
        height=cav_h - 1.0,
        depth=6.5,
        radius=2.0,
        center_xy=(0.0, 0.0),
        z0=-0.1,
    )
    # Shallow 2.0 mm recess across full PCB footprint (z = 0 to 2.0 mm) to clear 14x14 mm square lens bases
    lens_base_recess = rounded_rect_prism(
        width=cav_w - 0.4,
        height=cav_h - 0.4,
        depth=2.2,
        radius=1.2,
        center_xy=(0.0, 0.0),
        z0=-0.1,
    )
    visor = visor - ribbon_chamber - lens_base_recess

    # 5. Cut out the two circular binocular lens bores (dia = 16.6 mm at X = -40.0 and +40.0 mm)
    for lx in (-p.lens_baseline * 0.5, +p.lens_baseline * 0.5):
        visor = visor - cylinder_z(dia=p.lens_visor_bore_dia, depth=25.0, cx=lx, cy=0.0, z0=-1.0, segments=64)
        # Square 14.6 x 14.6 mm pocket on back of visor (z = 0 to 5.5 mm) for the 14x14 mm M12 lens base
        base_pocket = rounded_rect_prism(
            width=p.lens_base_size + 0.8,
            height=p.lens_base_size + 0.8,
            depth=5.5,
            radius=0.8,
            center_xy=(lx, 0.0),
            z0=-0.1,
        )
        visor = visor - base_pocket

    # 6. Cut out bottom-center arch for Mini-USB connector & plug
    usb_arch = rounded_rect_prism(
        width=p.usb_bay_inner_width + 0.6,
        height=11.0,
        depth=12.0,
        radius=2.0,
        center_xy=(0.0, -outer_h * 0.5 + 2.0),
        z0=-0.5,
    )
    visor = visor - usb_arch

    # 7. Drill 4 outer corner M2 screw holes + counterbores (and 4 inner M2 holes)
    corner_holes = [
        (-p.hole_outer_x, +p.hole_y),
        (+p.hole_outer_x, +p.hole_y),
        (-p.hole_outer_x, -p.hole_y),
        (+p.hole_outer_x, -p.hole_y),
    ]
    for hx, hy in corner_holes:
        visor = visor - cylinder_z(dia=2.3, depth=20.0, cx=hx, cy=hy, z0=-1.0)
        visor = visor - cylinder_z(dia=4.4, depth=12.0, cx=hx, cy=hy, z0=4.5)

    for hx in (-p.hole_inner_inner_x, +p.hole_inner_inner_x):
        for hy in (-p.hole_y, +p.hole_y):
            visor = visor - cylinder_z(dia=2.3, depth=20.0, cx=hx, cy=hy, z0=-1.0)
            visor = visor - cylinder_z(dia=4.2, depth=10.0, cx=hx, cy=hy, z0=5.5)

    return visor


def build_usb_shim(p: CameraMountParams) -> mf.Manifold:
    """Build `horace_cam_usb_shim.stl` (Parametric snap-in Mini-USB plug collar insert)."""
    shim_len = p.usb_clamp_length - 2.0  # 14.0 mm tall along Z
    outer_w = p.usb_bay_inner_width - 0.35  # 12.65 mm
    outer_d = p.usb_bay_inner_depth - 0.30  # 8.70 mm

    outer = rounded_rect_prism(
        width=outer_w,
        height=outer_d,
        depth=shim_len,
        radius=1.4,
        center_xy=(0.0, 0.0),
        z0=0.0,
    )
    # Retention ribs on sides that snap into the USB bay's internal groove
    rib = rounded_rect_prism(
        width=outer_w + 1.0,
        height=2.4,
        depth=shim_len - 2.0,
        radius=0.6,
        center_xy=(0.0, 0.0),
        z0=1.0,
    )
    shim = outer + rib

    # Upper plug overmold cavity (z = 3.5 to shim_len + 1)
    plug_cav = rounded_rect_prism(
        width=p.usb_plug_width,
        height=p.usb_plug_depth,
        depth=shim_len,
        radius=1.0,
        center_xy=(0.0, 0.0),
        z0=3.5,
    )
    # Lower round cable strain-relief bore (z = -1 to 5.0 mm)
    cable_bore = cylinder_z(dia=p.usb_cable_dia, depth=6.0, cx=0.0, cy=0.0, z0=-0.5)
    # Front U-opening slot so the shim can slip over an already-connected cable
    front_slot = rounded_rect_prism(
        width=max(2.6, p.usb_cable_dia - 0.4),
        height=outer_d,
        depth=shim_len + 2.0,
        radius=0.5,
        center_xy=(0.0, outer_d * 0.5),
        z0=-1.0,
    )
    return shim - plug_cav - cable_bore - front_slot


def manifold_to_trimesh(m: mf.Manifold) -> trimesh.Trimesh:
    mesh_data = m.to_mesh()
    verts = np.array(mesh_data.vert_properties[:, :3], dtype=np.float64)
    faces = np.array(mesh_data.tri_verts, dtype=np.int64)
    return trimesh.Trimesh(vertices=verts, faces=faces, process=True)


def generate_all(out_dir: Path, params: CameraMountParams) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        ("horace_cam_back_mount.stl", build_back_mount(params)),
        ("horace_cam_front_visor.stl", build_front_visor(params)),
        ("horace_cam_usb_shim.stl", build_usb_shim(params)),
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

    meta_path = out_dir / "camera_mount_dimensions.json"
    meta_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--lens-baseline", type=float, default=80.0, help="Stereo lens center-to-center baseline (mm)")
    parser.add_argument("--usb-plug-width", type=float, default=10.2, help="Mini-USB plug overmold width for shim (mm)")
    parser.add_argument("--usb-plug-depth", type=float, default=7.0, help="Mini-USB plug overmold depth for shim (mm)")
    parser.add_argument("--usb-cable-dia", type=float, default=4.5, help="Mini-USB cable neck OD for shim (mm)")
    args = parser.parse_args()

    params = CameraMountParams(
        lens_baseline=args.lens_baseline,
        usb_plug_width=args.usb_plug_width,
        usb_plug_depth=args.usb_plug_depth,
        usb_cable_dia=args.usb_cable_dia,
    )
    generate_all(args.out_dir, params)


if __name__ == "__main__":
    main()
