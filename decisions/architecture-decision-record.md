# Architecture Decision Record — Knoll Mk1

**Date:** 2026-10-26 · **Status:** DECIDED (pre-CAD). ADR-001. Revisit triggers listed in §6.

---

## 1. Decision

Build **Knoll Mk1**: a ~27 cm, ~1.1 kg dome-shelled biped mascot — 10-DOF (5/leg, no ankle roll, no neck v1), Waveshare ST3020 serial servos on a direct 2S rail, RP2350 MCU (safety owner) + optional Pi Zero 2 W (policies), BNO085 IMU, MuJoCo+BAM+ONNX pipeline, fully open hardware (CERN-OHL-S), DIY cost ≈ £280–360 depending on sourcing.

## 2. Candidate architectures compared

| | **A1 — "Lean open biped" (SELECTED)** | A2 — "Microduck-parity+" | A3 — "Budget duck" |
|---|---|---|---|
| DOF | 10 (5/leg), fixed head | 14–15 (6/leg + neck + beak) | 10 (5/leg) |
| Actuators | ST3020 6–14V ×10, 2S rail | XL430/XC430 mix, 3S rail | LX-16A/LDX-218 ×10 |
| Compute | RP2350 + Pi Zero 2 W | RK3566-class + MCU | Pico 2 W only |
| Sensors | BNO085 + proprio; camera/ToF optional | BNO085 + camera + ToF + foot sw | BMI270 + proprio |
| Mechanical | dome shell, PETG-CF, dual-bearing joints | same class, more joints | same, PLA |
| Recovery path | staged KFB→learned (same evidence base) | same | same but weaker feedback |
| Est. cost | £215 MVP / ~£300 rec / £500 perf | £450–650 | £150–190 |
| Recovery potential | high (joint torque + dome geometry designed for it) | high | medium (potentiometer feedback, no current sense) |
| DIY complexity | moderate | high (3S rail, more joints, more cables) | low |

## 3. Weighted scoring (weights justified in-line)

| Criterion | Wt | Rationale |
|---|---|---|
| Capability vs reference | 15 | must demonstrably walk/sit/get-up — the mission's core |
| Actuator adequacy | 15 | torque margins decide whether recovery is possible at all |
| Self-recovery potential | 15 | mission's hardest function; joint torque + CoM + shell geometry |
| Mechanical feasibility (DIY) | 10 | hobby FDM + tools only |
| Mass & power | 10 | CoM + battery + servo mass compound everywhere |
| Cost | 15 | mission objective — materially below reference |
| Reliability & repairability | 10 | open-hardware ethos, spare-ability |
| Reproducibility/openness | 5 | licensing + part availability |
| Software complexity | 5 | small team, staged plan |
| Originality | 5 | independence from reference |

Scores 1–5, weighted (max 500):

| Arch | Cap | Act | Rec | Mec | M&P | Cost | Rel | Open | SW | Orig | **Total** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A1 lean open biped** | 4 | 4 | 4 | 5 | 4 | 4 | 5 | 5 | 4 | 5 | **440/500 → 88** |
| A2 parity+ | 5 | 3 | 4 | 3 | 2 | 2 | 3 | 5 | 3 | 5 | **340/500 → 68** |
| A3 budget | 3 | 2 | 3 | 5 | 4 | 5 | 3 | 5 | 4 | 5 | **365/500 → 73** |

A1 wins: it concentrates spend exactly where capability lives (servo torque + feedback quality + fused IMU) and cuts where evidence shows capability doesn't (camera/ToF/ankle-roll/neck/beak for v1 — none are in the references' locomotion obs). A2 fails on cost/mass: XC430-class legs alone ≈£1,114; XL430 gives only ~1.3× knee margin — more money for *less* margin. A3's potentiometer servos lack current/load feedback and 1 Mbaud — the actuator study shows feedback richness is what the RL stack eats; cheap actuation would cap the ceiling.

## 4. Key sub-decisions (recorded for traceability)

| # | Decision | Choice | Driver |
|---|---|---|---|
| D1 | Leg DOF | 5/leg (no ankle roll) | Microduck+ODM-proven; wide feet + hip roll compensate; −2 servos/mass |
| D2 | Neck/head | fixed + LED eyes v1; bus+mount provision kept | −2 servos, lower CoM, fewer recovery snag points |
| D3 | Servo | ST3020 primary / STS3215 fallback / C018 perf | only wide-input pick in budget that keeps 2S in-spec; knee margin flagged → C018 drop-in path |
| D4 | Rail | direct 2S LiPo | ST3020's 6–14 V input makes regulator unnecessary; battery stays cheap/standard |
| D5 | Compute | RP2350 + optional Pi Zero 2 W | safety in MCU hardware; SBC socketed not soldered; ODM proves Pi-Zero-class runs 50 Hz ONNX |
| D6 | IMU | BNO085 fused | reference-class fusion without custom bridge board; BMI270 fallback −£10 |
| D7 | Sim | MuJoCo + BAM + mjlab/CrossQ | both references converged; FRASA proves CPU-trainable recovery |
| D8 | Camera/ToF | optional (provisions kept) | reference policies are proprioception-only; saves £24–45 and 0.5 W |
| D9 | Shell | dome + fused head (Knoll) | scoring matrix in mascot-concepts.md; dome doubles as recovery-friendly bumper |
| D10 | Licensing | CERN-OHL-S hw + Apache-2.0 sw + TM name | open-hardware differentiation is the product |

## 5. Trade-offs accepted (honest)

- **Knee continuous margin ~1–1.5×** (not the comfortable 2× wanted) — accepted because: get-up is transient (seconds), temp feedback allows duty management, mass gate 1.15 kg, and C018 is a drop-in upgrade. If bench SysID (P1.4) shows ST3020 continuous <0.45 N·m, escalate to C018 or ST3215-7.4V+buck before freezing CAD.
- **~1.1 kg vs reference 0.78 kg** — accepted: DIY servos are 3× XL330 mass; we're honest that we can't match 780 g at this price. Capability parity at higher mass is the trade.
- **Cost ≈ retail reference (~£300)** at UK-single pricing, not "materially lower" — the genuine saving comes from repairability (spares £19 vs dev-pack €99), openness, and the ~£215 MVP / ~£265 batch paths. Claim adjusted honestly vs the mission's stretch goal.
- **ST3020 has no published continuous rating** — accepted pending P1.4 thermal bench test; STS3215 (published 0.49 N·m) is the documented fallback.

## 6. Revisit triggers

- ST3020 bench: continuous-hold <0.45 N·m or protocol quirks → switch to STS3215+regulated rail.
- CAD mass model >1.25 kg → drop to 8-DOF? No — first drop dome mass, then re-evaluate geometry; never drop below 5/leg (capability floor).
- Pi Zero 2 W supply collapse → Radxa Zero 3W / CM4-Lite path documented.
- Servo channel shock → C variant of BOM (Waveshare ST3215) is pin-protocol-compatible fallback.
- Any ankle-roll need demonstrated in Stage C/D sims → frame provision exists; add 2 servos (+£39, +116 g).
