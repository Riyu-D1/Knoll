#!/usr/bin/env python3
"""
Microduck CAD assembly — FreeCAD edition.

Builds an editable CAD document from the official MJCF export in
pollen-robotics/microduck_rl (Apache-2.0). Assembles the robot into
App::Part containers that mirror the MJCF body tree (hip_yaw -> ... ->
ankle, neck -> head), so each kinematic body can be re-posed by editing
its Placement. Joints get red datum cylinders in a JOINTS container.

Modes:
  meshes  (default) Mesh::Feature objects — exact STL geometry at mm
                    scale, small .FCStd. This is the committed reference;
                    solidify individual parts on demand (Part workbench).
  solids            Full BRep conversion (mesh->shape->solid). Slow and
                    large; used to emit the STEP file. Combine with
                    --decimate R to keep the STEP reasonable.

Outputs (per --out dir):
  microduck-assembly.FCStd   native editable document
  microduck-assembly.step    STEP AP214 mm, assembly structure (solids mode)

Run headless:
  freecadcmd build_cad.py -- --md-dir <microduck robot dir> --out <dir> \
      [--mode meshes|solids] [--decimate 0.7]

Derivative of Pollen Robotics' design — see ../THIRD-PARTY-NOTICES.md.
"""
import os
import sys
import xml.etree.ElementTree as ET

import FreeCAD as fc
import Mesh
import Part
import Import

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


MD = arg("--md-dir")
OUT = arg("--out", ".")
MODE = arg("--mode", "meshes")
DECIMATE = float(arg("--decimate", "0"))
MM = 1000.0  # MJCF metres -> CAD millimetres

tree = ET.parse(os.path.join(MD, "robot_walk.xml"))
root_xml = tree.getroot()
worldbody = next(e for e in root_xml.iter("worldbody"))
meshdir = next(e for e in root_xml.iter("compiler")).get("meshdir", "assets")
ASSETS = os.path.join(MD, meshdir)


def quat_mjcf_to_fc(q):
    if not q:
        return fc.Rotation()
    w, x, y, z = (float(v) for v in q.split())
    return fc.Rotation(x, y, z, w)


def placement(pos, quat):
    p = [float(v) * MM for v in (pos or "0 0 0").split()]
    return fc.Placement(fc.Vector(*p), quat_mjcf_to_fc(quat))


BODIES = []   # (name, world_pl, [(part_name, mesh, local_pl)])
JOINTS = []   # (name, world_pl, axis_local, range)


def walk(el, parent_pl):
    name = el.get("name")
    pl = parent_pl.multiply(placement(el.get("pos"), el.get("quat")))
    parts = [(g.get("name") or g.get("mesh"), g.get("mesh"),
              placement(g.get("pos"), g.get("quat")))
             for g in el.findall("geom")
             if g.get("class") == "visual" and g.get("mesh")]
    BODIES.append((name, pl, parts))
    for j in el.findall("joint"):
        if j.get("type") == "hinge":
            JOINTS.append((j.get("name"), pl,
                           [float(v) for v in j.get("axis").split()],
                           j.get("range", "")))
    for sub in el.findall("body"):
        walk(sub, pl)


for b in worldbody.findall("body"):
    walk(b, fc.Placement())

nparts = sum(len(p) for _, _, p in BODIES)
print(f"[parse] {len(BODIES)} bodies, {nparts} parts, {len(JOINTS)} joints")

doc = fc.newDocument("microduck")
SCALE = fc.Matrix()
SCALE.A11 = SCALE.A22 = SCALE.A33 = MM

mesh_cache = {}
shape_cache = {}


def part_mesh(name):
    if name not in mesh_cache:
        m = Mesh.read(os.path.join(ASSETS, name + ".stl"))
        m.transform(SCALE)
        mesh_cache[name] = m
    return mesh_cache[name]


def part_shape(name):
    if name in shape_cache:
        return shape_cache[name]
    m = Mesh.read(os.path.join(ASSETS, name + ".stl"))
    m.transform(SCALE)
    if DECIMATE > 0:
        m.decimate(0.5, DECIMATE)
    shp = Part.Shape()
    shp.makeShapeFromMesh(m.Topology, 0.05)
    if shp.Shells and shp.isClosed():
        try:
            shp = Part.makeSolid(shp.Shells[0])
        except Exception:
            pass  # keep sewn shell if it won't solidify
    shape_cache[name] = shp
    return shp


def fc_name(s):
    return "".join(c if c.isalnum() or c == "_" else "_" for c in s)


def container(name, pl):
    obj = doc.addObject("App::Part", fc_name(name))
    obj.Label = name
    obj.Placement = pl
    return obj


top = container("microduck", fc.Placement())
objtype = "Mesh::Feature" if MODE == "meshes" else "Part::Feature"

for body_name, bpl, parts in BODIES:
    if not parts:
        continue
    bcont = container("body_" + body_name, bpl)
    top.addObject(bcont)
    for part_name, mesh_name, gpl in parts:
        o = doc.addObject(objtype, fc_name("p_" + part_name))
        o.Label = part_name
        if MODE == "meshes":
            o.Mesh = Mesh.Mesh(part_mesh(mesh_name))
        else:
            o.Shape = part_shape(mesh_name)
        o.Placement = gpl
        bcont.addObject(o)

jcont = container("JOINTS", fc.Placement())
top.addObject(jcont)
for jname, jpl, axis, rng in JOINTS:
    d = jpl.Rotation.multVec(fc.Vector(*axis)).normalize()
    base = jpl.Base - d.multiply(4.0)
    o = doc.addObject("Part::Feature", fc_name("J_" + jname))
    o.Label = f"J_{jname} [{rng}]"
    o.Shape = Part.makeCylinder(2.0, 8.0, base, d)
    jcont.addObject(o)

doc.recompute()

mins = [1e9] * 3
maxs = [-1e9] * 3
for body_name, bpl, parts in BODIES:
    for _, mesh_name, gpl in parts:
        m2 = Mesh.Mesh(part_mesh(mesh_name))
        m2.transform(bpl.multiply(gpl).toMatrix())
        b = m2.BoundBox
        mins[0], maxs[0] = min(mins[0], b.XMin), max(maxs[0], b.XMax)
        mins[1], maxs[1] = min(mins[1], b.YMin), max(maxs[1], b.YMax)
        mins[2], maxs[2] = min(mins[2], b.ZMin), max(maxs[2], b.ZMax)
print(f"[bbox] X {mins[0]:.1f}..{maxs[0]:.1f}  Y {mins[1]:.1f}..{maxs[1]:.1f}"
      f"  Z {mins[2]:.1f}..{maxs[2]:.1f}  mm")

fcstd = os.path.join(OUT, f"microduck-assembly-{MODE}.FCStd")
doc.saveAs(fcstd)
print(f"[saved] {fcstd}")
if MODE == "solids":
    step = os.path.join(OUT, "microduck-assembly.step")
    Import.export([top], step)
    print(f"[saved] {step}")
print("[done]")
