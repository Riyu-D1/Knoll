# Knoll Mk1 — Shell v0 Concept Renders

**Status:** concept visualisation only — NOT validated mechanical geometry. Produced 2026-10-29 with Blender 4.5.14 (EEVEE), headless.

This directory contains the first 3D visual prototype of the Knoll Mk1 external shell: three shell variants on a shared dimensioned robot proxy, studio renders, an exploded service view, and colourway comparisons.

## Recommended starting concept

**Variant B — Modular Terrarium.** It carries the repo's engineering intent most directly: replaceable face plate, visible service seams, rim fasteners, magnetic topper dock and rear hatch all read as real assembly features rather than decoration. Variant A (Soft Moss) is the softer alternative if character appeal outranks visible repairability; Variant C (Sculptural) is the most distinctive silhouette but its brow ledge is a mild recovery snag and reads slightly bill-adjacent. See `DESIGN-REVIEW.md`.

## Files

| File | Contents |
|---|---|
| `knoll-shell-v0.blend` | Editable Blender scene: all 3 variants, exploded assembly, colourway trio, materials, studio rig, cameras |
| `build_scene.py` | Reproducible parametric build + render script (edit `P` dict and `PALETTES` at top) |
| `img/comparison.png` | Variants A / B / C side by side, same scale, camera and lighting |
| `img/hero-variant-{a,b,c}.png` | Three-quarter studio view per variant |
| `img/ortho-{a,b,c}-{front,side,rear,34}.png` | Orthographic design sheet per variant (front / left side / rear / three-quarter) |
| `img/exploded-b.png` | Serviceability view of Variant B: dome, face plate, topper and hatch separated from chassis proxy |
| `img/colorways.png` | Variant B in Sage / Graphite / Terracotta |
| `img/detail-{eyes,topper,seam}.png` | Close-ups: LED face, topper dock, seams + rear hatch |

## Regenerating

```bash
blender --background --python build_scene.py -- --renders all
```

Optional subsets: `--renders comparison|heroes|ortho|exploded|colorways|details`. Requires Blender ≥ 4.x (EEVEE Next). No addons needed.

## Scene organisation

- Collections: `VAR_A`, `VAR_B`, `VAR_C` (assembled variants), `VAR_X` (exploded B), `VAR_COL0..2` (colourways), `LBL_*` (labels)
- Named objects per brief: `SHELL_DOME`, `SHELL_DOME_SKIRT`, `FACE_PLATE`, `EYES_L/R`, `SMILE`, `TOPPER_*`, `REAR_HATCH`, `CHASSIS_PROXY`, `LEG_{L,R}_*`, `FOOT_{L,R}*`
- Key dimensions are parameters in `build_scene.py` (`P` dict): dome 170×160 mm, skirt 20 mm + cap 115 mm, face position/size/tilt, eye spacing, topper height, leg joint heights, foot size — all adjustable without rebuilding

## Honesty notes

- Legs are **visual proxies** matching the joint heights and hip spacing in `design/mechanical-architecture.md`; they contain no servo bodies, bearings or cable channels.
- Panel seams on B are surface curves, not actual split geometry; real shell segmentation is a CAD task.
- Materials approximate matte FDM filament; renders are lighting-neutral (no DOF, no bloom) on purpose.
