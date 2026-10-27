import bpy

# reproduce the PANP union: copy TRUNK_F, try to union a cylinder at the post spot
tf = bpy.data.objects["TRUNK_F"]
dup = tf.copy()
dup.data = tf.data.copy()
bpy.context.scene.collection.objects.link(dup)

bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.0022, depth=0.004,
                                    location=(0.0174, -0.015, 0.089),
                                    rotation=(0, 1.5708, 0))
p = bpy.context.active_object

n0 = len(dup.data.vertices)
md = dup.modifiers.new("u", "BOOLEAN")
md.operation = "UNION"
md.object = p
md.solver = "EXACT"
bpy.context.view_layer.objects.active = dup
try:
    bpy.ops.object.modifier_apply(modifier="u")
    print("apply ok")
except RuntimeError as e:
    print("apply RAISED:", e)
print("verts", n0, "->", len(dup.data.vertices))
