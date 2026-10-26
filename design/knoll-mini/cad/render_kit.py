"""Render the actual production STLs (cad/parts/) — NOT the Blender mesh model.
Usage: blender -b -P render_kit.py   (run from design/knoll-mini/cad/)
"""
import bpy, math, os, sys
from mathutils import Vector

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "img", "cad")
PARTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parts")
os.makedirs(OUT, exist_ok=True)

# ---- clean scene ----------------------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in \
    [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] \
    else "BLENDER_EEVEE"
sc.render.resolution_x = sc.render.resolution_y = 900
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.film_transparent = False
world = bpy.data.worlds.new("W"); sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.012, 0.014, 0.02, 1)
bg.inputs[1].default_value = 0.35

# ---- materials ------------------------------------------------------------
def mat(name, rgb, metal=0.0, rough=0.55, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
        bsdf.inputs["Emission Strength"].default_value = emit
    return m

WHITE  = mat("shell",  (0.82, 0.84, 0.85), rough=0.4)
ORANGE = mat("accent", (0.95, 0.35, 0.06), rough=0.45)
DARK   = mat("dark",   (0.02, 0.025, 0.03), rough=0.3)
GRAY   = mat("sole",   (0.10, 0.11, 0.12), rough=0.8)
LENS   = mat("lens",   (0.25, 0.9, 1.0), emit=5.0)
BRASS  = mat("brass",  (0.55, 0.38, 0.12), metal=0.9, rough=0.3)

def material_for(name):
    n = name.upper()
    if "COLLAR" in n:                       return ORANGE
    if n.startswith(("EYE_RING", "EYE_")):  return LENS
    if n.startswith(("FACE_PLATE", "CHIN", "EAR_CAP", "NCOL")): return DARK
    if n.startswith(("SOLE", "TOE", "SHIN")): return GRAY
    if n.startswith(("CAM_BRK", "TOF_BRK")): return DARK
    return WHITE

# ---- import every STL (FreeCAD exports mm -> scale 0.001) -------------------
imported = []
for f in sorted(os.listdir(PARTS)):
    if not f.endswith(".stl"):
        continue
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=os.path.join(PARTS, f),
                        global_scale=0.001)
    for o in set(bpy.data.objects) - before:
        o.data.materials.append(material_for(f[:-4]))
        imported.append(o)

print(f"[import] {len(imported)} parts")

# smooth shade everything
for o in imported:
    for p in o.data.polygons:
        p.use_smooth = True

# ---- studio: camera + 3-point lights --------------------------------------
def add_light(name, loc, energy, size=0.6):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy; d.shape = "DISK"; d.size = size
    o = bpy.data.objects.new(name, d); bpy.context.collection.objects.link(o)
    o.location = loc
    return o

def point_at(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()

add_light("key",  (0.25, -0.30, 0.35), 38)
add_light("fill", (-0.28, -0.18, 0.22), 20)
add_light("rim",  (0.0, 0.28, 0.30), 50)
for L in [o for o in bpy.data.objects if o.type == "LIGHT"]:
    point_at(L, (0, 0, 0.08))

cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 58
cam = bpy.data.objects.new("cam", cam_d)
bpy.context.collection.objects.link(cam); sc.camera = cam

# robot bounds ~ x -35..45 mm, y +-50, z -2..160  -> meters
TARGET = Vector((0.005, 0, 0.075))

def shot(name, loc, hide=()):
    for o in imported:
        o.hide_render = o.name.split(".stl")[0] in hide or \
                        o.name in hide
    cam.location = loc
    point_at(cam, TARGET)
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    for o in imported:
        o.hide_render = False
    print("[shot]", name)

# hero 3/4 (x forward = face) — robot faces +X
shot("hero-3q",  (0.32, -0.30, 0.22))
shot("front",    (0.34, 0.0, 0.10))
shot("side",     (0.02, -0.36, 0.10))
shot("rear",     (-0.32, 0.24, 0.20))
# internals: hide front trunk shell + head shell -> shows pockets, collars,
# tray, panel posts, neck column
HIDE_INT = {"TRUNK_F", "HEAD_SHELL", "FACE_PLATE", "CHIN", "CHEST_PANEL",
            "EAR_L", "EAR_R", "EAR_CAP_L", "EAR_CAP_R"}
shot("internals", (0.30, -0.28, 0.20), hide=HIDE_INT)
# leg detail: servo station hardware close-up
TARGET2 = Vector((0.02, 0.017, 0.04))
cam.location = (0.14, -0.10, 0.08); point_at(cam, TARGET2)
for o in imported:
    o.hide_render = not any(k in o.name for k in
        ("KNEE_L", "HROLL_L", "FOOT_L", "SOLE_L", "TOE_L", "SHIN_L",
         "HPITCH_L", "HYAW_L"))
sc.render.filepath = os.path.join(OUT, "leg-detail.png")
bpy.ops.render.render(write_still=True)
print("[shot] leg-detail")
for o in imported:
    o.hide_render = False

print("[done]", OUT)
