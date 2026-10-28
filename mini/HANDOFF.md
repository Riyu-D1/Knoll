# HANDOFF: Knoll Mini

Every session reads this first and rewrites the "Current state" and "Next session" sections at the end.
Keep it under 150 lines. Paste the real check output (trimmed to the summary lines).

## Current state
- Branch: `build/microduck-bdx-mini`. Last finished session: `3` (BDX head shell, eyes, electronics).
- S = 0.72. Height: `198.2 mm` (cap 200). Model mass: `~390 g (est., [U])`.
- Python: `mini/.venv`, CPython 3.12.2. **mujoco pinned to 3.10.0** — 3.11+ ships no cp312 macOS x86_64 wheel.
- Upstream pins verified: `microduck_rl @ 29e887ecfbf5d37144759e5a9f8a176dfb83d547`, STL repo @ `bf96450c75e635efb993676fe90c6456fb8a00af`.
- spec.py now: `HEAD_MODE = "bdx"`, `EXTRA_PARTS = [("neck","neck_frame")]`, `REMOVED_PARTS = ["neck"]`.
- 8 replaced head STLs moved to `parts/attic/` (top/bottom_head_shell, face_part, jaw, jaw_soft,
  soft_mouth_top, noenoeil, m12_lens_holder). BDX parts in `parts/current/bdx_*.stl`.

## Check status (real outputs, end of session 3)
| Check | Command | Result |
|---|---|---|
| Clearance C1–C4 | `python tools/check_clearance.py` | `C1 PASS` `C2 PASS` `C3 PASS` `C4 height=198.2 (cap 200) PASS` · **OVERALL: PASS** |
| Sweep head_roll | `python tools/sweep_check.py --joint head_roll` | `swept -25..+25 deg: PASS` |
| Sweep head_pitch | `python tools/sweep_check.py --joint head_pitch` | `swept -45..+45 deg: PASS` |
| Sweep head_yaw | `python tools/sweep_check.py --joint head_yaw` | `swept -120..+120 deg: PASS` |
| Parts P1–P4 | `python tools/check_parts.py --only bdx_head_top,bdx_head_bottom,bdx_face_plate,bdx_eye_bezel_l,bdx_eye_bezel_r,bdx_eye_diffuser_l,bdx_eye_diffuser_r,motor_support` | all 8 PASS — face_plate p10=1.76, head_top 1.75, head_bottom 1.49, motor_support 1.22, bezels 4.4, diffusers 1.50 · **OVERALL: PASS** |
| Mount | `python - <<'PY' ... signed_distance(motor_support, bdx_head_top.vertices)` | `max penetration 0.35 mm · 583 vertices within 0.3 mm` (needs ≤0.6, ≥50) |
| Elec vs parts | collision audit all `elec_*` vs all parts | `penetrations >0.2mm: NONE` |
| Renders | `render_views.py` + `--q head_yaw=90 head_roll=20 head_pitch=-30 --out renders/s3_head` | wrote renders/{front,side,top,iso}.png + renders/s3_head/ |

## Session 3 — what was built
- **BDX head** (`tools/make_bdx_head.py`, `wall=1.8`): big leaning helmet ~96×92 mm, +12° nose-down
  lean. `bdx_head_top` + `bdx_head_bottom` shells, `bdx_face_plate` chin cover, `bdx_eye_bezel_l/r`
  (OD45 proud rings), `bdx_eye_diffuser_l/r` (Ø37.6×1.5 white PETG discs), brow ridge +4.5 mm.
- **Mounting**: posts moved to the solid back block of `motor_support` (`posts=[(-16,3),(-25,3)]`,
  `ms_y=(11,-22)` in the generator's H frame) — the S2 pocket had hollowed the original side-wall
  spots. Contact 0.35 mm pen / 583 verts. **4 × Ø1.6 × 6 pilot holes** drilled into motor_support,
  coaxial with the posts (`trimesh.creation.cylinder` difference in the ms frame).
- **Swept cuts re-derived** after regeneration: bdx_head_bottom vs `neck_frame`/`neck_pitch`/
  `yaw_roll_motion` hulls (head_roll ±25) + vs `neck_pitch` (head_yaw ±120) + a grown exact-mesh
  margin cut; `motor_support` corridor vs exact swept `yaw_roll_motion` (largest body kept);
  `jaw_soft` bearing pair relieved via instance-explicit boolean; `bdx_head_top` back-rim relief
  vs ms back block; `bdx_face_plate` + `elec_xiao` corridors vs `neck_pitch` (head_yaw ±120).
- **face_plate**: regenerated sliver failed P4 (0.78). Fixed with an internal backing tray +
  edge ribs bonded to the cover, socketed +0.15 around bezels/electronics → p10 1.76, 1 body,
  watertight, 9.7 cm³. Uniform thicken/crop/doubler variants were tried and rejected (collisions
  or knife edges).
- **Electronics** (all jaw_soft frame, pen ≤0.2 verified pairwise incl. servo envelopes):
  - `elec_xiao_esp32s3_sense` 21×17.5×15 behind cam window (y0,z−6, front ~2 mm inside wall);
    chamfered vs bezels/diffusers/rings (+0.2) and vl53, + neck_pitch yaw corridor.
  - `elec_eye_rings_x2` Ø37×3 pair behind the bezels; `elec_vl53l0x` 4×13×11 at ToF site
    (y12,z−9), chamfered vs bezel annulus (+0.3).
  - `elec_max98357_speaker` Ø23×5 disc at back-left of the head (J(4,30,32), −x-facing, grille
    band z_H −7.5..15.5) — the spec spot behind the centre grille is solid `motor_support`
    cradle; relocated [U].
  - `elec_buck_5v` 6×15×20 in the upper dome interior J(16,0,10) — low/back spots all swept
    into neck parts or `trunk_base`; this is the only sweep-clean volume found.
- **Cable route** (Ø6, neck channel → XIAO, no cut needed): exits neck_frame channel near
  H(23,−20.6,−20.9), rises along the right side of the cradle to H(23,−14,−18), then one straight
  jog to the XIAO rear corner H(38,−10,−6). Verified 0 mm intersection vs `motor_support` and
  shells. Clip points: channel exit, mid-rise, and at the XIAO socket edge; the service loop is
  a ~75 mm arc coiled in the right-side cavity (J_y ≈ −14..−22) so head_yaw ±150° pays out
  ≤60 mm of slack.
- **Look review** (renders/front,side,s3_head): the head reads as a single large rounded helmet
  leaning ~12° forward with the two big dark eye bezels dominating the face — convincingly
  BDX-droid at this scale. Posed view (yaw 90/roll 20/pitch −30) shows the chin plate closing
  the lower face and clearing the trunk. Suggested change: the eyes read dark/recessed — print
  the diffuser discs in opaque white and add a thin white rim inside the bezels.

## Interfaces for Session 4
- Head: all parts in `jaw_soft` frame; `motor_support` is the only keep-part (roll shaft at
  (0,12.96,3.24) along −y, 4 pilot holes on the posts).
- Electronics masses in spec.ELECTRONICS (jaw_soft rows) are [U] estimates.
- face_plate has a moulded socket/tray shaped around the XIAO position (front, between eyes).

## Open problems / things I could not do
- `elec_xiao_esp32s3_sense` and `elec_vl53l0x` are no longer clean boxes — chamfered corners
  from the socket cuts (documented; still readable as boards).
- Speaker is NOT behind the centre grille holes (cradle fills that space) — sits at back-left;
  a real grille should be cut there or the cradle pocketed in a later session.
- The S1 thin-wall list still stands (leg, power_support, ankles, soles...) — unchanged, P4
  cosmetic-bar exceptions documented in earlier sessions.

## Decisions that need the human
- Speaker relocation (back-left, off the printed grille) and buck placement (top of the head
  interior) are [U] judgement calls — the spec sites are physically occupied by the cradle.
- The face-plate tray bumps the removable cover to 9.7 cm³; if a slimmer cover is wanted it
  needs a different thickening scheme (e.g. ribs only on the rim).
- Cable clips and the 75 mm service-loop coil are described but have no printed anchors yet —
  decide whether Session 4 should model them.

## Next session
`Session 4` — legs/feet or torso cosmetics per the next prompt; nothing from this session blocks it.
