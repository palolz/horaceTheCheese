# Stereo Camera Enclosure & 90° Bracket Mount (`cad/camera_mount/`)

3D-printable enclosure, anti-rotation WAVE ROVER 90° front-tab bracket mount, and Mini-USB strain-relief holder for Horace's binocular stereo camera module.

## Back Cover v2 (`horace_cam_back_mount_v2.stl`) — Heat-Set Insert Edition

Redesigned specifically for **M3 (and optional M2) brass heat-set threaded inserts** with **zero hex-nut recesses** and a **100% flat, solid `Z = 0.0 mm` rear face** for support-free FDM printing:

- **Why M5 Threaded Inserts Are Too Large:**
  - The stereo camera PCB (`95.0 × 20.0 × 1.6 mm`) has 12× **`Ø 2.0 mm` mounting holes** placed just `1.5 mm` from the top/bottom PCB edges. An M5 screw (`Ø 5.0 mm`) or M5 brass insert (`Ø 6.4 mm` melt bore / `Ø 8.0 mm` OD / `Ø 12 mm` boss) is 3×–4× larger than the PCB holes and collides with the `14 × 14 mm` M12 lens holders.
  - The WAVE ROVER 90° metal bracket top crossbar is only **`4.22 mm` tall** with 2× **`Ø 2.3 mm` holes** (`X = ±10.25 mm`) above a **`25.75 × 9.30 mm` U-window** (`X = -12.88..+12.88 mm`). An M5 screw (`5.0 mm`) is wider than the entire `4.22 mm` metal bar.
- **Exact Hole Sizes on Back Cover v2 (`horace_cam_back_mount_v2.stl`):**
  1. **M3 Heat-Set Threaded Insert Bores (`7×` total — Primary Fastener):**
     - **Melt bore:** **`Ø 4.0 mm × 6.5 mm` deep** + **`Ø 4.8 mm × 0.6 mm` (45°)** soldering-iron lead-in chamfer (fits standard `M3 × 4 mm` or `M3 × 5 mm` brass heat-set inserts, `4.5–5.0 mm` OD).
     - **Locations:**
       - **4× Outer Cover-to-Cover Bosses (`X = ±51.5 mm, Y = ±8.5 mm`, `103.0 mm` C-to-C, `Ø 9.2 mm` boss OD):** Placed outside the `95 mm` PCB ends so the Front Cover bolts to the Back Cover with M3 screws without passing through the tiny `Ø 2.0 mm` PCB holes. Blind bores (`Z = 9.8` down to `3.3 mm`, leaving a `3.3 mm` solid floor at `Z = 0`).
       - **2× 90° Metal Bracket U-Window Bosses (`X = ±10.00 mm, Y = -14.00 mm`, `20.0 mm` C-to-C):** Centered inside the metal bracket's `25.75 × 9.30 mm` U-window (`Z = 0.0..6.5 mm` with 45° self-supporting conical roof), allowing 2× M3 screws + washers through the U-window with zero drilling.
       - **1× Mini-USB Pinch-Clamp Right Jaw (`X = +0.9..+15.0 mm, Y = -19.65 mm, Z = 12.6 mm`):** Horizontal `Ø 4.0 mm` M3 insert bore (`Ø 4.8 mm` chamfer on right outer face `X = +15.0 mm`), paired with a **`Ø 3.4 mm` M3 clearance bore + `Ø 6.4 mm` socket-head counterbore** on the left jaw (`X = -15.0..-0.9 mm`).
  2. **M2 Heat-Set Insert Bores (`6×` total — Optional) & 4× Press-Fit PCB Locating Pins:**
     - **Melt bore:** **`Ø 3.2 mm × 4.5 mm` deep** + **`Ø 3.8 mm × 0.5 mm` (45°)** lead-in chamfer (fits `M2 × 3–4 mm` brass inserts, `3.2–3.5 mm` OD).
     - **Locations:** 2× at **`X = ±10.25 mm, Y = -6.65 mm`** (matching the metal bracket's `Ø 2.3 mm` top crossbar holes) and 4× at **`X = ±46.0 mm, Y = ±8.5 mm`** (PCB corners).
     - **4× Integrated PCB Press-Fit Locating Pins (`Ø 1.85 mm × 2.2 mm` tall, tapered to `Ø 1.44 mm` tip)** at **`X = ±26.1 mm, Y = ±8.5 mm`** (`52.2 mm` C-to-C): Drop straight into four inner `Ø 2.0 mm` PCB holes to lock the camera board in X/Y without screws.
     - **2× Anti-Rotation Notch Alignment Sockets (`Ø 2.8 mm × 3.2 mm` deep)** at **`X = ±7.45 mm, Y = -7.70 mm`**: Align with the two `3.12 × 2.0 mm` half-square notches on the metal bracket.
- **Structural & Printability Upgrades (`112.2 × 40.2 × 18.8 mm`, `28.54 cm³`):**
  - **100% Flat & Sealed `Z = 0.0 mm` Backplate:** `6.8 mm` thick base (`5.4 mm` solid floor under the `1.4 mm` SMD pocket + `26 mm` wide full-thickness center spine) — zero rear cutouts, zero bridges, zero supports.
  - **Sweeping `88.0 mm` Triangular Gusset Wings + Raised Diagonal Ribs (`Z = 0..9.8 mm`):** Eliminates the neck stress concentration between the lower bracket/USB clamp and the wide `112.2 mm` camera body.

| File | Bounding Box (`X × Y × Z`) | Volume | Description |
| --- | --- | --- | --- |
| `horace_cam_back_mount_v2.stl` / `horace_cam_back_mount.stl` | `112.2 × 40.2 × 18.8 mm` | `28.54 cm³` | **v2 Rear structural shell** for M3 (`Ø 4.0 mm`) & optional M2 (`Ø 3.2 mm`) heat-set threaded inserts, 4× `Ø 1.85 mm` PCB locating pins, `88 mm` triangular gusset wings, and M3 Mini-USB pinch clamp. |
| `horace_cam_front_visor.stl` | `102.0 × 26.0 × 14.5 mm` | `12.50 cm³` | Retro binocular front cover protecting the exposed FFC ribbon cables, with `Ø 16.6 mm` lens openings (`80.0 mm` baseline) and sculpted top sun-visor brow. |
| `horace_cam_usb_shim.stl` | `13.7 × 8.7 × 14.0 mm` | `0.67 cm³` | Parametric snap-in U-collar insert sized for a `10.2 × 7.0 mm` Mini-USB plug overmold and `Ø 4.5 mm` cable neck (`2-minute` reprint if your cable plug differs). |

## Extracted Dimensions (Factory DXF + 5×5 mm Grid Photos)

- **Stereo Camera PCB (`P1044926`–`P1044928`):**
  - Outer PCB dimensions: **`95.0 × 20.0 × 1.6 mm`** (enclosure pocket: `96.0 × 21.0 mm`).
  - **Lens center-to-center baseline:** **`80.0 mm`** (`X = -40.0 mm` and `+40.0 mm`).
  - M12 lens holders & barrels: `14.0 × 14.0 mm` square base (`6.0 mm` tall), `Ø 14.0 mm` barrel (`Ø 15.0 mm` lens cap), **`19.0 mm`** total height above PCB front face (`Ø 16.6 mm` openings in front visor).
  - Outer corner M2 holes (4×): **`92.0 × 17.0 mm`** (`X = ±46.0 mm, Y = ±8.5 mm`, `Ø 2.0 mm`).
  - Inner FFC-flanking M2 holes (8×): `X = ±26.1 mm` (`52.2 mm`) and `X = ±22.1 mm` (`44.2 mm`), `Y = ±8.5 mm`.
  - Mini-USB 5-pin receptacle: Centered horizontally at **`X = 0.0 mm`** on the bottom edge (`6.8 × 7.2 × 3.9 mm`).
- **WAVE ROVER Expansion Plate 90° Upturned Front Bracket (`WAVE ROVER-EP DXF.dxf` + `P1044916`):**
  - Sheet metal thickness: **`2.00 mm`**.
  - Upturned tab width × height: **`44.88 mm` wide × `19.63 mm` tall** above the top deck (`4.22 mm` top crossbar over a `25.75 × 8.10 mm` central U-window).
  - Mounting holes (2×): **`Ø 2.2–2.3 mm`**, spaced **`21.00 mm`** in DXF (`X = ±10.50 mm`) and **`~20.0 mm`** on the 5×5 mm grid (`P1044916`). Matched by `3.5 × 2.4 mm` stadium slots at `X = ±10.25 mm` with captive rear M2 hex nut traps.
  - Inner "half-square" notches (2×): **`3.12 mm` wide × `2.0 mm` tall** centered at **`X = ±7.45 mm`** (`±5.89..±9.01 mm`, flanking the `11.78 mm` center bridge). Engaged by two **`2.70 × 3.0 × 2.10 mm` anti-rotation keys** on the back mount.

## Regenerating the STLs (or Customizing the Mini-USB Shim)

```bash
/opt/homebrew/Caskroom/miniforge/base/envs/ros_jazzy/bin/python3 \
  cad/camera_mount/generate_camera_mount.py \
  --lens-baseline 80.0 \
  --usb-plug-width 10.2 \
  --usb-plug-depth 7.0 \
  --usb-cable-dia 4.5
```

To regenerate the 3D preview sheet and engineering dimension diagrams in `docs/assets/cad/`:

```bash
/opt/homebrew/Caskroom/miniforge/base/envs/ros_jazzy/bin/python3 \
  cad/camera_mount/render_previews.py
```
