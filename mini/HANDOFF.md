# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last commit: session-1 fix commit (knee clash resolved).
- Last finished session: `1` (body + legs SCS0009 conversion) + focused knee fix.
- S = 0.72. Height: `192.6 mm`. Model mass: `~379 g (est., [U])`.
- Python: `mini/.venv`, CPython 3.12.2. **mujoco pinned to 3.10.0** — 3.11+ ships no cp312 macOS x86_64 wheel (Intel Mac).
- Upstream pins verified: `microduck_rl @ 29e887ecfbf5d37144759e5a9f8a176dfb83d547`, STL repo @ `bf96450c75e635efb993676fe90c6456fb8a00af`.

## Check status (paste the last lines of each tool)
| Check | Command | Result | Session |
|---|---|---|---|
| Clearance C1–C4 | `python tools/check_clearance.py` | `C1 PASS` · `C2 PASS` · `C3 FAIL` (3 lines, all neck/head — S2 scope) · `C4 height=192.6 mm (cap 200.0) PASS` · `OVERALL: FAIL` | 1 |
| Sweep R1 | `python tools/sweep_check.py --step 20` | **all 10 leg/hip joints PASS** (knees now clear −45..+45); neck_pitch/head_pitch/head_roll FAIL = S2 scope; head_yaw PASS | 1 fix |
| Parts P1–P4 | `python tools/check_parts.py` | `OVERALL: FAIL` — 12 thin-wall P4 lines (list below); every part watertight | 1 fix |

Real outputs:

C3 remaining FAILs (all neck/head, Session 2 scope — do not treat as regressions):
```
FAIL neck_pitch  (in neck)            penetrates right_shell   (trunk_base)   by 2.83 mm
FAIL head_pitch  (in neck)            penetrates neck_pitch    (neck_pitch)   by 5.90 mm
FAIL head_yaw    (in yaw_roll_motion) penetrates motor_support (jaw_soft)     by 0.73 mm
```

R1 per-joint (renders/s1_sweep.txt, step 20):
```
PASS: left/right_hip_yaw, left/right_hip_roll, left/right_hip_pitch,
      left_knee, right_knee, left_ankle, right_ankle, head_yaw
FAIL: neck_pitch, head_pitch, head_roll   (all neck/head interpenetration — Session 2)
```

## The knee fix (supersedes the old "inherited clash" note)
The ankle↔knee servo-case clash (3.12/2.73/6.88 mm at −45/+35/+45) is **resolved**:
`SERVO_ROLL_DEG` is now `left_ankle=90, right_ankle=270` — a *mirrored pair*. Verified directly on
envelopes: 0.00 mm max depth over the whole knee sweep on both sides, and the ankle↔hip_roll pairs
are also clear. Same-sign 90/90 and 270/270 each fail on the opposite side; 180 puts the case below
the sole (impossible). Joint positions/axes/limits untouched — the roll only spins the servo about
its own shaft. Leg/ankle/sole/foot parts re-cut for the rotated envelopes (details in parts table).
`leg.stl` is one shared file instanced by bodies `leg` (T≈[-7,0,29.7]) and `leg_2` (T≈[-38.7,0,29.7],
rot180-z + y offset): the swing corridor had to be cut for **both** instances via each instance's T.
**Knee safe range: full −45..+45 PASS on both sides** — the earlier −33..+21 note no longer applies.

## Parts changed so far (session 1 rows)
| Part STL | What was done | Watertight | Wall p10 |
|---|---|---|---|
| `trunk_base` | 2 hip_yaw pockets w/ cradle + 4 bridge boxes | True | 2.00 |
| `power_support` | 2 hip_yaw pockets; swept channels for both hip_roll servos | True | 0.72 |
| `yaw2roll` | hip_roll pocket+cradle, wrap bridges, cap+band shaves, tail-open | True | 2.00 |
| `bearing_roll` | same recipe (correct instance = idx 49) | True | 2.00 |
| `upper_leg_left`/`_right` | hip_pitch + knee pockets w/ cradles; ankle-servo swept channel | True | 0.72 |
| `upper_leg_rigidity_plate` | knee pocket w/ cradle + strap bridge; thickened x ×~2.4 | True | 1.08 |
| `leg` | rebuilt: ankle pocket+cradle at roll-90, idler pin, swing corridors BOTH instances (convex-hull cutters +0.4 mm, added-material only, pin protected), housing-graze patch trims | True | 0.80 |
| `ankle_left` | rebuilt from scaled at roll-90: channel grow 0.5, idler seat, pin-notch | True | 1.12 |
| `ankle_right` | exact x-mirror of ankle_left (roll-270 layout) | True | 1.08 |
| `sole_left` | rebuilt from scaled: channel grow 0.7, skirt notch at +45 graze zone | True | 1.13 |
| `sole_right` | exact x-mirror of sole_left | True | 1.13 |
| `foot_left`/`foot_right` | rebuilt from scaled: swept channel, main body kept (seam slivers dropped) | True | 1.23 / 1.26 |
| `hip_l` | idler-boss seat re-cut (pin removed) | True | 1.74 |

## Open problems / things I could not do
- **Thin walls (P4, all p10 < 1.2 spec):**
  - `leg` 0.80 (was 0.70, improved): cradle/pocket walls inside the ankle-swing corridor —
    can't thicken (inward = pocket void, outward = swing path). Clearance-bound.
  - `power_support` 0.72 (baseline 1.05): swept-channel walls, multi-directional; thicken_plate N/A.
  - `upper_leg_left/right` 0.72 (= baseline): pre-existing thin original shell.
  - `upper_leg_rigidity_plate` 1.08: thin readings are insertion-slot feather edges.
  - `ankle_left` 1.12 / `ankle_right` 1.08: channel + pin-notch edges around the swing corridor —
    same clearance-bound category. New flag vs session-1 end (was 1.28 PASS at roll-0).
  - `sole_left`/`sole_right` 1.13: now touched (channel+notch); thin readings at notch rim.
  - Untouched/out-of-scope: bottom_head_shell 0.90, m12_lens_holder 0.65, soft_mouth_top 0.58.
- Session-1 note about a −33..+21 knee safe range is **superseded** — see "The knee fix" above.
- mujoco version pin (see S0 note).

## Decisions that need the human
- **Thin-wall P4 list above** — all clearance-bound or pre-existing; accept as print notes or
  redesign geometry in a later session.
- None blocking for legs: knees and ankles pass full ±45 with real clearance (0.4 mm cutter margin
  baked into the corridors; R1 counts >0.5 mm deeper-than-zero contacts only).

## Next session
`Session 2` — neck + head: the 3 remaining C3 lines (neck_pitch↔right_shell,
head_pitch↔neck_pitch, head_yaw↔motor_support), their sweeps (neck_pitch/head_pitch/head_roll
currently FAIL at up to 20.2 mm), and P1–P4 on those parts.
