# Shared Design Brief — Knoll Mk1

**Version:** 1.0 — 2026-10-26 — LOCKED (post-research). Supersedes v0.1 assumptions where research forced changes. Changes vs v0.1 marked ⓒ.

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
