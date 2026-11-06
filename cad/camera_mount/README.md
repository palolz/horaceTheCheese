# Stereo Camera Enclosure & 90° Bracket Mount (`cad/camera_mount/`)

3D-printable enclosure, anti-rotation WAVE ROVER 90° front-tab bracket mount, and Mini-USB strain-relief holder for Horace's binocular stereo camera module.

## Generated STL Files (100% Support-Free FDM)

All three STL files are oriented with their flat build-plate face on **`Z = 0.0`** and require **zero supports**:

| File | Bounding Box (`X × Y × Z`) | Volume | Description |
| --- | --- | --- | --- |
| `horace_cam_back_mount.stl` | `101.0 × 42.0 × 17.8 mm` | `14.45 cm³` | Rear protective shell with 8× M2 PCB bosses, SMD clearance pocket, 90° bracket seat with **2× anti-rotation notch keys** (`X = ±7.45 mm`) and `20.0–21.0 mm` M2 stadium slots + nut traps, and lower **Mini-USB strain-relief clamp collar** (M3 pinch bolt + `4.2 mm` zip-tie channel). |
| `horace_cam_front_visor.stl` | `102.0 × 26.0 × 14.5 mm` | `12.50 cm³` | Retro binocular front cover protecting the exposed FFC ribbon cables, with `Ø 16.6 mm` lens openings (`80.0 mm` baseline), sculpted top sun-visor brow, and 4× M2 corner counterbores. |
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
