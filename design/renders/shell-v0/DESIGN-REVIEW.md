# Knoll Mk1 — Shell v0 Design Review

**Date:** 2026-10-29 · **Status:** concept visualisation for feedback — not engineering geometry. Companion to `README.md`; images in `img/`.

---

## 1. Three design directions

All three share the locked platform: dome ≈170×160×135 mm on a ~140 mm leg proxy, total ~275 mm to dome apex (~295 mm with topper), low-mounted LED-matrix face, 10-DOF proxy legs, broad feet.

| | A — Soft Moss | B — Modular Terrarium | C — Sculptural Knoll |
|---|---|---|---|
| Silhouette | Clean continuous dome, nothing to break up the form | Same dome, articulated by 3 meridian panel seams + rim screw band | Same dome + brow ledge shading the face |
| Face | Small flush dark plate, mint LED eyes, smile | Larger bolt-on plate with visible fasteners (replaceable read) | Deepest face surround; brow gives a "hooded, calm" expression |
| Topper | Two-leaf sprout | Button mushroom on a visible magnetic puck | Sculptural button mushroom |
| Feet | Rounded organic pads | Angular bevelled slabs | Forward-pointing river stones |
| Character | Calm, curious, friendliest | Well-engineered open-source product | Most premium/distinctive; quiet, slightly sleepy |

Key differences are features, not proportions — the platform is identical so the comparison isolates shell language.

## 2. Recommendation: **B — Modular Terrarium**

- Its seams, face-plate fasteners, rim screws, puck-mounted topper and rear hatch make repairability *legible* — the mission's differentiator vs the closed reference.
- Every shown feature maps to a real documented interface (face plate on 4 screws, dome on chassis-rim screws, topper on pogo dock, battery/ports through rear hatch) — nothing rendered is fiction.
- It already looks like a shippable open-hardware product rather than a clay study, which sets the right bar for the next iteration.
- **Blend strategy available:** if B feels too busy, adopt A's clean dome and keep only B's face plate + topper dock — the two strongest modular cues (easy change, see §6).

A is the fallback for maximum character warmth; C is the risk/reward option (best silhouette, mild snag + duck-adjacency concern).

## 3. Proportions used

| Element | Value (mm) | Source / note |
|---|---|---|
| Dome footprint | 170 × 160 | locked brief |
| Dome height | 135 = 20 rim band + 115 cap | locked brief; cap is a cut ellipsoid |
| Apex height | ~275 | within 265–280 brief |
| Topper | +20–28 → ~295 total | **exceeds brief** — flagged §5 |
| Face plate | 58 × 34 × 5 (A/B), 66 × 42 (C), 12° up-tilt | visual choice |
| Eyes | 20 × 20 emissive squares, 40 mm spacing | approximates 8×8 LED matrices |
| Leg joints | hip ±40 @ z140 / knee z85 / ankle z20 | mechanical-architecture.md (femur 55, shank 65, ankle→sole 20–22) |
| Feet | 85 × 95 × 26, ±~52 mm centres | brief foot dims; centres set by leg splay |
| Rear hatch | 52 × 38 on rear dome @ z~205 | visual placeholder |
| Chassis proxy | Ø150 × 6 disc @ z~143 | mechanical-architecture.md |

## 4. Visual assumptions vs engineering constraints

**Visual assumptions (chosen for looks, unverified):**
- Face plate mounted proud (~5 mm) on the dome surface at z≈205 — engineering intends a replaceable plate; flushness, sealing and gasket are unresolved.
- Face at ~205 mm (lower-mid dome) reads well; the brief says "low on the dome front" — could go lower (~185 mm) if preferred.
- Panel seams = surface curves, not split geometry; real B-panel segmentation needs CAD.
- Eyes drawn as proud emissive tiles; production version is LEDs *behind* a smoked plate (diffusion not modelled).
- Legs/feet have no servo bodies, bearings, or cable channels — pure stand-ins at the documented joint heights.
- Materials approximate FDM filament; colours are directional, not a print spec.

**Engineering constraints honoured:**
- Dome 170×160×135, height band 265–280, feet 85×95, hip spacing ~80, joint heights per joint table.
- No neck/actuators added; battery + electronics conceptually inside chassis; shell drawn as removable cover + bumper.
- Smooth back/top surfaces retained for roll-to-prone recovery; only small fasteners/seams protrude.

## 5. Conflicts with the mechanical architecture

1. **Standing height:** dome apex ≈275 mm meets the 265–280 brief, but the topper reaches ~295 mm — decide whether "standing height" includes the topper.
2. **Dome rim Ø170 vs chassis plate Ø150:** the skirt overhangs the plate edge; the rendered rim-screw ring is conceptual — the real fastener circle must land on the Ø150 plate or a dedicated rim flange (new part needed or plate widened).
3. **Face plate vs dome curvature:** a flat 58 mm plate on a Ø-ellipsoid leaves gaps at the corners; production plate needs a curved back or a flattened dome boss — not yet designed.
4. **Hip envelope clearance:** proxy hips at ±40 mm with ~26 mm blocks clear the Ø170 rim visually; real servo stacks (~40 mm wide each + horns) need the CAD clearance check already listed as open question #2 in mechanical-architecture.md.
5. **Leg proxy ≠ leg envelope:** rendered legs are slimmer than real servo struts will be; the dome/leg gap will shrink in CAD. Do not treat the rendered clearance as real.

## 6. Easiest things to change now

- Face plate size/position/tilt, eye spacing, smile — single parameters.
- Topper shape (sprout ↔ mushroom) and size.
- Seam layout on B (count, position) and whether A stays perfectly clean.
- Brow ledge on C (remove, shrink, or make it a TPU bumper).
- Foot style is per-variant; colourways are palette swaps — seconds to iterate.
- Dome cap height/roundness (ellipsoid scale) — still one parameter.

## 7. Risks (stability / printing / service / recovery)

- **Stability:** stance ~190 mm wide vs 170 mm dome is generous; real CoM depends on untested leg mass — unchanged risk from the mechanical doc, not made worse by the shell.
- **Printing:** a 170 mm dome is at the limit of common 180 mm beds — B's 3-panel split is the natural fallback and is *already drawn as its design language*, so adopting it costs nothing visually.
- **Service:** exploded view shows proposed separations only; real clearances (face-plate gasket, hatch hinge/latch, topper pogo alignment) unverified.
- **Recovery:** dome back/top is smooth and seam-low — good roll surface. C's brow is the only face-height protrusion (make it TPU/sacrificial or cut it); B's rim screws and topper puck are small snag candidates on the roll path — keep them flush.
- **Face-first falls:** the plate is the impact surface — it must be cheap and sacrificial (already the plan); consider a TPU bumper ring around it.

## 8. Decisions to review

1. **Direction:** proceed with B as the shell language? (or A-clean + B's face/topper hardware as a hybrid)
2. **Face position:** keep at ~205 mm, or push lower toward ~185 mm for a cuter read?
3. **Expression:** mint LED squares + smile as shown, or larger/wider eyes, or a rounder eye shape?
4. **Topper:** sprout (A), mushroom-on-puck (B), or button mushroom (C) as the default first-party topper? All variants share the same dock location.
5. **Colourway order:** Sage first (as shown), or lead with Graphite/Terracotta?
6. **B's seam count:** 3 panels as drawn vs 2 side panels + full rear shell?
7. **C's brow:** keep (distinctive, mild snag + slight bill-adjacency risk) or drop.

No action requested beyond this list — stopping here pending feedback, per milestone scope.
