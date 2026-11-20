# Stereo Camera Enclosure & 90° Bracket Mount (`cad/camera_mount/`)

3D-printable enclosure, anti-rotation WAVE ROVER 90° front-tab bracket mount, and Mini-USB strain-relief holder for Horace's binocular stereo camera module.

## Back Cover v2 (`horace_cam_back_mount_v2.stl`) — Heat-Set Insert Edition

Redesigned specifically for **M3 (and optional M2) brass heat-set threaded inserts** with **zero hex-nut recesses** and a **100% flat, solid `Z = 0.0 mm` rear face** for support-free FDM printing:

- **Why M5 Threaded Inserts Are Too Large:**
  - The stereo camera PCB (`100.0 × 22.0 × 1.6 mm`, inner pocket `101.2 × 23.2 mm`) has 12× **`Ø 2.0 mm` mounting holes** placed just `2.0 mm` from the PCB edges (`Y = ±9.0 mm`, `X = ±48.0 mm`). An M5 screw (`Ø 5.0 mm`) or M5 brass insert (`Ø 6.4 mm` melt bore / `Ø 8.0 mm` OD / `Ø 12 mm` boss) is 3×–4× larger than the PCB holes and collides with the `14 × 14 mm` M12 lens holders.
  - The WAVE ROVER 90° metal bracket top crossbar is only **`4.22 mm` tall** with 2× **`Ø 2.3 mm` holes** (`X = ±10.25 mm`) above a **`25.75 × 9.30 mm` U-window** (`X = -12.88..+12.88 mm`). An M5 screw (`5.0 mm`) is wider than the entire `4.22 mm` metal bar.
- **Exact Hole Sizes on Back Cover v2 (`horace_cam_back_mount_v2.stl`):**
  1. **M3 Heat-Set Threaded Insert Bores (`7×` total — Casing & Bracket Fasteners):**
     - **Melt bore:** **`Ø 4.0 mm × 6.5 mm` deep** + **`Ø 4.8 mm × 0.6 mm` (45°)** soldering-iron lead-in chamfer (fits standard `M3 × 4 mm` or `M3 × 5 mm` brass heat-set inserts, `4.5–5.0 mm` OD).
     - **Locations:**
       - **4× Outer Cover-to-Cover Bosses (`X = ±56.5 mm, Y = ±9.0 mm`, `113.0 × 18.0 mm` C-to-C, `Ø 9.2 mm` boss OD):** Placed completely outside the `101.2 × 23.2 mm` (`X = ±50.6 mm, Y = ±11.6 mm`) PCB pocket (inner boss edge at `X = ±51.9 mm`) so the Front Cover bolts to the Back Cover with M3 screws without encroaching on the `100.0 × 22.0 mm` board or its `X = ±48.0 mm, Y = ±9.0 mm` end holes. Blind bores (`Z = 9.8` down to `3.3 mm`, leaving a `3.3 mm` solid floor at `Z = 0`).
       - **2× 90° Metal Bracket U-Window Bosses (`X = ±10.00 mm, Y = -15.10 mm`, `20.0 mm` C-to-C):** Centered inside the metal bracket's `25.75 × 9.30 mm` U-window (`Z = 0.0..6.5 mm` with 45° self-supporting conical roof), allowing 2× M3 screws + washers through the U-window with zero drilling.
       - **1× Mini-USB Pinch-Clamp Right Jaw (`X = +0.9..+15.0 mm, Y = -20.75 mm, Z = 12.6 mm`):** Horizontal `Ø 4.0 mm` M3 insert bore (`Ø 4.8 mm` chamfer on right outer face `X = +15.0 mm`), paired with a **`Ø 3.4 mm` M3 clearance bore + `Ø 6.4 mm` socket-head counterbore** on the left jaw (`X = -15.0..-0.9 mm`).
  2. **M2 Heat-Set Insert Bores (`10×` total — 8× Board Mounting + 2× Tab Crossbar):**
     - **Melt bore:** **`Ø 3.2 mm × 4.5 mm` deep** + **`Ø 3.8 mm × 0.5 mm` (45°)** lead-in chamfer (fits `M2 × 3–4 mm` brass inserts, `3.2–3.5 mm` OD).
     - **Locations:**
       - **4× Outer Board Corner Holes:** **`X = ±48.0 mm, Y = ±9.0 mm` (`96.0 × 18.0 mm` C-to-C)** on the `Z = 6.8 mm` PCB shelf (`Ø 6.0 mm` support bosses underneath).
       - **4× Middle Board Holes (3rd from left/right):** **`X = ±26.1 mm, Y = ±9.0 mm` (`52.2 × 18.0 mm` C-to-C)** on the `Z = 6.8 mm` PCB shelf (`Ø 6.0 mm` support bosses underneath, replacing the earlier locating pins so you can install M2 threaded inserts directly).
       - **2× 90° Metal Bracket Top Crossbar Holes:** **`X = ±10.25 mm, Y = -7.75 mm`** (`20.5 mm` C-to-C).
     - **2× Anti-Rotation Notch Alignment Sockets (`Ø 2.8 mm × 3.2 mm` deep)** at **`X = ±7.45 mm, Y = -8.80 mm`**: Align with the two `3.12 × 2.0 mm` half-square notches on the metal bracket.
- **Cut-Down Mini-USB Holder Top (`Y ≤ -16.2 mm`):**
  - The raised front walls (`Z > 9.8 mm`) of the Mini-USB collar and pinch jaws start strictly at **`Y = -16.2 mm`** (`1.4 mm` below the Front Visor's `Y = -14.8 mm` bottom wall), and the USB neck channel (`Y = -16.2..-11.6 mm`) is cut down to **`Z = 6.4 mm`** so it never interferes with the USB connector or the Front Visor (`0.0000 mm³` boolean intersection).
- **Structural & Printability Upgrades (`122.2 × 42.4 × 18.8 mm`, `32.29 cm³`):**
  - **100% Flat & Sealed `Z = 0.0 mm` Backplate:** `6.8 mm` thick base (`5.4 mm` solid floor under the `1.4 mm` SMD pocket + `26 mm` wide full-thickness center spine) — zero rear cutouts, zero bridges, zero supports.
  - **Sweeping `96.0 mm` Triangular Gusset Wings + Raised Diagonal Ribs (`Z = 0..9.8 mm`):** Eliminates the neck stress concentration between the lower bracket/USB clamp and the wide `122.2 mm` camera body.

| File | Bounding Box (`X × Y × Z`) | Volume | Description |
| --- | --- | --- | --- |
| `horace_cam_back_mount_v2.stl` / `horace_cam_back_mount.stl` | `122.2 × 42.4 × 18.8 mm` | `32.29 cm³` | **v2.3 Rear structural shell** for `100.0 × 22.0 mm` board (`101.2 × 23.2 mm` pocket), **8× M2 board heat-set insert bores** (`4×` corners at `X = ±48.0, Y = ±9.0 mm` + `4×` middle holes at `X = ±26.1, Y = ±9.0 mm`), `113.0 × 18.0 mm` outer M3 casing ears (`X = ±56.5, Y = ±9.0 mm`), cut-down Mini-USB neck (`Y ≤ -16.2 mm`), and `96 mm` triangular gusset wings. |
| `horace_cam_front_visor_v2.stl` / `horace_cam_front_visor.stl` | `122.2 × 29.6 × 16.8 mm` | `31.38 cm³` | **v2.3 Retro binocular front cover** with **`85.0 mm` lens baseline (`X = ±42.5 mm, Y = 0.0 mm`)**, enlarged **`70.0 × 16.8 mm` FFC ribbon crevice** (`12.8 mm` height clearance above PCB for `10 × 13 mm` bowed ribbons), **clean front faceplate** (`4×` outer M3 holes only — NO PCB screw through-holes), and **8× blind underside M2 screw-head pockets (`Ø 4.8 × 2.8 mm`)**. |
| `horace_cam_usb_shim.stl` | `13.7 × 8.7 × 14.0 mm` | `0.67 cm³` | Parametric snap-in U-collar insert sized for a `10.2 × 7.0 mm` Mini-USB plug overmold and `Ø 4.5 mm` cable neck (`2-minute` reprint if your cable plug differs). |

## Extracted & Verified Dimensions (v2.2)

- **Stereo Camera PCB (`100.0 × 22.0 × 1.6 mm`):**
  - Outer PCB dimensions: **`100.0 × 22.0 × 1.6 mm`** (enclosure pocket: **`101.2 × 23.2 mm`**, `0.6 mm` clearance per side in X and Y).
  - **Lens center-to-center baseline:** **`85.0 mm`** (`X = -42.5 mm` and `+42.5 mm`, `Y = 0.0 mm` = `11.0 mm` from top/bottom edges and `7.5 mm` from left/right ends).
  - M12 lens holders & barrels: `14.0 × 14.0 mm` square base (`6.0 mm` tall, `X = ±35.5..±49.5 mm, Y = ±7.0 mm`), `Ø 14.0 mm` barrel (`Ø 15.0 mm` lens cap), **`19.0 mm`** total height above PCB front face (`Ø 16.6 mm` openings in front visor + `15.2 × 15.2 mm` rear base pockets).
  - Outer corner M2 holes (4×): **`96.0 × 18.0 mm`** (`X = ±48.0 mm, Y = ±9.0 mm`, `2.0 mm` inset from all four board edges).
  - Inner FFC-flanking M2 locating holes (4× pins + 4× pads): `X = ±26.1 mm` (`52.2 × 18.0 mm` press-fit `Ø 1.85 mm` locating pins) and `X = ±22.1 mm` (`44.2 × 18.0 mm`), `Y = ±9.0 mm`.
  - Outer M3 casing fastening ears (4×): **`113.0 × 18.0 mm`** (`X = ±56.5 mm, Y = ±9.0 mm`, `Ø 9.2 mm` boss OD, `Ø 4.0 × 6.5 mm` M3 insert bore on Back Cover, `Ø 3.4 mm` through + `Ø 6.5 mm` counterbore on Front Visor).
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
