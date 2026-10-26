# Knoll Mini — Wiring Map

Single TTL daisy-chain (half-duplex, 1 Mbps). One bus, 12 servos, ID-assigned
before power-on. All wires exit pocket back-slots and run inside the frame —
never across a joint pinch zone.

## Servo chain

```
ESP32-S3 ──► BUS HUB
  ├─► L leg: HYAW_L(1) → HROLL_L(2) → HPITCH_L(3) → KNEE_L(4) → ANKLE_L(5)
  ├─► R leg: HYAW_R(6) → HROLL_R(7) → HPITCH_R(8) → KNEE_R(9) → ANKLE_R(10)
  └─► neck:  NPITCH(11) → NYAW(12)
```

IDs in parentheses — assign with the hub tool before chaining.

## Power

```
2S LiPo ──► switch ──► 6V buck (SET TO 6.0V FIRST) ──► servo rail (bus hub power in)
                    └─► ESP32 5V pin (separate tap or same rail via onboard reg)
```

SCS0009 spec is 4–7.4 V — the buck protects them from the 8.4 V of a charged 2S.
**Never run the servo rail off unregulated 2S.**

## Signal runs

| Signal | From | To | Route |
|--------|------|----|-------|
| Servo bus (3-wire TTL) | hub | all servos | exits pocket back-slot → up leg pockets → trunk |
| I2C (SDA/SCL) | ESP32 | BNO085 + VL53L0X | IMU rides trunk ceiling; ToF flex through `NECK_CABLE` + `HEAD_BASE` slot |
| Camera FPC | ESP32 (or dedicated ESP32-CAM variant) | OV2640 (L eye) | same neck channel, lands in `SLOT_HEAD_ELEC` |
| WS2812 (1-wire) | ESP32 GPIO | both eye rings | daisy-chained rings, data in→out |
| I2S audio | ESP32 | MAX98357 | amp sits beside speaker in trunk |
| Mic (I2S, opt) | INMP441 | ESP32 | mic hole on face plate, taped behind |

## Head pass-through

All head wiring funnels through the **neck cable channel** (`NECK_CABLE` part,
behind the NYAW column) and enters the head via the **`HEAD_BASE` cable slot**
(5×6 mm). Leave 20 mm service loop inside the head so the face plate can come
off without unplugging.

## Strain relief

- Servo wires: zip-tie to the pocket floor before the back-slot exit (the wire
  takes the joint flex cycles, not the connector).
- Head flexes: tape flat-flex to the inside of `HEAD_SHELL` top — never let
  the camera FPC ride against the NYAW horn.
