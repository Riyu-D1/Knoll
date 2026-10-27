"""Thicken a flat plate-like part by scaling it along ONE of its own axes about its mid-plane.
Usage: python tools/thicken_plate.py --part upper_leg_rigidity_plate --axis x --factor 1.7
Only use on parts whose extent along --axis is basically the plate thickness. Re-run
check_clearance.py afterwards (a thicker plate can hit a neighbour)."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh, spec
ap = argparse.ArgumentParser()
ap.add_argument("--part", required=True); ap.add_argument("--axis", choices="xyz", required=True)
ap.add_argument("--factor", type=float, required=True)
a = ap.parse_args(); assert 1.0 < a.factor <= 2.5
p = spec.WORK_DIR / f"{a.part}.stl"; m = trimesh.load(p, force="mesh")
k = "xyz".index(a.axis); mid = m.bounds.mean(0)[k]; v = m.vertices.copy()
e0 = m.extents.copy(); v[:, k] = mid + (v[:, k] - mid) * a.factor; m.vertices = v
print(f"{a.part}: extents {e0.round(2)} -> {m.extents.round(2)} watertight={m.is_watertight}")
assert m.is_watertight; m.export(p); print("wrote", p)
