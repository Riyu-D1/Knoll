# Knoll Mini — Build & Assembly Manual

## 1. Print settings (per part group)

| Group | Parts | Walls | Infill | Supports | Material |
|-------|-------|-------|--------|----------|----------|
| Servo pockets | `*_{HYAW,HROLL,HPITCH,KNEE,ANKLE}_{floor,cheek,back,boss}` | 4 | 40% | No — orient flat | PETG |
| Collar plates | `*_collar` | 3 | 60% | No | PETG |
| Trunk shells | `TRUNK_F`, `TRUNK_R` | 4 | 25% | No — seam face down | PETG |
| Head | `HEAD_SHELL`, `HEAD_BASE`, `FACE_PLATE` | 4 | 25% | Face plate: none | PETG |
| Feet | `FOOT_*`, `SOLE_*`, `TOE_*` | 4 | 40% | No | PETG |
| Flippers | `FLIPPER_*`, `FLIP_TIP_*` | 3 | 20% | No | PETG |
| Trays/posts | `BAT_*`, `PCBP_*`, `IMUP_*`, `PANP_*`, `SEAM_*` | 3 | 40% | No | PETG |
| Links | `FEMUR_*`, `SHIN_*` | 3 | 30% | No | PETG |

- **Layer height** 0.2 mm; **nozzle** 0.4 mm; print all `*_collar` in accent color.
- **Print-first fit check:** `KNEE_L_floor` + `KNEE_L_cheek±1` + `KNEE_L_back` + `KNEE_L_collar`
  + `KNEE_L_boss0/1` — push a real SCS0009 in; it should slide with light finger pressure.
  If tight, re-print pocket walls at −0.2 mm.

## 2. Heat-set inserts (~60× M2)

Insert holes are printed at **Ø3.2 mm**. Set with a soldering iron at ~200 °C — press
straight, stop flush with the surface. All locations are modeled (brass objects in the
`HARDWARE` collection): 2× per servo station (24 leg + 2 neck), 6× trunk seam, 4× head
corners, 4× face plate posts, 8× feet, 4× flippers, 2× neck collars, posts for panel/PCB/IMU.

## 3. Assembly order

1. **Feet** — `SOLE` screws up into `FOOT` (4× M2×6, inserts in foot top face). Press `TOE` on.
2. **Ankle station** — servo into pocket → `collar` → 2× M2×6. Servo horn bolts to foot frame.
3. **Leg links** — repeat up the chain: `SHIN` cover clips between ankle collar and knee
   pocket; `KNEE` station → `FEMUR` → `HPITCH` → `HROLL` → `HYAW` (all same pocket/collar).
4. **Trunk** — set all 6 `SEAM` inserts; `TRUNK_F` + `TRUNK_R` join with 6× M2×6.
5. **Trunk interior** — battery tray walls are integral; drop `2S LiPo` in, strap it; `PCB` on
   4 `PCBP` standoffs (M2); `IMU` on `IMUP` posts; speaker press-fits `SPK_RING`; `CHEST_PANEL`
   on 4 `PANP` posts.
6. **Neck** — `NPITCH` into ceiling pocket (inside trunk top); `NYAW` between two `NCOL`
   collar rings (2× M2 each) — bottom collar to trunk top, top collar to `HEAD_BASE`.
7. **Head** — camera + ToF pods into their brackets behind the face bores; LED rings behind
   bezels; `FACE_PLATE` on 4 corner screws; `HEAD_BASE` + `HEAD_SHELL` screw at 4 corners;
   antenna press-fit.
8. **Flippers** — 2× M2 each side into trunk inserts.

## 4. Wiring (see WIRING.md for full map)

One servo daisy-chain: `HUB → L-leg (hyaw→hroll→hpitch→knee→ankle) → R-leg (same) → neck`.
Wire exits each pocket's back slot → routes up inside trunk → head flex runs through the
`NECK_CABLE` channel + `HEAD_BASE` slot. No wire crosses a moving joint's pinch zone.

## 5. QC checklist before power-on

- [ ] All 24 collar screws torqued (servos can't rock in pockets)
- [ ] Feet clear by ≥4 mm through full hip-roll range
- [ ] Servo horns on correct splines (home pose = legs parallel, head centered)
- [ ] Battery strapped, polarity checked, buck set to **6.0 V** before connecting servos
- [ ] Each servo ID assigned before chain power-on (hub tool)
- [ ] ToF + camera cables clear of neck yaw travel (±180°)
