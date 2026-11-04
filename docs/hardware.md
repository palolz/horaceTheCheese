# Hardware & BOM

Everything the rover is (or will be) made of, photographed on the workbench as parts land and get tested.

| Part | Role | Source / model | Status |
| --- | --- | --- | --- |
| WAVE ROVER 4WD chassis | 4× N20 gearmotors, General Driver for Robots (ESP32), 9-axis IMU, OLED, 3S 18650 pack (`12.39 V`) | [Waveshare WAVE ROVER](https://www.waveshare.com/wiki/WAVE_ROVER) (`MAC: XX:XX:XX:XX:XX:XX`) | <span class="htc-badge htc-badge--done">Done · Rolling</span> |
| Metal top expansion plate | Slotted anodized mounting deck + standoffs for LiDAR & compute | Bundled with WAVE ROVER | <span class="htc-badge htc-badge--done">On hand</span> |
| 2D LiDAR kit | 360° laser scans for Stage 2 SLAM | **LDROBOT D500 LiDAR Kit** (LD19 / DTOFLiDAR) | <span class="htc-badge htc-badge--done">On hand</span> |
| Companion SBC (bench candidate) | Compact Linux board spotted on the cutting mat beside Horace | Raspberry Pi Zero-form-factor board | <span class="htc-badge htc-badge--done">On hand</span> |
| Binocular stereo camera | Depth images + point clouds | TBD (unit ordered) | <span class="htc-badge htc-badge--progress">Ordered</span> |
| LiDAR mast + mounts | Yellow mast, printed brackets | 3D-printed, designed in-house | <span class="htc-badge htc-badge--planned">Planned</span> |

## Workbench gallery

<div class="htc-photo-grid">
  <figure class="htc-photo">
    <img src="../assets/hardware/horace-bench-d500.jpg" alt="Hero shot of the WAVE ROVER on the workbench with its metal mounting plate and LDROBOT D500 LiDAR kit box">
    <figcaption><strong>Workbench hero shot:</strong> Horace with the black anodized expansion deck to the left and the <strong>LDROBOT D500 LiDAR Kit</strong> box ready behind it.</figcaption>
  </figure>
  <figure class="htc-photo">
    <img src="../assets/hardware/horace-bench-pizero.jpg" alt="Angled workbench shot showing the WAVE ROVER, Raspberry Pi Zero-form-factor board on the grid mat, and LDROBOT box">
    <figcaption><strong>Scale check:</strong> WAVE ROVER alongside a Raspberry Pi Zero-form-factor board on the cutting mat and the LDROBOT LiDAR box.</figcaption>
  </figure>
  <figure class="htc-photo">
    <img src="../assets/hardware/esp32-top-pinout.jpg" alt="Top-down view of the WAVE ROVER smoked acrylic window, ESP32 board, and 40-pin header silkscreen">
    <figcaption><strong>Top deck & pinout silkscreen:</strong> Smoked acrylic window over the ESP32 General Driver for Robots board, 40-pin header legend (<code>5V / GND / RX / TX / SCL / SDA</code>), folding 2.4 GHz antenna, power switch, and 12.6 V charge jack.</figcaption>
  </figure>
  <figure class="htc-photo">
    <img src="../assets/hardware/oled-ap-ugv.jpg" alt="Close-up of the WAVE ROVER OLED displaying AP:UGV, ST: OFF, MAC:XX:XX:XX:XX:XX:XX, V:12.39">
    <figcaption><strong>Stock OLED status screen:</strong> <code>AP:UGV</code> (hotspot SSID), <code>ST: OFF</code> (station mode idle), <code>MAC:XX:XX:XX:XX:XX:XX</code>, and <code>V:12.39</code> across the 3S 18650 pack.</figcaption>
  </figure>
</div>

## Hardware notes from Stage 1 bring-up

- **OLED & Wi-Fi AP naming:** Newer Waveshare firmware advertises SSID **`UGV`** (password `12345678`, gateway `192.168.4.1`) rather than the older `WAVE_ROVER` SSID documented in early wiki revisions.
- **40-pin header silkscreen:** The top deck clearly labels the expansion header pins needed for Stage 1–3 wiring — `5V`, `3V3`, `GND`, `RX`, `TX` (3.3 V UART to the ESP32), and `SCL` / `SDA` (I²C bus).
- **UniFi Wi-Fi 7 (`T:404`) compatibility:** The ESP32's 2.4 GHz radio needs a **WPA2-PSK (PMF Disabled)** 2.4 GHz SSID if switching from `AP:UGV` to home-network station mode (`T:404`).
- **Power budget:** Full 3S 18650 charge reads `12.39 V` under idle OLED/Wi-Fi load; onboard buck converters feed the 5 V and 3.3 V rails on the 40-pin header.

