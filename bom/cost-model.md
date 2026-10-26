# Cost Model — Knoll Mk1

**Date:** 2026-10-26 (all prices) · GBP inc VAT where suppliers quote it. Line items: `bom/master-bom.csv`. Prices tagged verified / indicative / estimate in the CSV — the totals below show which parts of each total are firm.

**Reference point:** Microduck €340 billed in EUR (UK region, ~£290–295 at Oct-2026 FX) + shipping; dev pack €99.99. Its price is a *retail* price containing margin, support and assembly — ours is a *component* price. Fair comparison: our recommended-build total vs ~£300.

---

## Scenario 1 — Minimum viable prototype (MVP)

MCU-only (no SBC, no camera), import-channel servos, PLA structure, no spares:

| Group | £ | Basis |
|---|---|---|
| 10× STS3215-CN multi-pack | ~90–120 | eBay/AliExpress 6-packs ~£7–14 ea (verified channel; import lead time) |
| LiFePO4 2S pack (needed for C001 rail) | ~20 | in-spec rail for 7.4 V servos |
| Pico 2 W | 6.24 | verified |
| BNO085 → GY-521 clone (dev-grade) | ~5 | MVP compromise — noisy; upgrade path clear |
| Power parts (buck/FET/fuse/switch/conn) | ~12 | estimates |
| PCB (JLCPCB qty5) | ~8 | estimate |
| Filament PLA+TPU | ~8 | ~500 g |
| Hardware kit (screws/inserts/bearings/horns/wire) | ~45 | verified lines |
| Bus adapter (bench tool) | 10.90 | verified |
| Battery charger | ~10 | verified |
| **Total** | **≈ £215–235** | of which ~£120 verified prices |

Compromises: no onboard compute (USB-tether policy host), dev-grade IMU, CN lead times, no spare servo.

## Scenario 2 — Recommended reliable prototype ★

ST3020 servos on direct 2S, Pi Zero 2 W, BNO085, PETG-CF structure, 2 spare servos:

| Group | £ | Basis |
|---|---|---|
| 10× Waveshare ST3020 | 194 | verified UK singles (£19.40 Pi Hut) |
| 2× spare ST3020 | 38.80 | spares kit |
| Pico 2 W + Pi Zero 2 W | 20.64 | verified |
| BNO085 | 28.40 | verified |
| Power chain (battery 16 + charger 10 + buck 3.64 + FET/fuse/switch/conn/caps ~9) | ~39 | mostly verified |
| PCB + discretes | ~12 | estimate |
| 2S LiPo 2200 + charger | (incl. above) | verified |
| Filament (PETG-CF + PLA + TPU) | ~15 | verified kg prices, ~640 g used |
| Hardware kit | ~48 | verified lines (screws/inserts/bearings/dowels/horns/washers/threadlocker) |
| Wiring/connector kits | ~35 | verified |
| Bus adapter + microSD + eyes + misc | ~27 | verified/estimate |
| **Total** | **≈ £340–360** | ~75% verified pricing |

**vs Microduck ~£300 retail:** we are roughly at parity on parts alone — BUT the comparison isn't apples-to-apples: Microduck's retail price contains their servo OEM discount (15× XL330 ≈ $375+ at retail). Our honest position: **comparable cost for a fully open-hardware, repairable design — or ~£260–280 with import-channel ST3020s** (same part, AliExpress, ~£13 ea → servo line drops to ~£130, total ≈ £280–300). Cheaper MVP path ≈ £215.

## Scenario 3 — Performance configuration

Recommended + knee-margin headroom + options:

| Delta | £ |
|---|---|
| 10× STS3215-C018 instead of ST3020 (+£4.92 ea) | +49 |
| 3S LiPo 2200 (+~£6) + charger still B3-compatible | +6 |
| Pi Camera Module 3 | +24 |
| 4× foot switches | +2.40 |
| MAX98357A + speaker | +9 |
| STS3032 head-servo ×2 (regulated tap required) | +49 |
| **Total** | **≈ £480–500** |

Gains: published 0.98 N·m knee continuous margin, camera + audio + head capability. Cost: +35%.

## Scenario 4 — Batch-10 indicative (per unit)

Multi-packs, JLCPCB qty≥10 (~£1/board), AliExpress servos, shared shipping:

| Group | £ |
|---|---|
| ST3020-equivalent ×10+1 | ~120 |
| Electronics set | ~60 |
| Power+battery+charger | ~35 |
| Filament+hardware | ~50 |
| **≈ £265/unit** | plus NRE (PCB respin, jigs) amortized |

## Top-3 cost drivers + levers

| # | Driver | Share | Lever | Saving |
|---|---|---|---|---|
| 1 | Servos | 55–65% | CN multi-pack vs UK singles | ~£60–100 |
| 2 | Compute+IMU | ~15% | BMI270 vs BNO085 (−£10); drop SBC (−£14) | ~£10–25 |
| 3 | Battery+charger+harness | ~15% | builder-owned charger; 18650 DIY pack | ~£10–20 |

## Missing/hidden costs (honesty section)

- Tools-from-zero: +£70–170 (not in robot cost — most builders own some).
- LiPo shipping surcharges possible (courier battery rules).
- Failed prints/reprints: +10–15% filament real-world.
- Servo lead-time risk: Pi Zero 2 W + ST3020 stock fluctuates — buy early.
- Import orders >£135 attract courier VAT+duty+handling — split servo orders if needed.
- The 12th+ servo (head/aux) is NOT in scenarios 1–3 base — +£19–29 each when added.

## Mass roll-up (recommended build, estimate)

| Group | g |
|---|---|
| 10× ST3020 | ~580 |
| Structures+feet+bearings+fasteners | ~180 |
| Chassis plate+PCB+SBC+IMU+wiring | ~110 |
| Battery | ~112 |
| Dome+face+hatch | ~110 |
| **Total** | **~1.09 kg** — inside the 1.15 kg knee-margin gate, tighter than we'd like; mass watch is a design requirement |
