# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last finished session: `4` (head reverted to ORIGINAL Microduck head).
- S = 0.72. Height: `192.6 mm` (cap 200), measured on the concatenated assembly bbox `[[-45.1,-61.9,7.2],[69.4,61.9,199.8]]`.
- Python: `mini/.venv`, CPython 3.12.2. **mujoco pinned to 3.10.0** — 3.11+ ships no cp312 macOS x86_64 wheel.
- Upstream pins verified: `microduck_rl @ 29e887ecfbf5d37144759e5a9f8a176dfb83d547`, STL repo @ `bf96450c75e635efb993676fe90c6456fb8a00af`.
- spec.py now: `HEAD_MODE = "microduck"`, `EXTRA_PARTS = [("neck","neck_frame")]`, `REMOVED_PARTS = ["neck"]`.
- The 8 original head STLs are back in `parts/current/`; `bdx_*` + the old head `elec_*` are in `parts/attic_bdx/` (rejected, not deleted).

## Head decision (session 4)
- **Session-3 BDX head: REJECTED by the user** — do not use or improve it. The original Microduck
  head (dome + flat angled face + single Ø21.6 `noenoeil` cyclops puck, camera through the middle
  on the `m12_lens_holder` axis) is restored, scaled ×0.72.
- The `jaw` is FIXED (mouth servo dropped; jaw servo pocket unused). No moving jaw is modelled.
- Outside shape unchanged; only internal swept relief for the fatter SCS0009 neck hardware.

## Check status (real outputs, end of session 4)
| Check | Command | Result |
|---|---|---|
| Clearance C1–C4 | `python tools/check_clearance.py` | `C1 PASS` `C2 PASS` `C3 PASS` `C4 height=192.6 (cap 200) PASS` · **OVERALL: PASS** |
| Sweep head_roll | `python tools/sweep_check.py --joint head_roll` | `swept -25..+25 deg: PASS` |
| Sweep head_pitch | `python tools/sweep_check.py --joint head_pitch` | `swept -45..+45 deg: PASS` |
| Sweep head_yaw | `python tools/sweep_check.py --joint head_yaw` | `swept -120..+120 deg: PASS` |
| Parts P1–P4 | `python tools/check_parts.py --only top_head_shell,bottom_head_shell,jaw,motor_support` | all PASS — top 1.18, bottom 0.96 (cosmetic bar 0.9), jaw 1.22, motor_support 1.22 · **OVERALL: PASS** |
| Elec vs parts | pairwise boolean intersection, all `elec_*` vs all parts + each other | `intersections >1mm3: 0` |
| Renders | `python tools/render_solid.py` | wrote `renders/solid/{front,side,three_quarter,head}.png`, inspected |

## Session 4 — what changed
- **Revert:** `git mv` 8 original head STLs attic→current; bdx_* + 5 old elec_* → `parts/attic_bdx/`;
  `motor_support`/`neck_pitch`/`yaw_roll_motion` restored to the Session-2 state (S3 had only
  removed material); `HEAD_MODE` back to `"microduck"`.
- **head_roll fix (was the only failing sweep):** the S2 `yaw_roll_motion` SCS0009 cradle grew to
  z≤25.5 (was ≤13 upstream) and grazed the original shells. Swept cuts on HEAD parts only with new
  `swept_cut.py` modes — `exact:` mesh cutters, comma-list `--servo`, `--horn`, `--keep-largest`:
  - top_head_shell −6.8%, bottom_head_shell −6.8% (12 mm3 rim sliver dropped), jaw −4.7%,
    motor_support −3.4% (7 mm3 slivers dropped). Cutters: exact neck_frame/neck_pitch/yaw_roll_motion
    + head_pitch/head_yaw envelopes, grow 0.3, head_roll ±25.
- **Roll idler:** `assembly.py` skips `seeed_bearing__configuration_default` in the `jaw_soft` body —
  its Ø10.8 rim grazed static neck parts; the printed `motor_support` journal pin is the bushing
  (SPEC 5.4 allows bushing for the small default bearings).
- **Electronics** (`tools/make_head_elec.py`, jaw_soft frame, all pairwise <1 mm3 intersection):
  XIAO 21×17.5×6 right of the eye axis + OV2640 cube + ribbon; 2× Ø26/Ø18 halo rings around the
  lens barrel behind `noenoeil`; VL53L0X at the right ToF window; Ø22×4 speaker disc upper dome;
  6×18×15 buck on the left flank. All inside the original shells — silhouette unchanged.
- **Renderer:** `tools/render_solid.py` — trimesh + matplotlib Poly3DCollection, opaque shaded,
  writes `renders/solid/front,side,three_quarter,head.png`.

## Look review (renders/solid/*, inspected)
- Front: dome centred on the neck, angled flat face pointing down-forward, small dark eye/camera
  opening on the face. Legs/trunk/neck read normal.
- Side: correct original-head profile — dome with sloped face plate; head sits clean on the
  neck block; head_roll cradle (red SCS0009) visible at the junction, no shell blowout.
- Three-quarter: crown shows the original part's ribbed vent texture (upstream feature, not a
  defect). Face box + eye opening visible.
- Head close-up: dome, vent ribs, face plate with square eye opening, small latch detail on the
  face edge — all original geometry. No electronics visible from outside; no cradle poke-through.
- Known rendering limitation: flat-shaded facets only (no texture/colour per part type); internals
  are correctly hidden by the opaque shells.

## Interfaces for next sessions
- Head parts all live in `jaw_soft` frame; `motor_support` is the only keep-part (roll shaft +
  printed bushing journal; the seeed default bearing is intentionally absent).
- `elec_*` placeholders are non-printed (skipped by check_parts); regenerate via
  `tools/make_head_elec.py` if the layout must move.
- `swept_cut.py exact:<name>[:<body>]` cutters + `--horn` + `--keep-largest <frac>` are the tool
  for "part X grazes part Y during a sweep" — use boolean intersection volumes, NOT FCL depth
  (depth over-reports inside concave shells).

## Open problems / things I could not do
- The S1 thin-wall list still stands (leg, power_support, ankles, soles...) — unchanged, cosmetic-bar
  exceptions documented in earlier sessions.
- bottom_head_shell wall_p10 = 0.96 mm — passes the 0.9 cosmetic bar with little margin; if it is
  later thickened, re-run the head_roll sweep.
- Electronics sit with <1 mm3 intersections but several are within ~0.5 mm of a shell — real boards
  need foam/tape standoffs; mounting posts not yet modelled (allowed: small posts on shell parts).

## Decisions that need the human
- Speaker sits in the upper dome interior with no grille holes yet — drill a grille or leave.
- The Ø26/Ø18 halo rings are modelled for the common 12-LED mini ring [U] — confirm the real ring
  OD before printing.

## Next session
`Session 5` — mounting posts/grilles or torso cosmetics per the next prompt; nothing here blocks it.
