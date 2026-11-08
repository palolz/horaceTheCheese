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

    # --- 4. Enclosure Shell, Structural Gussets & Heat-Set Threaded Inserts (v2) ---
    wall_thickness: float = 3.2        # mm reinforced perimeter wall (up from 2.5 mm)
    corner_radius: float = 4.8         # mm outer rounded corner radius
    back_thickness: float = 6.8        # mm z=0 (flat rear bed face) to z=6.8 (PCB rear seating plane)
    pcb_recess_depth: float = 1.4      # mm SMD clearance pocket behind PCB (z=5.4 to 6.8 -> 5.4 mm solid floor!)
    shell_front_z: float = 9.8         # mm top of rear shell perimeter walls (cradles 1.6mm PCB at z=6.8..8.4)

    # Heat-set brass threaded insert specs (NO hex nut recesses!)
    m3_insert_bore_dia: float = 4.0    # mm standard melt bore for M3 brass heat-set inserts (OD 4.5-5.0 mm)
    m3_insert_depth: float = 6.5       # mm bore depth for M3 x 4/5/6 mm inserts
    m3_clearance_dia: float = 3.4      # mm M3 screw clearance through-hole
    m2_insert_bore_dia: float = 3.2    # mm standard melt bore for M2 brass heat-set inserts (OD 3.2-3.5 mm)
    m2_insert_depth: float = 4.5       # mm bore depth for M2 x 3/4 mm inserts
    pcb_locator_pin_dia: float = 1.85  # mm press-fit locating pin for Ø2.0 mm inner PCB holes
    outer_m3_ear_x: float = 51.5       # mm (+-51.5 mm = 103.0 mm C-to-C outer M3 cover-to-cover bolts)


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


def polygon_prism_z(
    points_xy: list[Tuple[float, float]],
    depth: float,
    z0: float = 0.0,
) -> mf.Manifold:
    """Extrude a 2D polygon in X-Y from z=z0 to z=z0+depth (auto-orienting CCW)."""
    arr = np.array(points_xy, dtype=np.float32)
    # Signed area via shoelace formula; reverse if clockwise so Manifold treats it as solid
    x, y = arr[:, 0], arr[:, 1]
    area2 = float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
    if area2 < 0.0:
        arr = arr[::-1].copy()
    cross = mf.CrossSection([arr])
    return mf.Manifold.extrude(cross, depth).translate([0.0, 0.0, z0])


def blind_insert_bore_from_top_z(
    bore_dia: float,
    depth: float,
    z_top: float,
    cx: float,
    cy: float,
    chamfer_extra: float = 0.8,
    chamfer_depth: float = 0.6,
    segments: int = 48,
) -> mf.Manifold:
    """Create a blind heat-set insert bore opening at z=z_top and going down (-Z) by `depth`.

    Includes a 45-deg soldering-iron alignment lead-in chamfer at the top mouth and a
    stepped/conical bottom relief so displaced molten plastic never blocks full insertion.
    """
    r_bore = bore_dia * 0.5
    r_chamfer = (bore_dia + chamfer_extra) * 0.5
    z_bot = z_top - depth
    main_cyl = mf.Manifold.cylinder(depth + 0.05, r_bore, r_bore, segments).translate([cx, cy, z_bot])
    lead_in = mf.Manifold.cylinder(
        chamfer_depth + 0.05, r_bore, r_chamfer, segments
    ).translate([cx, cy, z_top - chamfer_depth])
    bottom_cone = mf.Manifold.cylinder(
        r_bore * 0.8, 0.2, r_bore, segments
    ).translate([cx, cy, z_bot - r_bore * 0.8 + 0.02])
    return main_cyl + lead_in + bottom_cone


def blind_insert_bore_from_bottom_z(
    bore_dia: float,
    depth: float,
    cx: float,
    cy: float,
    z0: float = 0.0,
    chamfer_extra: float = 0.8,
    chamfer_depth: float = 0.6,
    segments: int = 48,
) -> mf.Manifold:
    """Create a blind heat-set insert bore opening on the flat build plate z=z0 going up (+Z).

    Terminates in a 45-deg self-supporting conical drill-point tip at the top so it prints
    100% support-free on an FDM printer with zero flat horizontal ceiling!
    """
    r_bore = bore_dia * 0.5
    r_chamfer = (bore_dia + chamfer_extra) * 0.5
    main_cyl = mf.Manifold.cylinder(depth, r_bore, r_bore, segments).translate([cx, cy, z0 - 0.02])
    lead_in = mf.Manifold.cylinder(
        chamfer_depth + 0.02, r_chamfer, r_bore, segments
    ).translate([cx, cy, z0 - 0.02])
    top_cone = mf.Manifold.cylinder(
        r_bore, r_bore, 0.15, segments
    ).translate([cx, cy, z0 + depth - 0.02])
    return main_cyl + lead_in + top_cone


def build_back_mount(p: CameraMountParams) -> mf.Manifold:
    """Build `horace_cam_back_mount_v2.stl` (100% flat Z=0 rear face, M3/M2 heat-set inserts, zero hex nuts)."""
    cav_w = p.pcb_width + 2.0 * p.pcb_clearance   # 96.0 mm
    cav_h = p.pcb_height + 2.0 * p.pcb_clearance  # 21.0 mm
    # Widen outer shell to 111.0 x 27.4 mm so 4x M3 heat-set insert bosses sit at X = +-51.5 mm outside the PCB!
    outer_w = 2.0 * p.outer_m3_ear_x + 8.0        # 111.0 mm
    outer_h = cav_h + 2.0 * p.wall_thickness      # 27.4 mm

    # 1. Main upper camera housing body (z = 0.0 to shell_front_z = 9.8 mm)
    # Entire rear face at z = 0.0 mm is 100% flat on the print bed!
    body = rounded_rect_prism(
        width=outer_w,
        height=outer_h,
        depth=p.shell_front_z,
        radius=p.corner_radius,
        center_xy=(0.0, 0.0),
        z0=0.0,
    )

    # 2. Structural Gusset Wings & Wide Lower Bracket Spine (y = -25.5 to -10.0 mm)
    # Eliminates the v1 narrow neck weak point by sweeping a 34 mm wide lower bracket block
    # smoothly out to X = +-44.0 mm on the main camera body, plus raised diagonal gusset ribs!
    spine_y_bot = -25.5
    spine_y_top = -10.0
    gusset_poly = [
        (-44.0, -11.5),
        (+44.0, -11.5),
        (+27.0, -18.5),
        (+17.0, spine_y_bot),
        (-17.0, spine_y_bot),
        (-27.0, -18.5),
    ]
    gusset_plate = polygon_prism_z(gusset_poly, depth=p.back_thickness + 0.8, z0=0.0)

    # Central reinforced bracket & Mini-USB spine block (34.0 mm wide at top, 28.0 mm at bottom, z = 0..10.5 mm)
    spine_block = rounded_rect_prism(
        width=31.0,
        height=spine_y_top - spine_y_bot + 2.0,
        depth=10.5,
        radius=3.2,
        center_xy=(0.0, 0.5 * (spine_y_top + spine_y_bot)),
        z0=0.0,
    )

    # Two raised diagonal stiffening ribs (z = 0.0 to shell_front_z = 9.8 mm) triangulating bracket to camera wings
    left_rib_pts = [
        (-13.5, -24.5),
        (-9.5, -24.5),
        (-33.0, -11.5),
        (-39.5, -11.5),
    ]
    right_rib_pts = [
        (+9.5, -24.5),
        (+13.5, -24.5),
        (+39.5, -11.5),
        (+33.0, -11.5),
    ]
    left_rib = polygon_prism_z(left_rib_pts, depth=p.shell_front_z, z0=0.0)
    right_rib = polygon_prism_z(right_rib_pts, depth=p.shell_front_z, z0=0.0)
    body = body + gusset_plate + spine_block + left_rib + right_rib

    # 3. Integrated Mini-USB strain-relief collar & M3 Heat-Set Insert Pinch Jaws
    clamp_outer_w = p.usb_bay_inner_width + 7.0  # 20.0 mm outer collar width
    clamp_y_top = -outer_h * 0.5 + 1.5           # overlaps bottom wall
    clamp_y_bot = spine_y_bot                    # -25.5 mm (flush with bottom of bracket spine)
    clamp_h = clamp_y_top - clamp_y_bot          # 13.3 mm
    clamp_yc = 0.5 * (clamp_y_top + clamp_y_bot) # -18.85 mm
    clamp_z_top = p.back_thickness + p.pcb_thickness + p.usb_bay_inner_depth + 1.4  # 18.8 mm

    usb_collar = rounded_rect_prism(
        width=clamp_outer_w,
        height=clamp_h,
        depth=clamp_z_top,
        radius=3.0,
        center_xy=(0.0, clamp_yc),
        z0=0.0,
    )

    # Reinforced M3 pinch-clamp jaws (30.0 mm wide across jaws, housing an M3 brass heat-set insert on the right jaw!)
    jaw_w = 30.0
    jaw_h = 8.4
    jaw_yc = clamp_yc - 0.8
    jaw_z0 = 7.2
    jaw_depth = 10.6  # z = 7.2 to 17.8 mm
    pinch_jaws = rounded_rect_prism(
        width=jaw_w,
        height=jaw_h,
        depth=jaw_depth,
        radius=2.4,
        center_xy=(0.0, jaw_yc),
        z0=jaw_z0,
    )
    body = body + usb_collar + pinch_jaws

    # 4. Cut out the PCB cradle cavity (96.0 x 21.0 mm, from z = p.back_thickness [6.8] to shell_front_z + 1)
    pcb_pocket = rounded_rect_prism(
        width=cav_w,
        height=cav_h,
        depth=p.shell_front_z - p.back_thickness + 1.0,
        radius=1.2,
        center_xy=(0.0, 0.0),
        z0=p.back_thickness,
    )
    body = body - pcb_pocket

    # 5. Cut out the rear SMD clearance pocket (z = 5.4 to 6.8 mm -> leaves a 5.4 mm solid backplate!)
    smd_floor_z = p.back_thickness - p.pcb_recess_depth  # 5.4 mm
    smd_pocket = rounded_rect_prism(
        width=p.pcb_width - 4.0,
        height=p.pcb_height - 3.4,
        depth=p.pcb_recess_depth + 0.5,
        radius=1.5,
        center_xy=(0.0, 0.0),
        z0=smd_floor_z,
    )
    body = body - smd_pocket

    # Add internal stiffening ribs & PCB seating bosses inside the SMD pocket:
    # - Central bridge rib (X = -14..+14 mm, Z = 5.4..6.8 mm) behind bare center of PCB
    center_pad = rounded_rect_prism(
        width=26.0,
        height=cav_h,
        depth=p.pcb_recess_depth,
        radius=1.5,
        center_xy=(0.0, 0.0),
        z0=smd_floor_z,
    )
    body = body + center_pad

    # - 4x Corner PCB Bosses at X = +-46.0, Y = +-8.5 mm (Ø6.4 mm pads up to z=6.8 mm)
    for bx in (-p.hole_outer_x, +p.hole_outer_x):
        for by in (-p.hole_y, +p.hole_y):
            body = body + cylinder_z(dia=6.4, depth=p.pcb_recess_depth, cx=bx, cy=by, z0=smd_floor_z)

    # - 8x Inner FFC-flanking PCB Support Bosses at X = +-26.1 and +-22.1 mm, Y = +-8.5 mm
    for bx in (-p.hole_inner_outer_x, +p.hole_inner_outer_x, -p.hole_inner_inner_x, +p.hole_inner_inner_x):
        for by in (-p.hole_y, +p.hole_y):
            body = body + cylinder_z(dia=5.2, depth=p.pcb_recess_depth, cx=bx, cy=by, z0=smd_floor_z)

    # - 4x Integrated Press-Fit PCB Locating Pins (Ø1.85 mm x 2.2 mm tall) at X = +-26.1, Y = +-8.5 mm
    #   Drops straight into four of the PCB's Ø2.0 mm holes so no tiny M2 nuts/bolts are required!
    for bx in (-p.hole_inner_outer_x, +p.hole_inner_outer_x):
        for by in (-p.hole_y, +p.hole_y):
            pin_base = mf.Manifold.cylinder(1.5, p.pcb_locator_pin_dia * 0.5, p.pcb_locator_pin_dia * 0.5, 36).translate(
                [bx, by, p.back_thickness - 0.1]
            )
            pin_tip = mf.Manifold.cylinder(0.8, p.pcb_locator_pin_dia * 0.5, 0.72, 36).translate(
                [bx, by, p.back_thickness + 1.4]
            )
            body = body + pin_base + pin_tip

    # 6. HEAT-SET THREADED INSERT BORES (ZERO HEX NUT RECESSES!)
    # 6a. 4x Outer Corner M3 Heat-Set Insert Bosses (X = +-51.5 mm, Y = +-8.5 mm, Ø4.0 mm bore x 6.5 mm deep)
    #     Reinforce the 4 outer corners with Ø9.2 mm cylindrical bosses blended into the outer end walls.
    for ex in (-p.outer_m3_ear_x, +p.outer_m3_ear_x):
        for ey in (-p.hole_y, +p.hole_y):
            body = body + cylinder_z(dia=9.2, depth=p.shell_front_z, cx=ex, cy=ey, z0=0.0)
            body = body - blind_insert_bore_from_top_z(
                bore_dia=p.m3_insert_bore_dia,
                depth=p.m3_insert_depth,
                z_top=p.shell_front_z,
                cx=ex,
                cy=ey,
            )

    # 6b. 4x PCB Corner M2 Heat-Set Insert Bores (X = +-46.0 mm, Y = +-8.5 mm, Ø3.2 mm bore x 4.5 mm deep)
    #     Blind from z = 6.8 mm down to z = 2.3 mm (leaves 2.3 mm solid sealed floor at z=0!).
    for bx in (-p.hole_outer_x, +p.hole_outer_x):
        for by in (-p.hole_y, +p.hole_y):
            body = body - blind_insert_bore_from_top_z(
                bore_dia=p.m2_insert_bore_dia,
                depth=p.m2_insert_depth,
                z_top=p.back_thickness,
                cx=bx,
                cy=by,
                chamfer_extra=0.6,
                chamfer_depth=0.5,
            )

    # 6c. 90° Metal Bracket Heat-Set Insert Bores on the Flat Rear Face (z = 0.0 mm):
    #   - 2x M3 Heat-Set Insert Bores (Ø4.0 mm x 6.5 mm deep) at X = +-10.00 mm, Y = -14.00 mm
    #     (Centered inside the metal bracket's 25.75 x 9.30 mm U-window for 100% M3 hardware setup!)
    #   - 2x M2 Heat-Set Insert Bores (Ø3.2 mm x 4.5 mm deep) at X = +-10.25 mm, Y = -6.65 mm
    #     (Aligned directly with the metal bracket's 2x Ø2.3 mm top crossbar holes!)
    #   - 2x Anti-Rotation Key Sockets (2.75 x 2.8 x 3.2 mm with 45-deg roof) at X = +-7.45 mm, Y = -7.70 mm
    #     (Aligned with the metal bracket's 2x 3.12 mm inner half-square notches!)
    for sign in (-1.0, +1.0):
        # M3 U-window insert bore (Ø4.0 mm x 6.5 mm deep + 45-deg conical roof)
        body = body - blind_insert_bore_from_bottom_z(
            bore_dia=p.m3_insert_bore_dia,
            depth=p.m3_insert_depth,
            cx=sign * 10.00,
            cy=-14.00,
            z0=0.0,
        )
        # M2 top crossbar insert bore (Ø3.2 mm x 4.5 mm deep + 45-deg conical roof)
        body = body - blind_insert_bore_from_bottom_z(
            bore_dia=p.m2_insert_bore_dia,
            depth=p.m2_insert_depth,
            cx=sign * 10.25,
            cy=-6.65,
            z0=0.0,
            chamfer_extra=0.6,
            chamfer_depth=0.5,
        )
        # Anti-rotation notch alignment socket (Ø2.8 mm x 3.2 mm deep at X = +-7.45 mm, Y = -7.70 mm)
        body = body - blind_insert_bore_from_bottom_z(
            bore_dia=2.8,
            depth=3.2,
            cx=sign * 7.45,
            cy=-7.70,
            z0=0.0,
            chamfer_extra=0.5,
            chamfer_depth=0.4,
        )

    # 7. Carve the Mini-USB plug tunnel & M3 Heat-Set Insert Pinch-Clamp Jaw Bores
    usb_neck = rounded_rect_prism(
        width=p.usb_port_width + 3.0,
        height=7.0,
        depth=8.8,
        radius=1.0,
        center_xy=(0.0, -cav_h * 0.5),
        z0=p.back_thickness - 0.4,
    )
    usb_bay_z0 = p.back_thickness + 0.6  # z = 7.4..16.4 mm (well in front of the z=0..6.8 mm spine!)
    usb_bay = rounded_rect_prism(
        width=p.usb_bay_inner_width,
        height=clamp_h + 4.0,
        depth=p.usb_bay_inner_depth,
        radius=1.6,
        center_xy=(0.0, clamp_yc),
        z0=usb_bay_z0,
    )
    shim_groove = rounded_rect_prism(
        width=p.usb_bay_inner_width + 1.4,
        height=clamp_h - 2.5,
        depth=3.0,
        radius=0.8,
        center_xy=(0.0, clamp_yc - 0.5),
        z0=usb_bay_z0 + 3.0,
    )
    flex_slit = rounded_rect_prism(
        width=1.8,
        height=clamp_h + 2.0,
        depth=5.5,
        radius=0.4,
        center_xy=(0.0, clamp_yc - 0.8),
        z0=usb_bay_z0 + p.usb_bay_inner_depth - 1.0,
    )
    body = body - usb_neck - usb_bay - shim_groove - flex_slit

    # Horizontal M3 Pinch-Clamp Screw + M3 Heat-Set Insert (at y = jaw_yc, z = 12.6 mm):
    # - Left jaw (X = -15.0..-0.9 mm): Ø3.4 mm M3 clearance hole + Ø6.4 mm socket head counterbore
    # - Right jaw (X = +0.9..+15.0 mm): Ø4.0 mm M3 heat-set insert bore (7.0 mm deep from slit face X=+0.9
    #   or outer face X=+15.0 -> pressing insert from outer right face X=+15.0 with Ø4.8 mm chamfer!)
    bolt_z = 12.6
    # Left jaw M3 clearance bore (from X = -16.0 to +2.0 mm)
    left_m3_clear = (
        cylinder_z(dia=p.m3_clearance_dia, depth=18.0, cx=0.0, cy=0.0, z0=-16.0)
        .rotate([0.0, 90.0, 0.0])
        .translate([0.0, jaw_yc, bolt_z])
    )
    left_m3_head = (
        cylinder_z(dia=6.4, depth=3.0, cx=0.0, cy=0.0, z0=-16.5)
        .rotate([0.0, 90.0, 0.0])
        .translate([0.0, jaw_yc, bolt_z])
    )
    # Right jaw M3 heat-set insert bore (Ø4.0 mm from X = +0.9 to +15.5 mm, with Ø4.8 mm chamfer on outer right face!)
    right_m3_insert = (
        cylinder_z(dia=p.m3_insert_bore_dia, depth=15.0, cx=0.0, cy=0.0, z0=0.8)
        .rotate([0.0, 90.0, 0.0])
        .translate([0.0, jaw_yc, bolt_z])
    )
    right_m3_chamfer = (
        mf.Manifold.cylinder(0.8, p.m3_insert_bore_dia * 0.5, (p.m3_insert_bore_dia + 0.8) * 0.5, 48)
        .rotate([0.0, 90.0, 0.0])
        .translate([jaw_w * 0.5 - 0.7, jaw_yc, bolt_z])
    )
    body = body - left_m3_clear - left_m3_head - right_m3_insert - right_m3_chamfer

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
    back_solid = build_back_mount(params)
    specs = [
        ("horace_cam_back_mount_v2.stl", back_solid),
        ("horace_cam_back_mount.stl", back_solid),
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
