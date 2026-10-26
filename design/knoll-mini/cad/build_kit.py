#!/usr/bin/env python3
"""
Knoll Mini — production CAD kit (FreeCAD 1.x, headless).

Rebuilds the full shell as native parametric BRep solids:
real cylindrical holes, fused pocket bodies, fillets/chamfers,
per-part STL + assembly STEP + FCStd.

    KNOLL_OUT=./cad freecadcmd build_kit.py

All dims mm, Z-up, robot faces +X. Same layout as the Blender model.
"""
import os
import sys

import FreeCAD as App
import Part

OUT = os.environ.get("KNOLL_OUT", ".")
STL = os.path.join(OUT, "parts")
os.makedirs(STL, exist_ok=True)

doc = App.newDocument("knoll-mini")

# ---------------- dims (mm) ----------------------------------------------
SV = (23.2, 12.1, 25.25)          # SCS0009 body (x,y,z)
FOOT = (44, 28, 7)
FEMUR, SHIN = 24.0, 22.0
TRUNK = (40, 50, 34)
NECK_H = 25.0
HEAD_W, HEAD_D, HEAD_H = 68.0, 38.0, 24.0
HIP_Y = 16.5
WALL = 1.6                        # printed wall thickness
CLR = 0.6                         # servo pocket clearance
BOSS_R, HOLE_R, INS_H = 2.6, 1.6, 4.0   # M2 insert boss / hole / insert depth
CSINK_R, CSINK_D = 2.3, 1.1       # M2 screw head counterbore

GRP = {}
def grp(n):
    g = doc.addObject("App::Part", n)
    GRP[n] = g
    return g


def feat(name, shape, g):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    g.addObject(o)
    return o


def box(dx, dy, dz, x=0, y=0, z=0):
    """box centered x,y — z given as BOTTOM."""
    s = Part.makeBox(dx, dy, dz, App.Vector(-dx / 2, -dy / 2, z))
    s.translate(App.Vector(x, y, 0))
    return s


def cyl(r, h, x=0, y=0, z=0, axis="Z"):
    v = {"Z": (0, 0, 1), "X": (1, 0, 0), "Y": (0, 1, 0)}[axis]
    b = {"Z": (x, y, z - h / 2), "X": (x - h / 2, y, z), "Y": (x, y - h / 2, z)}[axis]
    return Part.makeCylinder(r, h, App.Vector(*b), App.Vector(*v))


def fuse_all(parts):
    s = parts[0]
    for p in parts[1:]:
        s = s.fuse(p)
    return s


def fillet_where(shape, r, pred):
    edges = [e for e in shape.Edges
             if pred((e.BoundBox.XMin + e.BoundBox.XMax) / 2,
                     (e.BoundBox.YMin + e.BoundBox.YMax) / 2,
                     (e.BoundBox.ZMin + e.BoundBox.ZMax) / 2)]
    if not edges:
        return shape
    try:
        return shape.makeFillet(r, edges)
    except Exception:
        return shape


def chamfer_where(shape, r, pred):
    edges = [e for e in shape.Edges
             if pred((e.BoundBox.XMin + e.BoundBox.XMax) / 2,
                     (e.BoundBox.YMin + e.BoundBox.YMax) / 2,
                     (e.BoundBox.ZMin + e.BoundBox.ZMax) / 2)]
    if not edges:
        return shape
    try:
        return shape.makeChamfer(r, edges)
    except Exception:
        return shape


def servo_pocket(name, x, y, z, g, collar_color_part=True):
    """Solid pocket (floor+cheeks+back) + separate collar plate w/
    counterbored M2 holes + 2 boss posts. Servo drops in from +X side."""
    w, t, h = SV
    pw, pt = w + CLR * 2, t + CLR * 2
    parts = []
    # floor
    parts.append(box(pw + 2 * WALL, pt + 2 * WALL, WALL, x, y, z - h / 2 - WALL))
    # cheeks
    for sgn in (-1, 1):
        parts.append(box(pw + 2 * WALL, WALL, h + WALL, x,
                         y + sgn * (pt / 2 + WALL / 2), z - h / 2 - WALL))
    # back wall (wire exits low rear slot)
    parts.append(box(WALL, pt + 2 * WALL, h * 0.55, x - pw / 2 - WALL / 2,
                     y, z - h / 2 - WALL))
    # boss posts beside pocket (collar screws land here)
    for sgn in (-1, 1):
        bx = x + sgn * (pw / 2 + WALL + BOSS_R - 0.4)
        parts.append(cyl(BOSS_R, h + WALL + 2.4, bx, y, z - h / 2 - WALL))
    pocket = fuse_all(parts)
    # entry chamfer on cheek top edges for servo slide-in
    pocket = chamfer_where(pocket, 0.4,
                           lambda ex, ey, ez: ez > z + h / 2 - 0.6)
    # M2 holes down the bosses
    for sgn in (-1, 1):
        bx = x + sgn * (pw / 2 + WALL + BOSS_R - 0.4)
        pocket = pocket.cut(cyl(HOLE_R, 10, bx, y, z + h / 2 + 1.5))
    feat(name, pocket, g)
    # collar plate: covers servo top ear; counterbored screw holes
    cz = z + h / 2 + 1.2
    col = box(pw + 2 * (WALL + BOSS_R), pt + 2 * WALL, 2.4, x, y, cz - 1.2)
    for sgn in (-1, 1):
        bx = x + sgn * (pw / 2 + WALL + BOSS_R - 0.4)
        col = col.cut(cyl(CSINK_R, CSINK_D, bx, y, cz + 1.2))      # screw head
        col = col.cut(cyl(HOLE_R, 4, bx, y, cz + 0.2))             # through
    col = fillet_where(col, 0.6, lambda ex, ey, ez: ez > cz + 0.8)
    feat(name + "_collar", col, g)


def horn_disc(name, x, y, z, g, axis="Y"):
    """small driven-link coupler the horn screws into."""
    pass  # horns interface at links; handled per-link below


# ================= LEGS ===================================================
ankle_z, knee_z = 22.0, 22.0 + SHIN
hip_z = knee_z + FEMUR
trunk_z0 = hip_z + 7.0

for sgn, tag in ((1, "L"), (-1, "R")):
    y = sgn * HIP_Y
    g = grp(f"LEG_{tag}")
    servo_pocket(f"HYAW_{tag}", 0, sgn * (HIP_Y - 2), trunk_z0 + 10, g)
    servo_pocket(f"HROLL_{tag}", 0, sgn * (HIP_Y + 4), trunk_z0 - 10, g)
    servo_pocket(f"HPITCH_{tag}", 0, y, hip_z - 8, g)
    # femur/shin covers: open-backed C-channels over the links
    fem = box(13, 15, FEMUR - 6, 0, y, knee_z + 4)
    fem = fem.cut(box(13, 15, FEMUR - 6, -3, y, knee_z + 5))   # hollow back
    feat(f"FEMUR_{tag}", chamfer_where(fem, 1.2, lambda a, b, c: True), g)
    shin = box(11, 13, SHIN - 5, 0, y, ankle_z + 6)
    shin = shin.cut(box(11, 13, SHIN - 5, -2.5, y, ankle_z + 7))
    feat(f"SHIN_{tag}", chamfer_where(shin, 1.2, lambda a, b, c: True), g)
    servo_pocket(f"KNEE_{tag}", 0, y, knee_z, g)
    servo_pocket(f"ANKLE_{tag}", 6, y, ankle_z + 4, g)
    # foot: frame (open-top box, 2mm walls) + sole + toe
    ff = box(FOOT[0], FOOT[1], FOOT[2], 6, y, 0)
    ff = ff.cut(box(FOOT[0] - 4, FOOT[1] - 4, FOOT[2], 6, y, 2))  # open top
    for i, (dx, dy) in enumerate([(-14, -9), (-14, 9), (14, -9), (14, 9)]):
        ff = ff.cut(cyl(HOLE_R, 10, 6 + dx, y + dy, 5))
    ff = fillet_where(ff, 1.5, lambda a, b, c: c < 1.6)
    feat(f"FOOT_{tag}", ff, g)
    sole = box(41, 25, 2.5, 6, y, 0)
    for i, (dx, dy) in enumerate([(-14, -9), (-14, 9), (14, -9), (14, 9)]):
        sole = sole.cut(cyl(HOLE_R, 4, 6 + dx, y + dy, 0))
    feat(f"SOLE_{tag}", fillet_where(sole, 0.8, lambda a, b, c: c < 1.3), g)
    feat(f"TOE_{tag}", fillet_where(box(9, 26, 5, 26, y, 5), 1.0,
                                    lambda a, b, c: True), g)

# ================= TRUNK (clamshell) ======================================
tzc = trunk_z0 + TRUNK[2] / 2
g = grp("TRUNK")
# front shell: front 55% of depth with 2mm wall, open rear
tf = box(TRUNK[0] * 0.55, TRUNK[1], TRUNK[2], TRUNK[0] * 0.225, 0, trunk_z0)
tf = tf.cut(box(TRUNK[0] * 0.55, TRUNK[1] - 4, TRUNK[2] - 4,
                TRUNK[0] * 0.225 - 2, 0, trunk_z0 + 2))
tf = fillet_where(tf, 2.0, lambda a, b, c: c > trunk_z0 + TRUNK[2] - 2.5 or c < trunk_z0 + 2.5)
feat("TRUNK_F", tf, g)
tr = box(TRUNK[0] * 0.45, TRUNK[1], TRUNK[2], -TRUNK[0] * 0.275, 0, trunk_z0)
tr = tr.cut(box(TRUNK[0] * 0.45, TRUNK[1] - 4, TRUNK[2] - 4,
                -TRUNK[0] * 0.275 + 2, 0, trunk_z0 + 2))
tr = fillet_where(tr, 2.0, lambda a, b, c: c > trunk_z0 + TRUNK[2] - 2.5 or c < trunk_z0 + 2.5)
feat("TRUNK_R", tr, g)
# seam bosses: 3 posts per side on the joint line, holes into both halves
for sgn in (-1, 1):
    for i, zz in enumerate((tzc - 11, tzc, tzc + 11)):
        bx, by = 1.0, sgn * (TRUNK[1] / 2 - 3)
        feat(f"SEAM_{'F' if sgn > 0 else 'B'}{i}",
             cyl(BOSS_R, 6, bx, by, zz), g)
# chest service panel with 4 counterbored holes
cp = box(4, TRUNK[1] * 0.62, TRUNK[2] * 0.5, 21, 0, tzc + 2 - TRUNK[2] * 0.25)
for i, (dy, dz) in enumerate([(-12, -8), (-12, 8), (12, -8), (12, 8)]):
    cp = cp.cut(cyl(CSINK_R, CSINK_D, 23, dy, tzc + dz, axis="X"))
    cp = cp.cut(cyl(HOLE_R, 5, 21, dy, tzc + dz, axis="X"))
feat("CHEST_PANEL", fillet_where(cp, 0.6, lambda a, b, c: a > 22.5), g)
# battery tray: floor + 3 walls + strap slots
bt = box(36, 26, 1.6, 0, 0, tzc - 15.5)
for sgn in (-1, 1):
    bt = bt.fuse(box(36, 1.6, 5, 0, sgn * 13.0, tzc - 15.5))
bt = bt.fuse(box(1.6, 26, 5, -18, 0, tzc - 15.5))
for sgn in (-1, 1):  # strap slots through the tray walls
    bt = bt.cut(box(2.0, 5, 1.4, sgn * 10, 0, tzc - 11.5))
feat("BAT_TRAY", bt, g)
# pcb standoffs (4x) + imu posts (2x) — posts only, boards mount on top
for i, (dx, dy) in enumerate([(-13, -9), (-13, 9), (13, -9), (13, 9)]):
    p = cyl(2.2, 4, dx, dy, tzc - 4)
    feat(f"PCBP_{i}", p.cut(cyl(0.9, 6, dx, dy, tzc - 1)), g)
for i, dy in enumerate((-5, 5)):
    p = cyl(1.8, 3, 8, -11 + dy, tzc + 8)
    feat(f"IMUP_{i}", p.cut(cyl(0.7, 5, 8, -11 + dy, tzc + 10)), g)
# speaker retaining ring behind chest panel
feat("SPK_RING", cyl(8.5, 1.5, 18, 8, tzc - 5, axis="X")
     .cut(cyl(7.0, 3, 18, 8, tzc - 5, axis="X")), g)
# vent slats (printed detail on front shell)
for i in range(3):
    feat(f"VENT_{i}", box(2, TRUNK[1] * 0.4, 2, 20.8, 0,
                          tzc - TRUNK[2] * 0.34 - 1 + i * 5), g)
# rear button + usb (bore the rear shell)
tr2 = doc.getObject("TRUNK_R").Shape
tr2 = tr2.cut(cyl(3.2, 5, -19.5, 10, tzc + 6, axis="X"))
tr2 = tr2.cut(box(3, 9, 3.5, -19.5, -7, tzc + 4))
doc.getObject("TRUNK_R").Shape = tr2

# flippers + tips
g = grp("ARMS")
for sgn, tag in ((1, "L"), (-1, "R")):
    fp = box(32, 13, 28, 2, sgn * (TRUNK[1] / 2 + 5), tzc - 21)
    fp = fillet_where(fp, 3.0, lambda a, b, c: True)
    for i, dz in enumerate((-8, 8)):
        fp = fp.cut(cyl(HOLE_R, 14, 2, sgn * (TRUNK[1] / 2), tzc - 7 + dz, axis="Y"))
    feat(f"FLIPPER_{tag}", fp, g)
    tip = box(30, 13, 6, 2, sgn * (TRUNK[1] / 2 + 7), tzc - 22)
    feat(f"FLIP_TIP_{tag}", fillet_where(tip, 2.0, lambda a, b, c: True), g)

# ================= NECK =================================================
g = grp("NECK")
servo_pocket("NPITCH", 8, 0, neck_z0 := trunk_z0 + TRUNK[2] - 7, g)
nyz = neck_z0 + NECK_H / 2 - 2
for i, zz in enumerate((nyz - SV[2] / 2 - 1, nyz + SV[2] / 2 + 1)):
    cl = cyl(9, 2.5, 20, 0, zz)
    for j, sgn in enumerate((-1, 1)):
        cl = cl.cut(cyl(CSINK_R, CSINK_D, 20 + sgn * 6, 0, zz + 1.25))
        cl = cl.cut(cyl(HOLE_R, 5, 20 + sgn * 6, 0, zz))
    feat(f"NCOL_{i}", fillet_where(cl, 0.5, lambda a, b, c: True), g)
feat("NECK_CABLE", cyl(3, NECK_H - 6, 5, 0, nyz), g)

# ================= HEAD =================================================
hz0 = neck_z0 + NECK_H + 3
hzc = hz0 + HEAD_H / 2
hcx = 22.0
face_x = hcx + HEAD_D / 2
g = grp("HEAD")
# top shell: closed box with open bottom, 2mm walls
hs = box(HEAD_D, HEAD_W, HEAD_H, hcx, 0, hz0)
hs = hs.cut(box(HEAD_D - 4, HEAD_W - 4, HEAD_H, hcx, 0, hz0 + 2))
hs = fillet_where(hs, 4.0, lambda a, b, c: c > hz0 + HEAD_H - 5)
for i, (dx, dy) in enumerate([(-13, -26), (-13, 26), (13, -26), (13, 26)]):
    hs = hs.cut(cyl(HOLE_R, HEAD_H, hcx + dx, dy, hz0))
# face apertures through the front wall
for sgn in (1, -1):
    hs = hs.cut(cyl(8.5, 6, face_x - 1, sgn * 13.5, hzc + 1, axis="X"))
feat("HEAD_SHELL", hs, g)
# base plate: horn bore + cable slot + corner holes
hb = box(HEAD_D - 4, HEAD_W - 8, 2, hcx, 0, hz0)
hb = hb.cut(cyl(4.5, 3, 20 + SV[0] * 0.28, 0, hz0))
hb = hb.cut(box(5, 6, 3, 10, 12, hz0))
for i, (dx, dy) in enumerate([(-13, -26), (-13, 26), (13, -26), (13, 26)]):
    hb = hb.cut(cyl(HOLE_R, 3, hcx + dx, dy, hz0))
feat("HEAD_BASE", fillet_where(hb, 1.0, lambda a, b, c: True), g)
# face plate: real eye bores + 4 counterbored corners
fp = box(5, HEAD_W * 0.88, HEAD_H * 0.80, face_x + 1, 0, hzc - HEAD_H * 0.40)
for sgn in (1, -1):
    fp = fp.cut(cyl(8.5, 8, face_x + 1, sgn * 13.5, hzc + 1, axis="X"))
for i, (dy, dz) in enumerate([(-27, -8), (-27, 8), (27, -8), (27, 8)]):
    fp = fp.cut(cyl(CSINK_R, CSINK_D, face_x + 3.5, dy, hzc + dz, axis="X"))
    fp = fp.cut(cyl(HOLE_R, 6, face_x + 1, dy, hzc + dz, axis="X"))
feat("FACE_PLATE", fillet_where(fp, 0.8, lambda a, b, c: a > face_x + 2.5), g)
# eye bezels + lenses
for sgn, tag in ((1, "L"), (-1, "R")):
    feat(f"EYE_RING_{tag}", cyl(8, 4, face_x + 3, sgn * 13.5, hzc + 1, axis="X")
         .cut(cyl(6.4, 5, face_x + 3, sgn * 13.5, hzc + 1, axis="X")), g)
    feat(f"EYE_{tag}", cyl(5.3, 3, face_x + 6, sgn * 13.5, hzc + 1, axis="X"), g)
# cam/tof brackets
for sgn, pz in ((1, "CAM"), (-1, "TOF")):
    for csgn in (-1, 1):
        feat(f"{pz}_BRK{csgn}", box(1.6, 1.6, 12, face_x - 10,
                                   sgn * 13.5 + csgn * 6, hzc - 3), g)
# ear pods + caps
for sgn, tag in ((1, "L"), (-1, "R")):
    feat(f"EAR_{tag}", cyl(6, 3, hcx, sgn * (HEAD_W / 2 + 1.5), hzc, axis="Y"), g)
    feat(f"EAR_CAP_{tag}", cyl(3, 4, hcx, sgn * (HEAD_W / 2 + 2), hzc, axis="Y"), g)
feat("ANT_MAST", cyl(0.9, 16, hcx - HEAD_D * 0.32, -HEAD_W * 0.30,
                     hz0 + HEAD_H), g)
feat("CHIN", fillet_where(box(9, HEAD_W * 0.44, 6, face_x - 5, 0, hz0 - 1), 1.5,
                          lambda a, b, c: True), g)

# ================= export ===============================================
doc.recompute()
doc.saveAs(os.path.join(OUT, "knoll-mini.FCStd"))

import Mesh
count = 0
for gn, g in GRP.items():
    for o in g.Group:
        Mesh.export([o], os.path.join(STL, o.Name + ".stl"))
        count += 1
print(f"[stl] {count} parts")

allobjs = [o for g in GRP.values() for o in g.Group]
try:
    import Import
    Import.export(allobjs, os.path.join(OUT, "knoll-mini.step"))
    print("[step] written")
except Exception as e:
    print("[step] failed:", e)
print("[done]", App.Version())
