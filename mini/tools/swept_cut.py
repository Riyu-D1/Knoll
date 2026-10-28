"""Clearance cut: remove from a part every place a servo envelope (grown by --grow mm) passes through
while --move-joint sweeps --from..--to degrees. Use it when a servo hits a part of ANOTHER body
(e.g. hip_roll servo vs power_support). Works in the part's own mesh frame.
Usage: python tools/swept_cut.py --servo left_hip_roll --part power_support --move-joint left_hip_roll \
         --from -22 --to 22 [--grow 1.0] [--instance 0] [--dry-run]
Omit --move-joint to cut only at zero pose.
--servo part:<name> cuts with the convex hull of another part instead of a servo (e.g. neck parts vs a head shell).
--servo exact:<name>[:<body>] cuts with the exact mesh of another part (all matching instances;
  grown by --grow mm via +-grow translation union); use when a hull would remove too much.
--servo accepts a comma list, e.g. --servo exact:neck_frame,head_pitch (servo names = SCS0009 envelopes).
--horn includes the horn/spline discs in servo cutters (sweeps test the full envelope)."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
import spec, scs0009
from assembly import build
ap = argparse.ArgumentParser()
ap.add_argument("--servo", required=True); ap.add_argument("--part", required=True)
ap.add_argument("--move-joint"); ap.add_argument("--from", dest="lo", type=float, default=0); ap.add_argument("--to", dest="hi", type=float, default=0)
ap.add_argument("--grow", type=float, default=1.0); ap.add_argument("--horn", action="store_true")
ap.add_argument("--keep-largest", type=float, default=0.0,
                help="if the cut leaves fragments totalling < this fraction of the original volume, keep only the largest body")
ap.add_argument("--instance", type=int, default=0); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
angles = [0.0] if not a.move_joint else list(np.linspace(a.lo, a.hi, max(2, int(abs(a.hi - a.lo) / 5) + 1)))

def one_cutter(tok, items, Ti):
    if tok.startswith("part:"):          # convex hull of another part (no grow)
        src = [i for i in items if i.mesh == tok[5:]][0]
        c = src.mesh_obj.convex_hull.copy()
        return [c.apply_transform(Ti)]
    if tok.startswith("exact:"):         # exact mesh(es) of another part
        nm = tok[6:].split(":")
        srcs = [i for i in items if i.mesh == nm[0] and (len(nm) == 1 or i.body == nm[1])]
        out = []
        for s_ in srcs:
            c = s_.mesh_obj.copy(); c.apply_transform(Ti)
            if a.grow > 0:
                g = a.grow
                c = trimesh.boolean.union(
                    [c.copy().apply_transform(trimesh.transformations.translation_matrix(d))
                     for d in [(g,0,0),(-g,0,0),(0,g,0),(0,-g,0),(0,0,g),(0,0,-g)]], engine="manifold")
            out.append(c)
        return out
    sv = [i for i in items if i.mesh == f"scs0009:{tok}"][0]   # SCS0009 envelope for joint <tok>
    c = scs0009.envelope_mesh(grow=a.grow, horn=a.horn).copy()
    return [c.apply_transform(Ti @ sv.T)]

cutters = []
for ang in angles:
    items = build(q={a.move_joint: ang} if a.move_joint else {})
    pt = [i for i in items if i.mesh == a.part][a.instance]
    for tok in a.servo.split(","):
        cutters += one_cutter(tok.strip(), items, np.linalg.inv(pt.T))
cut = trimesh.boolean.union(cutters, engine="manifold") if len(cutters) > 1 else cutters[0]
path = spec.WORK_DIR / f"{a.part}.stl"; part = trimesh.load(path, force="mesh"); v0 = part.volume
res = trimesh.boolean.difference([part, cut], engine="manifold")
bodies = res.split(only_watertight=False)
nb = len(bodies)
if nb > 1 and a.keep_largest > 0:
    bodies = sorted(bodies, key=lambda b: b.volume, reverse=True)
    frag_vol = sum(b.volume for b in bodies[1:])
    if frag_vol <= a.keep_largest * v0:
        print(f"   dropping {nb-1} fragment(s), total {frag_vol:.1f} mm3 ({100*frag_vol/v0:.2f} % of part):")
        for b in bodies[1:]:
            print(f"     frag vol {b.volume:.1f} mm3 bounds {b.bounds.round(1).tolist()}")
        res = bodies[0]; nb = 1
    else:
        print(f"   fragments total {frag_vol:.1f} mm3 > {100*a.keep_largest:.1f} % of part - NOT saved"); sys.exit(1)
print(f"{a.part}: volume {v0/1000:.2f} -> {res.volume/1000:.2f} cm3 (removed {100*(1-res.volume/v0):.1f} %), watertight={res.is_watertight}, bodies={nb}")
assert res.is_watertight, "not watertight - not saved"
if nb > 1: print("WARNING: part split into pieces - NOT saved. Use a smaller --grow/range or redesign locally."); sys.exit(1)
if res.volume < 0.6 * v0: print("WARNING: removed > 40 % of the part - NOT saved; this needs a human decision."); sys.exit(1)
if not a.dry_run: res.export(path); print("wrote", path)
