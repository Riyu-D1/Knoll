# Handoff — Refinement A: head (branch `refine-head`)

## What changed

The BDX head surfaces were rebuilt from scratch by a new CAD generator,
`tools/make_head_bdx_v2.py` (build123d 0.13.0 in `~/Knoll-cad-venv`), replacing
the raster-derived/faceted geometry produced by `tools/make_head_bdx.py` (which
remains in the tree, superseded). All replaced STLs moved to
`mini/parts/attic_refine/*_v1.stl`.

Parts regenerated in `mini/parts/current/`:

- `top_head_shell.stl`    — watertight, 34.2 cm³
- `bottom_head_shell.stl` — watertight, 11.6 cm³
- `head_antenna_left/right.stl` — watertight
- `head_eye_lens_l.stl`   — watertight
- `elec_eye_rings_x2.stl` — watertight (non-printed electronics placeholder)

New shell design (per the BDX photo + `mini/docs/DESIGN_LANGUAGE.md`):

- Rounded-rectangle helmet box, 6 mm main corner radius, 3 mm on the raised
  panel (was ~2 mm and wrinkled); angled lower-front chamfer kept.
- Raised top panel with a 0.4 mm wide / 0.3 mm deep panel-line groove.
- Two eye bezels as proper proud rings (2.8 mm proud of the face) with recessed
  seats behind them; eye/bore/camera apertures unchanged (Ø21 bezel, Ø16 bore,
  Ø10 camera at ly 0 / lx 11.2; second eye ly -19.5). Lamp (11,18) and mic
  (-1.5,-16) holes kept.
- Two side-wall grilles, one consistent hole pattern on both walls.
- Deliberate parting line at lx=-3 with a conformal lip: the lip band
  lx -6.2..-1.5 is grown 1.5 mm proud and overlaps the top shell wall, so the
  seam reads as a designed brim (this makes outer extent 1.5 mm proud of the
  old envelope on all sides at the seam band).
- Antenna mounts as small filleted bosses with screw pilots; rods kept at
  ly ±29, lz 22, ±30° tilt. Overall height incl. antennae = 198.7 mm < 200.
- Neck opening is now a clean rounded rectangle (ly -28..24, lz -43..17.5,
  r 8) plus the -ly tab slot (ly -41..-24, lz -27..0.5, r 3), containing the
  swept neck footprint +2 mm. The -ly wall carries a drafted bulge reaching
  ly -46 over lz -31..+5 so the deepest swept reach (ly -40.04) stays INSIDE
  the cavity instead of needing a side-wall notch.
- Chassis tabs, seam-screw pilots (4 side @ lx -4.5, 2 front @ ly ±18),
  interior floor/ceiling and all mounting interfaces unchanged.
- STL export pipeline: OCC tessellation + cleanup (drop degenerate faces,
  weld, fill pinholes) → every exported part watertight.

## Checks (all actually run, real output)

| Check | Result |
|---|---|
| sweep_check head_yaw  -120..+120 | R1 OVERALL: PASS |
| sweep_check head_pitch -45..+45  | R1 OVERALL: PASS |
| sweep_check head_roll  -25..+25  | R1 OVERALL: PASS |
| sweep_check neck_pitch -45..+45  | R1 OVERALL: PASS |
| check_clearance.py | C1 PASS / C2 PASS / C3 PASS / C4 height 198.7 mm (cap 200) PASS / OVERALL PASS |
| check_parts.py head parts | bottom 1.65 mm p10, top 2.00, antennae 2.00, lens 1.40 (cosmetic ≥0.9) — all PASS, all watertight |
| build_mjcf.py | regenerated, jaw_soft body mass 80.1 g |
| torque_check.py | T1 stood PASS, T2 PASS, 0 joints over rated; model mass 438.5 g (target 350–450) |
| head_protrusion.py | see note below |
| swept-cloud clearance | full 3.36 M-pt cloud vs final shells, voxel-EDT: min distance to shell material 1.41 mm, 0 points < 1.0 mm |

check_parts.py on the full part set also shows pre-existing thin-wall FAILs on
`upper_leg_*` parts — those are not head parts and were not touched by this
work.

## head_protrusion.py result (real numbers, not 0)

- neck_pitch 1804/3185, head_pitch 1458/3185 — `[neck region]`, entirely below
  the head (lx -16..-69); inherent to the open-neck design, same as upstream.
- head_yaw 110/3185, head_roll 301/3185 — all visible points lie inside the
  neck-entry opening footprint/vestibule (verified by point sampling); nothing
  passes through a shell wall, seam or feature.
- Improvement vs the first v2 iteration: the deep -ly bulge eliminated the
  side-wall notch exposure (head_yaw "right" 21.67 mm → 0; visible samples
  138 → 110).

## Bottom closing plate — decision

Considered per the prompt and rejected: the swept neck/head hardware fills
essentially the whole opening footprint (min clearance 1.41 mm), so any plate
with a smaller hole would collide in motion, and a plate with the same hole
adds nothing — the floor ring is already part of the bottom shell. Documented,
not built.

## Renders (all opened and inspected)

- Before: `mini/renders/solid/refine_head_before/` (h_front/back/left/right/
  bottom/top/tq) — crumpled triangle-soup faces, jagged neck opening.
- After: `mini/renders/solid/refine_head_after2/` (same views) — clean rounded
  helmet, recessed eyes, raised panel, lip brim, grilles, antennae.
- Isolated parts: `mini/renders/parts_v2_final/` (each shell, 7 views).
- Reference studies: `mini/renders/ref_microduck/`, `mini/renders/ref_xgoduck/`.

## Unresolved / notes

- OCC sewing still leaves micro-sliver triangles (≤0.004 mm²) along boolean
  union seams; they appear as faint lines in flat-shaded renders but are
  sub-print-resolution and do not affect watertightness or wall thickness.
- The conformal lip makes the outer shell 1.5 mm proud around the seam band
  and the bezel rings sit 2.8 mm proud of the old face plane; both are
  deliberate design features and all collision/sweep checks pass with them.
- `mini/model/knoll_mini.xml` was regenerated (needed by torque_check) but is
  intentionally left uncommitted per the prompt rules.
- `tools/make_head_bdx.py` (v1 generator) left in place, superseded by v2.
