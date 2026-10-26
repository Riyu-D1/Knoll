# Knoll Mini — Build & Assembly Manual

Verified against `cad/knoll-mini.FCStd` — see `cad/VERIFICATION.md` (PASS: zero
interferences across 1326 part pairs, 11/11 fit probes, 18/18 screw paths).

**Configuration:** 9× Feetech SCS0009 — 4 per leg (hip yaw, hip pitch, hip roll,
knee) + 1 neck pitch. Ankles are passive: `SOLE` + `TOE` bolt to each `FOOT`
frame and flex as the compliance element. Head yaw is fixed (v0).

## 1. Print settings (per part group)

| Group | Parts | Walls | Infill | Material |
|-------|-------|-------|--------|----------|
| Servo pockets | `HYAW_*`, `HPITCH_*`, `HROLL_*`, `KNEE_*`, `NPITCH` | 4 | 40% | PETG |
| Collar plates | `*_collar` (accent color) | 3 | 60% | PETG |
| Trunk shells | `TRUNK_F`, `TRUNK_R` | 4 | 25% | PETG |
| Head | `HEAD_SHELL`, `HEAD_BASE`, `FACE_PLATE`, `CHIN`, `EAR_*`, `EYE_*`, `ANT_MAST` | 4 | 25% | PETG |
| Feet | `FOOT_*`, `SOLE_*`, `TOE_*`, `SHIN_*` | 4 | 40% | PETG |
| Arms | `FLIPPER_*`, `FLIP_TIP_*` | 3 | 20% | PETG |

- Layer 0.2 mm, nozzle 0.4 mm. No supports — every part is oriented flat.
- **Fit-check first:** one pocket + collar pair, push a real SCS0009 in — should
  slide with light finger pressure (0.6 mm modeled clearance).

## 2. Heat-set inserts (M2 × 4 mm)

Insert holes print at **Ø3.2 mm** — soldering iron ~200 °C, press flush.
Insert locations: 2× per servo-station boss (18 total), 4× head base corners,
4× face-plate posts, trunk seam tabs, PCB/IMU standoffs, chest-panel posts.

## 3. Assembly order

1. **Feet** — `SOLE` bolts under `FOOT` frame: 4× M2×6 into the floor threads.
   `TOE` on the front face: 2× M2×12 through counterbores into the interior
   landing pad.
2. **Leg frame** — four pockets per leg in two columns (rear: `HYAW`, `HPITCH`;
   front: `HROLL`, `KNEE`). Servo drops in, collar plate clamps the flange,
   2× M2×6 per station. `SHIN` plate links foot to knee pocket (passive).
3. **Trunk** — `TRUNK_F` + `TRUNK_R` join on 4 seam screws (M2×6 through the
   seam tabs at y ±24). Interior is integral to the front half: battery tray
   (strap through the wall slots), 4 PCB standoffs, 2 IMU posts, speaker ring,
   4 chest-panel posts.
4. **Trunk interior** — strap in the 2S LiPo; ESP32/hub/buck stack on the PCB
   posts; BNO085 on IMU posts; d16 speaker press-fits the ring behind the chest
   panel; `CHEST_PANEL` screws to its posts (4× M2×6, counterbored).
5. **Neck** — `NPITCH` servo into the trunk-top pocket (collar from above).
   `NCOL_0`/`NCOL_1` collar discs stack the neck column to `HEAD_BASE`.
   Head wiring threads the hollow column bore + base cable slot.
6. **Head** — camera/ToF pods into `CAM_BRK`/`TOF_BRK` brackets behind the face
   bores; LED rings into `EYE_RING` bezels; `FACE_PLATE` on 4 corner screws;
   `HEAD_BASE` closes the shell (4× M2); `CHIN`, `EAR`/`EAR_CAP`, `ANT_MAST`.
7. **Flippers** — `FLIPPER` 2× M2 through the trunk side-wall holes;
   `FLIP_TIP` 2× M2×12 into the flipper outer face.

## 4. Wiring (see WIRING.md)

One daisy-chain: `HUB → L-leg (hyaw→hpitch→hroll→knee) → R-leg → NPITCH`.
Wires exit each pocket back-slot → trunk floor openings → up the neck column
bore → `HEAD_BASE` cable slot. Zip-tie a service loop before every joint.

## 5. QC checklist before power-on

- [ ] All 18 collar screws torqued — no servo rocks in its pocket
- [ ] SOLE + TOE screws seated; soles flat on ground (±0.5 mm)
- [ ] Battery strapped, polarity checked, **buck preset to 6.0 V**
- [ ] Every servo ID assigned via hub tool before chaining
- [ ] Neck pitch travel clear: no cable pinched in the column bore
- [ ] ToF + camera flex routed clear of the NPITCH horn sweep
