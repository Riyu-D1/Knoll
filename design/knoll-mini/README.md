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
| `build_knoll_mini.py` | Parametric generator — Blender 4.x headless, rebuilds renders + preview STLs |
| `knoll-mini.blend` | Editable model; collections `LEG_L/R`, `TRUNK`, `ARMS`, `NECK`, `HEAD`, `COMPONENTS`, `SLOTS`, `HARDWARE` |
| **`cad/`** | **Production CAD** — `build_kit.py` (FreeCAD parametric source) → `knoll-mini.FCStd` + `knoll-mini.step` + 76 solid STLs with real holes/fillets |
| `img/` | hero, front, side, rear, head-detail, servo-station, internals renders |
| `parts/` | 152 preview STLs from the Blender pass |
| `cad/parts/` | **76 production STLs** (use these) — pockets/collars as single fused solids |
| `BOM.md` | Component cost + servo config decision (~£185) |
| `DESIGN-REVIEW.md` | Architecture, torque budget, eye-sensor rationale, open risks |
| `ASSEMBLY.md` | Print settings, insert map, step-by-step build, QC checklist |
| `WIRING.md` | Servo daisy-chain, power tree, signal routes, strain relief |

## Rebuild

```bash
# production CAD (solid STLs + STEP + FCStd)
KNOLL_OUT=./cad freecadcmd cad/build_kit.py

# preview model + renders
blender --background --python build_knoll_mini.py -- --out .
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

## Assembly — no glue, all mechanical

Every part mounts with **M2 screws into M2 heat-set brass inserts** (~60 each):

- **Servos (all 12):** drop into printed pockets (0.6 mm clearance), a collar plate clamps the
  ear flange, 2× M2 screws into boss posts beside the pocket. Horn exits the open side.
- **Trunk:** `TRUNK_F` + `TRUNK_R` clamshell halves join on 6 seam inserts; chest panel on
  4 posts; battery sits in a tray with strap slots (velcro tie, not glued); PCB on 4 standoff
  posts; IMU on 2 posts; speaker press-fits a ring behind the panel.
- **Head:** `HEAD_SHELL` + `HEAD_BASE` screw together at 4 corners; base plate has the NYAW
  horn bore + cable slot; `FACE_PLATE` screws on at 4 corners with real bored eye apertures;
  camera/ToF pods sit in printed brackets; eye bezels press-fit the bores.
- **Neck:** NYAW servo is the exposed column, clamped top/bottom by collar rings into inserts.
- **Feet:** sole plate screws up into the foot frame from below (4× M2).
- **Flippers:** 2× M2 each into trunk-side inserts.

All fasteners/inserts are modeled as objects in the `HARDWARE` collection (hidden in beauty
renders, shown in `servo-station.png`). `parts/` holds 152 STLs — the full printable kit.

## Honest status

**v1 build-ready geometry** — every component has a real mount now; no glue anywhere. Still
unverified: knee torque margin (BOM.md), self-recovery in sim, and real-world tolerances.
**Next step: print the servo-station parts (one pocket+collar) for a fit check before printing
the whole kit.**
