#!/usr/bin/env python3
"""Render 4-view orthographic engineering drawings and 4-panel 3D preview sheet for `cad/lidar_mount/`."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import trimesh

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon, FancyArrowPatch


REPO_ROOT = Path(__file__).resolve().parents[2]
LIDAR_CAD_DIR = REPO_ROOT / "cad" / "lidar_mount"
CAM_CAD_DIR = REPO_ROOT / "cad" / "camera_mount"


def shade_mesh_faces(
    mesh: trimesh.Trimesh,
    base_rgb: tuple[float, float, float],
    light_dir: tuple[float, float, float] = (0.45, -0.55, 0.70),
    alpha: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    tris = mesh.vertices[mesh.faces]
    normals = mesh.face_normals
    ldir = np.array(light_dir, dtype=np.float64)
    ldir /= np.linalg.norm(ldir)
    dots = np.clip(normals @ ldir, -1.0, 1.0)
    intensity = 0.58 + 0.38 * np.maximum(0.0, dots) + 0.08 * np.maximum(0.0, -dots)
    base = np.array(base_rgb, dtype=np.float64)[None, :]
    rgb = np.clip(base * intensity[:, None], 0.0, 1.0)
    rgba = np.column_stack([rgb, np.full(len(tris), alpha)])
    return tris, rgba


def add_mesh_to_ax(
    ax,
    mesh: trimesh.Trimesh,
    color_hex: str,
    alpha: float = 1.0,
    edge_rgba: tuple[float, float, float, float] = (0.13, 0.11, 0.08, 0.14),
    linewidth: float = 0.18,
) -> None:
    h = color_hex.lstrip("#")
    base_rgb = tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    tris, rgba = shade_mesh_faces(mesh, base_rgb, alpha=alpha)
    coll = Poly3DCollection(tris, facecolors=rgba, edgecolors=edge_rgba, linewidths=linewidth)
    ax.add_collection3d(coll)


def style_3d_ax(ax, title: str, subtitle: str, xlim=(-55, 55), ylim=(-55, 85), zlim=(-5, 70), elev=24, azim=-52) -> None:
    ax.set_facecolor("#F6EFE2")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_zlim(*zlim)
    ax.set_box_aspect([xlim[1] - xlim[0], ylim[1] - ylim[0], zlim[1] - zlim[0]])
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.text2D(
        0.02,
        0.95,
        title,
        transform=ax.transAxes,
        fontsize=11.5,
        fontweight="bold",
        color="#211D15",
        family="sans-serif",
        bbox=dict(boxstyle="round,pad=0.32", facecolor="#F2B417", edgecolor="#211D15", linewidth=1.8),
    )
    ax.text2D(
        0.02,
        0.03,
        subtitle,
        transform=ax.transAxes,
        fontsize=8.6,
        color="#211D15",
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="#EFE5D2", edgecolor="#211D15", linewidth=1.3),
    )


def build_hardware_context_meshes():
    """Build illustrative 3D meshes for Expansion Plate, Front Camera (45.5mm top), Radxa ZERO 3W, Breakout PCB, and D500 LiDAR."""
    import sys
    sys.path.insert(0, str(LIDAR_CAD_DIR))
    import manifold3d as mf
    from generate_lidar_tower import LidarTowerParams, cylinder_z, rounded_rect_prism, manifold_to_trimesh

    p = LidarTowerParams()

    # 1. WAVE ROVER Expansion Plate (Z = -2.0..0.0 mm, Y = -38.0..+73.0 mm, X = -44.0..+44.0 mm)
    #    plus upturned 90° front bracket at Y = +72.9..+74.9 mm, Z = 0.0..19.63 mm
    deck_main = rounded_rect_prism(88.0, 66.0, 2.0, 3.0, (0.0, -5.0), z0=-2.0)
    deck_front = rounded_rect_prism(48.0, 48.0, 2.0, 3.0, (0.0, 50.0), z0=-2.0)
    front_tab = rounded_rect_prism(44.88, 2.0, 19.63, 1.0, (0.0, 73.9), z0=0.0)
    # Rear rectangular GPIO cutout (Y = -34.0..-22.0, X = -15.0..+17.0)
    rear_cut = rounded_rect_prism(32.0, 12.0, 5.0, 1.0, (1.0, -28.0), z0=-3.0)
    plate_mesh = manifold_to_trimesh(deck_main + deck_front + front_tab - rear_cut)

    # 2. Front Stereo Camera Enclosure at Y = +64.0..+88.0 mm, reaching Z = +45.5 mm above deck!
    cam_box = rounded_rect_prism(122.2, 26.5, 29.6, 4.5, (0.0, 76.0), z0=15.9)
    cam_lenses = (
        cylinder_z(16.0, 4.0, -42.5, 0.0, z0=0.0).rotate([-90.0, 0.0, 0.0]).translate([0.0, 89.0, 30.7])
        + cylinder_z(16.0, 4.0, +42.5, 0.0, z0=0.0).rotate([-90.0, 0.0, 0.0]).translate([0.0, 89.0, 30.7])
    )
    cam_mesh = manifold_to_trimesh(cam_box + cam_lenses)

    # 3. Radxa ZERO 3W (65.0 x 30.0 x 1.6 mm green PCB at Z = 5.2..6.8 mm, Y = -26.0 mm)
    #    + 6.0 mm tall 40-pin GPIO header + 2x USB-C & Micro-HDMI ports (total 10.3 mm height)
    sbc_pcb = rounded_rect_prism(p.sbc_length, p.sbc_width, 1.6, 1.5, (0.0, p.sbc_center_y), z0=p.sbc_standoff_z)
    for bx in (-28.75, +28.75):
        for by in (p.sbc_center_y - 11.25, p.sbc_center_y + 11.25):
            sbc_pcb = sbc_pcb - cylinder_z(2.7, 5.0, bx, by, z0=p.sbc_standoff_z - 1.0)
    # 40-pin GPIO header along inner long edge (Y = -14.75 mm, Z = 6.8..15.5 mm)
    sbc_gpio = rounded_rect_prism(51.0, 5.0, 8.7, 0.4, (0.0, p.sbc_center_y + 11.25), z0=p.sbc_standoff_z + 1.6)
    # 2x USB-C + Micro-HDMI ports along rear edge (Y = -41.0 mm) + Rockchip RK3566 SoC
    sbc_ports = (
        rounded_rect_prism(9.0, 7.5, 3.4, 0.5, (-16.0, p.sbc_center_y - 11.5), z0=p.sbc_standoff_z + 1.6)
        + rounded_rect_prism(9.0, 7.5, 3.4, 0.5, (+6.0, p.sbc_center_y - 11.5), z0=p.sbc_standoff_z + 1.6)
        + rounded_rect_prism(9.0, 7.5, 3.4, 0.5, (+21.0, p.sbc_center_y - 11.5), z0=p.sbc_standoff_z + 1.6)
        + rounded_rect_prism(14.0, 14.0, 2.2, 0.5, (-2.0, p.sbc_center_y), z0=p.sbc_standoff_z + 1.6)
    )

    # 4. LiDAR Breakout Board (40.0 x 20.0 x 8.0 mm in mezzanine Z = 18.8..26.8 mm)
    brk_pcb = rounded_rect_prism(p.brk_width, p.brk_length, 1.6, 0.5, (0.0, 0.5), z0=p.brk_seat_z)
    brk_conn = (
        rounded_rect_prism(8.0, 6.5, 5.8, 0.5, (0.0, 17.0), z0=p.brk_seat_z + 1.6)  # Front Micro-USB
        + rounded_rect_prism(10.0, 6.5, 6.2, 0.5, (0.0, -16.0), z0=p.brk_seat_z + 1.6)  # Rear 4-pin header
    )

    # 5. LDROBOT D500 (STL-19P) LiDAR at Z = 30.0..65.0 mm
    lidar_base = rounded_rect_prism(p.lidar_base_size, p.lidar_base_size, p.lidar_base_height, 2.0, (0.0, 0.0), z0=p.lidar_deck_z)
    # 3 mounting ears on bottom of LiDAR base (Z = 30.0..33.5 mm)
    ear_f = cylinder_z(7.5, 3.5, 0.0, p.lidar_front_ear_y, z0=p.lidar_deck_z) - cylinder_z(2.5, 5.0, 0.0, p.lidar_front_ear_y, z0=p.lidar_deck_z - 0.5)
    ear_l = cylinder_z(7.5, 3.5, -21.95, p.lidar_side_ear_y, z0=p.lidar_deck_z) - cylinder_z(2.5, 5.0, -21.95, p.lidar_side_ear_y, z0=p.lidar_deck_z - 0.5)
    ear_r = cylinder_z(7.5, 3.5, +21.95, p.lidar_side_ear_y, z0=p.lidar_deck_z) - cylinder_z(2.5, 5.0, +21.95, p.lidar_side_ear_y, z0=p.lidar_deck_z - 0.5)
    lidar_body = lidar_base + ear_f + ear_l + ear_r
    lidar_turret = cylinder_z(p.lidar_turret_dia, p.lidar_turret_height, 0.0, 0.0, z0=p.lidar_deck_z + p.lidar_base_height, segments=64)

    return {
        "plate": (plate_mesh, "#2A2E34"),
        "camera": (cam_mesh, "#E4402A"),
        "sbc_pcb": (manifold_to_trimesh(sbc_pcb), "#2D8A4E"),
        "sbc_gpio": (manifold_to_trimesh(sbc_gpio), "#3A3F47"),
        "sbc_ports": (manifold_to_trimesh(sbc_ports), "#B8C2CC"),
        "brk_pcb": (manifold_to_trimesh(brk_pcb), "#1E3A5F"),
        "brk_conn": (manifold_to_trimesh(brk_conn), "#D8DEE6"),
        "lidar_body": (manifold_to_trimesh(lidar_body), "#22262C"),
        "lidar_turret": (manifold_to_trimesh(lidar_turret), "#2B5FAB"),
    }


def render_3d_preview_sheet() -> Path:
    tower_stl = trimesh.load_mesh(LIDAR_CAD_DIR / "horace_lidar_sbc_tower.stl")
    base_stl = trimesh.load_mesh(LIDAR_CAD_DIR / "horace_lidar_tower_base.stl")
    top_stl = trimesh.load_mesh(LIDAR_CAD_DIR / "horace_lidar_tower_top.stl")
    hw = build_hardware_context_meshes()

    fig = plt.figure(figsize=(16.5, 12.0), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · LiDAR (D500) + Breakout (40×20×8mm) + Radxa ZERO 3W Tower Mount (3D Printable CAD)",
        fontsize=15.5,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    # --- Panel 1: Full Assembled View on Expansion Plate with 45.5 mm Front Stereo Camera ---
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    add_mesh_to_ax(ax1, hw["plate"][0], hw["plate"][1], alpha=0.88)
    add_mesh_to_ax(ax1, hw["camera"][0], hw["camera"][1], alpha=0.85)
    add_mesh_to_ax(ax1, tower_stl, "#F2B417")
    for k in ("sbc_pcb", "sbc_gpio", "sbc_ports", "brk_pcb", "brk_conn", "lidar_body", "lidar_turret"):
        add_mesh_to_ax(ax1, hw[k][0], hw[k][1])
    style_3d_ax(
        ax1,
        "1 · Assembled on Expansion Plate (Clears 45.5mm Camera!)",
        "LiDAR turret at Z=52.2..65.0mm (+6.7mm above 45.5mm camera) · 33.5×33.5 & 49.0mm holes",
        xlim=(-65, 65),
        ylim=(-45, 92),
        zlim=(-4, 68),
        elev=22,
        azim=-54,
    )

    # --- Panel 2: Rear / Side 3/4 View Showing Radxa ZERO 3W, Press-Fit Breakout & Cable Loop Clips ---
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    add_mesh_to_ax(ax2, hw["plate"][0], hw["plate"][1], alpha=0.65)
    add_mesh_to_ax(ax2, tower_stl, "#F2B417")
    for k in ("sbc_pcb", "sbc_gpio", "sbc_ports", "brk_pcb", "brk_conn", "lidar_body", "lidar_turret"):
        add_mesh_to_ax(ax2, hw[k][0], hw[k][1])
    style_3d_ax(
        ax2,
        "2 · Rear/Side View: Radxa ZERO 3W + Breakout Mezzanine + Cable Clips",
        "Tier 1: Radxa ZERO 3W (65×30×10.3mm) · Tier 2: 40×20×8mm Press-Fit Breakout · Tier 3: D500 LiDAR",
        xlim=(-45, 45),
        ylim=(-46, 35),
        zlim=(-4, 66),
        elev=24,
        azim=-132,
    )

    # --- Panel 3: Exploded 3-Tier Stack View ---
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    add_mesh_to_ax(ax3, tower_stl, "#F2B417")

    for k in ("sbc_pcb", "sbc_gpio", "sbc_ports"):
        m = hw[k][0].copy()
        m.apply_translation([0.0, -28.0, 12.0])
        add_mesh_to_ax(ax3, m, hw[k][1])

    for k in ("brk_pcb", "brk_conn"):
        m = hw[k][0].copy()
        m.apply_translation([0.0, 36.0, 4.0])
        add_mesh_to_ax(ax3, m, hw[k][1])

    for k in ("lidar_body", "lidar_turret"):
        m = hw[k][0].copy()
        m.apply_translation([0.0, 0.0, 22.0])
        add_mesh_to_ax(ax3, m, hw[k][1])

    style_3d_ax(
        ax3,
        "3 · Exploded 3-Tier View (Tower + Radxa ZERO 3W + Breakout + LiDAR)",
        "Breakout slides into press-fit mezzanine · Radxa bolts to 57.5×22.5mm slots · LiDAR bolts to 3 ears",
        xlim=(-48, 48),
        ylim=(-68, 56),
        zlim=(0, 88),
        elev=23,
        azim=-50,
    )

    # --- Panel 4: Support-Free Print Bed Layout (1-Piece Tower + Optional 2-Piece Split) ---
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    gx = np.linspace(-80, 80, 17)
    gy = np.linspace(-45, 45, 10)
    for x in gx:
        ax4.plot([x, x], [gy[0], gy[-1]], [0, 0], color="#211D15", alpha=0.15, linewidth=0.7)
    for y in gy:
        ax4.plot([gx[0], gx[-1]], [y, y], [0, 0], color="#211D15", alpha=0.15, linewidth=0.7)

    t1 = tower_stl.copy()
    t1.apply_translation([-38.0, 8.0, 0.0])
    add_mesh_to_ax(ax4, t1, "#F2B417")

    b2 = base_stl.copy()
    b2.apply_translation([+38.0, -12.0, 0.0])
    add_mesh_to_ax(ax4, b2, "#2B5FAB")

    u2 = top_stl.copy()
    u2.apply_translation([+38.0, +24.0, 0.0])
    add_mesh_to_ax(ax4, u2, "#E4402A")

    style_3d_ax(
        ax4,
        "4 · Print Bed Layout: 1-Piece Tower (#F2B417) OR 2-Piece Split (#2B5FAB+#E4402A)",
        "Flat on Z=0.0 · 45° vaulted arches (Zero Supports) · 28.06 cm³ (~34g PLA/PETG)",
        xlim=(-80, 80),
        ylim=(-48, 48),
        zlim=(0, 38),
        elev=34,
        azim=-48,
    )

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    out_path = LIDAR_CAD_DIR / "lidar-tower-render.png"
    fig.savefig(out_path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved LiDAR Tower 3D preview sheet -> {out_path}")
    return out_path


def render_orthographic_drawings() -> tuple[Path, Path]:
    """Generate 4-panel true orthographic engineering drawing (`lidar-tower-orthographic.svg` & `.png`)."""
    fig, axes = plt.subplots(2, 2, figsize=(17.0, 12.6), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · LiDAR + Breakout (40×20×8mm) + Radxa ZERO 3W Tower — 4-View Orthographic Drawing (mm)",
        fontsize=15.5,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    def dim_arrow(ax, x1, y1, x2, y2, text, text_offset=(0, 2.2), color="#E4402A", fontsize=8.0):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="<->", color=color, lw=1.7, shrinkA=0, shrinkB=0),
        )
        mx, my = 0.5 * (x1 + x2) + text_offset[0], 0.5 * (y1 + y2) + text_offset[1]
        ax.text(
            mx,
            my,
            text,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color="#211D15",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#F6EFE2", edgecolor=color, lw=1.2),
        )

    # =========================================================================
    # VIEW 1 (axes[0, 0]): TOP ORTHOGRAPHIC PLAN VIEW (Mounting Holes & Looped USB Routing)
    # =========================================================================
    ax = axes[0, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-58, 58)
    ax.set_ylim(-58, 48)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title(
        "1 · TOP ORTHOGRAPHIC PLAN VIEW (Expansion Plate Holes & USB Cable Loops)",
        fontsize=11.0,
        fontweight="bold",
        color="#211D15",
        pad=8,
    )

    # Expansion plate reference outline (X = -44..+44, Y = -38..+45)
    ax.add_patch(Rectangle((-44.0, -38.0), 88.0, 82.0, facecolor="#D8CEB8", edgecolor="#211D15", lw=1.4, ls="--", alpha=0.45))
    # Rear expansion plate rectangular GPIO cutout (X = -15..+17, Y = -34..-22)
    ax.add_patch(Rectangle((-15.0, -34.0), 32.0, 12.0, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.2, ls=":"))

    # Tower Base Footprint (Yellow #F2B417)
    ax.add_patch(FancyBboxPatch((-33.5, -41.5), 67.0, 31.0, boxstyle="round,pad=0,rounding_size=4.2", facecolor="#F2B417", edgecolor="#211D15", lw=1.8, alpha=0.65))
    ax.add_patch(FancyBboxPatch((-28.5, -20.5), 57.0, 43.0, boxstyle="round,pad=0,rounding_size=4.5", facecolor="#F2B417", edgecolor="#211D15", lw=1.8, alpha=0.65))
    # Side cable clips at X = +-25.2, Y = -3.5..+9.5
    for sign in (-1.0, +1.0):
        ax.add_patch(FancyBboxPatch((sign * 25.2 - 3.4, -3.5), 6.8, 13.0, boxstyle="round,pad=0,rounding_size=1.8", facecolor="#F2B417", edgecolor="#211D15", lw=1.5))

    # Radxa ZERO 3W (65.0 x 30.0 mm green outline at Y = -41.0..-11.0)
    ax.add_patch(FancyBboxPatch((-32.5, -41.0), 65.0, 30.0, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#2D8A4E", edgecolor="#211D15", lw=1.8, alpha=0.78))
    # 40-pin GPIO header on Radxa ZERO 3W (Y = -14.75, X = -25.5..+25.5)
    ax.add_patch(Rectangle((-25.5, -16.8), 51.0, 4.2, facecolor="#211D15", edgecolor="#F6EFE2", lw=1.0))
    ax.text(0.0, -14.7, "40-Pin GPIO (6mm pins)", ha="center", va="center", fontsize=6.4, color="#F6EFE2", family="monospace", fontweight="bold")
    # 2x USB-C + Micro-HDMI ports on rear edge of Radxa (Y = -41.0 mm)
    for px, lbl in [(-16.0, "HDMI"), (+6.0, "USB-C1"), (+21.0, "USB-C2")]:
        ax.add_patch(Rectangle((px - 4.5, -42.5), 9.0, 5.5, facecolor="#D8DEE6", edgecolor="#211D15", lw=1.1))
        ax.text(px, -39.7, lbl, ha="center", va="center", fontsize=5.8, color="#211D15", family="monospace", fontweight="bold")

    # 4x Radxa ZERO 3W mounting holes (X = +-28.75, Y = -37.25 & -14.75 -> 57.5 x 22.5 mm slots)
    for bx in (-28.75, +28.75):
        for by in (-37.25, -14.75):
            ax.add_patch(Circle((bx, by), 2.1, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))

    # Middle Mezzanine: 40.0 x 20.0 mm Press-Fit Breakout Board (X = -10..+10, Y = -19.5..+20.5)
    ax.add_patch(Rectangle((-10.0, -19.5), 20.0, 40.0, facecolor="#1E3A5F", edgecolor="#F6EFE2", lw=1.5, ls="--", alpha=0.85))
    ax.text(0.0, 0.5, "Breakout\n40×20×8mm\n(Press-Fit\nin Tier 2)", ha="center", va="center", fontsize=6.6, color="#F6EFE2", family="monospace", fontweight="bold")

    # Top Deck: LDROBOT D500 LiDAR (38.5 x 38.5 mm square + Ø35.3 mm turret + 3 ears)
    ax.add_patch(FancyBboxPatch((-19.25, -19.25), 38.5, 38.5, boxstyle="round,pad=0,rounding_size=2.0", fill=False, edgecolor="#E4402A", lw=2.2))
    ax.add_patch(Circle((0.0, 0.0), 17.65, fill=False, edgecolor="#E4402A", lw=1.6, ls=":"))
    # 3x LiDAR Mounting Ears: Front (0, +23.30) and Rear-Sides (+-21.95, -8.65)
    ax.add_patch(Circle((0.0, 23.30), 2.2, facecolor="#E4402A", edgecolor="#211D15", lw=1.3))
    for sign in (-1.0, +1.0):
        ax.add_patch(FancyBboxPatch((sign * 21.95 - 2.7, -8.65 - 1.45), 5.4, 2.9, boxstyle="round,pad=0,rounding_size=1.4", facecolor="#E4402A", edgecolor="#211D15", lw=1.3))

    # 4x Central Expansion Plate Square Holes (33.5 x 33.5 / 34.0 x 34.0 mm at X = +-16.875, Y = +-16.875)
    for sx in (-16.875, +16.875):
        for sy in (-16.875, +16.875):
            ax.add_patch(Circle((sx, sy), 2.3, facecolor="#2B5FAB", edgecolor="#F6EFE2", lw=1.3))

    # 4x Wide 49.0 mm C-to-C Expansion Plate Holes (X = +-24.50, Y = +2.0 & -32.75)
    for wx in (-24.50, +24.50):
        for wy in (+2.0, -32.75):
            ax.add_patch(Circle((wx, wy), 2.1, facecolor="#2B5FAB", edgecolor="#F6EFE2", lw=1.2))

    # Draw Looped USB Cable Paths (Showing generous bend radius around the tower sides!)
    # 1. Breakout Micro-USB (front Y=+20.5) -> loops around Right Cable Clip (X=+25.4) -> Radxa USB-C2 (X=+21, Y=-42.5)
    usb_loop_r_x = [0.0, 12.0, 25.4, 25.4, 23.0, 21.0]
    usb_loop_r_y = [20.5, 27.5, 16.0, -20.0, -51.0, -43.0]
    ax.plot(usb_loop_r_x, usb_loop_r_y, color="#E4402A", lw=2.5, ls="-")
    ax.text(39.5, -14.0, "LiDAR USB\nLoop (R≥18mm)", ha="center", va="center", fontsize=6.8, fontweight="bold", family="monospace", color="#E4402A", bbox=dict(boxstyle="round,pad=0.2", facecolor="#F6EFE2", edgecolor="#E4402A"))

    # 2. Camera Mini-USB (from front Y=+46) -> along Left Cable Clip (X=-25.4) -> Radxa USB-C1 (X=+6, Y=-43.0)
    usb_loop_l_x = [-6.0, -25.4, -25.4, -10.0, +6.0]
    usb_loop_l_y = [45.0, 20.0, -22.0, -52.0, -43.0]
    ax.plot(usb_loop_l_x, usb_loop_l_y, color="#2B5FAB", lw=2.5, ls="-")
    ax.text(-39.5, -14.0, "Camera USB\nLoop to USB-C1", ha="center", va="center", fontsize=6.8, fontweight="bold", family="monospace", color="#2B5FAB", bbox=dict(boxstyle="round,pad=0.2", facecolor="#F6EFE2", edgecolor="#2B5FAB"))

    dim_arrow(ax, -16.875, 32.0, +16.875, 32.0, "33.5–34.0 mm Square (4× M3)", (0, 2.8), "#2B5FAB", fontsize=7.6)
    dim_arrow(ax, -21.95, 40.5, +21.95, 40.5, "42.7–45.0 mm LiDAR Side Ear Slots", (0, 2.8), "#E4402A", fontsize=7.6)
    dim_arrow(ax, -24.50, -47.5, +24.50, -47.5, "49.0 mm Deck Rear Holes", (0, -2.8), "#2B5FAB", fontsize=7.6)
    dim_arrow(ax, -28.75, -54.0, +28.75, -54.0, "57.0–58.0 × 22.0–23.0 mm Radxa ZERO 3W Slots", (0, -2.5), "#2D8A4E", fontsize=7.5)

    # =========================================================================
    # VIEW 2 (axes[0, 1]): RIGHT-SIDE ORTHOGRAPHIC ELEVATION (Line-of-Sight Over 45.5mm Camera)
    # =========================================================================
    ax = axes[0, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-52, 98)
    ax.set_ylim(-8, 76)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title(
        "2 · RIGHT-SIDE ORTHOGRAPHIC ELEVATION (Unobstructed Scan Over 45.5 mm Camera)",
        fontsize=11.0,
        fontweight="bold",
        color="#211D15",
        pad=8,
    )

    # Expansion plate (Z = -2.0..0.0, Y = -38..+74) + upturned 90-deg front tab (Y = +72..+74, Z = 0..19.63)
    ax.add_patch(Rectangle((-38.0, -2.0), 112.0, 2.0, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))
    ax.add_patch(Rectangle((72.0, 0.0), 2.0, 19.63, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))

    # Front Stereo Camera Casing (Y = +64..+90, top at Z = +45.5 mm!)
    ax.add_patch(FancyBboxPatch((64.0, 3.1), 24.0, 42.4, boxstyle="round,pad=0,rounding_size=2.5", facecolor="#E4402A", edgecolor="#211D15", lw=1.8, alpha=0.85))
    ax.plot([-48, 95], [45.5, 45.5], color="#E4402A", lw=1.5, ls="--")
    ax.text(76.0, 25.0, "Stereo\nCamera\nTop:\n45.5 mm", ha="center", va="center", fontsize=7.2, fontweight="bold", family="monospace", color="#F6EFE2")

    # 3-Tier Tower Profile (Y = -41.5..+26.0, Z = 0.0..30.0 mm)
    tower_side_poly = [
        (-41.5, 0.0),
        (22.5, 0.0),
        (22.5, 3.6),
        (20.2, 3.6),
        (20.2, 26.0),
        (27.5, 26.0),
        (27.5, 30.0),
        (-21.0, 30.0),
        (-21.0, 26.0),
        (-9.2, 16.0),
        (-9.2, 3.6),
        (-41.5, 3.6),
    ]
    ax.add_patch(Polygon(tower_side_poly, closed=True, facecolor="#F2B417", edgecolor="#211D15", lw=1.8, alpha=0.82))

    # Tier 1: Radxa ZERO 3W on Rear Standoffs (Y = -41.0..-11.0, Z = 5.2..15.5 mm; 10.3 mm total thickness)
    ax.add_patch(Rectangle((-39.5, 0.0), 6.0, 5.2, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
    ax.add_patch(Rectangle((-17.5, 0.0), 6.0, 5.2, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
    ax.add_patch(Rectangle((-41.0, 5.2), 30.0, 1.6, facecolor="#2D8A4E", edgecolor="#211D15", lw=1.5))
    ax.add_patch(Rectangle((-17.0, 6.8), 4.5, 6.0, facecolor="#211D15", edgecolor="#F6EFE2", lw=1.0))  # 6mm GPIO pins
    ax.add_patch(Rectangle((-41.0, 6.8), 7.5, 3.5, facecolor="#D8DEE6", edgecolor="#211D15", lw=1.0))  # USB-C port
    ax.text(-26.0, 11.2, "Radxa ZERO 3W\n(10.3mm w/ 6mm Pins)", ha="center", va="center", fontsize=6.6, fontweight="bold", family="monospace", color="#211D15", bbox=dict(boxstyle="round,pad=0.18", facecolor="#F6EFE2", edgecolor="#2D8A4E"))

    # Tier 2: 40x20x8mm Press-Fit Breakout Board in Mezzanine (Y = -19.5..+20.5, Z = 18.8..26.8 mm)
    ax.add_patch(Rectangle((-19.5, 18.8), 40.0, 1.6, facecolor="#1E3A5F", edgecolor="#F6EFE2", lw=1.3))
    ax.add_patch(Rectangle((-19.0, 20.4), 39.0, 6.4, facecolor="#3A6EA5", edgecolor="#211D15", lw=1.1, alpha=0.8))
    ax.text(0.5, 23.5, "40×20×8mm Breakout", ha="center", va="center", fontsize=6.5, fontweight="bold", family="monospace", color="#F6EFE2")

    # Tier 3: LDROBOT D500 LiDAR at Z = 30.0..65.0 mm
    # - Stationary square base: Y = -19.25..+19.25, Z = 30.0..52.2 mm
    ax.add_patch(Rectangle((-19.25, 30.0), 38.5, 22.2, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))
    ax.text(0.0, 41.0, "LiDAR Base\n38.5×22.2mm", ha="center", va="center", fontsize=7.0, fontweight="bold", family="monospace", color="#F6EFE2")
    # - Rotating optical turret: Y = -17.65..+17.65, Z = 52.2..65.0 mm (Beam plane at Z = 59.0 mm!)
    ax.add_patch(Rectangle((-17.65, 52.2), 35.3, 12.8, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8))
    ax.text(0.0, 58.6, "Turret Ø35.3", ha="center", va="center", fontsize=6.8, fontweight="bold", family="monospace", color="#F6EFE2")

    # Plot ±4.5° Laser Scan Fan from Z = 59.0 mm forward over the 45.5 mm Camera!
    y_ray = np.array([17.65, 95.0])
    z_center = np.full_like(y_ray, 59.0)
    z_low = 59.0 - (y_ray - 17.65) * np.tan(np.radians(4.5))
    z_high = 59.0 + (y_ray - 17.65) * np.tan(np.radians(4.5))
    ax.fill_between(y_ray, z_low, z_high, color="#F2B417", alpha=0.38)
    ax.plot(y_ray, z_center, color="#2B5FAB", lw=2.0, ls="-.")
    ax.plot(y_ray, z_low, color="#2B5FAB", lw=1.4, ls=":")
    ax.text(56.0, 62.5, "LiDAR Beam Z=59.0mm (±4.5° Fan)\nClears 45.5mm Camera by +13.5mm!", ha="center", va="center", fontsize=7.2, fontweight="bold", family="monospace", color="#211D15", bbox=dict(boxstyle="round,pad=0.22", facecolor="#F6EFE2", edgecolor="#2B5FAB"))

    dim_arrow(ax, -45.0, 0.0, -45.0, 30.0, "30.0mm\nTower", (-5.5, 0), "#211D15", fontsize=7.4)
    dim_arrow(ax, -45.0, 30.0, -45.0, 65.0, "35.0mm\nLiDAR", (-5.5, 0), "#2B5FAB", fontsize=7.4)
    dim_arrow(ax, 38.0, 0.0, 38.0, 45.5, "45.5mm\nCam Top", (8.5, -4.0), "#E4402A", fontsize=7.4)
    dim_arrow(ax, 38.0, 45.5, 38.0, 52.2, "+6.7mm Turret Clear", (13.5, 0.5), "#2D8A4E", fontsize=7.2)

    # =========================================================================
    # VIEW 3 (axes[1, 0]): REAR / BACK ORTHOGRAPHIC ELEVATION (3-Tier Stack)
    # =========================================================================
    ax = axes[1, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-46, 46)
    ax.set_ylim(-6, 72)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title(
        "3 · REAR ORTHOGRAPHIC ELEVATION (3-Tier Stack: Radxa ZERO 3W + Breakout + LiDAR)",
        fontsize=11.0,
        fontweight="bold",
        color="#211D15",
        pad=8,
    )

    # Expansion plate (X = -44..+44, Z = -2..0)
    ax.add_patch(Rectangle((-44.0, -2.0), 88.0, 2.0, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))

    # Tower Base & Pillars (X = -33.5..+33.5 at Z = 0..3.6; Pillars at X = +-15.8..+-23.4, Z = 0..30.0)
    ax.add_patch(Rectangle((-33.5, 0.0), 67.0, 3.6, facecolor="#F2B417", edgecolor="#211D15", lw=1.6))
    for sign in (-1.0, +1.0):
        ax.add_patch(Rectangle((sign * 19.6 - 3.8, 3.6), 7.6, 26.4, facecolor="#F2B417", edgecolor="#211D15", lw=1.6))
        # Side cable loop clip (X = +-23.0..+-28.6, Z = 5.0..16.0)
        ax.add_patch(FancyBboxPatch((sign * 25.2 - 3.4, 5.0), 6.8, 11.0, boxstyle="round,pad=0,rounding_size=1.8", facecolor="#F2B417", edgecolor="#211D15", lw=1.4))
        ax.add_patch(Circle((sign * 25.4, 10.5), 2.2, facecolor="#EFE5D2", edgecolor="#E4402A", lw=1.2))
        # Radxa ZERO 3W standoff at X = +-28.75, Z = 0..5.2
        ax.add_patch(Rectangle((sign * 28.75 - 4.3, 0.0), 8.6, 5.2, facecolor="#F2B417", edgecolor="#211D15", lw=1.4))

    # Top LiDAR platform (X = -22.5..+22.5, Z = 26.0..30.0) + Mezzanine (X = -18..+18, Z = 16.2..26.4)
    ax.add_patch(Rectangle((-18.0, 16.2), 36.0, 10.2, facecolor="#F2B417", edgecolor="#211D15", lw=1.6))
    ax.add_patch(Rectangle((-26.5, 26.0), 53.0, 4.0, facecolor="#F2B417", edgecolor="#211D15", lw=1.6))
    # Cut out press-fit mezzanine cavity in rear view (20.3 x 8.4 mm at Z = 18.8..27.2)
    ax.add_patch(Rectangle((-10.15, 18.8), 20.3, 8.2, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.4))
    ax.add_patch(Rectangle((-8.2, 16.2), 16.4, 2.8, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.1, ls="--"))

    # Tier 1: Radxa ZERO 3W (X = -32.5..+32.5, Z = 5.2..6.8 PCB + 6.0mm GPIO pins up to Z = 12.8 / 15.5mm)
    ax.add_patch(Rectangle((-32.5, 5.2), 65.0, 1.6, facecolor="#2D8A4E", edgecolor="#211D15", lw=1.6))
    ax.add_patch(Rectangle((-25.5, 6.8), 51.0, 6.0, facecolor="#211D15", edgecolor="#F6EFE2", lw=1.0, alpha=0.85))
    for px, lbl in [(-16.0, "HDMI"), (+6.0, "USB-C1"), (+21.0, "USB-C2")]:
        ax.add_patch(Rectangle((px - 4.5, 6.8), 9.0, 3.4, facecolor="#D8DEE6", edgecolor="#211D15", lw=1.1))
    ax.text(0.0, 9.8, "Radxa ZERO 3W (65×30×10.3mm · 6mm Pins)", ha="center", va="center", fontsize=6.6, color="#F6EFE2", family="monospace", fontweight="bold")

    # Tier 2: 40x20x8mm Breakout Board seated in press-fit cradle (X = -10..+10, Z = 18.8..26.8)
    ax.add_patch(Rectangle((-10.0, 18.8), 20.0, 1.6, facecolor="#1E3A5F", edgecolor="#F6EFE2", lw=1.3))
    ax.add_patch(Rectangle((-5.0, 20.4), 10.0, 6.2, facecolor="#D8DEE6", edgecolor="#211D15", lw=1.2))
    ax.text(0.0, 23.5, "4-Pin\nBreakout", ha="center", va="center", fontsize=6.2, color="#211D15", family="monospace", fontweight="bold")

    # Tier 3: LDROBOT D500 LiDAR (X = -19.25..+19.25, Z = 30.0..52.2 + Turret X = -17.65..+17.65, Z = 52.2..65.0)
    ax.add_patch(Rectangle((-19.25, 30.0), 38.5, 22.2, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))
    ax.add_patch(Rectangle((-17.65, 52.2), 35.3, 12.8, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8))
    # Rear-side LiDAR mounting ears at X = +-21.95 (42.7–45.0 mm C-to-C)
    for sign in (-1.0, +1.0):
        ax.add_patch(Rectangle((sign * 21.95 - 3.5, 30.0), 7.0, 3.5, facecolor="#E4402A", edgecolor="#211D15", lw=1.3))

    dim_arrow(ax, -28.75, -4.0, +28.75, -4.0, "57.0–58.0 mm Radxa ZERO 3W Slots", (0, 2.0), "#2D8A4E", fontsize=7.6)
    dim_arrow(ax, -21.95, 67.5, +21.95, 67.5, "42.7–45.0 mm LiDAR Side Ear Slots", (0, 2.2), "#E4402A", fontsize=7.6)
    dim_arrow(ax, 37.5, 5.2, 37.5, 15.5, "10.3mm\nSBC Ht", (5.5, 0), "#2D8A4E", fontsize=7.2)

    # =========================================================================
    # VIEW 4 (axes[1, 1]): PRESS-FIT BREAKOUT CRADLE DETAIL & HOLE CALLOUT TABLE
    # =========================================================================
    ax = axes[1, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        "4 · PRESS-FIT BREAKOUT CRADLE & MOUNTING HOLE SPECIFICATIONS",
        fontsize=11.0,
        fontweight="bold",
        color="#211D15",
        pad=8,
    )

    # Box 1: LDROBOT D500 LiDAR & Breakout Mezzanine
    ax.add_patch(FancyBboxPatch((2, 32), 46, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#E4402A", lw=2.0))
    ax.text(25, 55.5, "[TIER 2 & 3] LIDAR + BREAKOUT CRADLE", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#E4402A", family="monospace")
    ax.text(
        4.0,
        43.5,
        "• LiDAR Deck: Z = +30.0 mm above plate\n"
        "  (Turret Z = 52.2..65.0 mm; clears 45.5 mm\n"
        "   front camera by +6.7 mm / +13.5 mm beam)\n"
        "• 3× LiDAR Ears: Front (0, +23.30 mm) &\n"
        "  Rear-Sides (X=±21.95, Y=-8.65, 5.4×2.9 slot\n"
        "  fits 42.69 mm CAD & 45.0 mm measured!)\n"
        "• Breakout Cradle: 40.6 × 20.3 × 8.6 mm\n"
        "  press-fit ledges + 4× snap nibs (no screws)",
        ha="left",
        va="center",
        fontsize=6.4,
        color="#211D15",
        family="monospace",
    )

    # Box 2: Radxa ZERO 3W & Expansion Plate Interface
    ax.add_patch(FancyBboxPatch((52, 32), 46, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#2D8A4E", lw=2.0))
    ax.text(75, 55.5, "[TIER 1] RADXA ZERO 3W & PLATE BASE", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#2D8A4E", family="monospace")
    ax.text(
        54.0,
        43.5,
        "• Host Board: Radxa ZERO 3W (RK3566)\n"
        "  65.0 × 30.0 × 10.3 mm (with 6.0 mm pins)\n"
        "• 4× Corner Bosses: X=±28.75, Y=-26±11.25\n"
        "  (3.6×3.2 mm slots + Ø3.2 mm M2 inserts;\n"
        "   fits 57×22 mm measured & 58×23 mm spec)\n"
        "• Plate Mounting: 4× Central M3 Square\n"
        "  (33.5–34.0 mm) + 4× 49.0 mm Wide Slots",
        ha="left",
        va="center",
        fontsize=6.4,
        color="#211D15",
        family="monospace",
    )

    # Box 3: Cable Loop Routing & Support-Free Printing
    ax.add_patch(FancyBboxPatch((2, 2), 96, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#211D15", lw=2.0))
    ax.text(50, 25.5, "[USB CABLE LOOP CLEARANCE & 3D PRINTING] ZERO HEAD-TO-HEAD PORT COLLISION", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#211D15", family="monospace")
    ax.text(
        4.0,
        13.0,
        "1. Breakout Board Micro-USB faces forward (+Y = +20.5 mm) into open space; Radxa ZERO 3W 2× USB-C ports\n"
        "   face rearward (-Y = -41.0 mm) into open space — zero head-to-head plug interference!\n"
        "2. Integrated Left & Right Cable-Loop Guide Arches (X = ±25.4 mm) route both the Camera Mini-USB -> USB-C1\n"
        "   cable and the LiDAR Breakout Micro-USB -> USB-C2 cable in smooth R ≥ 18 mm loops along the tower sides.\n"
        "3. Included as both a 1-piece support-free tower (`horace_lidar_sbc_tower.stl`) and a 2-piece split.",
        ha="left",
        va="center",
        fontsize=6.5,
        color="#211D15",
        family="monospace",
    )

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    png_out = LIDAR_CAD_DIR / "lidar-tower-orthographic.png"
    svg_out = LIDAR_CAD_DIR / "lidar-tower-orthographic.svg"
    fig.savefig(png_out, dpi=180, facecolor=fig.get_facecolor())
    fig.savefig(svg_out, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved LiDAR Tower 4-view orthographic drawings -> {png_out} and {svg_out}")
    return svg_out, png_out


if __name__ == "__main__":
    render_3d_preview_sheet()
    render_orthographic_drawings()
