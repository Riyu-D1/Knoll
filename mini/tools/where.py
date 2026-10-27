"""Print where a servo sits in a part's OWN mesh frame (the frame stretch_mesh.py / thicken_plate.py use).
Usage: python tools/where.py --servo left_ankle --part ankle_left [--instance 0]
Prints: the part-local axis closest to the servo shaft, the servo case span along each part-local axis,
and the part's own extents, so you can choose --axis/--plane/--delta for stretch_mesh.py."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh, spec, scs0009
from assembly import build
ap = argparse.ArgumentParser(); ap.add_argument("--servo", required=True); ap.add_argument("--part", required=True)
ap.add_argument("--instance", type=int, default=0); a = ap.parse_args()
items = build()
sv = [i for i in items if i.mesh == f"scs0009:{a.servo}"][0]
pt = [i for i in items if i.mesh == a.part][a.instance]
rel = np.linalg.inv(pt.T) @ sv.T
shaft = rel[:3, :3] @ np.array([1.0, 0, 0])          # servo shaft = servo-local X
k = int(np.argmax(abs(shaft)))
env = scs0009.envelope_mesh(horn=False).copy(); env.apply_transform(rel)
horn_pt = rel @ np.array([-14.5 * spec.S, 0, 0, 1])
pm = trimesh.load(spec.WORK_DIR / f"{a.part}.stl", force="mesh")
print(f"part {a.part} (body {pt.body}); servo {a.servo} (body {sv.body})")
print(f"shaft direction in part frame: {shaft.round(3)}  -> closest axis '{'xyz'[k]}' (horn side is {'-' if shaft[k] > 0 else '+'}{'xyz'[k]})")
print(f"horn top point in part frame: {horn_pt[:3].round(2)}")
for i, n in enumerate("xyz"):
    print(f"  {n}: servo case+ears span {env.bounds[0][i]:8.2f} .. {env.bounds[1][i]:8.2f}   part span {pm.bounds[0][i]:8.2f} .. {pm.bounds[1][i]:8.2f}")
