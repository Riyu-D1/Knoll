# Knoll v1 — BDX-style head on the Microduck skeleton

First real **Knoll derivative**: the faithful Microduck mechanical core
(legs, trunk, neck, all electronics layout) with the cosmetic head
replaced by a **new, original head shell** inspired by Disney's BDX
droid family (slab "binocular bar" + dark face plate + lamp eyes + speaker grids + wire antenna + ear pods + visible neck column),
and cheap-servo proxies standing in for the XL330s.

Head geometry is Knoll-original parametric code (`build_knoll_v1.py`),
not copied Disney/Pollen meshes. The body/legs/internal parts remain
© Pollen Robotics (Apache-2.0 files — see
`../microduck-reference-v0/THIRD-PARTY-NOTICES.md`); BDX trade dress
stays Disney's — this is a study/derivative baseline.

## Files

| File | Contents |
|---|---|
| `build_knoll_v1.py` | Full parametric build (Blender ≥4.5 headless) |
| `knoll-v1.blend` | Editable scene — `BODY`, `HEAD_INTERNALS`, `HEAD_SHELL`, `SERVO_PROXY`, `JOINTS` collections |
| `img/` | hero-3q, front, side, rear, head-detail, **internals** (shell hidden — shows component space) |
| `parts/*.stl` | head-shell pieces (bar, face plate, eyes+rings, speakers, ears+caps, antenna, neck shroud/collar, chin) for CAD handoff |

## Rebuild

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/pollen-robotics/microduck_rl.git /tmp/microduck_rl
cd /tmp/microduck_rl && git sparse-checkout set --skip-checks \
  src/mjlab_microduck/robot/microduck
blender --background --python build_knoll_v1.py -- \
  --md-dir /tmp/microduck_rl/src/mjlab_microduck/robot/microduck --out .
```

## What changed vs the reference

- **Head**: 7 cosmetic Microduck meshes removed (`top/bottom_head_shell`,
  `face_part`, `jaw`, `jaw_soft`, `soft_mouth_top`, `noenoeil`) → 12
  parametric Knoll parts. Dome 90 W × 120 D × 75 H mm sits z=197–272 mm —
  overall height still ≤ 277 mm (not enlarged).
- **Internals kept**: lens + M12 holder, Pi Zero 2 W + robot-hat PCB,
  speaker, motor support, both head servos — all inside the new dome
  (see `img/internals.png`).
- **Servos**: 14 `xl330` placements → `SERVO_*` proxy boxes at the
  XL330 envelope (20×34×26 mm). See DESIGN-REVIEW for real cheap-servo
  options and the size/mass trade-offs — the swap is NOT free.
