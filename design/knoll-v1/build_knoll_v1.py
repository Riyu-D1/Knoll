#!/usr/bin/env python3
"""
Knoll v1 — first real derivative: Microduck skeleton + BDX-style head.

Builds on the official MJCF (pollen-robotics/microduck_rl, Apache-2.0):
- keeps every structural part and ALL head internals (camera lens, Pi
  Zero 2W + robot-hat PCB, speaker, motor support, bearings)
- drops the cosmetic Microduck head shell (top/bottom head shells,
  face_part, jaw, jaw_soft, soft_mouth_top, noenoeil)
- models a NEW parametric head shell (dome + dark visor + twin eyes +
  antenna + ear pods) sized to wrap the retained internals + margin
- swaps xl330 servos for cheap-servo proxy boxes at the same envelope
  (20x34x26 mm) — ST3215/XL330-clone class; brackets need re-check

    blender --background --python build_knoll_v1.py -- \
        --md-dir <robot dir> --out . [--quick]

Head geometry is Knoll-original (BDX-inspired, not a copy). Microduck
parts remain (c) Pollen Robotics — see ../microduck-reference-v0/THIRD-
PARTY-NOTICES.md.
"""
import os
import sys
import xml.etree.ElementTree as ET

import bpy
from mathutils import Matrix, Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MD = argv[argv.index("--md-dir") + 1]
OUT = argv[argv.index("--out") + 1]
QUICK = "--quick" in argv
IMG = os.path.join(OUT, "img")
PARTS = os.path.join(OUT, "parts")
os.makedirs(IMG, exist_ok=True)
os.makedirs(PARTS, exist_ok=True)

# cosmetic Microduck meshes we remove (bill/duck face identity lives here)
DROP = {"top_head_shell", "bottom_head_shell", "face_part", "jaw",
        "jaw_soft", "soft_mouth_top", "noenoeil"}
# servo meshes replaced by cheap proxy
SERVO = {"xl330"}

tree = ET.parse(os.path.join(MD, "robot_walk.xml"))
root_xml = tree.getroot()
worldbody = next(e for e in root_xml.iter("worldbody"))
meshdir = next(e for e in root_xml.iter("compiler")).get("meshdir", "assets")
ASSETS = os.path.join(MD, meshdir)

MATS = {}
for m in root_xml.iter("material"):
    rgba = [float(x) for x in m.get("rgba", "0.7 0.7 0.7 1").split()]
    mat = bpy.data.materials.get(m.get("name")) or bpy.data.materials.new(m.get("name"))
    mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgba[:3], 1)
    b.inputs["Roughness"].default_value = 0.55
    MATS[m.get("name")] = mat


def xf(pos, quat):
    m = Matrix.Identity(4)
    if quat:
        m = Quaternion([float(v) for v in quat.split()]).to_matrix().to_4x4()
    m.translation = Vector(float(v) for v in (pos or "0 0 0").split())
    return m


PL = []


def walk(el, parent, path):
    name = el.get("name")
    w = parent @ xf(el.get("pos"), el.get("quat"))
    for g in el.findall("geom"):
        if g.get("class") == "visual" and g.get("mesh"):
            PL.append((path + "/" + name, g.get("name") or g.get("mesh"),
                       g.get("mesh"), g.get("material", ""),
                       w @ xf(g.get("pos"), g.get("quat"))))
    for s in el.findall("body"):
        walk(s, w, path + "/" + name)


for b in worldbody.findall("body"):
    walk(b, Matrix.Identity(4), "")

mesh_cache = {}


def import_stl(name):
    if name in mesh_cache:
        return mesh_cache[name]
    before = set(bpy.data.meshes)
    bpy.ops.wm.stl_import(filepath=os.path.join(ASSETS, name + ".stl"))
    new = [m for m in bpy.data.meshes if m not in before][0]
    for o in list(bpy.context.selected_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    new.name = "STL_" + name
    mesh_cache[name] = new
    return new


def mat_principled(name, rgb, rough=0.5, metal=0.0, emit=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "DITHERED"
    return m


COLS = {}
def col(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    COLS[name] = c
    return c


def link_to(col_name, ob):
    for c in ob.users_collection:
        c.objects.unlink(ob)
    COLS[col_name].objects.link(ob)


def cube_obj(name, dims, loc, col_name, mat=None, rot=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    if rot:
        o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new("bev", "BEVEL")
        mod.width = bevel
        mod.segments = 4
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="bev")
    if mat:
        o.data.materials.append(mat)
    link_to(col_name, o)
    return o


def cyl_obj(name, r, depth, loc, col_name, mat=None, rot=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=depth,
                                        location=loc)
    o = bpy.context.active_object
    o.name = name
    if rot:
        o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        o.data.materials.append(mat)
    link_to(col_name, o)
    return o


# ------------------------------------------------ collections + parts
for c in ["BODY", "HEAD_INTERNALS", "HEAD_SHELL", "SERVO_PROXY", "JOINTS"]:
    col(c)

body_parts, head_internals, servo_locs = [], [], []
for path, part, mesh, mat_name, gm in PL:
    if mesh in DROP:
        continue
    ob = None
    if mesh in SERVO:
        servo_locs.append((part, gm.copy()))
        continue
    ob = bpy.data.objects.new(part, import_stl(mesh))
    ob.matrix_world = gm
    if mat_name in MATS:
        ob.data.materials.clear()
        ob.data.materials.append(MATS[mat_name])
    target = "HEAD_INTERNALS" if "jaw_soft" in path else "BODY"
    link_to(target, ob)
    (head_internals if target == "HEAD_INTERNALS" else body_parts).append(ob)

# cheap servo proxies — box + horn at xl330 envelope (0.020 x 0.034 x 0.026 m)
SMAT = mat_principled("servo_proxy", (0.18, 0.18, 0.20), rough=0.45)
for part, gm in servo_locs:
    p = cube_obj("SERVO_" + part, (0.020, 0.034, 0.026), gm.translation,
                 "SERVO_PROXY", SMAT)
    p.rotation_mode = "QUATERNION"
    p.rotation_quaternion = gm.to_quaternion()
    print(f"[servo] {part} @ {[round(v,4) for v in gm.translation]}")

# ------------------------------------------------ head internals envelope
def obj_bb(ob):
    return [ob.matrix_world @ Vector(c) for c in ob.bound_box]

all_hi = [v for o in head_internals for v in obj_bb(o)]
hi_min = Vector((min(v.x for v in all_hi), min(v.y for v in all_hi), min(v.z for v in all_hi)))
hi_max = Vector((max(v.x for v in all_hi), max(v.y for v in all_hi), max(v.z for v in all_hi)))
print(f"[head internals] {[(a, b) for a, b in zip(hi_min, hi_max)]}")

# shell dims = internals + margin, snapped to min size
M = 0.006  # wall margin
cx = (hi_min.x + hi_max.x) / 2
cy = (hi_min.y + hi_max.y) / 2
z0 = 0.197                                    # extend down to neck (encloses head servos)
z1 = hi_max.z + M                        # dome top
W = max(hi_max.y - hi_min.y + 2 * M, 0.090)   # width (Y)
D = max(hi_max.x - hi_min.x + 2 * M, 0.108)   # depth (X, face at +X)
H = z1 - z0
print(f"[head shell] W{W*1000:.0f} D{D*1000:.0f} H{H*1000:.0f} z {z0*1000:.0f}..{z1*1000:.0f}")

SHELL = mat_principled("shell_white", (0.92, 0.92, 0.90), rough=0.35)
VISOR = mat_principled("visor", (0.05, 0.05, 0.06), rough=0.12, metal=0.3)
EYEM = mat_principled("eye", (0.35, 0.75, 1.0), rough=0.2, emit=8.0)
ACCENT = mat_principled("accent", (0.95, 0.45, 0.15), rough=0.4)
EAR = mat_principled("ear", (0.25, 0.25, 0.28), rough=0.4)

face_x = cx + D / 2  # +X is the face side

# dome: rounded box shell over internals
dome = cube_obj("HEAD_DOME", (D, W, H), (cx, cy, z0 + H / 2), "HEAD_SHELL",
                SHELL, bevel=min(0.028, D * 0.28))
# brow band accent around dome base
cube_obj("HEAD_BAND", (D * 0.90, W * 0.94, 0.008), (cx, cy, z0 + 0.006),
         "HEAD_SHELL", ACCENT, bevel=0.003)
# visor: dark plate on the face (+X), slightly proud
vis_w = W * 0.72
vis_h = H * 0.52
vis = cube_obj("HEAD_VISOR", (0.012, vis_w, vis_h),
               (face_x + 0.002, cy, z0 + H * 0.58), "HEAD_SHELL", VISOR,
               bevel=0.010)
# twin eyes: glowing discs on visor
eye_r = vis_w * 0.11
eye_z = z0 + H * 0.60
for sgn, tag in ((1, "L"), (-1, "R")):
    cyl_obj(f"EYE_{tag}", eye_r, 0.006,
            (face_x + 0.009, cy + sgn * vis_w * 0.27, eye_z),
            "HEAD_SHELL", EYEM, rot=(0, 1.5708, 0))
# mouth slit: thin dark bar under eyes
cube_obj("MOUTH", (0.010, vis_w * 0.34, 0.006),
         (face_x + 0.009, cy, z0 + H * 0.40), "HEAD_SHELL", VISOR, bevel=0.003)
# antenna: mast + tip on dome top, offset rear
ant_x = cx - D * 0.18
cyl_obj("ANT_MAST", 0.0025, 0.018, (ant_x, cy, z1 + 0.009), "HEAD_SHELL", EAR)
bpy.ops.mesh.primitive_ico_sphere_add(radius=0.006, location=(ant_x, cy, z1 + 0.021))
tip = bpy.context.active_object
tip.name = "ANT_TIP"
tip.data.materials.append(ACCENT)
link_to("HEAD_SHELL", tip)
# ear pods: short cylinders on +-Y faces
for sgn, tag in ((1, "L"), (-1, "R")):
    cyl_obj(f"EAR_{tag}", 0.011, 0.008,
            (cx, cy + sgn * (W / 2 + 0.004), z0 + H * 0.55),
            "HEAD_SHELL", EAR, rot=(1.5708, 0, 0))
    cyl_obj(f"EAR_CAP_{tag}", 0.006, 0.009,
            (cx, cy + sgn * (W / 2 + 0.006), z0 + H * 0.55),
            "HEAD_SHELL", ACCENT, rot=(1.5708, 0, 0))

# export head-shell objects as STLs for CAD handoff
for ob in COLS["HEAD_SHELL"].objects:
    sel = bpy.context.selected_objects
    for s in sel:
        s.select_set(False)
    ob.select_set(True)
    bpy.ops.wm.stl_export(filepath=os.path.join(PARTS, ob.name + ".stl"),
                          export_selected_objects=True)
print(f"[export] {len(COLS['HEAD_SHELL'].objects)} head parts -> parts/")

# ------------------------------------------------ stage + render
bpy.ops.mesh.primitive_plane_add(size=6)
floor = bpy.context.active_object
fm = mat_principled("floor", (0.2, 0.2, 0.21), rough=0.85)
floor.data.materials.append(fm)
w = bpy.context.scene.world or bpy.data.worlds.new("w")
bpy.context.scene.world = w
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.02, 0.02, 0.025, 1)
bg.inputs[1].default_value = 0.25
for loc, e in [((0.5, -0.55, 0.8), 55), ((-0.6, 0.3, 0.55), 32), ((0.15, 0.6, 0.3), 20)]:
    d = bpy.data.lights.new("a", "AREA")
    d.energy = e
    d.shape = "DISK"
    d.size = 0.5
    o = bpy.data.objects.new("l", d)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 0.12)) - o.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x = 1280
sc.render.resolution_y = 1440
sc.render.image_settings.file_format = "PNG"
sc.view_settings.look = "AgX - Medium High Contrast"
TARGET = Vector((0, 0, 0.115))


def cam(name, loc, ortho=None, target=TARGET):
    d = bpy.data.cameras.new(name)
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (target - o.location).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        d.type = "ORTHO"
        d.ortho_scale = ortho
    else:
        d.lens = 50
    d.clip_start, d.clip_end = 0.01, 20
    sc.camera = o


def render(name):
    sc.render.filepath = os.path.join(IMG, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("[render]", name)


def set_col(col_name, hide):
    COLS[col_name].hide_render = hide
    for o in COLS[col_name].objects:
        o.hide_render = hide


cam("hero", (0.40, -0.30, 0.26))
render("hero-3q")

if not QUICK:
    cam("front", (0.46, 0, 0.11), ortho=0.34)
    render("front")
    cam("side", (0, -0.46, 0.11), ortho=0.34)
    render("side")
    cam("rear", (-0.46, 0, 0.11), ortho=0.34)
    render("rear")
    cam("hero", (0.40, -0.30, 0.26))
    cam("head", (0.24, -0.20, 0.28), ortho=0.16, target=Vector((0, 0, 0.21)))
    render("head-detail")

    # internals view: shell hidden -> shows space for components
    set_col("HEAD_SHELL", True)
    cam("head", (0.24, -0.20, 0.28), ortho=0.16, target=Vector((0, 0, 0.21)))
    render("internals")
    set_col("HEAD_SHELL", False)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "knoll-v1.blend"))
print("[done]")
