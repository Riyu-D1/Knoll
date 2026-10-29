# Handoff — Refinement C: trunk / neck / body shells (branch `refine-trunk`)

Refinement C replaces the blocky prototype trunk dressing (`left_shell`,
`right_shell`, `banana_pcb_locker`) with designed enclosure parts while leaving
every functional part, servo seat, joint axis, and range untouched.

## What changed

New generated parts (all in `mini/parts/current/`, authored by
`mini/tools/make_trunk.py`, build123d solids):

| part | body | what it is |
|---|---|---|
| `trunk_shell` | trunk_base | panelled enclosure: thin raised deck + side/rear/front walls, asymmetric neck port scooped through the right of the deck and wall top, engraved trim groove ring around the port, rear hatch aperture with sill, left flank aperture, right flank vent grille, open hip bay below a z≈89.5 beltline |
| `trunk_cover_left` | trunk_base | flush left access panel: recessed plate, screw dimples, grille patch |
| `trunk_cover_rear` | trunk_base | rear battery fairing/pod with stepped top (rear section z112.5, front z118), battery slide opening (top z110), side vent slots, rear grille, screw dimples |
| `elec_battery_2s_450`, `elec_ubec_6v_5a`, `elec_bno085`, `elec_bus_hub_and_wiring` | trunk_base | electronics placeholders in the rear bay (in `spec.ELECTRONICS`, ignored by printability, counted for mass/clearance) |

Archived to `parts/attic_refine/`: `left_shell`, `right_shell`,
`banana_pcb_locker` (added to `spec.REMOVED_PARTS`).

### Design decisions worth knowing

- **Open bottom**: the shell is a panel enclosure above a z≈89.5 beltline; the
  hip servos and leg mechanisms stay exposed below, matching the original look.
- **Battery lives out back**: the interior is full of hip-yaw servos (only a
  ~7 mm center channel was free), so the battery sits in the rear pod — same
  as the original NP-F970 rear-mount concept.
- **Stepped deck**: the raised lid (117.5–121) covers only the front of the
  trunk. Behind it the deck is **terraced by a heightfield relief cut**: at
  `head_pitch = -45°` the head's bottom shell sweeps the rear deck down to
  ~z117, so every deck column the corridor dips into is clipped to
  floor−1.2 mm (1.2 mm triangle-rastered heightfield, `hfloor()` in
  make_trunk.py). This is what makes the sweep pass — the original design had
  no raised lid there at all (chassis top plate is at z117).
- **No raised neck bezel**: tried twice (tall collar → shredded by the neck
  corridor; low bezel ring → clipped into fragments by the head_pitch
  corridor). The port gets an engraved 0.55 mm trim groove instead — a void
  cannot collide. `neck_shroud` was removed from `EXTRA_PARTS`/`COSMETIC_PARTS`
  and its STL deleted.
- **Stepped pod top**: at `neck_pitch = +45°` the head's bottom corner grazes
  the pod's rear-top edge, so the pod rear section (x < −32.5) is lowered to
  z112.5; front stays z118.
- **Electronics**: explicit placeholder boxes in the rear bay; generator
  reports `in-shell=0`, `in-pod=0`, min distance to statics ≥1.1 mm.

## Verification — all run on `refine-trunk`, real output

- `check_parts.py --only trunk_shell,trunk_cover_left,trunk_cover_rear` →
  **PASS** (watertight; wall_p10 = 2.00 / 2.10 / 1.79 mm)
- `check_clearance.py` → **C1 PASS** (14 servos on-axis), **C2 PASS**,
  **C3 PASS**, **C4 PASS** (height 195.2 < 200 mm)
- `sweep_check.py` per joint → **R1 PASS on all 14 joints**
  (`left/right hip_yaw/roll/pitch, knees, ankles ±45; neck_pitch, head_pitch
  ±45; head_yaw ±120; head_roll ±25`)
- `build_mjcf.py` → wrote `model/knoll_mini.xml` + `scene_knoll_mini.xml`;
  `mujoco.MjModel.from_xml_path` loads OK (16 bodies, 15 joints, 76 geoms);
  trunk z0 = 0.0797 m; total mass 441.5 g
- `torque_check.py` → **PASS**: stood=PASS, 0 joints over 0.069 N·m rated
- Renders in `renders/solid/trunk_after/` were inspected visually:
  stepped deck, engraved port groove, rear pod, left cover, no floating or
  shredded geometry; `head_pitch_neg45_right.png` shows the head skirt
  clearing the terraced deck.

## Known issues / baseline state (pre-existing, NOT introduced here)

- `check_parts.py` (full run) still reports thin-wall FAILs on untouched
  original parts (`upper_leg_left/right`, `leg`, ankle/sole parts,
  `power_support`, etc.) — same failures exist on the base commit.
- `sweep_check.py --joint head_pitch` on the base commit → PASS (verified in a
  temp worktree); the regression found mid-work was mine (raised deck) and is
  fixed by the terraced relief.
- Fillets on the pod's top/bottom edges and the shell's vertical edges are
  wrapped in `try/except` — OCCT rejects them on the stepped geometry; the
  solids remain watertight and printable without them.

## How to regenerate

```bash
~/Knoll-cad-venv/bin/python tools/make_trunk.py   # build123d venv
.venv/bin/python tools/check_parts.py --only trunk_shell,trunk_cover_left,trunk_cover_rear
.venv/bin/python tools/check_clearance.py
.venv/bin/python -u tools/sweep_check.py --joint <name>   # per-joint is fast enough
.venv/bin/python tools/build_mjcf.py && .venv/bin/python tools/torque_check.py
```
