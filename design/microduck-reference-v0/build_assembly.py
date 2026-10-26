#!/usr/bin/env python3
"""
Knoll reference build — faithful Microduck assembly from official MJCF.

Imports every visual part referenced by robot_walk.xml from
pollen-robotics/microduck_rl (Apache-2.0), applies the nested body
transforms exactly as MuJoCo does, assigns the official MuJoCo material
colors, and renders a review set. Run headless:

    blender --background --python build_assembly.py -- \
        --md-dir /path/to/microduck_rl/src/mjlab_microduck/robot/microduck \
        --out /path/to/design/microduck-reference-v0

This is a reference/derivative assembly of Pollen Robotics' design for
study, not Knoll's original geometry. See THIRD-PARTY-NOTICES.md.
"""
import argparse
import csv
import os
import xml.etree.ElementTree as ET

import bpy
from mathutils import Matrix, Quaternion, Vector

argv = []
if "--" in __import__("sys").argv:
    argv = __import__("sys").argv[__import__("sys").argv.index("--") + 1:]
ap = argparse.ArgumentParser()
ap.add_argument("--md-dir", required=True, help="microduck robot dir (contains assets/ + robot_walk.xml)")
ap.add_argument("--out", required=True, help="output dir for renders + .blend")
ap.add_argument("--quick", action="store_true", help="hero render only")
args = ap.parse_args(argv)

MD = os.path.abspath(args.md_dir)
OUT = os.path.abspath(args.out)
IMG = os.path.join(OUT, "img")
XML = os.path.join(MD, "robot_walk.xml")
os.makedirs(IMG, exist_ok=True)

# ---------------------------------------------------------------- parse MJCF
tree = ET.parse(XML)
root_xml = tree.getroot()
worldbody = next(e for e in root_xml.iter("worldbody"))
meshdir = next(e for e in root_xml.iter("compiler")).get("meshdir", "assets")
ASSETS = os.path.join(MD, meshdir)

# Official MuJoCo material colors (sRGB floats).
MATS = {}
for m in root_xml.iter("material"):
    name = m.get("name")
    rgba = [float(x) for x in m.get("rgba", "0.7 0.7 0.7 1").split()]
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*rgba[:3], 1)
    rough = 0.35 if any(k in name for k in ("lens", "shell", "face")) else 0.6
    bsdf.inputs["Roughness"].default_value = rough
    if "lens" in name or "face" in name:
        bsdf.inputs["Metallic"].default_value = 0.25
    MATS[name] = mat


def q2m(q):
    """MuJoCo quat (w x y z) -> Blender rotation matrix."""
    return Quaternion([float(v) for v in q.split()]).to_matrix().to_4x4() if q else Matrix.Identity(4)


def xf(pos, quat):
    m = q2m(quat)
    m.translation = Vector(float(v) for v in (pos or "0 0 0").split())
    return m


PLACEMENTS = []   # (body_path, geom_name, mesh, material, world_matrix)
JOINTS = []       # (name, world_pos, world_axis, range)


def walk(body_el, parent_m, path):
    name = body_el.get("name")
    m = parent_m @ xf(body_el.get("pos"), body_el.get("quat"))
    for j in body_el.findall("joint"):
        if j.get("type") == "hinge":
            axis = Vector(float(v) for v in j.get("axis").split())
            JOINTS.append((j.get("name"), m.translation.copy(),
                           m.to_3x3() @ axis, j.get("range", "")))
    for g in body_el.findall("geom"):
        if g.get("class") != "visual" or not g.get("mesh"):
            continue
        gm = m @ xf(g.get("pos"), g.get("quat"))
        part = (g.get("name") or g.get("mesh"))
        PLACEMENTS.append((path + "/" + name, part, g.get("mesh"),
                           g.get("material", ""), gm))
    for sub in body_el.findall("body"):
        walk(sub, m, path + "/" + name)


for b in worldbody.findall("body"):
    walk(b, Matrix.Identity(4), "")

print(f"[parse] {len(PLACEMENTS)} visual placements, {len(JOINTS)} joints")

# ---------------------------------------------------------------- import STLs
# One bpy data-mesh per STL; linked objects per placement keeps the file editable.
mesh_cache = {}


def import_stl(mesh_name):
    if mesh_name in mesh_cache:
        return mesh_cache[mesh_name]
    path = os.path.join(ASSETS, mesh_name + ".stl")
    before = set(bpy.data.meshes)
    bpy.ops.wm.stl_import(filepath=path)
    new = [m for m in bpy.data.meshes if m not in before][0]
    imp = bpy.context.selected_objects[0]
    # onshape-to-robot exports meters; guard against mm-scale files.
    if max(imp.dimensions) > 2.0:
        new.transform(Matrix.Scale(0.001, 4))
    for o in list(bpy.context.selected_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    new.name = "STL_" + mesh_name
    mesh_cache[mesh_name] = new
    return new


col_robot = bpy.data.collections.new("MICRODUCK_ASSEMBLY")
bpy.context.scene.collection.children.link(col_robot)
objects = []
for i, (path, part, mesh, mat_name, gm) in enumerate(PLACEMENTS):
    ob = bpy.data.objects.new(f"{part}", mesh and import_stl(mesh))
    ob.matrix_world = gm
    if mat_name in MATS and not ob.data.materials:
        ob.data.materials.append(MATS[mat_name])
    elif mat_name in MATS:
        ob.data.materials.clear()
        ob.data.materials.append(MATS[mat_name])
    ob["source_body"] = path
    ob["source_mesh"] = mesh
    col_robot.objects.link(ob)
    objects.append(ob)

print(f"[import] {len(objects)} parts, {len(mesh_cache)} unique meshes")

# ---------------------------------------------------------------- joint markers
col_j = bpy.data.collections.new("JOINT_MARKERS")
bpy.context.scene.collection.children.link(col_j)
jm = bpy.data.materials.new("joint_marker")
jm.use_nodes = True
jb = next(n for n in jm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
jb.inputs["Base Color"].default_value = (1, 0.1, 0.1, 1)
jb.inputs["Emission Color"].default_value = (1, 0.15, 0.15, 1)
jb.inputs["Emission Strength"].default_value = 2.0
for name, pos, axis, rng in JOINTS:
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.004, depth=0.02)
    jm_ob = bpy.context.active_object
    jm_ob.name = "J_" + name
    for c in jm_ob.users_collection:
        c.objects.unlink(jm_ob)
    col_j.objects.link(jm_ob)
    jm_ob.location = pos
    jm_ob.rotation_mode = "QUATERNION"
    jm_ob.rotation_quaternion = axis.normalized().to_track_quat("Z", "Y")
    jm_ob.data.materials.append(jm)
    jm_ob["range_rad"] = rng

# ---------------------------------------------------------------- stage
bpy.ops.mesh.primitive_plane_add(size=4)
floor = bpy.context.active_object
floor.name = "FLOOR"
fm = bpy.data.materials.new("floor")
fm.use_nodes = True
fb = next(n for n in fm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
fb.inputs["Base Color"].default_value = (0.22, 0.22, 0.23, 1)
fb.inputs["Roughness"].default_value = 0.85
floor.data.materials.append(fm)

world = bpy.data.worlds.new("world") if not bpy.data.worlds else bpy.data.worlds[0]
bpy.context.scene.world = world
world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.02, 0.02, 0.025, 1)
bg.inputs[1].default_value = 0.3

for loc, energy, size in [((0.5, -0.6, 0.9), 90, 0.5), ((-0.7, 0.3, 0.6), 55, 0.6), ((0.2, 0.7, 0.3), 35, 0.4)]:
    d = bpy.data.lights.new("area", "AREA")
    d.energy = energy
    d.shape = "DISK"
    d.size = size
    o = bpy.data.objects.new("light", d)
    o.location = loc
    tgt = Vector((0, 0, 0.12))
    o.rotation_euler = (tgt - o.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1280
scene.render.resolution_y = 1440
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.look = "AgX - Medium High Contrast"

CAM = (0.42, -0.27, 0.25)
TARGET = Vector((0, 0, 0.11))


def cam(name, loc, ortho=None):
    d = bpy.data.cameras.new(name)
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = (TARGET - o.location).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        d.type = "ORTHO"
        d.ortho_scale = ortho
    else:
        d.lens = 50
    d.clip_start, d.clip_end = 0.01, 20
    scene.camera = o
    return o


def render(name):
    scene.render.filepath = os.path.join(IMG, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("[render]", name)


def show_joints(on):
    col_j.hide_render = not on
    for o in col_j.objects:
        o.hide_render = not on


show_joints(False)
cam("hero", CAM)
render("hero-3q")

if not args.quick:
    cam("front", (0.46, 0, 0.11), ortho=0.34)
    render("front")
    cam("side", (0, -0.46, 0.11), ortho=0.34)
    render("side")
    cam("rear", (-0.46, 0, 0.11), ortho=0.34)
    render("rear")
    cam("top", (0, 0, 0.5), ortho=0.34)
    render("top")
    cam("hero", CAM)
    show_joints(True)
    render("dof-map")
    show_joints(False)

    # Exploded view: push each part along its offset-from-centre direction.
    centres = {}
    for ob in objects:
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        c = sum(bb, Vector()) / 8
        centres[ob.name] = c
    centre = sum(centres.values(), Vector()) / len(centres)
    saved = {o.name: o.location.copy() for o in objects}
    for ob in objects:
        d = centres[ob.name] - centre
        if d.length < 1e-6:
            continue
        ob.location = saved[ob.name] + d.normalized() * (0.06 + 0.35 * min(d.length, 0.2))
    cam("exploded", (0.55, -0.45, 0.42), ortho=None) if False else cam("exploded", (0.55, -0.45, 0.42))
    render("exploded")
    for ob in objects:
        ob.location = saved[ob.name]

    # Detail: head assembly only (crop = tight camera on head).
    cam("head-detail", (0.3, -0.22, 0.28), ortho=0.13)
    render("head-detail")
    cam("feet-detail", (0.28, -0.2, 0.09), ortho=0.16)
    render("feet-detail")

# ---------------------------------------------------------------- manifest
with open(os.path.join(OUT, "parts-manifest.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["object", "source_body_path", "mesh_stl", "world_pos_m"])
    for ob in objects:
        p = ob.matrix_world.translation
        w.writerow([ob.name, ob["source_body"], ob["source_mesh"],
                    f"{p.x:.4f} {p.y:.4f} {p.z:.4f}"])
    w.writerow([])
    w.writerow(["JOINT", "world_pos_m", "", "range_rad"])
    for name, pos, axis, rng in JOINTS:
        w.writerow([name, f"{pos.x:.4f} {pos.y:.4f} {pos.z:.4f}", "", rng])

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "microduck-reference-v0.blend"))
print("[done]")
