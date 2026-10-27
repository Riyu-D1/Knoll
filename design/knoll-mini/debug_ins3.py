import bpy
from mathutils import Vector

o = bpy.data.objects["TRUNK_F"]
dg = bpy.context.evaluated_depsgraph_get()
eo = o.evaluated_get(dg)
m = eo.to_mesh()

# verts near each PANP post centre (0.0174, +-0.015, 0.089/0.097), r~2.2, x 15.4..19.4
for dy, dz in [(-0.015, -0.004), (-0.015, 0.004), (0.015, -0.004), (0.015, 0.004)]:
    c = Vector((0.0174, dy, 0.093 + dz))
    n = sum(1 for v in m.vertices
            if (o.matrix_world @ v.co - c).length < 0.0035)
    print(f"verts within 3.5mm of PANP({dy},{dz}): {n}")
# and the PCB posts: (0.009,-0.0214,0.085/0.101) and (-0.011,...)
for px, pz in [(0.009, 0.085), (0.009, 0.101), (-0.011, 0.085), (-0.011, 0.101)]:
    c = Vector((px, -0.0214, pz))
    n = sum(1 for v in m.vertices
            if (o.matrix_world @ v.co - c).length < 0.0035)
    print(f"verts within 3.5mm of PCBP({px},{pz}): {n}")
eo.to_mesh_clear()
