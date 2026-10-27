"""Helper: find the per-servo spin (SERVO_ROLL_DEG) that minimises servo-servo clashes at the current
S and STRETCH. Prints a suggested SERVO_ROLL_DEG dict and the remaining deficits. It does NOT edit spec.py."""
import sys, itertools
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np
from trimesh.transformations import rotation_matrix
import spec, scs0009
from assembly import build
from check_clearance import gap
base = build(roll_override={})
servos = [i for i in base if i.kind == "servo"]
names = [i.mesh.split(":")[1] for i in servos]
ROLLS = (0, 90, 180, 270)
env = scs0009.envelope_mesh()
def placed(i, r):
    m = env.copy(); m.apply_transform(servos[i].T @ rotation_matrix(np.radians(r), [1, 0, 0])); return m
P = {(i, r): placed(i, r) for i in range(len(servos)) for r in ROLLS}
pairs = {}
for a, b in itertools.combinations(range(len(servos)), 2):
    ca, cb = servos[a].mesh_obj.bounds.mean(0), servos[b].mesh_obj.bounds.mean(0)
    if np.linalg.norm(ca - cb) > 60: continue
    pairs[(a, b)] = {(ra, rb): gap(P[a, ra], P[b, rb]) for ra in ROLLS for rb in ROLLS}
def cost(R):
    return sum(max(0, spec.MIN_SERVO_GAP_MM - g[(R[a], R[b])]) for (a, b), g in pairs.items())
R = [0] * len(servos); best = cost(R)
for _ in range(6):
    for i in range(len(servos)):
        for r in ROLLS:
            T = R.copy(); T[i] = r; c = cost(T)
            if c < best - 1e-6: best, R = c, T
print("total deficit mm:", round(best, 2))
print("SERVO_ROLL_DEG = {" + ", ".join(f'"{n}": {r}' for n, r in zip(names, R) if r) + "}")
for (a, b), g in pairs.items():
    v = g[(R[a], R[b])]
    if v < spec.MIN_SERVO_GAP_MM: print(f"  remaining {names[a]:16s} vs {names[b]:16s} gap {v:6.2f}")
