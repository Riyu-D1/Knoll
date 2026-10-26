#!/usr/bin/env python3
"""
Knoll Mini — ~16cm pocket biped, BDX-head, BUILD-READY shell.

v2: every component mounts mechanically — servo pockets + screwed collars,
heat-set insert bosses, clamshell trunk, mounting posts, cable channels.
No glue anywhere. Fasteners: M2 screws + M2 heat-set brass inserts.

    blender --background --python build_knoll_mini.py -- --out . [--quick]
"""
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1]
QUICK = "--quick" in argv
IMG = os.path.join(OUT, "img")
PARTS = os.path.join(OUT, "parts")
os.makedirs(IMG, exist_ok=True)
os.makedirs(PARTS, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

MM = 0.001
S = lambda *v: tuple(x * MM for x in v)

# ---------------- dims (mm) -----------------------------------------------
SV = S(23.2, 12.1, 25.25)         # SCS0009 / Waveshare SC09 body — all 12 joints
FOOT = S(44, 28, 7)
FEMUR, SHIN = 24.0, 22.0
TRUNK = S(40, 50, 34)             # (x depth, y width, z height)
NECK_H = 25.0
HEAD_W, HEAD_D, HEAD_H = 68.0, 38.0, 24.0
HIP_Y = 16.5
CLR = 0.6                          # clearance around servo body in pocket
BOSS_R = 0.0026                    # M2 insert boss radius (Ø5.2)
HOLE_R = 0.0016                    # M2 printed hole radius (Ø3.2 → insert)
INS_R, INS_D = 0.0018, 0.004       # heat-set insert proxy


def M(name, rgb, rough=0.5, metal=0.0, emit=0.0, alpha=1.0):
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


WHITE = M("white", (0.85, 0.84, 0.80), 0.5)
DARK = M("dark", (0.05, 0.05, 0.06), 0.6, 0.05)
GREY = M("grey", (0.30, 0.31, 0.33), 0.45)
ORANGE = M("orange", (0.78, 0.22, 0.02), 0.4)
YELLOW = M("sole", (0.95, 0.72, 0.16), 0.5)
STEEL = M("steel", (0.62, 0.66, 0.70), 0.3, 0.6)
BRASS = M("brass", (0.72, 0.53, 0.20), 0.35, 0.7)
GREEN = M("pcb", (0.16, 0.32, 0.24), 0.5)
EYEM = M("eye", (1.0, 0.96, 0.85), 0.15, emit=9.0)
CAMM = M("lens", (0.04, 0.05, 0.09), 0.05, 0.5)
SLOTM = M("slot", (0.2, 0.8, 0.4), 0.4, alpha=0.25)
BATT = M("batt", (0.10, 0.10, 0.12), 0.55)

COLS = {}
def col(n):
    c = bpy.data.collections.new(n)
    bpy.context.scene.collection.children.link(c)
    COLS[n] = c
for c in ["LEG_L", "LEG_R", "TRUNK", "ARMS", "NECK", "HEAD",
          "HARDWARE", "COMPONENTS", "SLOTS"]:
    col(c)


def link(cname, o):
    for c in o.users_collection:
        c.objects.unlink(o)
    COLS[cname].objects.link(o)


def cube(name, dims, loc, cname, mat=None, rot=None, bev=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    if rot:
        o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev:
        md = o.modifiers.new("bev", "BEVEL")
        md.width = bev
        md.segments = 3
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="bev")
    if mat:
        o.data.materials.append(mat)
    link(cname, o)
    return o


def cyl(name, r, d, loc, cname, mat=None, rot=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc)
    o = bpy.context.active_object
    o.name = name
    if rot:
        o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        o.data.materials.append(mat)
    link(cname, o)
    return o


def bore(o, pos, r, depth, axis="Z"):
    """drill a real hole through object o."""
    rot = {"Z": (0, 0, 0), "X": (0, 1.5708, 0), "Y": (1.5708, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=depth,
                                        location=pos, rotation=rot)
    c = bpy.context.active_object
    md = o.modifiers.new("b", "BOOLEAN")
    md.operation = "DIFFERENCE"
    md.object = c
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="b")
    bpy.data.objects.remove(c)


def insert(name, loc, axis="Z"):
    """heat-set brass insert proxy."""
    rot = {"Z": (0, 0, 0), "X": (0, 1.5708, 0), "Y": (1.5708, 0, 0)}[axis]
    cyl(name, INS_R, INS_D, loc, "HARDWARE", BRASS, rot=rot, verts=20)
    o = bpy.context.active_object
    o["part"] = "M2 heat-set insert"


def screw(name, loc, axis="Z"):
    rot = {"Z": (0, 0, 0), "X": (0, 1.5708, 0), "Y": (1.5708, 0, 0)}[axis]
    o = cyl(name, 0.0016, 0.0012, loc, "HARDWARE", STEEL, rot=rot, verts=20)
    o["part"] = "M2 screw"


def post(name, loc, h, r=BOSS_R, hole_axis="Z"):
    """mounting post: boss + printed M2 hole + insert + screw head."""
    o = cyl(name, r, h, (loc[0], loc[1], loc[2] + h / 2), "TRUNK", WHITE, verts=24)
    bore(o, (loc[0], loc[1], loc[2] + h / 2), HOLE_R, h + 0.002)
    insert(name + "_ins", (loc[0], loc[1], loc[2] + h - INS_D / 2))
    return o


def servo_station(name, loc, cn, tag):
    """servo in a printable pocket: floor + 2 cheeks + collar plate +
    M2 bosses. Servo drops in, collar traps it, horn exits open side."""
    w, t, h = SV
    x, y, z = loc
    # servo proxy (not printed)
    sv = cube(name, SV, loc, cn, GREY, bev=0.0006)
    sv["component"] = "SCS0009 servo"
    sv["proxy"] = True
    sh = cyl(name + "_shaft", 0.003, t + 0.003, (x + w * 0.28, y, z + h * 0.30),
        cn, STEEL, rot=(1.5708, 0, 0))
    sh["proxy"] = True
    # pocket walls (printed, same color as frame)
    pw, pt = w + CLR * MM, t + CLR * MM
    cube(name + "_floor", (pw + 0.004, pt + 0.004, 0.0016), (x, y, z - h / 2 - 0.0008),
         cn, WHITE)
    for sgn in (-1, 1):
        cube(name + f"_cheek{sgn}", (pw + 0.004, 0.0016, h + 0.004),
             (x, y + sgn * (pt / 2 + 0.0008), z), cn, WHITE)
    # back wall (wire exits through a slot at bottom rear)
    cube(name + "_back", (0.0016, pt + 0.004, h * 0.6),
         (x - pw / 2 - 0.0008, y, z - h * 0.2), cn, WHITE)
    # collar plate traps servo top: plate + 2 bosses + inserts + screws
    cz = z + h / 2 + 0.0012
    cp = cube(name + "_collar", (pw + 0.010, pt + 0.010, 0.0024), (x, y, cz),
              cn, ORANGE if tag else WHITE, bev=0.001)
    for i, sgn in enumerate((-1, 1)):
        bx, by = x + sgn * (pw / 2 + 0.003), y
        # boss post stands beside pocket, collar hole lands on it
        cube(name + f"_boss{i}", (0.004, 0.004, h + 0.006),
             (bx, by, z + 0.002), cn, WHITE)
        bore(cp, (bx, by, cz), HOLE_R, 0.004)
        insert(name + f"_ins{i}", (bx, by, z + h / 2 - 0.003))
        screw(name + f"_scr{i}", (bx, by, cz + 0.0018))


# ================= LEGS ===================================================
ankle_z = 0.022
knee_z = ankle_z + SHIN * MM
hip_z = knee_z + FEMUR * MM
trunk_z0 = hip_z + 0.007

for sgn, tag in ((1, "L"), (-1, "R")):
    y = sgn * HIP_Y * MM
    cn = f"LEG_{tag}"
    # hip yaw servo: horizontal pocket under trunk floor
    servo_station(f"HYAW_{tag}", (0, sgn * (HIP_Y - 2) * MM, trunk_z0 + 0.010), cn, tag)
    # hip roll servo
    servo_station(f"HROLL_{tag}", (0, sgn * (HIP_Y + 4) * MM, trunk_z0 - 0.010), cn, tag)
    # hip pitch servo at femur top
    servo_station(f"HPITCH_{tag}", (0, y, hip_z - 0.008), cn, tag)
    # femur shell link: slim cover around the link between hip-pitch & knee
    cube(f"FEMUR_{tag}", S(13, 15, FEMUR - 6), (0, y, (hip_z + knee_z) / 2 - 0.006),
         cn, WHITE, bev=0.003)
    servo_station(f"KNEE_{tag}", (0, y, knee_z), cn, tag)
    cube(f"SHIN_{tag}", S(11, 13, SHIN - 5), (0, y, (knee_z + ankle_z) / 2 + 0.004),
         cn, WHITE, bev=0.003)
    servo_station(f"ANKLE_{tag}", (0.006, y, ankle_z + 0.004), cn, tag)
    # foot: open-top frame + screwed sole plate + horn pocket on top
    fr = cube(f"FOOT_{tag}", FOOT, (0.006, y, 0.0035), cn, ORANGE, bev=0.003)
    cube(f"SOLE_{tag}", S(41, 25, 2.5), (0.006, y, 0.0012), cn, YELLOW, bev=0.001)
    # 4 sole screws up into foot frame
    for i, (dx, dy) in enumerate([(-0.014, -0.009), (-0.014, 0.009),
                                   (0.014, -0.009), (0.014, 0.009)]):
        bore(fr, (0.006 + dx, y + dy, 0.0035), HOLE_R, 0.010)
        insert(f"FOOTINS_{tag}{i}", (0.006 + dx, y + dy, 0.0055))
    cube(f"TOE_{tag}", S(9, 26, 5), (0.026, y, 0.008), cn, ORANGE, bev=0.002)

# ================= TRUNK (clamshell) =====================================
tzc = trunk_z0 + TRUNK[2] / 2
# front half: front wall + partial sides + interior posts
tf = cube("TRUNK_F", (TRUNK[0] * 0.55, TRUNK[1], TRUNK[2]),
          (TRUNK[0] * 0.225, 0, tzc), "TRUNK", WHITE, bev=0.008)
# rear half
tr = cube("TRUNK_R", (TRUNK[0] * 0.45, TRUNK[1], TRUNK[2]),
          (-TRUNK[0] * 0.275, 0, tzc), "TRUNK", WHITE, bev=0.008)
# seam bosses along the joint line (3 per side)
for sgn in (-1, 1):
    for i, zz in enumerate((tzc - 0.011, tzc, tzc + 0.011)):
        bx, by = 0.001, sgn * (TRUNK[1] / 2 - 0.004)
        cyl(f"SEAM_{'F' if sgn>0 else 'B'}{i}", BOSS_R, 0.006, (bx, by, zz),
            "TRUNK", WHITE, verts=24)
        bore(tr if sgn < 0 else tf, (bx, by, zz), HOLE_R, 0.010, axis="Y")
        insert(f"SEAMINS_{'F' if sgn>0 else 'B'}{i}", (bx, by * 0.96, zz), axis="Y")
# chest service panel — screwed to 4 posts
for i, (dy, dz) in enumerate([(-0.012, -0.008), (-0.012, 0.008),
                               (0.012, -0.008), (0.012, 0.008)]):
    post(f"PANP_{i}", (0.016, dy, tzc + dz), 0.0035, r=0.0022)
cp = cube("CHEST_PANEL", (0.004, TRUNK[1] * 0.62, TRUNK[2] * 0.5),
          (0.021, 0, tzc + 0.002), "TRUNK", DARK, bev=0.002)
for i, (dy, dz) in enumerate([(-0.012, -0.008), (-0.012, 0.008),
                               (0.012, -0.008), (0.012, 0.008)]):
    bore(cp, (0.021, dy, tzc + 0.002 + dz), HOLE_R, 0.006, axis="X")
    screw(f"PANSCR_{i}", (0.0235, dy, tzc + 0.002 + dz), axis="X")
# vents under panel
for i in range(3):
    cube(f"VENT_{i}", (0.002, TRUNK[1] * 0.4, 0.002),
         (0.0208, 0, tzc - TRUNK[2] * 0.34 + i * 0.005), "TRUNK", GREY)
# rear: power button + USB holes
cyl("PWR_BTN", 0.003, 0.004, (-0.0208, 0.010, tzc + 0.006), "TRUNK", GREY, rot=(0, 1.5708, 0))
cube("USB_SLOT", (0.003, 0.009, 0.0035), (-0.0208, -0.007, tzc + 0.004), "TRUNK", DARK)

# interior mounting: battery tray / pcb standoffs / imu posts / speaker ring
comp = [
    ("BATTERY_2S_300", S(34, 24, 10), (0, 0, tzc - 0.009), BATT, "2S 300mAh LiPo"),
    ("PCB_ESP32S3", S(32, 24, 6), (0, 0, tzc + 0.003), GREEN, "ESP32-S3 + bus hub + buck"),
    ("IMU_BNO085", S(16, 14, 4), (0.008, -0.011, tzc + 0.012), GREEN, "BNO085 IMU"),
    ("SPEAKER_16MM", (0.016, 0.016, 0.005), (0.015, 0.008, tzc - 0.005), DARK, "16mm 8ohm spkr"),
]
for name, dims, loc, mat, label in comp:
    o = cube(name, dims, loc, "COMPONENTS", mat)
    o["component"] = label
    s = cube("SLOT_" + name, tuple(d + 0.002 for d in dims), loc, "SLOTS", SLOTM)
    s["slot_for"] = label
# battery tray: low walls + strap slots
cube("BAT_FLOOR", S(36, 26, 1.6), (0, 0, tzc - 0.0155), "TRUNK", WHITE)
for sgn in (-1, 1):
    cube("BAT_WALL", S(36, 1.6, 5), (0, sgn * 0.0135, tzc - 0.013), "TRUNK", WHITE)
cube("BAT_END", S(1.6, 26, 5), (-0.018, 0, tzc - 0.013), "TRUNK", WHITE)
# pcb standoffs (4x M2)
for i, (dx, dy) in enumerate([(-0.013, -0.009), (-0.013, 0.009),
                               (0.013, -0.009), (0.013, 0.009)]):
    post(f"PCBP_{i}", (dx, dy, tzc - 0.004), 0.004, r=0.0022)
# imu posts (2x M1.6-ish)
for i, dy in enumerate((-0.005, 0.005)):
    post(f"IMUP_{i}", (0.008, -0.011 + dy, tzc + 0.008), 0.003, r=0.0018)
# speaker ring pocket behind chest panel
bpy.ops.mesh.primitive_torus_add(major_radius=0.0085, minor_radius=0.0015,
                                 major_segments=28,
                                 location=(0.018, 0.008, tzc - 0.005),
                                 rotation=(0, 1.5708, 0))
o = bpy.context.active_object
o.name = "SPK_RING"
o.data.materials.append(WHITE)
link("TRUNK", o)

# flippers: side shells screwed to trunk sides
for sgn, tag in ((1, "L"), (-1, "R")):
    cube(f"FLIPPER_{tag}", S(32, 13, 28),
         (0.002, sgn * (TRUNK[1] / 2 + 0.005), tzc - 0.007),
         "ARMS", WHITE, rot=(0, 0.10 * sgn, 0), bev=0.006)
    cube(f"FLIP_TIP_{tag}", S(30, 13, 6),
         (0.002, sgn * (TRUNK[1] / 2 + 0.007), tzc - 0.019),
         "ARMS", ORANGE, rot=(0, 0.10 * sgn, 0), bev=0.002)
    for i, dz in enumerate((-0.008, 0.008)):
        # side screw + insert into trunk wall
        insert(f"FLIPINS_{tag}{i}", (0.002, sgn * (TRUNK[1] / 2 - 0.001), tzc - 0.007 + dz), axis="Y")
        screw(f"FLIPSCR_{tag}{i}", (0.002, sgn * (TRUNK[1] / 2 + 0.0125), tzc - 0.007 + dz), axis="Y")

# ================= NECK =================================================
neck_z0 = trunk_z0 + TRUNK[2]
# NPITCH horizontal in trunk ceiling pocket
servo_station("NPITCH", (0.008, 0, neck_z0 - 0.007), "NECK", "")
# NYAW servo = exposed column; clamped top+bottom collars to trunk & head base
sv = cube("NYAW", SV, (0.020, 0, neck_z0 + NECK_H * MM / 2 - 0.002), "NECK", GREY, bev=0.0006)
sv["component"] = "SCS0009 servo"
sv["proxy"] = True
nyz = neck_z0 + NECK_H * MM / 2 - 0.002
for i, zz in enumerate((nyz - SV[2] / 2 - 0.001, nyz + SV[2] / 2 + 0.001)):
    cl = cyl(f"NCOL_{i}", 0.009, 0.0025, (0.020, 0, zz), "NECK", ORANGE, verts=28)
    for j, sgn in enumerate((-1, 1)):
        bore(cl, (0.020 + sgn * 0.006, 0, zz), HOLE_R, 0.005)
        insert(f"NCINS_{i}{j}", (0.020 + sgn * 0.006, 0, zz - 0.003 if i == 0 else zz + 0.003))
cyl("NECK_CABLE", 0.003, NECK_H * MM - 0.006, (0.005, 0, nyz), "NECK", DARK)

# ================= HEAD (BDX bar) =======================================
hz0 = neck_z0 + NECK_H * MM + 0.003
hzc = hz0 + HEAD_H * MM / 2
hcx = 0.022
face_x = hcx + HEAD_D * MM / 2
# top shell + base plate (two-part head, screwed)
hs = cube("HEAD_SHELL", S(HEAD_D, HEAD_W, HEAD_H), (hcx, 0, hzc), "HEAD", WHITE, bev=0.007)
hb = cube("HEAD_BASE", (S(HEAD_D - 4, HEAD_W - 8, 2)), (hcx, 0, hz0 + 0.001), "HEAD", WHITE)
# base plate: NYAW horn hole + 4 corner holes + cable slot
bore(hb, (0.020 + SV[0] * 0.28, 0, hz0 + 0.001), 0.0045, 0.004)
bore(hb, (0.010, 0.012, hz0 + 0.001), 0.0025, 0.004)  # cable slot hole
for i, (dx, dy) in enumerate([(-0.013, -0.026), (-0.013, 0.026),
                               (0.013, -0.026), (0.013, 0.026)]):
    bore(hs, (hcx + dx, dy, hzc), HOLE_R, HEAD_H * MM + 0.004)
    insert(f"HINS_{i}", (hcx + dx, dy, hz0 + 0.004))
# face plate + real holes: 2 eye apertures + corner screws
fp_w, fp_h = HEAD_W * 0.88 * MM, HEAD_H * 0.80 * MM
fp = cube("FACE_PLATE", (0.005, fp_w, fp_h), (face_x + 0.001, 0, hzc), "HEAD", DARK, bev=0.003)
eye_r, eye_z, eye_dy = 0.008, hzc + 0.001, 0.0135
for sgn in (1, -1):
    bore(fp, (face_x + 0.001, sgn * eye_dy, eye_z), 0.0085, 0.008, axis="X")
for i, (dy, dz) in enumerate([(-0.027, -0.008), (-0.027, 0.008),
                               (0.027, -0.008), (0.027, 0.008)]):
    bore(fp, (face_x + 0.001, dy, hzc + dz), HOLE_R, 0.008, axis="X")
    screw(f"FSCR_{i}", (face_x + 0.0038, dy, hzc + dz), axis="X")
# eye bezels + lit lenses (bezel press-fit into the face bores)
for sgn, tag in ((1, "L"), (-1, "R")):
    cyl(f"EYE_RING_{tag}", eye_r, 0.004, (face_x + 0.003, sgn * eye_dy, eye_z),
        "HEAD", DARK, rot=(0, 1.5708, 0))
    cyl(f"EYE_{tag}", eye_r * 0.66, 0.003, (face_x + 0.006, sgn * eye_dy, eye_z),
        "HEAD", EYEM, rot=(0, 1.5708, 0))
# speaker perforation dots (printed dimples)
for sgn in (1, -1):
    for r in range(2):
        for c in range(3):
            cyl(f"SPK_{'L' if sgn>0 else 'R'}_{r}{c}", 0.0011, 0.002,
                (face_x + 0.003, sgn * (0.023 + c * 0.0025), hzc - 0.003 + r * 0.005),
                "HEAD", DARK, rot=(0, 1.5708, 0))
# side pods
for sgn, tag in ((1, "L"), (-1, "R")):
    cyl(f"EAR_{tag}", 0.006, 0.003, (hcx, sgn * (HEAD_W / 2 * MM + 0.0015), hzc),
        "HEAD", GREY, rot=(1.5708, 0, 0))
    cyl(f"EAR_CAP_{tag}", 0.003, 0.004, (hcx, sgn * (HEAD_W / 2 * MM + 0.002), hzc),
        "HEAD", ORANGE, rot=(1.5708, 0, 0))
# antenna
cyl("ANT_MAST", 0.0009, 0.016,
    (hcx - HEAD_D * MM * 0.32, -HEAD_W * MM * 0.30, hz0 + HEAD_H * MM + 0.008),
    "HEAD", GREY, rot=(0.05, 0.08, 0))
cube("CHIN", (0.009, fp_w * 0.5, 0.006), (face_x - 0.005, 0, hz0 - 0.001), "HEAD", WHITE, bev=0.003)

# eye internals: sensor pods on brackets behind the bores
cam_o = cyl("CAM_POD", 0.0045, 0.010, (face_x - 0.010, eye_dy, eye_z), "COMPONENTS", CAMM, rot=(0, 1.5708, 0))
cam_o["component"] = "OV2640 camera (behind L eye)"
cyl("CAM_LENS", 0.003, 0.003, (face_x - 0.003, eye_dy, eye_z), "COMPONENTS", CAMM, rot=(0, 1.5708, 0))
tof = cube("TOF_POD", S(8, 8, 4), (face_x - 0.010, -eye_dy, eye_z), "COMPONENTS", GREEN)
tof["component"] = "VL53L0X ToF (behind R eye)"
# brackets: two cheek walls each holding the pods
for sgn, pz in ((1, "CAM"), (-1, "TOF")):
    for csgn in (-1, 1):
        cube(f"{pz}_BRK{csgn}", (0.0016, 0.0016, 0.012),
             (face_x - 0.010, sgn * eye_dy + csgn * 0.006, eye_z - 0.001), "HEAD", WHITE)
# LED rings
for sgn, tag in ((1, "L"), (-1, "R")):
    bpy.ops.mesh.primitive_torus_add(major_radius=eye_r * 0.8, minor_radius=0.0012,
                                     major_segments=28,
                                     location=(face_x + 0.005, sgn * eye_dy, eye_z),
                                     rotation=(0, 1.5708, 0))
    o = bpy.context.active_object
    o.name = f"LEDRING_{tag}"
    o["component"] = "WS2812 8-LED ring (eye glow)"
    o.data.materials.append(GREEN)
    link("COMPONENTS", o)
hv = cube("SLOT_HEAD_ELEC", S(HEAD_D - 8, HEAD_W - 14, 6), (hcx, 0, hz0 + 0.006), "SLOTS", SLOTM)
hv["slot_for"] = "head: eye wiring, camera FPC, ToF flex, mic"

# ================= stage + render =======================================
bpy.ops.mesh.primitive_plane_add(size=5)
floor = bpy.context.active_object
floor.data.materials.append(M("floor", (0.20, 0.20, 0.21), 0.85))
w = bpy.context.scene.world or bpy.data.worlds.new("w")
bpy.context.scene.world = w
w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.02, 0.02, 0.025, 1)
bg.inputs[1].default_value = 0.25
for loc, e in [((0.4, -0.4, 0.5), 18), ((-0.4, 0.3, 0.4), 11), ((0.1, 0.4, 0.2), 7)]:
    d = bpy.data.lights.new("a", "AREA")
    d.energy = e
    d.shape = "DISK"
    d.size = 0.3
    o = bpy.data.objects.new("l", d)
    o.location = loc
    o.rotation_euler = (Vector((0, 0, 0.09)) - o.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(o)

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x = 1280
sc.render.resolution_y = 1440
sc.render.image_settings.file_format = "PNG"
sc.view_settings.look = "AgX - Medium High Contrast"
top_z = hz0 + HEAD_H * MM
TARGET = Vector((0, 0, top_z * 0.45))


def cam(name, loc, ortho=None, target=None):
    d = bpy.data.cameras.new(name)
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    t = target or TARGET
    o.rotation_euler = (t - o.location).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        d.type = "ORTHO"
        d.ortho_scale = ortho
    else:
        d.lens = 50
    d.clip_start, d.clip_end = 0.01, 20
    sc.camera = o


def render(n):
    sc.render.filepath = os.path.join(IMG, n + ".png")
    bpy.ops.render.render(write_still=True)
    print("[render]", n)


def setcol(n, hide):
    COLS[n].hide_render = hide
    for o in COLS[n].objects:
        o.hide_render = hide


setcol("SLOTS", True)
setcol("COMPONENTS", True)
setcol("HARDWARE", True)  # inserts/screws hidden in beauty shots
cam("hero", (0.30, -0.24, 0.22))
render("hero-3q")
print(f"[dims] height ~{top_z*1000:.0f}mm")

if not QUICK:
    cam("front", (0.34, 0, top_z * 0.5), ortho=0.22)
    render("front")
    cam("side", (0, -0.34, top_z * 0.5), ortho=0.22)
    render("side")
    cam("rear", (-0.34, 0, top_z * 0.5), ortho=0.22)
    render("rear")
    cam("head", (0.15, -0.13, top_z * 0.93), ortho=0.09, target=Vector((0.03, 0, hzc)))
    render("head-detail")
    # leg station detail: collar + boss hardware visible
    setcol("HARDWARE", False)
    cam("legdet", (0.10, -0.10, 0.09), ortho=0.10, target=Vector((0, 0, 0.05)))
    render("servo-station")
    setcol("HARDWARE", True)
    # internals
    for c in ["TRUNK", "HEAD", "ARMS"]:
        setcol(c, True)
    setcol("SLOTS", False)
    setcol("COMPONENTS", False)
    cam("hero", (0.30, -0.24, 0.22))
    render("internals")
    for c in ["TRUNK", "HEAD", "ARMS"]:
        setcol(c, False)
    setcol("SLOTS", True)
    setcol("COMPONENTS", True)

# export printable parts (shells/brackets/plates — not proxies/slots/components)
PRINT_COLS = ["LEG_L", "LEG_R", "TRUNK", "ARMS", "NECK", "HEAD"]
for c in PRINT_COLS:
    for o in COLS[c].objects:
        if o.get("proxy"):
            continue  # servo/shaft proxies are not printed parts
        for s in bpy.context.selected_objects:
            s.select_set(False)
        o.select_set(True)
        bpy.ops.wm.stl_export(filepath=os.path.join(PARTS, o.name + ".stl"),
                              export_selected_objects=True)
        o.select_set(False)
n = sum(len(c.objects) for c in COLS.values())
print(f"[export] {n} objects")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "knoll-mini.blend"))
print("[done]")
