# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last finished session: `6` (BOM + wiring + assembly +
  print list docs; README updated). Nothing was purchased.
- S = 0.72. Height: `192.6 mm` (cap 200). Sim mass `428.9 g`. Head: original Microduck ×0.72,
  fixed jaw, 14 SCS0009 servos. All final — do not re-open.
- Python: `mini/.venv`, CPython 3.12.2, **mujoco pinned to 3.10.0**.
- spec.py: `HEAD_MODE = "microduck"`, `EXTRA_PARTS = [("neck","neck_frame")]`,
  `REMOVED_PARTS = ["neck"]` — unchanged.
- Model: `mini/model/knoll_mini.xml` + `scene_knoll_mini.xml`, `nq 21 nu 14 nbody 16`.
- NEW this session: `docs/BOM.md`, `docs/wiring.md`, `docs/assembly.md`, `docs/print_list.md`;
  licence block appended to `docs/mass_budget.md` + `docs/software_porting.md`; top-level
  README "Knoll Mini" section updated (doc links, BOM totals, stale "BDX head" text removed).

## Head decision (session 4, still final)
- **Session-3 BDX head: REJECTED.** Original Microduck head ×0.72, fixed jaw. `bdx_*` + old head
  `elec_*` live in `parts/attic_bdx/` (rejected, not deleted). Outside shape unchanged.

## Check status (real outputs, end of session 6)
| Check | Command | Result |
|---|---|---|
| Env | `python tools/assembly.py \| head -3` | `S=0.72 items=67 servos=14` · `height_mm 192.6` (unchanged, session 5) |
| MJCF / torque / sweep / clearance | session-5 checks | all PASS, unchanged this session (no geometry/tool changes) |
| A1 BOM totals | python snippet over 19 BOM lines | `total BNO085 USD 256` · `total MPU-6050 USD 246` · `GBP incl VAT @1.33: BNO085 GBP 193 MPU-6050 GBP 185` · `servos share 52%` — **PASS** (with UK-verified lines the GBP totals are £209/£201; see BOM.md) |
| A2 [U] count | `grep -c "\[U\]" docs/BOM.md` | `19` (≥1) — **PASS**; every [V] carries URL + date |
| A3 print list | trimesh volume×1.27×0.55 per STL | `TOTAL 35 pieces 161233 mm3 → 112.6 g` — **PASS**, output pasted in print_list.md |
| A4 licence | `grep -L "CC BY-NC-SA" docs/*.md` | prints nothing — **PASS** |
| A5 diff scope | `git diff --stat` | `README.md`, `mini/docs/mass_budget.md`, `mini/docs/software_porting.md` only; new files all under `mini/docs/` — **PASS** |

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
- SCS0009 actuator parameters (kp-equivalent, damping, armature, friction, backlash) unknown
  [U] — identify on real hardware before retraining.
- I2S pin assignment on the XIAO is [U] (D8–D10 proposed; D11/D12 blocked by the Sense mic).
- 74LVC 3.3V↔5V TTL level compatibility is [U] — bench-verify before the full bus.
- Exact-fit 450 mAh 30C XT30 LiPo, generic $13 BNO085, $5 VL53L0X, $2 WS2812 rings, $2 buck
  and $2 fuse lines remain [U] — verified alternatives are noted per line in BOM.md.
- Electronics standoffs/mounting posts inside the head are not modelled (<1 mm³ intersections,
  several within ~0.5 mm of a shell) — needs foam/tape or a future mounting-post pass.
- Mass is 428.9 g vs the docstring's 378.9 g baseline ([U] electronics are estimates).

## Decisions that need the human
- Speaker has no grille holes — drill a grille or leave.
- The Ø26/Ø18 halo rings are modelled for the common ~37 mm OD 12-LED ring [U] — confirm the
  real ring OD before printing.
- Head `jaw_soft` = 70.6 g vs ≤70 g [U] target — accept or shave the electronics estimate once
  real boards are weighed.
- MPU-6050 (~$3) vs BNO085 ($13–29.50) IMU choice — saves ~$10 but loses fusion quality.

## Next session
Hardware bring-up (buy parts, print per print_list.md, assemble per assembly.md) or a
mounting-post/grille CAD pass if desired — the model is otherwise build-ready.
