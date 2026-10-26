# Knoll Mini — Wiring Map

Single TTL daisy-chain (half-duplex, 1 Mbps). One bus, **9 servos**, ID-assigned
before power-on. Wires exit pocket back-slots and run inside the frame — never
across a joint pinch zone.

## Servo chain

```
ESP32-S3 ──► BUS HUB
  ├─► L leg: HYAW_L(1) → HPITCH_L(2) → HROLL_L(3) → KNEE_L(4)
  ├─► R leg: HYAW_R(5) → HPITCH_R(6) → HROLL_R(7) → KNEE_R(8)
  └─► neck:  NPITCH(9)
```

IDs in parentheses — assign with the hub tool before chaining. HYAW/HPITCH sit
in the rear column (x ≈ −16), HROLL/KNEE in the front column (x ≈ 20); each
leg's wires rise through the two trunk-floor openings at those x positions.

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
| Servo bus (3-wire TTL) | hub | all 9 servos | pocket back-slots → floor openings → trunk |
| I2C (SDA/SCL) | ESP32 | BNO085 + VL53L0X | IMU on trunk posts; ToF up the neck bore |
| Camera FPC | ESP32 | OV2640 (L eye) | same neck bore → `HEAD_BASE` slot |
| WS2812 (1-wire) | ESP32 GPIO | both eye rings | daisy-chained rings, data in→out |
| I2S audio | ESP32 | MAX98357 | amp beside the speaker ring in trunk |
| Mic (I2S, opt) | INMP441 | ESP32 | mic hole on face plate, taped behind |

## Head pass-through

All head wiring funnels through the **hollow neck column** (Ø5 bore through
`NCOL_0`/`NCOL_1`) and enters the head via the **`HEAD_BASE` cable slot**
(6×7 mm). Leave a 20 mm service loop inside the head so the face plate can
come off without unplugging.

## Strain relief

- Servo wires: zip-tie to the pocket floor before the back-slot exit — the wire
  takes joint flex cycles, not the connector.
- Head flexes: tape flat-flex to the inside of `HEAD_SHELL` top; keep clear of
  the NPITCH horn sweep (neck pitch servo lives in the trunk-top pocket).
- Battery: velcro strap through the tray wall slots — connector toward the rear
  so it unplugs through the clamshell seam when open.
