# Knoll Mk1 — Open-Hardware Mascot Robot Research & Engineering Package

**Status:** Phase-1 research & engineering specification — no hardware purchased, no CAD finalized, nothing built or tested. Everything is source-cited and every unknown is flagged.

## Executive summary

**Knoll Mk1** is an original ~27 cm, ~1.1 kg dome-shelled biped mascot designed to deliver Microduck-class capability — RL locomotion, sit/stand, and staged self-recovery — as a **fully open-hardware, repairable DIY build** for roughly **£215–360** (vs €340 + shipping reference retail, hardware closed).

Key decisions (full rationale in `decisions/architecture-decision-record.md`):

- **Character:** "Knoll" — a moss-dome creature whose shell is simultaneously mascot identity, structural bumper, and 6-screw service cover. Selected from 3 scored concepts (465/500). NOT a duck.
- **Motion:** 10 DOF (5-DOF legs: hip yaw/roll/pitch, knee, ankle — the joint layout both reference projects converge on; no ankle roll, no neck servo in v1).
- **Actuators:** 10× Waveshare ST3020 serial servos (£19.40 UK-verified) on a direct 2S LiPo rail — the only in-budget pick that's in-spec on unregulated 2S. Torque analysis shows the **knee is the binding joint** (~1.1 N·m peak vs ~2.0–2.45 N·m stall; continuous ~0.5 N·m vs est. 0.5–0.75 rating) → mass gate ≤1.15 kg + C018 drop-in upgrade path + mandatory bench validation before bulk purchase.
- **Electronics:** RP2350 MCU owns both servo buses + all safety (watchdog torque ramp-down, clamps, brownout, e-stop) + socketed Pi Zero 2 W for 50 Hz ONNX policies — robot stays safe with the SBC dead or absent. Custom 2-layer control board (KCB-1, ~£8 fab).
- **Control:** MuJoCo + BAM-identified actuator model + PPO/CrossQ → ONNX; deterministic safety/FSM + learned policies behind a fixed obs contract — the proven reference recipe (FRASA-style CPU-trainable get-up means no GPU is required for recovery).
- **Honest headline:** at UK-single pricing we are ~at parity with the reference's retail price (~£300), not dramatically cheaper — the real wins are open hardware, repairability (a spare servo costs £19.40 vs a €99.99 dev pack), and the ~£215 MVP / ~£265 batch paths. Claim stated plainly rather than inflated.

## What's verified vs not

- **Verified (external):** all Microduck published specs, all component datasheets/prices (dated, UK-supplier URLs), the reference-class sim2real recipe, recovery literature results.
- **Not yet verified (ours):** ST3020 continuous-torque rating (unpublished — bench test P1.4 is a purchase gate), real mass/coM, knee margin under dynamic load, all robot performance (nothing exists to test). Quality gates list every open item.

## Deliverables

| Doc | Content |
|---|---|
| `research/reference-analysis.md` | Microduck verified spec table — what it actually is/does/costs |
| `research/notes-microduck.md` | Deep repo archaeology (Agent A) |
| `research/sources.md` | Consolidated evidence register + conflicts + unknowns |
| `design/shared-design-brief.md` | Locked v1.0 assumptions all workstreams share |
| `design/mascot-concepts.md` | 3 original concepts, scoring matrix, Knoll selection |
| `design/mechanical-architecture.md` | DOF, dimensions, joint table, assembly tree, mass budget |
| `engineering/actuator-study.md` | Candidates, torque math, selection + fallbacks |
| `engineering/electronics-architecture.md` | Compute, bus, sensors, power budget |
| `engineering/pcb-specification.md` | KCB-1 requirements + schematic architecture + verification |
| `engineering/control-and-recovery.md` | Sim stack, sim2real method, staged recovery plan, metrics, risks |
| `engineering/notes-*.md` | Agent research notes (actuators, electronics, control) |
| `software/system-architecture.md` | Daemon split, intent API, safety invariants, AI path |
| `manufacturing/diy-build-guide.md` | Materials, print rules, assembly, spares, tools |
| `manufacturing/notes-manufacturing.md` | Sourcing research with UK prices |
| `bom/master-bom.csv` | Every part: number, qty, price, source, date, alternative |
| `bom/cost-model.md` | 4 scenarios, drivers, hidden costs, mass roll-up |
| `licensing/originality-and-licensing.md` | Licence stack + originality checklist |
| `validation/test-plan.md` | Stage gates + measurable acceptance criteria |
| `decisions/architecture-decision-record.md` | 3 architectures scored, trade-offs, revisit triggers |
| `roadmap/implementation-roadmap.md` | Dependency-ordered work packages for build agents |

## Top open risks (watch these)

1. **Knee continuous torque margin** — thin by design; mass gate + bench gate + upgrade path mitigate.
2. **Servo sourcing channel** — £120 vs £350 swings on where ST3020s come from.
3. **Hobby-servo sim2real gap** — the documented hard part of this robot class; BAM SysID before training is non-negotiable.
4. **Pi Zero 2 W stock** — intermittent; buy early or take the documented fallback.
5. **"Knoll" name** — working name; trademark check pending before release.

*Independent community design inspired by the capabilities of small open RL bipeds. Not affiliated with Pollen Robotics or Hugging Face. No Microduck assets reused.*
