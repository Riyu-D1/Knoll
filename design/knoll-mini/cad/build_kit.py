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
FOOT = (46, 28, 7)
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
    # boss posts: pocket floor -> collar bottom (flush), embedded in cheeks
    for sgn in (-1, 1):
        bx = x + sgn * (pw / 2 + WALL + BOSS_R - 2.0)
        parts.append(cyl(BOSS_R, h + WALL, bx, y, z - 0.8))
    pocket = fuse_all(parts)
    # entry chamfer on cheek top edges for servo slide-in
    pocket = chamfer_where(pocket, 0.4,
                           lambda ex, ey, ez: ez > z + h / 2 - 0.6)
    # M2 holes down the bosses
    for sgn in (-1, 1):
        bx = x + sgn * (pw / 2 + WALL + BOSS_R - 2.0)
        pocket = pocket.cut(cyl(HOLE_R, 10, bx, y, z + h / 2 + 1.5))
    feat(name, pocket, g)
    # collar plate: covers servo top ear; counterbored screw holes
    cz = z + h / 2 + 1.2
    col = box(pw + 2 * (WALL + BOSS_R), pt + 2 * WALL, 2.4, x, y, cz - 1.2)
    for sgn in (-1, 1):
        bx = x + sgn * (pw / 2 + WALL + BOSS_R - 2.0)
        col = col.cut(cyl(CSINK_R, CSINK_D, bx, y, cz + 1.2))      # screw head
        col = col.cut(cyl(HOLE_R, 4, bx, y, cz + 0.2))             # through
    col = fillet_where(col, 0.6, lambda ex, ey, ez: ez > cz + 0.8)
    feat(name + "_collar", col, g)


def horn_disc(name, x, y, z, g, axis="Y"):
    """small driven-link coupler the horn screws into."""
    pass  # horns interface at links; handled per-link below


# ================= LEGS ===================================================
# 4 DOF per leg — verification showed 5 x 29 mm pocket stations cannot fit
# the ~68 mm leg column; ankle is a passive compliant sole (rubber).
# Layout: two x-staggered pocket columns so neighbours clear each other.
knee_z = 30.0
hip_z = 68.0
trunk_z0 = hip_z + 7.0
COL_A, COL_B = -16.0, 20.0          # rear column / front column (Δx=36 clears bosses)

for sgn, tag in ((1, "L"), (-1, "R")):
    y = sgn * HIP_Y
    g = grp(f"LEG_{tag}")
    py = sgn * (HIP_Y - 2.5)        # leg pockets inboard of foot centre
    servo_pocket(f"HYAW_{tag}",   COL_A, py, 60.0, g)  # under trunk floor
    servo_pocket(f"HPITCH_{tag}", COL_A, py, 30.0, g)  # same column, below
    servo_pocket(f"HROLL_{tag}",  COL_B, py, 60.0, g)  # front column top
    servo_pocket(f"KNEE_{tag}",   COL_B, py, 30.0, g)  # front column low
    # shin link plate: foot top -> knee pocket floor (passive link zone)
    feat(f"SHIN_{tag}", fillet_where(box(8, 14, 8, COL_B - 8, y, 7), 1.0,
                                     lambda a, b, c: True), g)
    # foot: hollow frame (2mm walls + bottom plate) + sole bolted under + toe
    ff = box(FOOT[0], FOOT[1], FOOT[2], 10, y, 0)
    ff = ff.cut(box(FOOT[0] - 4, FOOT[1] - 4, FOOT[2], 10, y, 2))  # open top
    ff = ff.fuse(box(4, 18, 3, 29.5, y, 2))            # toe-screw landing pad
    for i, (dx, dy) in enumerate([(-14, -9), (-14, 9), (14, -9), (14, 9)]):
        ff = ff.cut(cyl(0.9, 4, 10 + dx, y + dy, 0))    # M2 thread into floor
    for i, dy in enumerate((-7, 7)):
        ff = ff.cut(cyl(0.9, 6, 30, y + dy, 3.5, axis="X"))  # toe screw thread
    ff = fillet_where(ff, 1.5, lambda a, b, c: c < 1.6)
    feat(f"FOOT_{tag}", ff, g)
    sole = box(FOOT[0] - 5, FOOT[1] - 5, 2.4, 10, y, -2.4)  # bolts under frame
    for i, (dx, dy) in enumerate([(-14, -9), (-14, 9), (14, -9), (14, 9)]):
        sole = sole.cut(cyl(HOLE_R, 4, 10 + dx, y + dy, -1.2))
    feat(f"SOLE_{tag}", fillet_where(sole, 0.8, lambda a, b, c: c < 1.3), g)
    toe = box(9, 26, 5, 37.5, y, 1)
    for i, dy in enumerate((-7, 7)):
        toe = toe.cut(cyl(CSINK_R, CSINK_D, 42, y + dy, 3.5, axis="X"))
        toe = toe.cut(cyl(HOLE_R, 10, 37.5, y + dy, 3.5, axis="X"))
    feat(f"TOE_{tag}", fillet_where(toe, 1.0,
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
# seam joinery: front-shell lip tabs slide inside the rear shell's side
# walls; M2 screws pass through rear wall + tab (hole + nut/self-tap)
for sgn in (-1, 1):
    tab = box(4, 1.2, 14, -4, sgn * (TRUNK[1] / 2 - 2.6), tzc - 7)
    tf = tf.fuse(tab)
    for i, zz in enumerate((tzc - 4, tzc + 4)):
        tf = tf.cut(cyl(HOLE_R, 4, -4, sgn * (TRUNK[1] / 2 - 2.6), zz, axis="Y"))
        tr = tr.cut(cyl(HOLE_R, 7, -4, sgn * (TRUNK[1] / 2 - 1), zz, axis="Y"))
# chest panel: posts cantilever from wall inner face, outboard of the tray
for i, (dy, dz) in enumerate([(-15, -4), (-15, 4), (15, -4), (15, 4)]):
    tf = tf.fuse(cyl(2.2, 3, 16.75, dy, tzc + dz, axis="X"))
    tf = tf.cut(cyl(HOLE_R, 6, 18, dy, tzc + dz, axis="X"))
cp = box(4, TRUNK[1] * 0.72, 15, 22, 0, tzc - 6)
for i, (dy, dz) in enumerate([(-15, -4), (-15, 4), (15, -4), (15, 4)]):
    cp = cp.cut(cyl(CSINK_R, CSINK_D, 24, dy, tzc + dz, axis="X"))
    cp = cp.cut(cyl(HOLE_R, 5, 22, dy, tzc + dz, axis="X"))
feat("CHEST_PANEL", fillet_where(cp, 0.6, lambda a, b, c: a > 23.5), g)
# floor openings over the hip pockets (poke-through + servo wire pass)
for sgn in (-1, 1):
    tf = tf.cut(box(40, 17.8, 8, COL_B - 2, sgn * (HIP_Y - 2.5), trunk_z0 - 2))
    tr = tr.cut(box(36, 17.8, 8, COL_A, sgn * (HIP_Y - 2.5), trunk_z0 - 2))
# battery tray fused into front shell floor + strap slots in side walls
tf = tf.fuse(box(36, 26, 1.6, 0, 0, trunk_z0 + 2))
for sgn in (-1, 1):
    tf = tf.fuse(box(36, 1.6, 5, 0, sgn * 13.3, trunk_z0 + 2))
    tf = tf.cut(box(2.0, 1.8, 1.4, 10, sgn * 13.3, trunk_z0 + 3))
tf = tf.fuse(box(1.6, 26, 5, -17, 0, trunk_z0 + 2))
# speaker ring fused behind the panel zone (bore seats a d16 speaker)
tf = tf.fuse(cyl(9.5, 1.5, 18.6, 0, tzc - 2, axis="X"))
tf = tf.cut(cyl(8.2, 4, 18.6, 0, tzc - 2, axis="X"))
# flipper screw bosses on the side-wall inner faces
for sgn in (-1, 1):
    for i, dz in enumerate((-8, 8)):
        tf = tf.fuse(cyl(BOSS_R, 4, 2, sgn * (TRUNK[1] / 2 - 2), tzc - 7 + dz, axis="Y"))
        tf = tf.cut(cyl(0.9, 8, 2, sgn * (TRUNK[1] / 2 - 2), tzc - 7 + dz, axis="Y"))
# vents: real through-slots in the front wall
for i in range(3):
    tf = tf.cut(box(4, TRUNK[1] * 0.4, 2, 20, 0,
                    tzc - TRUNK[2] * 0.34 - 1 + i * 5))
doc.getObject("TRUNK_F").Shape = tf
# pcb standoffs + imu posts fused into the REAR inner wall (vertical board)
for i, (dy, dz) in enumerate([(-11, -6), (-11, 6), (11, -6), (11, 6)]):
    tr = tr.fuse(cyl(2.2, 4, -16.5, dy, tzc + dz, axis="X"))
    tr = tr.cut(cyl(0.9, 6, -16.5, dy, tzc + dz, axis="X"))
for i, dy in enumerate((-5, 5)):
    tr = tr.fuse(cyl(1.8, 3, -16.5, -11 + dy, tzc - 8, axis="X"))
    tr = tr.cut(cyl(0.7, 5, -16.5, -11 + dy, tzc - 8, axis="X"))
# rear button + usb bores
tr = tr.cut(cyl(3.2, 5, -19.5, 10, tzc + 6, axis="X"))
tr = tr.cut(box(3, 9, 3.5, -19.5, -7, tzc + 4))
doc.getObject("TRUNK_R").Shape = tr
# opening in trunk top for the NPITCH pocket + neck column (both halves)
tf = doc.getObject("TRUNK_F").Shape
tf = tf.cut(box(39, 19, 10, 1.5, 0, trunk_z0 + TRUNK[2] - 9))
doc.getObject("TRUNK_F").Shape = tf
tr = doc.getObject("TRUNK_R").Shape
tr = tr.cut(box(39, 19, 10, 1.5, 0, trunk_z0 + TRUNK[2] - 9))
doc.getObject("TRUNK_R").Shape = tr

# flippers + tips
g = grp("ARMS")
for sgn, tag in ((1, "L"), (-1, "R")):
    fp = box(32, 13, 28, 2, sgn * (TRUNK[1] / 2 + 6.65), tzc - 21)
    fp = fillet_where(fp, 3.0, lambda a, b, c: True)
    for i, dz in enumerate((-8, 8)):
        fp = fp.cut(cyl(HOLE_R, 23, 2, sgn * (TRUNK[1] / 2 + 3),
                        tzc - 7 + dz, axis="Y"))
    for i, tx in enumerate((-8, 12)):
        fp = fp.cut(cyl(0.9, 6, tx, sgn * (TRUNK[1] / 2 + 11), tzc - 20,
                        axis="Y"))                       # tip screw thread
    feat(f"FLIPPER_{tag}", fp, g)
    tip = box(30, 13, 6, 2, sgn * (TRUNK[1] / 2 + 19.7), tzc - 20)
    for i, tx in enumerate((-8, 12)):
        tip = tip.cut(cyl(CSINK_R, CSINK_D, tx,
                          sgn * (TRUNK[1] / 2 + 26.2), tzc - 20, axis="Y"))
        tip = tip.cut(cyl(HOLE_R, 14, tx, sgn * (TRUNK[1] / 2 + 19.7),
                          tzc - 20, axis="Y"))
    feat(f"FLIP_TIP_{tag}", fillet_where(tip, 2.0, lambda a, b, c: True), g)

# ================= NECK =================================================
g = grp("NECK")
servo_pocket("NPITCH", 0, 0, neck_z0 := trunk_z0 + TRUNK[2] - 7, g)
nyz = neck_z0 + 15
for i, zz in enumerate((nyz - SV[2] / 2 - 1, nyz + SV[2] / 2 + 1)):
    cl = cyl(9, 2.5, 26.5, 0, zz)
    cl = cl.cut(cyl(2.5, 4, 26.5, 0, zz))        # cable pass-through bore
    for j, sgn in enumerate((-1, 1)):
        cl = cl.cut(cyl(CSINK_R, CSINK_D, 26.5 + sgn * 6, 0,
                        zz + (1.25 if i else -1.25)))
        cl = cl.cut(cyl(HOLE_R, 5, 26.5 + sgn * 6, 0, zz))
    feat(f"NCOL_{i}", fillet_where(cl, 0.5, lambda a, b, c: True), g)

# ================= HEAD =================================================
hz0 = neck_z0 + NECK_H + 5
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
# face apertures + face-plate screw posts (fused) + wall bores
for sgn in (1, -1):
    hs = hs.cut(cyl(8.5, 6, face_x - 1, sgn * 13.5, hzc + 1, axis="X"))
for i, (dy, dz) in enumerate([(-27, -8), (-27, 8), (27, -8), (27, 8)]):
    hs = hs.fuse(cyl(1.8, 3.5, face_x - 3.5, dy, hzc + dz, axis="X"))
    hs = hs.cut(cyl(HOLE_R, 8, face_x - 2, dy, hzc + dz, axis="X"))
feat("HEAD_SHELL", hs, g)
# base plate: sits inside the shell cavity; horn bore + cable slot + holes
hb = box(HEAD_D - 11, HEAD_W - 9, 2, hcx, 0, hz0 + 3)
hb = hb.cut(cyl(5.5, 3, 26.5 + SV[0] * 0.28, 0, hz0 + 3))  # horn disc clearance
hb = hb.cut(box(6, 7, 3, 26.5, 0, hz0 + 3))               # cable slot (collar bore line)
for i, (dx, dy) in enumerate([(-13, -26), (-13, 26), (13, -26), (13, 26)]):
    hb = hb.cut(cyl(HOLE_R, 3, hcx + dx, dy, hz0 + 3))
feat("HEAD_BASE", fillet_where(hb, 1.0, lambda a, b, c: True), g)
# face plate: sits ON the shell front face; real eye bores + counterbores
fp = box(5, HEAD_W * 0.88, HEAD_H * 0.80, face_x + 2.7, 0, hzc - HEAD_H * 0.40)
for sgn in (1, -1):
    fp = fp.cut(cyl(8.5, 8, face_x + 2.7, sgn * 13.5, hzc + 1, axis="X"))
for i, (dy, dz) in enumerate([(-27, -8), (-27, 8), (27, -8), (27, 8)]):
    fp = fp.cut(cyl(CSINK_R, CSINK_D, face_x + 5.2, dy, hzc + dz, axis="X"))
    fp = fp.cut(cyl(HOLE_R, 6, face_x + 2.7, dy, hzc + dz, axis="X"))
feat("FACE_PLATE", fillet_where(fp, 0.8, lambda a, b, c: a > face_x + 4.2), g)
# eye bezels inside the apertures + lens domes flush with plate face
for sgn, tag in ((1, "L"), (-1, "R")):
    feat(f"EYE_RING_{tag}", cyl(8, 4, face_x + 3.5, sgn * 13.5, hzc + 1, axis="X")
         .cut(cyl(6.4, 5, face_x + 3.5, sgn * 13.5, hzc + 1, axis="X")), g)
    feat(f"EYE_{tag}", cyl(5.3, 3, face_x + 4.7, sgn * 13.5, hzc + 1, axis="X"), g)
# cam/tof brackets
for sgn, pz in ((1, "CAM"), (-1, "TOF")):
    for csgn in (-1, 1):
        feat(f"{pz}_BRK{csgn}", box(1.6, 1.6, 12, face_x - 10,
                                   sgn * 13.5 + csgn * 6, hzc - 3), g)
# ear pods + outer face caps
for sgn, tag in ((1, "L"), (-1, "R")):
    feat(f"EAR_{tag}", cyl(6, 3, hcx, sgn * (HEAD_W / 2 + 1.5), hzc, axis="Y"), g)
    feat(f"EAR_CAP_{tag}", cyl(3, 4, hcx, sgn * (HEAD_W / 2 + 5), hzc, axis="Y"), g)
feat("ANT_MAST", cyl(0.9, 16, hcx - HEAD_D * 0.32, -HEAD_W * 0.30,
                     hz0 + HEAD_H), g)
feat("CHIN", fillet_where(box(9, HEAD_W * 0.44, 7, face_x - 1, 0, hz0 - 7), 1.5,
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
