import bpy
import bmesh

# 1) union the same cylinder into a FRESH cube — control case
bpy.ops.mesh.primitive_cube_add(location=(0.0174, -0.015, 0.089), size=0.01)
base = bpy.context.active_object
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0022, depth=0.004,
                                    location=(0.0174, -0.015, 0.089),
                                    rotation=(0, 1.5708, 0))
p = bpy.context.active_object
md = base.modifiers.new("u", "BOOLEAN")
md.operation = "UNION"; md.object = p; md.solver = "EXACT"
bpy.context.view_layer.objects.active = base
n0 = len(base.data.vertices)
bpy.ops.object.modifier_apply(modifier="u")
print(f"fresh cube: {n0} -> {len(base.data.vertices)}")

# 2) inspect TRUNK_F mesh health
tf = bpy.data.objects["TRUNK_F"]
bm = bmesh.new(); bm.from_mesh(tf.data)
nm_e = sum(1 for e in bm.edges if not e.is_manifold)
deg = sum(1 for e in bm.edges if e.calc_length() < 1e-7)
print(f"TRUNK_F: {len(bm.verts)} verts {len(bm.faces)} faces  "
      f"nonmanifold={nm_e} degenerate_edges={deg}")
# loose/duplicate verts?
import collections
cnt = collections.Counter(tuple(round(c, 6) for c in v.co) for v in bm.verts)
dups = sum(k - 1 for k in cnt.values() if k > 1)
print(f"duplicate verts: {dups}")
bm.free()
