# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last commit: `a5376ae mini: session 1 WIP leg and body pockets` (+ final session-1 commit on top).
- Last finished session: `1` (body + legs SCS0009 conversion).
- S = 0.72. Height: `192.6 mm`. Model mass: `~379 g (est., [U])`.
- Python: `mini/.venv`, CPython 3.12.2. **mujoco pinned to 3.10.0** — 3.11+ ships no cp312 macOS x86_64 wheel (Intel Mac).
- Upstream pins verified: `microduck_rl @ 29e887ecfbf5d37144759e5a9f8a176dfb83d547`, STL repo @ `bf96450c75e635efb993676fe90c6456fb8a00af`.

## Check status (paste the last lines of each tool)
| Check | Command | Result | Session |
|---|---|---|---|
| Clearance C1–C4 | `python tools/check_clearance.py --json renders/s1_clearance.json` | `C1 PASS` · `C2 PASS` · `C3 FAIL` (3 lines, all neck/head — S2 scope) · `C4 height=192.6 mm (cap 200.0) PASS` · `OVERALL: FAIL` | 1 |
| Sweep R1 | `python tools/sweep_check.py --joint <name> --step 20` | 8/10 leg joints PASS; knees FAIL on inherited servo-servo clash (below) | 1 |
| Parts P1–P4 | `python tools/check_parts.py` | `OVERALL: FAIL` — 10 FAIL lines, all thin-wall P4 | 1 |

Real outputs:

C3 remaining FAILs (all neck/head, Session 2 scope — do not treat as regressions):
```
FAIL neck_pitch  (in neck)            penetrates right_shell   (trunk_base)   by 2.83 mm
FAIL head_pitch  (in neck)            penetrates neck_pitch    (neck_pitch)   by 5.90 mm
FAIL head_yaw    (in yaw_roll_motion) penetrates motor_support (jaw_soft)     by 0.73 mm
```

R1 per-joint (renders/s1_sweep.txt, step 20):
```
left_hip_yaw/right_hip_yaw/left_hip_roll/right_hip_roll/left_hip_pitch/right_hip_pitch/left_ankle/right_ankle: PASS
left_knee / right_knee: FAIL
    at -45/+35/+45 deg  scs0009:{side}_ankle <-> scs0009:{side}_knee  depth 3.12 / 2.73 / 6.88 mm
```

## Parts changed so far (session 1 rows)
| Part STL | What was done | Watertight | Wall p10 |
|---|---|---|---|
| `trunk_base` | 2 hip_yaw pockets w/ cradle (`pocket_part.py` x2) + 4 bridge boxes (cradle↔plate weld) | True | 2.00 |
| `power_support` | 2 plain hip_yaw pockets; swept channels for both hip_roll servos (roll ±22 + yaw ±30) | True | 0.72 |
| `yaw2roll` | hip_roll pocket+cradle, 2 wrap bridges, cap-end shave, band shave, **tail-open** (env+1.2, y>13) | True | 2.00 |
| `bearing_roll` | same recipe as yaw2roll (correct instance = idx 49, not the mirrored idx 12) | True | 2.00 |
| `upper_leg_left`/`_right` | hip_pitch + knee pockets w/ cradles; swept channel for ankle servo swing (~2% vol) | True | 0.72 |
| `upper_leg_rigidity_plate` | knee pocket w/ cradle + strap bridge; thickened x ×~2.4 total | True | 1.08 |
| `leg` | ankle pocket+cradle, idler pin (idler_boss), below-axis + knee-rim + ledge shaves, swept cuts | True | 0.70 |
| `ankle_left` | SPEC 5.5 recipe: `--axis x --plane 30 --side - --delta 9`, idler seat, swept channel grow 1.5 | True | 1.28 |
| `ankle_right` | mirrored recipe: `--plane -30 --side + --delta 12`, idler seat, swept channel grow 1.5 | True | 1.29 |
| `foot_left`/`foot_right` | swept channel for ankle servo (grow ~2.3) | True | 1.26 |
| `hip_l` | idler-boss seat re-cut (pin removed again — case points outboard, pin engaged nothing) | True | 1.74 |

## Open problems / things I could not do
- **Knee servo-servo clash (inherited, physical):** `scs0009:ankle ↔ scs0009:knee` interpenetrate
  −45..−34 (3.12 mm) and +19..+45 (0.18 → 6.88 mm). Identical on the ORIGINAL scaled parts —
  the 0.72× body makes SCS0009 cases overlap at deep knee flexion. **Usable range −33° to +21°**
  (check threshold 0.5 mm; zero-contact limit is −33°/+18°). No ankle roll fixes it
  (90: R knee vs hip_roll; 180: case below sole, impossible; 270: L knee vs hip_roll) and no knee
  roll either (0/90/180/270 all fail somewhere). Software must limit knee travel or Session 2+ revisits.
- **Thin walls (P4, all p10 < 1.2 spec, reasons):**
  - `leg` 0.70 (baseline 0.94): cradle/pocket walls in the ankle-yoke swing zone — can't thicken
    (inward = pocket void, outward = sweep contact). Clearance-bound.
  - `power_support` 0.72 (baseline 1.05): swept-channel walls, multi-directional, distributed;
    thicken_plate N/A (non-flat, would distort pockets).
  - `upper_leg_left/right` 0.72 (= baseline): pre-existing thin original shell, unchanged by this session.
  - `upper_leg_rigidity_plate` 1.08 (baseline 0.72, improved): thin readings are insertion-slot
    feather edges, not plate thickness; 3 thicken attempts can't fix them.
  - Out of scope (untouched): bottom_head_shell 0.90, m12_lens_holder 0.65, soft_mouth_top 0.58,
    sole_left 1.12, sole_right 1.14.
- mujoco version pin (see S0 note).

## Decisions that need the human
- **Knee usable range:** accept −33°/+21° (or −33°/+18° strictly zero-contact) as the gait limit,
  OR redesign joint spacing/geometry later (would change joints — out of session scope by rule).
- **leg wall_p10 0.70:** acceptable for print (walls are cradle shell backed by the servo case)
  or requires a leg re-design with a bigger shin cavity — again a geometry change.
- power_support/upper_leg/rigidity_plate thin walls as listed above.

## Next session
`Session 2` — neck + head servos: the 3 remaining C3 lines (neck_pitch↔right_shell,
head_pitch↔neck_pitch, head_yaw↔motor_support) plus their P1–P4 parts.
