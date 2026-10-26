# Shared Design Brief — Knoll Mk1

**Version:** 1.1 — 2026-10-29 — **REDIRECT (user-approved, pending full re-validation).** Supersedes v1.0 concept/DOF rows below. v1.0 text kept for record; see revision note.

> **v1.1 revision note:** after the shell-v0 visual review the concept direction changed from *dome-shelled moss creature* to **agile biped-droid archetype** (compact torso + small actuated head + 2-DOF arms), Microduck-category but independently designed. DOF 10 → **15** (5/leg + 2/arm pitch+roll + 1 neck pitch). Direct consequences: mass estimate ~1.09 → ~1.4 kg — **breaches the 1.15 kg knee-torque gate** (mitigations: lighter arm/neck servo class, C018 legs, mass trim); height ~27 → ~30 cm; cost +~£100–150. Actuator study, mass budget and cost model require re-validation before build. Keeps name "Knoll" only — no moss/dome cues. Everything else in v1.0 (electrical architecture, control stack, staged recovery, licensing) carries forward; recovery now includes arm push-assist in scripted keyframes.

## Mission

Original, open-hardware, DIY-buildable mascot robot — comparable capability class to Microduck (small RL biped, self-recovery) — independently designed, repairable, lower or comparable DIY cost.

## Verified Microduck baseline

25 cm · 780 g · 15 servos (14 policy joints + beak) · XL330-family on Dynamixel-protocol bus @1 Mbps · custom BNO08x-class IMU bridge · RK3566 SBC (Radxa Zero 3W) · camera + 8×8 ToF + 2 IMU · 50 Hz policy · MuJoCo/mjlab+PPO+BAM, ONNX · €340 UK-billed · software Apache-2.0, **hardware closed**.

## Locked architecture (ADR-001)

| Parameter | Value |
|---|---|
| Concept | **Knoll** — dome-shelled moss creature, fused head, LED-matrix eyes, magnetic topper |
| Size/mass | ~27 cm · **≤1.15 kg gate** (est ~1.09 kg) |
| DOF | **10** (5/leg: hip_yaw, hip_roll, hip_pitch, knee, ankle) — no ankle roll, no neck v1; mounts+2 bus slots reserved |
| Actuators | **10× Waveshare ST3020** (6–14 V TTL serial, 25 kg·cm stall @12 V) + 2 spares; STS3215-C001 fallback; C018 perf upgrade |
| Servo rail ⓒ | **direct 2S LiPo** (ST3020's 6–14 V input makes 8.4 V in-spec — v0.1's "7.4 V bus" revised: rail is 6.0–8.4 V unregulated) |
| Compute | RP2350 Pico 2 W (safety owner, both buses, watchdog) + optional socketed Pi Zero 2 W (50 Hz ONNX policies) |
| IMU | BNO085 fused quaternion (BMI270 fallback) |
| Battery | 2S LiPo 2200 mAh, toolless sled, est ~55–65 min |
| Structure | PETG-CF structural / PLA cosmetic / TPU soles; M3 heat-set inserts; dual-bearing joints |
| Cost | MVP ~£215 · recommended ~£300 UK-sourced (~£280 import-servo) · perf ~£490 |
| Sim/control | MuJoCo + BAM SysID + PPO/CrossQ → ONNX, deterministic safety layer on MCU |

## Common BOM CSV schema
`category,item,part_number,manufacturer,qty,unit_price_gbp,source_url,supplier,price_date,price_type,mass_g,notes,alternative`

## Standing rules
No invented specs/prices. Stall≠continuous always separated. GBP+dates+URLs on prices. Facts/estimates/assumptions labelled. Conflicts documented, not smoothed over.
