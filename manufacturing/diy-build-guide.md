# DIY Manufacturing & Buildability — Knoll Mk1

**Date:** 2026-10-26 · **Status:** Manufacturing plan + sourcing + assembly strategy. Research evidence in `manufacturing/notes-manufacturing.md` (verified UK prices 2026-10-26). Nothing here is yet print- or assembly-validated.

---

## 1. Manufacturing assumptions

Builder has: a hobby FDM printer (≥180×180 mm bed, Bambu/Prusa/Ender class), basic hand tools, soldering ability, no CNC. ~£70–170 of tools if starting from zero (soldering iron, hex drivers, calipers, multimeter — full list in notes §7).

## 2. Material strategy (justified in notes §1)

| Part class | Material | Why | ~Mass | ~Cost |
|---|---|---|---|---|
| Structural load-path (leg links, joint blocks, hip blocks, chassis plate) | **eSUN PETG-CF** £21/kg | ~2× PETG stiffness, tough (survives demo falls), better creep, prints open-frame | ~400 g | ~£8 |
| Cosmetic (dome, face plate, hatch, topper) | PLA Basic £11–14/kg | colour + detail; carries no load | ~150–200 g | ~£3 |
| Feet soles, bumpers, grommets | TPU 95A £15–20/kg | grip + sacrificial drop protection | ~40 g | ~£1 |
| MVP alternative | eSUN PETG-Basic or PLA £11/kg | Open Duck Mini proves plain PLA works at this scale | ~600 g | ~£7–8 |

**Creep honesty:** all common filaments stress-relax under clamped joints; data is contradictory on which is worst. The engineering fix is design, not material: **joint loads through metal** (dowel pins, washers, through-bolts into heat-set inserts); plastic never carries sustained clamping. Validation coupon test (2-week clamped-joint creep) is roadmap item P2-adjacent.

## 3. Print rules (structural parts)

- 4–6 walls, 5 top/bottom, 40–60% gyroid (joint blocks 60–100% local infill); 0.2 mm layers.
- **Orientation beats infill:** layer-adhesion is 29–55% of in-plane strength — print leg links flat so loads run along layers.
- Heat-set inserts M3×5×4 (Voron spec) at every serviceable thread; boss OD ≥9 mm; never thread raw plastic.
- Holes print 0.1–0.2 mm undersize: CAD-compensate +0.15–0.2 mm or ream.
- Bearing seats: slip-fit + retainer plate (±0.08 mm print scatter makes press-fits inconsistent); 6700ZZ-class joint idlers.
- Total print: ~600–700 g filament, ~30–60 h (4–7 printer-days). CF filament needs hardened nozzle (£5–15).
- No glue in load paths; threadlocker on metal-to-metal only.

## 4. Buy-don't-print list

Servos, bearings (6700ZZ/MR126ZZ), dowel pins 3–4 mm, M2.5/M3 screws+nuts, heat-set inserts, 25T metal servo horns for high-load joints, 5264-3A connectors/pigtails, silicone wire (20 AWG trunk / 24 AWG signal), battery, all electronics, TPU soles COULD be printed (do print them). Everything else printed.

## 5. Assembly sequence (aligned to `design/mechanical-architecture.md` §5)

```
STEP 0 — Bench-configure servos FIRST (Open-Duck pattern):
  each servo on the £10.90 bus adapter → set ID + baud + verify
  range/temp readback BEFORE any screw turns. Record offsets.
STEP 1 — Leg modules ×2 (mirror): foot → ankle → shank → knee →
  femur → hip block; slack loops at every joint crossing;
  slack-loop + heat-shrink strain relief on every lead.
STEP 2 — Chassis plate: KCB-1 board + standoffs, battery sled,
  IMU at centreline, SBC; legs bolt on (4× M3 + keyed connector).
STEP 3 — Harness: bus A/B to PCB, VBAT, eyes, e-stop loop check.
STEP 4 — Dome + face plate + hatch LAST (panels before guts rule).
STEP 5 — Firmware flash, cal pose on alignment jig, joint-zero
  verification vs keyframe (the #1 sim2real failure source).
```

- Design targets: ≤80 screws total, leg swap <10 min, every servo reachable by removing its strut pair, battery swaps tool-free through the rear hatch.
- Print alignment jigs/witness marks so joints assemble at known angles (ToddlerBot zero-point pattern).

## 6. Failure points & repair plan (ranked by expected incidence)

| Failure | Prevention in design | Repair | Spare |
|---|---|---|---|
| Servo lead fatigue at hip/knee | printed channels + service loops, never across joint axis | re-terminate or swap lead ~£1 | 5× leads £5 |
| Horn/spline strip | metal 25T horns at knee/ankle/hip | swap horn £3–5 | 2× horns £8 |
| Gearbox tooth strip | firmware current limits, limp-fall | whole-servo swap ~£19–26 | **2× spare servos £40–50** |
| TPU sole wear/cracks | sacrificial by design | reprint ~£1 + 2 h | filament |
| Insert pull-out | ≥9 mm bosses, washers under every screw | re-seat + epoxy; boss redesign if repeat | surplus from kit |

**Spare kit ≈ £50–60** — built into the recommended-build BOM.

## 7. Sourcing summary (UK-accessible, dated 2026-10-26)

- Servos: UK singles £19.40–29 (Pi Hut/RobotShop/RC Hobby); **CN multi-packs via AliExpress/eBay ≈ £7–14 ea — the channel choice swings the servo bill £80 vs £350.** AliExpress collects UK VAT at checkout <£135 (no doorstep fees).
- PCB: JLCPCB economy £4–8 landed; order each design separately.
- Battery/charger: 2S LiPo 2200 £15–17; B3 charger £7–18.
- Full line items in `bom/master-bom.csv`; all four cost scenarios in `bom/cost-model.md`.

## 8. Repairability commitments (design requirements checklist)

- [x] Modular legs/head on keyed connectors
- [x] Toolless battery + external hatch for all ports
- [x] Every servo bench-configurable + reachable
- [x] Sacrificial parts identified and cheapest to reprint
- [x] Published STL + print profiles per part class
- [x] Spare parts kit costed in BOM
- [ ] Assembly guide with torque spec + cal jig (roadmap P5.3)
