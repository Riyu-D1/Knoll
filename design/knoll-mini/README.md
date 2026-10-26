# Knoll Mini — ~16 cm pocket BDX-style biped

The compact, buildable derivative: Microduck's architecture (5-DOF legs, static flipper shells,
actuated neck) shrunk to pocket size around **cheap serial-bus servos**, with a Disney BDX-style
slab head whose two lamp-eyes double as the robot's sensors.

- **Height:** ~162 mm (target window 150–200 mm) · **est. mass** ~250 g · **est. BOM** ≈ £200
- **DOF:** 12 — 10 leg (5/side) + 2 neck (pitch, yaw) — all SCS0009/SC09 serial servos (~£105)
- **Eyes:** left = OV2640 camera, right = VL53L0X ToF, each behind a WS2812 ring so they still glow

![hero](img/hero-3q.png)
![front](img/front.png)
![internals](img/internals.png)

## What's here

| Path | Contents |
|------|----------|
| `build_knoll_mini.py` | Fully parametric generator — Blender 4.x headless, one command rebuilds everything |
| `knoll-mini.blend` | Editable model; collections `LEG_L/R`, `TRUNK`, `ARMS`, `NECK`, `HEAD`, `COMPONENTS`, `SLOTS` |
| `img/` | hero, front, side, rear, head-detail, internals renders |
| `parts/` | 108 STLs — every printed part + servo proxies, ready for a slicer/mock build |
| `BOM.md` | Component-by-component cost (~£250) + the engineering trade-offs |
| `DESIGN-REVIEW.md` | Architecture, torque/mass budget, eye-sensor rationale, open risks |

## Rebuild

```bash
blender --background --python build_knoll_mini.py -- --out .        # full
blender --background --python build_knoll_mini.py -- --out . --quick  # hero only
```

Every dimension is a named constant at the top of the script (`SV_LEG`, `FEMUR`, `TRUNK`,
`HEAD_W`…). Change the servo constant and the whole frame re-fits itself.

## Component map (slots)

The `SLOTS` collection holds translucent envelopes showing exactly where each part sits;
`COMPONENTS` holds the parts themselves:

- **Trunk (40×50×34):** 2S LiPo (bottom) → ESP32-S3 + bus hub + buck (mid stack) → BNO085 IMU (top) → 16 mm speaker (behind chest panel); power button + USB port on rear
- **Head (68×38×24):** camera pod (behind left eye), ToF pod (behind right eye), 2× WS2812 rings, `SLOT_HEAD_ELEC` tray for the flex/mic run
- **Neck:** NPITCH horizontal in the trunk ceiling + NYAW as the exposed column (BDX-faithful visible mechanics) + wiring channel
- **Legs:** 5× SCS0009 per side — yaw under trunk floor, roll at trunk corner, pitch/knee/ankle stacked; feet clear by ~5 mm

## Honest status

This is **v0 packaging, not a verified build**: parts have real slots/envelopes but mounting
holes/insert bosses aren't detailed yet, and the knee torque margin is tight (see BOM.md). The
STL set is right for a **mock-up print + fit check** — which is the next step before committing
to a print-all.
