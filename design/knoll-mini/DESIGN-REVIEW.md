# Knoll Mini — Design Review (v0 packaging)

## 1. The ask

Pocket-size version: 15–20 cm tall (vs Microduck's ~25 cm), full STL set with real slots for
every component, cheap servos welcome, eyes used functionally — "think like a Disney imagineer".

## 2. What got built

A fully parametric Blender model at **~192 mm tall**: same family architecture as Microduck —
5-DOF legs, static flipper shells, actuated neck, big head — but scaled-down around parts that
actually exist at this size, and 100% Knoll-generated geometry (no Pollen meshes — this is the
first fully-original geometry pass).

```
feet+ankle 30 mm → shin 28 → knee → femur 32 → hip 90 → trunk 40 → neck 22 → head 28 = ~192 mm
```

The squatness is deliberate: legs shorter relative to the body than Microduck's (whose legs are
long for its gait); at ~350 g the stability envelope benefits, and it reads more mascot/droid
than scaled-down-humanoid.

## 3. Servo selection — the constraint that sized everything

At 15–20 cm the leg needs ~0.2 N·m working torque at ~350 g mass. Options:

| Servo | N·m (rated/stall) | g | £ | Verdict |
|-------|-------------------|---|---|---------|
| Dynamixel XL330 | 0.4 / 1.0 | 18 | ~45 | Too expensive for "cheap" |
| Hiwonder LX-16A | — / 1.9 | 53 | 15 | Too big: legs would be servo towers |
| Feetech STS3215 | 0.5 / 1.9 | 55 | 16 | Fallback upgrade (frame accepts it) |
| **Feetech STS3032** | **0.15 / 0.44** | **20** | **~14** | **Chosen: smallest serial bus w/ feedback** |
| Feetech SCS0009 | 0.07 / 0.22 | 9 | 9 | Head servos (low load) |
| SG90-class analog | ~0.18 / — | 9 | 3 | Rejected: no position/temp/load feedback = no walking policy, no compliance, no recovery sensing |

Serial bus is the non-negotiable: daisy-chained wiring + full feedback is what makes a
Microduck-family robot *function*. The saving comes from the servo class, not the protocol.

**Flag #1 — knee margin:** 0.15 N·m rated is tight. Gait must stay bent-knee; if it stalls,
`SV_LEG` swaps to STS3215 and the whole frame re-sizes (parametric). This is the same honest
class of warning as the Mk1 knee breach — flagged, not hidden.

## 4. The eyes — Imagineer pass

BDX's eyes read as reflector lamps. So: each eye is a **light ring + sensor pod**:

- **L eye** → OV2640 camera (vision, tracking, "it looks at me")
- **R eye** → VL53L0X ToF (distance → approach detection → flinch/greeting triggers)
- Both rings → WS2812s → the eyes glow, blink, change color — expression is the light layer;
  the sensor looks through the ring's open center.

One cosmetic surface doing three jobs = how an 84 mm head stays 84 mm. Mic hole and speaker
grille dots ride the same face plate. Antenna stays thin wire (BDX-faithful).

## 5. Layout / packaging

- **Trunk (64×52×40):** battery floor → main PCB stack → IMU ceiling; chest service panel +
  vents on the front face; power button + USB slot on the rear.
- **Head (84×46×28):** face plate + eye rings/sensors on the front; `SLOT_HEAD_ELEC` interior
  tray for ring wiring + camera/ToF flex + mic.
- **Neck (22 mm):** pitch servo low, yaw servo high, both SCS0009, shared wiring column.
- **Flippers:** static shells with orange tips — recovery bumpers, same job as Microduck's
  (which were never actuated).
- **Feet:** 52×34 mm, ~27% of width each — wide footprint for the squat stance.

## 6. Cost

**≈ £250 all-in** (≈ £235 with MPU-6050 fallback IMU) vs ~£650+ for genuine-servo Microduck.
Breakdown + alternates in `BOM.md`.

## 7. What this is NOT yet (build-gate list)

- Mounting detail: the STLs are shells + proxies — screw bosses, insert pockets and bracket
  holes are marked by slots, not final-cut. Next pass adds real fastener geometry.
- Knee torque: rated 0.15 N·m vs ~0.2 N·m worst case — needs either the bent-gait assumption
  verified or the STS3215 swap.
- Recovery: flipper geometry gives the rounded contact shell; whether 12-DOF + 350 g self-rights
  like Microduck is a sim question, not yet answered.
- Fit-check: print the `parts/` set first as a mock-up before committing to a full build.

## 8. Decisions for the user

1. **2 neck DOF vs 4** — saved 2 servos + 40 g + £18; add back if head motion feels dead.
2. **STS3032 vs STS3215** — cheap+small now, or +£60 +50 g for real torque margin.
3. **Camera eye**: OV2640 (self-contained, cheap) vs Pi-camera (better image, needs Pi-class
   host — changes the whole compute story).
4. **BNO085 vs MPU-6050** — £8 buys real sensor fusion; the cheap path works but adds software risk.
