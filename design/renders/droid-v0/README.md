# Knoll Mk1 — Droid v0 Concept Renders

**Status:** concept visualisation only — NOT validated mechanical geometry. Produced 2026-10-29 with Blender 4.5.14 (EEVEE), headless. Supersedes `design/renders/shell-v0/` as the active visual direction (kept for history).

This is the **agile-droid redirect** of Knoll Mk1: small biped droid archetype — compact torso, small actuated head, 2-DOF arms with hands, articulated legs — original geometry inspired by the Microduck *category*, not its design.

**Revised architecture (user-approved):** 15 DOF = 5/leg (unchanged joints) + 2/arm (shoulder pitch+roll) + 1 neck (pitch). Arm DOF chosen for genuine get-up push assist; see `DESIGN-REVIEW.md` for the mass/cost consequence.

## Recommended starting concept

**Variant A** — the friendly rounded droid: warmest character while still reading agile, least generic, furthest from a copy of anything. **B** is the modular/engineered fallback (visible service panel, eye-bar, fastener language — strongest repairability read); **C** has the most distinctive face (wrapped visor) and silhouette. A natural hybrid: A's body language with B's service-panel detail. See `DESIGN-REVIEW.md` §8 for the decision list.

## Files

| File | Contents |
|---|---|
| `knoll-droid-v0.blend` | Editable scene: 3 variants, exploded B, colourway trio, studio rig, cameras |
| `build_scene.py` | Reproducible parametric build + render script (`P` and `PALETTES` at top) |
| `img/comparison.png` | A / B / C side by side, same scale/camera/lighting |
| `img/hero-variant-{a,b,c}.png` | Three-quarter studio view per variant |
| `img/ortho-{a,b,c}-{front,side,rear,34}.png` | Ortho design sheet per variant |
| `img/exploded-b.png` | Serviceability: head, torso shell, arms separated (proposed, unverified) |
| `img/colorways.png` | Variant B in Sage / Graphite / Terracotta |
| `img/detail-{face,arm,rear}.png` | Close-ups: face visor + eyes, arm joints + hand, rear |

## Regenerating

```bash
blender --background --python build_scene.py -- --renders all
```

Subsets: `comparison|heroes|ortho|exploded|colorways|details`. Blender ≥ 4.x, no addons.

## Scene organisation

- Collections: `VAR_A/B/C`, `VAR_X` (exploded), `VAR_COL0..2` (colourways), `LBL_*`
- Key objects: `TORSO`, `HEAD`, `NECK_SERVO`, `FACE_VISOR`, `EYES_L/R` or `EYES_BAR`, `ARM_{L,R}_{SHOULDER,UPPER,ELBOW,FORE,HAND}`, `LEG_{L,R}_{HIPBLK,FEMUR,KNEE,SHANK,ANKLE}`, `FOOT_{L,R}*`, `CHEST_PANEL`
- All key dims are parameters (`P`): leg joints unchanged from the locked mechanical doc; torso/head/arm positions, face size, eye spacing, stance lean all adjustable without rebuilding

## Honesty notes

- Limbs are **visual proxies** at documented joint heights — no servo bodies, bearings or cables shown; real servo struts will be bulkier.
- The stance (slight knee load, hands low-forward) is a pose suggestion, not a balance solution.
- "Self-recovery capable" is an *engineering* claim from the control/RL docs — arms provide push-assist geometry, but nothing here validates get-up motions; that's simulation work (roadmap Stage D).
