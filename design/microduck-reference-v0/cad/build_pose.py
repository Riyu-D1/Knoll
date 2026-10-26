#!/usr/bin/env python3
"""
Microduck recovery-pose render — poses the assembled robot on its back
(legs tucked, head planted) using the real joint axes from robot_walk.xml,
then renders one image. Illustrative pose, not a captured policy frame.

    blender --background --python build_pose.py -- \
        --md-dir <robot dir> --out <img dir> [--pose name]
"""
import os
import sys
import xml.etree.ElementTree as ET

import bpy
from mathutils import Matrix, Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MD = argv[argv.index("--md-dir") + 1]
OUT = argv[argv.index("--out") + 1]
POSE = argv[argv.index("--pose") + 1] if "--pose" in argv else "getup"

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
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*rgba[:3], 1)
    bsdf.inputs["Roughness"].default_value = 0.45
    MATS[m.get("name")] = mat


def xf(pos, quat):
    m = Matrix.Identity(4)
    if quat:
        m = Quaternion([float(v) for v in quat.split()]).to_matrix().to_4x4()
    m.translation = Vector(float(v) for v in (pos or "0 0 0").split())
    return m


# get-up pose (radians): tucked legs, head pitched to prop against floor
POSES = {
    "getup": {"left_knee": 1.15, "right_knee": 1.15,
              "left_ankle": -0.55, "right_ankle": -0.55,
              "left_hip_pitch": -0.5, "right_hip_pitch": -0.5,
              "neck_pitch": 0.7, "head_pitch": 0.45, "head_roll": 0.15},
    "crouch": {"left_knee": 1.3, "right_knee": 1.3,
               "left_ankle": -0.7, "right_ankle": -0.7,
               "left_hip_pitch": -0.6, "right_hip_pitch": -0.6,
               "neck_pitch": 0.3},
    "look": {"head_yaw": 0.9, "head_roll": 0.4, "neck_pitch": 0.3},
}
pose = POSES.get(POSE, POSES["getup"])

PLACEMENTS = []


def walk(el, parent_rigid, path):
    name = el.get("name")
    rigid = parent_rigid @ xf(el.get("pos"), el.get("quat"))
    world = rigid
    for j in el.findall("joint"):
        if j.get("type") == "hinge" and j.get("name") in pose:
            axis_w = (rigid.to_3x3() @ Vector(
                float(v) for v in j.get("axis").split())).normalized()
            R = (Matrix.Translation(rigid.translation)
                 @ Quaternion(axis_w, pose[j.get("name")]).to_matrix().to_4x4()
                 @ Matrix.Translation(-rigid.translation))
            world = R @ rigid
    for g in el.findall("geom"):
        if g.get("class") == "visual" and g.get("mesh"):
            PLACEMENTS.append((path + "/" + name, g.get("name") or g.get("mesh"),
                               g.get("mesh"), g.get("material", ""),
                               world @ xf(g.get("pos"), g.get("quat"))))
    for sub in el.findall("body"):
        walk(sub, world, path + "/" + name)


for b in worldbody.findall("body"):
    walk(b, Matrix.Identity(4), "")

# global "on back" rotation: duck faces +X -> rotate -90 deg about Y so the
# back/head-shell rest on the floor, then snap min-Z to 0.
G = Quaternion(Vector((0, 1, 0)), -1.5708).to_matrix().to_4x4()
PLACEMENTS = [(path, part, mesh, mat, G @ gm) for path, part, mesh, mat, gm in PLACEMENTS]
print(f"[parse] {len(PLACEMENTS)} placements, pose={POSE}")

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


objects = []
for path, part, mesh, mat_name, gm in PLACEMENTS:
    ob = bpy.data.objects.new(part, import_stl(mesh))
    ob.matrix_world = gm
    if mat_name in MATS:
        ob.data.materials.clear()
        ob.data.materials.append(MATS[mat_name])
    bpy.context.scene.collection.objects.link(ob)
    objects.append(ob)

# true floor snap from object bound boxes
zmin = min((ob.matrix_world @ Vector(c)).z for ob in objects for c in ob.bound_box)
for ob in objects:
    ob.location.z -= zmin

# stage
bpy.ops.mesh.primitive_plane_add(size=6)
floor = bpy.context.active_object
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
fb.inputs["Base Color"].default_value = (0.2, 0.2, 0.21, 1)
fb.inputs["Roughness"].default_value = 0.85
floor.data.materials.append(fm)

world = bpy.context.scene.world or bpy.data.worlds.new("w")
bpy.context.scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.02, 0.02, 0.025, 1)
bg.inputs[1].default_value = 0.25

for loc, energy in [((0.4, -0.4, 0.5), 45), ((-0.4, 0.35, 0.4), 28), ((0.0, 0.3, 0.15), 15)]:
    d = bpy.data.lights.new("a", "AREA")
    d.energy = energy
    d.shape = "DISK"
    d.size = 0.5
    o = bpy.data.objects.new("l", d)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 0.05)) - o.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"

# frame the whole lying robot
xs = [(ob.matrix_world @ Vector(c)).x for ob in objects for c in ob.bound_box]
ys = [(ob.matrix_world @ Vector(c)).y for ob in objects for c in ob.bound_box]
cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
d = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", d)
bpy.context.scene.collection.objects.link(cam)
cam.location = (cx + 0.28, cy - 0.3, 0.34)
cam.rotation_euler = (Vector((cx, cy, 0.04)) - cam.location).to_track_quat("-Z", "Y").to_euler()
d.lens = 50
d.clip_start, d.clip_end = 0.01, 20
scene.camera = cam

scene.render.filepath = os.path.join(OUT, f"pose-{POSE}.png")
bpy.ops.render.render(write_still=True)
print("[render]", scene.render.filepath)
