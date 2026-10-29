# Refinement B — legs & knee — handoff

Worktree `Knoll-r-legs`, branch `refine-legs`. Visual rebuild of all 12 leg-chain
printed parts (hip clamshell, thigh shells, box-section shin, hip link, ankle
yokes, feet, soles). Kinematics untouched: `tools/spec.py` unmodified, joint
anchors/axes/ranges and all 14 SCS0009 placements identical.

## What was done

- `tools/make_legs.py` (new): per-STL generator — authored build123d shells
  (tapered thigh extrusions, hip clamshell, box-section shin w/ strut+knee wall,
  ankle yoke, foot shells, sole pads), interface keep-zones (horn wafers r7.2,
  bearing rings r11, contact pads) computed from the ORIGINAL parts in
  `parts/attic_refine/`, servo pocket + horn-disc + neighbor-servo-envelope
  cuts, right-side local mirroring. Shared STLs aggregate all instances.
- `tools/leg_clearance.py` (new): batch driver over the same contact machinery
  as `sweep_check.py`. Finds NEW moving-vs-static contacts per leg joint, then
  subtracts the swept mesh of the other part (or the SCS0009 envelope incl.
  horn, grow 0.4) from MY parts only — both sides of each pair, at padded 5 deg
  steps, with keep-zones subtracted from the cutter. Run repeatedly converges;
  some residuals remain (below).
- Original STLs preserved in `parts/attic_refine/`.

## Check results (real output)

- `check_clearance.py`: **PASS** (C1 14 servos, C2 gaps, C3 0.2mm, C4 h=195.7<200)
- `build_mjcf.py`: builds OK; total mass 443.5 g
- Watertight on disk: all 12 parts True.
  Volumes cm3: yaw2roll 5.86, bearing_roll 0.48, hip_l 5.57, upper_leg_l/r
  14.96/13.43, leg 4.56, ankle_l/r 3.01, foot_l/r 3.65/3.50, sole_l/r 2.82/1.96.
- `sweep_check.py`: **FAIL (residual)** — carving removed most collisions
  (worst depths dropped 23mm → ~1-4mm on many pairs) but contacts remain at:
  hip yaw/roll/pitch (1.3-4.2mm near hip cluster + trunk), knee (leg↔thigh
  1.3-3.9mm, shin↔rigidity-plate 3.7mm), ankle (foot/ankle↔servo case 1.3-12.9mm
  — residual sits inside/at the horn-disc radius which must stay for the
  mount). Restoring watertightness on hip_l/ankle_left/ankle_right required
  reinstating their uncarved shells, so their collisions are un-cut.
- Known non-issue: right-knee servo case sits 11.4mm further back than left
  (spec servo-frame inherent; joint anchors symmetric). Reported, not "fixed".

## Known limitations / next steps

- Sweep residuals: the remaining contacts are inside or adjacent to keep-zones
  (horn faces, bearing seats) or the horn disc. Proper fix is reshaping joint
  faces as cylinders about each pivot axis (thigh top, shin top, ankle wall,
  foot top) rather than more boolean carving; boolean artifact rate rises as
  parts thin.
- Carved notches on thigh/housing/shin/foot surfaces are visible on close
  inspection; horn-face discs remain clean.
- `finish()` meshfix path needs pymeshlab (repo .venv now has it); two parts
  resisted all repair paths and were reverted to their pre-carve shells.
