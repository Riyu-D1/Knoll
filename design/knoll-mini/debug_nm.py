import bpy
import bmesh
from mathutils import Vector

o = bpy.data.objects["FACE_PLATE"]
bm = bmesh.new(); bm.from_mesh(o.data)
pts = [o.matrix_world @ (e.verts[0].co + e.verts[1].co) * 0.5
       for e in bm.edges if not e.is_manifold]
print(f"{len(pts)} nonmanifold edge midpoints (mm):")
for p in pts:
    print(f"  ({p.x*1000:6.1f},{p.y*1000:6.1f},{p.z*1000:6.1f})")
bm.free()
