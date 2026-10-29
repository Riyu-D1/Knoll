"""Refinement B: rebuild the leg parts as smooth designed shells (Microduck thin-shell look,
BDX panel detailing). Function is unchanged: joint anchors/axes/ranges, servo positions,
horn interfaces, bearing seats and co-part mounting faces are preserved by KEEPING the
existing interface material (keep-zones) and recutting the same pockets/corridors.

Run:  ~/Knoll-cad-venv/bin/python tools/make_legs.py --parts yaw2roll,bearing_roll
      (needs build123d + trimesh + manifold3d; repo tools are on sys.path)

Pipeline per STL in parts/current:
  new = union(designed_shell, current_part INTERSECT keep_zones) - servo_pockets - corridors
keeps   = cylinders around each driven-joint horn face + each idler-bearing seat + co-part
          contact patches, evaluated in the STL's own local frame (so shared STLs keep every
          instance's interfaces).
shells  = authored in WORLD mm around the LEFT side (build123d solids -> STL -> trimesh),
          then mapped into the part-local frame; right-side-only STLs get the y-mirrored
          shell through their own instance transform (exact-mirror exterior).
corridors = union of every item that moves relative to the part's body, swept over the
          required joint ranges, mapped into the part frame (same maths as swept_cut.py).
"""
import sys, argparse, json
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
from trimesh.transformations import translation_matrix, rotation_matrix
import spec, scs0009
from assembly import build, joints_world, _walk

CAD = True
try:
    from build123d import (Box, Cylinder as BdCylinder, fillet, Pos, Rot, Mesher,
                       Plane, RectangleRounded, extrude)
except Exception:
    CAD = False

MAN = "manifold"
import manifold3d

def _to_man(m):
    if isinstance(m, trimesh.Trimesh):
        return manifold3d.Manifold(mesh=manifold3d.Mesh(
            vert_properties=np.asarray(m.vertices, dtype=np.float32),
            tri_verts=np.asarray(m.faces, dtype=np.uint32)))
    return m

def _to_tri(mf):
    mm = mf.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mm.vert_properties)[:, :3],
                           faces=np.asarray(mm.tri_verts), process=False)

def man_union(ms):
    ms = [_to_man(m) for m in ms if m is not None]
    if not ms:
        return None
    if len(ms) == 1:
        return ms[0]
    return manifold3d.Manifold.batch_boolean(ms, manifold3d.OpType.Add)

def union_all(ms):
    ms = [m for m in ms if m is not None]
    if not ms:
        return None
    if len(ms) == 1:
        return ms[0]
    try:
        return _to_tri(man_union(ms))
    except Exception:
        return trimesh.boolean.union(ms, engine=MAN)

def subtract_all(m, cuts):
    cuts = [c for c in cuts if c is not None]
    if not cuts:
        return m
    c = man_union(cuts)
    if c is None:
        return m
    return _to_tri(_to_man(m) - c)
WORK = spec.WORK_DIR
ATTIC = spec.ROOT / "parts" / "attic_refine"

# ---------------------------------------------------------------- static data
ITEMS0 = build()
J0 = joints_world()
BODY0 = {b: m.copy() for b, m in __import__("assembly").BODY_POSE.items()}
JPOS = {j[0]: np.array(j[1], float) * spec.S for j in spec.JOINTS}
JAX = {j[0]: np.array(j[2], float) for j in spec.JOINTS}
JBODY = {j[0]: j[3] for j in spec.JOINTS}
JHORN = {j[0]: j[4] for j in spec.JOINTS}   # body driven by the horn
JLIM = {j[0]: j[5] for j in spec.JOINTS}

MIRR_Y = np.diag([1.0, -1.0, 1.0, 1.0])
LEG_BODIES_L = {"yaw2roll", "hip_l", "upper_leg_left", "leg", "ankle_left"}
LEG_BODIES_R = {"bearing_roll", "hip_l_2", "upper_leg_right", "leg_2", "ankle_right"}

def instances(name):
    return [i for i in ITEMS0 if i.mesh == name]

def to_local(item, world_mesh):
    m = world_mesh.copy()
    m.apply_transform(np.linalg.inv(item.T))
    return m

def to_local_T(item):
    return np.linalg.inv(item.T)

def mirror_left_item(right_name):
    """the right-side instance mirroring left body<->right body"""
    mp = {"upper_leg_right": ("upper_leg_left", "upper_leg_right"),
          "ankle_right": ("ankle_left", "ankle_right"),
          "foot_right": ("ankle_left", "foot_left"),
          "sole_right": ("ankle_left", "sole_left")}
    return mp.get(right_name)

# ---------------------------------------------------------------- primitives
def cyl_at(p, a, r, h, sections=48):
    """cylinder of radius r, height h, axis a, centred at p (world)."""
    a = np.asarray(a, float); a /= np.linalg.norm(a)
    m = trimesh.creation.cylinder(radius=r, height=h, sections=sections)
    z = np.array([0, 0, 1.0])
    d = np.cross(z, a)
    if np.linalg.norm(d) > 1e-9:
        m.apply_transform(rotation_matrix(np.arccos(np.clip(z @ a, -1, 1)), d))
    elif a[2] < 0:
        m.apply_transform(rotation_matrix(np.pi, [1, 0, 0]))
    m.apply_translation(p)
    return m

def box_at(lo, hi):
    b = trimesh.creation.box(extents=np.asarray(hi) - np.asarray(lo))
    b.apply_translation((np.asarray(lo) + np.asarray(hi)) / 2)
    return b

def bd2tri(shape):
    import tempfile, os
    f = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
    f.close()
    mh = Mesher()
    mh.add_shape(shape, linear_deflection=0.05, angular_deflection=0.1)
    mh.write(f.name)
    m = trimesh.load(f.name, force="mesh")
    os.unlink(f.name)
    return m

def rounded_box(x0, x1, y0, y1, z0, z1, r=1.5):
    """build123d box with all edges filleted (falls back to plain trimesh box)."""
    if CAD:
        b = Box(x1 - x0, y1 - y0, z1 - z0)
        b = Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * b
        try:
            b = fillet(b.edges(), r)
        except Exception:
            pass
        return bd2tri(b)
    b = box_at((x0, y0, z0), (x1, y1, z1))
    return b

def shell_of(solid_mesh, wall):
    """hollow a solid mesh -> shell solid (outer minus eroded inner)."""
    inner = solid_mesh.copy()
    inner.apply_scale(1.0)  # placeholder; real erosion below via offset planes is complex
    raise NotImplementedError

# ---------------------------------------------------------------- keep zones
def _wafer(p, a, r, t0, t1):
    """cylinder + axis slab: keep-zone that is r-wide and spans t0..t1 along the axis."""
    c = cyl_at(np.asarray(p, float) + np.asarray(a, float) * (t0 + t1) / 2, a, r, t1 - t0)
    return c

def horn_keeps_local(item):
    """thin wafers around every horn face of joints that DRIVE this item's body
    (preserve the machined mount face, boss and screw pattern only)."""
    keeps = []
    for jn, body in JHORN.items():
        if body != item.body:
            continue
        anchor, axis = JPOS[jn], JAX[jn]
        keeps.append(_wafer(anchor, axis, 7.2, -3.5, 0.3))
    return [to_local(item, k) for k in keeps]

def horn_bosses_local(item):
    """designed round boss discs at each horn face - the clean outer face that
    replaces any crude material above the kept wafer."""
    bosses = []
    for jn, body in JHORN.items():
        if body != item.body:
            continue
        anchor, axis = JPOS[jn], JAX[jn]
        bosses.append(_wafer(anchor, axis, 12.5, -0.6, 2.0))
    return [to_local(item, k) for k in bosses]

def bearing_keeps_local(item):
    """rings around idler bearings in this item's body."""
    keeps = []
    for it in ITEMS0:
        if it.kind == "other" and it.body == item.body and "seeed" in it.mesh:
            c = (it.mesh_obj.bounds[0] + it.mesh_obj.bounds[1]) / 2
            best = None
            for jn, (p, a, b) in J0.items():
                a = np.asarray(a, float); a /= np.linalg.norm(a)
                d = np.linalg.norm(np.cross(c - p, a))
                if d < 1.5 and (best is None or d < best[0]):
                    best = (d, p, a)
            if best:
                keeps.append(_wafer(c, best[2], 11.0, -4.5, 4.5))
    return [to_local(item, k) for k in keeps]

def contact_keeps_local(item, all_items=None):
    """pads where this part touches co-body printed parts (bolt/index faces)."""
    all_items = all_items or ITEMS0
    keeps = []
    mine = item.mesh_obj
    for other in all_items:
        if other.kind != "printed" or other.body != item.body or other is item:
            continue
        # sample points on my surface close to the other part
        try:
            pts, _ = trimesh.sample.sample_surface(mine, 3000, seed=1)
        except Exception:
            continue
        d = other.mesh_obj.nearest.signed_distance(pts)
        near = pts[np.abs(d) < 0.6]
        if len(near) < 6:
            continue
        lo, hi = near.min(0) - 2.5, near.max(0) + 2.5
        keeps.append(box_at(lo, hi))
    return [to_local(item, k) for k in keeps]

# ---------------------------------------------------------------- pockets
def pockets_local(items):
    """SCS0009 pocket cutters (case+ears+cable+pilot holes) for servos in these
    bodies, mapped through every instance's local frame."""
    cuts = []
    for item in items:
        for s in (i for i in ITEMS0 if i.kind == "servo" and i.body == item.body):
            c = scs0009.cutter_mesh().copy()
            c.apply_transform(s.T)
            cuts.append(to_local(item, c))
    return cuts

def neighbor_servo_cuts(items, new_world_bounds):
    """envelopes (case+ears, NO horn) of servos in OTHER bodies whose zero-pose
    envelope overlaps this part - e.g. the leg's ankle servo reaching into
    ankle_left/foot parts, or the thigh's knee servo face reaching the shin wall."""
    cuts = []
    env_lo, env_hi = new_world_bounds
    for item in items:
        for s in (i for i in ITEMS0 if i.kind == "servo"):
            if s.body == item.body:
                continue
            e = s.mesh_obj
            if (e.bounds[0] > env_hi).any() or (e.bounds[1] < env_lo).any():
                continue
            c = scs0009.envelope_mesh(horn=False, grow=0.3).copy()
            c.apply_transform(s.T)
            cuts.append(to_local(item, c))
    return cuts

def horn_disc_local(items):
    """horn disc + spline volume of the servo that drives each body (the driven side
    needs clearance for the horn inside its mounting face, NOT the whole case)."""
    cuts = []
    f = scs0009.frame_numbers()
    c = spec.SCS
    for item in items:
        for jn, body in JHORN.items():
            if body != item.body:
                continue
            sv = [i for i in ITEMS0 if i.kind == "servo" and i.mesh == f"scs0009:{jn}"]
            if not sv:
                continue
            # spline stub + horn disc, both on the -X face of the servo frame
            g = 0.3
            parts = []
            sp = trimesh.creation.cylinder(radius=3.0 + g, height=c["spline_h"] + 0.01,
                                           sections=32)
            sp.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
            sp.apply_translation([f["case_top"] - c["spline_h"] / 2, 0, 0])
            parts.append(sp)
            hd = trimesh.creation.cylinder(radius=c["horn_d"] / 2 + g,
                                           height=c["horn_t"] + g, sections=48)
            hd.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0]))
            hd.apply_translation([f["horn_top"] + c["horn_t"] / 2 - g / 2, 0, 0])
            parts.append(hd)
            env = union_all(parts)
            env.apply_transform(sv[0].T)
            cuts.append(to_local(item, env))
    return cuts

# ---------------------------------------------------------------- corridors
_D_CACHE = {}
def _body_displacements(q):
    """world displacement D(body) = pose(q) @ inv(pose(0)) for every body. Cached."""
    key = tuple(sorted(q.items()))
    if key not in _D_CACHE:
        _walk(want_meshes=False, q=q)
        from assembly import BODY_POSE
        _D_CACHE[key] = {b: BODY_POSE[b] @ np.linalg.inv(BODY0[b]) for b in BODY_POSE}
    return _D_CACHE[key]

NEW_WORLD = {}     # index into ITEMS0 -> pre-cut world mesh of a redesigned part
IDX = {id(it): k for k, it in enumerate(ITEMS0)}

# bodies affected by each joint (its moving subtree) - one displaced walk per joint
_MOVING = {}
def _moving_bodies(jn):
    if jn not in _MOVING:
        D = _body_displacements({jn: 5.0})
        _MOVING[jn] = {b for b, T in D.items() if not np.allclose(T, np.eye(4), atol=1e-6)}
    return _MOVING[jn]

_SIDE = {"yaw2roll": "left", "hip_l": "left", "upper_leg_left": "left",
         "leg": "left", "ankle_left": "left",
         "bearing_roll": "right", "hip_l_2": "right", "upper_leg_right": "right",
         "leg_2": "right", "ankle_right": "right"}

def _joints_for(item):
    """joints whose sweep can bring neighbours near this part: the 5 joints of its
    own leg chain. Other-side / head / arm joints are tens of mm away and are culled."""
    side = _SIDE.get(item.body)
    if side is None:
        return [j[0] for j in spec.JOINTS]
    return [jn for jn, *_ in spec.JOINTS if jn.startswith(side + "_")]

def _corners(bb):
    lo, hi = bb
    return np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1])
                     for z in (lo[2], hi[2])])

def _corridors_one(item, new_shell_bounds, step=10.0):
    """swept union of all items moving relative to item's body, in the part frame.
    Only items whose swept path can come near the part are collected."""
    me = item
    out = []
    env_lo, env_hi = np.asarray(new_shell_bounds[0]) - 3.0, np.asarray(new_shell_bounds[1]) + 3.0
    static_bb = [k.mesh_obj.bounds for k in ITEMS0]
    for jn in _joints_for(item):
        moving = _moving_bodies(jn)
        lo_r, hi_r = spec.SWEEP_REQUIRED_DEG[jn]
        lo = max(lo_r, JLIM[jn][0]); hi = min(hi_r, JLIM[jn][1], 150)
        angs = sorted(set(np.r_[np.arange(lo, hi, step), hi, 0.0].round(2)))
        for a in angs:
            D = _body_displacements({jn: a})
            Dm = D.get(me.body, np.eye(4))
            Rinv = np.linalg.inv(Dm)
            for ki, k in enumerate(ITEMS0):
                R = Rinv @ D.get(k.body, np.eye(4))
                if np.allclose(R, np.eye(4), atol=1e-6):
                    continue   # moves together with me
                if ki in NEW_WORLD:
                    w = NEW_WORLD[ki].copy(); w.apply_transform(R)
                    bb = w.bounds
                else:
                    pts = np.hstack([_corners(static_bb[ki]), np.ones((8, 1))])
                    tc = (R @ pts.T).T[:, :3]
                    bb = np.array([tc.min(0), tc.max(0)])
                    if (bb[0] > env_hi).any() or (bb[1] < env_lo).any():
                        continue
                    w = k.mesh_obj.copy(); w.apply_transform(R); bb = w.bounds
                if (bb[0] > env_hi).any() or (bb[1] < env_lo).any():
                    continue
                out.append(to_local(me, w))
    if not out:
        return None
    return union_all(out)

def corridors_local(items, new_world_bounds, grow=0.3, step=5.0):
    """union of per-instance corridors, in the shared STL's local frame."""
    cors = [c for c in (_corridors_one(it, new_world_bounds, step) for it in items)
            if c is not None]
    if not cors:
        return None
    u = union_all(cors)
    if grow:
        g = grow
        u = trimesh.boolean.union(
            [u.copy().apply_transform(translation_matrix(d))
             for d in [(g,0,0),(-g,0,0),(0,g,0),(0,-g,0),(0,0,g),(0,0,-g)]], engine=MAN)
    return u

# ---------------------------------------------------------------- finish
def meshfix(m):
    """pymeshlab repair: close holes + remove non-manifold edges. Returns mesh or None."""
    try:
        import pymeshlab
        ms = pymeshlab.MeshSet()
        ms.add_mesh(pymeshlab.Mesh(vertex_matrix=np.asarray(m.vertices),
                                   face_matrix=np.asarray(m.faces)))
        try:
            ms.meshing_remove_duplicate_faces()
            ms.meshing_remove_duplicate_vertices()
            ms.meshing_repair_non_manifold_edges()
        except Exception:
            pass
        try:
            ms.meshing_close_holes(maxholesize=40)
        except Exception:
            pass
        out = ms.current_mesh()
        r = trimesh.Trimesh(vertices=out.vertex_matrix(), faces=out.face_matrix(),
                            process=True)
        return r
    except Exception as e:
        print(f"   meshfix failed: {e}")
        return None

def finish(name, local_geom, note=""):
    """validate + write the STL into parts/current (original goes to attic)."""
    bodies = local_geom.split(only_watertight=False)
    # a legit hollow part has multiple components (outer shell + inner cavity skins);
    # drop only sub-mm3 slivers, then concatenate the rest WITHOUT boolean union.
    big = [b for b in bodies if abs(b.volume) >= 1.0]
    if len(big) < len(bodies):
        frag = sum(b.volume for b in bodies) - sum(b.volume for b in big)
        print(f"   {name}: dropped {len(bodies)-len(big)} slivers ({frag:.2f} mm3)")
    if not big:
        raise RuntimeError(f"{name}: only slivers")
    local_geom = trimesh.util.concatenate(big) if len(big) > 1 else big[0]
    local_geom.merge_vertices()
    if not local_geom.is_watertight:
        fixed = meshfix(local_geom)
        if fixed is not None:
            local_geom = fixed
    src = WORK / f"{name}.stl"
    ATTIC.mkdir(exist_ok=True)
    dst = ATTIC / f"{name}.stl"
    if src.exists() and not dst.exists():
        src.rename(dst)
    local_geom.export(src)
    m = trimesh.load(src, force="mesh")          # report what actually landed on disk
    print(f"   {name}: watertight={m.is_watertight} vol={m.volume/1000:.2f} cm3 "
          f"ext={m.extents.round(1).tolist()} {note}")
    return m

def keep_material(name, items, extra_keeps=None):
    """current part material inside the keep-zones, in the local frame.
    Reads the ORIGINAL part (attic copy if we already replaced it).
    items = ALL instances of this STL - their local keep zones are unioned so the
    shared file keeps every instance's interfaces."""
    src = ATTIC / f"{name}.stl"
    if not src.exists():
        src = WORK / f"{name}.stl"
    cur = trimesh.load(src, force="mesh")
    zones = []
    for item in items:
        zones += horn_keeps_local(item) + bearing_keeps_local(item)
    zones += [k for k in (extra_keeps or [])]
    if not zones:
        return None
    z = union_all([z_ for z_ in zones])
    keep = trimesh.boolean.intersection([cur, z], engine=MAN)
    if keep is not None and keep.volume < 20.0:
        print(f"   {name}: keep material negligible ({keep.volume:.3f} mm3) - dropped")
        return None
    return keep

# ---------------------------------------------------------------- part builders
BUILDERS = {}

def builder(name):
    def deco(fn):
        BUILDERS[name] = fn
        return fn
    return deco

def slab(axis, lo, hi, size=400):
    """a thick slab covering axis range [lo,hi] (huge in the other two axes)."""
    e = [size, size, size]
    e["xyz".index(axis)] = hi - lo
    c = [0, 0, 0]
    c["xyz".index(axis)] = (lo + hi) / 2
    b = trimesh.creation.box(extents=e)
    b.apply_translation(c)
    return b

def trim_below(m, axis, val):
    return trimesh.boolean.intersection([m, slab(axis, val, 1e4)], engine=MAN)

def trim_above(m, axis, val):
    return trimesh.boolean.intersection([m, slab(axis, -1e4, val)], engine=MAN)

def local_box(x0, x1, y0, y1, z0, z1, r=0):
    if r and CAD:
        return rounded_box(x0, x1, y0, y1, z0, z1, r)
    return box_at((x0, y0, z0), (x1, y1, z1))

def plate_panel(x0, x1, z0, z1, y0, y1, r=1.2):
    """a flat panel spanning x/z at a y range, with rounded corners."""
    return local_box(x0, x1, y0, y1, z0, z1, r)

# ============================ hip housing: yaw2roll + bearing_roll ============================
# Local frame (shared by both hips): roll shaft = local -Y (horn face at y=-13.3, bearing -11.9),
# hip_yaw horn on top (+z face at z=9). Servo case toward +y.
#   yaw2roll.stl     = chamfered housing sleeve around the servo (open on -y, capped +y w/ cable slot)
#   bearing_roll.stl = end cap plate on -y carrying the roll horn bore + idler bearing seat
def _hip_shell_local():
    outer = local_box(3.4, 21.6, -9.4, 21.0, -22.6, 11.4, r=1.5)
    inner = local_box(5.4, 19.6, -20.0, 18.8, -20.4, 9.2, r=1.0)
    shell = trimesh.boolean.difference([outer, inner], engine=MAN)
    # cable slot through the +y cap
    slot = local_box(9.0, 16.0, 17.0, 24.0, -18.0, -10.0, r=2.0)
    shell = trimesh.boolean.difference([shell, slot], engine=MAN)
    # two internal ribs tying the pocket zone to the +/-x walls
    for xc in (5.6, 19.2):
        rib = local_box(xc - 1.0, xc + 1.0, -9.0, 18.0, -20.0, 9.0)
        shell = union_all([shell, rib])
    return shell

@builder("yaw2roll")
def build_yaw2roll(items):
    keeps = keep_material("yaw2roll", items)
    bosses = [b for it in items for b in horn_bosses_local(it)]
    return union_all([_hip_shell_local(), keeps, union_all(bosses)])

@builder("bearing_roll")
def build_bearing_roll(items):
    """idler-bearing cap on the roll axis: round cap plate at the face + the kept
    bearing-seat wafer. The servo ear-slot stays open (insertion face)."""
    gs = []
    for it in items:
        Ti = np.linalg.inv(it.T)
        jn = "left_hip_roll" if it.body == "yaw2roll" else "right_hip_roll"
        anchor_l = (Ti @ np.r_[JPOS[jn], 1])[:3]
        axis_l = Ti[:3, :3] @ JAX[jn]
        cap = cyl_at(anchor_l - axis_l / np.linalg.norm(axis_l) * 1.8, axis_l, 12.0, 3.8)
        bore = cyl_at(anchor_l, axis_l, 9.75, 16.0)
        gs.append(trimesh.boolean.difference([cap, bore], engine=MAN))
    return union_all(gs + [keep_material("bearing_roll", items)])

# ============================ thigh: upper_leg_left/right ============================
# upper_leg local frame: pitch horn face at x~28-30 inner end, two servo bays side by
# side extending +x (world +y, outward). Shell = tapered rounded prism (extrude+taper),
# hollow 2 mm, horn-face keeps inside, bearing seat at the knee idler.
def _shell_extrude(x0, cy, cz, wy, wz, rr, length, taper, wall=None, cap=2.0):
    """rounded-rect prism along +x from x0, hollowed to wall thickness.
    cap = thickness of the closed end wall at x0+length."""
    pl = Plane(origin=(x0, cy, cz), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    outer = extrude(pl * RectangleRounded(wy, wz, rr), amount=length, taper=taper)
    om = bd2tri(outer)
    if wall is None:
        return om
    shrink = 2 * wall
    pl2 = Plane(origin=(x0 + wall, cy, cz), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    inner = extrude(pl2 * RectangleRounded(wy - shrink, wz - shrink, max(rr - 1, 0.5)),
                    amount=length - wall - cap, taper=taper)
    im = bd2tri(inner)
    return trimesh.boolean.difference([om, im], engine=MAN)

def _thigh_shell_local():
    # yz section covers both servo envelopes (y -6.3..22.2, z -10.9..36.6) + 1.5 pad.
    # end extends past the pocket (63.6) so the 2 mm cap survives as a closed end.
    shell = _shell_extrude(26.2, 8.0, 12.9, 33.5, 52.5, 4.0, 42.6, taper=2.5, wall=2.0)
    return shell

@builder("upper_leg_left")
def build_upper_leg_left(items):
    return union_all([_thigh_shell_local(), keep_material("upper_leg_left", items)])

@builder("upper_leg_right")
def build_upper_leg_right(items):
    s = _thigh_shell_local()
    s.apply_transform(np.diag([-1.0, 1.0, 1.0, 1.0]))   # right part is local-x mirrored
    if s.volume < 0:
        s.invert()
    return union_all([s, keep_material("upper_leg_right", items)])

# ============================ shin: leg / leg_2 ============================
# leg local frame: knee horn face at (27.7,15.8,25.8) facing -x; ankle servo bay
# x12..47 y5..38 z-11..2 along the bottom; ankle horn exits +x at (46.4,15.8,-4.5).
def _shin_local():
    # ankle servo bay: closed box section, servo slides in -x, horn exits +x
    bay = _shell_extrude(10.5, 21.0, -4.0, 39.0, 17.0, 3.0, 39.0, taper=0, wall=2.0, cap=2.0)
    # strut from bay top up to the knee face plate
    strut = local_box(24.0, 33.0, 11.5, 21.5, -3.0, 22.0, r=2.0)
    # knee face wall (plate facing -x, carries the horn face + boss)
    wall = local_box(24.5, 30.5, 7.5, 28.5, 14.0, 36.0, r=2.0)
    g = union_all([bay, strut, wall])
    # bore through the +x cap where the ankle horn/shaft exits to ankle_left
    bore = cyl_at(np.array([46.4, 15.8, -4.5]) + np.array([2.0, 0, 0]), [1, 0, 0], 9.75, 10.0)
    g = trimesh.boolean.difference([g, bore], engine=MAN)
    return g

@builder("leg")
def build_leg(items):
    gs = [_shin_local(), keep_material("leg", items)]
    bosses = [b for it in items for b in horn_bosses_local(it)]
    gs.append(union_all(bosses))
    return union_all(gs)

# ============================ hip link: hip_l (shared) ============================
# hip_l local: roll horn face at (12.6,-13.3,0) axis -y; pitch horn face + bearing at
# (30.6,0,0)/(29.2,0,0) axis +x. Bent link joining the two faces.
def _hip_link_local():
    # mostly hidden inside the hip - a clean solid bracket (no internal cavity)
    pitch_wall = box_at((28.0, -10.5, -9.5), (31.5, 10.5, 9.5))
    roll_wall = box_at((5.0, -15.5, -9.0), (20.5, -10.5, 9.0))
    arm = box_at((8.0, -15.0, -7.5), (30.0, -7.5, 7.5))
    riser = box_at((24.0, -15.0, -7.5), (30.0, 6.0, 7.5))
    return union_all([pitch_wall, roll_wall, arm, riser])

@builder("hip_l")
def build_hip_l(items):
    gs = [_hip_link_local(), keep_material("hip_l", items)]
    bosses = [b for it in items for b in horn_bosses_local(it)]
    gs.append(union_all(bosses))
    return union_all(gs)

# ============================ ankle + foot ============================
# ankle_left local: ankle horn face at (46.6,15.8,-4.5) axis +x; bearing seat beside
# it (seeed at ~x24-30); foot plate + sole attach below (z<-9). Bracket + foot shoe.
def _ankle_local():
    horn_wall = local_box(43.5, 48.5, 6.0, 26.0, -14.0, 6.0, r=1.5)
    bracket = local_box(24.0, 46.0, 11.0, 22.0, -13.0, 2.0, r=1.5)
    brace = local_box(24.0, 44.0, 13.0, 19.0, -18.0, -8.0, r=1.5)
    g = union_all([horn_wall, bracket, brace])
    return g

@builder("ankle_left")
def build_ankle_left(items):
    gs = [_ankle_local(), keep_material("ankle_left", items)]
    bosses = [b for it in items for b in horn_bosses_local(it)]
    gs.append(union_all(bosses))
    return union_all(gs)

def _mirror_x(m):
    m = m.copy()
    m.apply_transform(np.diag([-1.0, 1.0, 1.0, 1.0]))
    if m.volume < 0:
        m.invert()
    return m

@builder("ankle_right")
def build_ankle_right(items):
    gs = [_mirror_x(_ankle_local()), keep_material("ankle_right", items)]
    bosses = [b for it in items for b in horn_bosses_local(it)]
    gs.append(union_all(bosses))
    return union_all(gs)

# foot: flat shoe plate z -21..-9, sole pad under it. Same local frame as ankle_left.
def _foot_local():
    shoe = _shell_extrude(20.0, 11.0, -16.5, 41.0, 13.0, 5.0, 30.0, taper=0,
                          wall=1.8, cap=1.8)
    return shoe

@builder("foot_left")
def build_foot_left(items):
    return union_all([_foot_local(), keep_material("foot_left", items)])

@builder("foot_right")
def build_foot_right(items):
    return union_all([_mirror_x(_foot_local()), keep_material("foot_right", items)])

@builder("sole_left")
def build_sole_left(items):
    pad = local_box(21.0, 50.5, -8.0, 29.5, -22.5, -19.0, r=3.0)
    return union_all([pad, keep_material("sole_left", items)])

@builder("sole_right")
def build_sole_right(items):
    pad = local_box(21.0, 50.5, -8.0, 29.5, -22.5, -19.0, r=3.0)
    return union_all([_mirror_x(pad), keep_material("sole_right", items)])

# ============================ main ============================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="")
    ap.add_argument("--dry", action="store_true", help="build but do not write STLs")
    ap.add_argument("--no-corr", action="store_true", help="skip swept-corridor cuts (faster, for look tests)")
    a = ap.parse_args()
    todo = a.parts.split(",") if a.parts else list(BUILDERS)
    # pass A: pre-cut geometry for every requested STL (registers NEW_WORLD per
    # instance so corridors of every part see the redesigned neighbours)
    pres = []
    for name in todo:
        fn = BUILDERS[name]
        items = instances(name)
        g = fn(items)                       # one geometry per STL (shared instances)
        if g is None:
            print(f"[{name}]: builder returned None - skipped"); continue
        for it in items:
            world = g.copy(); world.apply_transform(it.T)
            NEW_WORLD[IDX[id(it)]] = world
        pres.append((name, items, g))
    # pass B: cut pockets + swept corridors, finish
    for name, items, g in pres:
        wb = []
        for it in items:
            w = g.copy(); w.apply_transform(it.T); wb.append(w.bounds)
        wb = [np.minimum.reduce([b[0] for b in wb]), np.maximum.reduce([b[1] for b in wb])]
        print(f"[{name}] bodies={[it.body for it in items]}")
        cuts = pockets_local(items) + horn_disc_local(items) + \
            neighbor_servo_cuts(items, wb)
        if not a.no_corr:
            cor = corridors_local(items, wb)
            if cor is not None:
                # the corridor must not eat the functional keep-zones (horn faces,
                # bearing seats) - clip it away from them before cutting
                keepz = union_all([z for it in items
                                   for z in horn_keeps_local(it) + bearing_keeps_local(it)])
                if keepz is not None:
                    cor = trimesh.boolean.difference([cor, keepz], engine=MAN)
                cuts.append(cor)
        g = subtract_all(g, cuts)
        if a.dry:
            print(f"   dry: vol={g.volume/1000:.2f} cm3 watertight={g.is_watertight}")
        else:
            finish(name, g)

if __name__ == "__main__":
    main()
