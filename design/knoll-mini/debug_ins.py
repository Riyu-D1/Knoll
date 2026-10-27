import bpy
import bmesh
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

# where are the PANINS / PCBINS proxies actually located?
for o in bpy.data.objects:
    if o.name.startswith(("PANINS", "PCBINS", "PANP", "PCBP")):
        c = o.matrix_world.translation
        print(f"{o.name:12s} at ({c.x*1000:6.1f},{c.y*1000:6.1f},{c.z*1000:6.1f})")

tzc = 0.093
print("--- PANP post centres (should be material) ---")
for dy, dz in [(-0.015, -0.004), (-0.015, 0.004), (0.015, -0.004), (0.015, 0.004)]:
    for dx in (0.0174, 0.0162):
        print((dx, dy, tzc + dz), "->", inside(tf, (dx, dy, tzc + dz)))
print("--- PCB posts ---")
for px, pz in [(-0.011, -0.008), (-0.011, 0.008), (0.009, -0.008), (0.009, 0.008)]:
    # post is cyl axis Y at (px,-0.0214,tzc+pz): sample ring in XZ
    import math
    hits = 0
    for k in range(6):
        a = k * 1.0472
        pt = (px + 0.0017 * math.cos(a), -0.0214, tzc + pz + 0.0017 * math.sin(a))
        if inside(tf, pt):
            hits += 1
    print(f"PCB post ({px},{pz}) ring hits: {hits}/6")
