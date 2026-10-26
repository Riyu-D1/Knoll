# Actuator Research — Project MASCOT

**Author:** Actuator workstream · **Date:** 2026-10-26 · **Status:** Preliminary research
**Brief:** `design/shared-design-brief.md` v0.1 — targets: 26–32 cm biped, 0.9–1.3 kg, 10–14 DOF, 7.4 V (2S) serial-bus smart servos "or justified alternative", DIY build < £320.

---

## 0. TL;DR

- **Recommended:** all-Feetech TTL serial bus on a 2S rail — **10× Feetech STS3215-C001** (legs) + **2× Feetech STS3032** (neck/beak). ~£150–200 imported / ~£300 UK-retail. It is the de-facto standard for this robot class (Hugging Face LeRobot SO-ARM100/101 uses it; Pollen Robotics' rustypot Rust library supports it — the same ecosystem Microduck's software stack uses).
- **Cheaper fallback:** Waveshare ST3215-7.4V (functionally identical to STS3215, £20–23 UK) or Hiwonder LX-16A (~£14–18) — both have caveats; and a hobby-PWM MVP option for proof-of-motion only.
- **Performance alternative:** Feetech ST-3020-C001 (20 kg·cm @ 7.4 V, slimmer body) or STS3215-C018 (12 V variant, rated torque doubles to 10 kg·cm) on 3S; or Dynamixel XC430-W240-T — but Dynamixel-only legs blow the budget.
- **Critical flag for the brief:** the STS3215 7.4 V variant is rated **4–7.4 V input** — a fully-charged 2S LiPo (8.4 V) exceeds spec. Options: buck-regulated 7.4 V bus, 2S LiFePO4 (7.3 V max), or wide-input servos (Waveshare ST3020, 6–14 V).
- **Knee joint is the binding constraint** (~1.1 N·m peak required vs 0.49 N·m published continuous rating). Feasible with duty-cycle management at ≤1.1 kg total mass; validated numbers in §4.

---

## 1. Scope & method

Researched serial smart servos and integrated actuators for a 10–14 DOF biped
(leg = hip pitch, hip roll, knee pitch, ankle pitch, optional hip yaw; plus 1–2
neck/head and a possible beak joint). Sources: manufacturer datasheets/e-manuals
(Robotis, Feetech, Waveshare, Hiwonder), distributor pages (RobotShop UK,
RoboSavvy UK, Pi Hut, Generation Robots, Amazon/eBay UK, Alibaba/AliExpress).
All prices checked **2026-10-26**. USD→GBP conversions use ~£0.79/$ and are
marked *estimate*.

**Torque terminology used throughout (per brief rule):**
- *Stall torque* = maximum momentary torque at locked rotor. What most vendors headline.
- *Rated/continuous torque* = sustained torque under the vendor's life-test duty cycle. Only Feetech/SCS publish this consistently. Where unpublished, a conservative continuous estimate of **20–30 % of stall** is used and marked *estimate*.

---

## 2. Candidate servos — specification table

Torques given **stall / rated** separately, with voltage. "—" = not published.

| Servo | Stall torque | Rated (continuous) torque | No-load speed | Voltage range (nom.) | Current (idle / no-load / stall) | Feedback sensor | Protocol / bus | Gears | W×H×D (mm) | Mass | UK-indicative price (GBP, 2026-10-26) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Feetech STS3215-C001** (7.4 V) | 19.5 kg·cm (1.91 N·m) @ 7.4 V; 16.5 @ 6 V | **5 kg·cm (0.49 N·m) @ 7.4 V**; 4 @ 6 V — *published* | 0.192 s/60° (52 rpm) @ 7.4 V | 4–7.4 V (7.4 V) | 6 mA / 150 mA / 2.5 A @ 7.4 V | 12-bit magnetic, 360°/4096 | TTL half-duplex, 38.4k–1 Mbaud | Copper, 1:345 | 45.2×24.7×35 | 55 g | £26.30 RobotShop UK (verified); ~£10–13 AliExpress (indicative) |
| **Feetech STS3215-C018** (12 V) | 30 kg·cm (2.94 N·m) @ 12 V | **10 kg·cm (0.98 N·m) @ 12 V** — *published* | 0.222 s/60° (45 rpm) @ 12 V | ~9–14 V (12 V) | — / 180 mA / 2.7 A | 12-bit magnetic, 360°/4096 | TTL half-duplex | Metal (steel) | 45.2×24.7×35 | ~55–70 g¹ | £24.32 RobotShop UK; £25.00 RC Hobby-Models (verified) |
| **Feetech ST-3020-C001** | 20 kg·cm (1.96 N·m) @ 7.4 V | — (est. 4–6 kg·cm, 20–30 % of stall) | 68 rpm @ 8.4 V | 7.4 V class | — | magnetic | TTL half-duplex | Metal | ~40×20×40 | ~55–60 g (est.) | ~£18–22 (estimate; UK stock thin) |
| **Feetech STS3032-C001** | 4.5 kg·cm (0.44 N·m) @ 6 V | **1.5 kg·cm (0.15 N·m) @ 6 V** — *published* | 0.09 s/60° (111 rpm) @ 6 V | 4–7.4 V (6 V) | 6 mA / 150 mA / 1.2 A | 12-bit magnetic, 360°/4096 | TTL half-duplex | Metal; Al case, coreless motor | 23.2×12.1×28.5 | 20 g | £24.30–29.45 RC Hobby-Models (verified); ~£8–12 import (indicative) |
| **Feetech SCS15-C022** | 15.6 kg·cm (1.53 N·m) @ 7.4 V | **5.2 kg·cm (0.51 N·m) @ 7.4 V** — *published* | 0.156 s/60° (64 rpm) @ 7.4 V | 4–8.4 V | 7 mA / 270 mA / 2.5 A | **Potentiometer**, 220°/1024 (0.215°) | TTL half-duplex, SCS protocol | Copper; PA case | 40.2×20.2×40 | 58 g | ~£8–15 (estimate; few UK listings) |
| **Waveshare ST3215-7.4V** | 19.5 kg·cm (1.91 N·m) @ 7.4 V | 5 kg·cm (0.49 N·m) @ 7.4 V ("rated load") | 0.192 s/60° (52 rpm) | 4–7.4 V | — / 150 mA / 2.5 A | 12-bit magnetic, 360°/4096 | TTL half-duplex, 1 Mbaud default | Metal | 45.2×24.7×35 (est., same housing) | ~55 g (est.) | £22.99 Amazon UK (verified); $16.99–21.99 waveshare.com |
| **Waveshare ST3020** (wide-V) | 25 kg·cm (2.45 N·m) @ 12 V | — (est. 5–7.5 kg·cm) | 0.167 s/60° (60 rpm) @ 12 V | **6–14 V** | — / 200 mA / 2.7 A | 12-bit magnetic, 360°/4096 | TTL half-duplex | Metal | 40.2×20.2×40 | ~58 g (est.) | £19.40 Pi Hut (verified); $19.99 waveshare |
| **Hiwonder LX-16A** | 19.5 kg·cm (1.91 N·m) @ 7.4 V; 17 @ 6 V | — *only stall published* (est. ~4–6 kg·cm) | 0.19 s/60° @ 7.4 V | **6–8.4 V** | — / 100 mA / 2.4–3 A | **Potentiometer**, 0–240°/1000 | TTL half-duplex, **fixed 115200 baud**, proprietary proto | Metal | 45.2×24.7×36.3 | 54 g | ~£13.69–17.72 eBay UK + ship (indicative); $16.99 hiwonder.com |
| **Hiwonder LX-15D** | 17 kg·cm (1.67 N·m) @ 7.4 V; 15 @ 6 V | — *only stall published* | 0.22 s/60° @ 7.4 V | 6–8.4 V | — / 100 mA / 2.4–3 A | Potentiometer, 0–240° | TTL 115200, proprietary | Metal | 44×22.9×35.1 | 43 g | $16.99 direct ≈ £14 (indicative) |
| **Hiwonder LX-224 / LewanSoul** | 20 kg·cm (1.96 N·m) @ 7.4 V | — *only stall published* | 0.20 s/60° @ 7.4 V | 6–8.4 V | — / 100 mA / 2.4–3 A | Potentiometer, 0–240° | TTL 115200, proprietary | Metal | 40×20.1×51.1 | 63 g | $15.99 direct ≈ £13 (indicative) |
| **Hiwonder HTS-35H** | 35 kg·cm (3.43 N·m) @ 11.1 V | — *only stall published* | 0.18 s/60° @ 11.1 V | **9–12.6 V** | — / 100 mA / 3 A | Potentiometer, 0–240° | TTL 115200, proprietary | Brass | 40×20×40.5 (54.4×20×45.5 listing variant) | 64 g | $21.99 ≈ £18 (indicative) |
| **LewanSoul/Hiwonder LDX-218** (PWM, not serial) | 17 kg·cm (1.67 N·m) @ 7.4 V; 15 @ 6 V | — *only stall published* | 0.16 s/60° @ 7.4 V | 6–8.4 V | — / 100 mA / ~3 A | Potentiometer (no readback) | **PWM 500–2500 µs** — no bus feedback | Metal | 40×20×40.5 | 56–60 g | ~£8–10 (indicative, $9.49) |
| **Dynamixel XL330-M288-T** | 0.52 N·m @ 5 V (0.42 @ 3.7 V, 0.60 @ 6 V) | — *not published* (est. 0.10–0.16 N·m) | 103 rpm @ 5 V | 3.7–6.0 V (5 V) | 17 mA standby / 150 mA / 1.47 A | 12-bit contactless (AS5601), 4096 | TTL half-duplex, Protocol 2.0 | Engineering plastic | 20×34×26 | 18 g | £27.20 RoboSavvy UK (verified); £34.40 Generation Robots |
| **Dynamixel XL330-M077-T** | 0.215 N·m @ 5 V | — *not published* | 383 rpm @ 5 V | 3.7–6.0 V (5 V) | 17 mA / 150 mA / 1.47 A | 12-bit contactless, 4096 | TTL half-duplex, Protocol 2.0 | Engineering plastic | 20×34×26 | 18 g | £22.19 RoboSavvy UK (verified) |
| **Dynamixel XL430-W250-T** | 1.5 N·m @ 12 V (1.4 @ 11.1 V, 1.0 @ 9 V) | — *not published* (est. 0.3–0.45 N·m) | 61 rpm @ 12 V | 6.5–12.0 V (11.1 V = 3S) | 52 mA standby / 150 mA / 1.4 A | 12-bit contactless (AS5601), 4096 | TTL half-duplex, Protocol 1.0 & 2.0 | Engineering plastic | 28.5×46.5×34 | 57.2 g | £27.20 RoboSavvy UK (verified); $23.90 Robotis |
| **Dynamixel XC430-W240-T** | 1.9 N·m @ 12 V (1.7 @ 11.1 V, 1.4 @ 9 V) | — *not published* | 70 rpm @ 12 V | 6.5–14.8 V (12 V) | 46 mA / 60 mA / 1.4 A | 12-bit contactless, 4096 | TTL half-duplex, Proto 1.0 & 2.0 | **Metal** | 28.5×46.5×34 | 65 g | £111.38 RoboSavvy UK (verified) |
| **MyActuator RMD-L-4005** (rejected example) | ~0.07 N·m rated class (direct drive) | ~0.07 N·m | 1600 rpm | 24 V | — | 15–18-bit encoder | CAN / RS485 | None (BLDC DD) | Ø40 mm | 65 g | $123 ≈ £97+ (indicative) — 10–20× over budget per joint |

¹ RobotShop lists 55±1 g for C018; an Alibaba listing states 70.5±1 g. Use ~60 g in mass budgets until weighed. Sources in §7.

### Key spec observations

- **Only Feetech and Waveshare publish rated (continuous) torque** for these parts (STS3215: 5 kg·cm @ 7.4 V = 26 % of stall; SCS15: 5.2 kg·cm = 33 %; STS3032: 1.5 kg·cm = 33 %; ST3215: 5 kg·cm). **Robotis publishes stall + N-T performance graphs but no continuous rating** — table cells left "—"; treat ~25 % of stall as a working estimate. **Hiwonder/LewanSoul publish only "torque" figures that are stall values** — flagged, do not read as continuous.
- **XL330-M288-T cannot drive this robot's legs.** 0.52 N·m stall vs ~1.1 N·m knee peak requirement (§4) — below even the *required continuous* value at 1.1 kg mass. Suitable only for neck/beak.
- **XL330/XL430 voltage mismatch with a 2S bus.** XL330 needs 5 V (max 6.0 V). XL430 is a 12 V part (6.5 V abs min, rated points at ≥9 V); running it on 7.4 V gives ~0.85–0.95 N·m stall (estimate by voltage scaling) — weaker than STS3215 at the same rail. An all-Dynamixel leg set wants **3S (11.1 V)**.
- **STS3215 7.4 V variant: input max = 7.4 V.** Raw 2S LiPo at 8.4 V full charge is over spec (community does it; datasheet doesn't sanction it). See §6 mitigation.
- **Hiwonder LX family downsides for RL locomotion:** potentiometer feedback over only 240° (0–1000 counts, ~0.24°/count vs 0.088° on magnetic encoders), **no current/load/torque feedback** (position/temp/voltage only), fixed 115200 baud (sync-read all joints at 50–100 Hz is tight vs Feetech 1 Mbaud), and a proprietary protocol with no LeRobot/rustypot support.
- **SCS15 uses a potentiometer, not a magnetic encoder** — lower resolution (1024 counts/220°) and a wear component; STS3215 is preferable at similar rated torque.
- **MyActuator RMD-L:** true integrated BLDC actuators start ~$123/unit and are 24 V CAN/RS485 — 12 joints ≈ £1,200, 4× the whole robot budget. Rejected on cost; revisit only if the project pivots to quasi-direct-drive research (out of scope).
- **Waveshare ST3215-7.4V is functionally a Feetech STS3215 rebadge** (identical torque/speed/current/encoder/register map; Feetech-protocol compatible, works with the same SDKs). Community reports slightly looser QC tolerances vs Feetech-branded units but it is a legitimate, well-stocked supply channel (Pi Hut, Amazon UK).

---

## 3. What "Microduck-class" robots actually use

- Hugging Face **LeRobot SO-ARM100 / SO-ARM101** arms use **6× Feetech STS3215** — the Seeed datasheet bundle for the SO-ARM101 confirms this exact part (cdn.robotshop.com SO-ARM101 datasheet PDF). The STS3215 is *the* reference servo for the sub-£500 open-humanoid ecosystem.
- **rustypot** (Pollen Robotics' Rust servo library, used in Reachy and LeRobot) has first-class support for **Feetech STS3215** (plus STS3250, SCS0009, SM8512BL) alongside Dynamixel XL320/XL330/XL430/XM430 — same Rust ecosystem Microduck ships in. Choosing STS3215 keeps us on-library rather than writing a servo driver.
- Microduck itself is closed hardware; the brief's 15-motor count at <$400 retail implies a ~$10–15 servo — consistent with STS3215-class pricing at volume, not Dynamixel.

---

## 4. Joint torque requirements (worked math)

### 4.1 Assumptions (state: ASSUMPTION unless cited)

| Symbol | Value | Basis |
|---|---|---|
| Total mass m | 1.1 kg | mid-point of brief 0.9–1.3 kg |
| Weight W = m·g | 1.1 × 9.81 = **10.79 N** | — |
| Thigh L₁ (hip pitch → knee) | 0.070 m | preliminary geometry |
| Shank L₂ (knee → ankle) | 0.080 m | preliminary geometry |
| Foot | 90 mm fore-aft, 70 mm wide | preliminary geometry |
| Ankle joint position on foot | centred → max fore-aft lever 45 mm, lateral lever 35 mm | assumption |
| CoM height above ankle (standing) | ~0.15 m | assumption pending CAD |
| Mass above knee (get-up) | ~0.9 kg | robot minus shanks+feet (~0.2 kg) |
| Swing-leg mass | ~0.35 kg | 5×55 g servos + ~75 g structure |
| Dynamic factor k_dyn | 1.5–1.75 on quasi-static peaks | typical for get-up/step events on sub-1.5 kg bipeds; to be refined by sim |
| Required stall margin | stall ≥ ~1.7× required peak | keeps transients under ~60 % of stall; gear+thermal headroom |

### 4.2 Scenario A — single-leg support (quasi-static, full weight on one leg)

Conservative: support leg carries all 10.79 N (real: ~8.4 N once swing leg excluded).

**Ankle pitch, worst case (CoM over toe edge):**
T = W × d = 10.79 N × 0.045 m = **0.49 N·m**
Typical walking band (CoM held within ±20 mm of ankle): T ≈ 10.79 × 0.02 = **0.11–0.22 N·m**

**Knee pitch** (leg near-straight, allow 15° flexion in gait):
lever = L₂·sin15° = 0.08 × 0.259 ≈ 0.021 m → T ≈ 10.79 × 0.021 ≈ **0.22 N·m**

**Hip pitch:**
- Stance (CoM near hip axis): ~0.1–0.2 N·m.
- Swing leg held horizontal: T = m_leg·g·d = 0.35 × 9.81 × 0.075 = **0.26 N·m**; with k_dyn ≈ 1.5 → **~0.4 N·m** peak.

**Hip roll** (torso held level, CoM laterally offset to foot edge):
T = W × d = 10.79 × 0.035 = **0.38 N·m** worst-case; typical 0.15–0.25 N·m.
*Note: the preliminary leg has no ankle roll — the hip roll servo is the only joint that can move CoM laterally, so do not undersize it.*

**Hip yaw:** swing-leg yaw acceleration + stance-foot scrub. Estimate **0.05–0.15 N·m** — friction-dominated, needs validation in sim.

### 4.3 Scenario B — deep knee-bend get-up (governing case)

**B1 — symmetric two-leg squat, knee at 90° (thigh horizontal):**
Mass above knees ≈ 0.9 kg shared → F_per_leg = 4.4 N.
Knee: T = F × L₁ = 4.4 × 0.07 = **0.31 N·m** static → ×1.5 dyn ≈ **0.46 N·m**.
Ankle: shank near vertical → 0.1–0.2 N·m.

**B2 — asymmetric one-leg-dominant get-up** (Microduck-style recovery; the design driver):
F = 0.9 kg × 9.81 = 8.83 N on the dominant leg.
- **Knee:** T = 8.83 × 0.07 = **0.62 N·m** static → ×1.75 dyn ≈ **1.08 N·m peak**.
- **Ankle** (CoM ~40 mm ahead during push): T = 8.83 × 0.04 = **0.35 N·m** static → ~0.6 N·m peak.
- **Hip pitch** (torso leaned ~50 mm off hip axis, ~0.7 kg supported): T = 6.87 × 0.05 ≈ 0.34 N·m; lean to 70 mm → 0.48 N·m → ~0.8 N·m peak.
- **Hip roll** during asymmetric push (~50 mm offset): 8.83 × 0.05 ≈ **0.44 N·m** → ~0.7 N·m peak.

### 4.4 Scenario C — worst-case ankle, robot held tilted

Rigid-body tilt, CoM at recoverable foot edge (45 mm): T = 10.79 × 0.045 = **0.49 N·m**.
Equivalent tilt check: 20° lean, CoM 0.15 m above ankle → lever = sin20° × 0.15 = 0.051 m → T = 10.79 × 0.051 = **0.55 N·m**; ×1.5 → ~0.83 N·m peak.

### 4.5 Required torques → joint → candidate mapping

| Joint (per side) | Required continuous | Required peak | Candidate (stall / rated) | Verdict |
|---|---|---|---|---|
| Hip pitch | ~0.3 N·m | ~0.9 N·m | STS3215 (1.91 / 0.49 N·m) | OK — stall margin 2.1× |
| Hip roll | ~0.4 N·m | ~0.7 N·m | STS3215 | OK — margin 2.7× |
| Knee pitch | **~0.5 N·m** | **~1.1 N·m** | STS3215 | **Binding joint** — stall margin 1.7×, but required continuous ≈ published rated (0.49). Keep mass ≤1.1 kg, manage duty, monitor temp via feedback. Upgrade path in §5. |
| Ankle pitch | ~0.3–0.4 N·m | ~0.8 N·m | STS3215 | OK — margin 2.4× |
| Hip yaw (opt.) | ~0.1 N·m | ~0.3 N·m | STS3215 (uniform BOM) or STS3032 | OK |
| Neck pitch + yaw | <0.1 N·m | ~0.2 N·m | STS3032 (0.44 / 0.15 N·m) or XL330-M288 | OK — head+beak est. 60–100 g |
| Beak | <0.05 N·m | ~0.1 N·m | 9 g PWM micro (SG90/MG90S, £3–5) off a spare PWM pin, or STS3032 | Cheap + light; doesn't need bus feedback |

**Read on the knee constraint:** STS3215's published *rated* 0.49 N·m sits exactly at our knee's continuous requirement. Feetech's life-test basis is 1/5 stall cyclic loading (>100k cycles per datasheet §8), and our worst continuous state is transient (get-up is seconds). Mitigations: (a) hold total mass ≤1.1 kg — every +100 g adds ~0.07 N·m to the knee; (b) software current/temp limits + rest-detection; (c) deepen knee lever geometry if CAD allows; (d) upgrade path: STS3215-C018 on 12 V doubles published rated torque to 0.98 N·m, or XC430-W240-T metal-gear (see §5). If the mass budget slips toward 1.3 kg, the knee spec becomes a real risk — flag to the structures workstream.

---

## 5. Complete actuator strategies — comparison

DOF count used for costing: **12 smart servos** (10 leg: 5/leg incl. hip yaw; +2 neck). Beak = optional PWM micro (all strategies). Prices GBP, 2026-10-26; "import" prices assume AliExpress/direct + ~20 % VAT-included landing.

### Strategy A — All-Feetech, 2S bus (RECOMMENDED)

| BOM | Qty | Unit | Line |
|---|---|---|---|
| STS3215-C001 | 10 | £13 import / £26 UK | £130–260 |
| STS3032-C001 (neck ×2) | 2 | £10 import / £29 UK | £20–58 |
| **Actuator total** | | | **~£150–318** (realistic mixed sourcing ~£180–220) |

- **Mass:** 10×55 + 2×20 = **~590 g** actuators.
- **Bus:** one TTL half-duplex UART rail, 1 Mbaud; needs a half-duplex driver (Waveshare ESP32 servo driver board £15.40 at Pi Hut, or Feetech URT-1/SCPC-2, or simple UART+tri-state on the MCU).
- **Control complexity:** low — single protocol, position/velocity/load/voltage/current/temp feedback, accel shaping built in. SDKs: LeRobot `scservo_sdk`/`feetech-servo-sdk` (Python), Arduino `SCServo`, **rustypot** (Rust — matches our likely stack).
- **Repairability:** excellent — cheapest possible spares, huge stock depth (SO-ARM101 demand), swap-and-re-ID in minutes.
- **Performance:** covers all joints per §4.5; knee is marginal-continuous but workable. 52 rpm ≈ 312°/s joint speed — adequate for this scale.
- **Power:** 12×2.5 A stall theoretical = 30 A worst-case; realistic walking peak ~4–8 A → 2S LiPo ≥1500 mAh 20–30 C + 25 mm²-class bus wiring. **Overvoltage caveat: 7.4 V max vs 8.4 V charged 2S** — mitigate with regulated bus or LiFePO4 (see §6).

### Strategy B — All-Dynamixel, 3S bus

| BOM | Qty | Unit | Line |
|---|---|---|---|
| XL430-W250-T | 10 | £27.20 | £272 |
| XL330-M288-T (neck ×2) | 2 | £27.20 | £54.40 |
| **Actuator total** | | | **~£326 — exceeds the entire robot budget** |

- Proper leg part is really **XC430-W240-T** (metal gears, 1.9 N·m) → 10×£111 = **£1,114** — rejected outright.
- **Mass:** 10×57.2 + 2×18 = 608 g. **Control:** best-in-class docs (e-manual), DYNAMIXEL SDK/Wizard, Protocol 2.0 sync read/write, U2D2 interface.
- **Fatal flaws for this build:** XL430 on 3S gives 1.4 N·m stall @ 11.1 V → only ~1.3× margin over the 1.1 N·m knee peak (thin), plastic spur gears, and no published continuous rating; XL330 is head-joint-only. Cost-per-N·m is ~5× Feetech. Rejected on cost + thin margins.

### Strategy C — Mixed-tier / availability-driven (PRAGMATIC VARIANT of A)

| BOM | Qty | Unit | Line |
|---|---|---|---|
| Waveshare ST3215-7.4V *or* Feetech STS3215 (whichever in stock) | 10 | £21–23 UK | £210–230 |
| STS3032-C036 or XL330-M288-T (neck) | 2 | £24–27 | £48–54 |
| **Actuator total** | | | **~£260–285 all-UK-sourced** |

- Same Feetech-protocol bus for ST3215/STS parts (XL330 would need a separate 5 V rail + Protocol 2.0 — prefer STS3032 to keep one bus).
- Identical performance to A; trades a little QC consistency (Waveshare) for UK-stock convenience. **This is the fallback if AliExpress supply slips.**

### Strategy D — Hobby PWM fallback (MVP only)

LDX-218-type 17 kg·cm PWM servos (~£8–10) or MG996R (~£5): 12× ≈ **£60–120**.
- No position/load/temp feedback → dead-reckoned joints, no proprioception for RL policies, no bus wiring simplicity (12 PWM channels + big wiring loom). PWM servos of this class also publish only stall torque.
- **Verdict:** acceptable for a proof-of-motion chassis bring-up or as spares-bin parts; does not meet the "position/temp/load feedback" requirement in the brief. Not recommended for the final robot.

### Comparison summary

| | A: Feetech 2S | B: Dynamixel 3S | C: Waveshare/Feetech mix UK | D: PWM hobby |
|---|---|---|---|---|
| Actuator cost | £150–220 (mixed sourcing) | £326+ | £260–285 | £60–120 |
| Actuator mass | ~590 g | ~608 g | ~590 g | ~600–660 g |
| Continuous margin @ knee | ~1.0× rated (managed) | est. <1× (unpublished) | same as A | unknown (no data) |
| Peak margin @ knee | 1.7× | 1.3× | 1.7× | ~1.5× stall-only |
| Feedback richness | pos/vel/load/V/I/T | pos/vel/load/V/I/T | same as A | none |
| Bus speed | 1 Mbaud | 4.5 Mbaud | 1 Mbaud | 50 Hz PWM |
| Software ecosystem | LeRobot, rustypot, SCServo | Dynamixel SDK/Wizard | same as A | servo library |
| Repairability | excellent (£10–26/spare) | fair (£27/spare) | good | excellent but weak parts |
| Budget fit | **fits** | **fails** | fits | fits but fails spec |

---

## 6. Recommendation

**Primary: Strategy A/C hybrid — Feetech-protocol TTL servos on a 2S rail.**

- **Legs (10×):** Feetech STS3215-C001 where sourcing allows; Waveshare ST3215-7.4V interchangeable (same protocol/footprint class). Buy 11–12 to hold a spare — repairability goal.
- **Neck/head (2×):** Feetech STS3032 (20 g, magnetic encoder, same bus, same SDK).
- **Beak:** 9 g-class PWM micro servo on a spare MCU pin (~£4) — keeps cost/complexity down; only upgrade to bus servo if beak needs force feedback.
- **Bus interface:** Waveshare ESP32 serial-servo driver (£15.40, Pi Hut) for bench work; integrate a UART half-duplex transceiver on our MCU board for the robot (electronics workstream to pick up).
- **Battery/bus decision needed (flag to brief):** STS3215-C001's 7.4 V max vs 8.4 V charged 2S LiPo. Options ranked: **(1) 2S LiFePO4** — 6.4 V nominal, 7.3 V max, inside spec, safe chemistry; **(2) buck-regulated 7.4 V** from 2S/3S Li-ion; (3) accept 8.4 V on LiPo (community practice, out of datasheet spec — not recommended to design-in); (4) switch leg servos to wide-input ST3020 (6–14 V) — also fixes option to move to 3S later.

**Cheaper fallback:** Waveshare ST3215-7.4V (Amazon UK £22.99 verified, waveshare.com $16.99) or import STS3215 at ~£10–13; Hiwonder LX-16A (~£14–18) only if budget is desperate — loses current/load feedback, resolution, baud rate, and ecosystem support. Absolute-floor MVP: LDX-218 PWM ~£9 (Strategy D).

**Performance alternative (if budget grants +£60–150):**
- *Within Feetech:* **ST-3020-C001** (20 kg·cm @ 7.4 V, slimmer 40×20×40 body) at knees/ankles; or move the whole bus to 12 V with **STS3215-C018** (30 kg·cm stall / **10 kg·cm published rated** @ 12 V — doubles the knee continuous margin) — but forces a 3S/regulated rail and pushes actuators to ~£24–25 each UK.
- *Outside Feetech:* **Dynamixel XC430-W240-T** (1.9 N·m stall, metal gears) on knees/hips on a 3S rail — £111 each makes it a per-joint upgrade only (e.g., 4× knee+ankle-pitch ≈ £445 — likely still too rich; treat as a stretch experiment, not baseline).

---

## 7. Sources

Datasheets/specs:
- Feetech STS3215 official spec (A/0, 2020-04-10): https://www.feetech.cn/Data/feetechrc/upload/file/20260622/6391772523943436695270694.pdf and translated https://core-electronics.com.au/attachments/uploads/sts3215-smart-servo-datasheet-translated.pdf — rated 4/5 kg·cm @ 6/7.4 V; stall 16.5/19.5; life >100k cycles @ 1/5 stall.
- Feetech ST-3215-C001 product page (note: page lists rated 6.5 kg·cm @ 6 V vs datasheet 4 kg·cm — **vendor self-inconsistency flagged; datasheet used**): https://www.feetech.cn/en/74v-19-kgcm-plastic-case-metal-tooth-magnetic-code-double-axis-ttl-series-steering-gear.html
- Feetech STS3032 datasheet: https://evelta.com/content/datasheets/501-STS3032.pdf ; product page https://www.feetech.cn/6v-45kg-magnetic-code-360-degree-serial-bus-steering-gear.html
- Feetech SCS15-C022 product page (rated torque 5.2 kg·cm published): https://www.feetech.cn/en/6v-15kg-digital-robot-steering-gear
- Feetech ST series wiki (ST-3020-C001: 20 kg·cm @ 7.4 V, 68 rpm @ 8.4 V): https://ftservo.github.io/ftservo-wiki/en/products/datasheets/st/
- Waveshare ST3215 docs/specs/prices: https://docs.waveshare.com/ST3215_Servo ; https://www.waveshare.com/st3215-servo.htm
- Waveshare ST3020 wiki (6–14 V, 25 kg·cm @ 12 V): https://www.waveshare.com/wiki/ST3020_Servo
- Robotis e-manual XL330-M077: https://turtlebot3.ncnynl.com/en/turtlebot3/docs/en/dxl/x/xl330-m077/ ; XL330-M288: https://en.robotis.com/shop_en/item.php?it_id=902-0163-000 ; XL430-W250: https://turtlebot3.ncnynl.com/en/turtlebot3/docs/en/dxl/x/xl430-w250/ ; XC430-W240: https://emanual.robotis.com/docs/en/dxl/x/xc430-w240/
- Hiwonder LX-16A: https://www.hiwonder.com/products/lx-16a (+ manual PDF cdn.robotshop.com); LX-15D: https://www.hiwonder.com/products/lx-15d ; LX-224: https://www.hiwonder.com/products/lx-224 ; HTS-35H: https://www.hiwonder.com/products/hts-35h ; LDX-218: https://www.hiwonder.com/products/ldx-218
- MyActuator L series: https://myactuator.us/products/l-series
- rustypot (Rust SDK, Feetech STS3215 + Dynamixel): https://github.com/pollen-robotics/rustypot
- SO-ARM101 servo datasheet bundle: https://cdn.robotshop.com/media/S/See/RB-See-1200/pdf/seeedstudio_so_arm101_low_cost_ai_arm_3d_printed_s_servo_motor_datasheet.pdf

Prices (checked 2026-10-26):
- STS3215-C001 7.4 V: £26.30 uk.robotshop.com (verified); ~£29 eBay UK (verified); $13–16 Alibaba/AliExpress ≈ £10–13 (indicative)
- STS3215-C018 12 V: £24.32 uk.robotshop.com; £25.00 rchobby-models.co.uk (verified)
- STS3032-C001/C036: £29.45 / £24.30 rchobby-models.co.uk (verified)
- Waveshare ST3215-7.4V: £22.99 amazon.co.uk (verified); 30 kg version £20.30 uk.robotshop.com (verified)
- Waveshare ST3020: £19.40 thepihut.com (verified); $19.99 waveshare.com
- XL330-M077-T £22.19 / XL330-M288-T £27.20 / XL430-W250-T £27.20 / XC430-W240-T £111.38 — robotis.co.uk / robosavvy.co.uk (verified); Generation Robots £34.40 for XL330-M288
- Hiwonder direct USD: LX-16A $16.99, LX-15D $16.99, LX-224 $15.99, HTS-35H $21.99, LDX-218 ~$9.49 (indicative GBP ~£8–18 + shipping); eBay UK LX-16A ~£13.69–17.72 + shipping (indicative)
- MyActuator L-4005 $123 (indicative ~£97+)

---

## 8. Candidate BOM rows (per brief CSV schema)

```
category,item,part_number,manufacturer,qty,unit_price_gbp,source_url,supplier,price_date,price_type,mass_g,notes,alternative
actuator,leg smart servo 19.5kg TTL,STS3215-C001,Feetech,10,26.30,https://uk.robotshop.com/products/magnetic-encoding-servo-sts3215-74v-19kgcm,RobotShop UK,2026-10-26,verified,55,stall 1.91Nm/rated 0.49Nm @7.4V; 4-7.4V input max — see §6 bus note; ~£10-13 via AliExpress,Waveshare ST3215-7.4V
actuator,leg smart servo 19.5kg TTL,ST3215-7.4V,Waveshare,10,22.99,https://www.amazon.co.uk/Waveshare-Servo-Precision-Programmable-Switchable/dp/B0G2576KKN,Amazon UK,2026-10-26,verified,55,protocol-compatible STS3215 rebrand; same bus/SDK,Feetech STS3215-C001
actuator,neck smart servo 4.5kg TTL,STS3032-C001,Feetech,2,29.45,https://rchobby-models.co.uk/feetech-sts3032-st-3032-c001-6v-ttl-servo,RC Hobby-Models UK,2026-10-26,verified,20,stall 0.44Nm/rated 0.15Nm @6V; ~£8-12 import,XL330-M288-T (needs 5V rail)
actuator,neck smart servo alt,XL330-M288-T,Robotis,2,27.20,https://robotis.co.uk/robotis-dynamixel-xl330-m288-t.html,RoboSavvy UK,2026-10-26,verified,18,stall 0.52Nm @5V; TOO WEAK for legs; needs 5V+Protocol2,STS3032
actuator,beak micro servo PWM,MG90S-class,generic,1,4.00,,Amazon/AliExpress,2026-10-26,estimate,14,metal-gear micro on spare PWM pin; no feedback needed,STS3032 if bus feedback wanted
actuator,knee/ankle upgrade 20kg TTL,ST-3020-C001,Feetech,0-4,20.00,https://ftservo.github.io/ftservo-wiki/en/products/datasheets/st/,import,2026-10-26,estimate,58,20kgcm@7.4V slimmer body; UK stock thin,Waveshare ST3020 (25kg@12V; 6-14V input)
actuator,perf upgrade 12V 30kg TTL,STS3215-C018,Feetech,0-10,24.32,https://uk.robotshop.com/products/feetech-12v-30kgcm-magnetic-encoding-servo-sts3215,RobotShop UK,2026-10-26,verified,60,stall 2.94Nm/rated 0.98Nm @12V — needs 3S/regulated rail,ST3020
actuator,perf leg servo Dynamixel,XC430-W240-T,Robotis,0-4,111.38,https://robosavvy.co.uk/xc430-w240-t.html,RoboSavvy UK,2026-10-26,verified,65,1.9Nm stall metal gear; 10-14.8V — stretch experiment only,STS3215-C018
actuator,fallback PWM servo 17kg,LDX-218,LewanSoul/Hiwonder,0-12,9.00,https://www.hiwonder.com/products/ldx-218,import,2026-10-26,indicative,58,PWM no feedback — MVP bring-up/spares only,MG996R ~£5
actuator,bus servo debug/driver,ESP32 Servo Driver,Waveshare,1,15.40,https://thepihut.com/products/esp32-servo-driver-with-wifi-and-bluetooth,The Pi Hut,2026-10-26,verified,,bench debug + could host onboard MCU function,Feetech URT-1
```

---

## 9. Open questions / flags for other workstreams

1. **Brief conflict — bus voltage:** brief says "7.4 V nominal (2S)". STS3215-C001 max input is 7.4 V but a charged 2S LiPo is 8.4 V. Recommend the brief specify **"2S LiFePO4 or buck-regulated 7.4 V"** unless we switch to wide-input servos. Electronics workstream to pick a bus regulator / battery chemistry.
2. **Mass budget interaction:** knee continuous margin only holds if total mass ≤ ~1.1 kg at this geometry. If CAD pushes toward 1.3 kg, knee/ankle need the ST-3020/12V upgrade (~+£20–40) — flag to structures.
3. **No ankle roll in preliminary leg** — hip roll is sole lateral balance actuator; sizing already reflects that. If ankle roll is later added, hip roll requirement relaxes.
4. **Continuous ratings unavailable** for Robotis and Hiwonder — all continuous claims for those parts are 20–30 %-of-stall estimates pending bench thermal testing. Validation plan: instrumented 10-min continuous-hold at 0.5 N·m on a sacrificial servo, log internal temp via feedback.
5. **Protocol collision risk:** Feetech TTL protocol ≠ Hiwonder TTL protocol ≠ Dynamixel Protocol 2.0 — do not mix brands on one physical bus.
6. **Verification still needed:** actual STS3215-C001 behaviour at 8.4 V (overvolt protection triggers?), ST3020 at 7.4 V real torque curve, LX-16A position-feedback jitter (potentiometer) — bench tests recommended before BOM freeze.
