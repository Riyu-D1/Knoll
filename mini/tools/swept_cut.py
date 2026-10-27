"""Clearance cut: remove from a part every place a servo envelope (grown by --grow mm) passes through
while --move-joint sweeps --from..--to degrees. Use it when a servo hits a part of ANOTHER body
(e.g. hip_roll servo vs power_support). Works in the part's own mesh frame.
Usage: python tools/swept_cut.py --servo left_hip_roll --part power_support --move-joint left_hip_roll \
         --from -22 --to 22 [--grow 1.0] [--instance 0] [--dry-run]
Omit --move-joint to cut only at zero pose.
--servo part:<name> cuts with the convex hull of another part instead of a servo (e.g. neck parts vs a head shell)."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
import spec, scs0009
from assembly import build
ap = argparse.ArgumentParser()
ap.add_argument("--servo", required=True); ap.add_argument("--part", required=True)
ap.add_argument("--move-joint"); ap.add_argument("--from", dest="lo", type=float, default=0); ap.add_argument("--to", dest="hi", type=float, default=0)
ap.add_argument("--grow", type=float, default=1.0); ap.add_argument("--instance", type=int, default=0); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
angles = [0.0] if not a.move_joint else list(np.linspace(a.lo, a.hi, max(2, int(abs(a.hi - a.lo) / 5) + 1)))
cutters = []
for ang in angles:
    items = build(q={a.move_joint: ang} if a.move_joint else {})
    pt = [i for i in items if i.mesh == a.part][a.instance]
    if a.servo.startswith("part:"):      # cut with another PART's shape (convex hull, no grow), e.g. part:yaw_roll_motion
        src = [i for i in items if i.mesh == a.servo[5:]][0]
        c = src.mesh_obj.convex_hull.copy(); c.apply_transform(np.linalg.inv(pt.T))
    else:
        sv = [i for i in items if i.mesh == f"scs0009:{a.servo}"][0]
        c = scs0009.envelope_mesh(grow=a.grow, horn=False).copy(); c.apply_transform(np.linalg.inv(pt.T) @ sv.T)
    cutters.append(c)
cut = trimesh.boolean.union(cutters, engine="manifold") if len(cutters) > 1 else cutters[0]
path = spec.WORK_DIR / f"{a.part}.stl"; part = trimesh.load(path, force="mesh"); v0 = part.volume
res = trimesh.boolean.difference([part, cut], engine="manifold")
nb = len(res.split(only_watertight=False))
print(f"{a.part}: volume {v0/1000:.2f} -> {res.volume/1000:.2f} cm3 (removed {100*(1-res.volume/v0):.1f} %), watertight={res.is_watertight}, bodies={nb}")
assert res.is_watertight, "not watertight - not saved"
if nb > 1: print("WARNING: part split into pieces - NOT saved. Use a smaller --grow/range or redesign locally."); sys.exit(1)
if res.volume < 0.6 * v0: print("WARNING: removed > 40 % of the part - NOT saved; this needs a human decision."); sys.exit(1)
if not a.dry_run: res.export(path); print("wrote", path)
