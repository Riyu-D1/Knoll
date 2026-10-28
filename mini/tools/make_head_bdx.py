"""Session 8A: BDX-droid head shell for the Knoll Mini.

Replaces the outer head dressing (top_head_shell, bottom_head_shell, face_part, jaw, jaw_soft,
soft_mouth_top, noenoeil) with a wide, flat, boxy BDX head: two round eyes in raised bezels,
side vent grilles, a shallow raised top panel, angled antennae, a small lamp bump, a chamfered
lower front edge and a recessed bottom with a swept neck opening.

Everything is authored in the jaw_soft LOCAL frame (mm): +lx = up (world +z), +ly = robot-left
(world +y), +lz = back (world -x); the face looks toward -lz. Parts land via
spec.BDX_HEAD_PARTS (loaded at the jaw_soft body frame) when spec.HEAD_MODE == "bdx".

Structure follows the xgoduck reference (~/xgoduck_hardware/structure): a roomy outer shell
with real margin around the servo cluster, servos carried by the existing chassis
(motor_support + yaw_roll_motion, unchanged), a lid closing the shell (our clamshell split),
and a bottom neck opening swept for the joint ranges. We copy no meshes - proportions only.

Run:  python tools/make_head_bdx.py
Output: parts/current/{top_head_shell,bottom_head_shell,head_eye_lens_l,
                     head_antenna_left,head_antenna_right,elec_eye_rings_x2}.stl
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np, trimesh, spec, assembly
from trimesh.transformations import rotation_matrix as RM

ENG = dict(engine="manifold")

# ------------------------------------------------- parameters (mm, jaw_soft local)
WALL   = 2.0      # enclosure wall (task: >= 2.0)
CLEAR  = 1.0      # interior clearance to swept cloud / contents (task: >= 1.0)

# Outer footprint. Interior must cover static contents (ly -25.5..30.5, lz -52.8..33.7)
# and the swept cloud (ly -30.6..19.3 above lx -13), and carry the face bezels.
LY_LO, LY_HI = -34.0, 33.5      # width 67.5  -> interior -32..31.5
LZ_LO, LZ_HI = -56.0, 36.7      # depth 92.7  -> interior -54..34.7
LX_BOT       = -15.0            # outer bottom -> recessed neck vestibule under the head
LX_FLOOR     = -13.0            # interior floor surface
LX_CEIL      = 25.0             # interior ceiling (swept cloud <= 24 outside the tip patch)
LX_TOP       = 27.0             # outer top surface
PANEL_LY     = (-24.0, 10.0)    # shallow raised top panel (covers the swept-tip patch
PANEL_LZ     = (-28.0, 10.0)    #  ly -18..-7 / lz -22..-4.5 reaching lx 29.6)
PANEL_INT    = 30.8             # interior under the panel (29.6 + 1.0 + margin)
PANEL_TOP    = 32.8             # panel outer surface
SPLIT        = -3.0             # clamshell seam (bottom below, top above)
SKIRT        = -5.4             # top-shell skirt overlaps the bottom rim down to here

# Face features. Camera axis: ly = 0, lx = 11.16, along -z. Right eye = camera eye at ly 0.
EYE_LX    = 11.2
EYE_LY    = (0.0, -19.5)        # (right/camera, left/LED)
EYE_BEZ_D = 20.0                # raised round bezel, identical both eyes
EYE_BEZ_P = 3.4                 # bezel proud of the face
EYE_BORE  = 16.0                # eye bore through bezel + face
CAM_HOLE  = 10.0                # camera aperture continued into the interior
LAMP_LY, LAMP_LX, LAMP_D = 18.0, 11.0, 8.0   # small round lamp right of the eyes (ToF window)
MIC_LY, MIC_LX = -16.0, -1.5    # mic pin-hole low on the face
GRILLE_D  = 1.7
# antennae: angled rods at the rear top corners (200 mm height cap bounds the tips)
ANT_LY, ANT_LZ = 29.0, 22.0
ANT_TILT   = 30.0               # deg outward from vertical
ANT_ROD_D  = 2.0
ANT_SOCK_D = 2.2
ANT_IN     = 4.0
ANT_ROD_L  = 12.0               # total rod length

# chamfer lines: two contact points in (lz,lx) or (ly,lz) plane coords.
CH_FRONT  = ((-56.0, -7.0), (-47.0, -15.0))      # lower-front edge  (lz,lx)
CH_TOPF   = ((-56.0, 22.0), (-50.0, 27.0))       # small top-front chamfer (lz,lx)
CH_CR_L   = ((-30.5, -56.0), (-34.0, -49.0))     # left front corner (ly,lz) -> vent panel
CH_CR_R   = ((30.0, -56.0), (33.5, -49.0))       # right front corner (ly,lz) -> vent panel

NECK_GROW  = 2.0                # neck-opening margin past the swept footprint
PILOT_D    = 2.0
GRILLE_LX  = (5.0, 10.0)        # two rows of vent holes on each corner chamfer

SEAM_PADS = [   # (axis 'y'|'z', wall sgn, center coord, half width) - screw bosses in bottom rim
    ("y", -1, -48.0, 4.5), ("y", -1, 28.0, 4.5),
    ("y", +1, -48.0, 4.5), ("y", +1, 28.0, 4.5),
    ("z", -1, -18.0, 4.0), ("z", -1, 18.0, 4.0),
]
CHASSIS_TABS = [(-15.0, -1.0), (15.0, -1.0)]     # (ly, lx) pads on the interior back wall

# ------------------------------------------------------------------ helpers
def box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m

def cyl(r, h, center=(0, 0, 0), axis=2, tilt=None):
    m = trimesh.creation.cylinder(radius=r, height=h, sections=40)
    if axis == 0: m.apply_transform(RM(np.pi / 2, [0, 1, 0]))
    if axis == 1: m.apply_transform(RM(-np.pi / 2, [1, 0, 0]))
    if tilt is not None: m.apply_transform(RM(np.radians(tilt[0]), tilt[1]))
    m.apply_translation(center)
    return m

def ring(r_out, r_in, h, center=(0, 0, 0), axis=2):
    m = trimesh.boolean.difference([cyl(r_out, h), cyl(r_in, h + 2)], **ENG)
    m.apply_translation(center)
    return m

def _halfspace(org, n):
    B = trimesh.creation.box(extents=(900, 900, 900))
    z = np.array([0, 0, 1.0]); n = n / np.linalg.norm(n)
    v = np.cross(z, n); c = np.dot(z, n)
    if np.linalg.norm(v) < 1e-9:
        R = np.eye(3) if c > 0 else np.diag([1.0, -1, -1])
    else:
        vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        R = np.eye(3) + vx + vx @ vx * (1 - c) / (np.linalg.norm(v) ** 2)
    M = np.eye(4); M[:3, :3] = R; B.apply_transform(M)
    B.apply_translation(org + n * 450.0)
    return B

def chamfer(mesh, line, free_axis, coords, remove_side, offset=0.0):
    """Cut a straight chamfer: `line` = two contact points in `coords` order (the two non-free
    axes). The removed half-space is on the `remove_side` of the line's normal; `offset` shifts
    the cut plane along that normal (offset=e keeps a uniform wall for grown/shrunk copies)."""
    idx = list(coords)
    (a0, b0), (a1, b1) = line
    d = np.array([a1 - a0, b1 - b0]); d /= np.linalg.norm(d)
    n2 = np.array([-d[1], d[0]]) * remove_side
    n = np.zeros(3); n[idx[0]], n[idx[1]] = n2[0], n2[1]
    org = np.zeros(3); org[idx[0]], org[idx[1]] = a0, b0
    org += n * offset
    return trimesh.boolean.difference([mesh, _halfspace(org, n)], **ENG)

def _wedge(e=0.0):
    """Lower-right wall flare: the swept neck mouth reaches ly ~-37.5 at the floor level,
    tapering back to -31 by lx -1. Trapezoid in (lx,ly) extruded over lz -24.5..-1.5."""
    from shapely.geometry import Polygon as SP
    poly = SP([(LX_BOT - e, -41.0 - e), (LX_BOT - e, -31.5 - e), (-1.0, -31.5 - e), (-1.0, -34.2 - e)])
    m = trimesh.creation.extrude_polygon(poly, 26.0 + 2 * e)
    v = m.vertices.copy()
    m.vertices = np.stack([v[:, 0], v[:, 1], v[:, 2] - 25.5 - e], 1)
    return m

def outer_solid(e=0.0):
    """The outer profile grown by `e` on every face (e=-WALL gives the interior void)."""
    m = box(LX_BOT - e, PANEL_TOP + e, LY_LO - e, LY_HI + e, LZ_LO - e, LZ_HI + e)
    t = LX_TOP + e
    py = (PANEL_LY[0] - e, PANEL_LY[1] + e); pz = (PANEL_LZ[0] - e, PANEL_LZ[1] + e)
    m = trimesh.boolean.difference(
        [m, box(t, PANEL_TOP + e + 2, LY_LO - e - 1, py[0], LZ_LO - e - 1, LZ_HI + e + 1),
         box(t, PANEL_TOP + e + 2, py[1], LY_HI + e + 1, LZ_LO - e - 1, LZ_HI + e + 1),
         box(t, PANEL_TOP + e + 2, py[0], py[1], LZ_LO - e - 1, pz[0]),
         box(t, PANEL_TOP + e + 2, py[0], py[1], pz[1], LZ_HI + e + 1)], **ENG)
    m = chamfer(m, CH_FRONT, 1, (2, 0), -1, e)     # removes the (-lz,-lx) corner
    m = chamfer(m, CH_TOPF, 1, (2, 0), +1, e)      # removes the (-lz,+lx) corner
    m = chamfer(m, CH_CR_L, 0, (1, 2), +1, e)      # removes the (-ly,-lz) corner
    m = chamfer(m, CH_CR_R, 0, (1, 2), -1, e)      # removes the (+ly,-lz) corner
    return trimesh.boolean.union([m, _wedge(e)], **ENG)

CACHE = Path("/tmp/head_bdx_cloud.npz")

def swept_cloud(force=False):
    if not force and CACHE.exists():
        d = np.load(CACHE); return d["cloud"], d["by_mesh"]
    items0 = assembly.build()
    parts = []
    for i in items0:
        if i.body in ("yaw_roll_motion", "neck_pitch", "neck"):
            Tinv = np.linalg.inv(i.T)
            Vw = np.vstack([i.mesh_obj.vertices.T, np.ones(len(i.mesh_obj.vertices))])
            parts.append((i.body, i.mesh, i.T.copy(), (Tinv @ Vw)[:3].T))
    bp0 = {k: v.copy() for k, v in assembly.BODY_POSE.items()}
    geomT = {(b, m): np.linalg.inv(bp0[b]) @ T0 for b, m, T0, V in parts}
    poses = [{"head_yaw": a} for a in range(-120, 121, 8)]
    poses += [{"head_roll": a} for a in range(-25, 26, 5)]
    poses += [{"head_pitch": a} for a in range(-45, 46, 5)]
    poses += [{}]
    out, names = [], []
    for q in poses:
        assembly._walk(want_meshes=False, q=q)
        Ti = np.linalg.inv(assembly.BODY_POSE["jaw_soft"])
        for b, mesh, T0, V in parts:
            M = Ti @ assembly.BODY_POSE[b] @ geomT[(b, mesh)]
            out.append((M @ np.vstack([V.T, np.ones(len(V))]))[:3].T)
            names += [mesh] * len(V)
    np.savez(CACHE, cloud=np.vstack(out), by_mesh=np.array(names))
    return np.vstack(out), np.array(names)

# ------------------------------------------------------------------ build
def main():
    print("[1] swept cloud ...")
    cloud, cloud_mesh = swept_cloud()
    slab = cloud[(cloud[:, 0] > LX_BOT - 0.6) & (cloud[:, 0] < LX_FLOOR + 4.6)]
    print("    cloud:   lx[%.1f,%.1f] ly[%.1f,%.1f] lz[%.1f,%.1f]"
          % (cloud[:, 0].min(), cloud[:, 0].max(), cloud[:, 1].min(), cloud[:, 1].max(),
             cloud[:, 2].min(), cloud[:, 2].max()))
    print("    floor slab %.1f..%.1f footprint: ly[%.1f,%.1f] lz[%.1f,%.1f] n=%d"
          % (LX_BOT, LX_FLOOR + 4, slab[:, 1].min(), slab[:, 1].max(), slab[:, 2].min(), slab[:, 2].max(), len(slab)))

    print("[2] shell = outer - interior ...")
    shell = trimesh.boolean.difference([outer_solid(0.0), outer_solid(-WALL)], **ENG)
    print("    watertight=%s vol=%.1f cm3" % (shell.is_watertight, shell.volume / 1000))

    print("[3] neck opening through the floor + lower wall band ...")
    res = 0.4
    ys = np.arange(LY_LO - 9, LY_HI + 9 + res, res); zs = np.arange(LZ_LO - 9, LZ_HI + 9 + res, res)
    occ = np.zeros((len(ys), len(zs)), bool)
    iy = np.clip(((slab[:, 1] - ys[0]) / res).astype(int), 0, len(ys) - 1)
    iz = np.clip(((slab[:, 2] - zs[0]) / res).astype(int), 0, len(zs) - 1)
    occ[iy, iz] = True
    import scipy.ndimage as ndi
    occ = ndi.binary_dilation(occ, iterations=int(np.ceil(NECK_GROW / res)))
    occ = ndi.binary_closing(occ, structure=np.ones((11, 11)))
    occ = ndi.binary_dilation(occ, iterations=2)
    from skimage import measure
    from shapely.geometry import Polygon as SP
    contours = [c for c in measure.find_contours(occ.astype(float), 0.5) if len(c) > 20]
    big = max(contours, key=len)
    hole0 = np.stack([ys[0] + big[:, 0] * res, zs[0] + big[:, 1] * res], 1)
    sp = SP(hole0).buffer(0).simplify(0.6).buffer(0.6)
    hole = np.array(sp.exterior.coords)[:, :2]
    print("    hole ly[%.1f,%.1f] lz[%.1f,%.1f]"
          % (hole[:, 0].min(), hole[:, 0].max(), hole[:, 1].min(), hole[:, 1].max()))
    prism = trimesh.creation.extrude_polygon(SP(hole), (LX_FLOOR + 4) - (LX_BOT - 2))
    v = prism.vertices.copy()
    prism.vertices = np.stack([v[:, 2] + LX_BOT - 2, v[:, 0], v[:, 1]], 1)
    shell = trimesh.boolean.difference([shell, prism], **ENG)
    hole_prism = prism
    print("    watertight=%s vol=%.1f cm3" % (shell.is_watertight, shell.volume / 1000))

    print("[4] face + top features ...")
    adds, cuts = [], []
    for ly in EYE_LY:                                   # identical raised bezels + bores
        adds.append(ring(EYE_BEZ_D / 2, EYE_BORE / 2, EYE_BEZ_P + 2.0,
                         (EYE_LX, ly, LZ_LO - EYE_BEZ_P / 2 + 0.05), axis=2))
    # left/LED eye: full-depth bore (the diffuser lens plugs it from inside)
    cuts.append(cyl(EYE_BORE / 2, 17, (EYE_LX, EYE_LY[1], LZ_LO - EYE_BEZ_P + 3), axis=2))
    # right/camera eye: bore through bezel+wall, then a CAM_HOLE aperture into the interior
    cuts.append(cyl(EYE_BORE / 2, 9.0, (EYE_LX, EYE_LY[0], LZ_LO - EYE_BEZ_P - 1.5), axis=2))
    cuts.append(cyl(CAM_HOLE / 2, 12, (EYE_LX, EYE_LY[0], LZ_LO + WALL + 3), axis=2))
    adds.append(cyl(LAMP_D / 2 + 1.4, 2.6, (LAMP_LX, LAMP_LY, LZ_LO - 1.2), axis=2))
    cuts.append(cyl(2.8, 18, (LAMP_LX, LAMP_LY, LZ_LO - 2), axis=2))             # ToF window
    cuts.append(cyl(1.0, 18, (MIC_LX, MIC_LY, LZ_LO - 2), axis=2))               # mic hole
    # antenna sockets: internal bosses + blind tilted holes
    for sgn in (-1, 1):
        adds.append(cyl(3.6, 6.0, (LX_TOP - 3.0, sgn * ANT_LY, ANT_LZ)))
        cuts.append(cyl(ANT_SOCK_D / 2, 8.5,
                        (LX_TOP - 2.4, sgn * ANT_LY, ANT_LZ), axis=0, tilt=(sgn * ANT_TILT, [0, 0, 1])))
    # speaker grille on the top face, right of the raised panel
    for gy in np.arange(21.0, 30.0, 3.4):
        for gz in np.arange(-4.0, 12.0, 3.4):
            cuts.append(cyl(GRILLE_D / 2, 10, (LX_TOP - 4, gy, gz)))
    # vent grilles on the two front corner chamfers (drilled along -lz through the panel)
    def lz_chamfer_left(ly):   return -56.0 - 1.4 * (ly + 30.5)
    def lz_chamfer_right(ly):  return -56.0 + 1.4 * (ly - 30.0)
    for xx in GRILLE_LX:
        for ly_ in (-32.0, -33.3):
            cuts.append(cyl(GRILLE_D / 2, 9, (xx, ly_, lz_chamfer_left(ly_) + 1.5), axis=2))
        for ly_ in (31.3, 32.6):
            cuts.append(cyl(GRILLE_D / 2, 9, (xx, ly_, lz_chamfer_right(ly_) + 1.5), axis=2))

    print("[5] bosses + tabs ...")
    for axis_, sgn, c_, w_ in SEAM_PADS:                  # seam screw pads inside the bottom rim
        if axis_ == "y":
            y0 = (LY_LO + WALL - 0.5) if sgn < 0 else (LY_HI - WALL - 4.5)
            adds.append(box(-10.5, -3.2, min(y0, y0 + 4.0), max(y0, y0 + 4.0), c_ - w_, c_ + w_))
            cuts.append(cyl(PILOT_D / 2, 16, (SPLIT - 1.5, sgn * (abs(LY_LO) if sgn < 0 else abs(LY_HI)), c_), axis=1))
        else:
            z0 = (LZ_LO + WALL - 0.5) if sgn < 0 else (LZ_HI - WALL - 4.5)
            adds.append(box(-10.5, -3.2, c_ - w_, c_ + w_, min(z0, z0 + 4.0), max(z0, z0 + 4.0)))
            cuts.append(cyl(PILOT_D / 2, 16, (SPLIT - 1.5, c_, sgn * (abs(LZ_LO) if sgn < 0 else abs(LZ_HI))), axis=2))
    for ty, tx in CHASSIS_TABS:                            # chassis pads on interior back wall
        adds.append(box(-6.0, 2.0, ty - 4.5, ty + 4.5, 32.9, LZ_HI - WALL))
        cuts.append(cyl(PILOT_D / 2, 12, (tx, ty, LZ_HI - 1.5), axis=2))
    adds = [m for m in adds if m is not None]
    shell = trimesh.boolean.union([shell] + adds, **ENG)
    shell = trimesh.boolean.difference([shell] + cuts, **ENG)
    print("    watertight=%s vol=%.1f cm3" % (shell.is_watertight, shell.volume / 1000))

    print("[6] split + skirt ...")
    top = trimesh.boolean.intersection(
        [shell, box(SPLIT, PANEL_TOP + 4, LY_LO - 5, LY_HI + 5, LZ_LO - 5, LZ_HI + 5)], **ENG)
    bottom = trimesh.boolean.intersection(
        [shell, box(LX_BOT - 5, SPLIT, LY_LO - 5, LY_HI + 5, LZ_LO - 5, LZ_HI + 5)], **ENG)
    skirt = trimesh.boolean.difference(
        [trimesh.boolean.intersection(
            [outer_solid(2.0), box(SKIRT, SPLIT + 0.01, LY_LO - 5, LY_HI + 5, LZ_LO - 5, LZ_HI + 5)], **ENG),
         outer_solid(0.4)], **ENG)
    top = trimesh.boolean.union([top, skirt], **ENG)
    for axis_, sgn, c_, w_ in SEAM_PADS:                   # re-cut screw holes through the skirt
        if axis_ == "y":
            top = trimesh.boolean.difference(
                [top, cyl(PILOT_D / 2, 16, (SPLIT - 1.5, sgn * (abs(LY_LO) if sgn < 0 else abs(LY_HI)), c_), axis=1)], **ENG)
        else:
            top = trimesh.boolean.difference(
                [top, cyl(PILOT_D / 2, 16, (SPLIT - 1.5, c_, sgn * (abs(LZ_LO) if sgn < 0 else abs(LZ_HI))), axis=2)], **ENG)
    for nm, m in [("top_head_shell", top), ("bottom_head_shell", bottom)]:
        print("    %-18s watertight=%s vol=%.1f cm3 ~%.1f g"
              % (nm, m.is_watertight, m.volume / 1000, m.volume / 1000 * spec.PETG_DENSITY_G_CM3 * spec.PRINT_FILL_FACTOR))

    print("[7] antennae + lens + LED ring ...")
    parts = {"top_head_shell": top, "bottom_head_shell": bottom}
    for sgn, nm in ((-1, "head_antenna_right"), (1, "head_antenna_left")):
        rod = cyl(ANT_ROD_D / 2, ANT_ROD_L, axis=0)
        rod.apply_translation((ANT_ROD_L / 2 - ANT_IN, 0, 0))
        rod.apply_transform(RM(np.radians(sgn * ANT_TILT), [0, 0, 1]))
        rod.apply_translation((LX_TOP - ANT_IN + 0.6, sgn * ANT_LY, ANT_LZ))
        print("    %s tip lx=%.1f -> world z %.1f (cap 207.2)"
              % (nm, rod.vertices[:, 0].max(), 169.643 + rod.vertices[:, 0].max()))
        parts[nm] = rod
    lens = trimesh.boolean.union(
        [cyl(EYE_BORE / 2 - 0.35, 5.8, (EYE_LX, EYE_LY[1], LZ_LO - EYE_BEZ_P + 2.8), axis=2),
         cyl(EYE_BORE / 2 + 1.8, 1.4, (EYE_LX, EYE_LY[1], LZ_LO + WALL + 0.8), axis=2)], **ENG)
    parts["head_eye_lens_l"] = lens
    parts["elec_eye_rings_x2"] = trimesh.boolean.union(
        [ring(12.5, 9.5, 2.4, (EYE_LX, EYE_LY[1], -45.0), axis=2),
         ring(9.0, 6.5, 2.4, (EYE_LX, EYE_LY[1], -47.6), axis=2)], **ENG)

    print("[8] clearance check (swept + contents vs shell material) ...")
    items0 = assembly.build()
    skip = {"elec_eye_rings_x2", "m12_lens_holder"}     # regenerated / seated at the aperture
    inside = np.vstack([i.mesh_obj.vertices for i in items0
                        if i.body == "jaw_soft" and i.mesh not in skip
                        and i.mesh not in spec.BDX_HEAD_PARTS])
    Tjs = np.linalg.inv(assembly.BODY_POSE["jaw_soft"])
    inside = (Tjs @ np.vstack([inside.T, np.ones(len(inside))]))[:3].T
    shell_all = trimesh.boolean.union([top, bottom], **ENG)
    outer = outer_solid(0.0); inner = outer_solid(-WALL)
    print("    shell watertight:", shell_all.is_watertight)

    def report(tag, V):
        V = V[:: max(1, len(V) // 60000)]
        d = np.abs(shell_all.nearest.signed_distance(V))
        in_mat = outer.contains(V) & ~inner.contains(V) & ~hole_prism.contains(V)
        bad = V[in_mat | (d < CLEAR)]
        print("    %-7s  min surf-dist %.2f mm   material-hits %d   flagged<%.1fmm %d"
              % (tag, d.min(), in_mat.sum(), CLEAR, (d < CLEAR).sum()))
        if len(bad):
            print("      ! region: lx[%.1f,%.1f] ly[%.1f,%.1f] lz[%.1f,%.1f]"
                  % (bad[:, 0].min(), bad[:, 0].max(), bad[:, 1].min(), bad[:, 1].max(),
                     bad[:, 2].min(), bad[:, 2].max()))
        return in_mat.sum()
    report("swept", cloud)
    # per-part content breakdown
    for i in items0:
        if i.body == "jaw_soft" and i.mesh not in skip and i.mesh not in spec.BDX_HEAD_PARTS:
            V = (Tjs @ np.vstack([i.mesh_obj.vertices.T, np.ones(len(i.mesh_obj.vertices))]))[:3].T
            nm = "content:%s" % i.mesh
            report(nm[:34], V)

    print("[9] export ...")
    for nm, m in parts.items():
        m.export(spec.WORK_DIR / f"{nm}.stl"); print("    wrote", spec.WORK_DIR / f"{nm}.stl")
    tot = sum(parts[k].volume for k in ("top_head_shell", "bottom_head_shell",
          "head_eye_lens_l", "head_antenna_left", "head_antenna_right"))
    print("    new printed volume %.1f cm3 -> ~%.1f g"
          % (tot / 1000, tot / 1000 * spec.PETG_DENSITY_G_CM3 * spec.PRINT_FILL_FACTOR))

if __name__ == "__main__":
    main()
