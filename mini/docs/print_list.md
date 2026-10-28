# Knoll Mini — print list (Session 8A, BDX head)

Every printable STL in `mini/parts/current/` (28 files, 33 pieces).
The `elec_*` STLs are non-printed electronics placeholders and are
excluded. Slicer settings: **PETG, 0.2 mm layer, 3 walls/perimeters,
20 % gyroid infill**, no raft; brim on parts under ~20 mm tall or under
~15 cm2 footprint. Supports: none except where noted — every part was
re-oriented to print clean at these settings.

Mass estimate: `grams = volume_cm3 x 1.27 g/cm3 x 0.55` (PETG density x
effective fill factor) — same formula as `mass_budget.md`.

Session 8A: the Microduck head dressing (face_part, jaw, jaw_soft,
soft_mouth_top, noenoeil, and the old top/bottom shells) moved to
`parts/attic_head_orig/` — replaced by the BDX clamshell
(top_head_shell + bottom_head_shell), two antenna rods and the LED eye
lens. All functional head parts (motor_support, m12_lens_holder,
yaw_roll_motion, neck parts, servos) are unchanged.

## Computed volumes and masses (real trimesh output)

```
part                         qty   vol_mm3  g_each  g_line  dims_mm
ankle_left                     1      2198     1.5     1.5  37.4x26.3x18.4
ankle_right                    1      2198     1.5     1.5  37.4x26.3x18.4
banana_pcb_locker              1       172     0.1     0.1  38.9x2.7x4.8
bearing_roll                   2       4340     3.0     6.1  17.2x23.9x33.4
bottom_head_shell              1      13386     9.4     9.4  12.0x72.5x92.7
foot_left                      1       3701     2.6     2.6  28.9x38.9x12.2
foot_right                     1       3701     2.6     2.6  28.9x38.9x12.2
head_antenna_left              1        38     0.0     0.0  11.4x7.7x2.0
head_antenna_right             1        38     0.0     0.0  11.4x7.7x2.0
head_eye_lens_l                1      1446     1.0     1.0  19.6x19.6x7.0
hip_l                          2       1689     1.2     2.4  23.4x24.8x13.7
leg                            2       2293     1.6     3.2  31.3x25.1x43.4
left_shell                     1       4181     2.9     2.9  24.3x58.2x30.0
m12_lens_holder                1       410     0.3     0.3  17.3x10.7x11.5
motor_support                  1       8666     6.1     6.1  49.0x64.6x18.9
neck_frame                     1      19017    13.3    13.3  33.1x55.2x35.7
neck_pitch                     1       2005     1.4     1.4  40.0x19.0x23.0
power_support                  1       2735     1.9     1.9  39.2x12.2x60.1
right_shell                    1       3450     2.4     2.4  22.9x48.9x30.0
sole_left                      1       1746     1.2     1.2  29.6x38.9x9.3
sole_right                     1       1746     1.2     1.2  29.6x38.9x9.3
top_head_shell                 1      32971    23.0    23.0  38.2x73.6x99.0
trunk_base                     1      11666     8.1     8.1  42.0x33.1x31.7
upper_leg_left                 1      13288     9.3     9.3  31.3x34.3x47.5
upper_leg_right                1      13629     9.5     9.5  31.3x34.3x58.9
upper_leg_rigidity_plate       2       502     0.4     0.7  2.4x32.4x38.6
yaw2roll                       2       3875     2.7     5.4  16.7x22.6x33.4
yaw_roll_motion                1       7620     5.3     5.3  33.1x25.8x28.8
TOTAL                         33     175405           122.5
parts=28 files, pieces=33, excluded(non-printed)=elec_*, hardware_*, NON_PRINTED
```

Reproduce with:

```python
import trimesh
m = trimesh.load("parts/current/<name>.stl", force="mesh")
grams = m.volume / 1000.0 * 1.27 * 0.55   # volume mm3 -> cm3
```

## Orientations (suggested)

| part | qty | suggested orientation |
|---|---|---|
| trunk_base | 1 | as assembled, open side up |
| left_shell / right_shell | 1 ea | outer (curved) face down on bed |
| power_support | 1 | long edge down, standing |
| banana_pcb_locker | 1 | flat |
| yaw2roll / bearing_roll | 2 ea | flat side down |
| hip_l | 2 | flat side down |
| upper_leg_left / upper_leg_right | 1 ea | standing as assembled |
| upper_leg_rigidity_plate | 2 | flat |
| leg | 2 | standing, cradle opening up |
| ankle_left / ankle_right | 1 ea | flat face down |
| foot_left / foot_right | 1 ea | flat (sole face) down |
| sole_left / sole_right | 1 ea | flat down |
| neck_frame | 1 | flat back down |
| neck_pitch | 1 | flat side down |
| yaw_roll_motion | 1 | flat face down |
| motor_support | 1 | plate face down |
| top_head_shell | 1 | rim (seam plane) down, face pointing sideways; supports buildplate-only if needed for the eye bezels |
| bottom_head_shell | 1 | split-plane face down (flat), neck opening up |
| head_eye_lens_l | 1 | flat |
| head_antenna_left / right | 1 ea | flat, brim recommended (thin rods) |
| m12_lens_holder | 1 | flat |

## Batch notes

- Print one `yaw2roll` first and test-fit a real SCS0009 before running
  the batch — the cradle ear pilots are Ø1.6 mm self-tapping.
- Mirrored pairs (`foot`, `sole`, `ankle`, `upper_leg`) are separate
  STLs — do not mirror-print one to save a file.
- The BDX clamshell closes with six self-tap screws through the seam
  pilot holes (two per side wall, two on the front wall) into the seam
  pads inside the bottom rim; two screws from the back wall into the
  `motor_support` chassis tabs fix the shell to the head chassis.
- 33 pieces ≈ 122.5 g net; budget ~270 g of spool including skirts, brims
  and one or two failed prints.

---

```
Original design and STL: Pollen Robotics / Microduck.
STEP reconstruction, repairs, validation and CAD sheets: tianjin66 and project contributors.
Source: https://github.com/tianjin66/microduck-step-3d-models-ai-stl
Licence: CC BY-NC-SA 4.0 — https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: uniformly scaled by 0.72; servo pockets/cradles re-cut for Feetech SCS0009; local stretches
(see SPEC.md 5.3); bearing seats changed to 6700ZZ; Session 8A replaces the outer head shells with a
deterministically generated BDX-style clamshell (tools/make_head_bdx.py) — structural approach inspired
by the xgoduck head (helmet shell + bottom neck opening, shell carries no servo loads). Old shells in
parts/attic_head_orig/.
```
