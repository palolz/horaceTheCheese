# LiDAR (LDROBOT D500) + Breakout Board + Radxa ZERO 3W Tower Mount (`cad/lidar_mount/`)

3D-printable 3-tier mounting tower for Horace's **LDROBOT D500 (`STL-19P`) LiDAR**, **`40.0 × 20.0 × 8.0 mm` press-fit LiDAR USB-to-UART breakout board**, and **Radxa ZERO 3W (`65.0 × 30.0 × 10.3 mm`, `57.0–58.0 × 22.0–23.0 mm` holes)** on the WAVE ROVER metal expansion plate.

## Opening the 3D Assembly & Printable Parts in Onshape

All files are in `/Users/palolzaman/Desktop/horace_lidar_tower_onshape/` (and `/Users/palolzaman/Downloads/`) in **millimeters (`mm`)** sharing a single global coordinate origin `(0, 0, 0)` at the center of the `33.5×33.5 / 34.0×34.0 mm` 4-hole square on the top surface (`Z = 0.0 mm`) of the WAVE ROVER metal expansion plate:

1. **Multi-Part Onshape Assembly (`horace_lidar_tower_assembly.3mf`):**
   - In Onshape, click **Create → Import files…** (or `+` → **Import** inside a Document) and select **`horace_lidar_tower_assembly.3mf`**.
   - Choose **"Combine to a single Part Studio"** (leave **"Create composite"** unchecked so all 6 components appear as 6 separate named Parts in exact assembled alignment!).
   - Included objects (`unit="millimeter"`):
     - `01_Printable_Tower_Mount` (`Z = 0.00..32.00 mm`)
     - `02_Radxa_ZERO_3W_SBC` (`Z = 3.42..15.52 mm`)
     - `03_LiDAR_Breakout_40x20x8` (`Z = 18.82..26.82 mm`)
     - `04_LDROBOT_D500_LiDAR` (`Z = 30.02..65.02 mm`, rotating turret at `Z = 52.22..65.02 mm`)
     - `05_WAVE_ROVER_Expansion_Plate` (`Z = -2.00..19.63 mm`)
     - `06_Front_Stereo_Camera_v2_3` (`Z = 3.10..45.50 mm` — built from the actual `horace_cam_back_mount_v2.stl` + `horace_cam_front_visor_v2.stl`)
2. **Individual Co-Registered Assembly STLs (`assembly_parts_stl/01_...` through `06_...`):**
   - Because all 6 individual `.stl` files share the exact same `(0, 0, 0)` origin, importing them into Onshape (`Units: Millimeter`) or inserting them into an Onshape Assembly and clicking the green checkmark (`✓`) snaps all 6 parts into their exact assembled positions automatically.
   - Also includes **`horace_lidar_tower_assembly.stl`** (a single combined `.stl` of all 6 parts).

## Printable STL Files (100% Support-Free FDM on `Z = 0.0 mm`)

| File | Bounding Box (`X × Y × Z`) | Volume | Description |
| --- | --- | --- | --- |
| `horace_lidar_sbc_tower.stl` | `67.0 × 69.6 × 32.0 mm` | `27.90 cm³` (~34 g) | **1-piece support-free 3-tier tower** with 45°-vaulted arches, expansion plate `33.5×33.5 mm` + `49.0 mm` mounting slots, Radxa ZERO 3W bay (with left microSD recess), press-fit `40×20×8 mm` breakout mezzanine, side USB cable loop guide clips, and `Z = +30.0 mm` LiDAR platform. |
| `horace_lidar_tower_base.stl` | `67.0 × 64.0 × 16.0 mm` | `10.27 cm³` (~13 g) | **Optional 2-piece lower half** (`Z = 0.0..16.0 mm`): Expansion plate base + Radxa ZERO 3W bay + side cable clips + 2× M3 heat-set insert bores (`X = ±19.6, Y = +0.5 mm`). |
| `horace_lidar_tower_top.stl` | `54.9 × 49.4 × 16.0 mm` | `17.55 cm³` (~21 g) | **Optional 2-piece upper half** (`Z = 16.0..32.0 mm` shifted to `Z = 0.0` for printing; see `assembly_parts_stl/01b_tower_top_assembled_pos.stl` for `Z = 16..32 mm` assembled position). |

## Extracted & Verified Component Dimensions

1. **Linux Host SBC — Radxa ZERO 3W (`Rockchip RK3566`, Wi-Fi 6, Hardware H.264/H.265 Encoder):**
   - **Outer PCB size:** **`65.0 × 30.0 × 1.6 mm`** (`64.0–65.0 mm` long; **`10.3 mm` max total thickness** including the **`6.0 mm` tall** color-coded 40-pin GPIO header pins).
   - **4× Corner mounting holes:** User measured **`57.0 × 22.0–23.0 mm` C-to-C** (nominal Pi Zero spec `58.0 × 23.0 mm`). Matched by **`3.6 × 3.2 mm` oblong slots + `Ø 3.2 mm` M2 heat-set insert bores** centered at **`57.5 × 22.5 mm` (`X = ±28.75 mm, Y = -26.0 ± 11.25 mm`)** on `Z = 5.2 mm` standoffs.
   - **Port & GPIO orientation:** The **2× USB-C ports + Micro-HDMI port** face rearward (`Y = -41.0 mm`) into open space for unrestricted plug & cable loop access, while the **40-pin GPIO header** sits directly over the `46.0 × 22.0 mm` rear cutout aligned with the expansion plate's rectangular window.

2. **LiDAR USB-to-UART Breakout Board (`40.0 × 20.0 × 8.0 mm`, Screwless Press-Fit Cradle):**
   - **Outer size:** **`40.0 mm` long × `20.0 mm` wide × `8.0 mm` max thickness** (`1.6 mm` PCB, no mounting holes).
   - **Press-fit / snap-in mezzanine (`Z = 18.8..27.2 mm`):** **`40.6 × 20.3 mm` pocket** with `1.95 mm` bottom seating ledges (`16.4 mm` wide under-board solder-pin relief channel) and **4× chamfered top snap-retention nibs** that click over the `1.6 mm` FR4 edges without screws.
   - **Opposite-facing ports + side cable loop arches:** The 4-pin white header faces rearward (`-Y`) right beneath the LiDAR's 4-pin connector, while the **Micro-USB receptacle** faces forward (`+Y = +20.5 mm`) into open air and loops smoothly (`R ≥ 18 mm`) through the **integrated side cable-guide clips (`X = ±25.4 mm`)** back to the Radxa ZERO 3W's USB-C port.

3. **LDROBOT D500 (`STL-19P`) LiDAR (`38.5 × 38.5 × 35.0 mm`):**
   - **Elevation over `45.5 mm` Front Stereo Camera:** Mounted on the **`Z = +30.0 mm` top platform** so the `22.2 mm` stationary square base spans `Z = 30.0..52.2 mm` and the **`Ø 35.3 × 12.8 mm` rotating optical turret spans `Z = 52.2..65.0 mm`** — **`+6.7 mm` higher than the `45.5 mm` camera top** (`+13.5 mm` at the `Z = 59.0 mm` laser beam plane, clearing even the `-4.5°` downward beam cone by `+8.4 mm`).
   - **3× Mounting Ear Bosses (`Z = 30.0 mm`):**
     - **Front ear (`0°`):** `X = 0.0 mm, Y = +23.30 mm` (`4.05 mm` ahead of the `+19.25 mm` front wall; `Ø 3.2 mm` M2 insert bore + `2.8 × 3.8 mm` slot).
     - **Left & Right rear-side ears:** `Y = -8.65 mm` (`10.6 mm` forward of the `-19.25 mm` rear wall), with **`5.4 × 2.9 mm` horizontal stadium slots** centered at `X = ±21.95 mm` (plus `Ø 3.2 mm` M2 insert bores at `X = ±22.50 mm`), accommodating both **`42.69 mm` CAD** and **`45.0 mm` user-measured** C-to-C spacing.

4. **WAVE ROVER Metal Expansion Plate Interface (`Z = 0.0 mm`):**
   - **4× Central Square Holes (`33.5 × 33.5 mm` measured / `34.0 × 34.0 mm` DXF):** `4.3 × 4.3 mm` slots + `Ø 6.8 mm` M3 counterbores at **`X = ±16.875 mm, Y = ±16.875 mm`**.
   - **4× Wide `49.0 mm` C-to-C Holes (`X = ±24.50 mm`):** `3.4 × 4.8 mm` slots at `Y = +2.0 mm` and `Y = -32.75 mm`.
