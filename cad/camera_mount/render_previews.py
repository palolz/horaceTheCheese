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
    """Create illustrative 3D meshes for the 95x20x1.6mm stereo camera PCB, lenses, and Mini-USB."""
    import manifold3d as mf
    from generate_camera_mount import CameraMountParams, cylinder_z, manifold_to_trimesh, rounded_rect_prism

    p = CameraMountParams()
    # Black PCB substrate (z = 5.0 to 6.6 mm in assembly coords)
    pcb = rounded_rect_prism(p.pcb_width, p.pcb_height, p.pcb_thickness, 0.8, (0.0, 0.0), z0=5.0)
    for hx in (-p.hole_outer_x, +p.hole_outer_x, -p.hole_inner_inner_x, +p.hole_inner_inner_x, -p.hole_inner_outer_x, +p.hole_inner_outer_x):
        for hy in (-p.hole_y, +p.hole_y):
            pcb = pcb - cylinder_z(2.0, 5.0, hx, hy, z0=4.0)

    # Two 14x14mm M12 lens bases + Ø14mm barrels (z = 6.6 to 22.5 mm)
    lenses = None
    caps = None
    for lx in (-40.0, +40.0):
        base = rounded_rect_prism(14.0, 14.0, 6.0, 1.2, (lx, 0.0), z0=6.6)
        barrel = cylinder_z(14.0, 14.5, lx, 0.0, z0=6.6, segments=48)
        cap = cylinder_z(15.0, 4.2, lx, 0.0, z0=20.2, segments=48) - cylinder_z(12.6, 3.0, lx, 0.0, z0=21.6, segments=48)
        u = base + barrel
        lenses = u if lenses is None else (lenses + u)
        caps = cap if caps is None else (caps + cap)

    # Gold Mini-USB receptacle (x = -3.4..+3.4, y = -10.2..-3.0, z = 6.6..10.5)
    usb_rec = rounded_rect_prism(6.8, 7.2, 3.9, 0.6, (0.0, -6.6), z0=6.6)

    # Two blue/white FFC ribbon arches (x = +-29.0, y = -5..+5, z = 6.6..11.2)
    ribbons = None
    for rx in (-29.5, +29.5):
        rib = rounded_rect_prism(8.0, 10.0, 4.2, 1.2, (rx, 0.0), z0=6.6)
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

    # Vertical upturned tab (44.88 mm wide, y = -21.0 to -1.3, z = 0.0 to 2.0 mm)
    tab = rounded_rect_prism(44.88, 19.7, 2.0, 1.5, (0.0, -11.15), z0=0.0)
    # Central U-window cutout (25.75 mm wide x 8.5 mm tall)
    window = rounded_rect_prism(25.75, 9.5, 4.0, 1.2, (0.0, -10.5), z0=-1.0)
    # Two half-square notches on inside edge of top crossbar (X = +-7.45 mm, width = 3.12 mm)
    notch_l = rounded_rect_prism(3.12, 3.2, 4.0, 0.5, (-7.45, -5.2), z0=-1.0)
    notch_r = rounded_rect_prism(3.12, 3.2, 4.0, 0.5, (+7.45, -5.2), z0=-1.0)
    # Two M2 holes at X = +-10.50 mm, Y = -3.35 mm
    hole_l = cylinder_z(2.3, 5.0, -10.5, -3.35, z0=-1.0)
    hole_r = cylinder_z(2.3, 5.0, +10.5, -3.35, z0=-1.0)
    # Horizontal deck stub extending rearward (z = -28.0 to 2.0 mm, y = -23.0 to -21.0 mm)
    deck = rounded_rect_prism(68.0, 2.0, 30.0, 1.5, (0.0, -22.0), z0=-28.0)
    deck_cut = rounded_rect_prism(26.9, 4.0, 20.0, 1.5, (0.0, -22.0), z0=-18.0)

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
    ASSETS_CAD_DIR.mkdir(parents=True, exist_ok=True)
    back_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_back_mount.stl")
    visor_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_front_visor.stl")
    shim_stl = trimesh.load_mesh(CAD_DIR / "horace_cam_usb_shim.stl")
    pcb_parts = make_camera_pcb_meshes()
    bracket_mesh = make_upturned_bracket_mesh()

    fig = plt.figure(figsize=(16, 11.5), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · Stage 3 Binocular Stereo Camera Mount & Enclosure (3D Printable CAD)",
        fontsize=16,
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
    # Visor sits at z = 6.6 mm in assembly
    visor_assembled = visor_stl.copy()
    visor_assembled.apply_translation([0.0, 0.0, 6.6])
    add_mesh_to_ax(ax1, transform_mesh(visor_assembled), "#E4402A")
    # Shim inside lower USB bay
    shim_assembled = shim_stl.copy()
    shim_assembled.apply_Transform = None
    style_3d_ax(
        ax1,
        "1 · Assembled on WAVE ROVER 90° Front Bracket",
        "Front visor (#E4402A) + Rear mount (#2B5FAB) + 80.0 mm stereo baseline",
        xlim=(-56, 56),
        ylim=(-28, 28),
        zlim=(-30, 18),
        elev=20,
        azim=-58,
    )

    # --- Panel 2: Rear 3/4 View Showing Anti-Rotation Keys & Bracket Seat ---
    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    add_mesh_to_ax(ax2, transform_mesh(back_stl), "#2B5FAB")
    bracket_offset = bracket_mesh.copy()
    bracket_offset.apply_translation([0.0, 0.0, -18.0])
    add_mesh_to_ax(ax2, transform_mesh(bracket_offset), "#33373D", alpha=0.88)
    style_3d_ax(
        ax2,
        "2 · Rear Anti-Rotation Keys & 90° Tab Interface",
        "2x notch keys (X=±7.45mm) + 20–21mm M2 slots + M3/zip-tie Mini-USB clamp",
        xlim=(-56, 56),
        ylim=(-36, 22),
        zlim=(-30, 18),
        elev=22,
        azim=132,
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
    # Rotate shim so its Z-axis aligns with Y_up
    r_shim = trimesh.transformations.euler_matrix(np.radians(90.0), 0.0, 0.0, "sxyz")
    shim_exp.apply_transform(r_shim)
    shim_exp.apply_translation([0.0, -42.0, 6.0])
    add_mesh_to_ax(ax3, transform_mesh(shim_exp), "#F2B417")

    style_3d_ax(
        ax3,
        "3 · Exploded Assembly (5 Layers)",
        "90° Tab -> Back Mount -> 95x20mm Stereo PCB + USB Shim -> Front Visor",
        xlim=(-58, 58),
        ylim=(-42, 58),
        zlim=(-46, 20),
        elev=21,
        azim=-52,
    )

    # --- Panel 4: Support-Free Print Bed Layout (Z = 0 Flat on Build Plate) ---
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    # Draw build plate grid
    gx = np.linspace(-65, 65, 14)
    gy = np.linspace(-55, 55, 12)
    for x in gx:
        ax4.plot([x, x], [gy[0], gy[-1]], [0, 0], color="#211D15", alpha=0.15, linewidth=0.7)
    for y in gy:
        ax4.plot([gx[0], gx[-1]], [y, y], [0, 0], color="#211D15", alpha=0.15, linewidth=0.7)

    # Place back_stl flat on print bed (its model Z is already print-height Z>=0!)
    b_bed = back_stl.copy()
    b_bed.apply_translation([0.0, 22.0, 0.0])
    add_mesh_to_ax(ax4, b_bed, "#2B5FAB")

    v_bed = visor_stl.copy()
    v_bed.apply_translation([0.0, -20.0, 0.0])
    add_mesh_to_ax(ax4, v_bed, "#E4402A")

    s_bed = shim_stl.copy()
    s_bed.apply_translation([42.0, 2.0, 0.0])
    add_mesh_to_ax(ax4, s_bed, "#F2B417")

    style_3d_ax(
        ax4,
        "4 · Print Bed Orientation (100% Support-Free FDM)",
        "All 3 STLs print flat on Z=0 · ~27.6 cm³ total (~33g PLA/PETG, ~48 min)",
        xlim=(-65, 65),
        ylim=(-52, 52),
        zlim=(0, 32),
        elev=34,
        azim=-45,
    )

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    out_path = ASSETS_CAD_DIR / "camera-mount-render.png"
    fig.savefig(out_path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[OK] Saved 3D preview sheet -> {out_path}")
    return out_path


def render_engineering_dimensions() -> tuple[Path, Path]:
    """Generate engineering dimension sheet in both SVG and PNG formats."""
    ASSETS_CAD_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(16, 11.5), dpi=180, facecolor="#F6EFE2")
    fig.suptitle(
        "horaceTheCheese · Stereo Camera & Expansion Bracket Engineering Dimensions (mm)",
        fontsize=16,
        fontweight="bold",
        color="#211D15",
        y=0.975,
    )

    def dim_arrow(ax, x1, y1, x2, y2, text, text_offset=(0, 2.2), color="#E4402A", fontsize=9.0):
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

    # --- Panel A: Stereo Camera PCB Front Orthographic (Measured from 5x5mm Grid) ---
    ax = axes[0, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-60, 60)
    ax.set_ylim(-24, 24)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("A · Stereo Camera Module (Measured on 5×5 mm Grid)", fontsize=12, fontweight="bold", color="#211D15", pad=10)

    # Outer enclosure outline (101 x 26 mm)
    ax.add_patch(FancyBboxPatch((-50.5, -13.0), 101.0, 26.0, boxstyle="round,pad=0,rounding_size=4.2", fill=False, edgecolor="#2B5FAB", lw=2.2, ls="--", label="Enclosure Outer (101×26 mm)"))
    # PCB (95.0 x 20.0 mm)
    ax.add_patch(Rectangle((-47.5, -10.0), 95.0, 20.0, facecolor="#211D15", edgecolor="#211D15", lw=2.0))
    # 14x14 mm lens bases + Ø14 mm barrels + Ø15 mm caps at X = +-40.0 mm
    for lx in (-40.0, +40.0):
        ax.add_patch(Rectangle((lx - 7.0, -7.0), 14.0, 14.0, facecolor="#3A3F47", edgecolor="#F6EFE2", lw=1.2))
        ax.add_patch(Circle((lx, 0.0), 7.5, facecolor="#9BA5B4", edgecolor="#211D15", lw=1.5, alpha=0.85))
        ax.add_patch(Circle((lx, 0.0), 8.3, fill=False, edgecolor="#E4402A", lw=1.6, ls=":"))
        ax.plot([lx, lx], [-11, 16], color="#E4402A", lw=1.0, ls="-.")

    # FFC Ribbons
    for rx in (-29.5, +29.5):
        ax.add_patch(Rectangle((rx - 4.0, -5.5), 8.0, 11.0, facecolor="#2B5FAB", edgecolor="#F6EFE2", lw=1.0))

    # Mini-USB at X = 0, Y = -10.0.. -2.8 mm
    ax.add_patch(Rectangle((-3.4, -10.2), 6.8, 7.2, facecolor="#F2B417", edgecolor="#211D15", lw=1.5))

    # 12 M2 mounting holes
    for hx in (-46.0, -26.1, -22.1, +22.1, +26.1, +46.0):
        for hy in (-8.5, +8.5):
            ax.add_patch(Circle((hx, hy), 1.6, facecolor="#F2B417", edgecolor="#211D15", lw=0.8))
            ax.add_patch(Circle((hx, hy), 0.9, facecolor="#EFE5D2", edgecolor="#211D15", lw=0.6))

    dim_arrow(ax, -40.0, 14.2, +40.0, 14.2, "80.0 mm Lens Baseline (C-to-C)", (0, 2.8), "#E4402A")
    dim_arrow(ax, -46.0, -14.8, +46.0, -14.8, "92.0 mm Outer M2 Holes", (0, -2.8), "#2B5FAB")
    dim_arrow(ax, -47.5, -20.2, +47.5, -20.2, "95.0 mm PCB Width (101.0 mm Shell)", (0, -2.6), "#211D15")
    dim_arrow(ax, 52.5, -10.0, 52.5, +10.0, "20.0 mm\nPCB", (5.2, 0), "#211D15", fontsize=8.0)

    # --- Panel B: WAVE ROVER 90° Upturned Front Bracket & Anti-Rotation Keys ---
    ax = axes[0, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-32, 32)
    ax.set_ylim(-24, 11.5)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("B · WAVE ROVER 90° Upturned Tab (Factory DXF + P1044916)", fontsize=12, fontweight="bold", color="#211D15", pad=10)

    # Upturned tab outer boundary (-22.44 to +22.44 mm, height 19.63 mm from y=-20.8 to -1.2)
    ax.add_patch(Rectangle((-22.44, -20.83), 44.88, 19.63, facecolor="#2C3036", edgecolor="#211D15", lw=2.0))
    # Central U-window (-12.88 to +12.88 mm, y = -15.0 to -5.42 mm)
    ax.add_patch(Rectangle((-12.88, -14.8), 25.76, 9.38, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.6))
    # Two half-square notches on inside of top crossbar (X = +-5.89 to +-9.01 mm, y = -5.42 to -3.4 mm)
    for sign in (-1.0, +1.0):
        x0 = sign * 7.45 - 1.56
        ax.add_patch(Rectangle((x0, -5.5), 3.12, 2.2, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.4))
        # Anti-rotation key inside the notch
        ax.add_patch(Rectangle((sign * 7.45 - 1.35, -5.4), 2.70, 2.0, facecolor="#F2B417", edgecolor="#E4402A", lw=1.6))
        # M2 mounting hole at X = +-10.50 mm (DXF) / +-10.0 mm (grid) -> oblong slot
        ax.add_patch(FancyBboxPatch((sign * 10.25 - 1.75, -3.35 - 1.2), 3.5, 2.4, boxstyle="round,pad=0,rounding_size=1.1", facecolor="#2B5FAB", edgecolor="#F6EFE2", lw=1.2))

    dim_arrow(ax, -22.44, 5.2, +22.44, 5.2, "44.88 mm Tab Width (2.00 mm Thick)", (0, 2.2), "#211D15")
    dim_arrow(ax, -10.25, -0.2, +10.25, -0.2, "20.0–21.0 mm M2 Slots", (0, 2.1), "#2B5FAB")
    dim_arrow(ax, -7.45, -8.2, +7.45, -8.2, "14.9 mm Anti-Rot Keys (2.7×3.0 mm)", (0, -2.2), "#E4402A")
    dim_arrow(ax, -12.88, -17.5, +12.88, -17.5, "25.75 mm Central U-Window", (0, -2.2), "#211D15")
    dim_arrow(ax, 25.5, -20.83, 25.5, -1.2, "19.63 mm\nTab Ht", (4.2, 0), "#211D15", fontsize=8.0)

    # --- Panel C: Side Profile & Lens Protrusion Cross-Section (P1044928) ---
    ax = axes[1, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-6, 30)
    ax.set_ylim(-32, 18)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("C · Side Cross-Section (Z-Stack, Lens Height & Deck Clearance)", fontsize=12, fontweight="bold", color="#211D15", pad=10)

    # Rear shell (z = 0 to 8.2, y = -13 to +13) + lower USB collar (y = -29 to -13, z = 0 to 17.8)
    ax.add_patch(Rectangle((0.0, -13.0), 5.0, 26.0, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    ax.add_patch(Rectangle((0.0, -29.0), 17.8, 16.0, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.65))
    # Upturned 2.0 mm metal tab seated in z = 0..2.1 mm, y = -21..-1.2 mm + horizontal deck at y = -23..-21 mm
    ax.add_patch(Rectangle((0.0, -21.0), 2.0, 19.8, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))
    ax.add_patch(Rectangle((-5.0, -23.0), 7.0, 2.0, facecolor="#2C3036", edgecolor="#211D15", lw=1.8))
    # PCB (z = 5.0 to 6.6 mm, y = -10 to +10 mm)
    ax.add_patch(Rectangle((5.0, -10.0), 1.6, 20.0, facecolor="#1E242B", edgecolor="#211D15", lw=1.5))
    # Lens base + barrel + cap (z = 6.6 to 25.6 mm, y = -7 to +7 mm)
    ax.add_patch(Rectangle((6.6, -7.0), 15.5, 14.0, facecolor="#3A3F47", edgecolor="#211D15", lw=1.5))
    ax.add_patch(Rectangle((22.1, -7.5), 3.5, 15.0, facecolor="#9BA5B4", edgecolor="#211D15", lw=1.5))
    # Front visor + sun brow (z = 6.6 to 21.1 mm)
    ax.add_patch(Polygon([(6.6, 10.0), (21.1, 10.0), (21.1, 13.0), (6.6, 13.0)], closed=True, facecolor="#E4402A", edgecolor="#211D15", lw=1.6))

    dim_arrow(ax, 6.6, 15.0, 25.6, 15.0, "19.0 mm Lens + Cap", (0, 1.8), "#E4402A", fontsize=8.5)
    dim_arrow(ax, 0.0, -30.8, 17.8, -30.8, "17.8 mm Collar Depth", (0, 1.8), "#2B5FAB", fontsize=8.5)
    ax.text(14.5, -21.5, "Mini-USB drops in front\nof 2.0mm tab (Z=+5.6..14.6)", fontsize=8.3, family="monospace", color="#211D15", bbox=dict(boxstyle="round,pad=0.25", facecolor="#F2B417", edgecolor="#211D15"))

    # --- Panel D: Mini-USB Strain-Relief Clamp & Parametric Shim Detail ---
    ax = axes[1, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-18, 18)
    ax.set_ylim(-2, 22)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("D · Mini-USB Plug Holder, M3 Pinch Clamp & Parametric Shim", fontsize=12, fontweight="bold", color="#211D15", pad=10)

    # Outer collar + M3 ears (-13.5..+13.5, z = 0..17.8)
    ax.add_patch(FancyBboxPatch((-9.5, 0.0), 19.0, 17.8, boxstyle="round,pad=0,rounding_size=2.5", facecolor="#2B5FAB", edgecolor="#211D15", lw=2.0, alpha=0.85))
    ax.add_patch(FancyBboxPatch((-13.5, 5.5), 27.0, 11.0, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    # Inner USB bay (13.0 x 9.0 mm at z = 5.6..14.6)
    ax.add_patch(Rectangle((-6.5, 5.6), 13.0, 9.0, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.8))
    # Parametric USB shim inside bay (12.65 x 8.7 mm outer, 10.2 x 7.0 mm inner plug pocket)
    ax.add_patch(Rectangle((-6.2, 5.75), 12.4, 8.7, facecolor="#F2B417", edgecolor="#211D15", lw=1.6))
    ax.add_patch(Rectangle((-5.1, 6.6), 10.2, 7.0, facecolor="#3A3F47", edgecolor="#211D15", lw=1.4))
    # Front flex slit (1.8 mm)
    ax.add_patch(Rectangle((-0.9, 13.5), 1.8, 4.5, facecolor="#EFE5D2", edgecolor="#E4402A", lw=1.2))
    # M3 bolt axis at z = 11.0
    ax.plot([-15.5, 15.5], [11.0, 11.0], color="#E4402A", lw=2.0, ls="--")
    ax.text(0.0, 10.1, "10.2 × 7.0 mm\nMini-USB Plug\n(Parametric Shim)", ha="center", va="center", fontsize=8.0, fontweight="bold", color="#F6EFE2", family="monospace")

    dim_arrow(ax, -6.5, 3.2, +6.5, 3.2, "13.0 mm Max Bay Width", (0, -1.6), "#211D15", fontsize=8.5)
    dim_arrow(ax, -13.5, 19.2, +13.5, 19.2, "27.0 mm M3 Pinch-Clamp Ears + 4.2mm Zip-Tie Slot", (0, 1.4), "#E4402A", fontsize=8.2)

    plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.95])
    png_path = ASSETS_CAD_DIR / "camera-mount-dimensions.png"
    svg_path = ASSETS_CAD_DIR / "camera-mount-dimensions.svg"
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
        "1 · Front / Inside View (Heat-Set Insert Bosses & Locating Pins)",
        "4× Outer M3 (Ø4.0mm) + 4× PCB M2 (Ø3.2mm) + 4× Ø1.85mm Pins + Gusset Ribs",
        xlim=(-52, 52),
        ylim=(-26, 18),
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
        xlim=(-52, 52),
        ylim=(-22, 22),
        zlim=(0, 22),
        elev=48,
        azim=-58,
    )

    # Panel 3: Close-up of Structural Gusset Wings & M3 Heat-Set Mini-USB Clamp Jaws
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    add_mesh_to_ax(ax3, back_stl, "#E4402A")
    style_3d_ax(
        ax3,
        "3 · Structural Gusset Wings & M3 Heat-Set Mini-USB Clamp",
        "Sweeping triangular gussets + raised ribs + M3 insert jaw (Ø4.0mm) vs Ø3.4mm bolt jaw",
        xlim=(-46, 46),
        ylim=(-27, 12),
        zlim=(0, 20),
        elev=28,
        azim=-40,
    )

    # Panel 4: Flat FDM Print Bed Orientation (Z = 0.0 on Build Plate)
    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    gx = np.linspace(-60, 60, 13)
    gy = np.linspace(-30, 30, 7)
    for x in gx:
        ax4.plot([x, x], [gy[0], gy[-1]], [0, 0], color="#211D15", alpha=0.16, linewidth=0.8)
    for y in gy:
        ax4.plot([gx[0], gx[-1]], [y, y], [0, 0], color="#211D15", alpha=0.16, linewidth=0.8)

    b_bed = back_stl.copy()
    b_bed.apply_translation([0.0, 5.0, 0.0])
    add_mesh_to_ax(ax4, b_bed, "#2B5FAB")
    style_3d_ax(
        ax4,
        "4 · Print Orientation: Flat on Z=0.0 (Zero Supports, Zero Bridges)",
        "112.2 × 40.2 × 18.8 mm · 28.54 cm³ (~34g PLA/PETG) · 45° conical roofs on rear bores",
        xlim=(-56, 56),
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

    # --- Panel A: Front View (All Front Heat-Set Insert Bores, Locating Pins & Gussets) ---
    ax = axes[0, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-64, 64)
    ax.set_ylim(-33, 24)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("A · Front View — M3/M2 Heat-Set Insert Bores & Gusset Ribs", fontsize=11.5, fontweight="bold", color="#211D15", pad=8)

    # Gusset polygon outline
    gusset_xy = [(-44.0, -11.5), (44.0, -11.5), (27.0, -18.5), (17.0, -25.5), (-17.0, -25.5), (-27.0, -18.5)]
    ax.add_patch(Polygon(gusset_xy, closed=True, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.65))
    # Pinch jaws (30 x 8.4 mm)
    ax.add_patch(FancyBboxPatch((-15.0, -23.85), 30.0, 8.4, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.85))
    # Upper body (111.0 x 27.4 mm) + 4 corner Ø9.2 mm bosses (total width 112.2 mm)
    ax.add_patch(FancyBboxPatch((-55.5, -13.7), 111.0, 27.4, boxstyle="round,pad=0,rounding_size=4.8", facecolor="#2B5FAB", edgecolor="#211D15", lw=2.0, alpha=0.88))
    # Diagonal stiffening ribs
    ax.add_patch(Polygon([(-13.5, -24.5), (-9.5, -24.5), (-33.0, -11.5), (-39.5, -11.5)], closed=True, facecolor="#F2B417", edgecolor="#211D15", lw=1.3))
    ax.add_patch(Polygon([(9.5, -24.5), (13.5, -24.5), (39.5, -11.5), (33.0, -11.5)], closed=True, facecolor="#F2B417", edgecolor="#211D15", lw=1.3))
    # PCB cavity (96.0 x 21.0 mm)
    ax.add_patch(Rectangle((-48.0, -10.5), 96.0, 21.0, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.6))
    # SMD pocket (91.0 x 16.6 mm)
    ax.add_patch(Rectangle((-45.5, -8.3), 91.0, 16.6, facecolor="#DFD3BC", edgecolor="#211D15", lw=1.0, ls="--"))
    # Center stiffening bridge (26 x 21 mm)
    ax.add_patch(Rectangle((-13.0, -10.5), 26.0, 21.0, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.0))

    # 4x Outer Corner M3 Heat-Set Insert Bosses (X = +-51.5, Y = +-8.5, Ø9.2mm boss, Ø4.0mm bore)
    for ex in (-51.5, +51.5):
        for ey in (-8.5, +8.5):
            ax.add_patch(Circle((ex, ey), 4.6, facecolor="#E4402A", edgecolor="#211D15", lw=1.4))
            ax.add_patch(Circle((ex, ey), 2.0, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))

    # 4x PCB Corner M2 Heat-Set Insert Bosses (X = +-46.0, Y = +-8.5, Ø6.4mm boss, Ø3.2mm bore)
    for bx in (-46.0, +46.0):
        for by in (-8.5, +8.5):
            ax.add_patch(Circle((bx, by), 3.2, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
            ax.add_patch(Circle((bx, by), 1.6, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.0))

    # 4x Press-Fit Locating Pins (X = +-26.1, Y = +-8.5, Ø1.85mm pin on Ø5.2mm pad)
    for px in (-26.1, +26.1):
        for py in (-8.5, +8.5):
            ax.add_patch(Circle((px, py), 2.6, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.0))
            ax.add_patch(Circle((px, py), 0.925, facecolor="#E4402A", edgecolor="#211D15", lw=1.0))

    # 4x Inner Support Pads (X = +-22.1, Y = +-8.5)
    for sx in (-22.1, +22.1):
        for sy in (-8.5, +8.5):
            ax.add_patch(Circle((sx, sy), 2.6, facecolor="#9BA5B4", edgecolor="#211D15", lw=0.9))

    dim_arrow(ax, -51.5, 16.0, +51.5, 16.0, "103.0 mm · 4× M3 Inserts (Ø4.0×6.5mm Bore, Ø9.2mm Boss)", (0, 3.2), "#E4402A", fontsize=8.2)
    dim_arrow(ax, -46.0, -15.5, +46.0, -15.5, "92.0 mm · 4× PCB M2 Inserts (Ø3.2×4.5mm Bore)", (0, -3.0), "#211D15", fontsize=8.0)
    dim_arrow(ax, -26.1, 1.5, +26.1, 1.5, "52.2 mm · 4× Ø1.85mm PCB Locating Pins", (0, 2.6), "#2B5FAB", fontsize=8.0)
    dim_arrow(ax, -15.0, -28.0, +15.0, -28.0, "30.0 mm USB Pinch Jaws (Right: Ø4.0mm M3 Insert)", (0, -2.8), "#E4402A", fontsize=8.0)

    # --- Panel B: Rear Flat Bed Face (Z=0.0) & 90° Metal Bracket Fastening ---
    ax = axes[0, 1]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(-58, 58)
    ax.set_ylim(-31, 20)
    ax.set_aspect("equal")
    ax.grid(True, which="both", color="#211D15", alpha=0.12, linestyle="--")
    ax.set_title("B · Rear Face (Z = 0.0 Flat Bed) + 90° Metal Bracket Overlay", fontsize=11.5, fontweight="bold", color="#211D15", pad=8)

    # Flat rear outline of v2 back cover
    ax.add_patch(Polygon(gusset_xy, closed=True, facecolor="#2B5FAB", edgecolor="#211D15", lw=1.8, alpha=0.45))
    ax.add_patch(FancyBboxPatch((-55.5, -13.7), 111.0, 27.4, boxstyle="round,pad=0,rounding_size=4.8", facecolor="#2B5FAB", edgecolor="#211D15", lw=2.0, alpha=0.45))

    # Overlay WAVE ROVER 90° metal tab (-22.44..+22.44 mm, y = -24.13..-4.50 mm)
    ax.add_patch(Rectangle((-22.44, -24.13), 44.88, 19.63, facecolor="#2C3036", edgecolor="#211D15", lw=2.0, alpha=0.75))
    # Metal tab U-window (-12.88..+12.88 mm, y = -18.02..-8.72 mm)
    ax.add_patch(Rectangle((-12.88, -18.02), 25.76, 9.30, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.5))
    # Two half-square notches at X = +-7.45 mm, y = -8.72..-6.72 mm
    for sign in (-1.0, +1.0):
        ax.add_patch(Rectangle((sign * 7.45 - 1.56, -8.8), 3.12, 2.1, facecolor="#EFE5D2", edgecolor="#211D15", lw=1.2))
        # Ø2.8 mm notch alignment socket
        ax.add_patch(Circle((sign * 7.45, -7.70), 1.4, facecolor="#F2B417", edgecolor="#211D15", lw=1.2))
        # Ø3.2 mm M2 Heat-Set Insert Bore at X = +-10.25, Y = -6.65 mm
        ax.add_patch(Circle((sign * 10.25, -6.65), 1.6, facecolor="#2B5FAB", edgecolor="#F6EFE2", lw=1.4))
        # Ø4.0 mm M3 Heat-Set Insert Bore at X = +-10.00, Y = -14.00 mm (inside U-window!)
        ax.add_patch(Circle((sign * 10.00, -14.00), 2.4, facecolor="#E4402A", edgecolor="#211D15", lw=1.5))
        ax.add_patch(Circle((sign * 10.00, -14.00), 2.0, facecolor="#F6EFE2", edgecolor="#211D15", lw=1.2))

    ax.text(0.0, 5.5, "100% FLAT & SEALED REAR FACE (Z = 0.0 mm)\nZero Hex-Nut Recesses · Prints Flat on Bed Without Bridges!", ha="center", va="center", fontsize=8.8, fontweight="bold", family="monospace", color="#211D15", bbox=dict(boxstyle="round,pad=0.3", facecolor="#F2B417", edgecolor="#211D15", lw=1.4))
    dim_arrow(ax, -10.25, -2.5, +10.25, -2.5, "20.5 mm · 2× M2 Insert Bores (Ø3.2×4.5mm, Tab Holes)", (0, 2.5), "#2B5FAB", fontsize=8.0)
    dim_arrow(ax, -10.00, -20.5, +10.00, -20.5, "20.0 mm · 2× M3 Insert Bores (Ø4.0×6.5mm in U-Window!)", (0, -3.2), "#E4402A", fontsize=8.1)
    dim_arrow(ax, -44.0, -27.2, +44.0, -27.2, "88.0 mm Structural Gusset Span (Zero Neck Weak Point)", (0, -2.5), "#211D15", fontsize=8.0)

    # --- Panel C: Heat-Set Insert Bore Cross-Sections & Why M5 Is Too Large ---
    ax = axes[1, 0]
    ax.set_facecolor("#EFE5D2")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("C · Heat-Set Insert Bore Specs (M3 vs M2 vs Why M5 Is Too Large)", fontsize=11.5, fontweight="bold", color="#211D15", pad=8)

    # Box 1: M3 Heat-Set Insert Spec (USED IN 7 PLACES)
    ax.add_patch(FancyBboxPatch((2, 32), 46, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#E4402A", lw=2.0))
    ax.text(25, 55.5, "[RECOMMENDED] M3 HEAT-SET INSERT (7×)", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#E4402A", family="monospace")
    ax.text(
        4.0,
        43.5,
        "• Insert: M3 × 4mm or M3 × 5mm brass\n"
        "  (Voron/Ruthex/CNC Kitchen OD 4.5–5.0mm)\n"
        "• Melt Bore: Ø 4.0 mm × 6.5 mm deep\n"
        "• Lead-In:   Ø 4.8 mm × 0.6 mm (45°)\n"
        "• Boss OD:   Ø 9.2 mm (2.6 mm wall)\n"
        "• Used at:   4× Outer Cover (X=±51.5),\n"
        "  2× U-Window (X=±10.0), 1× USB Clamp Jaw",
        ha="left",
        va="center",
        fontsize=6.8,
        color="#211D15",
        family="monospace",
    )

    # Box 2: M2 Heat-Set Insert Spec (OPTIONAL — 6×)
    ax.add_patch(FancyBboxPatch((52, 32), 46, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#2B5FAB", lw=2.0))
    ax.text(75, 55.5, "[OPTIONAL] M2 HEAT-SET INSERT (6×)", ha="center", va="center", fontsize=8.2, fontweight="bold", color="#2B5FAB", family="monospace")
    ax.text(
        54.0,
        43.5,
        "• Insert: M2 × 3mm or M2 × 4mm brass\n"
        "  (Standard OD 3.2–3.5 mm)\n"
        "• Melt Bore: Ø 3.2 mm × 4.5 mm deep\n"
        "• Lead-In:   Ø 3.8 mm × 0.5 mm (45°)\n"
        "• Used at:   2× Tab Top Bar (X=±10.25)\n"
        "  & 4× PCB Corners (X=±46.0, Y=±8.5).\n"
        "• Note: 4× Ø1.85mm pins lock the PCB!",
        ha="left",
        va="center",
        fontsize=6.8,
        color="#211D15",
        family="monospace",
    )

    # Box 3: Why M5 Is Too Big
    ax.add_patch(FancyBboxPatch((2, 2), 96, 27, boxstyle="round,pad=0,rounding_size=2.0", facecolor="#F6EFE2", edgecolor="#211D15", lw=2.0))
    ax.text(50, 25.5, "[TOO LARGE] WHY M5 THREADED INSERTS DO NOT FIT THIS CAMERA OR BRACKET", ha="center", va="center", fontsize=8.4, fontweight="bold", color="#211D15", family="monospace")
    ax.text(
        4.0,
        13.0,
        "1. Stereo Camera PCB (95×20 mm): Has 12× Ø 2.0 mm holes just 1.5 mm from the PCB edge.\n"
        "   An M5 screw (Ø 5.0 mm) or M5 insert (Ø 6.4 mm bore / Ø 8.0 mm OD / Ø 12 mm boss) is\n"
        "   3×–4× wider than the PCB holes and collides with the 14×14 mm M12 lens holders!\n"
        "2. WAVE ROVER 90° Metal Bracket: Top bar is 4.22 mm tall with 2× Ø 2.3 mm holes — an M5\n"
        "   screw (5.0 mm) is wider than the metal bar! Use M3 heat-set inserts (Ø 4.0 mm bore).",
        ha="left",
        va="center",
        fontsize=6.9,
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


if __name__ == "__main__":
    render_back_mount_v2_sheets()

