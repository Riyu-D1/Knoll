"""Lengthen a part by moving every vertex on one side of a cut plane by --delta mm along --axis.
Works in the part's own mesh frame. Keeps topology, so a watertight part stays watertight.
Pick a plane that does not cut through a hole or a servo pocket (look at the part first).
Usage: python tools/stretch_mesh.py --part power_support --axis z --plane 3.0 --delta 2.5 [--side +|-]
  --side + (default): vertices with coord > plane move by +delta. --side -: coord < plane move by -delta."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh, spec
ap = argparse.ArgumentParser()
ap.add_argument("--part", required=True); ap.add_argument("--axis", choices="xyz", required=True)
ap.add_argument("--plane", type=float, required=True); ap.add_argument("--delta", type=float, required=True)
ap.add_argument("--side", choices="+-", default="+")
a = ap.parse_args()
p = spec.WORK_DIR / f"{a.part}.stl"; m = trimesh.load(p, force="mesh")
k = "xyz".index(a.axis); v = m.vertices.copy()
sel = v[:, k] > a.plane if a.side == "+" else v[:, k] < a.plane
v[sel, k] += a.delta if a.side == "+" else -a.delta
e0 = m.extents.copy(); m.vertices = v
print(f"{a.part}: moved {sel.sum()} of {len(v)} vertices; extents {e0.round(2)} -> {m.extents.round(2)}; watertight={m.is_watertight}")
assert m.is_watertight
m.export(p); print("wrote", p)
