# Knoll Mk1 — Droid v0 Design Review

**Date:** 2026-10-29 · **Status:** concept visualisation for feedback — not engineering geometry. Direction change from shell-v0: agile biped-droid archetype, user-approved 15-DOF (5/leg + 2/arm + 1 neck).

---

## 1. Three design directions

Same 15-DOF proxy platform throughout — only shell language, head and face treatment differ.

| | A — Field Buddy | B — Service Frame | C — Apex |
|---|---|---|---|
| Torso | Smooth egg capsule + belt | Bevelled box, chest service panel + fasteners, waist ring | Tapered organic two-lobe torso, hidden waist |
| Head | Round, dark visor + 2 LED eyes + smile | Box head, single wide eye-bar | Wrapped visor band (reads as one confident element) |
| Arms | Capsule links, mitten hand | Struts + box hand, visible shoulder caps | Fully hidden joints, slimmest |
| Character | Friendly, agile, approachable | Engineered open-hardware product | Premium, most distinctive silhouette |

## 2. Recommendation: **A**

Closest to the brief's "calm, determined" character while unambiguously reading as an agile droid — the criticism of shell-v0 resolved. It's also the furthest from both Microduck's specifics and generic robot-icon clichés (B risks the latter). Strong alternative: **A's body language + B's chest service panel** as the repairability cue.

## 3. Proportions used

| Element | Value (mm) | Note |
|---|---|---|
| Total height | ~300 incl head | ~20 mm over old brief — head adds height; flag §5 |
| Leg joints | hip ±40 @140 / knee @85 / ankle @20 | locked from mechanical doc (unchanged) |
| Torso | ~95×82×105 @ z145–250 | contains battery + electronics (conceptual) |
| Head | ~74×70×64 @ z~285 | on 1-DOF pitch neck |
| Shoulders | ±52 @ z230 | 2-DOF (pitch+roll) |
| Arms | elbow ~190, wrist ~158, hand ~145 | bent ready-pose, ~90 mm reach |
| Feet | 80×95×24, ±8° toe-out | unchanged |

## 4. Visual assumptions vs engineering constraints

**Visual assumptions:** limb thicknesses (real servo struts bulkier), head/torso split heights, visor mount (proud plate vs recessed — undecided), hand shapes (mitten/box — no gripper DOF modelled), stance pose.
**Honoured constraints:** leg joint heights/spacing, foot size, 15-DOF layout itself, no extra actuators beyond approved count, battery+electronics inside torso, service-panel intent on B.

## 5. Conflicts / consequences of the redirect (honest)

1. **Mass gate breach.** +5 servos ≈ +280 g + ~40 g links/head ⇒ **~1.4 kg vs the 1.15 kg knee-torque gate.** Mitigations, in order: lighter arm/neck servos (STS3032/XL330-class ~30 g → ~+170 g); knee+ankle to STS3215-C018 class (already the documented upgrade path); torso shell mass. **This is the single biggest engineering consequence — needs an actuator re-study before build.**
2. **Height:** ~300 mm vs 265–280 brief — head+neck adds ~25 mm. Acceptable if intentional (Microduck is 250 mm at 15 servos; we could trim torso/leg stand-off slightly).
3. **Torso interior:** 95 mm-wide torso must hold battery sled (Ø~65×18 cell block), PCB, SBC — plausible but tighter than the old dome volume; packaging is a CAD task.
4. **Recovery geometry:** no more dome bumper — falls land on torso shell/arms. Arms enable push-up recovery (the point of the redirect) but are also snag candidates; hands should be rounded and shoulder horns recessed.
5. **Cost:** +5 servos ~+£100–150 vs the 10-servo BOM; servo class mix can claw much of it back.

## 6. Easiest changes now

Face treatment (visor vs eyes vs bar — one parameter each), head size/shape, torso taper, arm pose angle, hand style, colourways, stance lean. All in `P`/`PALETTES`.

## 7. Risks

- **Stability:** higher mass + head high = higher CoM than dome design → knee margin + balance both tighter; arms help recovery but hurt mass.
- **Printing:** simpler than the 170 mm dome — all parts < 100 mm; torso splits into shell halves.
- **Recovery:** arm push-assist is *designed intent, not validated* — needs the same staged recovery plan (scripted first, learned later), now with arm trajectories in the keyframes.
- **Originality:** archetype shared with Microduck by request; distinct face/visor, proportions and surface language keep it our design — do NOT add a bill, do NOT copy its head/body ratio or colourway.

## 8. Decisions to review

1. Direction A as the shell language? (or A+B hybrid)
2. Face: A's twin eyes + smile vs C's wrapped visor vs B's eye-bar — pick the face family.
3. Arm servo class: full ST3020 everywhere vs smaller/cheaper arm-neck servos (affects mass gate directly).
4. Accept ~300 mm height or trim toward ~285 mm?
5. Keep "Knoll" name on the droid (yes per your call) — any name-adjacent accent kept (e.g., sage colourway) or fully clean?

Stopping here pending feedback — no production CAD or further robot changes until reviewed.
