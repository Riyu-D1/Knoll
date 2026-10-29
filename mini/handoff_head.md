# Handoff — Refinement A follow-up: head v3 (branch `refine-head`)

Round 2 of head refinement.  The user reviewed v2 images with a true z-buffer
render and rejected 7 design issues; all are fixed in `tools/make_head_bdx_v2.py`
(regenerated geometry — no STL hand edits).  A new renderer
`tools/render_zbuf.py` (numpy, orthographic, per-face lambert, back-face culling,
real depth test) replaces `render_solid.py` for review — the old painter's-sort
images were misleading (see-through shells, stray diagonals).  `render_solid.py`
is kept for compatibility only; do not trust it for geometry review.

## The 7 review findings and what was done

1. **Open rear/underside.**  True cause: not a hole in the back wall (probes
   showed it closed) but the large floor/neck opening exposing the cavity from
   below-behind.  Fix: the floor is now solid and carries a 2 mm **removable
   closing plate** (`head_back_plate.stl`) seated flush in a rounded-rect
   pocket: 0.8 mm gap line all round, 4 × Ø2.2 countersunk screws into two
   ledge strips left in the pocket, and a rounded-rect neck/cable hole
   (ly -38.8..22.5 × lz -42..16.3, r5) sized to the measured swept crossing at
   the plate band (ly -37.2..20.9 × lz -40.4..14.7 + ~1.5 mm).  A first version
   with the plate 2 mm below the floor failed `sweep_check head_pitch`
   (13 mm into trunk at -45°); flush mounting adds zero swept volume -> PASS.
2. **Open-ended L groove** replaced by a closed, symmetric rounded-rect
   panel-line frame on the top face (0.4 mm wide, 0.3 mm deep, inset 3.5 mm
   from the walls, mirrored L/R).
3. **Loose wedge at lower front-left** — the bulge loft sections are now
   rounded rectangles (was trapezoid polygons); the -ly protrusion reads as a
   smooth drafted cheek pod, silhouette is a clean rounded box.
4. **Unexplained rectangular slot** — was a real see-through sliver: the
   front-bottom chamfer line `CH_FRONT ((-56,-7),(-47,-15))` pierced the
   interior corner (lz -54, lx -13).  Shortened to `((-56,-12),(-53,-15))`
   keeping ~1 mm wall; verified closed by ray probes and renders.
5. **Missing right lens** — added `head_eye_lens_r.stl`: same plug+flange
   profile as the left lens but an annular ring with a Ø10.4 bore, so the
   camera aperture/axis is unchanged.
6. **Antennae** — now tapered stalks (Cone Ø4.4 -> Ø1.5, h 8 mm) with dome
   tips, sunk 3 mm into the same bosses, ±30° tilt, symmetric.  Span height
   incl. antennae = 197.8 mm < 200 cap.
7. **Mesh weight** — export tolerance loosened (TOL 0.12, ANG 0.30):
   `top_head_shell` 67,030 -> 15,716 faces, `bottom_head_shell` 2,178,
   `head_back_plate` 1,576 — all < 25k, still smooth in z-buffer renders.

## Checks — all actually run on the regenerated parts

| check | result |
|---|---|
| `sweep_check --joint head_yaw` (-120..+120) | PASS |
| `sweep_check --joint head_pitch` (-45..+45) | PASS (plate flush redesign fixed 13 mm collision) |
| `sweep_check --joint head_roll` (-25..+25) | PASS |
| `sweep_check --joint neck_pitch` (-45..+45) | PASS |
| `check_clearance` | PASS (C1-C3 gaps OK, C4 height 197.8 mm < 200) |
| `check_parts` (head parts) | all PASS, watertight: top 1.70, bottom 1.00, plate 2.00, lenses 1.40, antennae 1.60 mm wall_p10 |
| `build_mjcf` | regenerated `model/knoll_mini.xml` (left uncommitted per rules); jaw_soft mass 85.6 g, model 444.0 g |
| `torque_check` | PASS, 0 joints over rated 0.069 N.m |
| `head_protrusion` | head_yaw **enclosed 0/3185** (was 110); head_roll 301 bottom-only via required neck hole; neck servos visible below head (inherent, as v1/v2) |
| generator swept-cloud report | min dist to shells 2.69 mm, 0 points < 1.0 |

Pre-existing `check_parts` FAILs are non-head parts (ankles, legs, soles,
power_support, m12_lens_holder) — untouched.

## Render evidence — `mini/renders/zbuf/head_v3/`

True z-buffer renders of the head assembly (servos dark red, lenses blue,
elec green).  Every image was opened and inspected:

- `front.png` — flat face, two proud bezel rings, both lenses present (right
  ring shows open camera bore), mic/lamp dots, no slots, clean rounded box.
- `back.png` — fully closed rear wall; lip band + seam pilots; no rectangle.
- `left.png` / `right.png` — grille dot fields both walls, seam line, the -ly
  bulge reads as a deliberate raised pod; no wedge remnant.
- `top.png` — raised panel + closed panel-line frame, tapered antenna stalks.
- `bottom.png` — the closing plate covers the underside: gap line round its
  edge, 4 screw countersinks, rounded-rect neck hole only.
- `iso.png` / `iso2.png` — front-left / rear-right 3/4: panel, lip, eyes,
  antennae, pod; no floating parts, no unexplained cutouts.
- `section_iso.png` / `section_left.png` — sagittal cut (y<=0, capped):
  all servos/boards fully inside the shells.

BDX comparison (`ref_bdx_head.png`): wide boxy lid, two big round eyes, side
vent grilles, two antennae — all present and intentional.

## Unresolved / notes

- Neck-region servos remain visible below the head silhouette (they are neck
  hardware, not inside the head) — same class as accepted in v1/v2; the plate
  cut the underside exposure to just the neck hole (head_yaw now 0).
- `elec_eye_rings_x2.stl` re-exported (identical design, tolerance change).
- `mini/model/knoll_mini.xml` regenerated but intentionally uncommitted.
- Mass: head body 85.6 g (was ~80 g target; +plate and +lens ~5 g).
- Parts replaced this round kept the same filenames; the v1 originals remain
  in `mini/parts/attic_refine/*_v1.stl` (the interim v2 files were
  regenerated in place).
