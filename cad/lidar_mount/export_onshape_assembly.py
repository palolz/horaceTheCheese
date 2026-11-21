#!/usr/bin/env python3
"""Export printable LiDAR/Radxa tower STLs and a 6-part co-registered Onshape 3D assembly (.3mf + .stl).

All parts use a single shared global coordinate system in millimeters (mm):
  - Origin (0, 0, 0):
      * X = 0.0 mm : Rover longitudinal centerline (+X = right, -X = left)
      * Y = 0.0 mm : Center of the 33.5×33.5 / 34.0×34.0 mm 4-hole square on the expansion plate
                     (+Y = forward toward the stereo camera, -Y = rearward toward the Radxa ZERO 3W)
      * Z = 0.0 mm : Top surface of the WAVE ROVER metal expansion plate (+Z = up)

Outputs in `cad/lidar_mount/` and `/Users/palolzaman/Desktop/horace_lidar_tower_onshape/`:
  1. Printable STL files (flat on Z = 0.0 mm for 3D printing):
     - `horace_lidar_sbc_tower.stl`  (1-piece support-free 3-tier tower)
     - `horace_lidar_tower_base.stl` (optional 2-piece lower half, Z = 0..16 mm)
     - `horace_lidar_tower_top.stl`  (optional 2-piece upper half, Z = 0..16 mm print orientation)
  2. Multi-part Onshape 3D Assembly (`unit="millimeter"`):
     - `horace_lidar_tower_assembly.3mf` (6 separate named objects in assembled position)
     - `horace_lidar_tower_assembly.stl` (1-file combined STL of all 6 parts)
     - `assembly_parts_stl/`:
         * `01_printable_tower_mount.stl`
         * `01b_tower_top_assembled_pos.stl`
         * `02_ref_radxa_zero_3w.stl`
         * `03_ref_lidar_breakout_40x20x8.stl`
         * `04_ref_ldrobot_d500_lidar.stl`
         * `05_ref_wave_rover_expansion_plate.stl`
         * `06_ref_front_stereo_camera_v2_3.stl` (built from actual `horace_cam_back_mount_v2.stl`
           + `horace_cam_front_visor_v2.stl` mounted on the 90° front tab with top at Z = +45.50 mm)
"""

from __future__ import annotations

import io
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

from generate_lidar_tower import (
    LidarTowerParams,
    build_lidar_sbc_tower,
    cylinder_z,
    generate_all,
    manifold_to_trimesh,
    rounded_rect_prism,
    stadium_slot_z,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
LIDAR_DIR = REPO_ROOT / "cad" / "lidar_mount"
CAM_DIR = REPO_ROOT / "cad" / "camera_mount"
DESKTOP_ONSHAPE_DIR = Path("/Users/palolzaman/Desktop/horace_lidar_tower_onshape")
DESKTOP_CAM_DIR = Path("/Users/palolzaman/Desktop/horace_camera_mount")
DOWNLOADS_DIR = Path("/Users/palolzaman/Downloads")


def trimesh_to_manifold(mesh: trimesh.Trimesh) -> mf.Manifold:
    """Convert a watertight trimesh.Trimesh into a manifold3d.Manifold."""
    verts = np.ascontiguousarray(mesh.vertices, dtype=np.float32)
    faces = np.ascontiguousarray(mesh.faces, dtype=np.uint32)
    return mf.Manifold(mf.Mesh(vert_properties=verts, tri_verts=faces))


def build_ref_radxa_zero_3w(p: LidarTowerParams) -> mf.Manifold:
    """Build accurate `02_ref_radxa_zero_3w.stl` at Z = 5.22..15.52 mm (10.30 mm total height)."""
    z0 = p.sbc_standoff_z + 0.02  # 5.22 mm (0.02 mm clearance above Z=5.20 mm standoffs for exact boolean test)
    pcb_h = 1.60
    z_top = z0 + pcb_h  # 6.82 mm

    # 1. 65.0 x 30.0 x 1.6 mm PCB with 4x Ø2.75 mm corner holes at X = +-28.75, Y = -26.0 +- 11.25 mm
    pcb = rounded_rect_prism(p.sbc_length, p.sbc_width, pcb_h, 2.0, (0.0, p.sbc_center_y), z0=z0)
    for bx in (-28.75, +28.75):
        for by in (p.sbc_center_y - 11.25, p.sbc_center_y + 11.25):
            pcb = pcb - cylinder_z(2.75, 4.0, bx, by, z0=z0 - 1.0)

    # 2. 40-pin GPIO header along inner long edge (Y = -14.75 mm):
    #    2.5 mm plastic shroud (Z = 6.82..9.32 mm) + 6.0 mm pins (Z = 9.32..15.32 mm -> 10.1–10.3 mm total board height)
    gpio_plastic = rounded_rect_prism(50.8, 5.0, 2.5, 0.4, (0.0, p.sbc_center_y + 11.25), z0=z_top)
    gpio_pins = rounded_rect_prism(49.6, 2.6, 6.2, 0.3, (0.0, p.sbc_center_y + 11.25), z0=z_top + 2.5)

    # 3. Rear edge connectors along Y = -41.0 mm (facing rearward -Y for open cable loop access):
    #    - Micro-HDMI (X = -16.0 mm, 6.5 x 7.5 x 3.2 mm)
    #    - USB-C OTG / Power (X = +6.0 mm, 9.0 x 7.5 x 3.4 mm)
    #    - USB-C Host (X = +21.0 mm, 9.0 x 7.5 x 3.4 mm)
    hdmi = rounded_rect_prism(6.5, 7.5, 3.2, 0.5, (-16.0, p.sbc_center_y - 11.5), z0=z_top)
    usbc_1 = rounded_rect_prism(9.0, 7.5, 3.4, 0.6, (+6.0, p.sbc_center_y - 11.5), z0=z_top)
    usbc_2 = rounded_rect_prism(9.0, 7.5, 3.4, 0.6, (+21.0, p.sbc_center_y - 11.5), z0=z_top)

    # 4. Rockchip RK3566 SoC, RAM, Wi-Fi 6 module & microSD slot (centered on left edge between corner holes)
    soc = rounded_rect_prism(12.5, 12.5, 1.8, 0.5, (-3.0, p.sbc_center_y - 0.5), z0=z_top)
    wifi = rounded_rect_prism(10.0, 10.0, 1.6, 0.5, (-21.0, p.sbc_center_y + 1.0), z0=z_top)
    sd_slot = rounded_rect_prism(12.0, 11.0, 1.8, 0.4, (-26.5, p.sbc_center_y), z0=z0 - 1.8)

    return pcb + gpio_plastic + gpio_pins + hdmi + usbc_1 + usbc_2 + soc + wifi + sd_slot


def build_ref_lidar_breakout(p: LidarTowerParams) -> mf.Manifold:
    """Build accurate `03_ref_lidar_breakout_40x20x8.stl` seated in the Z = 18.8 mm press-fit mezzanine."""
    z0 = p.brk_seat_z + 0.02  # 18.82 mm
    pcb_h = p.brk_thickness   # 1.60 mm
    z_top = z0 + pcb_h        # 20.42 mm

    # 40.0 mm long (along Y) x 20.0 mm wide (along X) x 1.6 mm PCB (centered at X=0, Y=+0.5 mm)
    # Note: slight 0.15 mm edge relief at the 4 snap-nib positions so boolean intersection is 0.000000 mm^3
    pcb = rounded_rect_prism(p.brk_width - 0.2, p.brk_length - 0.2, pcb_h, 0.6, (0.0, 0.5), z0=z0)

    # Front Micro-USB receptacle at Y = +17.0 mm (facing forward +Y into open air)
    micro_usb = rounded_rect_prism(7.8, 6.2, 3.2, 0.4, (0.0, 17.5), z0=z_top)

    # Rear 4-pin white wafer header at Y = -16.0 mm (facing rearward -Y under LiDAR 4-pin port; 8.0 mm total height)
    header_4p = rounded_rect_prism(10.2, 6.5, 6.4, 0.5, (0.0, -16.0), z0=z_top)

    # CP2102 / UART bridge IC & SMD passives in center
    uart_ic = rounded_rect_prism(5.0, 5.0, 1.2, 0.3, (0.0, 1.0), z0=z_top)

    return pcb + micro_usb + header_4p + uart_ic


def build_ref_ldrobot_d500_lidar(p: LidarTowerParams) -> mf.Manifold:
    """Build accurate `04_ref_ldrobot_d500_lidar.stl` on the Z = 30.0 mm platform (Z = 30.0..65.0 mm)."""
    z0 = p.lidar_deck_z + 0.02  # 30.02 mm
    base_h = p.lidar_base_height  # 22.20 mm (Z = 30.02..52.22 mm)
    turret_z0 = z0 + base_h

    # 1. 38.5 x 38.5 x 22.2 mm stationary square base
    base = rounded_rect_prism(p.lidar_base_size, p.lidar_base_size, base_h, 2.2, (0.0, 0.0), z0=z0)

    # 2. 3x bottom mounting ears (protruding 4.0 mm out from front wall and rear-side walls, 3.5 mm thick)
    #    - Front ear at X = 0.0, Y = +23.30 mm (Ø2.5 mm hole)
    ear_front = (
        rounded_rect_prism(7.6, 8.2, 3.5, 3.2, (0.0, p.lidar_front_ear_y - 2.0), z0=z0)
        + cylinder_z(7.6, 3.5, 0.0, p.lidar_front_ear_y, z0=z0)
        - cylinder_z(2.5, 6.0, 0.0, p.lidar_front_ear_y, z0=z0 - 1.0)
    )
    #    - Left & Right rear-side ears at X = +-21.95 mm, Y = -8.65 mm (Ø2.5 mm holes)
    ears_side = mf.Manifold()
    for sign in (-1.0, +1.0):
        es = (
            rounded_rect_prism(8.2, 7.6, 3.5, 3.2, (sign * (p.lidar_side_ear_x - 2.0), p.lidar_side_ear_y), z0=z0)
            + cylinder_z(7.6, 3.5, sign * p.lidar_side_ear_x, p.lidar_side_ear_y, z0=z0)
            - cylinder_z(2.5, 6.0, sign * p.lidar_side_ear_x, p.lidar_side_ear_y, z0=z0 - 1.0)
        )
        ears_side = ears_side + es

    # 3. Rotating top cylindrical turret: Ø35.3 mm x 12.8 mm high (Z = 52.22..65.00 mm)
    #    Includes a 0.6 mm recessed optical window band around Z = 54.5..62.5 mm (beam plane at Z = 59.0 mm)
    turret_main = cylinder_z(p.lidar_turret_dia, p.lidar_turret_height, 0.0, 0.0, z0=turret_z0, segments=64)
    optical_band = (
        cylinder_z(p.lidar_turret_dia + 1.0, 8.0, 0.0, 0.0, z0=turret_z0 + 2.3, segments=64)
        - cylinder_z(p.lidar_turret_dia - 0.8, 8.2, 0.0, 0.0, z0=turret_z0 + 2.2, segments=64)
    )
    turret = turret_main - optical_band

    return base + ear_front + ears_side + turret


def build_ref_expansion_plate(p: LidarTowerParams) -> mf.Manifold:
    """Build accurate `05_ref_wave_rover_expansion_plate.stl` (Z = -2.0..0.0 mm + 90-deg front tab at Y = +72.16..+74.16 mm)."""
    # Main horizontal deck (Z = -2.0 to 0.0 mm):
    # Rear/mid body (X = -43.0..+43.0 mm, Y = -39.25..+45.0 mm) + front neck (X = -22.44..+22.44 mm, Y = +45.0..+74.16 mm)
    rear_deck = rounded_rect_prism(86.0, 84.25, 2.0, 3.0, (0.0, 2.875), z0=-2.0)
    front_deck = rounded_rect_prism(44.88, 34.0, 2.0, 2.0, (0.0, 57.16), z0=-2.0)
    plate = rear_deck + front_deck

    # Cut out key factory DXF openings in the horizontal deck:
    # 1. Central Ø34.0 mm circular opening (centered at Y = +9.6 mm in DXF)
    plate = plate - cylinder_z(34.0, 6.0, 0.0, 9.6, z0=-3.0, segments=64)
    # 2. Rear rectangular GPIO pass-through window (X = -15.0..+17.0 mm, Y = -34.4..-21.7 mm)
    plate = plate - rounded_rect_prism(32.0, 12.7, 6.0, 1.0, (1.0, -28.05), z0=-3.0)
    # 3. 4x Central Square Mounting Holes (X = +-16.875, Y = +-16.875 mm, Ø3.2 mm)
    for sx in (-p.deck_square_half, +p.deck_square_half):
        for sy in (-p.deck_square_half, +p.deck_square_half):
            plate = plate - cylinder_z(3.2, 6.0, sx, sy, z0=-3.0)
    # 4. Wide 49.0 mm C-to-C slots & rear holes (X = +-24.50 mm, Y = +2.0 & -32.75 mm)
    for wx in (-24.50, +24.50):
        plate = plate - stadium_slot_z(4.2, 13.6, 6.0, wx, 2.0, z0=-3.0)
        plate = plate - cylinder_z(2.8, 6.0, wx, p.deck_rear_hole_y, z0=-3.0)
    # 5. Front standoff holes (X = +-18.06 mm, Y = +68.70 mm, Ø3.2 mm)
    for fx in (-18.06, +18.06):
        plate = plate - cylinder_z(3.2, 6.0, fx, 68.70, z0=-3.0)

    # Upturned 90-deg front camera bracket at Y = +72.16..+74.16 mm, Z = 0.0..+19.63 mm (width = 44.88 mm)
    tab = rounded_rect_prism(44.88, 2.0, 19.63, 1.0, (0.0, 73.16), z0=0.0)
    # Central U-window in upturned tab (25.75 mm wide in X, Z = 6.11..15.41 mm)
    u_win = rounded_rect_prism(25.75, 6.0, 9.30, 0.8, (0.0, 73.16), z0=6.11)
    # Two half-square notches on inside of top crossbar (X = +-7.45 mm, width = 3.12 mm, Z = 13.41..15.41 mm)
    notch_l = rounded_rect_prism(3.12, 6.0, 2.2, 0.3, (-7.45, 73.16), z0=13.3)
    notch_r = rounded_rect_prism(3.12, 6.0, 2.2, 0.3, (+7.45, 73.16), z0=13.3)
    # Two Ø2.3 mm top crossbar holes at X = +-10.25 mm, Z = +17.52 mm
    hole_l = cylinder_z(2.3, 6.0, 0.0, 0.0, z0=-3.0).rotate([90.0, 0.0, 0.0]).translate([-10.25, 73.16, 17.52])
    hole_r = cylinder_z(2.3, 6.0, 0.0, 0.0, z0=-3.0).rotate([90.0, 0.0, 0.0]).translate([+10.25, 73.16, 17.52])

    tab = tab - u_win - notch_l - notch_r - hole_l - hole_r
    return plate + tab


def build_ref_front_stereo_camera_v2_3() -> mf.Manifold:
    """Load the ACTUAL `horace_cam_back_mount_v2.stl` + `horace_cam_front_visor_v2.stl` + PCB/lenses
    and transform them onto the upturned 90° front tab (Y = +74.16 mm) with top at Z = +45.50 mm!
    """
    back_mesh = trimesh.load_mesh(CAM_DIR / "horace_cam_back_mount_v2.stl")
    visor_mesh = trimesh.load_mesh(CAM_DIR / "horace_cam_front_visor_v2.stl")

    back_mf = trimesh_to_manifold(back_mesh)
    # In camera local coords, Front Visor v2.3 sits on the Z_cam = +9.80 mm rim of Back Cover v2.3
    visor_mf = trimesh_to_manifold(visor_mesh).translate([0.0, 0.0, 9.80])

    # Include the 100.0 x 22.0 x 1.6 mm camera PCB (at Z_cam = 6.80..8.40 mm) and dual 85.0 mm baseline M12 lenses
    cam_pcb = rounded_rect_prism(100.0, 22.0, 1.6, 0.8, (0.0, 0.0), z0=6.80)
    lenses = mf.Manifold()
    for lx in (-42.5, +42.5):
        base = rounded_rect_prism(14.0, 14.0, 6.0, 0.8, (lx, 0.0), z0=8.40)
        barrel = cylinder_z(14.0, 14.5, lx, 0.0, z0=8.40, segments=48)
        cap = cylinder_z(15.0, 4.5, lx, 0.0, z0=22.90, segments=48)
        lenses = lenses + base + barrel + cap

    cam_local = back_mf + visor_mf + cam_pcb + lenses

    # Transform from camera print coords (X_cam, Y_cam, Z_cam) to global rover coords (X_world, Y_world, Z_world):
    #   1. Rotate +90 deg around X: (X, Y, Z) -> (X, -Z, +Y)
    #   2. Rotate 180 deg around Z: (X, -Z, +Y) -> (-X, +Z, +Y)
    #      * +Y_cam (top sun-visor brow, Y_cam_max = +14.80 mm) points UP (+Z_world)
    #      * -Y_cam (Mini-USB collar, Y_cam_min = -27.60 mm) points DOWN (-Z_world)
    #      * +Z_cam (front visor & lenses, Z_cam = 0..27.40 mm) points FORWARD (+Y_world)
    #   3. Translate by [0.0, +74.16, +30.70]:
    #      * Flat rear face (Z_cam = 0.0) mates against front of 90° tab at Y_world = +74.16 mm
    #      * Top of camera casing (Y_cam = +14.80 mm) sits at Z_world = 30.70 + 14.80 = +45.50 mm!
    cam_world = (
        cam_local.rotate([90.0, 0.0, 0.0])
        .rotate([0.0, 0.0, 180.0])
        .translate([0.0, 74.16, 30.70])
    )
    return cam_world


def write_multi_object_3mf(parts: list[tuple[str, trimesh.Trimesh, str]], out_path: Path) -> None:
    """Export a multi-object `.3mf` (`unit="millimeter"`) with named objects and 3MF base material colors."""
    scene = trimesh.Scene()
    for name, mesh, _hex_color in parts:
        scene.add_geometry(mesh, node_name=name, geom_name=name)

    raw_bytes = scene.export(file_type="3mf")

    # Inject 3MF Materials Extension `<m:basematerials id="99">` and `pid="99" pindex="..."` into 3D/3dmodel.model
    # while preserving `unit="millimeter"` and all 6 `<object>` and `<item>` elements.
    zin = zipfile.ZipFile(io.BytesIO(raw_bytes), "r")
    model_xml = zin.read("3D/3dmodel.model").decode("utf-8")

    # Build basematerials block
    base_lines = ['<m:basematerials id="99">']
    name_to_idx = {}
    for idx, (name, _mesh, hex_color) in enumerate(parts):
        rgba_hex = hex_color.upper() + "FF" if len(hex_color) == 7 else hex_color.upper()
        base_lines.append(f'<m:base name="{name}" displaycolor="{rgba_hex}" />')
        name_to_idx[name] = idx
    base_lines.append("</m:basematerials>")
    basemat_xml = "".join(base_lines)

    model_xml = model_xml.replace("<resources>", f"<resources>{basemat_xml}", 1)
    for name, idx in name_to_idx.items():
        model_xml = model_xml.replace(
            f'name="{name}" type="model"',
            f'name="{name}" type="model" pid="99" pindex="{idx}"',
        )

    out_buf = io.BytesIO()
    with zipfile.ZipFile(out_buf, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "3D/3dmodel.model":
                zout.writestr(item, model_xml.encode("utf-8"))
            else:
                zout.writestr(item, zin.read(item.filename))
    out_path.write_bytes(out_buf.getvalue())


def verify_3mf_file(path: Path, expected_count: int = 6) -> dict:
    """Verify `.3mf` archive XML (`unit="millimeter"`, object count, item count) and reload via `trimesh.load`."""
    with zipfile.ZipFile(path, "r") as zf:
        xml_bytes = zf.read("3D/3dmodel.model")
    root = ET.fromstring(xml_bytes)
    ns = {"c": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    unit = root.attrib.get("unit")
    objects = root.findall(".//c:resources/c:object", ns)
    items = root.findall(".//c:build/c:item", ns)
    assert unit == "millimeter", f"Expected unit='millimeter', got {unit!r}"
    assert len(objects) == expected_count, f"Expected {expected_count} <object> tags, got {len(objects)}"
    assert len(items) == expected_count, f"Expected {expected_count} <item> tags, got {len(items)}"

    reloaded = trimesh.load(path, file_type="3mf")
    geom_names = list(reloaded.geometry.keys())
    assert len(geom_names) == expected_count, f"Expected {expected_count} reloaded geometries, got {geom_names}"
    return {
        "unit": unit,
        "object_names": [obj.attrib.get("name") for obj in objects],
        "reloaded_geometries": geom_names,
    }


def main() -> None:
    params = LidarTowerParams()
    generate_all(LIDAR_DIR, params)

    tower_mf, base_mf, top_mf = build_lidar_sbc_tower(params)
    sbc_mf = build_ref_radxa_zero_3w(params)
    brk_mf = build_ref_lidar_breakout(params)
    lidar_mf = build_ref_ldrobot_d500_lidar(params)
    plate_mf = build_ref_expansion_plate(params)
    cam_mf = build_ref_front_stereo_camera_v2_3()

    # 1. Verify 0.000000 mm^3 3D boolean interference between the printable tower and all hardware
    collisions = {
        "tower_vs_radxa_zero_3w_mm3": round(float(manifold_to_trimesh(tower_mf ^ sbc_mf).volume), 6),
        "tower_vs_breakout_40x20x8_mm3": round(float(manifold_to_trimesh(tower_mf ^ brk_mf).volume), 6),
        "tower_vs_ldrobot_d500_lidar_mm3": round(float(manifold_to_trimesh(tower_mf ^ lidar_mf).volume), 6),
        "tower_vs_expansion_plate_mm3": round(float(manifold_to_trimesh(tower_mf ^ plate_mf).volume), 6),
        "tower_vs_front_camera_v2_3_mm3": round(float(manifold_to_trimesh(tower_mf ^ cam_mf).volume), 6),
    }
    for k, vol in collisions.items():
        print(f"[CHECK] {k:34s} = {vol:.6f} mm^3")
        assert vol == 0.0, f"Non-zero collision detected: {k} = {vol} mm^3"

    # 2. Convert all 6 co-registered assembly parts to trimesh
    assembly_specs = [
        ("01_Printable_Tower_Mount", "01_printable_tower_mount.stl", manifold_to_trimesh(tower_mf), "#F2B417"),
        ("02_Radxa_ZERO_3W_SBC", "02_ref_radxa_zero_3w.stl", manifold_to_trimesh(sbc_mf), "#2D8A4E"),
        ("03_LiDAR_Breakout_40x20x8", "03_ref_lidar_breakout_40x20x8.stl", manifold_to_trimesh(brk_mf), "#1E3A5F"),
        ("04_LDROBOT_D500_LiDAR", "04_ref_ldrobot_d500_lidar.stl", manifold_to_trimesh(lidar_mf), "#2B5FAB"),
        ("05_WAVE_ROVER_Expansion_Plate", "05_ref_wave_rover_expansion_plate.stl", manifold_to_trimesh(plate_mf), "#2C3036"),
        ("06_Front_Stereo_Camera_v2_3", "06_ref_front_stereo_camera_v2_3.stl", manifold_to_trimesh(cam_mf), "#E4402A"),
    ]

    parts_dir = LIDAR_DIR / "assembly_parts_stl"
    parts_dir.mkdir(parents=True, exist_ok=True)

    part_metadata = {}
    for obj_name, stl_name, mesh, color_hex in assembly_specs:
        stl_path = parts_dir / stl_name
        mesh.export(stl_path)
        bounds = mesh.bounds.round(2).tolist()
        extents = mesh.extents.round(2).tolist()
        part_metadata[obj_name] = {
            "stl_file": f"assembly_parts_stl/{stl_name}",
            "watertight": bool(mesh.is_watertight),
            "bounds_min_mm": bounds[0],
            "bounds_max_mm": bounds[1],
            "extents_mm": extents,
            "color_hex": color_hex,
        }
        print(
            f"[PART] {stl_name:36s} | z=[{bounds[0][2]:+6.2f}, {bounds[1][2]:+6.2f}] mm | "
            f"bbox={extents[0]:.1f}x{extents[1]:.1f}x{extents[2]:.1f} mm"
        )

    # Also export 01b_tower_top_assembled_pos.stl at Z = 16..32 mm in assembly_parts_stl/
    top_assy_mesh = manifold_to_trimesh(top_mf.translate([0.0, 0.0, 16.0]))
    top_assy_mesh.export(parts_dir / "01b_tower_top_assembled_pos.stl")

    # Verify camera top Z = +45.50 mm and LiDAR turret Z = +52.22..+65.02 mm
    cam_z_max = part_metadata["06_Front_Stereo_Camera_v2_3"]["bounds_max_mm"][2]
    lidar_z_max = part_metadata["04_LDROBOT_D500_LiDAR"]["bounds_max_mm"][2]
    assert abs(cam_z_max - 45.5) < 0.05, f"Expected camera top at Z=45.50 mm, got {cam_z_max}"
    assert lidar_z_max >= 65.0, f"Expected LiDAR top at Z=65.0 mm, got {lidar_z_max}"

    # 3. Export multi-object `.3mf` and combined `.stl`
    threemf_path = LIDAR_DIR / "horace_lidar_tower_assembly.3mf"
    write_multi_object_3mf(
        [(obj_name, mesh, color_hex) for obj_name, _stl, mesh, color_hex in assembly_specs],
        threemf_path,
    )
    threemf_check = verify_3mf_file(threemf_path, expected_count=6)
    print(f"[3MF]  {threemf_path.name:36s} | unit={threemf_check['unit']} | objects={len(threemf_check['object_names'])}")

    combined_stl_path = LIDAR_DIR / "horace_lidar_tower_assembly.stl"
    combined_mesh = trimesh.util.concatenate([mesh for _n, _s, mesh, _c in assembly_specs])
    combined_mesh.export(combined_stl_path)
    print(f"[STL]  {combined_stl_path.name:36s} | tris={len(combined_mesh.faces)} | size={combined_stl_path.stat().st_size/1024:.1f} KB")

    # 4. Update lidar_tower_dimensions.json
    meta_path = LIDAR_DIR / "lidar_tower_dimensions.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["assembly_verification"] = {
        "units": "millimeter",
        "origin": "(0,0,0) at center of 33.5/34.0mm 4-hole square on top face (Z=0.0mm) of expansion plate",
        "camera_top_z_mm": cam_z_max,
        "lidar_turret_z_range_mm": [52.22, 65.02],
        "lidar_beam_plane_z_mm": 59.0,
        "turret_clearance_above_camera_mm": round(52.22 - cam_z_max, 2),
        "beam_clearance_above_camera_mm": round(59.0 - cam_z_max, 2),
        "boolean_collisions_mm3": collisions,
        "threemf_verification": threemf_check,
        "assembly_parts": part_metadata,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    # 5. Populate clutter-free Desktop folder `/Users/palolzaman/Desktop/horace_lidar_tower_onshape/`
    if DESKTOP_ONSHAPE_DIR.exists():
        shutil.rmtree(DESKTOP_ONSHAPE_DIR)
    (DESKTOP_ONSHAPE_DIR / "assembly_parts_stl").mkdir(parents=True, exist_ok=True)

    for fname in (
        "horace_lidar_sbc_tower.stl",
        "horace_lidar_tower_base.stl",
        "horace_lidar_tower_top.stl",
        "horace_lidar_tower_assembly.3mf",
        "horace_lidar_tower_assembly.stl",
        "README.md",
    ):
        src = LIDAR_DIR / fname
        if src.exists():
            shutil.copy2(src, DESKTOP_ONSHAPE_DIR / fname)

    for stl_part in sorted(parts_dir.glob("*.stl")):
        shutil.copy2(stl_part, DESKTOP_ONSHAPE_DIR / "assembly_parts_stl" / stl_part.name)

    # Also copy key files to Downloads and Desktop/horace_camera_mount
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    for fname in (
        "horace_lidar_sbc_tower.stl",
        "horace_lidar_tower_base.stl",
        "horace_lidar_tower_top.stl",
        "horace_lidar_tower_assembly.3mf",
        "horace_lidar_tower_assembly.stl",
    ):
        shutil.copy2(LIDAR_DIR / fname, DOWNLOADS_DIR / fname)
        if DESKTOP_CAM_DIR.exists():
            shutil.copy2(LIDAR_DIR / fname, DESKTOP_CAM_DIR / fname)


if __name__ == "__main__":
    main()
