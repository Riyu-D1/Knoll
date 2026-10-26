# Mechanical Architecture — Knoll Mk1

**Date:** 2026-10-26 · **Status:** Preliminary dimensioned layout. All dimensions are CAD-starting-point values; interfaces, clearances and assembly constraints are NOT yet CAD-verified. Servo-dependent values marked ⟳ pending `engineering/notes-actuators.md`.

---

## 1. Architectures compared

| Arch | DOF | Leg layout | Head | Verdict |
|---|---|---|---|---|
| **M1 — Biped, 5-DOF legs, fixed head** | 10 | hip_yaw, hip_roll, hip_pitch, knee, ankle_pitch | none (matrix eyes) | **SELECTED** — matches the proven Microduck/Open-Duck-Mini joint layout (ankle-roll omitted by design, lateral control via hip roll + wide feet), minimum servo count that walks + self-recovers |
| M2 — Biped, 6-DOF legs, fixed head | 12 | adds ankle_roll | none | More ground-contact authority, +2 servos (+£, +mass at the worst place — distal foot); real need unproven at 800g–1.2kg scale; defer to v2 (frame leaves mounting provision) |
| M3 — Biped, 5-DOF legs + 2-DOF neck | 12 | as M1 | pitch+yaw | Most expressive; but neck mass raises CoM, adds snag points during get-up, +2 servos; rejected for v1, documented as upgrade path |
| M4 — Biped, 4-DOF legs | 8 | drops hip_yaw | none | Cheapest; turning requires walk-around arcs only; poor for a mascot that must orient/reach — rejected on capability grounds |

Rationale: Microduck ships exactly the M1 leg layout (5/leg) and demonstrates walk + get-up + grab. The 4-DOF saving isn't worth losing yaw turns; 6-DOF buys marginal foot control our mass doesn't need yet.

## 2. Preliminary dimensioned layout (mm)

```
            ┌──────── dome apex (topper pogo slot)
           ╱  ╲       dome shell ~170 W × 160 D × ~135 H
          │ FACE│     face plate low on dome front
          │ ▄▄ │
           ╲──╱ ──── chassis plate Ø ~150 (dome seats & seals here)
         ┌─┴────┴─┐
   hip   │ chassis │    internal stack: battery sled low + centre,
   yaw   │  + hip  │    servo-bus board, SBC above, MCU below
         └─┬────┬─┘
       hip_roll+pitch (co-located per hip)
           │ femur 55
         knee
           │ shank 65
         ankle_pitch
           ╱        ╲   ankle axis ~22 above sole
        ┌──┐      ┌──┐   foot 85 W × 95 L, TPU sole, ~8° splay
     standing height ≈ 265–280 mm
```

| Segment | Value (mm) | Basis |
|---|---|---|
| Femur (hip_pitch→knee) | 55 | keeps leg compact; shorter = lower knee torque, less stride |
| Shank (knee→ankle) | 65 | slight shank bias aids crouched get-up geometry |
| Ankle→sole | 22 | low pivot = smaller ankle torque demand |
| Leg extension (standing) | ~140 | crouched stance, CoM ~120–140 mm up |
| Foot | 85×95, ~8° toe-out | wide support polygon compensates missing ankle roll |
| Hip lateral spacing | ~75–85 | ⟳ set by servo pair width side-by-side |
| Dome | ~170×160×135 | prints on ≥180 mm beds; splits into 3 panels if not |
| Total height | ~265–280 | comparable class to 25 cm reference |
| CoM target | ≤ 140 mm above sole, on centreline ±5 mm | battery sled sits dead-centre under chassis plate |

## 3. Joint table (all values preliminary ⟳)

| # | Joint | Type | Range (mech stop) | Req. continuous / peak* | Servo (selected) | Margin | Notes |
|---|---|---|---|---|---|---|---|
| L1/R1 | hip_yaw | servo direct | ±60° | ~0.1 / ~0.3 | ST3020 (40.2×20.2×40 mm, ~58 g) | >5× | vertical axis; low load |
| L2/R2 | hip_roll | servo + horn | ±45° | ~0.4 / ~0.7 | ST3020 | ~3× | sole lateral authority (no ankle roll) |
| L3/R3 | hip_pitch | servo + horn | −60°…+90° | ~0.3 / ~0.9 | ST3020 | ~2.7× | get-up body swing |
| L4/R4 | knee_pitch | servo + horn | 0–110° | ~0.5 / ~1.1 | ST3020 | ~1.5–2× | **binding joint** — mass ≤1.15 kg gate; C018 drop-in |
| L5/R5 | ankle_pitch | servo + horn | ±45° | ~0.35 / ~0.83 | ST3020 | ~2.9× | stabilising |
| OPT | ankle_roll / neck (v2 provision) | — | — | — | frame + bus slots reserved | — | mounting lands kept in CAD |

\* from engineering/actuator-study.md §2 (Case B governing). Continuous ≠ stall — peak figures already include dynamic factors.

Bearing support: every leg joint is servo-shaft-driven on one side and runs on an MR-class bearing or printed bushing on the opposite side (dual-support horns — never cantilever a loaded joint off one shaft). ⟳ bearing sizes pending servo horn geometry.

## 4. Structural load paths & materials (summary — details in manufacturing doc)

- **Load path:** foot → ankle servo/bearing frame → shank strut → knee servo → femur → hip block (bolted to chassis plate) → chassis plate (main skeleton, 4 mm plate + ribs) → dome shell is COSMETIC+bumper only, carries no joint load.
- **Structural parts:** PETG-CF or ASA-CF (stiff, creep-resistant) for leg struts & hip blocks; PETG for chassis plate; TPU-95A for foot soles + face-plate bumper ring + beak/snag trims.
- **Fasteners:** M2.5/M3 heat-set inserts in all plastic load paths; M3 socket-head screws into servo mounting tabs (servo class standard); threadlocker on metal-to-metal.
- **Cables:** servo daisy-chain inside each leg with printed cable channels + 20 mm service loops at every joint crossing; hip yaw pass-through uses a spiral-wrap channel (continuous flex); no cable crosses a joint on the outside.
- **Pinch points:** dome skirt shrouds the hip region; knee pinch arc covered by shank shell lips.
- **CoM discipline:** battery (heaviest single module ~90–110 g) slides on a centreline sled low in the belly; SBC+PCB stacked above it; legs carry servos symmetrically; face electronics < 15 g high on the dome is acceptable as it's light.

## 5. Modular assembly tree

```
Knoll Mk1
├── Leg assembly L/R (mirror pair, user builds 2)
│   ├── foot shell + TPU sole + ankle servo frame
│   ├── shank strut (print, cable channel inside)
│   ├── knee servo + horn + far-side bearing bushing
│   ├── femur strut
│   └── hip block: hip_roll + hip_pitch servos stacked orthogonally,
│       hip_yaw servo on top, bolts to chassis plate (4× M3 + locating boss)
├── Chassis plate assembly
│   ├── printed plate Ø~150×4 mm + ribs
│   ├── controller PCB (custom) + SBC on printed standoffs
│   ├── battery sled + battery (toolless slide, rear eject)
│   └── IMU rigid-mounted to plate centreline
├── Dome shell
│   ├── dome (1 pc or 3-panel split) — screws to chassis rim, 6× M3
│   ├── face plate subassembly: LED eyes + driver + optional camera
│   ├── rear hatch: USB-C, power, charge port, SD access
│   └── topper pogo dock (apex) + sprout topper
└── Harness: one servo daisy-chain per leg → bus board; legs keyed L/R
```

- Legs detach from chassis with 4 M3 screws + 1 keyed connector each (leg swap < 10 min).
- Every servo reachable by removing its strut pair — no servo is buried.
- Face plate is sacrificial cosmetic — £ of plastic, 4 screws.

## 6. Mass budget (preliminary, g)

| Group | Est. | Confidence |
|---|---|---|
| 10× ST3020 servos (~58 g ea) | ~580 | medium (unverified mass — weigh on receipt) |
| Leg structures + feet + bearings + fasteners | ~180 | medium |
| Chassis plate + standoffs + sled | ~70 | medium |
| Battery 2S 2200 mAh | ~112 | verified-ish (listing) |
| Electronics (PCB, SBC, IMU, eyes, wiring) | ~110 | medium |
| Dome + face + hatch + topper | ~110 | medium |
| **Total** | **~1.09 kg** | within the ≤1.15 kg knee-margin gate — tight, mass watch required |

If weigh-in or CAD pushes total above ~1.15 kg, the knee continuous margin erodes further (every +100 g ≈ +0.07 N·m knee) — mitigations in order: lighten dome/harness first, then ST-3020→C018 upgrade at knee+ankle (+£20, +40 g). Mass beats features; M2/M3 architectures do not return.

## 7. Open mechanical questions for CAD stage

1. Servo horn + far-side bearing geometry per servo model (⟳ Agent C part dims).
2. Dome rim vs thigh clearance through full hip_yaw/roll envelope.
3. Foot sole friction spec: TPU-95A on smooth floors — needs real test; add removable silicone tread stickers option.
4. Get-up geometry: does back-lying posture let feet plant under CoM? → Stage-D sim must include dome contact geometry (dome as collision sphere-cap).
5. Screw/insert pull-out at hip block under repeated get-up loads → specify ≥ M3×8 inserts, 3 per load point.
