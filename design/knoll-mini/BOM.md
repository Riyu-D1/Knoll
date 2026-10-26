# Knoll Mini — Bill of Materials & Cost

Target: **~19 cm, ~350 g, ~£230 all-in** — vs Microduck's ~25 cm / ~800 g / ~£650+ (genuine XL330s).
All prices GBP, typical AliExpress/generic-supplier prices (Nov 2025).

## Actuators — 12 DOF total

| Qty | Part | Role | Unit £ | Sub £ |
|-----|------|------|--------|-------|
| 10 | Feetech STS3032 (serial TTL, 20 g, 23×12×28 mm, 0.44 N·m stall / 0.15 N·m rated, position+temp+load feedback) | Legs: hip yaw/roll/pitch, knee, ankle ×2 | 14 | 140 |
| 2 | Feetech SCS0009 (serial, 9 g, ~22 mm, 0.22 N·m peak) | Neck pitch + yaw | 9 | 18 |

Serial bus = daisy-chained wiring + position/load/temperature feedback on every joint — required for a walking policy, which is why plain £3 analog servos were rejected despite the lower price.

**Knee-margin flag:** STS3032 rated torque (0.15 N·m) is tight for a 350 g biped at full leg extension (~0.2 N·m worst case). Mitigations: keep CoM low + feet under hips, bias the gait to bent knees, and if it stalls, the same frame accepts Feetech STS3215-class (55 g, 1.9 N·m) at +£6/servo and +35 g each — frame geometry is parametric (`SV_LEG` constant).

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
