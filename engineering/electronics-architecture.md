# Electronics Architecture — Knoll Mk1

**Date:** 2026-10-26 · **Status:** Architecture selected; component BOM with verified prices in `bom/master-bom.csv`. Full research + flags in `engineering/notes-electronics.md`. PCB specifics in `engineering/pcb-specification.md`.

---

## 1. Architecture decision

**Split architecture:** RP2350 (Pico 2 W) real-time node + socketed, optional Pi Zero 2 W high-level node — mirroring the proven Open Duck Mini pattern (Pi Zero 2 W runs 50 Hz ONNX policies) and adding a safety-owning MCU layer Microduck implements inside `robotd` (we do it in hardware/firmware instead — stronger isolation).

- **MCU owns:** both servo buses, IMU, joint clamps, watchdog torque ramp-down, brownout derate, e-stop. **Robot stands, idles and safes itself with the SBC absent or dead.**
- **SBC owns:** policy inference (ONNX), FSM, telemetry, camera (optional), WiFi clients.
- **v1 fallback:** MCU-only, USB-CDC tether to a laptop — cheapest bring-up; SBC is a socketed add-on, not a redesign.
- Rejected: ESP32-S3 (WiFi jitter on control path; kept as option), STM32G4 (fine part, thinner bus-servo ecosystem), CM4/5 (overkill + carrier complexity), Radxa Zero 3W (£77, thin UK supply — though it IS what Microduck uses), MCU-only-forever (no camera/heavier policies).

## 2. Servo bus

- Servos (Waveshare ST3020 / Feetech STS-class): single-wire half-duplex TTL, 38.4 k–1 Mbaud, 3-pin 5264-3A/KK254 connectors `GND|DATA|V+`.
- **Two independent buses:** UART0 → left leg (5), UART1 → right leg + aux (5+) — halves latency and fault domain.
- Interface circuit per Waveshare open reference: `SN74LVC1G126` (TX→DATA, TXEN) + `SN74LVC1G125` (DATA→RX) at 3.3 V, GPIO direction control, SMAJ TVS + 100 Ω series on DATA, 220 µF bulk per branch.
- **Trap:** 5264-3A ≠ JST-XH (lookalike, doesn't latch) — keyed 5264 housings only.
- 3.3 V→bus logic level is community-proven (whole LeRobot/SO-ARM ecosystem); keep 5 V-VCC populate option as margin.

## 3. Power architecture

```
2S LiPo 2200mAh (XT30+JST-XH bal) → [E-STOP 15A] → [FUSE 10A] → [P-FET AO4407 rev-pol]
   ├──► 8.4V-max SERVO RAIL (star distribution; NEVER through MCU/SBC)
   │      ├─ Bus A 5264×5 (L leg) · Bus B 5264×5+ (R leg, aux)
   │      └─ VBAT sense divider → MCU ADC (brownout derate/cut)
   └──► [BUCK 5V/3A fixed] → Pi Zero 2W, camera, LED eyes, aux 5V
          └──► [3.3V via Pico reg] → RP2350, buffers, BNO085
```

- **Why direct 2S works:** selected servos accept 6–14 V (ST3020) — charged-2S 8.4 V is in-spec. If STS3215-C001 (7.4 V max) is substituted, the rail needs 2S LiFePO4 or a 15 A buck — documented in actuator-study §4.
- Rules: servo current never transits logic boards; fuse on servo rail (PTC on 5 V branch only); fixed-output buck (no pots — vibration drifts them); ≥470 µF low-ESR on buck in, 220 µF out; MCU ADC watches VBAT (derate <6.6 V, torque-off <6.0 V); hard e-stop = 15 A latching switch in battery lead (software torque-off is layer 2, not the cut).
- Battery: **2S LiPo 2200 mAh 30C+** (£15–17 verified) in a toolless rear sled; XT30 main + JST-XH balance out for charging; external B3-class charger. 18650-pack alternative noted (safer handling, −capacity, +complexity).

## 4. Power budget (10-servo build)

| Load | Typical (est) | Bounded peak | Rail |
|---|---|---|---|
| 10× servo gait (~150–200 mA avg ea) | 1.0–1.5 A | 10×1 A FW-limited = **10 A** (true 25 A all-stall prevented by FW current limit) | 7.4 V |
| Pi Zero 2W + optional camera | 0.15–0.3 A | 0.6 A | 5 V |
| RP2350 + buffers + BNO085 | 0.05 A | 0.15 A | 3.3 V |
| LED eyes + status | 0.05–0.15 A | 0.4 A | 5 V |

- Typical ≈ **8–13 W**; worst bounded ≈ ~80 W transients. Runtime: 16.3 Wh ×0.8 / ~12 W ≈ **~55–65 min walk** — meets ≥45 min (bench-validate; provision sled for 3000 mAh).
- Battery C-rating: 2.2 Ah × 30 C = 66 A ≫ 10 A bounded peak. Wire: 20 AWG trunk, 22 AWG branches, 26 AWG logic.

## 5. Compute & sensing

| Slot | Pick | Price (2026-10-26) | Alt |
|---|---|---|---|
| MCU | **Pico 2 W (RP2350+WiFi)** £6.24 Rapid | 2 UARTs + PIO, native USB, Rust/C SDK | Pico 2 £5.39; ESP32-S3 £9.60 |
| SBC (optional) | **Pi Zero 2 W** £14.40 | runs 50 Hz ONNX + camera; intermittent stock — buy early | none (MCU-only mode) |
| IMU | **BNO085 breakout** £28.40 Pi Hut | fused SH-2 quaternion over I²C — the same fusion class Microduck's custom board uses | BMI270 £17.80 + Madgwick on MCU |
| Eyes | 2× 8×8 LED matrix (MAX7219 or WS2812) ~£4 | face = status display | — |
| Camera | **OPTIONAL v1** — Pi Cam 3 £24 / ZeroCam £15 | locomotion policies are proprioceptive-only (reference-proven); cable route kept clear | — |
| Foot contact | OPTIONAL: 2 microswitches/foot ~£0.60 ea | policy obs includes them only if fitted AND trained | FSR (worse: noisy/drifty) |
| Audio | OPTIONAL v2: MAX98357A I²S £5.70 + speaker | driven from Pi, not MCU | — |

## 6. Interfaces & connectors

- SBC↔MCU: USB-CDC (Pi OTG ↔ Pico micro-USB) preferred; UART fallback; binary length-prefixed CRC frames.
- Debug: Pico SWD 3-pin, USB serial CLI (bus scan, VBAT, temp), Pi ssh over WiFi.
- Expansion: spare UART + I²C + 4 GPIO to a header (aux servos, topper pogo dock = 5V+I²C+2GPIO), SWD, test pads.
- Firmware update: MCU UF2/bootloader; SBC = A/B image swap.

## 7. Verification plan (feeds validation/test-plan.md §E)

Bench order: board-only rails → MCU+buffers loopback → single servo → full bus current-limited → battery. Worst-case current test sets the final fuse value. See `engineering/notes-electronics.md` §13 for the full DFT list.

## 8. Outstanding flags

1. Pi Zero 2 W stock is intermittent — buy early or qualify a second source.
2. 3.3 V→servo-TTL is community-proven but not datasheet-guaranteed → 5 V populate option retained.
3. Runtime figure is an estimate pending a real gait's current measurement.
4. ST3020 8.4 V no-load speed/torque curve unverified → P1.4 bench test.
5. If aux/head servos are added, they must be 6–14 V class (STS3032 7.4 V-max would overvolt on this rail) or on a regulated tap.
