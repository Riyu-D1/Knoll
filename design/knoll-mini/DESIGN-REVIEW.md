# Knoll Mini — Design Review (v0 packaging)

## 1. The ask

Pocket-size version: 15–20 cm tall (vs Microduck's ~25 cm), full STL set with real slots for
every component, cheap servos welcome, eyes used functionally — "think like a Disney imagineer".

## 2. What got built

A fully parametric Blender model at **~162 mm tall**: same family architecture as Microduck —
5-DOF legs, static flipper shells, actuated neck, big head — but scaled-down around parts that
actually exist at this size, and 100% Knoll-generated geometry (no Pollen meshes — this is the
first fully-original geometry pass).

```
feet+ankle 22 mm → shin 22 → knee → femur 24 → hip 68 → trunk 34 → neck 25 → head 24 = ~162 mm
```

The big-head/small-body proportion is deliberate: at 16 cm the head *must* stay 68 mm wide to
house the eye sensor pods, and the oversized face is what makes it read as a mascot droid rather
than a scaled-down humanoid — same trick BDX uses.

## 3. Servo decision — config B locked

First pricing pass was wrong (STS3032 ≈ £20 street, not £14). Re-surveyed the real market —
see `BOM.md` for the full table and all four configs. Chosen:

**12× Feetech SCS0009 / Waveshare SC09 — ~£105 total.** Serial TTL bus, magnetic-encoder
feedback (position, load, temp, voltage) on every joint — the Microduck-class control path
stays open — at £8.75/servo. 13 g each keeps total mass ~250 g, which is what makes the
0.22 N·m stall torque adequate at 16 cm scale (knee worst case ~0.11 N·m).

Alternatives rejected: STS3032 (fits, but £200+ bill), LX-15D/SCS15 (cheap torque but 40 mm
servos force ~24 cm robot — violates the size constraint), MG90S analog (£36 but zero feedback
→ no compliance, no recovery sensing, no RL path — saves £70 by cutting the robot's purpose).

**Flag:** 0.07 N·m rated torque is the thin margin — gait must stay bent-knee, recovery will be
careful not athletic. Escape hatch: SCS0009 and STS3032 share a footprint within 3 mm, so the
4 load joints upgrade for +£40 without a frame redesign.

## 4. The eyes — Imagineer pass

BDX's eyes read as reflector lamps. So: each eye is a **light ring + sensor pod**:

- **L eye** → OV2640 camera (vision, tracking, "it looks at me")
- **R eye** → VL53L0X ToF (distance → approach detection → flinch/greeting triggers)
- Both rings → WS2812s → the eyes glow, blink, change color — expression is the light layer;
  the sensor looks through the ring's open center.

One cosmetic surface doing three jobs = how a 68 mm head carries vision + depth + mic hole +
speaker grille. Antenna stays thin wire (BDX-faithful).

## 5. Layout / packaging

- **Trunk (40 deep × 50 wide × 34):** battery floor → main PCB stack → IMU ceiling; chest service
  panel + vents front; power button + USB rear. Speaker behind the panel.
- **Head (68×38×24):** face plate + eye rings/sensors front; `SLOT_HEAD_ELEC` interior tray for
  ring wiring + camera/ToF flex + mic.
- **Neck (25 mm):** NPITCH horizontal in trunk ceiling; NYAW servo body *is* the exposed column —
  BDX-faithful visible mechanics; wiring channel behind.
- **Flippers:** static shells + orange tips — recovery bumpers, same job as Microduck's
  (which were never actuated).
- **Feet:** 44×28 mm at ±16.5 mm hips — ~5 mm clear stance.

## 6. Cost

**≈ £190 all-in** (≈ £180 with MPU-6050 fallback IMU) vs ~£650+ for genuine-servo Microduck.
Breakdown + rejected alternates in `BOM.md`.

## 7. What this is NOT yet (build-gate list)

- Mounting detail: the STLs are shells + proxies — screw bosses, insert pockets and bracket
  holes are marked by slots, not final-cut. Next pass adds real fastener geometry.
- Knee torque: 0.22 N·m stall vs ~0.11 N·m working — fine bent; marginal straight. Needs the
  gait assumption held in practice.
- Recovery: flipper bumpers + rounded head give the contact geometry; whether 12-DOF + 250 g
  self-rights like Microduck is a sim question, not yet answered.
- Fit-check: print the `parts/` set first as a mock-up before committing to a full build.

## 8. Decisions for the user

1. **2 neck DOF vs 4** — saved 2 servos + ~£17 + ~26 g; add back if head motion feels dead.
2. **BNO085 vs MPU-6050** — £8 buys real sensor fusion; cheap path adds software risk.
3. **Camera eye**: OV2640 (cheap, self-contained) vs Pi-camera (better image, changes the whole
   compute story to Pi-class).
4. **Speaker**: 16 mm behind chest panel vs moving it into the head (better voice direction,
   harder wiring).
