# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last finished session: `7` (head enclosure — head_roll
  fully enclosed, head_yaw partially; all sweeps + clearance PASS). Nothing was purchased.
- S = 0.72. Height: `192.7 mm` (cap 200). Sim mass `431.1 g`; head body (`jaw_soft`) `72.8 g`.
  Head: original Microduck ×0.72, fixed jaw, 14 SCS0009 servos. All final — do not re-open.
- Python: `mini/.venv`, CPython 3.12.2, **mujoco pinned to 3.10.0**.
- spec.py: `HEAD_MODE = "microduck"`, `EXTRA_PARTS = [("neck","neck_frame")]`,
  `REMOVED_PARTS = ["neck"]` — unchanged.
- Model: `mini/model/knoll_mini.xml` + `scene_knoll_mini.xml`, `nq 21 nu 14 nbody 16`.
- NEW this session: `top_head_shell.stl` + `bottom_head_shell.stl` extended outward to enclose
  head-region servos (old versions in `parts/attic_head_v1/`); tools `head_protrusion.py`,
  `head_enclosure.py`; render presets `back`, `servo_side`, `head_low` in `render_solid.py`.

## Head decision (session 4, still final)
- **Session-3 BDX head: REJECTED.** Original Microduck head ×0.72, fixed jaw. `bdx_*` + old head
  `elec_*` live in `parts/attic_bdx/` (rejected, not deleted). Outside shape unchanged.

## Check status (real outputs, end of session 7)
| Check | Command | Result |
|---|---|---|
| Clearance | `python tools/check_clearance.py` | `C1 PASS` `C2 PASS` `C3 PASS` `C4 height=192.7 mm (cap 200.0) PASS` — **OVERALL PASS** |
| Parts | `python tools/check_parts.py` | `bottom_head_shell` watertight wall_p10=0.99mm PASS · `top_head_shell` watertight wall_p10=1.18mm PASS (other FAILs are pre-existing thin leg/trunk parts, unchanged) |
| Sweeps | `python tools/sweep_check.py --joint X` | `head_yaw -120..+120 PASS` · `head_roll -25..+25 PASS` · `head_pitch -45..+45 PASS` · `neck_pitch -45..+45 PASS` |
| Protrusion | `python tools/head_protrusion.py` | `head_roll 0/3185 enclosed` · `head_yaw 533/3185 right 4.50 mm` (residual in swept neck corridor) · `neck_pitch`/`head_pitch` neck region, by design |
| MJCF | `python tools/build_mjcf.py` | wrote `knoll_mini.xml` + `scene_knoll_mini.xml`; `jaw_soft 72.8 g`, total `431.1 g` |
| Torque | `python tools/torque_check.py` | `[STAND] T1 PASS` `T2 PASS; joints over rated 0.069: 0` — **OVERALL PASS** |
| Renders | `python tools/render_solid.py` | `renders/solid/{front,side,three_quarter,head,back,servo_side,head_low}.png` — dome + face original; residual yaw band visible low on the right |

## Session 6 — what changed
- `docs/BOM.md`: 19 lines, USD + GBP-incl-VAT columns, every line linked to a product page
  opened 2026-10-28 (or 2026-10-27 where the prompt supplied it). Totals $256/$246 — about
  3–7 % over the ~$240 target, stated plainly in the doc.
- `docs/wiring.md`: power path (LiPo → fuse → switch → UBEC 6V trunk hub + neck cable → head
  5V buck → XIAO), SCS half-duplex bus via 74LVC1G125/126 + D3 DIR, I2C on D4/D5, UART on
  D6/D7, I2S [U] on D8–D10, D11/D12 reserved for the Sense onboard mic, servo ID table in
  SPEC §6 order + the upstream ctrl-index remap, neck bundle = 6V/GND/BUS/SDA/SCL (22 AWG
  power, 26 AWG signals, ≥60 mm service loop).
- `docs/assembly.md`: 10 numbered steps naming exact STLs; inserts → servo ID/centre →
  legs foot-up → trunk (battery tray, UBEC, hub, BNO085) → neck → head → routing →
  unloaded-rail power-on check → one-joint-at-a-time motion test.
- `docs/print_list.md`: all 30 printed STLs, shared parts ×2 (`yaw2roll`, `bearing_roll`,
  `hip_l`, `leg`, `upper_leg_rigidity_plate`), volumes/masses from trimesh, orientations.
- Safety boxes (LiPo, soldering/inserts, buck bring-up, pinch points) in BOM.md + assembly.md.
- **No geometry, spec.py or tool changes.** Nothing moved, nothing deleted.

## Session 7 (head enclosure) — what changed
- `tools/head_protrusion.py` (new): rasterizes all parts into a 0.5 mm occlusion grid, tests
  servo-envelope samples for an unblocked path to the exterior; reports visible count and mm
  past the skin silhouette per side. Baseline: `head_roll` back ~3.9 mm, `head_yaw`
  sides ~4.5-4.9 mm + top ~0.7 mm; `neck_pitch`/`head_pitch` are neck-body servos (by design,
  not part of this fix).
- `tools/head_enclosure.py` (new): convex-hull bulge from exposed swept-envelope points +
  nearby shell verts, grown by wall+clearance, unioned into the part; interior void = swept
  env grown by `--void` (1.2 mm — the real STL horn tip sits ~0.7 mm past the envelope model).
  `--zfloor` clips added material above a world-z plane; `--clear` carves a corridor out of
  the bulge for every stationary part swept through head_yaw/head_roll/head_pitch (5° steps).
- `bottom_head_shell.stl`: local back-rim bulge enclosing `head_roll` (vol 8.27→8.77 cm3,
  extent +5.7 mm in the rear direction). `head_roll`: **0 visible — enclosed**.
- `top_head_shell.stl`: small bulge covering the `head_yaw` top/back escapes at the dome edge
  (vol 10.39→13.07 cm3, extents ~unchanged — fills the existing gap). Corridor-carved where
  `yaw_roll_motion` sweeps during rolls.
- **Residual (accepted per session instructions):** `head_yaw` low band on the right still
  visible — 533/3185 samples, max 4.50 mm past the skin, at the dome-tray gap over the neck.
  That region is the swept corridor of the neck parts: a full skirt enclosure collided up to
  8.7 mm with `neck_pitch`/`neck_frame` during yaw/roll/pitch sweeps. Sweeps were kept over
  enclosure — all four joints PASS with the committed shells.
- `renders/solid/`: front, side, three_quarter, head, back, servo_side, head_low — dome and
  flat angled face unchanged; no servo visible except the residual yaw band low on the right.

## Key facts for the next session
- Electronics all sit in the head (all five `elec_*` placeholders). Trunk = battery, fuse,
  switch, UBEC, bus hub, BNO085. Neck carries 6V+GND up, BUS/SDA/SCL between head XIAO and
  trunk hub/BNO085.
- Servo IDs 1–14 in SPEC §6 order; firmware ctrl order (L leg 0-4, neck/head 5-8, R leg 9-13)
  needs the remap table in wiring.md.
- Servo sourcing is cheapest at Seeed 10+ pricing ($8 ea → ~$112 vs the $133 budgeted).
- LiPo at ~450 mAh 30C with **XT30** was not found verified — the £8.08 Radient unit ships JST.
- Head buck 6V→5V has thin headroom — flagged [U] with a pre-UBEC fallback in wiring.md.

## Open problems / things I could not do
- `head_yaw` residual exposure: 4.50 mm on the right side (low band through the dome-tray
  gap, over the neck column). Full enclosure is geometrically impossible there — stationary
  neck parts sweep that space during head motion. Fix would need servo relocation or a
  neck-part redesign, not a shell bulge.
- SCS0009 actuator parameters (kp-equivalent, damping, armature, friction, backlash) unknown
  [U] — identify on real hardware before retraining.
- I2S pin assignment on the XIAO is [U] (D8–D10 proposed; D11/D12 blocked by the Sense mic).
- 74LVC 3.3V↔5V TTL level compatibility is [U] — bench-verify before the full bus.
- Exact-fit 450 mAh 30C XT30 LiPo, generic $13 BNO085, $5 VL53L0X, $2 WS2812 rings, $2 buck
  and $2 fuse lines remain [U] — verified alternatives are noted per line in BOM.md.
- Electronics standoffs/mounting posts inside the head are not modelled (<1 mm³ intersections,
  several within ~0.5 mm of a shell) — needs foam/tape or a future mounting-post pass.
- Mass is 431.1 g vs the docstring's 378.9 g baseline ([U] electronics are estimates;
  +2.2 g of new shell material this session).

## Decisions that need the human
- Speaker has no grille holes — drill a grille or leave.
- The Ø26/Ø18 halo rings are modelled for the common ~37 mm OD 12-LED ring [U] — confirm the
  real ring OD before printing.
- Head `jaw_soft` = 72.8 g vs ≤70 g [U] target — accept or shave the electronics estimate once
  real boards are weighed (bulges added ~2.2 g).
- MPU-6050 (~$3) vs BNO085 ($13–29.50) IMU choice — saves ~$10 but loses fusion quality.

## Next session
Hardware bring-up (buy parts, print per print_list.md, assemble per assembly.md) or a
mounting-post/grille CAD pass if desired — the model is otherwise build-ready.
