"""Refinement A: clean-surface rebuild of the BDX head shells (build123d CAD kernel).

Replaces tools/make_head_bdx.py output. SAME function, new skin: identical interior
dims, servo positions, neck-opening swept footprint (+2 mm), camera axis, seam-screw
positions, chassis tabs and >=1.0 mm swept clearance. Outer surfaces are now designed
CAD surfaces (extruded/lofted profiles, real fillets) instead of raster-boolean soup.

CAD frame used here:  X = head-local ly (robot-left +), Y = head-local lz (back +),
Z = head-local lx (up +).  Exported STLs are permuted back to the jaw_soft frame
(lx, ly, lz) with a cyclic (det +1) permutation - no mirroring.

Run:  ~/Knoll-cad-venv/bin/python tools/make_head_bdx_v2.py
Output: parts/current/{top_head_shell,bottom_head_shell,head_eye_lens_l,
        head_antenna_left,head_antenna_right,elec_eye_rings_x2}.stl
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from build123d import (
    Axis, Box, BuildPart, BuildSketch, Cylinder, Mode, Plane, Polygon, Pos,
    RectangleRounded, Rot, Sphere, export_stl, extrude, fillet, loft, offset,
)
import trimesh

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "parts" / "current"
CLOUD_NPY = Path("/tmp/refine_head_cloud.npy")

WALL = 2.0
CLEAR = 1.0
TOL, ANG = 0.05, 0.1                     # STL export tolerances (process rules)

# ------------------------------------------------- invariant envelope (jaw_soft mm)
LY_LO, LY_HI = -34.0, 33.5               # footprint width 67.5
LZ_LO, LZ_HI = -56.0, 36.7               # footprint depth 92.7
LX_BOT, LX_FLOOR = -15.0, -13.0          # outer bottom / interior floor
LX_CEIL, LX_TOP = 25.0, 27.0             # interior ceiling / outer top
PANEL_LY, PANEL_LZ = (-24.0, 10.0), (-28.0, 10.0)
PANEL_INT, PANEL_TOP = 30.8, 32.8
SPLIT = -3.0                             # clamshell seam
LIP_LO, LIP_HI = -6.2, -1.5              # skirt wraps the top rim down past the seam
LIP_PROUD = 1.5                          # brim sticks out this far past the walls

INT_LY, INT_LZ = (-32.0, 31.5), (-54.0, 34.7)   # interior walls (footprint - WALL)

# face features (unchanged positions)
EYE_LX = 11.2
EYE_LY = (0.0, -19.5)                    # (right/camera, left/LED)
EYE_BEZ_D, EYE_BORE = 21.0, 16.0
EYE_BEZ_FACE = LZ_LO - 2.8               # bezel outer face (2.8 proud of lz=-56)
CAM_HOLE = 10.0
LAMP_LY, LAMP_LX, LAMP_D = 18.0, 11.0, 8.0
MIC_LY, MIC_LX = -16.0, -1.5
GRILLE_D, GRILLE_PITCH = 1.8, 3.2

ANT_LY, ANT_LZ = 29.0, 22.0
ANT_TILT = 30.0                          # deg outward from vertical
ANT_SOCK_D = 2.2
ANT_ROD_D, ANT_ROD_L, ANT_IN = 2.0, 10.0, 4.0

# chamfer lines in (lz,lx) resp. (ly,lz) plane coords. Front/top-front same as v1.
# Front-corner chamfers are tuned to NOT pierce the interior corner (v1's did).
CH_FRONT = ((-56.0, -7.0), (-47.0, -15.0))
CH_TOPF = ((-56.0, 22.0), (-50.0, 27.0))
CH_CR_L = ((-30.5, -56.0), (-34.0, -52.0))
CH_CR_R = ((30.5, -56.0), (33.5, -52.0))

# neck opening: clean rounded rect + tab slot containing the swept floor-band
# footprint (lx -17..-9) + 2 mm.  swept: ly[-40.04,23.82] x lz[-42.93,17.16],
# with the -ly deep reach only over lz[-24.4,-1.4].
OPEN_MAIN = ((-28.0, 24.0), (-43.0, 17.5), 8.0)   # (ly lo/hi, lz lo/hi, corner r)
OPEN_TAB = ((-41.0, -24.0), (-27.0, 0.5), 3.0)
OPEN_TOP = -9.0                          # main prism top: through floor + lower band
OPEN_TAB_TOP = -12.4                     # tab slot pierces the floor band only

# -ly drafted bulge (lofted, tapered ends) so the tab slot stays inside material;
# inner face keeps >=1 mm from the swept cloud over lx -15..-1, lz ~-27..+1.
BULGE_LZ = (-31.0, 5.0)                  # loft span; end sections merge into wall
BULGE_MID = (-27.0, 1.0)                 # full-depth section band

SEAM_PADS = [                            # screw bosses in the bottom rim (as v1)
    ("y", -1, -48.0, 4.5), ("y", -1, 28.0, 4.5),
    ("y", +1, -48.0, 4.5), ("y", +1, 28.0, 4.5),
    ("z", -1, -18.0, 4.0), ("z", -1, 18.0, 4.0),
]
CHASSIS_TABS = [(-15.0, -1.0), (15.0, -1.0)]     # (ly, lx) pads on the back wall
PILOT_D = 2.0

JAW_SOFT_Z = 169.643                     # world z of jaw_soft origin


# ------------------------------------------------------------------ helpers
def cyl_dir(d, h, center, direction):
    """cylinder Ød x h centred at `center` with axis along `direction` (CAD frame)."""
    dn = np.asarray(direction, float); dn = dn / np.linalg.norm(dn)
    z = np.array([0, 0, 1.0]); v = np.cross(z, dn); s = np.linalg.norm(v)
    cc = float(np.dot(z, dn))
    m = Cylinder(d / 2, h)
    if s > 1e-9:
        m = Rot(axis=Axis((0, 0, 0), tuple(v)),
                angle=float(np.degrees(np.arccos(np.clip(cc, -1, 1))))) * m
    elif cc < 0:
        m = Rot(180, 0, 0) * m
    return Pos(*center) * m


def fused(parts):
    cut = parts[0]
    for c in parts[1:]:
        cut = cut + c
    return cut


def _loft_poly(full, end):
    """Loft a drafted bulge section: (ly,lx) polygons on sections at Y=lz;
    end sections collapse into the flat wall so the bulge blends smoothly."""
    secs = [end, full, full, end]
    zs = [BULGE_LZ[0], BULGE_MID[0], BULGE_MID[1], BULGE_LZ[1]]
    faces = []
    for z, poly in zip(zs, secs):
        pl = Plane(origin=(0, z, 0), x_dir=(1, 0, 0), y_dir=(0, 0, 1))
        faces.append(pl.location * Polygon(*[(ly, lx) for lx, ly in poly]))
    return loft(faces, ruled=True)


# polygon sections in (lx,ly) - outer face drafted -46@-15 -> -35.5@+0.9,
# inner face -44@-15 -> -33.5@+0.8: the swept -ly reach (max -40.04) stays
# inside the cavity, so the -ly wall needs no notch; ends collapse into the wall
WO_FULL = [(-15.0, -46.0), (-15.0, -30.6), (0.9, -30.6), (0.9, -35.5), (-1.0, -36.5)]
WO_END = [(-15.0, -33.8), (-15.0, -32.4), (0.9, -32.4), (0.9, -33.6), (-1.0, -33.9)]
WI_FULL = [(-15.0, -44.0), (-15.0, -30.5), (0.8, -30.5), (0.8, -33.5), (-1.0, -34.5)]
WI_END = [(-15.0, -33.5), (-15.0, -32.2), (0.8, -32.2), (0.8, -33.4), (-1.0, -33.6)]


def outer_solid(grow=0.0):
    """whole-enclosure outer solid; grow>0 used only for the conformal lip band."""
    g = grow
    f = Pos((LY_LO + LY_HI) / 2, (LZ_LO + LZ_HI) / 2, LX_BOT - g) * \
        RectangleRounded((LY_HI - LY_LO) + 2 * g, (LZ_HI - LZ_LO) + 2 * g, 6.0 + g)
    m = extrude(f, amount=LX_TOP - LX_BOT + 2 * g)
    f2 = Pos((PANEL_LY[0] + PANEL_LY[1]) / 2, (PANEL_LZ[0] + PANEL_LZ[1]) / 2,
             LX_TOP + g) * \
        RectangleRounded(PANEL_LY[1] - PANEL_LY[0] + 2 * g,
                         PANEL_LZ[1] - PANEL_LZ[0] + 2 * g, 3.0 + g)
    m = m + extrude(f2, amount=PANEL_TOP - LX_TOP)
    # chamfers (halfspace shifted outward by g along the cut normal)
    m = _chamfer_g(m, CH_FRONT, (1, 2), -1, g)
    m = _chamfer_g(m, CH_TOPF, (1, 2), +1, g)
    m = _chamfer_g(m, CH_CR_L, (0, 1), +1, g)
    m = _chamfer_g(m, CH_CR_R, (0, 1), -1, g)
    if g == 0.0:
        m = m + _loft_poly(WO_FULL, WO_END)
    else:
        m = m + _loft_poly(_poly_grow(WO_FULL, g), _poly_grow(WO_END, g))
    return m


def _chamfer_g(part, line, coords, remove_side, grow):
    idx = list(coords)
    (a0, b0), (a1, b1) = line
    d = np.array([a1 - a0, b1 - b0]); d /= np.linalg.norm(d)
    n2 = np.array([-d[1], d[0]]) * remove_side
    n = np.zeros(3); n[idx[0]], n[idx[1]] = n2[0], n2[1]
    org = np.zeros(3); org[idx[0]], org[idx[1]] = a0, b0
    org += n * grow                                   # shift the cut plane outward
    pl = Plane(origin=org.tolist(), z_dir=(-n).tolist())
    return part - (pl * Pos(0, 0, -450) * Box(900, 900, 900))


def _poly_grow(poly, g):
    """offset a convex (lx,ly) polygon outward by g: move each edge along its
    outward normal, keep edge-edge intersections as the new vertices."""
    if g == 0.0:
        return poly
    p = np.asarray(poly, float)
    c = p.mean(axis=0)
    out = []
    n = len(p)
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        d = b - a; d = d / np.linalg.norm(d)
        nrm = np.array([-d[1], d[0]])
        if np.dot(nrm, (a - c)) < 0:
            nrm = -nrm
        out.append((a + nrm * g, b + nrm * g))
    verts = []
    for i in range(n):
        (p0, p1), (q0, q1) = out[i - 1], out[i]
        A = np.stack([p1 - p0, q0 - q1], axis=1)
        if abs(np.linalg.det(A)) < 1e-9:
            verts.append(p1)
            continue
        t = np.linalg.solve(A, q0 - p0)[0]
        verts.append(p0 + t * (p1 - p0))
    return verts


def inner_void():
    f = Pos((INT_LY[0] + INT_LY[1]) / 2, (INT_LZ[0] + INT_LZ[1]) / 2, LX_FLOOR) * \
        RectangleRounded(INT_LY[1] - INT_LY[0], INT_LZ[1] - INT_LZ[0], 2.0)
    m = extrude(f, amount=LX_CEIL - LX_FLOOR)
    f2 = Pos((PANEL_LY[0] + PANEL_LY[1]) / 2, (PANEL_LZ[0] + PANEL_LZ[1]) / 2,
             LX_CEIL) * \
        RectangleRounded(PANEL_LY[1] - PANEL_LY[0] - 2 * WALL,
                         PANEL_LZ[1] - PANEL_LZ[0] - 2 * WALL, 2.0)
    m = m + extrude(f2, amount=PANEL_INT - LX_CEIL)
    return m + _loft_poly(WI_FULL, WI_END)


def opening_prism():
    f1 = Pos((OPEN_MAIN[0][0] + OPEN_MAIN[0][1]) / 2,
             (OPEN_MAIN[1][0] + OPEN_MAIN[1][1]) / 2, LX_BOT - 2.0) * \
        RectangleRounded(OPEN_MAIN[0][1] - OPEN_MAIN[0][0],
                         OPEN_MAIN[1][1] - OPEN_MAIN[1][0], OPEN_MAIN[2])
    f2 = Pos((OPEN_TAB[0][0] + OPEN_TAB[0][1]) / 2,
             (OPEN_TAB[1][0] + OPEN_TAB[1][1]) / 2, LX_BOT - 2.0) * \
        RectangleRounded(OPEN_TAB[0][1] - OPEN_TAB[0][0],
                         OPEN_TAB[1][1] - OPEN_TAB[1][0], OPEN_TAB[2])
    return extrude(f1, amount=OPEN_TOP - (LX_BOT - 2.0)) + \
        extrude(f2, amount=OPEN_TAB_TOP - (LX_BOT - 2.0))


# ------------------------------------------------------------------ main build
def build_shell():
    print("[1] outer solid + interior void")
    outer = outer_solid(0.0)
    inner = inner_void()
    shell = outer - inner
    print("    shell volume %.1f cm3" % (shell.volume / 1000))

    print("[2] neck opening (rounded rect + tab slot)")
    shell = shell - opening_prism()

    print("[3] face: eye bezels + recessed rings, bores, lamp, mic")
    for ly in EYE_LY:
        bez = Pos(ly, (EYE_BEZ_FACE + LZ_LO + 1.6) / 2, EYE_LX) * Rot(90, 0, 0) * \
            Cylinder(EYE_BEZ_D / 2, (LZ_LO + 1.6) - EYE_BEZ_FACE)
        shell = shell + bez
    face_cuts = []
    for i, ly in enumerate(EYE_LY):
        # recessed ring: Ø18.2 pocket ~0.9 deep below the bezel face
        face_cuts.append(
            cyl_dir(18.2, 2.2, (ly, EYE_BEZ_FACE - 0.2, EYE_LX), (0, -1, 0)))
        if i == 1:   # LED eye: Ø16 through
            face_cuts.append(
                cyl_dir(EYE_BORE, 12.0, (ly, LZ_LO - 3.0, EYE_LX), (0, -1, 0)))
        else:        # camera eye: Ø16 pocket + Ø10 aperture through wall
            face_cuts.append(
                cyl_dir(EYE_BORE, 5.0, (ly, LZ_LO - 2.2, EYE_LX), (0, -1, 0)))
            face_cuts.append(
                cyl_dir(CAM_HOLE, 14.0, (ly, LZ_LO + 2.0, EYE_LX), (0, -1, 0)))
    # lamp boss + ToF window + mic
    shell = shell + Pos(LAMP_LY, LZ_LO - 0.9, LAMP_LX) * Rot(90, 0, 0) * \
        Cylinder(LAMP_D / 2 + 1.4, 2.6)
    face_cuts.append(cyl_dir(2.8, 14.0, (LAMP_LY, LZ_LO - 1.0, LAMP_LX), (0, -1, 0)))
    face_cuts.append(cyl_dir(2.0, 14.0, (MIC_LY, LZ_LO - 1.0, MIC_LX), (0, -1, 0)))
    shell = shell - fused(face_cuts)
    # small fillet on the bezel front rims
    try:
        rims = [ed for ed in shell.edges()
                if abs(tuple(ed.center())[1] - EYE_BEZ_FACE) < 0.4
                and tuple(ed.bounding_box().size)[0] > 19.0]
        shell = fillet(rims, 0.8)
    except Exception as ex:
        print("    bezel fillet skipped:", str(ex).split(chr(10))[0][:70])

    print("[4] side-wall vent grilles: recessed panel + Ø%.1f @ %.1f grid"
          % (GRILLE_D, GRILLE_PITCH))
    gr_cuts = []
    for sgn in (-1, 1):
        xw = LY_LO if sgn < 0 else LY_HI      # outer side-wall face
        gr_cuts.append(Pos(xw + sgn * 0.3, -44.8, 9.8) * Box(1.6, 11.6, 21.6))
        for col in (-1, 0, 1):
            for row in range(6):
                lz = -44.8 + col * GRILLE_PITCH
                lx = 1.6 + row * GRILLE_PITCH
                gr_cuts.append(cyl_dir(GRILLE_D, 8.0,
                                       (xw + sgn * 2.0, lz, lx), (-sgn, 0, 0)))
    shell = shell - fused(gr_cuts)

    print("[5] antenna bosses + tilted sockets")
    sock = []
    for sgn in (-1, 1):
        boss = Pos(sgn * ANT_LY, ANT_LZ, LX_TOP + 1.5) * Cylinder(4.0, 4.0)
        try:
            be = [ed for ed in boss.edges() if tuple(ed.center())[2] > LX_TOP + 3.0]
            boss = fillet(be, 1.0)
        except Exception:
            pass
        shell = shell + boss
        tilt = np.radians(sgn * ANT_TILT)
        sock.append(cyl_dir(ANT_SOCK_D, 12.0,
                            (sgn * ANT_LY, ANT_LZ, LX_TOP + 2.6),
                            (np.sin(tilt), 0.0, np.cos(tilt))))
    shell = shell - fused(sock)

    print("[6] seam pads + chassis tabs")
    for axis_, sgn, c_, w_ in SEAM_PADS:
        if axis_ == "y":
            x0 = (INT_LY[0] - 0.6) if sgn < 0 else (INT_LY[1] - 4.0)
            shell = shell + Pos(x0 + 2.0, c_, (-10.5 - 3.2) / 2) * Box(4.0, 2 * w_, 7.3)
        else:
            z0 = (LZ_LO + WALL - 0.5) if sgn < 0 else (LZ_HI - WALL - 4.5)
            shell = shell + Pos(c_, z0 + 2.0, (-10.5 - 3.2) / 2) * Box(2 * w_, 4.0, 7.3)
    for ty, tx in CHASSIS_TABS:
        # overlap 0.9 into the back wall so the union is real, not tangent
        shell = shell + Pos(ty, (32.9 + LZ_HI - WALL + 0.9) / 2, -2.0) * \
            Box(9.0, (LZ_HI - WALL + 0.9) - 32.9, 8.0)

    print("[7] 0.4x0.3 panel-line groove at panel foot")
    ring = Pos((PANEL_LY[0] + PANEL_LY[1]) / 2, (PANEL_LZ[0] + PANEL_LZ[1]) / 2,
               LX_TOP - 0.01) * \
        RectangleRounded(PANEL_LY[1] - PANEL_LY[0] + 0.8,
                         PANEL_LZ[1] - PANEL_LZ[0] + 0.8, 2.4)
    ring = ring - Pos((PANEL_LY[0] + PANEL_LY[1]) / 2,
                      (PANEL_LZ[0] + PANEL_LZ[1]) / 2, LX_TOP - 0.01) * \
        RectangleRounded(PANEL_LY[1] - PANEL_LY[0], PANEL_LZ[1] - PANEL_LZ[0], 2.0)
    shell = shell - extrude(ring, amount=0.4)

    print("[8] split + conformal lip")
    top_box = Pos(0, 0, (SPLIT + 90) / 2) * Box(400, 400, 90 - SPLIT)
    bot_box = Pos(0, 0, (SPLIT - 100) / 2) * Box(400, 400, SPLIT + 100)
    top = shell - bot_box
    bottom = shell - top_box
    # skirt band: everything between the interior cavity and a +1.5 mm grown
    # outer surface, sliced to the band -> fuses to the top wall, hangs 1.5 proud
    lip = (outer_solid(LIP_PROUD) - inner) & \
        Pos(0, 0, (LIP_LO + LIP_HI) / 2) * Box(400, 400, LIP_HI - LIP_LO)
    top = top + lip

    print("[9] screw pilots (same positions as v1)")
    pilots = []
    for axis_, sgn, c_, w_ in SEAM_PADS:
        if axis_ == "y":
            xw = LY_LO if sgn < 0 else LY_HI
            pilots.append(
                cyl_dir(PILOT_D, 16.0, (sgn * abs(xw), c_, SPLIT - 1.5), (sgn, 0, 0)))
        else:
            zw = LZ_LO if sgn < 0 else LZ_HI
            pilots.append(
                cyl_dir(PILOT_D, 16.0, (c_, sgn * abs(zw), SPLIT - 1.5), (0, sgn, 0)))
    for ty, tx in CHASSIS_TABS:
        pilots.append(cyl_dir(PILOT_D, 12.0, (ty, LZ_HI - 1.5, tx), (0, 1, 0)))
    pc = fused(pilots)
    top = top - pc
    bottom = bottom - pc
    print("    top    %.1f cm3\n    bottom %.1f cm3"
          % (top.volume / 1000, bottom.volume / 1000))
    return top, bottom


def small_parts():
    parts = {}
    boss_top = LX_TOP + 3.5                     # boss upper surface
    for sgn, nm in ((-1, "head_antenna_right"), (+1, "head_antenna_left")):
        rod = Cylinder(ANT_ROD_D / 2, ANT_ROD_L) + \
            Pos(0, 0, ANT_ROD_L / 2 - 0.3) * Sphere(ANT_ROD_D / 2)
        rod = Pos(0, 0, ANT_ROD_L / 2 - ANT_IN) * rod
        rod = Rot(0, -sgn * ANT_TILT, 0) * rod   # tip leans outward in +-ly
        rod = Pos(sgn * ANT_LY, ANT_LZ, boss_top - 0.2) * rod
        tip_lx = boss_top - 0.2 + \
            (ANT_ROD_L + ANT_ROD_D / 2 - ANT_IN) * np.cos(np.radians(ANT_TILT))
        parts[nm] = rod
        print("    %s tip lx=%.1f -> world z %.1f" % (nm, tip_lx, JAW_SOFT_Z + tip_lx))
    # left-eye lens plug: Ø15.3 plug + Ø19.6 inner flange (flange inside, +lz)
    plug = Pos(0, 0, 0) * Cylinder(EYE_BORE / 2 - 0.35, 5.8)
    flan = Pos(0, 0, 3.6) * Cylinder(EYE_BORE / 2 + 1.8, 1.4)
    lens = Rot(-90, 0, 0) * (plug + flan)
    lens = Pos(EYE_LY[1], -56.0, EYE_LX) * lens
    parts["head_eye_lens_l"] = lens
    # LED ring pair placeholder (same as v1)
    ring1 = Pos(EYE_LY[1], -45.0, EYE_LX) * Rot(90, 0, 0) * \
        (Cylinder(12.5, 2.4) - Cylinder(9.5, 4))
    ring2 = Pos(EYE_LY[1], -47.6, EYE_LX) * Rot(90, 0, 0) * \
        (Cylinder(9.0, 2.4) - Cylinder(6.5, 4))
    parts["elec_eye_rings_x2"] = ring1 + ring2
    return parts


def export(part, name):
    """CAD (ly,lz,lx) -> jaw_soft (lx,ly,lz): cyclic permutation, det +1."""
    p = WORK / f"{name}.stl"
    export_stl(part, str(p), tolerance=TOL, angular_tolerance=ANG)
    m = trimesh.load(p, force="mesh")
    # drop zero-area sliver triangles left by tangent boolean intersections,
    # weld the seam vertices that opened up, and close pinholes
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    m.merge_vertices()
    m.fill_holes()
    P = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    m.vertices = (P @ m.vertices.T).T
    m.export(p)
    return m


def clearance_report(top, bottom):
    print("[10] clearance check vs swept cloud")
    cloud = np.load(CLOUD_NPY)
    shell_all = trimesh.util.concatenate([top, bottom])
    V = cloud[:: max(1, len(cloud) // 15000)]
    d = np.abs(shell_all.nearest.signed_distance(V))
    print("    swept cloud n=%d  min dist to shell %.2f mm   flagged<%.1f: %d"
          % (len(V), d.min(), CLEAR, (d < CLEAR).sum()))
    bad = V[d < CLEAR]
    if len(bad):
        print("    ! worst lx[%.1f,%.1f] ly[%.1f,%.1f] lz[%.1f,%.1f]"
              % (bad[:, 0].min(), bad[:, 0].max(), bad[:, 1].min(),
                 bad[:, 1].max(), bad[:, 2].min(), bad[:, 2].max()))


def main():
    top, bottom = build_shell()
    parts = small_parts()
    print("[export] jaw_soft frame")
    out = {}
    for nm, p in [("top_head_shell", top), ("bottom_head_shell", bottom)]:
        m = export(p, nm)
        out[nm] = m
        print("    %-18s watertight=%s vol=%.1f cm3" % (nm, m.is_watertight, m.volume / 1000))
    for nm, p in parts.items():
        m = export(p, nm)
        out[nm] = m
        print("    %-18s watertight=%s vol=%.1f cm3" % (nm, m.is_watertight, m.volume / 1000))
    clearance_report(out["top_head_shell"], out["bottom_head_shell"])
    tot = sum(out[k].volume for k in
              ("top_head_shell", "bottom_head_shell", "head_eye_lens_l",
               "head_antenna_left", "head_antenna_right"))
    print("    printed head volume %.1f cm3" % (tot / 1000))


if __name__ == "__main__":
    main()
