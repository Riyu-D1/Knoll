# Session 8A — BDX head shape (handoff)

Replaces the outer head dressing with a Disney-BDX-droid-style enclosure.
Everything functional is untouched: all 14 SCS0009 servos, joint axes and
ranges, neck + neck frame, yoke/mounting interfaces, screw-boss
relationships, camera axis and electronics bays. Only the skin changed.

## What changed

- `spec.HEAD_MODE = "bdx"`; `spec.HEAD_REPLACE_PARTS` keeps
  `m12_lens_holder` (camera-axis part) and drops the old dressing
  (`top_head_shell`, `bottom_head_shell`, `face_part`, `jaw`,
  `jaw_soft`, `soft_mouth_top`, `noenoeil` — all archived in
  `parts/attic_head_orig/`, nothing deleted).
- New deterministic generator `tools/make_head_bdx.py` (trimesh +
  manifold3d booleans, no hand-edited STL): builds the shell as
  `outer_solid(0) − outer_solid(−2.0)` so every wall is 2.0 mm even
  across chamfers, sweeps the moving head-chain point cloud (cached at
  /tmp/head_bdx_cloud.npz), derives the neck opening from the swept
  floor slab by raster dilation/closing + contour extraction, then
  splits the clamshell at lx = −3.0 with a +2 mm skirt overlap.
- `spec.BDX_HEAD_PARTS` = `top_head_shell`, `bottom_head_shell`,
  `head_eye_lens_l`, `head_antenna_left`, `head_antenna_right` —
  authored in the jaw_soft frame, loaded by `assembly.py` only in bdx
  mode. `elec_eye_rings_x2.stl` regenerated as the LED-ring placeholder
  behind the left eye.
- `tools/render_solid.py`: added `h_*` view presets (front/back/left/
  right/top/bottom/tq/cutaway). NB the legacy `front`/`back` presets are
  mislabeled vs the real robot axes — the face is +x, so the true front
  is `h_front` (azim 0); `front.png` (azim 180) actually shows the rear.

## Design (xgoduck structural principles, no meshes copied)

The xgoduck head taught: (1) roomy helmet shell around the servo
cluster — the shell carries no servo loads, chassis does; (2) one-piece
top + closing bottom plate; (3) neck servo stack rises through a bottom
opening slightly behind center. Same here:

- Outer box 67.5 (ly) × 92.7 (lz) footprint, lower-right trapezoidal
  wedge flare where the neck_frame/neck_pitch sweep exits low; raised
  top panel over the one swept high patch (yaw_roll_motion tips,
  lx 29.6).
- Face (+lz outward = world +x): two Ø20 mm raised bezels (Ø16 mm
  bores); right/center eye at ly = 0 carries the Ø10 mm camera aperture
  on the camera axis (world y 0, z 180.8 — lens holder sits directly
  behind it); left eye at ly = −19.5 carries the LED lens + ring
  placeholder. Small Ø8 mm lamp at ly +18, Ø2 mm mic hole at ly −16.
- Vent grilles: Ø1.7 mm holes through both front corner chamfers +
  a top-face grille patch; front-bottom edge chamfer (the BDX chin
  line), full-depth back.
- Antennae: Ø2 mm rods, 12 mm long, tilted ±30° outward in Ø2.2 mm
  sockets on the top corners; tips world z = 200.7.
- Clamshell: horizontal split at lx = −3.0, skirt skirt-band overlap
  to lx −5.4; six horizontal self-tap seam screws (Ø2 pilots) into pads
  inside the bottom rim; two rear chassis tabs sit against
  `motor_support` (self-tap into its back face) fixing the shell to the
  head chassis.
- Neck opening: non-convex raster-derived contour, swept footprint +
  2 mm margin, through the floor plate and lower wall band to lx = −9 —
  the helmet opening the neck stack enters through (as xgoduck).

## Measured numbers (assembled)

- Head bbox: 99.0 deep × 74.5 wide × 47.8 tall mm (z 154.6..202.4)
- Total robot height: 195.2 mm (z 7.2..202.4; cap 200 via C4) 
- Printed head parts: 47.9 cm3 -> ~33.4 g (top 33.0, bottom 13.4,
  lens 1.45, antennae 0.04 each) — was ~23.5 g of old dressing (+9.9 g)
- jaw_soft body mass (head incl. servos+electronics): 80.5 g
- Total model mass: 438.8 g (target 350–450)
- Swept clearance, whole head chain vs shell material: min 1.15 mm,
  0 material hits, 0 flags < 1 mm (generator step [8]).
- Contents vs shell: head_roll 2.45 mm, elec_buck 1.5 mm, other
  electronics 6.5–9 mm; motor_support min 0.81 mm with 2 flags at
  lz = 32.7 — that is the intended chassis-tab mounting interface
  (pads bridge to the back wall; screws go through them into
  motor_support). 0 material hits anywhere.

## Checks (real output)

check_clearance:
```
C1 servos placed=14 on-axis-and-matching-joint-list: PASS
C2 servo-servo gaps (need >= 2.0 mm):
   C2 PASS
C3 servo case/ears vs parts of other bodies (max penetration 0.2 mm):
   C3 PASS
C4 height=195.2 mm (cap 200.0) PASS
OVERALL: PASS
```

check_parts (new head parts only — all PASS):
```
PASS bottom_head_shell  watertight=True ext=[12.  72.5 92.7] wall_p10=2.00mm
PASS top_head_shell     watertight=True ext=[38.2 73.6 99. ] wall_p10=2.00mm
PASS head_antenna_left  watertight=True ext=[11.4  7.7  2. ] wall_p10=1.99mm
PASS head_antenna_right watertight=True ext=[11.4  7.7  2. ] wall_p10=1.99mm
PASS head_eye_lens_l    watertight=True ext=[19.6 19.6  7. ] wall_p10=1.40mm
```
Overall FAIL from pre-existing thin walls on untouched leg/foot/older
parts (ankle_left/right, leg, sole_left/right, upper_leg_left/right,
upper_leg_rigidity_plate, power_support, m12_lens_holder) — all files
unmodified by this session; not introduced here.

sweep_check (each joint alone over its required range, step 10 deg):
```
head_yaw    swept -120..+120 deg: PASS
head_roll   swept  -25..+25  deg: PASS
head_pitch  swept  -45..+45  deg: PASS
neck_pitch  swept  -45..+45  deg: PASS
R1 OVERALL: PASS
```

head_protrusion (visibility through shell openings):
```
neck_pitch  1804/3185 visible  [neck region]   (neck servo below head — by design)
head_pitch  1458/3185 visible  [neck region]   (mounted in neck — by design)
head_yaw      80/3185 visible  right 21.7mm    (through neck opening only)
head_roll    301/3185 visible  bottom 21.8mm   (through neck opening only)
```
Verified by sampling: every visible point lies inside the neck-opening
footprint at the vestibule band — the servos are only exposed when
sighting straight up the intended neck entry, exactly like xgoduck's
servo stack through its bottom opening and the original chin. No servo,
horn or ear pokes through any shell wall, seam or feature.

torque_check:
```
model mass = 438.8 g (target 350-450 g incl. electronics)
[STAND] T1 stood=PASS (z 87.2 -> 85.2 mm)
[STAND] T2 PASS; joints over rated 0.069: 0
OVERALL: PASS
```

Exported STL validation (trimesh reload): top watertight, all edges
count 2, +32.97 cm3; bottom watertight, all edges count 2, +13.39 cm3;
antennae/lens/rings watertight. 6300-ray probe through the top shell:
0 unpaired hits -> no unintended top openings.

## Renders (all inspected vs ref_bdx_head.png)

`renders/solid/head_bdx/` — h_front (eyes+lamp+mic on face, lower-front
chamfer), h_back (flat rear, two pilot dimples), h_left / h_right (flat
walls, front-corner chamfers, seam line), h_top (raised panel, antenna
sockets, grille patch), h_bottom (floor plate + neck opening +
vestibule), h_tq (the BDX shot), h_cutaway (sagittal cut at y=0
through the camera eye — contents enclosed, camera aperture open),
front + three_quarter (whole robot), h_tq_yaw120 + h_bottom_yaw120
(extreme yaw — shell still covers the neck passage).

Matches the reference: wide flat boxy lid, flat top with raised panel,
two round eyes in raised bezels, side vent grilles, small lamp, two
antenna rods at the corners, chamfered lower-front edge, deeper back,
helmet overhang.

## Caveats

- Eyes are not perfectly symmetric: the camera axis is fixed at ly = 0,
  so the pair (ly 0, −19.5) sits slightly right of center; the left eye
  is the LED/display eye.
- Through the bottom neck opening you can glimpse yaw/roll servo
  undersides and neck hardware at grazing below-angles — same exposure
  class as the xgoduck helmet and the original chin (the neck must pass
  through there).
- Grille holes are Ø1.7 mm — subtle at render resolution but real
  through-holes.
- Legacy `front`/`back` render presets are mislabeled (see above);
  use the `h_*` set.
- `mini/model/*.xml` regenerated (build_mjcf.py) but intentionally not
  committed.
