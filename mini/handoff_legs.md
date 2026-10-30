# Refinement B — legs & knee — handoff

Worktree `Knoll-r-legs`, branch `refine-legs`. Visual rebuild of all 12
leg-chain printed parts (hip clamshell, thigh shells, box-section shin, hip
link, ankle towers, foot shoes, soles). Kinematics untouched: `tools/spec.py`
unmodified, joint anchors/axes/ranges and all 14 SCS0009 placements identical.
`mini/HANDOFF.md` intentionally not edited.

## Authoritative joint data (assembly.joints_world)

| joint | anchor (world mm) | axis | body |
|---|---|---|---|
| left_hip_yaw | [4.32, 12.6, 80.3] | [0,0,-1] | yaw2roll |
| left_hip_roll | [16.2, 12.6, 71.3] | [1,0,0] | hip_l |
| left_hip_pitch | [2.88, 30.6, 71.3] | [0,1,0] | upper_leg_left |
| left_knee | [-22.88, 27.72, 55.46] | [0,-1,0] | leg |
| left_ankle | [-22.88, 46.44, 25.22] | [0,1,0] | ankle_left |
| right_knee | [-22.88, -27.72, 55.46] | [0,1,0] | leg_2 |
| right_ankle | [-22.88, -46.44, 25.22] | [0,-1,0] | ankle_right |
| right_hip_roll | [16.2, -12.6, 71.3] | [1,0,0] | hip_l_2 |

Leg-local pivot constants used by the builders (verified against
joints_world + the attic STLs): knee (y=15.84, z=25.76, dir -x);
ankle (y=15.84, z=-4.48, dir +x). Joint anchors are symmetric L/R.

## The ~11.4 mm right-side servo offset (reported, not "fixed")

The right knee/ankle SCS0009 cases sit ~11.4 mm rearward in the source servo
frame vs the left side. Measured: `scs0009:right_knee` world x[-44.8,-12.3]
vs `left_knee` x[-33.4,-12.3] (identical y/z extents -> pure -x shift of
11.4); in thigh-local the right knee servo spans z[15.2,47.7] vs left
z[3.8,36.3]. The shared `leg.stl` must pocket BOTH ankle servos: the right
pocket lands ~11.4 mm offset (-y) from the left pocket, so the ankle bay and
foot recesses are sized for the union of both positions. Joint anchors remain
symmetric; this is an inherited spec-frame asymmetry, documented per spec.

## What was done (geometry)

All in `tools/make_legs.py`; originals preserved in `parts/attic_refine/`.

- **Hip cluster** (`_hip_shell_local` L763, `build_yaw2roll`/`build_bearing_roll`
  L776-800): clamshell hip housing + bearing-cap drum about the roll axis.
- **Thigh** (`_shell_extrude` L801, `_thigh_shell_local` L816, `_knee_face_disc`
  L836, builders L842-854): closed tapered shell over the hip-pitch/knee
  servos; knee face disc + telescoping skirt over the shin's collar. The right
  thigh is an authored x-mirror of the left shell (`diag([-1,1,1,1])` L850).
- **Shin `leg`** (`_annulus` L866, `_shin_local` L873, `build_leg` L923):
  hollow rounded box-section (L-profile tube, ~2 mm walls, capped ends), closed
  ankle-servo bay whose mouth telescopes with the ankle drum+lip, short knee
  collar concentric with the knee axis, horn backing plate. Replaces the
  original flat plate+discs.
- **Hip link** (`_hip_link_local` L933): hip_l/hip_l_2 pitch link shells.
- **Ankle** (`_ankle_local` L951, builders L968-990): drum tower + lip ring
  about the ankle axis (top arcs clipped at the shoe deck); the case lives in
  the leg's bay.
- **Foot/sole** (`_foot_local` L993, builders L1024-1043): closed shoe shell
  with swept ankle-region recess (true swept volume of the joint hardware at
  +-45 deg, mirrored back into the right local frame) + sole pads.
- Keep-zones (horn wafers r7.2, bearing rings r11, contact pads) computed
  from the ORIGINAL parts (`keep_material` L698); servo pocket + horn-disc +
  neighbor-servo-envelope cuts in every instance's local frame
  (`pockets_local`/`neighbor_servo_cuts`/`horn_disc_local` L227-285).
- `finish()` L633: weld + degenerate/sliver drop + reloaded-file repair so
  exported STLs are watertight (coincident-face collapse on float32 export).
- `tools/render_zbuf.py` (new): true numpy z-buffer renderer used for all
  verification renders (`render_solid.py`'s painter sort misleads on dense
  shells).

## Check results (real output)

- `check_clearance.py`: **PASS** — C1 14 servos on-axis, C2 servo-servo gaps,
  C3 servo-vs-other-body <=0.2 mm, C4 height 195.7 mm < 200 cap.
- `torque_check.py` (repo `.venv`): **PASS** — stands (z 89.7 -> 84.9 mm
  settle), model mass 443.5 g in 350-450 target, 0 joints over rated torque.
- `build_mjcf.py`: builds OK; body masses total 479.6 g (printed bodies).
- Watertight on disk: **all 12 parts True.** Volumes cm3: yaw2roll 8.08,
  bearing_roll 0.69, hip_l 5.57, upper_leg_l/r 18.87/18.46, leg 19.50,
  ankle_l/r 4.26, foot_l/r 2.13/2.15, sole_l/r 3.56.
- `sweep_check.py` (all 14 joints, padded steps): **R1 OVERALL: FAIL** —
  the refined shells introduce swept-space contacts the original open
  brackets did not have (originals: full PASS). Worst residual depths:
  - `hip_roll +-22`: leg<->yaw2roll up to 17.5, bearing_roll<->hip_l ~12.3,
    leg<->scs0009:hip_roll ~8.5 mm (leg top rolls into the hip cluster).
  - `hip_yaw`: power_support<->yaw2roll ~14, leg<->trunk/power up to ~15.
  - `knee -45`: leg<->upper_leg ~13-15, scs0009:ankle<->upper_leg ~14.7,
    ankle<->upper_leg ~7 (swung-up shin/bay meets thigh shell);
    `knee +15`: leg<->yaw2roll ~15.8, ankle servo env<->thigh ~14.7.
  - `ankle +-30..-45`: sole<->leg up to ~20.6, foot<->leg ~13 (shoe recess
    floor vs bay bottom); smaller ankle<->leg ~5 contacts.
  - `hip_pitch`: hip_l<->upper_leg ~7, leg<->hip_roll servo ~3.5.
  - head joints (neck/head pitch/yaw/roll): PASS.
- `check_parts.py` wall_p10 (local thickness ray test): leg 0.80 mm (same as
  attic 0.80), upper_leg 0.50 (attic 0.72), ankle 0.45 (attic 1.12), foot
  0.42 (attic 1.23), bearing_roll 0.74 (attic 2.00), hip_l 1.44 PASS, soles
  ~2.95 PASS. Non-leg parts (power_support 0.72, m12_lens_holder 0.65,
  upper_leg_rigidity_plate 1.08) were already thin. The low leg readings
  come from telescoping rim/lip edges, not the 2 mm shell walls — print at
  >=2 perimeters; treat as a cosmetic-strength caveat, see below.

## Why no automatic clearance carving (decision)

Three keep-out strategies were implemented and rejected — every one destroys
2 mm shells before reaching PASS:

1. Swept-mesh booleans (`leg_clearance.py` driver, corridor passes): real
   cutters but terraced/ragged faces; parts fragmented, non-watertight
   (leg 19.5->7-11 cm3, soles -65%).
2. Convex-hull swept keep-outs: hulls engulf the part (leg -> ~4 cm3).
3. Sector-prism keep-outs (`_sector_prism` L480, `clearance_local` L532):
   watertight cylindrical scoops, but bounding sectors of a part moving
   under 6 joints still cover it -> leg gutted to ~0.3 cm3 even after
   per-pose box clipping. Kept in the tree as an opt-in experiment:
   `make_legs.py --corr` (default OFF; builds ship clean shells).

The honest ship state is therefore: visually closed, watertight, printable
shells with an honest documented sweep **FAIL** — not shredded shells with a
closer-to-PASS number. The correct fix is pivot-conformal surface design
(next steps), not post-hoc booleans.

## Renders (true z-buffer, `renders/zbuf/legs_final/`)

- `front/left/iso/iso2/back/right.png`: full leg chain both sides + servo
  envelopes (red). Thigh reads as a closed shell; knee shows the
  telescoping drum stack; shin is a box column; ankle servo is enclosed in
  the bay; feet are closed shoes.
- `shin_sec/` (y>=30 section): hollow shin interior, knee collar/skirt,
  bay walls, servo inside the thigh cavity.
- `foot_sec2/` (y>=30 section): concentric ankle drum+lip telescoping pair,
  ankle servo case inside the closed bay, swept recess in the shoe.

## Known limitations / next steps

- **Sweep FAIL** (detailed above). Root cause: shell material near pivots is
  fatter than the original open brackets; real collisions are localized
  (sub-cm) but pervasive across 6 joints. Proper fix: reshape the joint-adjacent
  faces as cylinders/sectors about each pivot axis (thigh lower band about the
  knee axis, shin top about knee, bay bottom + shoe recess floor about the
  ankle axis, leg top + hip cluster about roll axis) — designed surfaces, not
  carved ones. `_sector_prism`/`clearance_local` are available as a starting
  point for generating those surfaces rather than as cutters.
- Right thigh mounting face shows the offset knee servo case as a solid
  rectangle through the interface opening (left shows less — the servo sits
  11.4 mm away). The opening itself is the required insertion interface and
  is mirror-symmetric; visibility is inherent to the offset.
- Servo insertion-profile ear/pilot windows on both thigh faces (red in
  renders) — same interface openings as the original face had.
- wall_p10 regressions listed above: thin readings are at telescoping rim
  edges. If print robustness is a concern, thicken rims to >=1.5 mm or treat
  them as sacrificial cosmetic lips.
- Swept horn voids leave small stepped terraces on interior shin/bay surfaces
  (visible in sections); exterior faces are clean.
- `leg_clearance.py` remains in the tree but its output is NOT shipped; the
  shipped parts are the uncarved shells.
