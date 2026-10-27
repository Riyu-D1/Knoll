import bpy
from mathutils import Vector

for o in bpy.data.objects:
    if "FACE" in o.name.upper() or "SPK_" in o.name:
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = [min(p[i] for p in bb) for i in range(3)]
        hi = [max(p[i] for p in bb) for i in range(3)]
        f = lambda p: "(" + ",".join(f"{c*1000:6.1f}" for c in p) + ")"
        print(f"{o.name:20s} verts={len(o.data.vertices):5d}  bbox {f(lo)} .. {f(hi)}")
