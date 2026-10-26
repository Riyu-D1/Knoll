#!/usr/bin/env python3
"""
Knoll Mini — ~18cm pocket biped, BDX-head, designed around cheap parts.

Fully parametric original model (no imported Pollen meshes this time).
Every component gets a real slot in the frame:

  Legs    5x STS3032-class serial servos each (hip yaw/roll/pitch,knee,ankle)
  Neck    2x SCS0009 micro serial servos (pitch+yaw) -> head bar
  Head    BDX slab bar: dark face, 2 lamp-eyes, speaker dots, antenna,
          ears — eyes are functional: L=camera pod, R=ToF pod, each
          behind a lit WS2812 ring (expression + sensing, Imagineer-style)
  Trunk   slots: 2S LiPo, ESP32-S3 board stack, bus hub, IMU, speaker
  Arms    static flipper shells (recovery bumpers, like the reference)

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
bpy.ops.object.delete()  # wipe default cube/light/camera

MM = 0.001  # work in metres, dims given in mm
S = lambda *v: tuple(x * MM for x in v)      # mm tuple -> m
P = lambda *v: tuple(x * MM for x in v)

# ---------------- dims (mm) -----------------------------------------------
SV_LEG = S(23.2, 12.1, 25.25)     # SCS0009 / Waveshare SC09 body — all 12 joints
FOOT = S(44, 28, 7)
FEMUR, SHIN = 24.0, 22.0          # link lengths between joint axes
TRUNK = S(40, 50, 34)             # (x depth, y width, z height)
NECK_H = 25.0                     # NYAW servo body IS the neck column
HEAD_W, HEAD_D, HEAD_H = 68.0, 38.0, 24.0
HIP_Y = 16.5                      # hip lateral offset (feet clear by ~4mm)


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
for c in ["LEG_L", "LEG_R", "TRUNK", "ARMS", "NECK", "HEAD", "COMPONENTS", "SLOTS"]:
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


def cyl(name, r, d, loc, cname, mat=None, rot=None, verts=36):
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


def servo(name, dims, loc, cname, shaft_axis="Y", body_mat=GREY):
    """servo body + shaft stub + ear flanges (approx STS/SCS class)."""
    o = cube(name, dims, loc, cname, body_mat, bev=0.0006)
    w, t, h = dims
    # mounting ears (top/bottom flanges along the body axis)
    for sgn in (1, -1):
        cube(name + "_ear", (w * 0.45, t * 0.9, 0.0016),
             (loc[0], loc[1], loc[2] + sgn * (h / 2 + 0.0008)), cname, body_mat)
    # output shaft stub on one side
    if shaft_axis == "Y":
        cyl(name + "_shaft", 0.0035, t + 0.004, (loc[0] + w * 0.28, loc[1], loc[2] + h * 0.30),
            cname, STEEL, rot=(1.5708, 0, 0))
    else:
        cyl(name + "_shaft", 0.0035, w + 0.004, (loc[0] + w * 0.28, loc[1], loc[2] + h * 0.30),
            cname, STEEL, rot=(0, 1.5708, 0))
    return o


# ================= LEGS ===================================================
# chain: hip_yaw(under trunk) -> hip_roll -> hip_pitch -> knee -> ankle -> foot
ankle_z = 0.022        # ankle axis (foot 7mm + servo half-height)
knee_z = ankle_z + SHIN * MM
hip_z = knee_z + FEMUR * MM
trunk_z0 = hip_z + 0.007       # trunk bottom just above hip servos

for sgn, tag in ((1, "L"), (-1, "R")):
    y = sgn * HIP_Y * MM
    cn = f"LEG_{tag}"
    # hip yaw servo: horizontal under trunk floor, shaft down
    servo(f"HYAW_{tag}", (SV_LEG[2], SV_LEG[0], SV_LEG[1]),
          (0, sgn * (HIP_Y - 2) * MM, trunk_z0 + 0.010), cn)
    # hip roll servo: vertical block inside trunk-side bracket
    servo(f"HROLL_{tag}", SV_LEG, (0, sgn * (HIP_Y + 4) * MM, trunk_z0 - 0.012), cn)
    # hip pitch servo at femur top
    servo(f"HPITCH_{tag}", SV_LEG, (0, y, hip_z - 0.010), cn)
    # femur shell link
    cube(f"FEMUR_{tag}", S(14, 16, FEMUR - 8), (0, y, (hip_z + knee_z) / 2),
         cn, WHITE, bev=0.004)
    # knee servo
    servo(f"KNEE_{tag}", SV_LEG, (0, y, knee_z), cn)
    # shin shell link
    cube(f"SHIN_{tag}", S(12, 14, SHIN - 6), (0, y, (knee_z + ankle_z) / 2),
         cn, WHITE, bev=0.004)
    # ankle servo
    servo(f"ANKLE_{tag}", SV_LEG, (0.006, y, ankle_z + 0.004), cn)
    # foot: orange frame + yellow sole
    cube(f"FOOT_{tag}", FOOT, (0.006, y, 0.0035), cn, ORANGE, bev=0.004)
    cube(f"SOLE_{tag}", S(41, 27, 2.5), (0.006, y, 0.0012), cn, YELLOW, bev=0.001)
    cube(f"TOE_{tag}", S(9, 28, 5), (0.026, y, 0.008), cn, ORANGE, bev=0.002)

# ================= TRUNK =================================================
tzc = trunk_z0 + TRUNK[2] / 2
cube("TRUNK_SHELL", TRUNK, (0, 0, tzc), "TRUNK", WHITE, bev=0.008)
# front service panel (BDX-style chest plate) — trunk front face at x=0.020
cube("CHEST_PANEL", (0.005, TRUNK[1] * 0.7, TRUNK[2] * 0.55),
     (0.0205, 0, tzc + 0.002), "TRUNK", DARK, bev=0.002)
# vent slots under the panel
for i in range(3):
    cube(f"VENT_{i}", (0.003, TRUNK[1] * 0.5, 0.0025),
         (0.0205, 0, tzc - TRUNK[2] * 0.36 + i * 0.006), "TRUNK", GREY)
# power button + charge port on rear
cyl("PWR_BTN", 0.0035, 0.003, (-0.0205, 0.010, tzc + 0.006), "TRUNK", GREY,
    rot=(0, 1.5708, 0))
cube("USB_SLOT", (0.003, 0.009, 0.0035), (-0.0205, -0.007, tzc + 0.004), "TRUNK", DARK)

# flippers: static arm shells on trunk sides (recovery bumpers)
for sgn, tag in ((1, "L"), (-1, "R")):
    fp = cube(f"FLIPPER_{tag}", S(32, 13, 28),
              (0.002, sgn * (TRUNK[1] / 2 + 0.005), tzc - 0.007),
              "ARMS", WHITE, rot=(0, 0.10 * sgn, 0), bev=0.006)
    cube(f"FLIP_TIP_{tag}", S(30, 13, 6),
         (0.002, sgn * (TRUNK[1] / 2 + 0.007), tzc - 0.019),
         "ARMS", ORANGE, rot=(0, 0.10 * sgn, 0), bev=0.002)

# ================= COMPONENTS (real slots) ===============================
# inside trunk: battery / PCB stack / IMU / speaker — shown through slots
comp = [
    ("BATTERY_2S_300", S(34, 24, 10), (0, 0, tzc - 0.009), BATT, "2S 300mAh LiPo"),
    ("PCB_ESP32S3", S(32, 24, 6), (0, 0, tzc + 0.002), GREEN, "ESP32-S3 + bus hub + 6V buck"),
    ("IMU_BNO085", S(16, 14, 4), (0.008, -0.010, tzc + 0.011), GREEN, "BNO085 IMU"),
    ("SPEAKER_16MM", (0.016, 0.016, 0.005), (0.017, 0.008, tzc - 0.005), DARK, "16mm 8ohm spkr"),
]
for name, dims, loc, mat, label in comp:
    o = cube(name, dims, loc, "COMPONENTS", mat)
    o["component"] = label
    # translucent slot envelope around it
    s = cube("SLOT_" + name, tuple(d + 0.002 for d in dims), loc, "SLOTS", SLOTM)
    s["slot_for"] = label

# ================= NECK =================================================
neck_z0 = trunk_z0 + TRUNK[2]
# NPITCH lies horizontally inside the trunk ceiling (pitch axis = Y);
# NYAW servo body IS the visible neck column (BDX-faithful exposed mech)
servo("NPITCH", (SV_LEG[0], SV_LEG[2], SV_LEG[1]),
      (0.008, 0, neck_z0 - 0.007), "NECK")
servo("NYAW", SV_LEG, (0.020, 0, neck_z0 + NECK_H * MM / 2 - 0.002), "NECK")
cyl("NECK_CABLE", 0.003, NECK_H * MM - 0.006, (0.005, 0, neck_z0 + NECK_H * MM / 2), "NECK", DARK)

# ================= HEAD (BDX bar) =======================================
hz0 = neck_z0 + NECK_H * MM + 0.004          # bar bottom
hzc = hz0 + HEAD_H * MM / 2
hcx = 0.022                                   # bar center X (slightly fwd of neck)
face_x = hcx + HEAD_D * MM / 2
cube("HEAD_BAR", S(HEAD_D, HEAD_W, HEAD_H), (hcx, 0, hzc), "HEAD", WHITE, bev=0.008)
# dark face plate
fp_w, fp_h = HEAD_W * 0.88 * MM, HEAD_H * 0.80 * MM
cube("FACE_PLATE", (0.006, fp_w, fp_h), (face_x + 0.001, 0, hzc), "HEAD", DARK, bev=0.004)
# lamp eyes: ring + lit lens; sensors live behind the rings
eye_r, eye_z, eye_dy = 0.008, hzc + 0.001, 0.0135
for sgn, tag in ((1, "L"), (-1, "R")):
    cyl(f"EYE_RING_{tag}", eye_r, 0.004, (face_x + 0.003, sgn * eye_dy, eye_z),
        "HEAD", DARK, rot=(0, 1.5708, 0))
    cyl(f"EYE_{tag}", eye_r * 0.66, 0.003, (face_x + 0.006, sgn * eye_dy, eye_z),
        "HEAD", EYEM, rot=(0, 1.5708, 0))
# speaker dot grids flanking eyes (kept inside the plate width)
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
# antenna wire rear-left
cyl("ANT_MAST", 0.0009, 0.016, (hcx - HEAD_D * MM * 0.32, -HEAD_W * MM * 0.30, hz0 + HEAD_H * MM + 0.008),
    "HEAD", GREY, rot=(0.05, 0.08, 0))
# chin ledge
cube("CHIN", (0.009, fp_w * 0.5, 0.006), (face_x - 0.005, 0, hz0 - 0.001), "HEAD", WHITE, bev=0.003)

# sensor pods behind the eyes — L=camera, R=ToF (the Imagineer trick)
cam_o = cyl("CAM_POD", 0.0045, 0.010, (face_x - 0.010, eye_dy, eye_z), "COMPONENTS", CAMM, rot=(0, 1.5708, 0))
cam_o["component"] = "OV2640 camera (behind L eye ring)"
cyl("CAM_LENS", 0.003, 0.003, (face_x - 0.003, eye_dy, eye_z), "COMPONENTS", CAMM, rot=(0, 1.5708, 0))
tof = cube("TOF_POD", S(8, 8, 4), (face_x - 0.010, -eye_dy, eye_z), "COMPONENTS", GREEN)
tof["component"] = "VL53L0X ToF (behind R eye ring)"
# WS2812 rings inside the eyes (the glow hardware)
for sgn, tag in ((1, "L"), (-1, "R")):
    bpy.ops.mesh.primitive_torus_add(major_radius=eye_r * 0.8, minor_radius=0.0012,
                                     major_segments=32,
                                     location=(face_x + 0.005, sgn * eye_dy, eye_z),
                                     rotation=(0, 1.5708, 0))
    o = bpy.context.active_object
    o.name = f"LEDRING_{tag}"
    o["component"] = "WS2812 8-LED ring (eye glow)"
    o.data.materials.append(GREEN)
    link("COMPONENTS", o)

# head internals volume marker
hv = cube("SLOT_HEAD_ELEC", S(HEAD_D - 8, HEAD_W - 14, 6), (hcx, 0, hz0 + 0.006), "SLOTS", SLOTM)
hv["slot_for"] = "head: eye rings wiring, camera FPC, ToF flex, mic slot"

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
setcol("COMPONENTS", True)   # internals only — LED rings/pods must not leak through the face
cam("hero", (0.30, -0.24, 0.22))
render("hero-3q")
print(f"[dims] height ~{top_z*1000:.0f}mm")

if not QUICK:
    cam("front", (0.34, 0, top_z * 0.5), ortho=0.24)
    render("front")
    cam("side", (0, -0.34, top_z * 0.5), ortho=0.24)
    render("side")
    cam("rear", (-0.34, 0, top_z * 0.5), ortho=0.24)
    render("rear")
    cam("head", (0.17, -0.15, top_z * 0.95), ortho=0.10, target=Vector((0.03, 0, hzc)))
    render("head-detail")
    # internals: hide shell parts, show slots+components
    for c in ["TRUNK", "HEAD", "ARMS"]:
        setcol(c, True)
    setcol("SLOTS", False)
    setcol("COMPONENTS", False)
    cam("hero", (0.30, -0.24, 0.22))
    render("internals")
    for c in ["TRUNK", "HEAD", "ARMS"]:
        setcol(c, False)
    setcol("SLOTS", True)

# export shell/print parts (not components/slots)
for c in ["LEG_L", "LEG_R", "TRUNK", "ARMS", "NECK", "HEAD"]:
    for o in COLS[c].objects:
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
