# Actuator Study — Knoll Mk1

**Date:** 2026-10-26 · **Status:** Selection complete, supported by calculations. All prices GBP dated 2026-10-26; full evidence in `engineering/notes-actuators.md` and `research/sources.md`.

---

## 1. Requirements (from mechanical architecture)

10 actuated joints v1 (5-DOF legs: hip_yaw, hip_roll, hip_pitch, knee_pitch, ankle_pitch ×2), +2 reserved positions (head/aux) — see `design/mechanical-architecture.md`. Requirements per joint below; method: rigid-body statics (τ = F × d⊥) + explicit dynamic factors, then checked across three scenarios. Robot mass planning value **1.1 kg → 10.79 N**.

## 2. Load cases (worked; details in notes-actuators.md §4)

**Case A — single-leg quasi-static stance:** ankle worst-case (CoM over toe edge, 45 mm lever): τ = 10.79 × 0.045 = **0.49 N·m**; knee at 15° gait flexion ≈ 0.22; hip_roll to foot edge (35 mm) ≈ 0.38.

**Case B — asymmetric deep-knee get-up (GOVERNING):** dominant leg supports ~0.9 kg (8.83 N):
- knee: 8.83 × 0.070 m = 0.62 static → ×1.75 dyn = **1.08 N·m peak** (≈11 kg·cm)
- ankle: 8.83 × 0.040 = 0.35 → ~0.6 peak
- hip_pitch (torso 50 mm off-axis): 6.87 × 0.05 ≈ 0.34 → ~0.8 peak
- hip_roll (50 mm lateral offset): 8.83 × 0.05 ≈ 0.44 → ~0.7 peak

**Case C — held 20° tilt:** ankle: 10.79 × sin20°×0.15 = 0.55 → ~0.83 peak.

Required stall margin: ≥1.7× peak (keeps transients <60% stall). Required continuous ≈ peak ÷ 2 for the governing joint.

| Joint | Req. continuous | Req. peak | Pick (stall/continuous) | Margin | Verdict |
|---|---|---|---|---|---|
| hip_yaw | ~0.1 | ~0.3 | ST3020 (~2.45*/~0.5–0.75 est) | >5× | ample |
| hip_roll | ~0.4 | ~0.7 | same | ~3× | ok |
| hip_pitch | ~0.3 | ~0.9 | same | ~2.7× | ok |
| knee_pitch | **~0.5** | **~1.1** | same | ~2× stall; continuous ~1–1.5× | **binding joint — see §5** |
| ankle_pitch | ~0.35 | ~0.83 | same | ~2.9× | ok |

\* stall at 12 V datasheet; at 8.4 V (2S full) ≈ ~2.0–2.2 N·m est.

## 3. Candidates evaluated (exact part numbers; stall and rated kept separate)

| Servo | Stall N·m | Continuous (published?) | Voltage | Mass | UK price | Verdict |
|---|---|---|---|---|---|---|
| **Waveshare ST3020** | 2.45 @12 V | no (est 0.5–0.75) | **6–14 V** | ~58 g | £19.40 Pi Hut verified | **PRIMARY** — wide input solves the 2S overvoltage problem; cheapest UK-verified |
| **Feetech STS3215-C001** | 1.91 @7.4 V | **0.49 @7.4 V published** | 4–7.4 V | 55 g | £26.30 RobotShop / ~£10–13 import | **FALLBACK** — ecosystem standard (SO-ARM101, rustypot); needs LiFePO4 or buck to stay in-spec on 2S |
| Waveshare ST3215-7.4V | 1.91 @7.4 V | 0.49 ("rated load") | 4–7.4 V | ~55 g | £22.99 Amazon verified | interchangeable STS3215 rebrand |
| **Feetech STS3215-C018** | 2.94 @12 V | **0.98 @12 V published** | 9–14 V | ~60 g | £24.32 RobotShop verified | **PERFORMANCE** — doubles knee continuous margin on same 3S-class rail |
| Feetech STS3032 | 0.44 @6 V | 0.15 published | 4–7.4 V | 20 g | £24.30–29.45 RC Hobby | head/aux option (needs ≤7.4 V rail!) |
| Dynamixel XL330-M288-T | 0.52 @5 V | no | 3.7–6.0 V | 18 g | £27.20 RoboSavvy | too weak for ANY leg joint — head only; rejected |
| Dynamixel XL430-W250-T | 1.5 @12 V | no | 6.5–12 V | 57 g | £27.20 | needs 3S; 1.3× knee margin thin; 5× cost/N·m — rejected |
| Dynamixel XC430-W240-T | 1.9 @12 V | no | 6.5–14.8 V | 65 g | £111.38 | right capability, wrong price — stretch only |
| Hiwonder LX-16A | 1.91 @7.4 V | stall only | 6–8.4 V | 54 g | ~£14–18 | potentiometer feedback, fixed 115200 baud, no current sense, own protocol — MVP floor only |
| LewanSoul LDX-218 (PWM) | 1.67 | stall only | 6–8.4 V | ~58 g | ~£9 | no feedback at all — bring-up/spares only |
| MyActuator RMD-L | ~0.07 rated | — | 24 V CAN | 65 g | ~£97 | BLDC class, 10–20× budget — rejected |

## 4. Strategy comparison (full detail in notes §5)

| | A: ST3020 + 2S (PICK) | B: STS3215-C001 + regulated/LiFePO4 | C: Dynamixel 3S | D: PWM hobby |
|---|---|---|---|---|
| Servo spend (10×) | **£194 UK-verified** (~£120 import) | £230–263 UK / £100–130 import + £10–20 regulator | £272+ | £60–120 |
| Voltage compliance | in-spec on raw 2S (6–14 V) AND raw 3S | NOT in-spec on raw 2S (8.4 V > 7.4 V) | in-spec on 3S | in-spec on 2S |
| Continuous rating published | no (est) | yes (0.49) | no | no |
| Extra power parts | none | buck 15A or LiFePO4 sourcing | none | none |
| Feedback richness | pos/vel/load/V/I/T | same | same | none |
| Ecosystem | Feetech-protocol; growing | largest (LeRobot, rustypot) | Dynamixel SDK | servo libs |
| Verdict | **recommended** | fallback if ST3020 fails validation/stock | rejected (cost) | rejected (spec) |

## 5. Recommendation & risks

**Primary: 10× Waveshare ST3020** (6–14 V TTL bus servo, Feetech-protocol family) on a **direct 2S LiPo servo rail** — no servo-rail regulator needed; 8.4 V max stays within the 6–14 V spec. Reserve 2 bus positions for optional head/aux servos (must be wide-input class or on a regulated tap — STS3032 is 7.4 V-max, flag).

**Cheaper fallback:** STS3215-C001/Waveshare ST3215-7.4V (~£100–130 import for 10) + 2S LiFePO4 (6.4 V nom/7.3 V max) or a 15 A buck to 7.4 V — cheaper servos but adds power hardware or sacrifices ~15% torque headroom. **MVP floor:** LX-16A/LDX-218 — documented capability loss.

**Performance alternative:** 10× **STS3215-C018** + 3S LiPo — published 0.98 N·m continuous doubles the knee margin for +£50 servo cost and +~40 g battery. Also: mixed fit — C018 at knee+ankle_pitch only (4× = +£20 vs ST3020).

**Knee-margin risk register:** required knee continuous ≈ 0.5 N·m vs ST3020 est. 0.5–0.75. Mitigations: (a) mass ≤1.15 kg gate — every +100 g adds ~0.07 N·m; (b) firmware current/temp limits + get-up duty management; (c) geometry — keep femur ≤70 mm; (d) drop-in C018 upgrade. **Bench gate (roadmap P1.4):** buy ONE ST3020 first — measure continuous-hold thermals at 0.5 N·m, protocol compatibility, and real torque before committing to 10.

## 6. Electrical implications (handed to electronics doc)

- Rail: direct 2S LiPo, 6.0–8.4 V; firmware current limit ~1 A/servo → bounded peak ~10 A; fuse 10 A, wire 20 AWG trunk.
- Two half-duplex TTL buses @1 Mbaud (L leg / R leg+aux), 74LVC buffers per notes-electronics §5.
- Servo mass ~58 g ×10 = ~580 g — mass model updated accordingly.
