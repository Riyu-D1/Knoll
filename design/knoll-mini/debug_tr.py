import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

o = bpy.data.objects["TRUNK_R"]
dg = bpy.context.evaluated_depsgraph_get()
eo = o.evaluated_get(dg)
m = eo.to_mesh()
bm = bmesh.new()
bm.from_mesh(m)
bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
t = BVHTree.FromBMesh(bm)
bm.free()
eo.to_mesh_clear()

def inside(pt):
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

# points in the reported overlap band that should be CAVITY VOID
for pt in [(-0.010, -0.018, 0.090), (-0.008, -0.017, 0.100),
           (-0.010, 0.018, 0.086), (-0.012, 0.017, 0.082),
           (-0.010, -0.018, 0.085), (-0.015, 0.018, 0.086)]:
    print(pt, "inside TRUNK_R:", inside(pt))
# sanity: a point that IS material (rear wall)
print("rear wall (-0.019,0,0.090):", inside((-0.019, 0, 0.090)))
# and a void far from walls
print("cavity centre (-0.008,0,0.092):", inside((-0.008, 0, 0.092)))
