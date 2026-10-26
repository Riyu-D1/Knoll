# DESIGN-REVIEW — knoll-v1

## 1. What this is

The first Knoll derivative: Microduck's mechanical skeleton +
a Knoll-original BDX-style head + cheap-servo placeholders. Body is
still Pollen geometry; the head is parametric Knoll code you can
reshape freely.

## 2. The head — what was modeled

| Part | Notes |
|---|---|
| `HEAD_BAR` | BDX-style slab/"binocular bar": 122 D × 115 W × 42 H mm, z 230–272 — encloses all head internals |
| `FACE_PLATE` | dark front face inset, carries eyes + speaker grids |
| `EYE_L/R` + `EYE_RING_L/R` | reflector-lamp eyes (dark ring + warm glowing lens) |
| `SPK_L/R_*` | 2×3 perforated speaker dots flanking the eyes |
| `EAR_L/R` + caps | flush side pods at the bar ends |
| `ANT_MAST` | thin wire antenna, rear-left top |
| `NECK_SHROUD` + `NECK_COLLAR` | dark column trunk→bar — the visible BDX-style neck (z≈150–232) |
| `CHIN` | small ledge under the face plate |

Dropped Microduck cosmetics: top/bottom head shells, face_part, jaw,
jaw_soft, soft_mouth_top, noenoeil (the duck bill — the single most
distinctive Microduck feature — is gone, which helps originality).

**Space for components (verified in `img/internals.png`):** the bar
wraps the full stock electronics pod — M12 lens + holder, Pi Zero 2 W,
robot-hat PCB, speaker, motor support, 4 head servos — with the lower
dome volume (z≈197–231 mm) free for added parts: ToF/IMU board,
mic, extra battery, or the cheap-servo control board.

## 3. Cheap servo swap — the honest version

The proxy boxes are the **XL330 envelope** (20×34×26 mm, ~18 g each).
What's realistic at ~14 servos:

| Option | Price/ea | Mass | Size vs XL330 | Verdict |
|---|---|---|---|---|
| Dynamixel XL330-M288-T | £45–55 | 18 g | — | baseline (≈£700/set) |
| XL330 clones (various) | £10–18 | ~18–22 g | same envelope | **easiest swap** — brackets unchanged, protocol same; quality varies |
| Feetech STS3032 | £12–16 | ~22 g | longer (~48 mm) | leg mounts rework needed |
| Waveshare ST3215 | £12–14 | ~60 g | much bigger | too heavy for head; legs only |

**Best cheap path:** XL330-form-factor clones at ~£12–15 → ~£180–210/set
(saves ~£500 vs genuine). Legs can take STS3032-class later if knees
need margin — but head servos must stay light (head = ~19% of mass
already). Torque: XL330-M288 ~1.0 N·m; clones typically derate ~10–20% —
knee margin must be re-verified on the bench (same gate as the earlier
actuator study).

## 4. What stayed the same

Height ≤ 277 mm (no enlargement), 14 actuated joints, all joint axes/
ranges, leg geometry, trunk + flipper shells, feet/soles, battery +
trunk electronics. Recovery geometry preserved — legs + 4-DOF neck +
shell contact all unchanged.

## 5. Design decisions for review

1. **Head proportions** — the bar is deep (122 mm) because the internals
   PCB stack needs it; width 115 mm, height 42 mm. Could slim D a few mm
   if the internals are repacked.
2. **Eye style** — twin cyan discs now; BDX eyes are bigger/expressive —
   want larger eyes or an LED matrix look instead?
3. **Antenna** — keep single rear mast or drop it (snag risk in falls)?
4. **Ear pods** — keep (bumper look) or remove for cleaner silhouette?
5. **Accent color** — orange band vs Knoll's sage/moss palette?
6. **Bill removal is permanent?** — some beak/chin styling could return
   in Knoll's own language if you want a friendlier face.

## 6. Known gaps

- Head shell is a visual model: no wall thickness, mounts, or print
  split yet — internals placement comes from the reference, mounting
  bosses TBD.
- Servo proxies are envelope boxes, not real servo CAD.
- The dome→neck joint visual gap: the head pivots on head_roll at
  z≈236 mm; the dome floats above the thin neck like BDX's does, but a
  cosmetic neck shroud may be wanted.
- Disney BDX is trade dress — this head is *inspired*, already differs
  (dome proportions, visor shape, antenna, chin band); keep diverging
  before any public release.
