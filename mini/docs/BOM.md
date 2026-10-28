# Knoll Mini — bill of materials (Session 6)

Marks: **[V]** = price confirmed on the linked product page on the date shown
(all pages opened 2026-10-28 unless noted). **[U]** = unverified estimate;
the page linked is a real product page opened for reference, but the line
price itself is an estimate, not the price shown there. **Do not buy yet** —
this is a planning BOM; no orders have been placed.

USD totals exclude shipping and tax. GBP column is UK retail **incl. VAT**
where a UK price was verified, else USD ÷ 1.33.

| # | Item | Qty | USD ea | Line USD | GBP line | Source (opened 2026-10-28) |
|---|---|---|---|---|---|---|
| 1 | Feetech SCS0009 servo | 14 | 9.50 | 133 | 100 | [V] Seeed $9.00, 10+ $8.00 — https://www.seeedstudio.com/Feetech-SCS0009-Servo-p-6535.html (2026-10-28). [V] Lextronic €5.40 incl VAT — https://www.lextronic.fr/servomoteur-feetech-scs0009-a-bus-uart-80296.html (2026-10-27). [V] Eckstein €12.95 incl VAT — https://eckstein-shop.de/Feetech-SCS0009-6V-23kgcm-Serial-Control-BUS-Servo (2026-10-28). $9.50 each is a midpoint [U]; Seeed 10+ pricing makes 14 servos ~$112 |
| 2 | Seeed XIAO ESP32-S3 Sense (camera + mic) | 1 | 14 | 14 | 13.50 | [V] Seeed $13.90 — https://www.seeedstudio.com/XIAO-ESP32S3-Sense-p-5639.html (2026-10-28). [V] Pi Hut £13.50 incl VAT loose headers / £14.50 pre-soldered — https://thepihut.com/products/seeed-studio-xiao-esp32s3-sense (2026-10-28) |
| 3 | BNO085 IMU breakout | 1 | 13 | 13 | 10 | [U] $13 is the generic-board estimate. Name-brand reference: Adafruit PID 4754 $29.50 — https://www.adafruit.com/product/4754 (2026-10-28). Cheaper option: MPU-6050 ~$3, see line below |
| 4 | VL53L0X ToF breakout | 1 | 5 | 5 | 4 | [U] $5 generic (GY-530 type). Name-brand reference: Adafruit PID 3317 $14.95 — https://www.adafruit.com/product/3317 (2026-10-28) |
| 5 | WS2812 12-LED ring, OD ≈37 mm | 2 | 2 | 4 | 3 | [U] $2 each is marketplace pricing. [V] AZ-Delivery €4.79 incl tax (38 mm OD / 27 mm ID) — https://www.az-delivery.de/en/products/rgb-led-ring-ws2812-mit-12-rgb-leds-5v-fuer-arduino (2026-10-28). [V] Adafruit NeoPixel Ring 12 $8.95 (36.8 mm OD) — https://www.adafruit.com/product/1643 (2026-10-28). **Check real ring OD against the modelled Ø26/Ø18 halos before printing** |
| 6 | MAX98357A I2S amp | 1 | 4 | 4 | 5.40 | [V] Adafruit PID 3006 $5.95 — https://www.adafruit.com/product/3006 (2026-10-28); £5.40 incl VAT at SB Components UK. $4 is the generic-module estimate [U] |
| 7 | Speaker, Ø20–28 mm, 8 Ω, 1 W | 1 | 3 | 3 | 2 | [V] SparkFun 20 mm 8 Ω 1 W $1.25 — https://www.sparkfun.com/mini-speaker-1w-8-ohm.html (2026-10-28). $3 covers any Ø20–28 mm variant [U] |
| 8 | 2S 7.4 V 450 mAh ≥30 C LiPo, XT30 | 1 | 12 | 12 | 8 | [V] Radient 2S 450 mAh 30C £8.08 incl VAT — https://www.align-trex.co.uk/lipo-2s-450mah-7-4v-30c-jst-rdnb4502s30jst.html (2026-10-28) — **ships with JST; buy an XT30 variant or re-terminate** [U]. ~32 g, ~8×30×54 mm class |
| 9 | 2S balance charger, USB-C | 1 | 8 | 8 | 9.90 | [V] ISDT UC2 1S/2S USB-C £9.90 incl VAT — https://www.flyingtech.co.uk/product/isdt-uc2-1s-2s-usb-c-micro-charger/ (2026-10-28). $8 generic estimate [U] |
| 10 | Switch + XT30 pair + silicone wire | 1 | 4 | 4 | 3 | [V] XT30 male w/ 18 AWG silicone $1.99, female $1.09, m/f pair $2.59 — https://itgresa.com/product/xt30-connector-male-wires/ (2026-10-28); FingerTech Mini Power Switch $8.88 (same shop). $4 covers XT30 pair + wire + a generic mini slide switch [U] |
| 11 | 6 V 5 A UBEC/buck (servo rail) | 1 | 7 | 7 | 10.99 | [V] Hobbywing UBEC 5A V2 (5/6/7.4 V selectable) £10.99 incl VAT — https://www.3dxr.co.uk/products/hobbywing-5a-ubec-5v-6v-7-4v-2-8s-v2-air (2026-10-28); $13.99 at hobbywingdirect.com. $7 is the generic-UBEC estimate [U] |
| 12 | 5 V 1 A mini buck (XIAO + rings) | 1 | 2 | 2 | 2 | [V] MP1584 fixed-5V module $6.99 — https://www.jacobsparts.com/items/DCMOD-I-5V (2026-10-28). $2 is the generic adjustable-module estimate [U] |
| 13 | Inline blade fuse holder + 5 A fuse | 1 | 2 | 2 | 2 | [U] ~$2–7.50: Lumision MINI ATM inline holder + 5 A fuse — https://www.amazon.com/Lumision-Shipping-BLADE-Inline-Holder/dp/B00L6T1DX2 (page opened 2026-10-28; price not displayed without cart; similar holders $4.99–7.99). Fuse goes **at the pack** |
| 14 | 74LVC1G125 + 74LVC1G126 (half-duplex bus) | 1 | 1 | 1 | 0.75 | [V] 74LVC1G125 $0.21 ea — https://www.sg-micro.com/product/74LVC1G125 (2026-10-28); 74LVC1G126 £0.15 ea at Mouser UK. $1 covers both plus breakout/postage [U]. **Verify level compatibility on a bench** |
| 15 | Feetech FE-URT-1 USB adapter (servo ID setup) | 1 | 10 | 10 | 8 | [V] Seeed $10.00 — https://www.seeedstudio.com/Feetech-FE-URT-1-p-6705.html (2026-10-28) |
| 16 | PETG filament, ~250 g used | 1 | 8 | 8 | 7.99 | [V] UK 1 kg spools £7.99–13 (e.g. Buddy3D £7.99 — https://www.amazon.co.uk/Buddy3D-PETG-Printer-Filament-Blue/dp/B0GKJGJN64, opened 2026-10-28). Print uses ~113 g; a 1 kg spool covers the build plus reprints [U] |
| 17 | M2 screws + heat-set inserts kit | 1 | 10 | 10 | 8 | [V] Mardatt 230-pc M2 insert + screw kit $11.89 — https://www.amazon.com/Mardatt-Screws-Assortment-Assorted-Knurled/dp/B0DRV9R3H9 (2026-10-28). $10 estimate stands [U] |
| 18 | 6700ZZ bearing 10×15×4 | 11 | 0.55 | 6 | 5 | [U] $0.55 each is bulk-pack pricing. Retail reference: RCBearings $2.97 ea — https://rcbearings.com/product/435/ (2026-10-28); 10-packs ~$12–20 |
| 19 | Spare horns, 5264 servo leads, 26 AWG wire | 1 | 10 | 10 | 8 | [V] Waveshare 5264-3PIN cable 6-pack $1.99–3.99 — https://www.waveshare.com/product/sr-cable-5264-3pin.htm (2026-10-28). Rest is hook-up wire + horns [U] |
| | **Total (BNO085)** | | | **256** | **≈209** | |
| | **Total (MPU-6050 instead of BNO085, line 3 → ~$3/£2)** | | | **246** | **≈201** | |
| | Optional: 4 × STS3032 for hip_roll + knee | 4 | ~21.5 | +86 | +70 | [U] only if the real robot stalls at the knees. Feetech STS3032 4.5 kg·cm: €37.24 Eckstein — https://eckstein-shop.de/Feetech-STS3032-6V-45kgcm-Magnetically-Encoded-360-Degree-Serial-Bus-Servo (opened 2026-10-28); $17.55–25.35 Alibaba. **Check footprint against SCS0009 pockets before buying** |

## Totals (recomputed, real output)

```
total BNO085   USD 256
total MPU-6050 USD 246
GBP incl VAT @1.33: BNO085 GBP 193  MPU-6050 GBP 185
servos share 52%
```

With verified UK retail prices where they exist (XIAO £13.50, UBEC £10.99,
LiPo £8.08, charger £9.90, amp £5.40, PETG £7.99), the GBP totals are
**£209 (BNO085) / £201 (MPU-6050)** — inside rounding of the earlier
~£217/£207 estimate, which used £1 = $1.33 throughout.

## Where the money goes

Servos are 52 % of the BOM ($133/256). Everything else is ~$123 spread over
power ($45: battery, charger, UBEC, buck, fuse, connectors), compute and
sensors ($36), audio and lights ($11), and hardware/consumables ($31).

## Compared with the original Microduck BOM

- Removed: 15 × Dynamixel XL330, Pi Zero 2 W, Waveshare servo HAT,
  NP-F970 battery and its mount, separate camera module.
- Added: 14 × SCS0009, XIAO ESP32-S3 Sense (which now carries the camera
  *and* the mic), 2S LiPo + UBEC + buck power path, FE-URT-1 for ID setup.
- The target was about the same price (~$240) for a smaller, cheaper-servo
  robot. **The real totals are $246–256 — about 3–7 % over target.**
- If knees lack margin on the real robot (Session 5's 2.72× dynamic margin
  is the weakest), the 4 × STS3032 upgrade adds ~$86.

## Safety

> **LiPo:** balance charger only (line 9). Never leave it charging
> unattended; charge inside a LiPo bag on a non-flammable surface. Do not
> discharge below 3.3 V/cell; store at ~3.8 V/cell. Never puncture, crush
> or short the pack — retire any puffed or crash-damaged pack. The 5 A
> blade fuse sits **at the pack**, before everything else.
>
> **Soldering:** work with ventilation/fume extraction and eye protection;
> use an iron stand and never a live iron near the LiPo. Heat-set inserts
> are set with a ~200 °C+ iron tip — they stay hot for a minute; don't
> touch them or the surrounding plastic until cool.
>
> **Buck converters:** set the output (UBEC 6.0 V, mini buck 5.0 V) and
> measure it with a multimeter **before connecting anything**. A wrong
> output kills the XIAO and every servo on the rail.
>
> **Pinch points:** the joints have real torque — keep fingers out of
> knee/ankle/hip openings and the neck/head gap whenever power is on.
> First power-up: prop the robot so the feet hang free.

---

```
Original design and STL: Pollen Robotics / Microduck.
STEP reconstruction, repairs, validation and CAD sheets: tianjin66 and project contributors.
Source: https://github.com/tianjin66/microduck-step-3d-models-ai-stl
Licence: CC BY-NC-SA 4.0 — https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: uniformly scaled by 0.72; servo pockets/cradles re-cut for Feetech SCS0009; local stretches
(see SPEC.md 5.3); bearing seats changed to 6700ZZ; head shells swept-relieved internally for the
SCS0009 neck cradle (Session 3's BDX head rejected; outside shape unchanged).
```
