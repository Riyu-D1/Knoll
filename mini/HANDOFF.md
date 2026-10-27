# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last commit: session-0 commit (this file ships inside it) — `mini: session 0 - kit, scaled parts, licence fix`.
- Last finished session: `0`
- S = 0.72. Height: `192.6 mm`. Model mass: `~379 g (est., [U])`.
- Python: `mini/.venv`, CPython 3.12.2. **mujoco pinned to 3.10.0** — 3.11+ ships no cp312 macOS x86_64 wheel (Intel Mac); see Open problems.
- Upstream pins verified: `microduck_rl @ 29e887ecfbf5d37144759e5a9f8a176dfb83d547` (= spec.UPSTREAM_COMMIT), STL repo @ `bf96450c75e635efb993676fe90c6456fb8a00af`, `robot_walk.xml` present, 30 STLs in `01_STL_original` (+1 README).

## Check status (paste the last lines of each tool)
| Check | Command | Result | Date/session |
|---|---|---|---|
| Clearance C1–C4 | `python tools/check_clearance.py` | `C1 servos placed=14 ... PASS` · `C2 PASS` · `C3 FAIL` (9 expected clashes, below) · `C4 height=192.6 mm (cap 200.0) PASS` · `OVERALL: FAIL` | 2026-10-27 / S0 |
| Parts P1–P4 | `python tools/check_parts.py` | `OVERALL: FAIL` — 14 FAIL lines, all thin-wall P4 (expected baseline) | 2026-10-27 / S0 |
| Sweep R1 | `python tools/sweep_check.py` | NOT RUN (sessions 1+) | — |
| MJCF loads | `python tools/build_mjcf.py` + load test | NOT RUN (session 4) | — |
| Torque T1–T2 | `python tools/torque_check.py` | NOT RUN (session 4) | — |

C3 clash list (matches SPEC 5.5 exactly):
```
FAIL left_hip_roll    (in yaw2roll)      penetrates power_support  (trunk_base)   by  8.85 mm
FAIL right_hip_roll   (in bearing_roll)  penetrates power_support  (trunk_base)   by  4.37 mm
FAIL left_ankle       (in leg)           penetrates ankle_left yoke              by 13.32 mm
FAIL right_ankle      (in leg_2)         penetrates ankle_right yoke             by 16.61 mm
FAIL left_ankle       (in leg)           penetrates foot_left                    by  0.30 mm
FAIL right_ankle      (in leg_2)         penetrates foot_right                   by  0.30 mm
FAIL neck_pitch       (in neck)          penetrates right_shell   (trunk_base)   by  2.83 mm
FAIL head_pitch       (in neck)          penetrates neck_pitch yoke              by  5.90 mm
FAIL head_yaw         (in yaw_roll_motion) penetrates motor_support (jaw_soft)   by  0.73 mm
```
JSON: `renders/baseline_clearance.json`. Parts report: `renders/baseline_parts.txt`.
P4 thin-wall FAILs (14): bearing_roll 0.72, bottom_head_shell 0.90, foot_right 1.19, leg 0.94,
m12_lens_holder 0.65, power_support 1.05, soft_mouth_top 0.58, sole_left 1.12, sole_right 1.14,
trunk_base 0.72, upper_leg_left 0.72, upper_leg_right 0.72, upper_leg_rigidity_plate 0.72, yaw2roll 0.97.

## Parts changed so far
| Part STL | Session | What was done (tool + args) | Watertight | Wall p10 |
|---|---|---|---|---|
| all 30 upstream STLs → `parts/scaled/` + `parts/current/` | 0 | `scale_parts.py`, uniform ×0.72, all `matches_upstream=True` | True (all) | see baseline_parts.txt |
| `parts/lib/scs0009_{envelope,cutter,cradle}.stl` | 0 | `scs0009.py` library build; horn top −10.44, case −5.24..+20.01 | True (all) | n/a (tools) |

## Licence edits this session (step 12)
- Created `mini/LICENSE-MESHES.md` (SPEC §10 block + "All files in mini/parts/ are CC BY-NC-SA 4.0. Non-commercial use only.").
- Created `mini/third_party_licenses/`: `microduck_rl_LICENSE`, `LICENSE`, `NOTICE.md`, `REUSE_POLICY.md` (from the STL repo).
- `licensing/originality-and-licensing.md` — scoped the CERN-OHL-S STL row to original Knoll designs; added pointer exception note under the table.
- `decisions/architecture-decision-record.md` — added CC BY-NC-SA 4.0 exception notes to the §1 decision line and the D10 licensing row.
- `README.md` — appended "Knoll Mini (work in progress)" section with description + attribution block.
- Files checked and left unchanged (third-party licence *facts*, not claims over our meshes):
  `research/notes-microduck.md`, `research/sources.md`, `research/reference-analysis.md`,
  `design/shared-design-brief.md`, `engineering/notes-control.md`, `software/system-architecture.md`.
- No top-level `LICENSE` file exists → nothing to annotate there.

## Open problems / things I could not do
- **mujoco version pin:** `mujoco==3.17.0`/`3.16.0` fail — PyPI ships no cp312 macOS **x86_64** wheel ≥3.11
  (arm64 only), and the sdist aborts with `MUJOCO_PATH environment variable is not set`.
  Resolved by pinning `mujoco==3.10.0` (last version with an x86_64 wheel). Session 4's `build_mjcf.py`
  only needs mujoco to load/validate the MJCF — 3.10.0 imports fine, but if the MJCF needs newer
  schema features this must be revisited (arm64 machine, or conda-packaged mujoco).
- C3 FAIL is expected this session — the 9 clashes above are Sessions 1–2 work, not bugs.
- 14 thin-wall P4 FAILs are expected this session — `thicken_plate.py`/cradles in Sessions 1–3.
- SCS0009 mechanical dims (shaft offset, horn, ears) are still UNVERIFIED until calipered (SPEC 5.1).

## Decisions that need the human
- Is `mujoco==3.10.0` acceptable for session-4 MJCF checks on this Intel Mac, or should session 4 plan
  around an arm64 machine / different mujoco source? (Recommendation: keep 3.10.0, revisit only if
  `build_mjcf.py` fails on schema.)
- Confirm CC BY-NC-SA 4.0 exception wording in `licensing/` + `decisions/` reads as intended.

## Next session
- Session 1 – body and legs: SCS0009 pockets, cradles, hip_roll/ankle clashes.
  First command: `cd mini && .venv/bin/python tools/check_clearance.py` (re-confirm C3 baseline), then
  `pocket_part.py`/`stretch_mesh.py`/`idler_boss.py`/`swept_cut.py` per the verified left-ankle recipe in SPEC 5.5.
