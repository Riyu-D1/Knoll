# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last finished session: `5` (MuJoCo model + checks).
- S = 0.72. Height: `192.6 mm` (cap 200), measured on the concatenated assembly bbox
  `[[-45.1,-61.9,7.2],[69.4,61.9,199.8]]`.
- Python: `mini/.venv`, CPython 3.12.2. **mujoco pinned to 3.10.0** — 3.11+ ships no cp312
  macOS x86_64 wheel.
- Upstream pins verified: `microduck_rl @ 29e887ecfbf5d37144759e5a9f8a176dfb83d547`, STL repo
  @ `bf96450c75e635efb993676fe90c6456fb8a00af`.
- spec.py: `HEAD_MODE = "microduck"`, `EXTRA_PARTS = [("neck","neck_frame")]`,
  `REMOVED_PARTS = ["neck"]` (unchanged this session).
- Head is FINAL: original Microduck head ×0.72, fixed jaw (no mouth servo), 14 SCS0009 servos.
- NEW: `mini/model/knoll_mini.xml` + `mini/model/scene_knoll_mini.xml` built by
  `tools/build_mjcf.py` — loads in mujoco 3.10.0, `nq 21 nu 14 nbody 16`, subtree mass 428.9 g.

## Head decision (session 4, still final)
- **Session-3 BDX head: REJECTED** — do not use or improve it. Original Microduck head
  (dome + flat angled face + single Ø21.6 `noenoeil` cyclops puck, camera through the middle
  on the `m12_lens_holder` axis), scaled ×0.72. `jaw` is FIXED. `bdx_*` + old head `elec_*`
  are in `parts/attic_bdx/` (rejected, not deleted).
- Outside shape unchanged; only internal swept relief for the fatter SCS0009 neck hardware.

## Check status (real outputs, end of session 5)
| Check | Command | Result |
|---|---|---|
| Env | `python tools/assembly.py \| head -3` | `S=0.72 items=67 servos=14` · `height_mm 192.6` |
| MJCF build | `python tools/build_mjcf.py` | `wrote model/knoll_mini.xml and scene_knoll_mini.xml; trunk z0 = 0.0797 m` · total mass 428.9 g |
| A1 load test | `mujoco.MjModel.from_xml_path('model/scene_knoll_mini.xml')` | `nq 21 nu 14 nbody 16 mass_g 428.9` — nu=14, mass in 350–450 · **PASS** |
| A2 servo placement | cross-check MJCF vs `assembly.py` at INIT | `servos 14 max mismatch mm 0.0` (≤ 0.5) · **PASS** |
| A3 static torque | `python tools/torque_check.py` | `[STAND] T1 stood=PASS (z 87.2 -> 85.5 mm)` · `[STAND] T2 PASS; joints over rated 0.069: 0` · **OVERALL: PASS** |
| Dynamic margin | `0.226/(3·static)` per leg joint | knees 2.72, hip_roll ~18, ankles ~26, hip_pitch ~95, hip_yaw ~520 — **no joint below 1.5** (info only, not pass/fail) |
| R1 range sweep | `python tools/sweep_check.py > renders/s4_sweep.txt` | all 14 joints swept, every line `PASS` · **R1 OVERALL: PASS** |
| A4 docs | `docs/mass_budget.md`, `docs/software_porting.md` | both exist; electronics masses marked [U] |
| Clearance C1–C4 | `python tools/check_clearance.py` (session 4) | `C1 PASS` `C2 PASS` `C3 PASS` `C4 height=192.6 (cap 200) PASS` · OVERALL: PASS |

## Torque table (STAND keyframe, mean |force| last 1 s of 3 s hold)
| Joint | N·m | | Joint | N·m |
|---|---|---|---|---|
| right_knee | 0.028 | | left_ankle | 0.003 |
| left_knee | 0.028 | | right_ankle | 0.003 |
| head_pitch | 0.006 | | right_hip_pitch | 0.001 |
| right_hip_roll | 0.004 | | left_hip_pitch | 0.001 |
| left_hip_roll | 0.004 | | head_roll | 0.000 |
| neck_pitch | 0.004 | | hip_yaws, head_yaw | 0.000 |

Max static 0.028 N·m = 12 % of stall (0.226), 41 % of rated (0.069). 0 joints over rated.

## Session 5 — what changed
- Built `mini/model/knoll_mini.xml` + `mini/model/scene_knoll_mini.xml` (first MuJoCo model of
  the mini): positions ×S + STRETCH, 14 SCS0009 actuators (forcerange ±0.226 N·m), joint ranges
  clipped to ±150°, masses from real STL volumes + servos + bearings + `spec.ELECTRONICS`.
- Wrote `mini/docs/mass_budget.md` (per-body mass table, 428.9 g total) and
  `mini/docs/software_porting.md` (retraining + ESP32-S3 + SCS bus porting plan).
- Wrote `mini/renders/s4_sweep.txt` (full 14-joint sweep log).
- **No geometry, spec.py or tool changes.** Nothing moved, nothing deleted.

## Software porting summary (docs/software_porting.md)
- Upstream policy was trained for XL330 (kp 0.55, forcerange ±0.96, damping 0.053,
  armature 0.0018) → **retraining required** for SCS0009 (forcerange ±0.226).
- Identify on the real servo [U]: gain equivalent, damping, armature, friction, backlash,
  latency — step-response logging over the bus at 100 Hz.
- Compute: ESP32-S3 has no Linux → off-board Wi-Fi inference for bring-up (~10–20 ms [U]),
  then quantize to TFLite Micro/ESP-NN on-device.
- Bus: Feetech SCS half-duplex 1 Mbps; set 14 unique IDs one by one with FE-URT-1.
- IMU: BNO085 at the unchanged `imu` site/frame.
- Same: joint names, order, axes, limits (head_yaw ±150°). mjlab task can point at
  `scene_knoll_mini.xml`.

## Interfaces for next sessions
- `elec_*` placeholders are non-printed (skipped by check_parts); regenerate via
  `tools/make_head_elec.py` if the layout must move.
- `swept_cut.py exact:<name>[:<body>]` cutters + `--horn` + `--keep-largest <frac>` are the
  tool for "part X grazes part Y during a sweep" — boolean intersection volumes, NOT FCL depth.
- MuJoCo: `python tools/build_mjcf.py` regenerates the model after any part/spec change;
  `python tools/torque_check.py` re-runs T1/T2.

## Open problems / things I could not do
- SCS0009 actuator parameters (kp-equivalent, damping, armature, friction, backlash) are
  unknown [U] — the MJCF uses defaults; servo ID on real hardware is required before retraining.
- The S1 thin-wall list still stands (leg, power_support, ankles, soles...) — cosmetic-bar
  exceptions documented in earlier sessions.
- bottom_head_shell wall_p10 = 0.96 mm — passes the 0.9 cosmetic bar with little margin.
- Electronics sit with <1 mm³ intersections but several are within ~0.5 mm of a shell —
  real boards need foam/tape standoffs; mounting posts not yet modelled.
- Mass is 428.9 g vs the docstring's 378.9 g baseline — the delta is the session-3/4 head
  electronics placeholders + session-2/4 part changes; [U] electronics are estimates.

## Decisions that need the human
- Speaker sits in the upper dome interior with no grille holes yet — drill a grille or leave.
- The Ø26/Ø18 halo rings are modelled for the common 12-LED mini ring [U] — confirm the real
  ring OD before printing.
- Head body `jaw_soft` = 70.6 g vs the ≤ 70 g [U] target — accept or shave the electronics
  estimate once the real boards are weighed.

## Next session
`Session 6` — BOM/docs session (BOM, wiring, assembly docs per SPEC §3 layout) and/or mounting
posts + speaker grille; nothing here blocks it.
