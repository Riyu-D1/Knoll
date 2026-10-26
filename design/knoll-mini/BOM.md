# Knoll Mini — Bill of Materials & Cost

Target: **~19 cm, ~350 g, ~£230 all-in** — vs Microduck's ~25 cm / ~800 g / ~£650+ (genuine XL330s).
All prices GBP, typical AliExpress/generic-supplier prices (Nov 2025).

## Actuators — corrected street prices (Nov 2025)

First-pass pricing was wrong: STS3032 is **~£20 on AliExpress, not £14**. Re-surveyed market:

| Servo | Torque (stall/rated) | Size mm | g | Street £ | Feedback |
|-------|----------------------|---------|---|----------|----------|
| Feetech STS3032 | 0.44 / 0.15 N·m | 23×12×28 | 20 | **~20** | Serial full |
| Feetech SCS0009 / Waveshare SC09 | 0.22 / 0.07 N·m | 23×12×25 | 13 | **~8–9** | Serial full |
| Hiwonder LX-15D | 1.7 N·m | 40×20×40 | ~50 | ~8.5 | Serial (pos) |
| Feetech SCS15 | 1.5 N·m | ~35×17×40 | ~31 | ~12 | Serial full |
| DSServo DS3218 | 2.0 N·m | 40×20×37 | 60 | ~9 | Analog (none) |
| MG90S | 0.25 N·m | 23×12×29 | 13 | ~3 | Analog (none) |

### Config options — size is set by which servo the knee can afford

**A. Stay 19 cm, split servos** — 4× STS3032 (hip pitch + knees, the load joints) + 8× SCS0009 (hip yaw/roll, ankles, neck): bill **~£152**. Still pricey for marginal gain.

**B. Shrink to ~15–16 cm — all SCS0009** — 12× ~£8.5 ≈ **£105**. Mass drops to ~230 g → knee worst-case ~0.10 N·m vs 0.22 stall: workable for gentle walking. Smallest and (honestly) the *most* BDX in proportion — bigger head-to-body ratio = cuter.

**C. Grow to ~24–25 cm — LX-15D / SCS15 legs** — 10× ~£8.5–12 + 2× SCS0009 ≈ **£105–140**. Real torque margin (8× headroom), easy walking + recovery — but back at Microduck height, not pocket.

**D. Cheapest possible — all MG90S analog** — 12× ~£3 ≈ **£36**, stays 19 cm. No position/load feedback → Otto-style scripted oscillator gaits only; loses Microduck-style compliance sensing and RL-pipeline compatibility. Self-recovery becomes scripted at best.

**Torque math:** knee worst case ≈ mass × g × leg lever (~60 mm). 350 g → 0.21 N·m; 230 g → 0.14 N·m; 800 g → 0.5 N·m. Serial feedback is what makes Microduck-family control possible; analog saves ~£100 but forecloses the RL path.

## Electronics

| Qty | Part | Role | Unit £ |
|-----|------|------|--------|
| 1 | ESP32-S3 dev board (XIAO ESP32-S3 or WROOM mini) | Main controller: servo bus master, policy inference (TFLite), WiFi | 7 |
| 1 | BNO085 IMU breakout | Orientation fusion (fallback: MPU-6050, £2) | 10 |
| 1 | VL53L0X ToF breakout | **Right eye**: distance sensor | 4 |
| 1 | OV2640 camera module (FPC) | **Left eye**: vision | 4 |
| 2 | WS2812 8-LED rings (~18 mm) | Eye glow — expressions, status | 3 |
| 1 | MAX98357A I2S amp | Audio | 3 |
| 1 | 20 mm 8 Ω speaker | Voice/beeps (behind face grille dots) | 2 |
| 1 | INMP441 I2S mic (optional) | Sound reactivity | 3 |
| 1 | 6 V 5 A buck regulator | Servo rail (2S → 6 V; keeps STS3032 inside its 4–7.4 V spec) | 3 |
| 1 | Feetech TTL bus hub / debug board | Servo daisy-chain + USB programming | 8 |

## Power

| Qty | Part | Unit £ |
|-----|------|--------|
| 1 | 2S 450 mAh LiPo (~48×28×14 mm — battery slot sized to this) | 9 |
| 1 | USB-C 2S balance charger module | 6 |
| 1 | Power switch + JST leads | 3 |

## Structure / misc

| Qty | Part | Unit £ |
|-----|------|--------|
| ~300 g | PETG filament (printed shell, feet, flippers, head bar) | 6 |
| 1 set | M2/M2.5 screws + heat-set brass inserts (~60 pcs) | 8 |
| 4 | 3×8×4 mm flange bearings (un-driven servo hubs) | 3 |
| 1 | Servo horns/brackets kit + wiring, heat-shrink | 8 |

## Total

| Scope | £ |
|-------|---|
| Actuators | 158 |
| Electronics | ~48 |
| Power | 18 |
| Structure | ~25 |
| **Build total** | **≈ £250** (≈ £235 with MPU-6050 instead of BNO085) |

## The eyes — Imagineer logic

Each lamp-eye is a **light + sensor pod**:

- **Left eye**: OV2640 camera behind the ring → sees forward, frames for vision/follow behaviors.
- **Right eye**: VL53L0X ToF behind the ring → distance → approach detection → reactions.
- **Both**: WS2812 ring in front of the sensor window → the eye still *glows* (expression layer) while the sensor sees through the ring's open center.

That's the Disney BDX trick: the face IS the sensor pod, one cosmetic surface doing three jobs (expression, depth sensing, vision) at zero extra volume — which is how an 84 mm-wide head carries a camera, a ranger, a mic hole, and a speaker grille without growing.

## What 12 DOF costs vs Microduck's 14

Dropped: head_pitch + head_roll (2 servos, –£18, –40 g) — kept neck pitch + yaw, which is what reads as "alive". Arms stay static flippers (as on Microduck — they were never actuated there either).
