#!/usr/bin/env python3
"""Dump the world-space overlap region (mm) for flagged part pairs."""
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PAIRS = [
    ("HROLL_L", "HIP_L"), ("HROLL_R", "HIP_R"),
    ("BATTERY_2S_300", "TRUNK_F"), ("SPEAKER_16MM", "TRUNK_F"),
    ("FEMUR_R", "SHIN_R"),
]


def wt(o):
    m = o.data.copy()
    bm = bmesh.new()
    bm.from_mesh(m)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    bb = [(o.matrix_world @ Vector(c)) for c in o.bound_box]
    return t, bb


def march(tree, pt, ray):
    p = Vector(pt)
    hits = 0
    last = None
    for _ in range(600):
        loc, n, i, d = tree.ray_cast(p, ray)
        if loc is None:
            break
        if last is None or (loc - last).length > 5e-5:
            hits += 1
            last = loc
        p = loc + ray * 2e-6
    return hits


_RAYS = (
    Vector((0.57735, 0.57735, 0.57735)),
    Vector((0.57735, -0.57735, 0.57735)),
    Vector((-0.57735, 0.57735, 0.57735)),
)


def inside(tree, pt):
    return sum(1 for r in _RAYS if march(tree, pt, r) % 2 == 1) >= 2


def get(name):
    for o in bpy.data.objects:
        if o.name == name or o.name.startswith(name + "."):
            return o
    return None


for an, bn in PAIRS:
    a, b = get(an), get(bn)
    if not a or not b:
        print(f"[{an} x {bn}] missing object")
        continue
    ta, ba = wt(a)
    tb, bb = wt(b)
    lo = [max(min(p[i] for p in ba), min(p[i] for p in bb)) for i in range(3)]
    hi = [min(max(p[i] for p in ba), max(p[i] for p in bb)) for i in range(3)]
    if any(hi[i] <= lo[i] + 1e-6 for i in range(3)):
        print(f"[{an} x {bn}] AABBs disjoint")
        continue
    vol = 1.0
    for i in range(3):
        vol *= max(hi[i] - lo[i], 1e-6)
    step = max((vol / 40000.0) ** (1 / 3), 0.00015)
    pts = []
    x = lo[0] + step / 2
    while x < hi[0]:
        y = lo[1] + step / 2
        while y < hi[1]:
            z = lo[2] + step / 2
            while z < hi[2]:
                if inside(ta, (x, y, z)) and inside(tb, (x, y, z)):
                    pts.append((x, y, z))
                z += step
            y += step
        x += step
    if not pts:
        print(f"[{an} x {bn}] surfaces touch, 0 volume")
        continue
    v = len(pts) * step**3 * 1e9
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    f = lambda p: "(" + ",".join(f"{c*1000:6.1f}" for c in p) + ")"
    print(f"[{an} x {bn}] {v:8.1f} mm3  region {f(mn)} .. {f(mx)}")

print("[done]")
