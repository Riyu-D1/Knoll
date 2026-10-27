"""Range-of-motion collision sweep. Run: python tools/sweep_check.py [--joint NAME] [--step 15]
For each joint: rotate it alone through spec.SWEEP_REQUIRED_DEG (clipped to the joint range) in steps,
and test everything that moves (its body + all child bodies) against everything that does not.
A contact counts as NEW if it is > 0.5 mm deeper than the same pair at 0 deg (zero-pose contacts are
C3's job). R1 PASS = no NEW contact inside the required range for any joint. Exit 0 = PASS."""
import sys, argparse, xml.etree.ElementTree as ET
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np
from trimesh.collision import CollisionManager
import spec
from assembly import build

ap = argparse.ArgumentParser(); ap.add_argument("--joint"); ap.add_argument("--step", type=float, default=15)
a = ap.parse_args()
root = ET.parse(spec.UPSTREAM_DIR / "robot_walk.xml").getroot()
joint_body, desc = {}, {}
def walk(b, chain):
    n = b.get("name"); chain = chain + [n]
    for anc in chain:
        desc.setdefault(anc, set()).add(n)
    for j in b.findall("joint"):
        if j.get("name"):
            joint_body[j.get("name")] = n
    for c in b.findall("body"):
        walk(c, chain)
for b in root.find("worldbody").findall("body"):
    walk(b, [])
rng = {j.get("name"): [np.degrees(float(x)) for x in j.get("range").split()] for j in root.iter("joint") if j.get("name") and j.get("range")}

def contacts(q, moving):
    items = build(q=q)
    A, B = CollisionManager(), CollisionManager()
    for k, it in enumerate(items):
        (A if it.body in moving else B).add_object(f"{k}|{it.mesh}|{it.body}", it.mesh_obj)
    hit, names, data = A.in_collision_other(B, return_names=True, return_data=True)
    out = {}
    for c in (data or []):
        key = tuple(sorted(x.split("|", 1)[1] for x in c.names))
        out[key] = max(out.get(key, 0), c.depth)
    return out

ok = True
joints = [a.joint] if a.joint else [j[0] for j in spec.JOINTS]
for jn in joints:
    moving = desc[joint_body[jn]]
    lo_r, hi_r = spec.SWEEP_REQUIRED_DEG[jn]
    lo, hi = max(lo_r, rng[jn][0]), min(hi_r, min(rng[jn][1], 150))
    base = contacts({}, moving)
    angles = sorted(set(np.r_[np.arange(lo, hi, a.step), hi].round(1)) - {0.0})
    bad = []
    for ang in angles:
        for k, dpt in contacts({jn: ang}, moving).items():
            if dpt > base.get(k, 0) + 0.5:
                bad.append((ang, k, dpt))
    print(f"{jn:16s} swept {lo:+.0f}..{hi:+.0f} deg: {'PASS' if not bad else 'FAIL'}")
    for ang, k, dpt in bad[:12]:
        print(f"    at {ang:+6.1f} deg  {k[0]}  <->  {k[1]}  depth {dpt:.2f} mm")
    if len(bad) > 12: print(f"    ... {len(bad)-12} more")
    ok &= not bad
print("R1 OVERALL:", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
