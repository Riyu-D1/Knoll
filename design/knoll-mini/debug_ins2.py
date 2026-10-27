import bpy
import bmesh
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def tree(name):
    o = bpy.data.objects[name]
    dg = bpy.context.evaluated_depsgraph_get()
    eo = o.evaluated_get(dg)
    m = eo.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(m)
    bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    eo.to_mesh_clear()
    return t


def inside(t, pt):
    ray = Vector((0.57735, 0.57735, 0.57735))
    p = Vector(pt)
    hits = 0
    for _ in range(600):
        loc, n, i, d = t.ray_cast(p, ray)
        if loc is None:
            break
        hits += 1
        p = loc + ray * 1e-6
    return hits % 2 == 1


tf = tree("TRUNK_F")
tr = tree("TRUNK_R")

# PANINS_0 at (0.0159, -0.015, 0.089) axis X -> ring in YZ plane
print("PANINS_0 ring (YZ):")
for i in range(6):
    a = 2 * math.pi * i / 6
    p = (0.0159, -0.015 + 0.0017 * math.cos(a), 0.089 + 0.0017 * math.sin(a))
    print(f"  {p} -> {inside(tf, p)}")

# same ring in TRUNK_R just in case
print("  in tr:", sum(inside(tr, (0.0159, -0.015 + 0.0017 * math.cos(2*math.pi*i/6),
                                 0.089 + 0.0017 * math.sin(2*math.pi*i/6)))
                     for i in range(6)), "/6")

# PCBINS_2 at (0.009, -0.0214, 0.085) axis Y -> ring in XZ plane
print("PCBINS_2 ring (XZ) in tf:", sum(
    inside(tf, (0.009 + 0.0017 * math.cos(2*math.pi*i/6), -0.0214,
                0.085 + 0.0017 * math.sin(2*math.pi*i/6)))
    for i in range(6)), "/6")

# where exactly does the PANP post centre sit? probe the post at radius 1.4
# (inside the post r2.2 but outside its r0.9 pilot bore)
print("post body at r1.4:", inside(tf, (0.0166, -0.015 + 0.0014, 0.089)))
print("post body at x16:", inside(tf, (0.0160, -0.015 + 0.0014, 0.089)))
