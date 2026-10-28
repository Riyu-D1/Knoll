# Knoll Mini (Microduck ×0.72): SPEC

The fixed design contract. All numbers also live in `mini/tools/spec.py`, which the tools read, so change them **there** and log each change in section 12.
Marker meanings:
- **[V]**: verified on 2026-10-27, either from the upstream XML/STL or by running the tools.
- **[U]**: unverified estimate. Measure or confirm it before relying on it.

## 1. Goal
A cheaper, smaller Microduck:
- **Height:** 15–20 cm. Target is 192.6 mm at the S=0.72 baseline [V].
- **Servos:** 14 Feetech SCS0009 replace the 15 Dynamixel XL330. The mouth servo is dropped.
- **Body, legs and neck:** same joints, same axes and same kinematics as Microduck. Every part is uniformly scaled by S, then locally modified only where the smaller servo needs it.
- **Head:** the ORIGINAL Microduck head (the 8 upstream STLs, scaled ×0.72) on the unchanged head_roll interface, relieved internally only where the SCS0009 hardware sweeps it. The Session-3 BDX head was rejected — see section 7.

## 2. Sources and pinning
| What | Where | Pin |
|---|---|---|
| Microduck MJCF + meshes (metres) | github.com/pollen-robotics/microduck_rl `src/mjlab_microduck/robot/microduck/` | commit `29e887ecfbf5d37144759e5a9f8a176dfb83d547` [V] |
| Microduck STLs (mm, = MJCF meshes ×1000 [V]) | github.com/tianjin66/microduck-step-3d-models-ai-stl `01_STL_original/` | HEAD `bf96450` [V] |
| Work repo | github.com/Riyu-D1/Knoll | branch `build/microduck-bdx-mini`, created from `main` (`d3f6b0e`) |

`mini/tools/fetch_upstream.sh` clones both upstream repos into `mini/third_party/`, which is git-ignored. Never edit anything in `third_party/`.

## 3. Repo layout (inside Knoll, branch `build/microduck-bdx-mini`)
```
mini/SPEC.md  mini/HANDOFF.md  mini/LICENSE-MESHES.md
mini/tools/            spec.py (numbers), assembly, scs0009, scale_parts, check_clearance, check_parts,
                       sweep_check, search_layout, pocket_part, swept_cut, where, stretch_mesh, idler_boss,
                       thicken_plate, merge_body_frame, make_bdx_head, build_mjcf, torque_check, render_views
mini/third_party/      upstream clones (git-ignored)
mini/parts/scaled/     S-scaled originals (Session 0; never edited afterwards)
mini/parts/current/    the parts in use (Sessions 1–3 modify these)
mini/parts/lib/        scs0009 envelope/cutter/cradle STLs
mini/model/            knoll_mini.xml + scene_knoll_mini.xml (Session 4)
mini/renders/          PNG views
mini/docs/             BOM, wiring, assembly (Session 5)
```

## 4. Frame, units, scale
- **Units:** mm everywhere in tools and STLs. The MJCF uses metres, and `build_mjcf.py` converts.
- **World frame:** the Microduck MJCF world at zero pose. +X is forward (where the face looks), +Y is robot-left, +Z is up. The trunk origin is at z = 120 mm at full scale [V].
- **Scale:** S = 0.72 [V]. Scaling is about the world origin, and every part STL is scaled about its own origin by S. This matches the MJCF, where geom positions ×S are the meshes ×S.
- **Size:** the full-scale envelope is 144 × 141 × 264 mm and the mass is 737 g [V]. At S=0.72 the height is 192.6 mm with the stretches below [V], and the model mass is ~379 g including estimated electronics [U].
- **Joints:** all hinges sit at the body origin with local axis Z (MJCF) [V].

## 5. Servo
### 5.1 Feetech SCS0009 (datasheet values; mechanical details [U] until calipered)
- **Case:** 23.2 × 12.1 × 25.25 mm, mass 13.2 g.
- **Gearing and feedback:** 20T spline, OD 3.95 mm, M2×4 horn screw. Potentiometer feedback, 300° range.
- **Torque at 6 V:** 0.226 N·m stall, 0.069 N·m rated.
- **Bus and power:** 5264-3P connector, TTL half-duplex bus at 1 Mbps default, 4.8–6 V supply.
- **Mechanical details [U]:**

| Detail | Value |
|---|---|
| Shaft offset from case centre | 5.7 mm |
| Spline height | 3.2 mm |
| Horn thickness | 2.0 mm |
| Horn diameter | Ø18 mm |
| Ear span | 32.5 mm |
| Ear thickness | 2.0 mm |
| Ear hole pitch | 28.5 mm |
| Ear holes | Ø2 mm |
| Pocket clearance | 0.3 mm per side |

### 5.2 Placement rule [V]
- **XL330 raw-STL frame:** the shaft is local X through y=0, z=0, and the horn side is −X with the boss tip at x = −14.5 mm.
- **Where the SCS0009 goes:** each SCS0009 is placed so its horn top sits at x = −14.5·S = −10.44 mm in that frame. The driven part's horn interface therefore does not move.
- **Resulting case position:** case top is at x = −5.24 and case bottom at x = +20.01 (case centre at local z −5.7; ears at x −1.24..+0.76). The SCS case therefore sticks out about 10.6 mm further on the +X (idler) side than the scaled XL330. That causes most of the clashes in 5.5.
- **Code:** `tools/scs0009.py` (envelope, cutter, cradle) and `tools/assembly.py` (FK).

### 5.3 Servo rolls and stretches (pre-verified; C2 servo-servo = PASS, height 192.6 mm) [V]
**SERVO_ROLL_DEG** (spin about the servo's own shaft, so kinematics are unchanged):
- left_knee 90
- right_knee 90
- neck_pitch 270

**STRETCH** (world mm, applied after scaling):
- yaw2roll (0,0,−2.5)
- bearing_roll (0,0,−2.5)
- neck (+3,0,0)

Without these, the deficits were:
- neck_pitch vs head_pitch: −12.1 mm
- knee vs hip_pitch: −2.24 mm
- hip_yaw vs hip_roll: −0.11 mm
- hip_yaw vs neck_pitch: −0.5 mm

### 5.4 Why parts must change (the hard part)
- **The XL330 case is structural.** The printed parts screw into tapped holes on its sides and back, and the opposite side carries an idler/bearing boss.
- **The SCS0009 is different.** It has only 2 ear holes and no rear idler boss.
- **What every holder part therefore needs:**
  - a **cradle**, a 2 mm-wall sleeve around the case that is open on the horn side. Use `pocket_part.py --cradle`.
  - a **pocket**, cut by the case+ears cutter with 0.3 mm clearance, a cable exit and 2 × Ø1.6 pilot holes for the ear screws.
- **Bridges:** if the cradle doesn't touch the part (the tool warns "disconnected body"), add a bridge. Union a box between them (trimesh `creation.box` + `boolean.union`, engine `manifold`) of at least 3 mm × 3 mm section.
- **Yoke joints** (hip_roll, ankle, head_pitch, neck_pitch) need two things:
  - a coaxial idler pin/boss on the case side opposite the horn, carried by the cradle;
  - the driven yoke's idler arm moved outward by the overshoot (5.5), along the shaft axis.
- **Bearings:**
  - The 11 × 22×16×4 bearings become **6700ZZ (10×15×4)**. The scaled seat OD is 15.84, so seats are re-cut to Ø15.1 press fit [U].
  - The 3 small default bearings scale or are replaced by a plain bushing.

### 5.5 Work list at zero pose (C3, `check_clearance.py`) [V]
| Servo (holder body) | Penetrates | Depth mm | Session |
|---|---|---|---|
| left_hip_roll (yaw2roll) | power_support (trunk) | 8.85 | 1 |
| right_hip_roll (bearing_roll) | power_support (trunk) | 4.37 | 1 |
| left_ankle (leg) | ankle_left yoke | 13.32 | 1 |
| right_ankle (leg_2) | ankle_right yoke | 16.61 | 1 |
| left/right_ankle | foot_left/right | 0.30 | 1 |
| neck_pitch (neck) | right_shell (trunk) | 2.83 | 2 |
| head_pitch (neck) | neck_pitch yoke | 5.90 | 2 |
| head_yaw (yaw_roll_motion) | motor_support (head) | 0.73 | 2 |

Motion sweep baseline (`sweep_check.py`, 2026-10-27) [V]:

| Joint | Swept range | Result | Clashes found |
|---|---|---|---|
| hip_yaw L | | PASS | |
| hip_yaw R | | FAIL | power_support vs right_hip_roll servo, 10.45 mm at ±15° |
| hip_roll L/R | | PASS | |
| hip_pitch L/R | | PASS | |
| knee L/R | | FAIL | knee servo vs ankle servo, 3.1 mm at −45°, 1.9 mm at +30°, 6.9 mm at +45° |
| ankle L/R | | FAIL | foot vs ankle servo up to 16.9 mm; ankle yoke vs ankle servo up to 19.4 mm |
| neck_pitch | | FAIL | right_shell vs neck_pitch servo, 3.8–5.6 mm; left_shell, 1.2 mm at +30° |
| head_pitch | ±45° | FAIL | neck_pitch yoke vs head_pitch servo, 6.6–9.6 mm |
| head_yaw | ±120° | PASS | |
| head_roll | ±25° | FAIL | old head shells vs head_pitch servo, up to 20.2 mm; motor_support vs head_yaw servo, 3.0 mm at +25° |

Session 1 fixes the hip, knee and ankle rows. Session 2 fixes neck_pitch, head_pitch and the motor_support part of head_roll. Session 4 fixes the rest of head_roll by swept cuts on the original head shells (the Session-3 BDX head was rejected).

Left-ankle recipe, verified on a scratch copy: pocket+cradle in `leg`, `stretch_mesh` ankle_left x/plane 30/side −/delta 9, `idler_boss`, then `swept_cut` on ankle_left (grow 0.8, −24 % volume) and foot_left (grow 0.5). Result: left-ankle C3 clear, and ankle_left, leg and foot_left all P1–P4 PASS.

### 5.6 Holders per joint (body → printed parts holding the case) [V]
| Joint | Holder parts |
|---|---|
| hip_yaw | trunk_base, power_support, left_shell/right_shell |
| hip_roll | yaw2roll (L), bearing_roll (R) |
| hip_pitch + knee | upper_leg_left/right, upper_leg_rigidity_plate |
| ankle | leg |
| neck_pitch + head_pitch | neck (plates ×2) |
| head_yaw | yaw_roll_motion |
| head_roll | motor_support |

- **Shared STLs:** yaw2roll/bearing_roll, hip_l, leg, neck and upper_leg_rigidity_plate are each used for both sides. Edit once, using the LEFT joint, then check both sides.
- **Thin walls:** uniform scaling turns 1.0 mm walls into 0.72 mm. The `check_parts.py` P4 rule (10th-percentile wall thickness) is:
  - structural parts ≥ 1.2 mm
  - cosmetic parts ≥ 0.9 mm

  Fix with `thicken_plate.py` or a cradle, never by changing S. At baseline, trunk_base, upper_leg_rigidity_plate (0.72), leg (0.94) and yaw2roll (0.97) fail [V].

## 6. Joint table (full-scale world mm; ×S for mini; limits in degrees) [V]
| Joint | Anchor (full) | Axis | Servo in | Horn drives | Limits |
|---|---|---|---|---|---|
| left_hip_yaw | (6, 17.5, 115) | (0,0,−1) | trunk_base | yaw2roll | −25..30 |
| right_hip_yaw | (6, −17.5, 115) | (0,0,−1) | trunk_base | bearing_roll | −30..25 |
| left/right_hip_roll | (22.5, ±17.5, 102.5) | (1,0,0) | yaw2roll / bearing_roll | hip_l / hip_l_2 | ±22 |
| left_hip_pitch | (4, 42.5, 102.5) | (0,1,0) | upper_leg_left | hip_l | ±90 |
| right_hip_pitch | (4, −42.5, 102.5) | (0,−1,0) | upper_leg_right | hip_l_2 | ±90 |
| left_knee | (−31.8, 38.5, 80.5) | (0,−1,0) | upper_leg_left | leg | ±90 |
| right_knee | (−31.8, −38.5, 80.5) | (0,1,0) | upper_leg_right | leg_2 | ±90 |
| left_ankle | (−31.8, 64.5, 38.5) | (0,1,0) | leg | ankle_left | ±90 |
| right_ankle | (−31.8, −64.5, 38.5) | (0,−1,0) | leg_2 | ankle_right | ±90 |
| neck_pitch | (26, 14.5, 152.4) | (0,−1,0) | neck | trunk_base | −90..60 |
| head_pitch | (26, 14.5, 202.4) | (0,1,0) | neck | neck_pitch | ±90 |
| head_yaw | (26, 0, 221.1) | (0,0,1) | yaw_roll_motion | neck_pitch | ±150 (was ±170) |
| head_roll | (8.1, 0, 235.6) | (−1,0,0) | jaw_soft | yaw_roll_motion | ±25 |

The dropped mouth servo was an XL330 in jaw_soft at world (33, 25.6, 238.6) full scale.

## 7. Head interface and ORIGINAL Microduck head
- **Interface (keep, do not move):**
  - The head is body `jaw_soft`. The head_roll servo is held by `motor_support`, which is KEPT, pocketed for the SCS0009 and becomes the head's mounting chassis.
  - Sites in the jaw_soft frame (full-scale metres, ×S): head_camera (0.0155, 0, −0.0733), tof (0.0135, 0.0224, −0.0733), head_imu (0.0152, 0, −0.051) [V].
- **Head parts (`HEAD_MODE = "microduck"`, all upstream STLs scaled ×0.72):**
  top_head_shell, bottom_head_shell, face_part, jaw, jaw_soft, soft_mouth_top, noenoeil, m12_lens_holder
  (+ kept `motor_support`). `noenoeil` is a single Ø21.6 mm cyclops eye puck with a recessed centre;
  the OV2640 camera looks through it on the `m12_lens_holder` axis.
  - The **jaw is static/fixed** — the mouth servo was dropped, so `jaw`'s servo pocket is left unused and no moving jaw is modelled.
  - **Session-3 BDX head: rejected.** `bdx_*.stl` and its `elec_*` placeholders are kept in `parts/attic_bdx/`; do not use or improve them.
  - **Servo clearance (Session 4):** the fatter SCS0009 `yaw_roll_motion` cradle and neck parts graze the original shells during `head_roll ±25°`. Fixed by swept cuts on the HEAD parts only (`swept_cut.py` exact-mesh cutters, grow 0.3): top_head_shell −6.8%, bottom_head_shell −6.8%, jaw −4.7%, motor_support −3.4%; outside shape unchanged. The jaw_soft `seeed_bearing__configuration_default` roll idler is omitted (plain printed bushing per §5.4) — its rim grazed neck parts the same way.
- **Electronics in the head** (`tools/make_head_elec.py`, authored in the jaw_soft frame in mm; pairwise boolean intersection with every part < 1 mm³ [V]):

| Component | Position and mounting |
|---|---|
| XIAO ESP32-S3 Sense | Board 21×17.5×6 right of the eye axis (x −4..17, y −25..−8, z −37..−30, rear-outer corner chamfered for the dome wall); OV2640 cube at the eye axis z −39.6..−34.6 joined by a flex-ribbon stub |
| 2 × WS2812 rings | Ø26/Ø18 × 2.4 halo annuli stacked around the lens barrel behind `noenoeil`, z −42.9..−37.5 |
| VL53L0X | 10.5×11×3 board at the right ToF window (x 4.5..15, y 14..25, z −42.5..−39.5) |
| Speaker (Ø22 × 4) | Flat disc membrane-up in the upper dome (x 12..16, y ±11, z −3..19) |
| Buck 5 V | 6×18×15 board on the left interior flank (x −11..−5, y 12..30, z 0.5..15.5) |
| MAX98357A amp | Next to the XIAO |
| Mic | On the XIAO Sense board; a Ø2 hole near it |
| Cables | One bundle through the neck along the head_yaw axis with a ≥ 60 mm service loop for ±150° yaw; strain relief clip on motor_support |

- **Head limits:**
  - Head mass target ≤ 70 g including electronics [U].
  - The head must clear the neck through head_pitch ±45°, head_yaw ±120° and head_roll ±25° (`sweep_check.py`) — all three PASS in session 4 [V].
  - Electronics placeholders live inside the original shells; the outside shape is unchanged.
- **Printability:** unchanged from upstream (the shells are the original two-part dome).

## 8. Electronics (replaces Pi Zero 2 W + HAT + NP-F970)
| Item | Notes |
|---|---|
| XIAO ESP32-S3 Sense | Controller, camera, mic, Wi-Fi. Lives in the head |
| BNO085 IMU | In the trunk at the old imu site (MPU-6050 is the cheaper fallback) |
| Bus wiring | UBEC 6 V/5 A from a 2S 450 mAh ≥30C LiPo with XT30, inline fuse and switch, to a servo bus hub in the trunk. The 5 V buck in the head feeds the XIAO and rings |
| Bus interface | Half-duplex TTL from XIAO UART via 74LVC1G125/126 buffer [U, test]. FE-URT-1 USB adapter for setting servo IDs from a PC |
| Through-neck wires | 6V, GND, BUS, SDA, SCL |
| Safety | LiPo: balance charger only, never unattended, storage voltage, fuse at the pack. Soldering: ventilation and eye protection. Buck: set and measure the output before connecting the XIAO |

## 9. Software (porting risks)
- **What the upstream policy assumes:** the RL policy was trained with mjlab for XL330 dynamics:
  - actuator class `chosen_actuator`: kp 0.55, forcerange ±0.96, damping 0.053, armature 0.0018
  - a Linux SBC
- **What changes here:** SCS0009 dynamics (forcerange ±0.226; kp, damping and armature UNKNOWN [U]), an ESP32-S3 and different masses.
- **Consequence:** the old policy will not transfer. It needs a new MJCF (`build_mjcf.py`), servo identification, retraining in mjlab, and an on-device or Wi-Fi-offboard inference plan. This is a risk and is out of scope for the CAD sessions.

## 10. Licence (must be in `mini/LICENSE-MESHES.md` and the README)
```
Original design and STL: Pollen Robotics / Microduck.
STEP reconstruction, repairs, validation and CAD sheets: tianjin66 and project contributors.
Source: https://github.com/tianjin66/microduck-step-3d-models-ai-stl
Licence: CC BY-NC-SA 4.0 — https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: uniformly scaled by 0.72; servo pockets/cradles re-cut for Feetech SCS0009; local stretches
(see SPEC.md 5.3); bearing seats changed to 6700ZZ; head shells swept-relieved internally for the
SCS0009 neck cradle (Session 3's BDX head rejected; outside shape unchanged).
```
- **Derived meshes:** all derived meshes and STLs in `mini/parts/` are **CC BY-NC-SA 4.0**, so non-commercial and share-alike.
- **Fix Knoll's claims:** any CERN-OHL or Apache-2.0 claim in the Knoll repo that covers these meshes is wrong.
  - Replace it with the block above.
  - Code in `mini/tools/` may stay Apache-2.0 if the user wants, but say clearly that it does not cover the meshes.
- **MJCF:** the MJCF derived from microduck_rl must keep that repo's licence notice. Copy its LICENSE into `mini/third_party_licenses/`.

## 11. Forbidden for every session
- Do not rebuild parts from scratch, re-model the body, change S, or change any joint position, axis or limit, except head_yaw, already capped at ±150.
- Do not delete files. Superseded STLs go to `mini/parts/attic/`.
- Do not edit `third_party/`, `parts/scaled/` or `main`. Do not force-push or rewrite history.
- Do not claim PASS without running the check and pasting its real output.
- Do not install anything except the packages each prompt names.

## 12. Change log
| Date | Session | Change | Why | Check output |
|---|---|---|---|---|
| 2026-10-27 | prep | S=0.72, rolls + stretches of 5.3 | C2 PASS, height 192.6 | check_clearance C2 PASS |
| 2026-10-27 | 1 | SERVO_ROLL_DEG ankles kept 0 (trialled 90/180/270, none usable) | 90: right_ankle vs right_hip_roll servo at knee -45; 180: passes knees but the case envelope reaches z 3.27, ~4 mm below the sole bottom (physically impossible); 270: left_ankle vs left_hip_roll servo at knee +45. Roll 0 has the smallest ankle C3 (the verified recipe) | see HANDOFF S1 |
| 2026-10-27 | 1 | Knee rolls also trialled 0/90/180/270 for the ankle↔knee case clash | none clears it (90 kept — upstream-verified for knee↔hip_pitch) | sweep_check left/right_knee; direct env depth test |
| 2026-10-27 | 1 fix | SERVO_ROLL_DEG ankles -> left_ankle=90, right_ankle=270 (mirrored pair; same-sign 90/90 and 270/270 both fail on the opposite side) | Clears BOTH the inherited ankle↔knee case clash (was 3.12/2.73/6.88 mm at -45/+35/+45) AND the ankle↔hip_roll pair: 0.00 mm max envelope depth over the full knee sweep on both sides. Both knees now PASS -45..+45; earlier "usable range -33..+21" note is superseded. Leg + ankle parts re-cut for the rotated envelopes (shared leg.stl carries the corridor for both sides via the leg/leg_2 instance rotation) | sweep_check left/right_knee+ankle all PASS; check_clearance unchanged |
| 2026-10-27 | 2 | EXTRA_PARTS = [("neck","neck_frame")]; REMOVED_PARTS = ["neck"] | merge_body_frame --hull replaces the two tiny XL330 neck plates with one SCS0009 bracket cradling neck_pitch + head_pitch; final part is the hull clipped to x<=-1 plus swept clearance cuts (full --hull was too fat to swing neck_pitch +-45 past the trunk) | merge: watertight bodies=1; check_clearance C1-C4 PASS; check_parts + all 3 neck/head sweeps PASS |
| 2026-10-27 | 3 | HEAD_MODE = "bdx" | BDX head parts generated by make_bdx_head.py (5 watertight parts), replacing the 8 upstream head STLs | see HANDOFF S3 |
| 2026-10-27 | 3 | COSMETIC_PARTS += 7 bdx_* names; BDX_HEAD_PARTS += bdx_eye_diffuser_l/r | head shells/bezels/diffusers are cosmetic parts (P4 0.9 mm bar); diffuser discs ship as printed parts | check_parts --only bdx_* + motor_support: OVERALL PASS |
| 2026-10-28 | 4 | HEAD_MODE = "microduck"; 8 original head STLs back in parts/current; bdx_* + old elec_* -> parts/attic_bdx/ | Session-3 BDX head rejected; revert to the original Microduck head | check_clearance C1-C4 PASS; all 3 head sweeps PASS |
| 2026-10-28 | 4 | swept_cut.py: exact: cutters, multi-token --servo, --horn, --keep-largest; head shells swept vs exact neck/yaw meshes (grow 0.3, head_roll ±25) | hull cutters removed too much; FCL depth over-reports for parts inside concave shells — boolean volumes were tens of mm3 | head_roll PASS; check_parts top/bottom_head_shell, jaw, motor_support PASS |
| 2026-10-28 | 4 | assembly.py skips jaw_soft seeed_bearing__configuration_default; elec_* placeholders regenerated for the original head (make_head_elec.py) | roll idler rim grazed static neck parts; plain printed bushing per 5.4; electronics refit inside the original dome | elec pairwise intersections <1 mm3; check_clearance C1-C4 PASS |
