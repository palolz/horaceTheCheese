# LiDAR (LDROBOT D500) + Breakout Board + Radxa ZERO 3W Tower Mount v2 (`cad/lidar_mount/`)

3D-printable structure-only mounting tower (`v2`) for Horace's **LDROBOT D500 (`STL-19P`) LiDAR**, **`40.0 × 20.0 × 8.0 mm` press-fit LiDAR USB-to-UART breakout board**, and **Radxa ZERO 3W (`65.0 × 30.0 × 10.3 mm`, `57.0–58.0 × 22.0–23.0 mm` holes)** on the WAVE ROVER metal expansion plate.

## Printable Structure STL Files (100% Support-Free FDM on `Z = 0.0 mm`, Single Solid Body)

Every STL file is verified as a **single connected watertight solid (`body_count = 1`, `watertight = True`)** with a flat `Z = 0.0 mm` bottom face:

| File | Bounding Box (`X × Y × Z`) | Volume | Bodies | Description |
| --- | --- | --- | --- | --- |
| `horace_lidar_sbc_tower.stl` | `67.0 × 95.0 × 37.0 mm` | `44.76 cm³` (~54 g) | `1` | **1-piece support-free 3-tier tower (`v2`)** with flush side pillars (zero side clip protrusions), `Z = +35.0 mm` LiDAR platform (`Z = 30.8..35.0 mm` deck, zero front-ear downward hang), `17.3 mm` tall (`Z = 13.5..30.8 mm`) × `16.2 mm` wide USB plug/breakout clearance corridor (`13.8 mm` above the `Z = 17.0 mm` PCB seat), and rear open-sky Radxa ZERO 3W bay (`Y = -50.5 mm` center, 100% unobstructed vertical 40-pin GPIO access). |
| `horace_lidar_tower_base.stl` | `67.0 × 89.0 × 12.0 mm` | `14.56 cm³` (~18 g) | `1` | **Optional 2-piece lower half** (`Z = 0.0..12.0 mm`): Expansion plate base (`33.5–34.0 mm` 4× M3 square + `49.0 mm` wide holes) + rear Radxa ZERO 3W bay (`Y = -50.5 mm`) + 2× M3 heat-set insert bores (`X = ±19.6, Y = +9.5 mm`). |
| `horace_lidar_tower_top.stl` | `54.9 × 49.8 × 25.0 mm` | `30.03 cm³` (~36 g) | `1` | **Optional 2-piece upper half** (`Z = 12.0..37.0 mm` shifted to `Z = 0.0` for flat printing): Press-fit `40×20×8 mm` breakout mezzanine + `17.3 mm` USB plug tunnel + `Z = +35.0 mm` LDROBOT D500 LiDAR platform. |

## Key v2 Structural Revisions (from Onshape Review)

1. **Both Side Protrusions Removed (`body_count = 1`):**
   - Deleted the left and right side cable-clip protrusions completely so the outer pillar walls (`X = ±23.4 mm`) are clean, flush, and print as a single solid body (`body_count = 1` on `horace_lidar_sbc_tower.stl`, `horace_lidar_tower_base.stl`, and `horace_lidar_tower_top.stl`).
   - Kept the lower pillars at `Y = -12.5..+13.5 mm` (between the `Y = ±16.875 mm` central square M3 holes) so all 4 central M3 deck bolts have 100% open vertical screwdriver access.

2. **Front LiDAR Ear Downward Protrusion Removed + Doubled Breakout / USB Plug Clearance (`Z = 13.5..30.8 mm`):**
   - Raised the LiDAR mounting deck from `Z = +30.0 mm` to **`Z = +35.0 mm`** (`4.2 mm` thick top plate `Z = 30.8..35.0 mm`, placing the rotating LiDAR optical turret at **`Z = 57.2..70.0 mm`** — **`+11.7 mm` higher than the `45.5 mm` front camera casing** and **`+18.5 mm` higher at the `Z = 64.0 mm` laser beam plane**).
   - Eliminated the downward-hanging cone under the front LiDAR ear (`X = 0.0, Y = +23.30 mm`): the front ear is now supported laterally within `Z = 30.8..35.0 mm` and by side corbels at `|X| ≥ 8.5 mm`, with a blind `Ø 3.2 × 3.0 mm` M2 insert bore (`Z = 35.0..31.6 mm`) + `Ø 2.6 mm` pilot hole so **nothing hangs below `Z = 30.8 mm` anywhere in the `16.2 mm`-wide central corridor (`X = -8.1..+8.1 mm`)**.
   - Lowered the `40.0 × 20.0 × 8.0 mm` breakout board seating ledges to **`Z = 17.0 mm`** and carved a continuous **`16.2 mm` wide × `17.3 mm` tall (`Z = 13.5..30.8 mm`) USB plug & under-board channel** through the entire length of the bridge:
     - **`13.8 mm` vertical clearance above the `Z = 17.0 mm` PCB seat** (more than double the `6.4 mm` component height),
     - **`3.5 mm` under-plug clearance below the `Z = 17.0 mm` PCB seat** (`Z = 13.5..17.0 mm`) for thick USB-C / Micro-USB plug overmolds,
     - **4× corner Y-stops** (`X = ±8.1..±10.15 mm`) + **4× top snap-retention nibs** (`Z = 18.6..20.0 mm`) hold the `40 × 20 mm` breakout board securely without screws.

3. **Radxa ZERO 3W Moved Rearward (`Y = -50.5 mm`) for 100% Open-Sky 40-Pin GPIO Access:**
   - Moved the `65.0 × 30.0 × 10.3 mm` Radxa ZERO 3W bay back to **`Y = -50.5 mm`** (`Y = -65.5..-35.5 mm`, corner standoffs at **`X = ±28.75 mm, Y = -39.25` & `-61.75 mm`**, `Z = 5.6 mm`).
   - The **40-pin GPIO header (`Y = -39.25 mm`)** now sits **`17.75 mm` behind the rearmost edge of the LiDAR bridge (`Y = -21.5 mm`)** with **100% unobstructed vertical sky (`Z = 7.2 mm → ∞`)** so DuPont jumper wires or a 40-pin connector plug straight in from above.
   - The expansion plate's rear mounting holes (`X = ±24.50 mm, Y = -32.75 mm`) sit cleanly ahead of the Radxa PCB (`Y = -35.5 mm`), giving unobstructed vertical access to every mounting screw.

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
