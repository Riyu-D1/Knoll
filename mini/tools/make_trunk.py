"""Refinement C: trunk, neck and body shells for the Knoll Mini.

Replaces the cosmetic trunk dressing (left_shell, right_shell, banana_pcb_locker —
moved to parts/attic_refine/) with a designed enclosure in the shared design
language (mini/docs/DESIGN_LANGUAGE.md):

  trunk_shell        main wrap: smooth rounded backpack over the two hip-yaw
                     servo pockets + chassis. Open bottom for the leg mechanisms,
                     rear bay aperture, neck port through the top-front deck,
                     integral right flank (vent grille), left flank closed by the
                     cover plate.
  trunk_cover_left   left side access panel: recessed flush panel + screw
                     dimples + interior ribs pressing the servo case faces.
  trunk_cover_rear   rear access cover / battery fairing over the power_support
                     cage perch; battery + electronics live in the rear bay.
  elec_*             electronics placeholders inside the rear bay.

The deck around the neck port is terraced by the head_pitch swept corridor
(a raised bezel cannot live there); the port gets an engraved trim groove.

All functional parts are untouched: trunk_base chassis, power_support cage,
neck_frame, neck_pitch yoke, yaw_roll_motion, motor_support, every servo seat,
horn interface, bearing seat, joint axis and range.

CAD: build123d solids (filleted boxes, extruded/lofted profiles). Swept-
clearance cutters derived from FK vertex clouds (same technique as
make_head_bdx.py). Authored in WORLD mm at zero pose, transformed into the
owning body's frame on export.

Run:  ~/Knoll-cad-venv/bin/python tools/make_trunk.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np, trimesh
import spec, assembly, scs0009
import build123d as bd
import xml.etree.ElementTree as ET
import scipy.ndimage as ndi
from shapely.geometry import Polygon as SP

WALL  = 2.0     # enclosure wall
CLEAR = 1.0     # required clearance to swept clouds
OUT   = spec.WORK_DIR
SWEPT = Path("/tmp/knoll_trunk_swept")

# ---------------------------------------------------------------- helpers
DESC, JBODY, JRNG = {}, {}, {}
def _desc_maps():
    root = ET.parse(spec.UPSTREAM_DIR / "robot_walk.xml").getroot()
    def walk(b, chain):
        n = b.get("name"); chain = chain + [n]
        for anc in chain:
            DESC.setdefault(anc, set()).add(n)
        for j in b.findall("joint"):
            if j.get("name"):
                JBODY[j.get("name")] = n
        for c in b.findall("body"):
            walk(c, chain)
    for b in root.find("worldbody").findall("body"):
        walk(b, [])
    JRNG.update({j.get("name"): [np.degrees(float(x)) for x in j.get("range").split()]
                 for j in root.iter("joint") if j.get("name") and j.get("range")})
_desc_maps()

def cloud(joint, lo_r, hi_r, step):
    """Swept vertex cloud of the joint's subtree over [lo,hi] deg (world mm), cached."""
    SWEPT.mkdir(exist_ok=True)
    f = SWEPT / f"{joint}_{lo_r}_{hi_r}_v2.npy"
    if f.exists():
        return np.load(f)
    moving = DESC[JBODY[joint]]
    lo, hi = max(lo_r, JRNG[joint][0]), min(hi_r, JRNG[joint][1])
    angles = sorted(set(np.r_[np.arange(lo, hi, step), hi, 0.0].round(2)))
    pts = []
    for a in angles:
        for it in assembly.build(q={joint: a}):
            if it.body in moving:
                m = it.mesh_obj
                v = m.vertices
                if len(v) > 8000:
                    v = v[np.linspace(0, len(v) - 1, 8000).astype(int)]
                pts.append(v)
                # surface samples too: face interiors reach deeper than verts
                pts.append(trimesh.sample.sample_surface(m, 1500, seed=0)[0])
    c = np.vstack(pts); np.save(f, c)
    return c

def hfloor(joint, lo_r, hi_r, step, res=1.2, xr=(-28, 20), yr=(-26, 26)):
    """Min-z heightfield of a swept joint subtree: for each grid cell the lowest
    z reached by any swept triangle overlapping it (conservative per-triangle
    bbox fill). Returns (x0, y0, res, field 2D array, default_z)."""
    moving = DESC[JBODY[joint]]
    lo, hi = max(lo_r, JRNG[joint][0]), min(hi_r, JRNG[joint][1])
    angles = sorted(set(np.r_[np.arange(lo, hi, step), hi, 0.0].round(2)))
    nx = int((xr[1] - xr[0]) / res); ny = int((yr[1] - yr[0]) / res)
    field = np.full((nx, ny), 1e9)
    for a in angles:
        for it in assembly.build(q={joint: a}):
            if it.body not in moving:
                continue
            tri = it.mesh_obj.triangles          # (n,3,3) world coords
            zmin = tri[:, :, 2].min(axis=1)
            x0i = ((tri[:, :, 0].min(axis=1) - xr[0]) / res).astype(int)
            x1i = ((tri[:, :, 0].max(axis=1) - xr[0]) / res + 1).astype(int)
            y0i = ((tri[:, :, 1].min(axis=1) - yr[0]) / res).astype(int)
            y1i = ((tri[:, :, 1].max(axis=1) - yr[0]) / res + 1).astype(int)
            for t in range(len(tri)):
                xa, xb = max(x0i[t], 0), min(x1i[t], nx)
                ya, yb = max(y0i[t], 0), min(y1i[t], ny)
                if xa < xb and ya < yb:
                    field[xa:xb, ya:yb] = np.minimum(field[xa:xb, ya:yb], zmin[t])
    return xr[0], yr[0], res, field

def fpoly(pts, grow=1.5, res=0.4, closing=5, axes=(0, 1)):
    """Rastered footprint polygon of a point cloud on `axes`, dilated by grow."""
    a, b = pts[:, axes[0]], pts[:, axes[1]]
    lo0, lo1 = a.min() - grow - 2, b.min() - grow - 2
    hi0, hi1 = a.max() + grow + 2, b.max() + grow + 2
    ax0 = np.arange(lo0, hi0 + res, res); ax1 = np.arange(lo1, hi1 + res, res)
    occ = np.zeros((len(ax0), len(ax1)), bool)
    iA = np.clip(((a - lo0) / res).astype(int), 0, len(ax0) - 1)
    iB = np.clip(((b - lo1) / res).astype(int), 0, len(ax1) - 1)
    occ[iA, iB] = True
    occ = ndi.binary_dilation(occ, iterations=int(np.ceil(grow / res)))
    occ = ndi.binary_closing(occ, structure=np.ones((closing, closing)))
    from skimage import measure
    from shapely.ops import unary_union
    polys = []
    for c in measure.find_contours(occ.astype(float), 0.5):
        if len(c) < 30:
            continue
        hole0 = np.stack([ax0[0] + c[:, 0] * res, ax1[0] + c[:, 1] * res], 1)
        sp = SP(hole0).buffer(0).simplify(0.15).buffer(0.8)
        if not sp.is_empty:
            polys.append(sp)
    return polys

def prism_yz(polys, x0, x1):
    """prism over (y,z) footprint polygon(s), extruded along x."""
    if not isinstance(polys, (list, tuple)):
        polys = [polys]
    sol = None
    for poly in polys:
        if poly.geom_type == "Polygon":
            coords = np.array(poly.exterior.coords)[:, :2]
        else:
            coords = np.asarray(poly)
        f = bd.Polygon(*[tuple(p) for p in coords])
        face = bd.Plane(origin=(x0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * f
        s_ = bd.extrude(face, x1 - x0)
        s_ = s_.translate((x0 - s_.bounding_box().min.X, 0, 0))
        sol = s_ if sol is None else sol + s_
    return sol

def prism_xy(polys, z0, z1):
    """prism over one or many footprint polygons (a list from fpoly)."""
    if isinstance(polys, np.ndarray):
        polys = [polys]
    sol = None
    for poly in polys:
        if poly.geom_type == "Polygon":
            coords = np.array(poly.exterior.coords)[:, :2]
        else:
            coords = np.asarray(poly)
        s = bd.extrude(bd.Sketch() + bd.Polygon(*[tuple(p) for p in coords]), z1 - z0)
        s = s.translate((0, 0, z0 - s.bounding_box().min.Z))  # bd.extrude goes -z
        sol = s if sol is None else sol + s
    return sol

def xprism(w_sk, h_sk, r, x0, x1, cy=0.0, cz=0.0):
    """Extrude a rounded-rect sketch (local x->world z, local y->world y) along x."""
    s = bd.extrude(bd.Sketch() + rrect_sk(w_sk, h_sk, r), x1 - x0).locate(bd.Rot(0, -90, 0))
    s = s.translate((x0 - s.bounding_box().min.X, cy, cz))
    return s

def yprism(w_sk, h_sk, r, y0, y1, cx=0.0, cz=0.0):
    """Extrude a rounded-rect sketch (local x->world x, local y->world z) along y."""
    s = bd.extrude(bd.Sketch() + rrect_sk(w_sk, h_sk, r), y1 - y0).locate(bd.Rot(90, 0, 0))
    s = s.translate((cx, y0 - s.bounding_box().min.Y, cz))
    return s

def banded_prism(pts, bands, grow, res=0.5):
    """Union of XY prisms, one per (z0,z1) band, each from that band's own
    point footprint. Follows a swept corridor far better than one tall prism."""
    sol = None
    for z0, z1 in bands:
        sub = pts[(pts[:, 2] >= z0) & (pts[:, 2] < z1)]
        if len(sub) < 50:
            continue
        sol_i = prism_xy(fpoly(sub, grow=grow, res=res), z0 - 1, z1 + 1)
        if sol_i is not None:
            sol = sol_i if sol is None else sol + sol_i
    return sol

def rrect_sk(w, h, r):
    f = bd.Rectangle(w, h)
    return bd.fillet(f.vertices(), r)

def box(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).translate(
        ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))

def solid_mesh(s):
    vs, fs = s.tessellate(0.05, 0.1)
    return trimesh.Trimesh(np.array([(v.X, v.Y, v.Z) for v in vs]), np.array(fs))

def to_body_frame(mesh, body):
    m = mesh.copy(); m.apply_transform(np.linalg.inv(assembly.BODY_POSE[body]))
    return m

from scipy.spatial import cKDTree
_SURF = {}
def _surf_tree(mesh):
    key = id(mesh)
    if key not in _SURF:
        pts, _ = trimesh.sample.sample_surface(mesh, 40000)
        _SURF[key] = cKDTree(np.vstack([pts, mesh.vertices]))
    return _SURF[key]

def sd(pts, mesh, n=120000):
    """min distance from pts to the mesh surface (sampled KD-tree, ~0.05 mm)."""
    pts = pts[:: max(1, len(pts) // n)]
    if not len(pts):
        return np.inf
    return _surf_tree(mesh).query(pts)[0].min()

def inside_count(pts, mesh, n=8000):
    pts = pts[:: max(1, len(pts) // n)]
    return int(mesh.contains(pts).sum()) if len(pts) else 0

def vcloud(items):
    return np.vstack([i.mesh_obj.vertices for i in items])

def in_solid(pts, m_solid, void_meshes, n=6000, dbg=False):
    """points inside the solid material: inside outer surface but not any void."""
    pts = pts[:: max(1, len(pts) // n)]
    if not len(pts):
        return 0
    m = m_solid.contains(pts)
    for v in void_meshes:
        m &= ~v.contains(pts)
    if dbg and m.any():
        q = pts[m]
        print("      in-solid pts bounds x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f  n=%d"
              % (q[:,0].min(), q[:,0].max(), q[:,1].min(), q[:,1].max(), q[:,2].min(), q[:,2].max(), m.sum()))
    return int(m.sum())

def report(tag, pts, mesh, voids=(), dbg=True):
    print("    %-36s min %6.2f mm  in-solid=%d" %
          (tag, sd(pts, mesh), in_solid(pts, mesh, voids, dbg=dbg)))

def export(name, mesh, body):
    m = to_body_frame(mesh, body)
    f = OUT / f"{name}.stl"
    m.export(f)
    print("    wrote %-24s watertight=%s vol=%6.1f cm3 mass=%5.1f g" %
          (f.name, m.is_watertight, m.volume / 1000, m.volume / 1000 * spec.PETG_DENSITY_G_CM3))

# ---------------------------------------------------------------- parameters (world mm)
SX0, SX1 = -26.5, 18.5           # trunk shell outer x
SY = 24.6                        # half width
SZ0, SZ1 = 80.0, 121.0           # bottom rim .. top lid surface
LID_Z0 = 117.5                   # lid bottom (floats 0.5 over chassis plate z117)
IX0, IX1 = SX0 + WALL, SX1 - WALL
IY = SY - WALL                   # interior half width 22.6
IZ1 = SZ1 - WALL                 # interior ceiling (deck above)

CASE_FACE = 21.6                 # servo case outer face (left + / right -)
NECK_GROW = 2.2
LEG_GROW  = 2.0
GRILLE_D, GRILLE_P = 1.8, 3.2
GROOVE_D = 0.3

# rear bay / battery pod
POD_X0, POD_X1 = -38.0, -26.3    # pod outer .. front face (meets shell at -26.5)
POD_Y, POD_Z0, POD_Z1 = 18.0, 83.0, 118.0
AP_Y, AP_Z0, AP_Z1 = 14.0, 88.0, 112.0   # rear wall aperture

# ================================================================ main
def main():
    items = assembly.build()
    NEW = ("trunk_shell", "trunk_cover_left", "trunk_cover_rear")
    tstat = [i for i in items if i.body == "trunk_base"
             and i.mesh not in ("left_shell", "right_shell", "banana_pcb_locker")
             and i.mesh not in NEW and not i.mesh.startswith("elec_")]
    nstat = [i for i in items if i.body == "neck" and i.mesh not in NEW]
    tpts = vcloud(tstat); npts = vcloud(nstat)
    _tstat_mesh = trimesh.util.concatenate([i.mesh_obj for i in tstat])

    print("[1] swept clouds ...")
    legs = np.vstack([cloud(j, lo, hi, st) for j, lo, hi, st in [
        ("left_hip_yaw", -45, 45, 5), ("left_hip_roll", -22, 22, 4),
        ("left_knee", -45, 45, 8), ("left_ankle", -45, 45, 10),
        ("right_hip_yaw", -45, 45, 5), ("right_hip_roll", -22, 22, 4),
        ("right_knee", -45, 45, 8), ("right_ankle", -45, 45, 10)]])
    necksw = cloud("neck_pitch", -45, 45, 3)                       # subtree from body neck_pitch
    hchain = np.vstack([cloud("head_pitch", -45, 45, 5),
                        cloud("head_yaw", -120, 120, 8),
                        cloud("head_roll", -25, 25, 5)])
    moving_neck = np.vstack([necksw, hchain])                      # everything aft of body 'neck'
    print("    legs n=%d  necksw n=%d  head n=%d" % (len(legs), len(necksw), len(hchain)))

    print("[2] cutters ...", flush=True)
    # neck port through the lid: swept verts in the exit band, clipped inside
    # the wall line so the side walls keep a clean exterior
    clip = SP([(-30, -22.8), (20, -22.8), (20, 22.8), (-30, 22.8)])
    zone = (necksw[:, 2] > 104) & (necksw[:, 2] < 125) & (np.abs(necksw[:, 1]) < 28) & (necksw[:, 0] > -30)
    band = necksw[zone]
    deckpolys = [pp.intersection(clip) for pp in fpoly(band, grow=2.0, res=0.4)]
    deckpolys = [pp for pp in deckpolys if not pp.is_empty]
    port = prism_xy(deckpolys, 110, 122)
    # neck corridor through the front wall top and the lid's front edge:
    # the sweep below deck height is asymmetric (y -22.3..10.4) and opens
    # toward the right corner, under the shroud's canopy
    fport = box(13, 20, -24.8, 12, 94, 122)
    try:
        fport = bd.fillet(fport.edges().filter_by(bd.Axis.Y), 2.5)
    except Exception:
        pass
    print("    port polys=%d" % len(deckpolys))

    # head_pitch corridor relief: the head's bottom shell sweeps the rear
    # deck and flank pockets far below the lid top. A triangle-rastered
    # heightfield gives the true swept floor per deck cell; terrace every
    # column it dips into (floor - 1.2 mm).
    print("    head-pitch deck relief ...", flush=True)
    HF = SWEPT / "hfloor_head_pitch_v1.npy"
    if HF.exists():
        hx0, hy0, hres, field = np.load(HF, allow_pickle=True)
    else:
        hx0, hy0, hres, field = hfloor("head_pitch", -45, 45, 3)
        np.save(HF, np.array([hx0, hy0, hres, field], dtype=object))
    cbx, cby = [], []
    nx, ny = field.shape
    for ix in range(nx):
        for iy in range(ny):
            fz = field[ix, iy]
            if fz < 124.6:
                cbx.append((hx0 + ix * hres, hy0 + iy * hres, fz))
    relief = bd.Compound(children=[box(x, x + hres + 0.05, y, y + hres + 0.05,
                                       fz - 1.2, 131.0) for x, y, fz in cbx])
    print("    relief cells=%d  floor-min=%.1f" % (len(cbx), field.min()))

    # ------------------------------------------------ neck port trim: a
    # recessed groove ring echoing the port outline, engraved into the deck.
    # (A raised bezel was tried and deleted: the head-pitch corridor sweeps
    # the ring footprint below the deck, so any raised ring is clipped into
    # fragments. A groove is a void — it cannot collide.)
    lidfp = SP([(SX0 + 0.4, -SY + 0.4), (SX1 - 0.4, -SY + 0.4),
                (SX1 - 0.4, SY - 0.4), (SX0 + 0.4, SY - 0.4)])
    trim_rings = []
    for pp in deckpolys:
        ring = pp.buffer(2.6).intersection(lidfp) - pp.buffer(1.0)
        if not ring.is_empty:
            trim_rings.append(ring)

    # ------------------------------------------------ trunk shell: panelled enclosure
    #   thin lid 117.5..121 resting on the walls (reveal line); the chassis
    #   already carries a flat top plate at z117, so the lid floats 0.5 over
    #   it instead of swallowing it. side/rear/front walls rise to meet it;
    #   open hip bay below.
    print("[4] trunk_shell ...", flush=True)
    deck = box(SX0, SX1, -SY, SY, LID_Z0, SZ1)
    fw   = box(IX1, SX1, -SY, SY, 86.0, 117.5)
    rw   = box(SX0, IX0, -SY, SY, 84.5, 117.5)
    lw   = box(SX0, SX1, IY, SY, 89.5, 117.5)
    rwall= box(SX0, SX1, -SY, -IY, 89.5, 117.5)
    shell = deck + fw + rw + lw + rwall
    try:
        shell = bd.fillet(shell.edges().filter_by(bd.Axis.Z), 3.0)
        print("    vert fillet ok", flush=True)
    except Exception as e:
        print("    vert fillet skipped:", e)
    try:
        shell = bd.fillet([e for e in shell.edges() if e.center().Z > SZ1 - 0.1], 3.0)
        print("    top fillet ok", flush=True)
    except Exception as e:
        print("    top fillet skipped:", e)
    # right-side interior pad pressing the right servo case face (-21.6)
    shell = shell + box(-17.0, 9.0, -IY, -CASE_FACE - 0.3, 90.0, 112.0)
    shell = shell - port
    shell = shell - fport
    shell = shell - relief            # terrace the deck under the head skirt
    # trim groove ring around the neck port (0.55 deep into the deck top)
    for ring in trim_rings:
        shell = shell - prism_xy([ring], 120.55, 121.3)
    # rear access aperture through the rear wall (rounded corners)
    rear = xprism(AP_Z1 - AP_Z0, 2 * AP_Y, 4, -28.0, -19.0, cz=(AP_Z0 + AP_Z1) / 2)
    shell = shell - rear
    # left flank aperture (reveals the servo case faces + pocket mouth)
    lapp = box(-18.0, 12.0, CASE_FACE + 0.1, SY + 2, 91.0, 112.0)
    shell = shell - lapp
    # right flank vent grille (over the right hip-yaw servo)
    for gx in np.arange(-16.0, -4.5, GRILLE_P):
        for gz in np.arange(96.0, 105.0, GRILLE_P):
            shell = shell - bd.Cylinder(GRILLE_D / 2, 8).locate(
                bd.Pos(gx, -SY - 1, gz) * bd.Rot(90, 0, 0))
    # deck panel-line groove (recessed rectangular outline)
    gout = box(-19.0, 7.0, -15.0, 15.0, SZ1 - GROOVE_D, SZ1 + 1)
    gin = box(-16.0, 4.0, -12.0, 12.0, SZ1 - GROOVE_D - 1, SZ1 + 1)
    shell = shell - (gout - gin)
    m_shell = solid_mesh(shell)
    shell_voids = [solid_mesh(s_) for s_ in (port, fport, rear, lapp)]
    print("    watertight=%s vol=%.1f cm3" % (m_shell.is_watertight, m_shell.volume / 1000))
    print("    static trunk clearance:")
    report("trunk statics", tpts, m_shell, shell_voids)

    # ------------------------------------------------ left cover plate
    print("[4] trunk_cover_left ...")
    plate = box(-20.0, 14.0, CASE_FACE + 0.3, SY - 0.6, 89.5, 114.5)
    plate = bd.fillet(plate.edges().filter_by(bd.Axis.Z), 0.9)
    plate = bd.fillet([e for e in plate.edges() if e.center().Y > SY - 0.8], 0.7)
    # screw dimples (cosmetic)
    for (dx, dz) in [(-17.5, 92.5), (-17.5, 111.5), (11.5, 92.5), (11.5, 111.5)]:
        plate = plate - bd.Cylinder(1.0, 1.8).locate(
            bd.Pos(dx, SY - 0.5, dz) * bd.Rot(90, 0, 0))
    # grille patch on the plate (mirrors the right flank)
    for gx in np.arange(-14.0, -6.5, GRILLE_P):
        for gz in np.arange(97.0, 104.0, GRILLE_P):
            plate = plate - bd.Cylinder(GRILLE_D / 2, 8).locate(
                bd.Pos(gx, SY - 0.5, gz) * bd.Rot(90, 0, 0))
    m_covl = solid_mesh(plate)
    print("    watertight=%s vol=%.1f cm3" % (m_covl.is_watertight, m_covl.volume / 1000))
    print("    clearance:")
    report("trunk statics", tpts, m_covl)

    # ------------------------------------------------ rear pod cover
    print("[5] trunk_cover_rear ...")
    # stepped top: the head's bottom shell sweeps the rear-top corner at
    # neck_pitch=+45 (reaches z~115 at x<-35), so the rear section drops to
    # z112.5 behind a vertical riser at x=-32.5 — no bevel, no thin lips.
    pod = (box(POD_X0, -32.5, -POD_Y, POD_Y, POD_Z0, 112.5)
         + box(-32.5, POD_X1, -POD_Y, POD_Y, POD_Z0, POD_Z1))
    try:
        pod = bd.fillet(pod.edges().filter_by(bd.Axis.Z), 3.0)
    except Exception as e:
        print("    vert fillet skipped:", e)
    try:
        pod = bd.fillet([e for e in pod.edges() if e.center().Z > 112.4 or e.center().Z < POD_Z0 + 0.1], 2.0)
    except Exception as e:
        print("    top/bottom fillet skipped:", e)
    # interior void; battery bay opens through the rear face
    podvoid = box(POD_X0 + WALL, POD_X1 - WALL, -POD_Y + WALL, POD_Y - WALL, POD_Z0 + WALL, POD_Z1 - WALL)
    pod = pod - podvoid
    # rear battery slide opening (battery cap sits flush in it, NP-F970 style)
    bopen = xprism(110 - 88, 2 * 13.5, 1.0, -39.5, -35.0, cz=(88 + 110) / 2)
    pod = pod - bopen
    # matching aperture in the pod's front wall (registers with the shell's)
    ap = xprism(AP_Z1 - AP_Z0, 2 * AP_Y, 4, -33.0, -25.0, cz=(AP_Z0 + AP_Z1) / 2)
    pod = pod - ap
    # vent slots on each side wall, up high clear of the leg sweep
    for sgn in (-1, 1):
        pod = pod - yprism(8.0, 16.0, 2.5,
                           sgn * (POD_Y - 4.0) - (0 if sgn > 0 else 4.0),
                           sgn * (POD_Y - 4.0) + (4.0 if sgn > 0 else 0.0),
                           cx=-33.5, cz=99.0)
    # pod grille (battery vent) on the outer face
    for gy in np.arange(-9.0, 10.0, GRILLE_P):
        for gz in np.arange(86.0, 96.0, GRILLE_P):
            pod = pod - bd.Cylinder(GRILLE_D / 2, 8).locate(
                bd.Pos(POD_X0 - 1, gy, gz) * bd.Rot(0, -90, 0))
    # screw dimples on the pod front face (around the aperture)
    for (dy, dz) in [(-POD_Y + 1.2, POD_Z0 + 4), (-POD_Y + 1.2, POD_Z1 - 4),
                     (POD_Y - 1.2, POD_Z0 + 4), (POD_Y - 1.2, POD_Z1 - 4)]:
        pod = pod - bd.Cylinder(1.0, 1.8).locate(
            bd.Pos(POD_X1, dy, dz) * bd.Rot(0, 90, 0))
    m_pod = solid_mesh(pod)
    pod_voids = [solid_mesh(podvoid), solid_mesh(ap), solid_mesh(bopen)]
    print("    watertight=%s vol=%.1f cm3" % (m_pod.is_watertight, m_pod.volume / 1000))
    print("    clearance:")
    report("trunk statics", tpts, m_pod, pod_voids)
    report("legs", legs, m_pod, pod_voids)

    # ------------------------------------------------ electronics placeholders (trunk_base frame)
    print("[7] electronics placeholders ...")
    elec = {
        "elec_battery_2s_450":      box(-36.8, -28.5, -12.0, 12.0, 89.5, 109.5),
        "elec_ubec_6v_5a":          box(-23.0, -19.0, -8.0, 8.0, 88.0, 96.0),
        "elec_bno085":              box(-24.0, -21.0, 6.0, 16.0, 104.0, 107.0),
        "elec_bus_hub_and_wiring":  box(-24.0, -19.0, -6.0, 4.0, 94.0, 104.0),
    }
    for name, s in elec.items():
        m = solid_mesh(s)
        print("    %-26s watertight=%s" % (name, m.is_watertight))

    # ------------------------------------------------ clearance vs swept clouds
    print("[8] swept clearance reports ...")
    for tag, m, vd in [("trunk_shell", m_shell, shell_voids), ("cover_left", m_covl, ()),
                       ("cover_rear", m_pod, pod_voids)]:
        print("  %s:" % tag)
        report("legs", legs, m, vd)
        report("neck_pitch sweep", necksw, m, vd)
        report("head chain", hchain, m, vd)
    print("  electronics in shell solid (must be 0):")
    for name, s in elec.items():
        m = solid_mesh(s)
        print("    %-26s in-shell=%d  in-pod=%d  min-dist statics %.2f" %
              (name, in_solid(m.vertices, m_shell, shell_voids),
               in_solid(m.vertices, m_pod, pod_voids),
               sd(m.vertices, _tstat_mesh)))

    # ------------------------------------------------ export
    print("[9] export ...")
    export("trunk_shell", m_shell, "trunk_base")
    export("trunk_cover_left", m_covl, "trunk_base")
    export("trunk_cover_rear", m_pod, "trunk_base")
    for name, s in elec.items():
        export(name, solid_mesh(s), "trunk_base")

if __name__ == "__main__":
    main()
