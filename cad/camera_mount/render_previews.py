#!/usr/bin/env python3
"""Render multi-angle 3D preview sheet and engineering dimension diagrams for horaceTheCheese."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import trimesh

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon


REPO_ROOT = Path(__file__).resolve().parents[2]
CAD_DIR = REPO_ROOT / "cad" / "camera_mount"
ASSETS_CAD_DIR = REPO_ROOT / "docs" / "assets" / "cad"


def shade_mesh_faces(
    mesh: trimesh.Trimesh,
    base_rgb: tuple[float, float, float],
    light_dir: tuple[float, float, float] = (0.45, -0.55, 0.70),
    alpha: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Lambertian-shaded face colors and triangles for Poly3DCollection."""
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


def transform_mesh(
    mesh: trimesh.Trimesh,
    rot_xyz_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
    translate: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> trimesh.Trimesh:
    """Return a transformed copy of a mesh where model (X, Y_up, Z_front) maps to plot (X, Y_depth, Z_up)."""
    m = mesh.copy()
    # Map model coords (X_right, Y_up, Z_front) -> world (X_right, Y_front=Z_front, Z_up=Y_up)
    v = m.vertices.copy()
    m.vertices = np.column_stack([v[:, 0], v[:, 2], v[:, 1]])
    # Fix face winding if determinant < 0 (swapping Y and Z flips handedness)
    m.faces = m.faces[:, ::-1]
    rx, ry, rz = [np.radians(a) for a in rot_xyz_deg]
    if any(rot_xyz_deg):
        rot = trimesh.transformations.euler_matrix(rx, ry, rz, "sxyz")
        m.apply_transform(rot)
    m.apply_translation(translate)
    return m


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


def make_camera_pcb_meshes() -> list[tuple[trimesh.Trimesh, str]]:
    """Create illustrative 3D meshes for the 100x22x1.6mm stereo camera PCB, 85mm baseline lenses, and Mini-USB."""
    import manifold3d as mf
    from generate_camera_mount import CameraMountParams, cylinder_z, manifold_to_trimesh, rounded_rect_prism

    p = CameraMountParams()
    z_pcb = p.back_thickness  # 6.8 mm
    z_front = z_pcb + p.pcb_thickness  # 8.4 mm
    # Black PCB substrate (z = 6.8 to 8.4 mm in assembly coords)
    pcb = rounded_rect_prism(p.pcb_width, p.pcb_height, p.pcb_thickness, 0.8, (0.0, 0.0), z0=z_pcb)
    for hx in (-p.hole_outer_x, +p.hole_outer_x, -p.hole_inner_inner_x, +p.hole_inner_inner_x, -p.hole_inner_outer_x, +p.hole_inner_outer_x):
        for hy in (-p.hole_y, +p.hole_y):
            pcb = pcb - cylinder_z(2.0, 5.0, hx, hy, z0=z_pcb - 1.0)

    # Two 14x14mm M12 lens bases + Ø14mm barrels at X = +-42.5 mm, Y = 0.0 mm (85.0 mm baseline)
    lenses = None
    caps = None
    for lx in (-p.lens_baseline * 0.5, +p.lens_baseline * 0.5):
        base = rounded_rect_prism(14.0, 14.0, 6.0, 1.2, (lx, 0.0), z0=z_front)
        barrel = cylinder_z(14.0, 14.5, lx, 0.0, z0=z_front, segments=48)
        cap = cylinder_z(15.0, 4.2, lx, 0.0, z0=z_front + 13.6, segments=48) - cylinder_z(12.6, 3.0, lx, 0.0, z0=z_front + 15.0, segments=48)
        u = base + barrel
        lenses = u if lenses is None else (lenses + u)
        caps = cap if caps is None else (caps + cap)

    # Gold Mini-USB receptacle (x = -3.4..+3.4, y = -11.2..-4.0, z = 8.4..12.3)
    usb_rec = rounded_rect_prism(6.8, 7.2, 3.9, 0.6, (0.0, -7.6), z0=z_front)

    # Two blue/white FFC ribbon arches (10.0 mm high x 13.0 mm wide at x = +-28.0, y = -6.5..+6.5, z = 8.4..18.4)
    ribbons = None
    for rx in (-28.0, +28.0):
        rib = rounded_rect_prism(10.0, 13.0, 10.0, 1.2, (rx, 0.0), z0=z_front)
        ribbons = rib if ribbons is None else (ribbons + rib)

    return [
        (manifold_to_trimesh(pcb), "#1E242B"),
        (manifold_to_trimesh(lenses), "#2B3038"),
        (manifold_to_trimesh(caps), "#D8DEE6"),
        (manifold_to_trimesh(usb_rec), "#D4A437"),
        (manifold_to_trimesh(ribbons), "#2B5FAB"),
    ]


def make_upturned_bracket_mesh() -> trimesh.Trimesh:
    """Create the exact factory DXF 90-degree upturned front bracket of the WAVE ROVER expansion plate."""
    import manifold3d as mf
    from generate_camera_mount import cylinder_z, manifold_to_trimesh, rounded_rect_prism

    # Vertical upturned tab (44.88 mm wide, y = -25.23 to -5.60, z = -2.0 to 0.0 mm behind flat Z=0 backplate)
    tab = rounded_rect_prism(44.88, 19.63, 2.0, 1.5, (0.0, -15.415), z0=-2.0)
    # Central U-window cutout (25.75 mm wide x 9.30 mm tall)
    window = rounded_rect_prism(25.75, 9.30, 4.0, 1.2, (0.0, -14.47), z0=-3.0)
    # Two half-square notches on inside edge of top crossbar (X = +-7.45 mm, width = 3.12 mm)
    notch_l = rounded_rect_prism(3.12, 3.2, 4.0, 0.5, (-7.45, -8.8), z0=-3.0)
    notch_r = rounded_rect_prism(3.12, 3.2, 4.0, 0.5, (+7.45, -8.8), z0=-3.0)
    # Two M2 holes at X = +-10.25 mm, Y = -7.75 mm
    hole_l = cylinder_z(2.3, 5.0, -10.25, -7.75, z0=-3.0)
    hole_r = cylinder_z(2.3, 5.0, +10.25, -7.75, z0=-3.0)
    # Horizontal deck stub extending rearward (z = -30.0 to 0.0 mm, y = -27.23 to -25.23 mm)
    deck = rounded_rect_prism(68.0, 2.0, 30.0, 1.5, (0.0, -26.23), z0=-30.0)
    deck_cut = rounded_rect_prism(26.9, 4.0, 20.0, 1.5, (0.0, -26.23), z0=-20.0)

    solid = (tab - window - notch_l - notch_r - hole_l - hole_r) + (deck - deck_cut)
    return manifold_to_trimesh(solid)


def style_3d_ax(ax, title: str, subtitle: str, xlim=(-60, 60), ylim=(-35, 35), zlim=(-32, 22), elev=22, azim=-52) -> None:
    ax.set_facecolor("#F6EFE2")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_zlim(*zlim)
    ax.set_box_aspect([xlim[1] - xlim[0], ylim[1] - ylim[0], zlim[1] - zlim[0]])
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.text2D(
        0.03,
        0.95,
        title,
        transform=ax.transAxes,
        fontsize=12.5,
        fontweight="bold",
        color="#211D15",
        family="sans-serif",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#F2B417", edgecolor="#211D15", linewidth=2.0),
    )
    ax.text2D(
        0.03,
        0.04,
        subtitle,
        transform=ax.transAxes,
        fontsize=9.2,
        color="#211D15",
        family="monospace",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#EFE5D2", edgecolor="#211D15", linewidth=1.4),
    )


def render_3d_preview_sheet() -> Path:
    back_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_back_mount_v2.stl")
    visor_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_front_visor_v2.stl")
    shim_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_usb_shim.stl")
    pcb_parts = make_camera_pcb_meshes()
    bracket_mesh = make_upturned_bracket_mesh()

    fig = plt.figure(figsize=(16, 11.5), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · Binocular Stereo Camera Mount v2.2 (100×22mm PCB · 85.0mm Lens Baseline · M3/M2 Inserts)",
        fontsize=15.5,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    # --- Panel 1: Assembled Front 3/4 View on Upturned 90° Metal Bracket ---
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    add_mesh_to_ax(ax1, transform_mesh(bracket_mesh), "#2A2D32")
    add_mesh_to_ax(ax1, transform_mesh(back_stl), "#2B5FAB")
    for m_pcb, c_pcb in pcb_parts:
        add_mesh_to_ax(ax1, transform_mesh(m_pcb), c_pcb)
    # Visor sits at z = 9.8 mm in assembly
    visor_assembled = visor_stl.copy()
    visor_assembled.apply_translation([0.0, 0.0, 9.8])
    add_mesh_to_ax(ax1, transform_mesh(visor_assembled), "#E4402A")
    style_3d_ax(
        ax1,
        "1 · Assembled on WAVE ROVER 90° Front Bracket",
        "Front visor v2 (#E4402A) + Back mount v2 (#2B5FAB) + 85.0 mm lens baseline (X=±42.5mm)",
        xlim=(-64, 64),
        ylim=(-30, 30),
        zlim=(-32, 19),
        elev=20,
        azim=122,
    )

    # --- Panel 2: Rear 3/4 View Showing Flat Z=0 Backplate & 90° Tab Interface ---
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    add_mesh_to_ax(ax2, transform_mesh(back_stl), "#2B5FAB")
    add_mesh_to_ax(ax2, transform_mesh(visor_assembled), "#E4402A")
    bracket_offset = bracket_mesh.copy()
    bracket_offset.apply_translation([0.0, 0.0, -16.0])
    add_mesh_to_ax(ax2, transform_mesh(bracket_offset), "#33373D", alpha=0.88)
    style_3d_ax(
        ax2,
        "2 · Rear 90° Tab Interface & M3 Heat-Set Insert Bores",
        "2x U-window M3 (X=±10.0mm) + 2x crossbar M2 (X=±10.25mm) + M3 Mini-USB clamp",
        xlim=(-64, 64),
        ylim=(-38, 24),
        zlim=(-32, 19),
        elev=22,
        azim=-52,
    )

    # --- Panel 3: Exploded Assembly View ---
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    b_exp = bracket_mesh.copy()
    b_exp.apply_translation([0.0, 0.0, -26.0])
    add_mesh_to_ax(ax3, transform_mesh(b_exp), "#2A2D32")

    back_exp = back_stl.copy()
    back_exp.apply_translation([0.0, 0.0, -4.0])
    add_mesh_to_ax(ax3, transform_mesh(back_exp), "#2B5FAB")

    for m_pcb, c_pcb in pcb_parts:
        mp = m_pcb.copy()
        mp.apply_translation([0.0, 0.0, 14.0])
        add_mesh_to_ax(ax3, transform_mesh(mp), c_pcb)

    vis_exp = visor_stl.copy()
    vis_exp.apply_translation([0.0, 0.0, 38.0])
    add_mesh_to_ax(ax3, transform_mesh(vis_exp), "#E4402A")

    # USB shim exploded below the collar
    shim_exp = shim_stl.copy()
    r_shim = trimesh.transformations.euler_matrix(np.radians(90.0), 0.0, 0.0, "sxyz")
    shim_exp.apply_transform(r_shim)
    shim_exp.apply_translation([0.0, -44.0, 6.0])
    add_mesh_to_ax(ax3, transform_mesh(shim_exp), "#F2B417")

    style_3d_ax(
        ax3,
        "3 · Exploded Assembly (5 Layers)",
        "90° Tab -> Back Cover v2 -> 100×22mm PCB (85mm Lenses) + USB Shim -> Front Visor v2",
        xlim=(-64, 64),
        ylim=(-42, 58),
        zlim=(-46, 20),
        elev=21,
        azim=128,
    )

    # --- Panel 4: Support-Free Print Bed Layout (Z = 0 Flat on Build Plate) ---
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    gx = np.linspace(-65, 65, 14)
    gy = np.linspace(-55, 55, 12)
    for x in gx:
        ax4.plot([x, x], [gy[0], gy[-1]], [0, 0], color="#211D15", alpha=0.15, linewidth=0.7)
    for y in gy:
        ax4.plot([gx[0], gx[-1]], [y, y], [0, 0], color="#211D15", alpha=0.15, linewidth=0.7)

    b_bed = back_stl.copy()
    b_bed.apply_translation([0.0, 23.0, 0.0])
    add_mesh_to_ax(ax4, b_bed, "#2B5FAB")

    v_bed = visor_stl.copy()
    v_bed.apply_translation([0.0, -22.0, 0.0])
    add_mesh_to_ax(ax4, v_bed, "#E4402A")

    s_bed = shim_stl.copy()
    s_bed.apply_translation([48.0, 0.0, 0.0])
    add_mesh_to_ax(ax4, s_bed, "#F2B417")

    style_3d_ax(
        ax4,
        "4 · Print Bed Orientation (100% Support-Free FDM)",
        "All 3 STLs print flat on Z=0 · 58.1 cm³ total (~70g PLA/PETG) · 45° vaulted roofs",
        xlim=(-66, 66),
        ylim=(-54, 54),
        zlim=(0, 32),
        elev=34,
        azim=-45,
    )

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    out_path = CAD_DIR / "camera-mount-render.png"
    fig.savefig(out_path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved 3D preview sheet -> {out_path}")
    return out_path


def render_engineering_dimensions() -> tuple[Path, Path]:
    """Generate assembly engineering dimension sheet in both SVG and PNG formats."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 11.5), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · Stereo Camera (100×22 mm, 85 mm Baseline) & Enclosure v2.2 Dimensions (mm)",
        fontsize=15.5,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    def dim_arrow(ax, x1, y1, x2, y2, text, text_offset=(0, 2.2), color="#E4402A", fontsize=8.6):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="<->", color=color, lw=1.8, shrinkA=0, shrinkB=0),
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

    # --- Panel A: Stereo Camera PCB & Enclosure Front Orthographic ---
    ax = axes[0, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-68, 68)
    ax.set_ylim(-26, 26)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("A · Stereo Camera Module (100×22 mm PCB · 85.0 mm Lens Baseline)", fontsize=11.5, fontweight="bold", color="#211D15", pad=10)

    # Outer enclosure outline (122.2 x 29.6 mm)
    ax.add_patch(FancyBboxPatch((-60.5, -14.8), 121.0, 29.6, boxstyle="round,pad=0,rounding_size=4.8", fill=False, edgecolor="#2B5FAB", lw=2.2, ls="--"))
    # 4x Outer M3 Casing Ears at X = +-56.5, Y = +-9.0
    for ex in (-56.5, +56.5):
        for ey in (-9.0, +9.0):
            ax.add_patch(Circle((ex, ey), 4.6, facecolor="#E4402A", edgecolor="#211D15", lw=1.2, alpha=0.8))
            ax.add_patch(Circle((ex, ey), 1.7, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.0))

    # PCB (100.0 x 22.0 mm)
    ax.add_patch(Rectangle((-50.0, -11.0), 100.0, 22.0, facecolor="#211D15", edgecolor="#211D15", lw=2.0))
    # 14x14 mm lens bases + Ø14 mm barrels + Ø16.6 mm visor bores at X = +-42.5 mm, Y = 0.0 mm
    for lx in (-42.5, +42.5):
        ax.add_patch(Rectangle((lx - 7.0, -7.0), 14.0, 14.0, facecolor="#3A3F47", edgecolor="#F6EFE2", lw=1.2))
        ax.add_patch(Circle((lx, 0.0), 7.5, facecolor="#9BA5B4", edgecolor="#211D15", lw=1.5, alpha=0.85))
        ax.add_patch(Circle((lx, 0.0), 8.3, fill=False, edgecolor="#E4402A", lw=1.6, ls=":"))
        ax.plot([lx, lx], [-12, 16], color="#E4402A", lw=1.0, ls="-.")

    # FFC Ribbons
    for rx in (-29.5, +29.5):
        ax.add_patch(Rectangle((rx - 4.0, -5.5), 8.0, 11.0, facecolor="#2B5FAB", edgecolor="#F6EFE2", lw=1.0))

    # Mini-USB at X = 0, Y = -11.0..-3.8 mm
    ax.add_patch(Rectangle((-3.4, -11.2), 6.8, 7.2, facecolor="#F2B417", edgecolor="#211D15", lw=1.5))

    # 12 M2 mounting holes at X = +-48.0, +-26.1, +-22.1, Y = +-9.0
    for hx in (-48.0, -26.1, -22.1, +22.1, +26.1, +48.0):
        for hy in (-9.0, +9.0):
            ax.add_patch(Circle((hx, hy), 1.6, facecolor="#F2B417", edgecolor="#211D15", lw=0.8))
            ax.add_patch(Circle((hx, hy), 0.9, facecolor="#EFE5D2", edgecolor="#211D15", lw=0.6))

    dim_arrow(ax, -42.5, 16.2, +42.5, 16.2, "85.0 mm Lens Baseline (X=±42.5, Y=0.0)", (0, 2.8), "#E4402A", fontsize=8.2)
    dim_arrow(ax, -48.0, -16.8, +48.0, -16.8, "96.0 × 18.0 mm Board Corner Holes (X=±48.0, Y=±9.0)", (0, -2.8), "#2B5FAB", fontsize=8.0)
    dim_arrow(ax, -56.5, -22.5, +56.5, -22.5, "113.0 × 18.0 mm Casing M3 Ears (122.2 mm Shell)", (0, -2.6), "#211D15", fontsize=8.0)
    dim_arrow(ax, 62.5, -11.0, 62.5, +11.0, "22.0 mm\nPCB", (3.8, 0), "#211D15", fontsize=7.6)

    # --- Panel B: WAVE ROVER 90° Upturned Front Bracket & M3/M2 Insert Bores ---
    ax = axes[0, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-32, 32)
    ax.set_ylim(-24, 11.5)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("B · WAVE ROVER 90° Upturned Tab & Heat-Set Insert Bores", fontsize=11.5, fontweight="bold", color="#211D15", pad=10)

    ax.add_patch(Rectangle((-22.44, -20.83), 44.88, 19.63, facecolor="#2C3036", edgecolor="#211D15", lw=2.0))
    ax.add_patch(Rectangle((-12.88, -14.8), 25.76, 9.38, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.6))
    for sign in (-1.0, +1.0):
        x0 = sign * 7.45 - 1.56
        ax.add_patch(Rectangle((x0, -5.5), 3.12, 2.2, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.4))
        ax.add_patch(Circle((sign * 7.45, -4.4), 1.4, facecolor="#F2B417", edgecolor="#E4402A", lw=1.4))
        ax.add_patch(Circle((sign * 10.25, -3.35), 1.6, facecolor="#2B5FAB", edgecolor="#F6EFE2", lw=1.4))
        ax.add_patch(Circle((sign * 10.00, -10.5), 2.0, facecolor="#E4402A", edgecolor="#F6EFE2", lw=1.4))

    dim_arrow(ax, -22.44, 5.2, +22.44, 5.2, "44.88 mm Tab Width (2.00 mm Thick)", (0, 2.2), "#211D15")
    dim_arrow(ax, -10.25, -0.2, +10.25, -0.2, "20.5 mm M2 Insert Bores (Ø3.2mm)", (0, 2.1), "#2B5FAB")
    dim_arrow(ax, -10.00, -17.5, +10.00, -17.5, "20.0 mm M3 U-Window Inserts (Ø4.0mm)", (0, -2.4), "#E4402A")
    dim_arrow(ax, 25.5, -20.83, 25.5, -1.2, "19.63 mm\nTab Ht", (4.2, 0), "#211D15", fontsize=8.0)

    # --- Panel C: Side Profile & Lens Protrusion Cross-Section ---
    ax = axes[1, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-6, 30)
    ax.set_ylim(-32, 19)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("C · Side Cross-Section (6.8 mm Base + 1.6 mm PCB + Front Visor v2)", fontsize=11.5, fontweight="bold", color="#211D15", pad=10)

    # Rear shell (z = 0 to 9.8, y = -14.8 to +14.8) + lower USB collar (y = -26.6 to -13.3, z = 0 to 18.8)
    ax.add_patch(Rectangle((0.0, -14.8), 6.8, 29.6, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    ax.add_patch(Rectangle((0.0, -26.6), 18.8, 13.3, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.65))
    # Upturned 2.0 mm metal tab behind z = 0 (-2.0..0.0 mm)
    ax.add_patch(Rectangle((-2.0, -25.23), 2.0, 19.63, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))
    ax.add_patch(Rectangle((-5.5, -27.23), 5.5, 2.0, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))
    # PCB (z = 6.8 to 8.4 mm, y = -11 to +11 mm)
    ax.add_patch(Rectangle((6.8, -11.0), 1.6, 22.0, facecolor="#1E242B", edgecolor="#211D15", lw=1.5))
    # Lens base + barrel + cap (z = 8.4 to 27.4 mm, y = -7 to +7 mm)
    ax.add_patch(Rectangle((8.4, -7.0), 15.5, 14.0, facecolor="#3A3F47", edgecolor="#211D15", lw=1.5))
    ax.add_patch(Rectangle((23.9, -7.5), 3.5, 15.0, facecolor="#9BA5B4", edgecolor="#211D15", lw=1.5))
    # Front visor + sun brow (z = 9.8 to 24.3 mm)
    ax.add_patch(Polygon([(9.8, 10.6), (24.3, 10.6), (24.3, 14.8), (9.8, 14.8)], closed=True, facecolor="#E4402A", edgecolor="#211D15", lw=1.6))

    dim_arrow(ax, 8.4, 15.8, 27.4, 15.8, "19.0 mm Lens + Cap", (0, 1.8), "#E4402A", fontsize=8.5)
    dim_arrow(ax, 0.0, -29.2, 18.8, -29.2, "18.8 mm Collar Depth", (0, -2.0), "#2B5FAB", fontsize=8.5)

    # --- Panel D: Mini-USB Strain-Relief Clamp & Parametric Shim Detail ---
    ax = axes[1, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-18, 18)
    ax.set_ylim(-2, 22)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("D · Mini-USB Plug Holder, M3 Insert Pinch Clamp & Parametric Shim", fontsize=11.5, fontweight="bold", color="#211D15", pad=10)

    ax.add_patch(FancyBboxPatch((-10.0, 0.0), 20.0, 18.8, boxstyle="round,pad=0,rounding_size=2.5", facecolor="#2B5FAB", edgecolor="#211D15", lw=2.0, alpha=0.85))
    ax.add_patch(FancyBboxPatch((-15.0, 7.2), 30.0, 10.6, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    ax.add_patch(Rectangle((-6.5, 7.4), 13.0, 9.0, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.8))
    ax.add_patch(Rectangle((-6.2, 7.55), 12.4, 8.7, facecolor="#F2B417", edgecolor="#211D15", lw=1.6))
    ax.add_patch(Rectangle((-5.1, 8.4), 10.2, 7.0, facecolor="#3A3F47", edgecolor="#211D15", lw=1.4))
    ax.add_patch(Rectangle((-0.9, 15.4), 1.8, 3.6, facecolor="#EFE5D2", edgecolor="#E4402A", lw=1.2))
    ax.plot([-16.5, 16.5], [12.6, 12.6], color="#E4402A", lw=2.0, ls="--")
    ax.text(0.0, 11.9, "10.2 × 7.0 mm\nMini-USB Plug\n(Parametric Shim)", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#F6EFE2", family="monospace")

    dim_arrow(ax, -6.5, 4.2, +6.5, 4.2, "13.0 mm Max Bay Width", (0, -1.6), "#211D15", fontsize=8.5)
    dim_arrow(ax, -15.0, 19.6, +15.0, 19.6, "30.0 mm M3 Heat-Set Insert Pinch Jaws", (0, 1.2), "#E4402A", fontsize=8.2)

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    png_path = CAD_DIR / "camera-mount-dimensions.png"
    svg_path = CAD_DIR / "camera-mount-dimensions.svg"
    fig.savefig(png_path, dpi=180, facecolor=fig.get_facecolor())
    fig.savefig(svg_path, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved engineering dimensions -> {png_path} and {svg_path}")
    return svg_path, png_path


def render_back_mount_v2_sheets() -> tuple[Path, Path, Path]:
    """Render 4-panel 3D inspection sheet + 4-panel engineering drawing for Back Cover v2."""
    back_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_back_mount_v2.stl")

    # =========================================================================
    # 1. 4-Panel 3D Render Sheet of `horace_cam_back_mount_v2.stl`
    # =========================================================================
    fig = plt.figure(figsize=(16, 11.5), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · Back Camera Cover v2 (M3/M2 Heat-Set Inserts · Zero Hex Nuts · Gusset Reinforced)",
        fontsize=15.5,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    # Panel 1: Front / Inside View (looking directly into the Z=+9.8mm PCB cavity & heat-set insert bosses)
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    add_mesh_to_ax(ax1, back_stl, "#2B5FAB")
    style_3d_ax(
        ax1,
        "1 · Front / Inside View (8× Board M2 Inserts + 4× Casing M3 Inserts)",
        "4× Outer M3 (X=±56.5, Y=±9.0) + 8× Board M2 Inserts (X=±48.0 & X=±26.1, Y=±9.0)",
        xlim=(-58, 58),
        ylim=(-27, 19),
        zlim=(0, 22),
        elev=46,
        azim=-62,
    )

    # Panel 2: Rear Face (Flipped 180° around X so the 100% flat Z=0 build-plate face is facing up!)
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    back_rear_up = back_stl.copy()
    r_flip = trimesh.transformations.euler_matrix(np.radians(180.0), 0.0, 0.0, "sxyz")
    back_rear_up.apply_transform(r_flip)
    back_rear_up.apply_translation([0.0, -5.0, 18.8])
    add_mesh_to_ax(ax2, back_rear_up, "#2B5FAB")
    style_3d_ax(
        ax2,
        "2 · Rear Face (100% Flat Z=0 Build Plate — Zero Hex Nut Recesses!)",
        "Sealed 6.8mm backplate · Only 2× M3 (Ø4.0mm) + 2× M2 (Ø3.2mm) + 2× Ø2.8mm bracket bores",
        xlim=(-58, 58),
        ylim=(-23, 23),
        zlim=(0, 22),
        elev=48,
        azim=-58,
    )

    # Panel 3: Close-up of Structural Gusset Wings & Cut-Down M3 Mini-USB Clamp Jaws
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    add_mesh_to_ax(ax3, back_stl, "#E4402A")
    style_3d_ax(
        ax3,
        "3 · Cut-Down USB Collar (Y ≤ -16.2mm) & M3 Heat-Set Pinch Clamp",
        "1.4 mm clear below Front Visor (Y=-14.8mm) · Open USB neck (Z=6.4mm) · M3 insert jaw",
        xlim=(-50, 50),
        ylim=(-28, 13),
        zlim=(0, 20),
        elev=28,
        azim=-40,
    )

    # Panel 4: Flat FDM Print Bed Orientation (Z = 0.0 on Build Plate)
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    gx = np.linspace(-65, 65, 14)
    gy = np.linspace(-30, 30, 7)
    for x in gx:
        ax4.plot([x, x], [gy[0], gy[-1]], [0, 0], color="#211D15", alpha=0.16, linewidth=0.8)
    for y in gy:
        ax4.plot([gx[0], gx[-1]], [y, y], [0, 0], color="#211D15", alpha=0.16, linewidth=0.8)

    b_bed = back_stl.copy()
    b_bed.apply_translation([0.0, 5.5, 0.0])
    add_mesh_to_ax(ax4, b_bed, "#2B5FAB")
    style_3d_ax(
        ax4,
        "4 · Print Orientation: Flat on Z=0.0 (Zero Supports, Zero Bridges)",
        "122.2 × 42.4 × 18.8 mm · 32.29 cm³ (~39g PLA/PETG) · 45° conical roofs on rear bores",
        xlim=(-62, 62),
        ylim=(-28, 28),
        zlim=(0, 22),
        elev=36,
        azim=-48,
    )

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    render_out = CAD_DIR / "back-mount-v2-render.png"
    fig.savefig(render_out, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved Back Cover v2 3D render -> {render_out}")

    # =========================================================================
    # 2. 4-Panel Engineering & Heat-Set Insert Dimension Drawing (SVG + PNG)
    # =========================================================================
    fig, axes = plt.subplots(2, 2, figsize=(16.5, 12.0), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · Back Camera Cover v2 — Heat-Set Insert Hole Sizes & Structural Drawing (mm)",
        fontsize=15.5,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    def dim_arrow(ax, x1, y1, x2, y2, text, text_offset=(0, 2.2), color="#E4402A", fontsize=8.6):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="<->", color=color, lw=1.8, shrinkA=0, shrinkB=0),
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
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#F6EFE2", edgecolor=color, lw=1.2),
        )

    # --- Panel A: Front View (All Front Heat-Set Insert Bores & Cut-Down USB Collar) ---
    ax = axes[0, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-69, 69)
    ax.set_ylim(-34, 26)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("A · Front View — 8× Board M2 Inserts (X=±48.0 & ±26.1) + 4× Casing M3 Ears", fontsize=10.8, fontweight="bold", color="#211D15", pad=8)

    # Gusset polygon outline
    gusset_xy = [(-48.0, -12.6), (48.0, -12.6), (29.0, -19.6), (17.0, -26.6), (-17.0, -26.6), (-29.0, -19.6)]
    ax.add_patch(Polygon(gusset_xy, closed=True, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.65))
    # Cut-down USB collar & pinch jaws strictly below Y = -16.2 mm (Y = -26.6..-16.2 mm)
    ax.add_patch(FancyBboxPatch((-15.0, -25.8), 30.0, 8.4, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    ax.add_patch(FancyBboxPatch((-10.0, -26.6), 20.0, 10.4, boxstyle="round,pad=0,rounding_size=2.2", facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.9))
    # Upper body (121.0 x 29.6 mm) + 4 corner Ø9.2 mm bosses (total width 122.2 mm)
    ax.add_patch(FancyBboxPatch((-60.5, -14.8), 121.0, 29.6, boxstyle="round,pad=0,rounding_size=4.8", facecolor="#2B5FAB", edgecolor="#211D15", lw=2.0, alpha=0.88))
    # Diagonal stiffening ribs
    ax.add_patch(Polygon([(-13.5, -25.6), (-9.5, -25.6), (-36.0, -12.6), (-43.0, -12.6)], closed=True, facecolor="#F2B417", edgecolor="#211D15", lw=1.3))
    ax.add_patch(Polygon([(9.5, -25.6), (13.5, -25.6), (43.0, -12.6), (36.0, -12.6)], closed=True, facecolor="#F2B417", edgecolor="#211D15", lw=1.3))
    # PCB cavity (101.2 x 23.2 mm for 100.0 x 22.0 mm board)
    ax.add_patch(Rectangle((-50.6, -11.6), 101.2, 23.2, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.6))
    # SMD pocket (98.0 x 18.0 mm)
    ax.add_patch(Rectangle((-49.0, -9.0), 98.0, 18.0, facecolor="#DFD3BC", edgecolor="#211D15", lw=1.0, ls="--"))
    # Center stiffening bridge (26 x 23.2 mm)
    ax.add_patch(Rectangle((-13.0, -11.6), 26.0, 23.2, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.0))

    # 4x Outer Corner M3 Heat-Set Insert Bosses (X = +-56.5, Y = +-9.0, Ø9.2mm boss, Ø4.0mm bore — outside pocket!)
    for ex in (-56.5, +56.5):
        for ey in (-9.0, +9.0):
            ax.add_patch(Circle((ex, ey), 4.6, facecolor="#E4402A", edgecolor="#211D15", lw=1.4))
            ax.add_patch(Circle((ex, ey), 2.0, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))

    # 4x PCB End M2 Heat-Set Insert Bosses (X = +-48.0, Y = +-9.0, Ø6.0mm boss, Ø3.2mm bore — 96.0 x 18.0mm C-to-C!)
    for bx in (-48.0, +48.0):
        for by in (-9.0, +9.0):
            ax.add_patch(Circle((bx, by), 3.0, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
            ax.add_patch(Circle((bx, by), 1.6, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.0))

    # 4x Middle PCB M2 Heat-Set Insert Bosses (X = +-26.1, Y = +-9.0, Ø6.0mm boss, Ø3.2mm bore — 52.2 x 18.0mm C-to-C!)
    for px in (-26.1, +26.1):
        for py in (-9.0, +9.0):
            ax.add_patch(Circle((px, py), 3.0, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
            ax.add_patch(Circle((px, py), 1.6, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.0))

    dim_arrow(ax, -56.5, 17.5, +56.5, 17.5, "113.0 × 18.0 mm · 4× Casing M3 Inserts (X=±56.5, Y=±9.0)", (0, 3.2), "#E4402A", fontsize=7.9)
    dim_arrow(ax, -50.6, 12.2, +50.6, 12.2, "101.2 × 23.2 mm Pocket (100×22mm Board + 0.6mm/side)", (0, 2.2), "#211D15", fontsize=7.6)
    dim_arrow(ax, -48.0, -16.5, +48.0, -16.5, "96.0 × 18.0 mm · 4× Corner M2 Inserts (X=±48.0, Y=±9.0)", (0, -3.0), "#211D15", fontsize=7.8)
    dim_arrow(ax, -26.1, 1.2, +26.1, 1.2, "52.2 × 18.0 mm · 4× Middle M2 Inserts (X=±26.1, Y=±9.0)", (0, 2.5), "#2B5FAB", fontsize=7.8)
    dim_arrow(ax, -15.0, -29.0, +15.0, -29.0, "30.0 mm USB Jaws (Cut Down to Y ≤ -16.2mm)", (0, -2.8), "#E4402A", fontsize=8.0)

    # --- Panel B: Rear Flat Bed Face (Z=0.0) & 90° Metal Bracket Fastening ---
    ax = axes[0, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-64, 64)
    ax.set_ylim(-32, 21)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("B · Rear Face (Z = 0.0 Flat Bed) + 90° Metal Bracket Overlay", fontsize=11.5, fontweight="bold", color="#211D15", pad=8)

    # Flat rear outline of v2 back cover
    ax.add_patch(Polygon(gusset_xy, closed=True, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.45))
    ax.add_patch(FancyBboxPatch((-60.5, -14.8), 121.0, 29.6, boxstyle="round,pad=0,rounding_size=4.8", facecolor="#2B5FAB", edgecolor="#211D15", lw=2.0, alpha=0.45))

    # Overlay WAVE ROVER 90° metal tab (-22.44..+22.44 mm, y = -25.23..-5.60 mm)
    ax.add_patch(Rectangle((-22.44, -25.23), 44.88, 19.63, facecolor="#2C3036", edgecolor="#211D15", lw=2.0, alpha=0.75))
    # Metal tab U-window (-12.88..+12.88 mm, y = -19.12..-9.82 mm)
    ax.add_patch(Rectangle((-12.88, -19.12), 25.76, 9.30, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.5))
    # Two half-square notches at X = +-7.45 mm, y = -9.9..-7.8 mm
    for sign in (-1.0, +1.0):
        ax.add_patch(Rectangle((sign * 7.45 - 1.56, -9.9), 3.12, 2.1, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.2))
        # Ø2.8 mm notch alignment socket
        ax.add_patch(Circle((sign * 7.45, -8.80), 1.4, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
        # Ø3.2 mm M2 Heat-Set Insert Bore at X = +-10.25, Y = -7.75 mm
        ax.add_patch(Circle((sign * 10.25, -7.75), 1.6, facecolor="#2B5FAB", edgecolor="#F6EFE2", lw=1.4))
        # Ø4.0 mm M3 Heat-Set Insert Bore at X = +-10.00, Y = -15.10 mm (inside U-window!)
        ax.add_patch(Circle((sign * 10.00, -15.10), 2.4, facecolor="#E4402A", edgecolor="#211D15", lw=1.5))
        ax.add_patch(Circle((sign * 10.00, -15.10), 2.0, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))

    ax.text(0.0, 6.2, "100% FLAT & SEALED REAR FACE (Z = 0.0 mm)\nZero Hex-Nut Recesses · Prints Flat on Bed Without Bridges!", ha="center", va="center", fontsize=8.8, fontweight="bold", family="monospace", color="#211D15", bbox=dict(boxstyle="round,pad=0.3", facecolor="#F2B417", edgecolor="#211D15", lw=1.4))
    dim_arrow(ax, -10.25, -3.5, +10.25, -3.5, "20.5 mm · 2× M2 Insert Bores (Ø3.2×4.5mm, Tab Holes)", (0, 2.5), "#2B5FAB", fontsize=8.0)
    dim_arrow(ax, -10.00, -21.5, +10.00, -21.5, "20.0 mm · 2× M3 Insert Bores (Ø4.0×6.5mm in U-Window!)", (0, -3.2), "#E4402A", fontsize=8.1)
    dim_arrow(ax, -48.0, -28.2, +48.0, -28.2, "96.0 mm Structural Gusset Span (Zero Neck Weak Point)", (0, -2.5), "#211D15", fontsize=8.0)

    # --- Panel C: Heat-Set Insert Bore Cross-Sections & Why M5 Is Too Large ---
    ax = axes[1, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("C · Updated 100×22mm Board & Hole Coordinates (M3 vs M2 Specs)", fontsize=11.3, fontweight="bold", color="#211D15", pad=8)

    # Box 1: M3 Heat-Set Insert Spec (USED IN 7 PLACES)
    ax.add_patch(FancyBboxPatch((2, 32), 46, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#E4402A", lw=2.0))
    ax.text(25, 55.5, "[CASING & BRACKET] M3 INSERTS (7×)", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#E4402A", family="monospace")
    ax.text(
        4.0,
        43.5,
        "• Insert: M3 × 4mm or M3 × 5mm brass\n"
        "  (Voron/Ruthex/CNC Kitchen OD 4.5–5.0mm)\n"
        "• Melt Bore: Ø 4.0 mm × 6.5 mm deep\n"
        "• Lead-In:   Ø 4.8 mm × 0.6 mm (45°)\n"
        "• Boss OD:   Ø 9.2 mm (inner edge X=±51.9)\n"
        "• 4× Casing Ears: X=±56.5, Y=±9.0 (113×18mm)\n"
        "• 2× U-Window (X=±10.0), 1× USB Clamp Jaw",
        ha="left",
        va="center",
        fontsize=6.6,
        color="#211D15",
        family="monospace",
    )

    # Box 2: M2 Heat-Set Insert Spec (BOARD MOUNTING — 10× TOTAL)
    ax.add_patch(FancyBboxPatch((52, 32), 46, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#2B5FAB", lw=2.0))
    ax.text(75, 55.5, "[BOARD & TAB] M2 INSERTS (10× TOTAL)", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#2B5FAB", family="monospace")
    ax.text(
        54.0,
        43.5,
        "• Board Pocket: 101.2 × 23.2 mm\n"
        "  (Fits 100.0×22.0mm PCB + 0.6mm/side)\n"
        "• 4× Corner Board M2: X = ±48.0, Y = ±9.0\n"
        "  (96.0×18.0mm C-C, Ø 3.2×4.5mm M2 insert)\n"
        "• 4× Middle Board M2: X = ±26.1, Y = ±9.0\n"
        "  (52.2×18.0mm C-C, Ø 3.2×4.5mm M2 insert)\n"
        "• 2× Tab Top Bar: X = ±10.25 (Ø 3.2mm M2)",
        ha="left",
        va="center",
        fontsize=6.6,
        color="#211D15",
        family="monospace",
    )

    # Box 3: Clearance Verification Between Board Pocket (101.2 x 23.2 mm) & Cut-Down USB Holder
    ax.add_patch(FancyBboxPatch((2, 2), 96, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#211D15", lw=2.0))
    ax.text(50, 25.5, "[ZERO INTERFERENCE] 8× BOARD M2 INSERTS & CUT-DOWN USB HOLDER (Y ≤ -16.2mm)", ha="center", va="center", fontsize=7.9, fontweight="bold", color="#211D15", family="monospace")
    ax.text(
        4.0,
        13.0,
        "1. 8× M2 Heat-Set Insert Bores (Ø 3.2 × 4.5 mm) at X = ±48.0 & X = ±26.1, Y = ±9.0 mm secure the PCB directly.\n"
        "2. Mini-USB raised collar & pinch jaws start strictly at Y = -16.2 mm (1.4 mm below Front Visor's Y = -14.8 mm wall),\n"
        "   and the USB neck (Y = -16.2..-11.6 mm) is cut down to Z = 6.4 mm so it never interferes with the Front Visor!\n"
        "3. 4× Outer M3 Casing Bosses (X = ±56.5, Y = ±9.0 = 113.0 × 18.0 mm) clamp the Front Visor to the Back Cover.",
        ha="left",
        va="center",
        fontsize=6.6,
        color="#211D15",
        family="monospace",
    )

    # --- Panel D: Structural Z-Stack & M3 Mini-USB Clamp Cross-Section ---
    ax = axes[1, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-18, 18)
    ax.set_ylim(-2, 22)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("D · Mini-USB M3 Heat-Set Insert Clamp & 6.8mm Reinforced Base", fontsize=11.5, fontweight="bold", color="#211D15", pad=8)

    # Spine & collar base (z = 0..18.8)
    ax.add_patch(FancyBboxPatch((-15.5, 0.0), 31.0, 10.5, boxstyle="round,pad=0,rounding_size=2.5", facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.65))
    ax.add_patch(FancyBboxPatch((-10.0, 0.0), 20.0, 18.8, boxstyle="round,pad=0,rounding_size=2.8", facecolor="#2B5FAB", edgecolor="#211D15", lw=2.0, alpha=0.85))
    ax.add_patch(FancyBboxPatch((-15.0, 7.2), 30.0, 10.6, boxstyle="round,pad=0,rounding_size=2.2", facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.9))

    # Inner USB bay (13.0 x 9.0 mm at z = 7.4..16.4)
    ax.add_patch(Rectangle((-6.5, 7.4), 13.0, 9.0, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.8))
    # Front flex slit (1.8 mm at z = 15.4..18.8)
    ax.add_patch(Rectangle((-0.9, 15.4), 1.8, 3.6, facecolor="#EFE5D2", edgecolor="#E4402A", lw=1.4))

    # Left jaw: Ø3.4 mm M3 clearance + Ø6.4 mm head counterbore
    ax.add_patch(Rectangle((-15.0, 12.6 - 1.7), 14.1, 3.4, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))
    ax.add_patch(Rectangle((-15.0, 12.6 - 3.2), 2.5, 6.4, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))

    # Right jaw: Ø4.0 mm M3 heat-set insert bore + Ø4.8 mm chamfer
    ax.add_patch(Rectangle((0.9, 12.6 - 2.0), 14.1, 4.0, facecolor="#F2B417", edgecolor="#E4402A", lw=1.5))
    ax.plot([-16.5, 16.5], [12.6, 12.6], color="#E4402A", lw=1.8, ls="--")

    ax.text(-10.5, 12.6, "Ø3.4mm\nM3 Bolt", ha="center", va="center", fontsize=7.5, fontweight="bold", family="monospace", color="#211D15")
    ax.text(+8.2, 12.6, "Ø4.0mm M3\nInsert Bore", ha="center", va="center", fontsize=7.5, fontweight="bold", family="monospace", color="#211D15")
    dim_arrow(ax, -15.5, 3.2, +15.5, 3.2, "6.8 mm Base / 10.5 mm Spine (5× Stiffer than v1)", (0, 0), "#F2B417", fontsize=8.0)
    dim_arrow(ax, -15.0, 19.8, +15.0, 19.8, "30.0 mm Pinch Jaws (M3 Heat-Set Insert — No Hex Nut!)", (0, 0.8), "#E4402A", fontsize=8.0)

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    png_out = CAD_DIR / "back-mount-v2-dimensions.png"
    svg_out = CAD_DIR / "back-mount-v2-dimensions.svg"
    fig.savefig(png_out, dpi=180, facecolor=fig.get_facecolor())
    fig.savefig(svg_out, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved Back Cover v2 engineering dimensions -> {png_out} and {svg_out}")
    return render_out, svg_out, png_out


def render_front_visor_v2_sheets() -> tuple[Path, Path, Path]:
    """Render 4-panel 3D inspection sheet + 4-panel engineering drawing for Front Visor v2."""
    visor_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_front_visor_v2.stl")
    back_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_back_mount_v2.stl")
    pcb_parts = make_camera_pcb_meshes()

    # =========================================================================
    # 1. 4-Panel 3D Render Sheet of `horace_cam_front_visor_v2.stl`
    # =========================================================================
    fig = plt.figure(figsize=(16, 11.5), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · Front Visor v2 (85.0 mm Lens Baseline · 100×22 mm Board · 113×18 mm M3 Ears)",
        fontsize=15.5,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    # Panel 1: Front 3/4 View (Looking at the 85.0mm binocular lens turrets, sun-visor brow & 4x outer M3 counterbores)
    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    add_mesh_to_ax(ax1, visor_stl, "#E4402A")
    style_3d_ax(
        ax1,
        "1 · Front 3/4 View (85.0 mm Lens Baseline · Clean Faceplate)",
        "2× Ø16.6mm lens bores + 4× Outer M3 C'bores (X=±56.5, Y=±9.0) · NO PCB screw holes on front!",
        xlim=(-60, 60),
        ylim=(-20, 20),
        zlim=(0, 19),
        elev=42,
        azim=-58,
    )

    # Panel 2: Rear / Inside Cavity View (Flipped 180° so flat Z=0 mating face & internal pockets face up!)
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    visor_inside_up = visor_stl.copy()
    r_flip = trimesh.transformations.euler_matrix(np.radians(180.0), 0.0, 0.0, "sxyz")
    visor_inside_up.apply_transform(r_flip)
    visor_inside_up.apply_translation([0.0, 0.0, 16.8])
    add_mesh_to_ax(ax2, visor_inside_up, "#E4402A")
    style_3d_ax(
        ax2,
        "2 · Rear / Inside View (70×16.8×11.4 mm FFC Crevice & 8× Screw Pockets)",
        "12.8 mm clearance above PCB for 10×13mm ribbons + 8× blind Ø4.8mm M2 screw-head pockets",
        xlim=(-60, 60),
        ylim=(-20, 20),
        zlim=(0, 19),
        elev=46,
        azim=-56,
    )

    # Panel 3: Assembled Fit Check on Back Cover v2 + 100×22 mm Stereo Camera PCB
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    add_mesh_to_ax(ax3, transform_mesh(back_stl), "#2B5FAB")
    for m_pcb, c_pcb in pcb_parts:
        add_mesh_to_ax(ax3, transform_mesh(m_pcb), c_pcb)
    visor_assy = visor_stl.copy()
    visor_assy.apply_translation([0.0, 0.0, 9.8])
    add_mesh_to_ax(ax3, transform_mesh(visor_assy), "#E4402A", alpha=0.92)
    style_3d_ax(
        ax3,
        "3 · Assembled Fit Check (Visor v2 + 100×22 PCB + Back Cover v2)",
        "0.0000 mm³ interference · USB collar cut down to Y ≤ -16.2mm · 10×13mm ribbons protected",
        xlim=(-62, 62),
        ylim=(-26, 26),
        zlim=(-28, 18),
        elev=22,
        azim=124,
    )

    # Panel 4: Flat FDM Print Bed Orientation (Z = 0.0 on Build Plate)
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    gx = np.linspace(-65, 65, 14)
    gy = np.linspace(-25, 25, 6)
    for x in gx:
        ax4.plot([x, x], [gy[0], gy[-1]], [0, 0], color="#211D15", alpha=0.16, linewidth=0.8)
    for y in gy:
        ax4.plot([gx[0], gx[-1]], [y, y], [0, 0], color="#211D15", alpha=0.16, linewidth=0.8)

    add_mesh_to_ax(ax4, visor_stl, "#E4402A")
    style_3d_ax(
        ax4,
        "4 · Print Orientation: Flat on Z=0.0 (100% Support-Free FDM)",
        "122.2 × 29.6 × 16.8 mm · 31.38 cm³ (~38g PLA/PETG) · 45° vaulted internal ceilings",
        xlim=(-62, 62),
        ylim=(-22, 22),
        zlim=(0, 19),
        elev=36,
        azim=-48,
    )

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    render_out = CAD_DIR / "front-visor-v2-render.png"
    fig.savefig(render_out, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved Front Visor v2 3D render -> {render_out}")

    # =========================================================================
    # 2. 4-Panel Engineering Dimension Drawing for Front Visor v2 (SVG + PNG)
    # =========================================================================
    fig, axes = plt.subplots(2, 2, figsize=(16.5, 12.0), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · Front Visor v2 — 85.0 mm Lens Baseline & Fastening Hole Coordinates (mm)",
        fontsize=15.5,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    def dim_arrow(ax, x1, y1, x2, y2, text, text_offset=(0, 2.2), color="#E4402A", fontsize=8.4):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="<->", color=color, lw=1.8, shrinkA=0, shrinkB=0),
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
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#F6EFE2", edgecolor=color, lw=1.2),
        )

    # --- Panel A: Front View (85.0 mm Lens Turrets, Top Sun-Visor Brow & ONLY 4x Outer M3 Counterbores) ---
    ax = axes[0, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-69, 69)
    ax.set_ylim(-25, 25)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("A · Front View — Clean Faceplate (85.0 mm Lenses + 4× Outer M3 Only)", fontsize=11.1, fontweight="bold", color="#211D15", pad=8)

    # Main visor body (121.0 x 29.6 mm, 122.2 mm across Ø9.2 mm corner ears)
    ax.add_patch(FancyBboxPatch((-60.5, -14.8), 121.0, 29.6, boxstyle="round,pad=0,rounding_size=4.8", facecolor="#E4402A", edgecolor="#211D15", lw=2.0, alpha=0.88))
    # Top sun-visor brow (Y = +10.6..+14.8 mm)
    ax.add_patch(FancyBboxPatch((-60.0, 10.6), 120.0, 4.2, boxstyle="round,pad=0,rounding_size=1.8", facecolor="#B82D1B", edgecolor="#211D15", lw=1.5, alpha=0.9))

    # 2x Binocular Lens Turrets at X = +-42.5, Y = 0.0 (Ø22.4 mm turret OD, Ø18.2 mm chamfer, Ø16.6 mm through-bore)
    for lx in (-42.5, +42.5):
        ax.add_patch(Circle((lx, 0.0), 11.2, facecolor="#E4402A", edgecolor="#211D15", lw=1.8))
        ax.add_patch(Circle((lx, 0.0), 9.1, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
        ax.add_patch(Circle((lx, 0.0), 8.3, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.6))
        ax.plot([lx, lx], [-13.5, 13.5], color="#211D15", lw=0.9, ls="-.")
        ax.plot([lx - 12.5, lx + 12.5], [0.0, 0.0], color="#211D15", lw=0.9, ls="-.")

    # 4x Outer M3 Fastening Holes + Ø6.5 mm Counterbores (X = +-56.5, Y = +-9.0)
    for ex in (-56.5, +56.5):
        for ey in (-9.0, +9.0):
            ax.add_patch(Circle((ex, ey), 4.6, facecolor="#E4402A", edgecolor="#211D15", lw=1.4))
            ax.add_patch(Circle((ex, ey), 3.25, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
            ax.add_patch(Circle((ex, ey), 1.7, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))

    dim_arrow(ax, -56.5, 17.5, +56.5, 17.5, "113.0 × 18.0 mm · 4× M3 Casing Bolts (Ø3.4mm + Ø6.5mm C'Bore)", (0, 3.0), "#E4402A", fontsize=7.9)
    dim_arrow(ax, -42.5, 11.5, +42.5, 11.5, "85.0 mm Lens Center-to-Center (X = ±42.5 mm, Y = 0.0 mm)", (0, 2.5), "#211D15", fontsize=8.0)
    ax.text(0.0, -18.8, "NO PCB Screw Through-Holes on Front Faceplate (8× Blind Screw-Head Pockets Underneath)", ha="center", va="center", fontsize=7.8, fontweight="bold", family="monospace", color="#211D15", bbox=dict(boxstyle="round,pad=0.25", facecolor="#F6EFE2", edgecolor="#2B5FAB", lw=1.2))
    dim_arrow(ax, 62.5, -14.8, 62.5, +14.8, "29.6 mm\nHeight", (3.8, 0), "#211D15", fontsize=7.6)

    # --- Panel B: Rear / Inside View with Enlarged 70×16.8mm FFC Crevice & 8× Blind Screw Pockets ---
    ax = axes[0, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-69, 69)
    ax.set_ylim(-25, 25)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("B · Rear / Inside View — 70×16.8 mm FFC Crevice & 8× Blind Screw Pockets", fontsize=11.0, fontweight="bold", color="#211D15", pad=8)

    # Visor outer footprint
    ax.add_patch(FancyBboxPatch((-60.5, -14.8), 121.0, 29.6, boxstyle="round,pad=0,rounding_size=4.8", facecolor="#E4402A", edgecolor="#211D15", lw=2.0, alpha=0.55))
    # 100 x 22 mm PCB dashed reference outline
    ax.add_patch(Rectangle((-50.0, -11.0), 100.0, 22.0, fill=False, edgecolor="#211D15", lw=1.8, ls="--"))
    # Enlarged Central FFC ribbon vaulted chamber (70.0 x 16.8 mm, X = -35..+35, Y = -8.4..+8.4)
    ax.add_patch(FancyBboxPatch((-35.0, -8.4), 70.0, 16.8, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#EFE5D2", edgecolor="#211D15", lw=1.6))
    # Bottom Mini-USB arch (13.8 x 8.8 mm)
    ax.add_patch(FancyBboxPatch((-6.9, -14.8), 13.8, 7.6, boxstyle="round,pad=0,rounding_size=1.4", facecolor="#EFE5D2", edgecolor="#211D15", lw=1.5))

    # 2x Square 15.2 x 15.2 mm pockets (X = +-34.9..+-50.1, Y = -7.6..+7.6) around 14.0 x 14.0 mm M12 lens bases
    for lx in (-42.5, +42.5):
        ax.add_patch(FancyBboxPatch((lx - 7.6, -7.6), 15.2, 15.2, boxstyle="round,pad=0,rounding_size=1.0", facecolor="#F2B417", edgecolor="#211D15", lw=1.5, alpha=0.75))
        ax.add_patch(Rectangle((lx - 7.0, -7.0), 14.0, 14.0, fill=False, edgecolor="#211D15", lw=1.3, ls=":"))
        ax.add_patch(Circle((lx, 0.0), 8.3, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.5))

    # 8x Blind Internal M2 Screw-Head Clearance Pockets (X = +-48.0 & +-26.1, Y = +-9.0, Ø4.8 mm x 2.8 mm deep)
    for px in (-48.0, -26.1, +26.1, +48.0):
        for py in (-9.0, +9.0):
            ax.add_patch(Circle((px, py), 2.4, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.2, alpha=0.85))

    # 4x M3 Through-Holes
    for ex in (-56.5, +56.5):
        for ey in (-9.0, +9.0):
            ax.add_patch(Circle((ex, ey), 1.7, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))

    dim_arrow(ax, -50.0, 15.5, +50.0, 15.5, "100.0 × 22.0 mm PCB Outline (8× Blind Ø4.8mm Screw-Head Pockets)", (0, 2.8), "#211D15", fontsize=7.8)
    dim_arrow(ax, -35.0, 0.0, +35.0, 0.0, "70.0 × 16.8 mm FFC Crevice (12.8mm Height Above PCB)", (0, 2.2), "#2B5FAB", fontsize=7.7)
    dim_arrow(ax, -50.1, -17.0, -34.9, -17.0, "15.2×15.2mm Base Pocket", (0, -3.0), "#E4402A", fontsize=7.6)
    dim_arrow(ax, -26.1, -11.5, +26.1, -11.5, "52.2 × 18.0 mm · 4× Middle Screw Pockets", (0, -2.6), "#2B5FAB", fontsize=7.7)

    # --- Panel C: Longitudinal Cross-Section Through Lenses (Y=0) & 10mm High FFC Ribbons ---
    ax = axes[1, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-66, 66)
    ax.set_ylim(-3, 31)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("C · Z-Stack Cross-Section (12.8 mm FFC Ribbon Clearance Above PCB)", fontsize=11.2, fontweight="bold", color="#211D15", pad=8)

    # Back Cover v2 (Z = 0..9.8 mm, width = 122.2 mm)
    ax.add_patch(Rectangle((-61.1, 0.0), 122.2, 6.8, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    ax.add_patch(Rectangle((-61.1, 6.8), 10.5, 3.0, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    ax.add_patch(Rectangle((50.6, 6.8), 10.5, 3.0, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    # SMD pocket (Z = 5.4..6.8 mm)
    ax.add_patch(Rectangle((-49.0, 5.4), 98.0, 1.4, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.0, ls="--"))
    # 100 mm PCB (Z = 6.8..8.4 mm)
    ax.add_patch(Rectangle((-50.0, 6.8), 100.0, 1.6, facecolor="#1E242B", edgecolor="#211D15", lw=1.5))

    # Front Visor v2 sitting on Z = 9.8 mm (Z = 9.8..24.3 mm plate, Z = 9.8..25.3 mm turrets)
    ax.add_patch(Rectangle((-61.1, 9.8), 122.2, 14.5, facecolor="#E4402A", edgecolor="#211D15", lw=1.8, alpha=0.85))
    for lx in (-42.5, +42.5):
        ax.add_patch(Rectangle((lx - 11.2, 9.8), 22.4, 15.5, facecolor="#E4402A", edgecolor="#211D15", lw=1.8, alpha=0.9))
        # 15.2 mm base pocket + Ø16.6 mm lens bore
        ax.add_patch(Rectangle((lx - 8.3, 9.7), 16.6, 15.8, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.4))
        # M12 lens base (14x14x6mm, Z = 8.4..14.4 mm) + barrel + cap (Z = 8.4..27.4 mm)
        ax.add_patch(Rectangle((lx - 7.0, 8.4), 14.0, 6.0, facecolor="#3A3F47", edgecolor="#211D15", lw=1.4))
        ax.add_patch(Rectangle((lx - 7.0, 14.4), 14.0, 13.0, facecolor="#6C7582", edgecolor="#211D15", lw=1.4))

    # Enlarged Central FFC ribbon vaulted chamber in Front Visor (Z = 9.8..21.2 mm -> 12.8 mm above PCB Z=8.4!)
    ax.add_patch(Polygon([(-35.0, 8.4), (35.0, 8.4), (35.0, 18.6), (32.4, 21.2), (-32.4, 21.2), (-35.0, 18.6)], closed=True, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.3, ls="--"))
    # Two 10.0 mm tall bowed FFC ribbons (Z = 8.4..18.4 mm) inside the Z = 8.4..21.2 mm chamber!
    for rx in (-28.0, +28.0):
        ax.add_patch(Rectangle((rx - 5.0, 8.4), 10.0, 10.0, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.2, alpha=0.85))
    ax.text(0.0, 14.8, "12.8 mm FFC Chamber Height\n(Clears 10×13mm Bowed Ribbons!)", ha="center", va="center", fontsize=7.5, fontweight="bold", family="monospace", color="#211D15")

    # Outer M3 Heat-Set Insert (in Back Cover Z = 3.3..9.8 mm) + M3 Bolt through Front Visor (X = +-56.5 mm)
    for ex in (-56.5, +56.5):
        ax.add_patch(Rectangle((ex - 2.0, 3.3), 4.0, 6.5, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
        ax.add_patch(Rectangle((ex - 1.7, 9.8), 3.4, 5.5, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.1))
        ax.add_patch(Rectangle((ex - 3.25, 15.3), 6.5, 9.0, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.1))

    dim_arrow(ax, -42.5, 28.0, +42.5, 28.0, "85.0 mm Lens Baseline (X = ±42.5 mm)", (0, 1.8), "#E4402A", fontsize=8.2)
    dim_arrow(ax, -56.5, -1.2, +56.5, -1.2, "113.0 mm Outer M3 Heat-Set Insert Fastening", (0, -1.2), "#2B5FAB", fontsize=8.0)

    # --- Panel D: Front Visor v2 Feature & Clearance Table ---
    ax = axes[1, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("D · Front Visor v2 (`horace_cam_front_visor_v2.stl`) Specification Summary", fontsize=11.2, fontweight="bold", color="#211D15", pad=8)

    ax.add_patch(FancyBboxPatch((2, 32), 46, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#E4402A", lw=2.0))
    ax.text(25, 55.5, "[OPTICS & FFC CREVICE] 85.0 mm LENSES", ha="center", va="center", fontsize=8.1, fontweight="bold", color="#E4402A", family="monospace")
    ax.text(
        4.0,
        43.5,
        "• Lens Centers: X = ±42.5 mm, Y = 0.0 mm\n"
        "  (85.0 mm C-to-C; Ø 16.6 mm through-bore)\n"
        "• FFC Ribbon Crevice: 70.0 × 16.8 mm wide\n"
        "  (Clears 13.0 mm wide ribbons + 1.9mm/side)\n"
        "• Crevice Height: 12.8 mm above PCB face\n"
        "  (Clears 10.0 mm tall ribbon bow + 2.8mm gap)",
        ha="left",
        va="center",
        fontsize=6.6,
        color="#211D15",
        family="monospace",
    )

    ax.add_patch(FancyBboxPatch((52, 32), 46, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#2B5FAB", lw=2.0))
    ax.text(75, 55.5, "[FASTENING] CLEAN FRONT FACEPLATE", ha="center", va="center", fontsize=8.1, fontweight="bold", color="#2B5FAB", family="monospace")
    ax.text(
        54.0,
        43.5,
        "• Outer Footprint: 122.2 × 29.6 × 16.8 mm\n"
        "• 4× Outer M3 Through-Holes: X=±56.5, Y=±9.0\n"
        "  (113×18mm C-C, Ø 3.4mm + Ø 6.5mm C'Bore)\n"
        "• 0× PCB Through-Holes on Front Faceplate!\n"
        "• 8× Blind Underside M2 Head Pockets (Ø4.8×2.8)\n"
        "  at X=±48.0 & X=±26.1, Y=±9.0 (4.2mm head gap)",
        ha="left",
        va="center",
        fontsize=6.6,
        color="#211D15",
        family="monospace",
    )

    ax.add_patch(FancyBboxPatch((2, 2), 96, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#211D15", lw=2.0))
    ax.text(50, 25.5, "[4-POINT FIT VERIFICATION] 0.0000 mm³ BOOLEAN INTERFERENCE", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#211D15", family="monospace")
    ax.text(
        4.0,
        13.0,
        "1. Back Cover has 8× M2 insert bores (Ø 3.2×4.5 mm) at X = ±48.0 (corners) & X = ±26.1 (3rd holes from left/right).\n"
        "2. Mini-USB holder top is cut down to Y ≤ -16.2 mm (1.4 mm below Front Visor's Y = -14.8 mm bottom wall).\n"
        "3. Enlarged 70.0 × 16.8 × 11.4 mm FFC crevice gives 12.8 mm height above PCB for 10×13 mm bowed ribbons.\n"
        "4. Front Visor has NO PCB screw holes through the faceplate (8× blind Ø 4.8 mm head pockets underneath).",
        ha="left",
        va="center",
        fontsize=6.6,
        color="#211D15",
        family="monospace",
    )

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    png_out = CAD_DIR / "front-visor-v2-dimensions.png"
    svg_out = CAD_DIR / "front-visor-v2-dimensions.svg"
    fig.savefig(png_out, dpi=180, facecolor=fig.get_facecolor())
    fig.savefig(svg_out, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved Front Visor v2 engineering dimensions -> {png_out} and {svg_out}")
    return render_out, svg_out, png_out


if __name__ == "__main__":
    render_back_mount_v2_sheets()
    render_front_visor_v2_sheets()
    render_3d_preview_sheet()
    render_engineering_dimensions()


