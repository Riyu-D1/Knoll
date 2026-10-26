# DESIGN-REVIEW — microduck-reference-v0

## 1. What was built and why

Per your direction, this is **the actual Microduck**, reconstructed
part-for-part from the official MJCF export (`robot_walk.xml`,
generated from the real Onshape CAD via onshape-to-robot). No
interpretation: every part's position, rotation, joint location, axis and
range comes straight out of the file the trained policies run against.
This is the baseline you asked to alter from — the previous droid-v0 and
shell-v0 concepts are superseded for mechanical design (still on
`design/knoll-shell-v0` for history).

## 2. What the model actually is — corrected facts

Reading the assembly directly overturns two assumptions we had carried:

- **14 actuated joints, not 15.** Legs: 5 each — `hip_yaw, hip_roll,
  hip_pitch, knee, ankle` (ranges: yaw ±25–30°, roll ±22°,
  pitch/knee/ankle ±90°). Head: 4 — `neck_pitch` (−90°..+60°),
  `head_pitch` (±90°), `head_yaw` (±170°), `head_roll` (±25°).
- **There are no actuated arms.** The "hands" are `left_shell` /
  `right_shell` — fixed flipper-shells attached to `trunk_base`. The
  earlier "15th servo = beak" is a jaw shell set (`jaw`, `jaw_soft`,
  `soft_mouth_top`, `noenoeil`) — static in this export; the mouth is
  cosmetic, possibly servo'd in the retail unit, not in this model.
- **Recovery is legs + head + shell**, not arms. Self-righting uses the
  legs and the 4-DOF neck to push/roll against the floor plus the
  rounded shell surfaces as contact geometry. That *is* how Microduck
  gets up — worth internalizing before redesigning.

## 3. Measured architecture (from the assembled model)

- ~0.25 m tall standing; ankle joint at z≈38 mm; hip pitch plane z≈102 mm;
  head top ≈0.25 m. Trunk root at z=0.12 m.
- 70 part placements from 38 unique meshes (see `parts-manifest.csv`).
- Head is dense: M12 camera lens + holder, ToF site, head IMU site,
  Raspberry Pi Zero 2 W + robot-hat PCB, speaker, motor-support — the
  head *is* the compute pod, consistent with the earlier finding that
  the head carries a large share of mass (inertial ~0.19 kg).
- Trunk: `np_f970` mount (Sony NP-F battery), power support, banana PCB
  locker, bearings, the fixed flipper shells.
- Legs: XL330 × 5 per leg in a yaw→roll→pitch→knee→ankle chain with
  bearing supports (`seeed_bearing` rings), `upper_leg_rigidity_plate`
  braces, `sole_*` under `foot_*`.

## 4. Fidelity vs. claims

**Exact (from file):** part placement/orientation, joint positions/axes/
ranges, part names, mesh geometry, official colors, overall mass
distribution (inertials in XML).
**Not validated:** physical tolerances, fasteners (absent from export —
Onshape mates only), wiring, the real unit's cosmetic shell finish
(matte vs. this smooth), any parts the walk model omits (e.g. possible
beak servo in retail units — check `robot_allcollisions*.xml` variants
if needed).

## 5. Recovery-relevant geometry (what to preserve when altering)

- Rounded head top + head-roll joint → head-as-prop during get-up.
- Wide, flat, low feet (sole parts) — stable contact patches.
- Leg chain reaches well below/behind trunk — ±90° pitch/knee/ankle.
- Flipper shells double as side-impact bumpers.
- Compact trunk, high-mounted battery (`np_f970`) — mass sits ~z≈0.11,
  head adds the rest; get-up policies rely on that mass layout.
- Nothing fragile protrudes past the shell envelope.

## 6. Alteration roadmap — how Knoll diverges from here

Suggested order (each step keeps the file buildable):

1. **Shell language** — restyle `left/right_shell`, `top/bottom_head_shell`,
   `trunk_base` covers, `face_part`/`jaw*` (this is where the identity
   lives; also the most legally sensitive — change silhouette, not just color).
2. **Proportions** — head size vs. body, leg length, foot shape; keep
   joint axes within ±few mm of the reference initially or every trained
   behavior assumption shifts.
3. **Feet/soles** — tread, toe/heel shape; affects standing + get-up directly.
4. **Servo/electronics swap** — XL330→cheaper class only after knee-torque
   re-check at the real mass (inertials are in the XML — reuse them).
5. **New parts** — rename to Knoll naming, re-derive inertials, re-export MJCF.

## 7. Decisions for your review

- Is this the Microduck you meant (the RL/HF biped — ~25 cm)? It matches
  the Pollen/HF Microduck product, not a larger Reachy derivative.
- Do you want the **beak actuated** in Knoll (retail units appear to move
  it; this export leaves it static)?
- Keep the **cyclops single-lens face** or is that too signature to keep
  even restyled? (High trade-dress risk — recommend changing.)
- Arms: keep static flipper-shells (faithful, cheaper, proven) or pay
  +4 servos for actuated ones — the earlier mass/torque trade still applies.

## 8. Quality gates checked

✓ all 38 unique meshes imported, 70 instances placed — zero missing
✓ joint count/locations/ranges match the MJCF exactly (dof-map.png)
✓ proportions ~25 cm confirmed against XML geometry
✓ renders real (Eevee, Blender 4.5 headless), consistent scale across views
✓ every part individually selectable/editable in the .blend
✗ not a physical/sim validation — geometry only
