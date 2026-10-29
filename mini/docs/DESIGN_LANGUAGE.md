# Knoll Mini — surface design language (refinement sessions)

Goal: production-ready look. Function (joints, axes, ranges, servo
positions, mounting interfaces) is frozen; only the skin changes.
Every generator is deterministic CAD (build123d, or trimesh+manifold3d
on analytic primitives only) — never raster contours or hand-edited STL.

1. **Clean designed surfaces.** Outer skins come from 2D profiles:
   extruded/lofted boxes with true fillets. No triangle soup, no
   wrinkled boolean scars, no sliver facets.
2. **One edge family.** Outer edge fillet 1.5 mm (0.8 mm on small
   parts); chamfers only where deliberate. Same radius everywhere.
3. **Walls.** Shells 2.0 mm (never below 1.6 mm); ribs 2.0 mm;
   0.3 mm print clearance on mating faces.
4. **Panel lines.** 0.4 mm wide × 0.3 mm deep grooves, only on
   deliberate seams (raised panels, parting lines, service doors).
5. **Openings.** Only functional, always rounded: cable slot (2 mm
   fillet), screw access, camera, servo horn travel, grilles.
   Vent/speaker grilles use ONE pattern: Ø1.8 mm holes, 3.2 mm pitch,
   straight grid.
6. **Hide the hardware.** Servos, horns, cables, boards, battery live
   inside shells or behind covers; parting lines are placed on purpose
   (a lip or brim band, not a raw butt joint). Moving shells keep
   ≥ 1.0 mm gap to neighbours through the full range (sweep_check).
7. **Printable.** Each part prints without supports in a stated
   orientation; overhangs ≤ ~55° or drafted. Part names stay stable
   so assembly.py / build_mjcf.py keep working.
8. **Proportions.** Keep the original Microduck silhouette on
   legs/trunk; the head uses the BDX-droid look (filleted wide helmet,
   angled lower-front chamfer, raised top panel, recessed eye rings,
   corner grilles, brim parting line, antenna bosses).
