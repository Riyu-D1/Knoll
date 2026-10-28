# Knoll Mini — wiring (Session 6)

Power and signal plan for the 14-servo SCS bus, XIAO ESP32-S3 Sense,
BNO085, VL53L0X, eye rings and audio. Everything shares **one common GND**
— battery GND, UBEC GND, head-buck GND and XIAO GND are tied together.
**Set both regulators and check them with a multimeter unloaded before
plugging anything in.**

Layout follows the model: all five electronics placeholders
(`elec_xiao_esp32s3_sense`, `elec_buck_5v`, `elec_eye_rings_x2`,
`elec_max98357_speaker`, `elec_vl53l0x`) sit **in the head**. The trunk
holds the battery, fuse, switch, UBEC and the bus hub.

## Diagram

```
  TRUNK                                              HEAD
  2S 7.4V LiPo (450mAh, >=30C)                        neck cable: 6V, GND, BUS, SDA, SCL
        |  XT30                                       ==================================
        +--[5A blade fuse at the pack]--[switch]--UBEC 6V 5A (servo rail)
                              |   |                        |    |              |
                              |   +---- 6V GND BUS up -----+----+-+            |
                              |   |     the neck           |    | buck 5V      | SDA/SCL
                     hub 6V GND DATA                       |    | (in head)    | down to
                     to L-leg chain 1,3,5,7,9          head servo          BNO085 (trunk)
                     to R-leg chain 2,4,6,8,10         chain 11-14            |
                              |                            |    |             |
                              +------------ DATA ----------+    +--5V--+      |
                                    (one TTL net)               XIAO   |      |
                                                                ESP32-S3    I2C bus
                                                                Sense   (BNO085 0x28 +
                                                                |      VL53L0X 0x29)
                                         74LVC1G125+126 buffer--+
                                         <- D6/D7 UART + D3 DIR

  In the head: XIAO 5V pin <- head buck (fed 6V via neck); 3V3 -> VL53L0X,
  74LVC pair; WS2812 ring x2 on buck 5V (330R in DIN, 1000uF across 5V/GND);
  I2S -> MAX98357A -> 8 ohm speaker; SDA/SCL <- neck pair -> BNO085 in trunk.
```

## Servo bus

- Feetech SCS half-duplex TTL, 1 Mbit/s, 5264-3 pin connectors
  (GND / DATA / V+ 6 V). One DATA net serves all 14 servos.
- The trunk hub splits the 6 V rail and DATA into three branches:
  **L leg** (IDs 1, 3, 5, 7, 9), **R leg** (IDs 2, 4, 6, 8, 10), and the
  **neck cable** up to the head servos (IDs 11–14). Bus GND and 6 V ride
  every 5264 cable — no signal-only jumpers.
- The XIAO sits in the head; its UART is full-duplex 3.3 V while the bus
  is half-duplex ~5 V TTL. Bridge them in the head with a
  74LVC1G125 + 74LVC1G126 pair powered from the XIAO 3V3 pin (74LVC
  inputs are 5 V-tolerant; its 3.3 V high meets TTL VIH — **verify level
  compatibility on a bench before the full bus is attached [U]**):
  - `D6/TX (GPIO43)` -> 74LVC1G126 A; 74LVC1G126 Y -> DATA (the BUS
    conductor down the neck to the hub).
  - DATA -> 74LVC1G125 A; 74LVC1G125 Y -> `D7/RX (GPIO44)`.
  - `D3` (GPIO4) = DIR: high = transmit via the '126 (OE active high),
    low = receive via the '125 (/OE active low). Or use an SCS UART
    library that owns a DIR pin.

## XIAO ESP32-S3 Sense pin map

From the Seeed wiki pinout — https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/ (opened 2026-10-28):

| XIAO pad | GPIO | Knoll Mini use |
|---|---|---|
| 5V | — | power in from the head 5 V buck (USB while bench-testing) |
| GND | — | common ground |
| 3V3 | — | 3.3 V out -> VL53L0X, 74LVC pair (BNO085 via neck pair) |
| D0 | GPIO1 | WS2812 DIN (through 330 Ω) [U] |
| D1 | GPIO2 | spare [U] |
| D2 | GPIO3 | spare [U] |
| D3 | GPIO4 | bus DIR [U] |
| D4/SDA | GPIO5 | I2C SDA -> VL53L0X (0x29) + BNO085 (0x28, via neck) |
| D5/SCL | GPIO6 | I2C SCL |
| D6/TX | GPIO43 | UART TX -> 74LVC1G126 -> servo DATA |
| D7/RX | GPIO44 | UART RX <- 74LVC1G125 <- servo DATA |
| D8/SCK | GPIO7 | I2S BCK -> MAX98357A [U] |
| D9/MISO | GPIO8 | I2S LRC/WS -> MAX98357A [U] |
| D10/MOSI | GPIO9 | I2S DIN -> MAX98357A [U] |
| D11 | GPIO42 | **reserved** — Sense onboard digital mic CLK |
| D12 | GPIO41 | **reserved** — Sense onboard digital mic DATA |

Notes:

- D11/D12 are **not** free on the Sense: the camera-board's onboard
  microphone sits on GPIO42/GPIO41. The I2S pins above (D8–D10) are the
  first three free pads; treat the exact I2S assignment as **[U]** until
  the firmware pin table is written — the XIAO I2S peripheral can be
  routed to any free GPIO.
- MAX98357A: VIN 5 V, GND, BCK, LRC, DIN; speaker on its +/- output;
  gain pin floating (9 dB) to start.
- WS2812 rings: 5 V and GND from the head buck, 330 Ω in series with
  DIN, 1000 µF across 5 V/GND at the first ring. Daisy-chain
  DOUT -> DIN, or common DIN for identical eyes.
- BNO085 (trunk) and VL53L0X (head) share the one I2C bus at 3.3 V
  (0x28 / 0x29 — no address conflict); the SDA/SCL pair rides the neck
  cable. Breakouts carry their own pull-ups [U].
- **Head buck headroom [U]:** a buck typically wants ~1–1.5 V of
  headroom; 6 V -> 5 V is tight. If the head 5 V rail sags under LED
  load, re-feed the head buck from the fused battery side (pre-UBEC)
  instead of the 6 V rail — measure it under load in step 9.

## Neck/head cable bundle

Through `neck_frame` into the head — five conductors, per the model:

| conductor | gauge | notes |
|---|---|---|
| 6 V servo rail | 22 AWG silicone | up: feeds head servos 11–14 and the head buck |
| GND | 22 AWG silicone | common ground |
| BUS DATA | 26 AWG | SCS net: head buffer -> trunk hub; head chain taps it |
| I2C SDA | 26 AWG | head XIAO -> BNO085 in trunk |
| I2C SCL | 26 AWG | head XIAO -> BNO085 in trunk |

Leave a **>=60 mm service loop** at the head_yaw axis so the head can
still turn ~±150° without straining the bundle (per SPEC). Keep the loop
behind `motor_support`, clear of the head_roll/head_yaw horns.

## Servo ID assignment (SPEC §6 joint order)

Set IDs with the **FE-URT-1** and Feetech FD/URT software **one servo at
a time, before assembly**; also write centre = 150° (of the 300° range)
on each servo before its horn goes on.

| ID | Joint (SPEC §6) | STL / location |
|---|---|---|
| 1 | left_hip_yaw | `trunk_base` pocket, left |
| 2 | right_hip_yaw | `trunk_base` pocket, right |
| 3 | left_hip_roll | `yaw2roll` cradle |
| 4 | right_hip_roll | `bearing_roll` cradle |
| 5 | left_hip_pitch | `upper_leg_left` |
| 6 | right_hip_pitch | `upper_leg_right` |
| 7 | left_knee | `upper_leg_left` |
| 8 | right_knee | `upper_leg_right` |
| 9 | left_ankle | `leg` cradle (left) |
| 10 | right_ankle | `leg` cradle (right) |
| 11 | neck_pitch | `neck_frame` |
| 12 | head_pitch | `neck_frame` |
| 13 | head_yaw | `yaw_roll_motion` |
| 14 | head_roll | `motor_support` area |

> Firmware note: the upstream Microduck policy orders actuators
> differently — ctrl 0–4 = left leg (hip_yaw, hip_roll, hip_pitch, knee,
> ankle), 5–8 = neck/head (neck_pitch, head_pitch, head_yaw, head_roll),
> 9–13 = right leg. So the ctrl->ID map is
> `0->1, 1->3, 2->5, 3->7, 4->9, 5->11, 6->12, 7->13, 8->14,
> 9->2, 10->4, 11->6, 12->8, 13->10`. Keep that table in the firmware.

## Bring-up order

1. UBEC jumper at 6 V, head buck at 5 V — measure both unloaded.
2. Battery -> fuse -> switch -> UBEC only; buzz out rail voltages.
3. One servo at a time on FE-URT-1: set ID, set 1 Mbit/s, centre 150°.
4. XIAO on the head 5 V rail; flash a bus scan; expect 14 unique IDs.
5. Then IMU/ToF on I2C scan (0x28, 0x29), rings, amp last.

---

```
Original design and STL: Pollen Robotics / Microduck.
STEP reconstruction, repairs, validation and CAD sheets: tianjin66 and project contributors.
Source: https://github.com/tianjin66/microduck-step-3d-models-ai-stl
Licence: CC BY-NC-SA 4.0 — https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: uniformly scaled by 0.72; servo pockets/cradles re-cut for Feetech SCS0009; local stretches
(see SPEC.md 5.3); bearing seats changed to 6700ZZ; head shells swept-relieved internally for the
SCS0009 neck cradle (Session 3's BDX head rejected; outside shape unchanged).
```
