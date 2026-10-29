# Knoll Mini — enclosure design language (refinement)

Applied to every cosmetic part regenerated in the refinement sessions.
Reference looks: original Microduck shells (smooth rounded bathtub halves) for the
body/trunk proportions, xgoduck_hardware/structure (chassis + cover plates) for
structure, and the BDX droid photo (panelled, chamfered, boxy-but-designed) for
detailing, consistent with the Session-8A head.

## Form

- Outer surfaces are designed surfaces only: extruded/lofted 2D profiles, boxes
  and cylinders with real fillets/chamfers. No triangle-soup boolean relics, no
  raster contours, no wrinkles or sliver triangles on visible faces.
- Trunk keeps the Microduck silhouette: a smooth rounded backpack shell wrapping
  the back, top deck and flanks, with the neck rising through a rounded front-top
  port and the hip mechanisms exiting through the open bottom — like the original.
- Head keeps the Session-8A BDX box; trunk detail follows it.

## Numbers (one consistent family)

- Wall: 2.0 mm (min 1.6) on shells; ribs/bosses 2.0 mm; cosmetic parts P4 >= 0.9 mm.
- Outer edge fillet: 1.5 mm (0.8 mm on small parts) — the head uses the same
  chamfer/fillet scale; corners may read as either in that family.
- Panel-line groove: 0.4 mm wide × 0.3 mm deep, only on deliberate seams.
- Vent grille: Ø1.8 mm holes at 3.2 mm pitch, same everywhere.
- Print clearance on mating faces: 0.3 mm. Cover plates: Ø2 mm pilot dimples.
- Any opening must be functional AND designed: cable slot (rounded, 2 mm fillet),
  grille, screw access, joint/servo travel. All openings rounded.
- Moving vs static shells: >= 1.0 mm gap through the FULL sweep of every joint
  that moves them relative to each other (verified by tools/sweep_check.py).

## Structure

- xgoduck principle: the shell carries no servo loads; the chassis does.
  Covers close over the chassis; servo pockets/cradles stay untouched inside.
- Hardware hidden: servos, horns, cables, boards and battery live inside a shell
  or behind a cover plate; parting lines are placed on purpose.
- Battery: slides into the rear bay (power_support cage area) from the back and
  is hidden by the rear access cover — the original NP-F970 also sat out the back.
- Every part prints without supports in its stated orientation.
