"""Cut an SCS0009 pocket into a printed part (and optionally add a cradle first).
Usage:
  python tools/pocket_part.py --joint left_hip_yaw --part trunk_base [--instance 0] [--cradle] [--dry-run]
What it does (all in the PART's own mesh frame, so the MJCF placement stays valid):
  1. finds the SCS0009 placed for --joint (assembly.build(), uses spec.S/STRETCH/SERVO_ROLL_DEG)
  2. finds the --part instance (same body as the servo, or any body if --any-body), index --instance
  3. if --cradle: part = part UNION scs0009.cradle_mesh  (2 mm wall sleeve, open on the horn side)
  4. part = part MINUS scs0009.cutter_mesh (case+ears+0.3 mm clearance, cable exit, 2x M2 pilot holes)
  5. checks the result is watertight, writes parts/current/<part>.stl, prints volume before/after.
Parts used twice (yaw2roll, hip_l, leg, neck, bearing_roll, upper_leg_rigidity_plate) share ONE STL:
only run this with the LEFT joint, then run check_clearance.py, which tests both sides."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
import spec, scs0009
from assembly import build

ap = argparse.ArgumentParser()
ap.add_argument("--joint", required=True); ap.add_argument("--part", required=True)
ap.add_argument("--instance", type=int, default=0); ap.add_argument("--cradle", action="store_true")
ap.add_argument("--any-body", action="store_true"); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
items = build()
sv = [i for i in items if i.kind == "servo" and i.mesh == f"scs0009:{a.joint}"]
assert sv, f"no servo for joint {a.joint}"
sv = sv[0]
cands = [i for i in items if i.mesh == a.part and (a.any_body or i.body == sv.body)]
assert cands, f"part {a.part} not found in body {sv.body} (use --any-body if intended)"
pt = cands[a.instance]
to_local = np.linalg.inv(pt.T) @ sv.T            # servo frame -> part-local frame
path = spec.WORK_DIR / f"{a.part}.stl"
part = trimesh.load(path, force="mesh"); v0 = part.volume
if a.cradle:
    cr = scs0009.cradle_mesh().copy(); cr.apply_transform(to_local)
    part = trimesh.boolean.union([part, cr], engine="manifold")
cut = scs0009.cutter_mesh().copy(); cut.apply_transform(to_local)
part = trimesh.boolean.difference([part, cut], engine="manifold")
print(f"{a.part}: volume {v0/1000:.2f} -> {part.volume/1000:.2f} cm3, watertight={part.is_watertight}, bodies={len(part.split(only_watertight=False))}")
assert part.is_watertight, "result not watertight - do NOT save; report in HANDOFF.md"
if len(part.split(only_watertight=False)) > 1:
    print("WARNING: result has more than one disconnected body (the cut split the part, or the cradle does not touch it). Do NOT save as-is: use --cradle or add a bridge (SPEC.md 5.4).")
if not a.dry_run:
    part.export(path); print("wrote", path)
