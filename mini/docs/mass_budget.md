# Knoll Mini — mass budget (Session 5, simulation)

All masses in grams, computed by `tools/build_mjcf.py`'s bookkeeping from the
real `parts/current/*.stl` volumes × PETG 1.27 g/cm³ × 0.55 fill, plus 13.2 g
per SCS0009 servo, 2 g per bearing, plus `spec.ELECTRONICS` (estimates, **[U]**).
Run: `python tools/build_mjcf.py` on 2026-10-28; MJCF `model/scene_knoll_mini.xml`
subtree mass verified at 428.9 g.

| Body | Printed | Servos | Bearings | Electronics [U] | Total |
|---|---|---|---|---|---|
| trunk_base | 15.5 | 26.4 (2) | 4.0 | 78.0 | 123.9 |
| yaw2roll | 5.7 | 13.2 (1) | 2.0 | — | 20.9 |
| hip_l | 1.2 | — | 2.0 | — | 3.2 |
| upper_leg_left | 9.6 | 26.4 (2) | 2.0 | — | 38.0 |
| leg | 1.6 | 13.2 (1) | — | — | 14.8 |
| ankle_left | 5.3 | — | 2.0 | — | 7.3 |
| neck | 13.3 | 26.4 (2) | — | — | 39.7 |
| neck_pitch | 1.4 | — | 2.0 | — | 3.4 |
| yaw_roll_motion | 5.3 | 13.2 (1) | 4.0 | — | 22.5 |
| jaw_soft (head) | 29.9 | 13.2 (1) | — | 27.5 | 70.6 |
| bearing_roll | 5.7 | 13.2 (1) | 2.0 | — | 20.9 |
| hip_l_2 | 1.2 | — | 2.0 | — | 3.2 |
| upper_leg_right | 9.9 | 26.4 (2) | 2.0 | — | 38.3 |
| leg_2 | 1.6 | 13.2 (1) | — | — | 14.8 |
| ankle_right | 5.3 | — | 2.0 | — | 7.3 |
| **TOTAL** | **112.6** | **184.8 (14)** | **26.0 (13)** | **105.5** | **428.9** |

## Electronics detail (all [U] estimates, `spec.ELECTRONICS`)

| Item | Body | g |
|---|---|---|
| 2S 450 mAh LiPo + XT30 | trunk_base | 32.0 |
| UBEC 6 V/5 A | trunk_base | 10.0 |
| BNO085 IMU | trunk_base | 3.0 |
| Bus hub + wiring | trunk_base | 18.0 |
| Screws + inserts | trunk_base | 15.0 |
| XIAO ESP32-S3 Sense + OV2640 | jaw_soft | 10.0 |
| 2 × WS2812 halo rings | jaw_soft | 6.0 |
| MAX98357A + speaker | jaw_soft | 8.0 |
| VL53L0X ToF | jaw_soft | 1.5 |
| 5 V buck | jaw_soft | 2.0 |
| **Subtotal** | | **105.5** |

## Notes
- Head body `jaw_soft` totals 70.6 g — just over the ≤ 70 g [U] target; the margin
  depends on the real electronics masses (weigh before printing).
- The 13 bearings counted are 6700ZZ seats plus small default/bushing stand-ins at
  2 g each; the jaw_soft roll idler bearing is intentionally absent (printed bushing).
- Baseline docstring reference was 378.9 g before head electronics placeholders and
  the session-2/4 part changes; current verified total is 428.9 g.
