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
for f in os.listdir(PARTS):            # remove stale exports from old runs
    if f.endswith(".stl"):
        os.remove(os.path.join(PARTS, f))

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


def cube(name, dims, loc, cname, mat=None, rot=None, bev=0.0, defer=False):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.name = name
    o.dimensions = dims
    if rot:
        o.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev and defer:
        o["bev"] = bev          # applied after fusion/booleans, not before
    elif bev:
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


import bmesh


def clean(o, dist=1e-6):
    """merge degenerate verts left by booleans; they poison later ops."""
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(o.data); bm.free()


def nonmanifold(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    n = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    return n


def mesh_vol(o):
    """signed mesh volume — the only reliable union-success test (vertex
    count changes even when the solver drops the operand entirely)."""
    m = o.data
    v = 0.0
    for p in m.polygons:
        vs = p.vertices
        if len(vs) < 3:
            continue
        a = m.vertices[vs[0]].co
        for k in range(1, len(vs) - 1):
            b = m.vertices[vs[k]].co
            c = m.vertices[vs[k + 1]].co
            v += a.dot(b.cross(c))
    return v / 6.0


def bore(o, pos, r, depth, axis="Z"):
    """drill a real hole through object o."""
    rot = {"Z": (0, 0, 0), "X": (0, 1.5708, 0), "Y": (1.5708, 0, 0)}[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=r, depth=depth,
                                        location=pos, rotation=rot)
    c = bpy.context.active_object
    nm0 = nonmanifold(o)
    md = o.modifiers.new("b", "BOOLEAN")
    md.operation = "DIFFERENCE"
    md.object = c
    md.solver = "EXACT"
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="b")
    n = nonmanifold(o)
    if n != nm0:
        print(f"[nm-bore] {o.name} @{tuple(round(v*1000,1) for v in pos)}: {nm0} -> {n}")
    bpy.data.objects.remove(c)


def cut_box(o, dims, loc):
    """boolean-subtract a box from object o."""
    c = cube("__cut", dims, loc, "TRUNK")
    nm0 = nonmanifold(o)
    md = o.modifiers.new("b", "BOOLEAN")
    md.operation = "DIFFERENCE"; md.object = c; md.solver = "EXACT"
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier="b")
    n = nonmanifold(o)
    if n != nm0:
        print(f"[nm-cut] {o.name} @{tuple(round(v*1000,1) for v in loc)}: {nm0} -> {n}")
    bpy.data.objects.remove(c)


_failed_unions = []


def fuse_into(base, *others):
    """boolean-union others into base (in place). A real merge adds the
    child's volume; a union that silently drops the operand leaves the
    base volume unchanged — keep such children as <base>_u* members."""
    for other in others:
        v0 = mesh_vol(base)
        vc = abs(mesh_vol(other))
        oname = other.name
        nm0 = nonmanifold(base)
        merged = False
        for attempt in range(3):
            md = base.modifiers.new("u", "BOOLEAN")
            md.operation = "UNION"; md.object = other
            md.solver = "FAST" if attempt == 2 else "EXACT"
            bpy.context.view_layer.objects.active = base
            try:
                bpy.ops.object.modifier_apply(modifier="u")
            except RuntimeError:
                pass
            # union gained volume -> operand really merged; a contained
            # child legitimately adds ~0 and is safe to drop either way
            if mesh_vol(base) > v0 + max(vc * 0.02, 1e-15):
                merged = True
                break
            clean(base)          # degenerate residue can reject the union
            clean(other)
        if merged:
            bpy.data.objects.remove(other)
            nm_now = nonmanifold(base)
            if nm_now != nm0:
                print(f"[nm] {base.name} <- {oname}: {nm0} -> {nm_now} edges")
        else:
            _failed_unions.append(oname)
            other.name = f"{base.name}_u{len(_failed_unions)}"
            print(f"[fuse-FAIL] {oname} -> {other.name} kept as separate member")


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


def servo_station(name, loc, cn, tag, rot=None, shaft_len=None):
    """servo in a printable pocket: floor + 2 cheeks + collar plate +
    M2 bosses. Servo drops in, collar traps it, horn exits open side.
    rot (Euler) reorients the whole station about `loc` so each joint's
    shaft axis is mechanically correct (default shaft axis = Y).
    shaft_len overrides the default horn stub (t + 3 mm)."""
    w, t, h = SV
    x, y, z = loc
    before = set(bpy.data.objects)
    # servo proxy (not printed)
    sv = cube(name, SV, loc, cn, GREY, bev=0.0006)
    sv["component"] = "SCS0009 servo"
    sv["proxy"] = True
    sh = cyl(name + "_shaft", 0.003, shaft_len or (t + 0.003),
             (x + w * 0.28, y, z + h * 0.30), cn, STEEL, rot=(1.5708, 0, 0))
    sh["proxy"] = True
    # pocket walls (printed, same color as frame). Cheeks end flush with the
    # servo top so the removable collar can sit flat on the mouth.
    pw, pt = w + CLR * MM, t + CLR * MM
    cube(name + "_floor", (pw + 0.004, pt + 0.004, 0.0016), (x, y, z - h / 2 - 0.0012),
         cn, WHITE)
    for sgn in (-1, 1):
        cube(name + f"_cheek{sgn}", (pw + 0.004, 0.0016, h + 0.002),
             (x, y + sgn * (pt / 2 + 0.0008), z - 0.001), cn, WHITE)
    # back wall (wire exits through a slot at bottom rear)
    cube(name + "_back", (0.0016, pt + 0.004, h * 0.6),
         (x - pw / 2 - 0.0008, y, z - h * 0.2), cn, WHITE)
    # bosses beside the pocket in Y, tops flush with the cheek/servo top,
    # bottoms flush with the floor underside so they never poke neighbours
    for i, sgn in enumerate((-1, 1)):
        bx, by = x, y + sgn * (pt / 2 + 0.0036)
        bs = cube(name + f"_boss{i}", (0.005, 0.005, h + 0.0016),
                  (bx, by, z - 0.0008), cn, WHITE)
        bore(bs, (bx, by, z + h / 2 - 0.002), 0.0016, 0.005)
    cz = z + h / 2 + 0.0012   # rests on cheek/boss tops, touches servo top
    cp = cube(name + "_collar", (pw + 0.006, pt + 0.013, 0.0024), (x, y, cz),
              cn, ORANGE if tag else WHITE, bev=0.001)
    for i, sgn in enumerate((-1, 1)):
        bx, by = x, y + sgn * (pt / 2 + 0.0036)
        bore(cp, (bx, by, cz), HOLE_R, 0.004)
        insert(name + f"_ins{i}", (bx, by, z + h / 2 - 0.002))
        screw(name + f"_scr{i}", (bx, by, cz + 0.0018))
    if rot:
        from mathutils import Euler, Matrix
        T = (Matrix.Translation(Vector(loc))
             @ Euler(rot).to_matrix().to_4x4()
             @ Matrix.Translation(-Vector(loc)))
        for o in bpy.data.objects:
            if o not in before:
                o.matrix_world = T @ o.matrix_world


# ================= LEGS ===================================================
# Serial chain — real biped structure. Each member holds ONE servo body and
# is driven by the previous joint's horn (the leg is NOT one rigid frame):
#   trunk floor hub -> [yaw shaft] -> HIP block (yaw+roll bodies)
#     -> [roll horn] -> FEMUR (pitch servo) -> [pitch horn]
#     -> SHIN (knee servo) -> [knee horn] -> FOOT (passive ankle)
# Verified: five 29 mm pockets can't stack in a 76 mm leg, so pitch and knee
# members are staggered in x at the same z-band; the hip block carries yaw
# flat (shaft Z into the floor hub) and roll on edge (shaft X).
trunk_z0 = 0.076                   # leg chain centre y = HIP_Y (mm)

for sgn, tag in ((1, "L"), (-1, "R")):
    y = sgn * HIP_Y * MM
    cn = f"LEG_{tag}"
    # ---------- member A: HIP block -------------------------------------
    # top plate bears under the trunk floor (sliding yaw bearing)
    tp = cube(f"HIP_{tag}_top", (0.036, 0.028, 0.0016),
              (0.001, y - sgn * 0.0005, 0.0750), cn, WHITE,
              bev=0.002, defer=True)
    # yaw servo flat inside the block (t-axis -> Z; shaft rises into floor)
    yw = cube(f"HYAW_{tag}", SV, (0.0, y, 0.06705), cn, GREY, bev=0.0006)
    yw.rotation_euler = (sgn * 1.5708, 0, 0)
    yw["component"] = "SCS0009 servo"; yw["proxy"] = True
    shf = cyl(f"HYAW_{tag}_shaft", 0.003, 0.010,
              (0.0065, sgn * 0.0079, 0.0781), cn, STEEL)
    shf["proxy"] = True
    # yaw horn stub: rises from the body top face into the trunk hub
    # roll servo on edge, forward of the yaw servo (t-axis -> X; shaft X)
    svr = cube(f"HROLL_{tag}", SV, (0.022, y, 0.0522), cn, GREY, bev=0.0006)
    svr.rotation_euler = (0, 0, -sgn * 1.5708)
    svr["component"] = "SCS0009 servo"; svr["proxy"] = True
    # horn stub: from the body +x face out to the femur arm bore
    shr = cyl(f"HROLL_{tag}_shaft", 0.003, 0.0192,
              (0.0255, y - sgn * 0.0065, 0.0601), cn, STEEL,
              rot=(0, 1.5708, 0))
    shr["proxy"] = True
    hp = [
        # yaw pocket: floor + 2 x-walls + inner end wall (mouth faces outer)
        cube(f"HIP_{tag}_yfloor", (0.026, 0.028, 0.0016),
             (0.0, y, 0.0598), cn, WHITE),
        cube(f"HIP_{tag}_ywallx-1", (0.0016, 0.0123, 0.016),
             (-0.0127, sgn * 0.00865, 0.0675), cn, WHITE),
        cube(f"HIP_{tag}_ywallx1", (0.0016, 0.0123, 0.016),
             (0.0127, sgn * 0.00865, 0.0675), cn, WHITE),
        cube(f"HIP_{tag}_ywalle", (0.026, 0.0016, 0.016),
             (0.0, y - sgn * 0.0137, 0.0675), cn, WHITE),
        # mouth corner posts (yaw collar screws into them)
        cube(f"HIP_{tag}_ypost-1", (0.003, 0.004, 0.0155),
             (-0.0135, y + sgn * 0.0128, 0.0675), cn, WHITE),
        cube(f"HIP_{tag}_ypost1", (0.003, 0.004, 0.0155),
             (0.0135, y + sgn * 0.0128, 0.0675), cn, WHITE),
        # roll pocket: floor + x-cheeks + y end plates (mouth faces +x);
        # walls start at z 39 so the femur collar top (z~37.5) clears them
        cube(f"HIP_{tag}_rfloor", (0.016, 0.028, 0.0016),
             (0.022, y, 0.0384), cn, WHITE),
        cube(f"HIP_{tag}_rcheek-1", (0.0016, 0.028, 0.029),
             (0.022 - 0.00745, y, 0.0535), cn, WHITE),
        cube(f"HIP_{tag}_rcheek1", (0.0016, 0.028, 0.029),
             (0.022 + 0.00745, y, 0.0535), cn, WHITE),
        cube(f"HIP_{tag}_rend-1", (0.016, 0.0016, 0.029),
             (0.022, y - 0.0130, 0.0535), cn, WHITE),
        cube(f"HIP_{tag}_rend1", (0.016, 0.0016, 0.029),
             (0.022, y + 0.0130, 0.0535), cn, WHITE),
        # -x rear skirt: flush on the yaw wall outer face (clears the body)
        cube(f"HIP_{tag}_side", (0.0016, 0.028, 0.032),
             (-0.0143, y, 0.054), cn, WHITE)]
    # front-mouth corner posts for the roll cover
    for a, (sy, dz) in enumerate(
            ((-1, -0.010), (-1, 0.010), (1, -0.010), (1, 0.010))):
        hp.append(cube(f"HIP_{tag}_cpos{a}", (0.003, 0.004, 0.004),
                       (0.0295, y + sy * 0.011, 0.0510 + dz), cn, WHITE))
    # flipper mounting pad: fused to the roll end plate, face at y+0.0166
    # (clears the yaw collar face at y+0.0164 and both servo bodies)
    hp.append(cube(f"HIP_{tag}_fpad", (0.020, 0.0036, 0.024),
                   (0.016, y + sgn * 0.0148, 0.046), cn, WHITE))
    fuse_into(tp, *hp)
    # post-fusion bores into the block (shaft, ears, posts, wire, flip nubs)
    for sx in (-1, 1):                   # roll shaft bores through x-cheeks
        bore(tp, (0.022 + sx * 0.00745, y - sgn * 0.0065, 0.0601),
             0.0036, 0.004, axis="X")
    for sy in (-1, 1):                   # roll ear-screw bores in end plates
        for ex in (-0.0045, 0.0045):
            for ez in (-0.008, 0.008):
                bore(tp, (0.022 + ex, y + sy * 0.0130, 0.0510 + ez),
                     0.0011, 0.003, axis="Y")
    bore(tp, (0.0065, sgn * 0.0079, 0.0750), 0.0033, 0.003)   # yaw shaft bore
    bore(tp, (-0.002, sgn * 0.0079, 0.0750), 0.0016, 0.003)   # yaw wire bore
    for sy, dz in ((-1, -0.010), (-1, 0.010), (1, -0.010), (1, 0.010)):
        bore(tp, (0.0295, y + sy * 0.011, 0.0510 + dz), 0.0009, 0.005, axis="X")
    for fx, fz in ((0.010, 0.040), (0.010, 0.052), (0.022, 0.040), (0.022, 0.052)):
        bore(tp, (fx, y + sgn * 0.0145, fz), 0.0009, 0.006, axis="Y")
        insert(f"FLPINS_{tag}{fx}{fz}", (fx, y + sgn * 0.0145, fz), axis="Y")
    # yaw mouth collar (separate part) — flush on the mouth-post faces
    yc = cube(f"HYAW_{tag}_collar", (0.030, 0.0016, 0.017),
              (0.0, y + sgn * 0.0156, 0.0675), cn, ORANGE, bev=0.001, defer=True)
    for sx in (-1, 1):
        bore(yc, (sx * 0.0135, y + sgn * 0.0156, 0.0675), 0.0012, 0.003, axis="Y")
        insert(f"HYAW_{tag}_ins{sx}", (sx * 0.0135, y + sgn * 0.0130, 0.0675), axis="Y")
        screw(f"HYAW_{tag}_scr{sx}", (sx * 0.0135, y + sgn * 0.0170, 0.0675), axis="Y")
    # roll front cover (separate part) — flush on the corner-post faces;
    # bottom edge raised over the femur collar top (z~37.5)
    rc = cube(f"HROLL_{tag}_cover", (0.0016, 0.028, 0.029),
              (0.0318, y, 0.05275), cn, ORANGE, bev=0.001, defer=True)
    for sy, dz in ((-1, -0.010), (-1, 0.010), (1, -0.010), (1, 0.010)):
        bore(rc, (0.0318, y + sy * 0.011, 0.0510 + dz), 0.0012, 0.003, axis="X")
        insert(f"HRCOV_{tag}_ins{sy}{dz}",
               (0.0295, y + sy * 0.011, 0.0510 + dz), axis="X")
        screw(f"HRCOV_{tag}_scr{sy}{dz}",
              (0.0332, y + sy * 0.011, 0.0510 + dz), axis="X")
    bore(rc, (0.0318, y - sgn * 0.0065, 0.0601), 0.0038, 0.003, axis="X")

    # ---------- member B: FEMUR — pitch pocket + roll-horn arm -----------
    servo_station(f"HPITCH_{tag}", (0.020, y, 0.0222), cn, tag, shaft_len=0.021)
    for cs in (-1, 1):                   # horn bores through both cheeks
        bore(bpy.data.objects[f"HPITCH_{tag}_cheek{cs}"],
             (0.0265, y + cs * 0.00715, 0.0298), 0.0040, 0.004, axis="Y")
    # notch the floor's front overhang — the toe sweeps up under it when the
    # ankle pitches; the servo is trapped by cheeks+collar so a partial floor
    # still registers it
    cut_box(bpy.data.objects[f"HPITCH_{tag}_floor"],
            (0.018, 0.020, 0.005), (0.0290, y, 0.0092))
    arm = cube(f"FEMUR_{tag}_arm", (0.0036, 0.0122, 0.028),
               (0.0345, sgn * 0.0105, 0.048), cn, WHITE)
    bore(arm, (0.0345, sgn * 0.0100, 0.0601), 0.0033, 0.005, axis="X")
    # collar notch so the arm doesn't touch the removable collar
    cut_box(bpy.data.objects[f"HPITCH_{tag}_collar"],
            (0.004, 0.014, 0.005), (0.0335, sgn * 0.0105, 0.0360))
    # ---------- member C: SHIN — knee pocket + pitch-horn link -----------
    servo_station(f"KNEE_{tag}", (-0.012, y, 0.0222), cn, tag, shaft_len=0.024)
    for cs in (-1, 1):
        bore(bpy.data.objects[f"KNEE_{tag}_cheek{cs}"],
             (-0.0055, y + cs * 0.00715, 0.0298), 0.0040, 0.004, axis="Y")
    # the pitch horn (x 26.5) passes THROUGH the outboard cheek on its way to
    # the link tab — bore clearance for it (separate from the knee horn bores)
    bore(bpy.data.objects[f"KNEE_{tag}_cheek{sgn}"],
         (0.0265, y + sgn * 0.00715, 0.0298), 0.0040, 0.004, axis="Y")
    # link tab on the outboard cheek face, bore engages the pitch horn tip;
    # kept clear of the femur's outboard boss (x<=22.5)
    lp = cube(f"SHIN_{tag}_link", (0.007, 0.003, 0.006),
              (0.027, sgn * 0.02595, 0.0298), cn, WHITE)
    bore(lp, (0.0265, sgn * 0.02595, 0.0298), 0.0033, 0.004, axis="Y")
    # inboard cheek notch so the ankle arm clears the pocket floor/cheek
    cut_box(bpy.data.objects[f"KNEE_{tag}_cheek{-sgn}"],
            (0.012, 0.005, 0.020), (-0.0055, sgn * 0.0060, 0.019))
    # ---------- member D: FOOT + ankle arm -------------------------------
    fr = cube(f"FOOT_{tag}", FOOT, (0.006, y, 0.0035), cn, ORANGE, bev=0.003, defer=True)
    so = cube(f"SOLE_{tag}", S(41, 25, 2.5), (0.006, y, -0.00125), cn, YELLOW, bev=0.001, defer=True)
    aa = cube(f"FOOT_{tag}_ankle", (0.010, 0.0025, 0.0245),
              (-0.0055, sgn * 0.0025, 0.0185), cn, ORANGE)
    bore(aa, (-0.0055, sgn * 0.0025, 0.0298), 0.0033, 0.004, axis="Y")
    fuse_into(fr, aa)
    for i, (dx, dy) in enumerate([(-0.014, -0.009), (-0.014, 0.009),
                                   (0.014, -0.009), (0.014, 0.009)]):
        bore(fr, (0.006 + dx, y + dy, 0.0035), HOLE_R, 0.008)
        bore(so, (0.006 + dx, y + dy, -0.0012), 0.0012, 0.004)
        bore(so, (0.006 + dx, y + dy, -0.0022), 0.0019, 0.0012)
        insert(f"FOOTINS_{tag}{i}", (0.006 + dx, y + dy, 0.0035))
    # toe: front bumper cap on the foot face (x>=0.028) — sits below the
    # femur floor notch and sweeps clear under ankle pitch
    toe = cube(f"TOE_{tag}", S(8, 26, 4), (0.032, y, 0.0055), cn, ORANGE, bev=0.002, defer=True)
    for dy2 in (-0.007, 0.007):
        # insert pocket inside the foot face + through-bore in the toe
        bore(fr, (0.026, y + dy2, 0.0055), HOLE_R, 0.006, axis="X")
        insert(f"TOEINS_{tag}{dy2}", (0.025, y + dy2, 0.0055), axis="X")
        bore(toe, (0.035, y + dy2, 0.0055), 0.0019, 0.0016, axis="X")
        bore(toe, (0.032, y + dy2, 0.0055), 0.0012, 0.009, axis="X")
        screw(f"TOESCR_{tag}{dy2}", (0.0365, y + dy2, 0.0055), axis="X")

# ================= TRUNK (clamshell) =====================================
tzc = trunk_z0 + TRUNK[2] / 2
SEAM_X = -0.002          # clamshell joint plane
W = 0.0016               # wall thickness
# front half: front wall + partial sides — hollowed, cavity opens at seam
# (bevel on the clean cube BEFORE the cavity cut — bevels after fusion
# leave degenerate rims where they cross union seams)
tf = cube("TRUNK_F", (TRUNK[0] * 0.55, TRUNK[1], TRUNK[2]),
          (TRUNK[0] * 0.225, 0, tzc), "TRUNK", WHITE, bev=0.008)
# rear half — hollowed the same way
tr = cube("TRUNK_R", (TRUNK[0] * 0.45, TRUNK[1], TRUNK[2]),
          (-TRUNK[0] * 0.275, 0, tzc), "TRUNK", WHITE, bev=0.008)
inner_x = 0.020 - W                       # F interior front face
rear_x = -0.020 + W                       # R interior rear face
inner_y = TRUNK[1] / 2 - W                # ±0.0234
inner_z = TRUNK[2] / 2 - W                # ±0.0154 about tzc
floor_z = tzc - inner_z                    # interior floor level
cut_box(tf, (0.0209, inner_y * 2, inner_z * 2), (0.00795, 0, tzc))
cut_box(tr, (0.0169, inner_y * 2, inner_z * 2), (-0.00995, 0, tzc))
# seam lugs: rectangular blocks hugging the side-wall inner faces, keeping
# the y-band >20.4 that neither board reaches. +y lugs sit at z 105.5 to
# clear the speaker ring (z 81-101) and IMU (z<=94); -y lugs run two heights
for sgn, zlist in ((-1, (tzc - 0.010, tzc + 0.010)), (1, (tzc + 0.0125,))):
    for i, zz in enumerate(zlist):
        by = sgn * (inner_y - 0.0010)   # 1 mm embedded into the wall — a
        fst = cube(f"SEAMF_{sgn}{i}", (0.006, 0.004, 0.006),  # coplanar back
                   (SEAM_X + 0.003, by, zz), "TRUNK", WHITE)  # face poisons
        fuse_into(tf, fst)                                   # the solver
        bore(tf, (SEAM_X + 0.003, by, zz), 0.0009, 0.007, axis="X")
        bore(tf, (SEAM_X + 0.0058, by, zz), 0.0019, 0.0015, axis="X")  # csink
        rst = cube(f"SEAMR_{sgn}{i}", (0.005, 0.004, 0.006),
                   (SEAM_X - 0.0025, by, zz), "TRUNK", WHITE)
        fuse_into(tr, rst)
        bore(tr, (SEAM_X - 0.0025, by, zz), HOLE_R, 0.006, axis="X")
        insert(f"SEAMINS_{sgn}{i}", (SEAM_X - 0.0018, by, zz), axis="X")
# chest service panel — horizontal posts fused to front inner face
for i, (dy, dz) in enumerate([(-0.015, -0.004), (-0.015, 0.004),
                               (0.015, -0.004), (0.015, 0.004)]):
    p = cyl(f"PANP_{i}", 0.0022, 0.004, (inner_x - 0.001, dy, tzc + dz),
            "TRUNK", WHITE, rot=(0, 1.5708, 0), verts=24)
    fuse_into(tf, p)
    bore(tf, (inner_x - 0.001, dy, tzc + dz), 0.0009, 0.006, axis="X")
    insert(f"PANINS_{i}", (inner_x - 0.0025, dy, tzc + dz), axis="X")
cp = cube("CHEST_PANEL", (0.004, TRUNK[1] * 0.62, 0.015),
          (0.022, 0, tzc), "TRUNK", DARK, bev=0.002, defer=True)
for i, (dy, dz) in enumerate([(-0.015, -0.004), (-0.015, 0.004),
                               (0.015, -0.004), (0.015, 0.004)]):
    bore(cp, (0.023, dy, tzc + dz), 0.0019, 0.0012, axis="X")   # csink
    bore(cp, (0.021, dy, tzc + dz), HOLE_R, 0.006, axis="X")
    screw(f"PANSCR_{i}", (0.0235, dy, tzc + dz), axis="X")
# vents: real through-slots in the front wall (no loose strips — no glue)
for i in range(3):
    vz = tzc - TRUNK[2] * 0.34 + i * 0.005
    cut_box(tf, (0.005, TRUNK[1] * 0.4, 0.002), (0.020, 0, vz))
# rear: power button + USB holes through rear wall (plunger/connector are
# proxies — the real parts live on the PCB/hub behind the holes)
bore(tr, (-0.020, 0.010, tzc + 0.006), 0.0032, 0.005, axis="X")
pb = cyl("PWR_BTN", 0.0028, 0.003, (-0.0205, 0.010, tzc + 0.006), "COMPONENTS", GREY, rot=(0, 1.5708, 0))
pb["proxy"] = True
cut_box(tr, (0.004, 0.009, 0.0035), (-0.020, -0.007, tzc + 0.002))
us = cube("USB_SLOT", (0.0016, 0.008, 0.0028), (-0.0194, -0.007, tzc + 0.002), "COMPONENTS", DARK)
us["proxy"] = True

# interior mounting: battery tray / pcb standoffs / imu posts / speaker ring
comp = [
    ("BATTERY_2S_300", S(34, 21, 10), (0.001, 0, 0.0904), BATT, "2S 300mAh LiPo"),
    ("PCB_ESP32S3", S(32, 3, 24), (-0.001, -0.0175, tzc), GREEN, "ESP32-S3 + bus hub + buck"),
    ("IMU_BNO085", S(14, 4, 16), (-0.010, 0.0165, 0.086), GREEN, "BNO085 IMU (+y wall)"),
]
for name, dims, loc, mat, label in comp:
    o = cube(name, dims, loc, "COMPONENTS", mat)
    o["component"] = label
    s = cube("SLOT_" + name, tuple(d + 0.002 for d in dims), loc, "SLOTS", SLOTM)
    s["slot_for"] = label
spk = cyl("SPEAKER_16MM", 0.008, 0.005, (0.008, 0.0192, tzc - 0.002),
          "COMPONENTS", DARK, rot=(1.5708, 0, 0))
spk["component"] = "16mm 8ohm speaker"
s = cube("SLOT_SPEAKER_16MM", S(17, 6, 17), (0.008, 0.0192, tzc - 0.002), "SLOTS", SLOTM)
s["slot_for"] = "16mm 8ohm speaker"
# ---- leg yaw bearings: hub bores through the floor at each yaw shaft ----
# The hip top plate is a sliding bearing under the floor; the yaw shaft
# rises through the hip-plate bore + floor bore + cavity hub plate.
for sgn, tag in ((1, "L"), (-1, "R")):
    hb = cube(f"YHUB_{tag}", (0.013, 0.013, 0.0026),
              (0.0065, sgn * 0.0079, 0.0783), "TRUNK", WHITE)  # 0.3 into floor
    fuse_into(tf, hb)
    bore(tf, (0.0065, sgn * 0.0079, 0.0770), 0.0033, 0.006)   # shaft pivot
    bore(tf, (-0.002, sgn * 0.0079, 0.0768), 0.0016, 0.004)   # wire pass

# ---- raised battery tray: legs stand on the cavity floor ---------------
# tray floor clears the yaw shaft tips (z~0.081) and the hub plates
parts_f = [cube("BATF_FLOOR", (0.0215, 0.022, 0.0016), (0.00875, 0, 0.0846), "TRUNK", WHITE)]
parts_r = [cube("BATR_FLOOR", (0.0155, 0.022, 0.0016), (-0.010, 0, 0.0846), "TRUNK", WHITE)]
for sgn in (-1, 1):
    parts_f.append(cube(f"BATF_WALL{sgn}", (0.0215, 0.0016, 0.004),
         (0.00875, sgn * 0.0118, 0.0874), "TRUNK", WHITE))
    parts_r.append(cube(f"BATR_WALL{sgn}", (0.0155, 0.0016, 0.004),
         (-0.010, sgn * 0.0118, 0.0874), "TRUNK", WHITE))
    # legs at corners, embedded 0.4 into the cavity floor
    for lx in (-0.014, 0.014):
        shx = tr if lx < 0 else tf
        lg = cyl(f"BATLG_{sgn}{lx}", 0.002, 0.008,
                 (lx, sgn * 0.0085, 0.0812), "TRUNK", WHITE, verts=20)
        fuse_into(shx, lg)
parts_r.append(cube("BATR_END", (0.0016, 0.022, 0.004), (-0.0174, 0, 0.0874), "TRUNK", WHITE))
fuse_into(tf, *parts_f)
fuse_into(tr, *parts_r)
# strap slots through the fused rails
for sgn in (-1, 1):
    cut_box(tf, (0.002, 0.0018, 0.0014), (0.010, sgn * 0.0118, 0.0868))
    cut_box(tr, (0.002, 0.0018, 0.0014), (-0.010, sgn * 0.0118, 0.0868))

# ---- PCB vertical on the -y side wall inner face: 4 posts axis Y --------
# (front-wall mount collided with the battery tray floor; side wall is free)
for i, (px, pz) in enumerate([(-0.011, -0.008), (-0.011, 0.008),
                               (0.009, -0.008), (0.009, 0.008)]):
    shx = tr if px < -0.002 else tf
    p = cyl(f"PCBP_{i}", 0.0022, 0.005, (px, -0.0219, tzc + pz),
            "TRUNK", WHITE, rot=(1.5708, 0, 0), verts=24)  # 1 mm into wall
    fuse_into(shx, p)
    bore(shx, (px, -0.0214, tzc + pz), 0.0009, 0.0045, axis="Y")
    insert(f"PCBINS_{i}", (px, -0.0214, tzc + pz), axis="Y")
    screw(f"PCBSCR_{i}", (px, -0.0190, tzc + pz), axis="Y")

# ---- imu on the +y side wall inner face (floor is crowded by tray legs,
# yaw hubs, the neck wire; +y wall is free inboard of the speaker ring)
for i, (px, pz) in enumerate([(-0.015, 0.082), (-0.015, 0.090),
                               (-0.005, 0.082), (-0.005, 0.090)]):
    p = cyl(f"IMUP_{i}", 0.0018, 0.005, (px, 0.0219, pz),
            "TRUNK", WHITE, rot=(1.5708, 0, 0), verts=24)  # 1 mm into wall
    fuse_into(tr, p)
    bore(tr, (px, 0.0214, pz), 0.0008, 0.0045, axis="Y")
    insert(f"IMUINS_{i}", (px, 0.0214, pz), axis="Y")
    screw(f"IMUSCR_{i}", (px, 0.0194, pz), axis="Y")
# speaker seat: annular disc fused to the +y side wall inner face,
# through-bored for the 16 mm speaker driver
sk = cyl("SPK_RING", 0.010, 0.003, (0.008, 0.0222, tzc - 0.002),
         "TRUNK", WHITE, rot=(1.5708, 0, 0))
fuse_into(tf, sk)
bore(tf, (0.008, 0.0225, tzc - 0.002), 0.0086, 0.004, axis="Y")

# flippers: hip pods screwed to the hip block's outer face via fused nubs
# (nubs + bores were added inside the HIP block above)
# flippers: hip pods on the block's outer pad (face y+0.0166 rel); inner
# face clears the yaw collar face (y+0.0164) and both servo bodies
for sgn, tag in ((1, "L"), (-1, "R")):
    y = sgn * HIP_Y * MM
    fp = cube(f"FLIPPER_{tag}", S(24, 10, 34),
              (0.016, sgn * 0.0381, 0.050),
              "ARMS", WHITE, rot=(0, 0.10 * sgn, 0), bev=0.006, defer=True)
    tip = cube(f"FLIP_TIP_{tag}", S(22, 4, 10),
               (0.016, sgn * 0.0451, 0.040),
               "ARMS", ORANGE, rot=(0, 0.10 * sgn, 0), bev=0.002, defer=True)
    # 4 M2 through the pod into the fused pad inserts (FLPINS above)
    for i, (fx, fz) in enumerate(((0.010, 0.040), (0.010, 0.052),
                                   (0.022, 0.040), (0.022, 0.052))):
        bore(fp, (fx, sgn * 0.0381, fz), 0.0012, 0.012, axis="Y")
        screw(f"FLIPSCR_{tag}{i}", (fx, sgn * 0.0425, fz), axis="Y")
    # tip screws: counterbored M2 through the tip into the flipper face
    for i, tx in enumerate((0.006, 0.026)):
        bore(tip, (tx, sgn * 0.0462, 0.040), 0.0019, 0.002, axis="Y")
        bore(tip, (tx, sgn * 0.0445, 0.040), HOLE_R, 0.008, axis="Y")
        bore(fp, (tx, sgn * 0.0415, 0.040), 0.0009, 0.006, axis="Y")
        screw(f"FTIPSCR_{tag}{i}", (tx, sgn * 0.0470, 0.040), axis="Y")

# ================= NECK =================================================
# NPITCH is the visible mechanical neck block (BDX-style exposed actuator),
# standing on the trunk top. One DOF: head pitch. Servo verified not to fit
# inside the 34 mm cavity alongside battery/PCB.
neck_z0 = trunk_z0 + TRUNK[2]           # 0.110 = trunk top face
# flange ring around the pocket base, screwed down into top-face nubs
fr2 = cube("NPITCH_flange", (0.034, 0.026, 0.0016), (0.006, 0, 0.1108), "NECK", WHITE)
cut_box(fr2, (0.0285, 0.0170, 0.004), (0.006, 0, 0.1108))   # clears the pocket floor
for dx, sh in ((-0.014, tr), (0.014, tf)):
    for dy in (-0.011, 0.011):
        bore(fr2, (0.006 + dx, dy, 0.1108), 0.0012, 0.003)
        nb = cyl(f"NPNUB_{dx}{dy}", 0.0026, 0.0045,
                 (0.006 + dx, dy, 0.1075), "TRUNK", WHITE, verts=20)
        fuse_into(sh, nb)
        bore(sh, (0.006 + dx, dy, 0.107), HOLE_R, 0.006)
        insert(f"NPINS_{dx}{dy}", (0.006 + dx, dy, 0.1075))
        screw(f"NPSCR_{dx}{dy}", (0.006 + dx, dy, 0.1125))
# seat recess in the top face so the pocket floor keys into the trunk
cut_box(tf, (0.023, 0.018, 0.0005), (0.0095, 0, 0.10975))
cut_box(tr, (0.007, 0.018, 0.0005), (-0.0055, 0, 0.10975))
# NPITCH pocket standing on the flange/top face — floor bottom at z=0.110
servo_station("NPITCH", (0.006, 0, 0.1242), "NECK", "", shaft_len=0.021)
# shaft horn access bores through both cheeks (shaft axis = Y)
for cname, sy in (("NPITCH_cheek1", 0.00715), ("NPITCH_cheek-1", -0.00715)):
    bore(bpy.data.objects[cname], (0.006 + SV[0] * 0.28, sy, 0.1242 + SV[2] * 0.30),
         0.0036, 0.004, axis="Y")
# wire hole through the top face behind the pocket back wall
bore(tr, (-0.0145, 0.004, 0.109), 0.0018, 0.005)
# neck arm: plate on the +y cheek outer face (7.95), horn at bottom, screwed
# up into the head base plate — spans horn z0.1318 to base bottom z0.1417
na = cube("NECK_ARM", (0.007, 0.003, 0.0159), (0.0125, 0.00945, 0.13375), "NECK", WHITE)
bore(na, (0.0125, 0.00945, 0.1318), 0.0033, 0.004, axis="Y")  # horn bore
for dx in (-0.002, 0.002):
    bore(na, (0.0125 + dx, 0.00945, 0.1385), 0.0012, 0.006)
# notch the removable collar where the arm passes through its outboard corner
cut_box(bpy.data.objects["NPITCH_collar"], (0.013, 0.005, 0.006),
        (0.0125, 0.0094, 0.138))
# cable conduit from trunk top into head base (behind the pocket back wall,
# clear of the collar's -x edge at -8.9 and the back wall at -7.5)
nc = cyl("NECK_CABLE", 0.003, 0.030, (-0.0145, 0.004, 0.125), "NECK", DARK)
bore(nc, (-0.0145, 0.004, 0.125), 0.002, 0.032)

# ================= HEAD (BDX bar) =======================================
hz0 = 0.141          # head base bottom, above the NPITCH collar top (~0.1394)
hzc = hz0 + HEAD_H * MM / 2
hcx = 0.022
face_x = hcx + HEAD_D * MM / 2
# top shell (hollowed, open at bottom) + base plate closing it
hs = cube("HEAD_SHELL", S(HEAD_D, HEAD_W, HEAD_H), (hcx, 0, hzc), "HEAD", WHITE, bev=0.007, defer=True)
cut_box(hs, ((HEAD_D - 3.2) * MM, (HEAD_W - 3.2) * MM, 0.0229),
        (hcx, 0, hz0 + 0.01095))
# 4 interior corner posts fused to the shell, insert pocket at post bottom
for i, (dx, dy) in enumerate([(-0.013, -0.026), (-0.013, 0.026),
                               (0.013, -0.026), (0.013, 0.026)]):
    p = cyl(f"HPOST_{i}", BOSS_R, 0.020, (hcx + dx, dy, hz0 + 0.0127), "HEAD",
            WHITE, verts=24)
    fuse_into(hs, p)
    bore(hs, (hcx + dx, dy, hz0 + 0.0045), HOLE_R, 0.004)
    insert(f"HINS_{i}", (hcx + dx, dy, hz0 + 0.005))
hb = cube("HEAD_BASE", (S(HEAD_D - 10, HEAD_W - 11, 2)), (hcx, 0, hz0 + 0.0017), "HEAD", WHITE)
# base plate: horn clearance + 4 corner holes + cable conduit + neck-arm pilots
bore(hb, (0.020 + SV[0] * 0.28, 0, hz0 + 0.0017), 0.0045, 0.004)
bore(hb, (-0.0145, 0.004, hz0 + 0.0017), 0.0025, 0.004)  # cable conduit hole
for dx in (-0.002, 0.002):
    bore(hb, (0.0125 + dx, 0.00945, hz0 + 0.0017), 0.0009, 0.004)
for i, (dx, dy) in enumerate([(-0.013, -0.026), (-0.013, 0.026),
                               (0.013, -0.026), (0.013, 0.026)]):
    bore(hb, (hcx + dx, dy, hz0 + 0.0017), HOLE_R, 0.004)
# face plate + real holes: 2 eye apertures + corner screws
fp_w, fp_h = HEAD_W * 0.88 * MM, HEAD_H * 0.80 * MM
fp = cube("FACE_PLATE", (0.005, fp_w, fp_h), (face_x + 0.0025, 0, hzc), "HEAD", DARK, bev=0.0012)
eye_r, eye_z, eye_dy = 0.008, hzc + 0.001, 0.0135
for sgn in (1, -1):
    bore(fp, (face_x + 0.0025, sgn * eye_dy, eye_z), 0.010, 0.007, axis="X")
    # matching bore through the shell front wall — camera/ToF see through,
    # LED ring recess clears it too
    bore(hs, (face_x - 0.0015, sgn * eye_dy, eye_z), 0.0088, 0.004, axis="X")
for i, (dy, dz) in enumerate([(-0.027, -0.008), (-0.027, 0.008),
                               (0.027, -0.008), (0.027, 0.008)]):
    bore(fp, (face_x + 0.0025, dy, hzc + dz), HOLE_R, 0.007, axis="X")
    screw(f"FSCR_{i}", (face_x + 0.0048, dy, hzc + dz), axis="X")
    # matching posts fused to the shell front inner face; M2 self-tap path
    p = cyl(f"FPPOST_{i}", 0.0018, 0.004,
            (face_x - 0.0029, dy, hzc + dz), "HEAD", WHITE,
            rot=(0, 1.5708, 0), verts=24)
    fuse_into(hs, p)
    bore(hs, (face_x - 0.0020, dy, hzc + dz), 0.0009, 0.008, axis="X")
# eye bezels + lit lenses: bezel is a real ring — centre bore for the lens,
# front counterbore seats the LED ring (light floods the lens back)
for sgn, tag in ((1, "L"), (-1, "R")):
    ring = cyl(f"EYE_RING_{tag}", 0.009, 0.004,
               (face_x + 0.003, sgn * eye_dy, eye_z),
               "HEAD", DARK, rot=(0, 1.5708, 0))
    bore(ring, (face_x + 0.003, sgn * eye_dy, eye_z), 0.0055, 0.006, axis="X")
    # rear counterbore seats the LED torus (its tube is r6.4+1.2 = 7.6)
    bore(ring, (face_x + 0.0019, sgn * eye_dy, eye_z), 0.0084, 0.0022, axis="X")
    cyl(f"EYE_{tag}", 0.0048, 0.003, (face_x + 0.006, sgn * eye_dy, eye_z),
        "HEAD", EYEM, rot=(0, 1.5708, 0))
# speaker perforation dimples — real shallow bores in the plate face
# (cosmetic only; the actual speaker sits on the trunk +y wall)
for sgn in (1, -1):
    for r in range(2):
        for c in range(3):
            bore(fp, (face_x + 0.0045, sgn * (0.023 + c * 0.0025),
                      hzc - 0.003 + r * 0.005), 0.0011, 0.002, axis="X")
# side pods: ear ring + cap on the shell face; cap peg seats into wall bore
for sgn, tag in ((1, "L"), (-1, "R")):
    er = cyl(f"EAR_{tag}", 0.006, 0.003, (hcx, sgn * (HEAD_W / 2 * MM + 0.003), hzc),
             "HEAD", GREY, rot=(1.5708, 0, 0))
    bore(er, (hcx, sgn * (HEAD_W / 2 * MM + 0.003), hzc), 0.0024, 0.004, axis="Y")
    cap = cyl(f"EAR_CAP_{tag}", 0.003, 0.004,
              (hcx, sgn * (HEAD_W / 2 * MM + 0.008), hzc),
              "HEAD", ORANGE, rot=(1.5708, 0, 0))
    peg = cyl(f"EAR_CAP_{tag}_peg", 0.0018, 0.008,
              (hcx, sgn * (HEAD_W / 2 * MM + 0.004), hzc),
              "HEAD", ORANGE, rot=(1.5708, 0, 0))
    fuse_into(cap, peg)
    bore(hs, (hcx, sgn * (HEAD_W / 2 * MM - 0.001), hzc), 0.002, 0.005, axis="Y")
# antenna: mast peg drops into a seat bore in the shell top
bore(hs, (hcx - HEAD_D * MM * 0.32, -HEAD_W * MM * 0.30, hz0 + HEAD_H * MM - 0.001),
     0.0012, 0.005)
cyl("ANT_MAST", 0.0009, 0.016,
    (hcx - HEAD_D * MM * 0.32, -HEAD_W * MM * 0.30, hz0 + HEAD_H * MM + 0.006),
    "HEAD", GREY, rot=(0.05, 0.08, 0))
# chin: flush under the base front edge, 2x M2 up into the base plate
chin = cube("CHIN", (0.009, fp_w * 0.5, 0.006), (face_x - 0.005, 0, hz0 - 0.003), "HEAD", WHITE, bev=0.003, defer=True)
for dy2 in (-0.010, 0.010):
    bore(chin, (face_x - 0.004, dy2, hz0 - 0.0058), 0.0019, 0.0012)
    bore(chin, (face_x - 0.004, dy2, hz0 - 0.003), HOLE_R, 0.006)
    bore(hb, (face_x - 0.004, dy2, hz0 + 0.0017), 0.0009, 0.003)

# eye internals: sensor pods on brackets behind the bores
cam_o = cyl("CAM_POD", 0.0045, 0.010, (face_x - 0.010, eye_dy, eye_z), "COMPONENTS", CAMM, rot=(0, 1.5708, 0))
cam_o["component"] = "OV2640 camera (behind L eye)"
cl = cyl("CAM_LENS", 0.003, 0.003, (face_x - 0.0035, eye_dy, eye_z), "COMPONENTS", CAMM, rot=(0, 1.5708, 0))
cl["proxy"] = True
tof = cube("TOF_POD", S(8, 8, 4), (face_x - 0.010, -eye_dy, eye_z), "COMPONENTS", GREEN)
tof["component"] = "VL53L0X ToF (behind R eye)"
# brackets: cheek walls holding the pods, fused to the front inner face
for sgn, pz in ((1, "CAM"), (-1, "TOF")):
    for csgn in (-1, 1):
        b = cube(f"{pz}_BRK{csgn}", (0.009, 0.0016, 0.012),
             (face_x - 0.0055, sgn * eye_dy + csgn * 0.006, eye_z - 0.001), "HEAD", WHITE)
        fuse_into(hs, b)
# LED rings recessed into the bezel counterbore
for sgn, tag in ((1, "L"), (-1, "R")):
    bpy.ops.mesh.primitive_torus_add(major_radius=eye_r * 0.8, minor_radius=0.0012,
                                     major_segments=28,
                                     location=(face_x + 0.0006, sgn * eye_dy, eye_z),
                                     rotation=(0, 1.5708, 0))
    o = bpy.context.active_object
    o.name = f"LEDRING_{tag}"
    o["component"] = "WS2812 8-LED ring (eye glow)"
    o["proxy"] = True
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


# ================= print export ===========================================
# Fuse each part's sub-primitives into ONE manifold solid, then export STL
# at real mm scale (model is in meters -> global_scale 1000).

def union_group(name, members):
    """Boolean-union all member objects into the first; rename to `name`."""
    members = [m for m in members if m is not None]
    if not members:
        return None
    base = members[0]
    for other in members[1:]:
        v0 = mesh_vol(base)
        vc = abs(mesh_vol(other))
        oname = other.name
        nm0 = nonmanifold(base)
        merged = False
        for attempt in range(3):
            md = base.modifiers.new("u", "BOOLEAN")
            md.operation = "UNION"; md.object = other
            md.solver = "FAST" if attempt == 2 else "EXACT"
            bpy.context.view_layer.objects.active = base
            try:
                bpy.ops.object.modifier_apply(modifier="u")
            except RuntimeError:
                pass
            if mesh_vol(base) > v0 + max(vc * 0.02, 1e-15):
                merged = True
                break
            clean(base)
            clean(other)
        if merged:
            bpy.data.objects.remove(other)
            nm_now = nonmanifold(base)
            if nm_now != nm0:
                print(f"[nm] {name} <- {oname}: {nm0} -> {nm_now} edges")
        else:
            # silent no-op union: keep the child — slicers union overlapping
            # shells implicitly, and the verifier still sees the geometry
            print(f"[union-FAIL] {name} <- {oname} (kept)")
            other.name = f"{name}_u{oname[-6:]}"
            base = _rejoin(base, other)
            base.name = name
            continue
    base.name = name
    return base


def _rejoin(base, other):
    """join() keeps both shells in one object — used when boolean union
    silently no-ops; overlapping shells slice identically to a union."""
    bpy.ops.object.select_all(action="DESELECT")
    base.select_set(True)
    other.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()
    return base


def stl_export(o):
    for s in bpy.context.selected_objects:
        s.select_set(False)
    o.select_set(True)
    bpy.ops.wm.stl_export(filepath=os.path.join(PARTS, o.name + ".stl"),
                          export_selected_objects=True, global_scale=1000)
    o.select_set(False)


obj = bpy.data.objects.get
def grp_objs(prefixes):
    return [obj(n) for n in
            (o.name for o in bpy.data.objects)
            if any(n == p or n.startswith(p + ".") for p in prefixes)]

GROUPS = {}
for tag in ("L", "R"):
    # serial-chain leg members (each is one fused print part)
    GROUPS[f"HIP_{tag}"] = [f"HIP_{tag}_top"]
    GROUPS[f"HYAW_{tag}_collar"] = [f"HYAW_{tag}_collar"]
    GROUPS[f"HROLL_{tag}_cover"] = [f"HROLL_{tag}_cover"]
    GROUPS[f"FEMUR_{tag}"] = [f"HPITCH_{tag}_floor", f"HPITCH_{tag}_cheek-1",
                              f"HPITCH_{tag}_cheek1", f"HPITCH_{tag}_back",
                              f"HPITCH_{tag}_boss0", f"HPITCH_{tag}_boss1",
                              f"FEMUR_{tag}_arm"]
    GROUPS[f"HPITCH_{tag}_collar"] = [f"HPITCH_{tag}_collar"]
    GROUPS[f"SHIN_{tag}"] = [f"KNEE_{tag}_floor", f"KNEE_{tag}_cheek-1",
                             f"KNEE_{tag}_cheek1", f"KNEE_{tag}_back",
                             f"KNEE_{tag}_boss0", f"KNEE_{tag}_boss1",
                             f"SHIN_{tag}_link"]
    GROUPS[f"KNEE_{tag}_collar"] = [f"KNEE_{tag}_collar"]
    for p in ("FOOT", "SOLE", "TOE", "FLIPPER", "FLIP_TIP"):
        GROUPS[f"{p}_{tag}"] = [f"{p}_{tag}"]
GROUPS["NPITCH_pocket"] = ["NPITCH_floor", "NPITCH_cheek-1", "NPITCH_cheek1",
                           "NPITCH_back", "NPITCH_boss0", "NPITCH_boss1",
                           "NPITCH_flange"]
GROUPS["NPITCH_collar"] = ["NPITCH_collar"]
GROUPS["NECK_ARM"] = ["NECK_ARM"]
GROUPS["TRUNK_F"] = ["TRUNK_F"]
GROUPS["TRUNK_R"] = ["TRUNK_R"]
GROUPS["CHEST_PANEL"] = ["CHEST_PANEL"]
for tag in ("L", "R"):
    GROUPS[f"FLIPPER_{tag}"] = [f"FLIPPER_{tag}"]
    GROUPS[f"FLIP_TIP_{tag}"] = [f"FLIP_TIP_{tag}"]
GROUPS["NECK_CABLE"] = ["NECK_CABLE"]
GROUPS["HEAD_SHELL"] = ["HEAD_SHELL"]
GROUPS["HEAD_BASE"] = ["HEAD_BASE"]
GROUPS["FACE_PLATE"] = ["FACE_PLATE"]
for tag in ("L", "R"):
    GROUPS[f"EYE_RING_{tag}"] = [f"EYE_RING_{tag}"]
    GROUPS[f"EYE_{tag}"] = [f"EYE_{tag}"]
    GROUPS[f"EAR_{tag}"] = [f"EAR_{tag}"]
    GROUPS[f"EAR_CAP_{tag}"] = [f"EAR_CAP_{tag}"]
GROUPS["ANT_MAST"] = ["ANT_MAST"]
GROUPS["CHIN"] = ["CHIN"]

# resolve each member string: exact name, Blender .001 dedup suffixes, and
# any <name>_u* children kept after a failed fuse_into. A bare startswith
# would collide (EYE_R would also capture EYE_RING_L/R).
def resolve_all(m):
    out = []
    if obj(m):
        out.append(obj(m))
    out += [o for o in bpy.data.objects
            if (o.name.startswith(m + ".") or o.name.startswith(m + "_u"))
            and o not in out]
    return out

made = []
for gname, members in GROUPS.items():
    objs = []
    for m in members:
        objs += resolve_all(m)
    objs = list(dict.fromkeys(objs))
    fused = union_group(gname, objs)
    if fused is None:
        print(f"[skip] {gname}: no members")
        continue
    bv = fused.get("bev")
    nm_pre = nonmanifold(fused)
    if bv:
        md = fused.modifiers.new("bev", "BEVEL")
        md.width = bv; md.segments = 3; md.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = fused
        try:
            bpy.ops.object.modifier_apply(modifier="bev")
        except RuntimeError:
            print(f"[bev-FAIL] {gname}")
    nm = nonmanifold(fused)
    if nm != nm_pre:
        print(f"[bev-nm] {gname}: {nm_pre} -> {nm}")
    stl_export(fused)
    made.append((gname, nm))
    print(f"[stl] {gname}  nonmanifold_edges={nm}")

print(f"[export] {len(made)} fused printable parts")

# ================= beauty renders (of the fused production parts) =========
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

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "knoll-mini.blend"))
print("[done]")
