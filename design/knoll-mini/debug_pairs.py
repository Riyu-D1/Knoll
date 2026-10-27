import bpy
from mathutils import Vector

def find(n):
    return bpy.data.objects.get(n)

def mesh_copy_world(o):
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    m = e.to_mesh()
    nm = bpy.data.meshes.new("c")
    nm.from_pydata([o.matrix_world @ v.co for v in m.vertices], [],
                   [list(p.vertices) for p in m.polygons])
    nm.update()
    e.to_mesh_clear()
    return nm

def overlap_region(a, b):
    ma, mb = find(a), find(b)
    m1 = mesh_copy_world(ma); m2 = mesh_copy_world(mb)
    oa = bpy.data.objects.new("A", m1); bpy.context.collection.objects.link(oa)
    ob = bpy.data.objects.new("B", m2); bpy.context.collection.objects.link(ob)
    mod = oa.modifiers.new("b", "BOOLEAN"); mod.operation = "INTERSECT"; mod.object = ob
    mod.solver = "EXACT"
    bpy.context.view_layer.objects.active = oa
    try:
        bpy.ops.object.modifier_apply(modifier="b")
        vs = [v.co for v in oa.data.vertices]
        if vs:
            xs = [v.x*1000 for v in vs]; ys = [v.y*1000 for v in vs]; zs = [v.z*1000 for v in vs]
            print(f"  {a} x {b}: {len(vs)} verts  x[{min(xs):.1f}..{max(xs):.1f}] y[{min(ys):.1f}..{max(ys):.1f}] z[{min(zs):.1f}..{max(zs):.1f}]")
        else:
            print(f"  {a} x {b}: empty intersection")
    except Exception as e:
        print(f"  {a} x {b}: bool err {e}")
    bpy.data.objects.remove(oa); bpy.data.objects.remove(ob)

for a, b in [("HROLL_L","HIP_L"),("HYAW_R","HIP_R"),("HROLL_R","HIP_R"),
             ("PCB_ESP32S3","TRUNK_R"),("IMU_BNO085","TRUNK_R"),
             ("LEDRING_L","HEAD_SHELL"),
             ("EYE_L","EYE_R"),
             ("EAR_L","EAR_CAP_L"),("EAR_R","EAR_CAP_R")]:
    overlap_region(a, b)

for n in ("EYE_L","EYE_R","EAR_L","EAR_CAP_L","FACE_PLATE"):
    o = find(n)
    if not o: print(f"{n}: MISSING"); continue
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    xs=[v.x*1000 for v in vs]; ys=[v.y*1000 for v in vs]; zs=[v.z*1000 for v in vs]
    print(f"{n}: {len(vs)} verts x[{min(xs):.2f}..{max(xs):.2f}] y[{min(ys):.2f}..{max(ys):.2f}] z[{min(zs):.2f}..{max(zs):.2f}]")

def verts_near(name, c, r):
    o = find(name)
    if not o: return -1
    c = Vector(c)
    return sum(1 for v in o.data.vertices if ((o.matrix_world @ v.co) - c).length < r)

probes = [
    ("HEAD_SHELL", (0.0336, 0.027, 0.1565), "FPPOST"),
    ("HEAD_SHELL", (0.0336, -0.027, 0.1485), "FPPOST"),
    ("TRUNK_F", (0.0159, 0.015, 0.089), "PANP"),
    ("TRUNK_F", (-0.011, -0.0214, 0.085), "PCBP"),
    ("TRUNK_R", (-0.0038, 0.0219, 0.086), "SEAM lug"),
    ("TRUNK_R", (-0.0038, -0.0219, 0.086), "SEAM lug"),
]
for obj, c, what in probes:
    print(f"{what} @ {c}: verts in {obj} = {verts_near(obj, c, 0.003)}")
