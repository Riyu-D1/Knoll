import bpy
import bmesh

o = bpy.data.objects["FACE_PLATE"]
print("loc:", o.location[:], "rot:", o.rotation_euler[:], "scale:", o.scale[:])
bm = bmesh.new(); bm.from_mesh(o.data)
print("verts:", len(bm.verts), "edges:", len(bm.edges), "faces:", len(bm.faces))
pts = [(e.verts[0].co + e.verts[1].co) * 0.5
       for e in bm.edges if not e.is_manifold]
print(f"{len(pts)} nonmanifold edge midpoints, LOCAL (mm):")
for p in pts:
    print(f"  ({p.x*1000:6.1f},{p.y*1000:6.1f},{p.z*1000:6.1f})")
bm.free()
