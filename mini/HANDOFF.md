# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last finished session: `2` (neck + head attach, cable channel).
- S = 0.72. Height: `192.6 mm`. Model mass: `~379 g (est., [U])`.
- Python: `mini/.venv`, CPython 3.12.2. **mujoco pinned to 3.10.0** — 3.11+ ships no cp312 macOS x86_64 wheel (Intel Mac).
- Upstream pins verified: `microduck_rl @ 29e887ecfbf5d37144759e5a9f8a176dfb83d547`, STL repo @ `bf96450c75e635efb993676fe90c6456fb8a00af`.
- spec.py now: `EXTRA_PARTS = [("neck","neck_frame")]`, `REMOVED_PARTS = ["neck"]` (plates STL in parts/attic/).

## Check status (real outputs this session)
| Check | Command | Result |
|---|---|---|
| Clearance C1–C4 | `python tools/check_clearance.py --json renders/s2_clearance.json` | `C1 PASS` `C2 PASS` `C3 PASS` `C4 height=192.6 (cap 200) PASS` · **OVERALL: PASS** |
| Sweep neck_pitch | `python tools/sweep_check.py --joint neck_pitch` | `swept -45..+45 deg: PASS` |
| Sweep head_pitch | `python tools/sweep_check.py --joint head_pitch` | `swept -45..+45 deg: PASS` |
| Sweep head_yaw | `python tools/sweep_check.py --joint head_yaw` | `swept -120..+120 deg: PASS` |
| Sweep head_roll | `python tools/sweep_check.py --joint head_roll` | **FAIL — expected**: contacts vs `jaw`, `top_head_shell`, `bottom_head_shell`, `neck_pitch`, `motor_support` (old head shells; replaced in S3) |
| Parts P1–P4 | `python tools/check_parts.py --only neck_frame,neck_pitch,yaw_roll_motion,motor_support,left_shell,right_shell` | all 6 PASS (plus trunk_base 2.00); other FAIL lines are the documented S1 thin parts |
| Renders | `render_views.py` + `--q neck_pitch=-30 head_pitch=30 head_yaw=90 --out renders/s2_neck` | wrote renders/{front,side,top,iso}.png + renders/s2_neck/ |

## Session 2 — what was built
- **`neck_frame`** (NEW, replaces the two `neck` plates): cradle pair for neck_pitch + head_pitch
  merged with the plates, hull clipped to **x≤−1 mm** (the full --hull wedge at +x could not swing
  ±45° past the trunk — hull fill on the far side of the pivot only). Then:
  - `idler_boss` Ø10 pin on the head_pitch axis (6700ZZ inner race), seat cut in yoke arm.
  - **head_pitch corridor**: difference vs union(61 poses of the exact yoke mesh −45..+45 ∪ both
    servo pocket cutters) — merging pockets into the cutter kept the boolean output manifold.
  - **hip/trunk notch**: difference vs union(31 inverse-swept poses of all trunk_base items) +
    cutter dilated by ±0.5 mm x/z translations for real clearance margin.
  - **Ø6 cable channel**: groove along the top, axis z=31.0, neck_frame frame:
    (10.6,+10.5) → (10.6,−11) → (−10.0,−15.5) → (−10.3,−36) → (−10.1,−39) — enters the trunk-end
    top edge, runs the +x face past the neck_pitch band, crosses the inter-pocket dead zone,
    exits the left face near the head_yaw side. 0 mm³ intersection with servo pockets.
  - Final: `19.02 cm3 watertight=True bodies=1 wall_p10=2.00mm`, ext [33.1 55.2 35.7].
- **`neck_pitch` (yoke)**: stretched idler arm +12.5 mm at x=−6.5 (clears cradle floor at
  part-x −22.31), idler seat Ø15.1×~1.7 + Ø11 through, swept servo corridor (−90..+90, grow 0.8),
  plus a Ø19/Ø12.2 ×2.8 mm reinforcement ring around the seat (coaxial = sweep-invariant).
  `2.00 cm3 wall_p10=1.40mm` (was 0.58 before the ring).
- **`yaw_roll_motion`**: head_yaw pocket+cradle. **`motor_support`**: head_roll pocket+cradle +
  swept cut vs head_yaw servo over head_roll ±25 (grow 0.8). Ready for S3.
- **`trunk_base`**: swept corridor vs convex-hull(neck_frame) over neck_pitch ±45 (−15.5%); the
  neck_pitch servo corridor came for free inside it (0.0% on the second pass).
- **`right_shell`**: same corridor (−7.6%); **`left_shell`**: second corridor (0.0% — already clear
  from the S2 step-2 servo corridor).
- Boolean hygiene note: manifold-engine differences vs swept unions leave degenerate self-loop
  faces and coincident-vertex slivers that only appear AFTER the STL round-trip. Fix used:
  keep largest component, then `faces[(a==b)|(b==c)|(a==c)]` delete, re-verify watertight on
  the reloaded file. Grow cutters by union-of-translations (±0.5 mm), never vertex normals.

## Interfaces for Session 3
- **`motor_support`** extents in jaw_soft frame: x −28.44..+24.48, y −18.86..+45.71, z −5.11..+13.82
  → `[52.9 × 64.6 × 18.9]` mm. head_roll shaft along −y at (0, 12.96, 3.24); outer faces untouched.
- **Cable channel**: neck_frame-frame polyline above; Ø6, ~4.3 mm deep guide groove; intended
  path trunk → head_yaw. Ends near (−10,−39,31) — pick it up into the head in S3.
- **Idler pin** on neck_frame at head_pitch axis (0,−36) z≈30→36.5 — 6700ZZ drops on the yoke seat.

## Open problems / things I could not do
- head_roll sweep FAIL vs the OLD head shells (jaw, top/bottom_head_shell) — by design, S3 replaces them.
- Thin-wall P4 list unchanged from S1 (leg 0.80, power_support 0.72, upper_leg_* 0.72, ankles ~1.1,
  soles 1.13, head shells, m12_lens_holder, soft_mouth_top) — all clearance-bound/pre-existing.
- neck_pitch sweep needed BOTH sides trimmed: trunk_base+shells corridors AND a bracket notch —
  the clipped bracket still kisses the hip servos at ±45 extremes (now clear with 0.5 mm margin).

## Decisions that need the human
- **neck_frame deviates from the plain `merge_body_frame --hull` recipe**: the full hull could not
  physically swing neck_pitch ±45 past the trunk (bracket flank is ~52 mm from the pivot).
  Shipped = hull clipped to x≤−1 (keeps the −x spine that ties both cradles + the plates).
- Same thin-wall list as S1 — accept as print notes or redesign later.

## Next session
`Session 3` — BDX head: replace jaw/top_head_shell/bottom_head_shell on `jaw_soft` around
`motor_support` (extents above) + the head_roll/head_yaw interfaces, pick up the cable channel,
then head_roll sweep must pass −25..+25.
