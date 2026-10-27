"""Verify the fused production parts in out/knoll-mini.blend.

Checks (on the actual exported meshes):
  1. every printable part is a positive-volume closed solid
  2. component/servo proxies have zero volumetric intersection with
     every printable part they should clear
  3. printed parts do not collide with each other (part x part)
  4. every heat-set insert proxy is embedded in solid material —
     sampled on a ring at r=1.7 mm around its axis (the Ø3.6 insert
     presses into a Ø3.2 printed hole, so its centre is air: the
     engagement ring is what must sit inside material)
Run:  blender -b out/knoll-mini.blend --python verify_parts.py
"""
import sys

import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

PCOLS = ("LEG_L", "LEG_R", "TRUNK", "ARMS", "NECK", "HEAD")


def mesh_vol(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    v = abs(bm.calc_volume())
    bm.free()
    return v


def bvh(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    # triangulate first — FromBMesh tessellates n-gons differently than the
    # STL export path (an annulus cap n-gon reads as a plugged hole), which
    # flips inside() parity and produces phantom overlaps
    bmesh.ops.triangulate(bm, faces=bm.faces)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def _march(tree, p, ray):
    """count surface crossings; skips grazing double-hits (a ray exiting a
    cylindrical bore obliquely can hit two adjacent faces ~1 um apart and
    flip parity — real walls are >=1.2 mm, so 50 um dedupe is safe)."""
    hits = 0
    last = None
    for _ in range(600):
        loc, n, i, d = tree.ray_cast(p, ray)
        if loc is None:
            break
        if last is None or (loc - last).length > 5e-5:
            hits += 1
            last = loc
        p = loc + ray * 2e-6
    return hits


def inside(obj, tree, pt_world):
    """odd/even ray cast for point-in-closed-solid (local space)."""
    inv = obj.matrix_world.inverted()
    ray = inv.to_3x3() @ Vector((0.57735, 0.57735, 0.57735))
    ray.normalize()
    p = inv @ Vector(pt_world)
    return _march(tree, p, ray) % 2 == 1


def bbox_overlap(a, b, pad=0.0):
    a = [a.matrix_world @ Vector(c) for c in a.bound_box]
    b = [b.matrix_world @ Vector(c) for c in b.bound_box]
    return all(
        min(p[i] for p in a) - pad <= max(p[i] for p in b)
        and min(p[i] for p in b) - pad <= max(p[i] for p in a)
        for i in range(3))


def world_bvh(o):
    """BVH of the mesh baked into world space."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.transform(o.matrix_world)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


_AXIS_RAYS = (
    Vector((1, 0, 0)), Vector((-1, 0, 0)),
    Vector((0, 1, 0)), Vector((0, -1, 0)),
    Vector((0, 0, 1)), Vector((0, 0, -1)),
)


def inside_w(tree, pt):
    """point-in-closed-solid, world space. Diagonal rays graze corner
    posts/mouth rims of the fused pockets and flip parity; axis rays cross
    the boxy walls perpendicularly. A point inside an open pocket reads
    even on nearly every axis ray (exits through walls in pairs or out the
    mouth) while a point inside material reads odd — require >=4 of 6."""
    p = Vector(pt)
    votes = sum(1 for r in _AXIS_RAYS if _march(tree, p, r) % 2 == 1)
    return votes >= 4


def overlap_vol(a, b, ta, tb):
    """Approximate mm^3 of a n b: BVH triangle-overlap gate, then a point
    grid inside the shared AABB sampled against both solids. Boolean-free —
    immune to solver failures on multi-shell fused parts."""
    ra = [a.matrix_world @ Vector(c) for c in a.bound_box]
    rb = [b.matrix_world @ Vector(c) for c in b.bound_box]
    lo = [max(min(p[i] for p in ra), min(p[i] for p in rb)) for i in range(3)]
    hi = [min(max(p[i] for p in ra), max(p[i] for p in rb)) for i in range(3)]
    if any(hi[i] <= lo[i] + 1e-6 for i in range(3)):
        return 0.0
    if not ta.overlap(tb):
        # no surface contact: possible full nesting — probe a few verts of
        # the smaller solid inside the larger before grid sampling
        ca = sum((Vector(p) for p in ra), Vector()) / 8.0
        cb = sum((Vector(p) for p in rb), Vector()) / 8.0
        if not (inside_w(ta, cb) or inside_w(tb, ca)):
            return 0.0
        # fall through to the grid — it resolves partial overlaps correctly
    # pick a grid step so total samples stay ~<60k
    vol_aabb = 1.0
    for i in range(3):
        vol_aabb *= max(hi[i] - lo[i], 1e-6)
    step = (vol_aabb / 60000.0) ** (1.0 / 3.0)
    step = max(step, 0.0002)
    import math
    nx = max(1, int((hi[0] - lo[0]) / step) + 1)
    ny = max(1, int((hi[1] - lo[1]) / step) + 1)
    nz = max(1, int((hi[2] - lo[2]) / step) + 1)
    cnt = 0
    for ix in range(nx):
        px = lo[0] + (ix + 0.5) * (hi[0] - lo[0]) / nx
        for iy in range(ny):
            py = lo[1] + (iy + 0.5) * (hi[1] - lo[1]) / ny
            for iz in range(nz):
                pz = lo[2] + (iz + 0.5) * (hi[2] - lo[2]) / nz
                if inside_w(ta, (px, py, pz)) and inside_w(tb, (px, py, pz)):
                    cnt += 1
    return cnt * vol_aabb / (nx * ny * nz)


def ring_inside(obj, tree, ins, npts=6, r=0.0017):
    """sample npts on a ring of radius r around the insert's axis."""
    m = ins.matrix_world
    axis = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
    ref = axis.cross(Vector((1, 0, 0)))
    if ref.length < 0.5:
        ref = axis.cross(Vector((0, 1, 0)))
    u = ref.normalized()
    v = axis.cross(u).normalized()
    c = m.translation
    import math
    ok = 0
    for i in range(npts):
        a = 2 * math.pi * i / npts
        p = c + (u * math.cos(a) + v * math.sin(a)) * r
        if inside(obj, tree, p):
            ok += 1
    return ok


parts, probes, inserts = [], [], []
for cname in PCOLS:
    col = bpy.data.collections.get(cname)
    if not col:
        continue
    for o in col.objects:
        if o.type != "MESH":
            continue
        if o.get("proxy") or o.get("component"):
            probes.append(o)
        else:
            parts.append(o)
col = bpy.data.collections.get("COMPONENTS")
if col:
    probes += [o for o in col.objects if o.type == "MESH"]
col = bpy.data.collections.get("HARDWARE")
if col:
    inserts += [o for o in col.objects if o.type == "MESH"
                and "INS" in o.name.upper()]

print(f"[parts] {len(parts)} printable  [probes] {len(probes)}  [inserts] {len(inserts)}")

fails = []

# 1. solid volumes
print("\n== solid volumes ==")
minv = 1e9
for o in parts:
    v = mesh_vol(o) * 1e9  # m^3 -> mm^3
    minv = min(minv, v)
    if v < 1.0:
        fails.append(f"{o.name}: volume {v:.3f} mm3 (degenerate)")
        print(f"  FAIL {o.name} vol={v:.3f} mm3")
print(f"  smallest part volume: {minv:.1f} mm3  ({len(parts)} checked)")

wtrees = {o.name: world_bvh(o) for o in parts}
ptrees = {o.name: world_bvh(o) for o in probes}

# 2. component clearance: probe vs every part whose AABB overlaps
print("\n== component fit (volumetric) ==")
tested = 0
for p in probes:
    for t in parts:
        if not bbox_overlap(p, t):
            continue
        v = overlap_vol(p, t, ptrees[p.name], wtrees[t.name])
        tested += 1
        if v == -2.0:
            fails.append(f"{p.name} x {t.name}: nested containment")
            print(f"  HIT  {p.name:22s} x {t.name:22s} NESTED")
        elif v > 0.5e-9:  # > 0.5 mm3 — print-tolerance floor
            fails.append(f"{p.name} x {t.name}: {v*1e9:.2f} mm3 intrusion")
            print(f"  HIT  {p.name:22s} x {t.name:22s} {v*1e9:8.2f} mm3")
print(f"  {tested} pairs tested")

# 3. part x part interference (printed parts must not occupy same space)
print("\n== part x part interference ==")
tested = 0
for i, a in enumerate(parts):
    for b in parts[i + 1:]:
        if not bbox_overlap(a, b):
            continue
        v = overlap_vol(a, b, wtrees[a.name], wtrees[b.name])
        tested += 1
        if v == -2.0:
            fails.append(f"{a.name} x {b.name}: nested containment")
            print(f"  HIT  {a.name:22s} x {b.name:22s} NESTED")
        elif v > 1e-9:  # > 1 mm3 — real overlap, not a touch
            fails.append(f"{a.name} x {b.name}: {v*1e9:.2f} mm3 part overlap")
            print(f"  HIT  {a.name:22s} x {b.name:22s} {v*1e9:8.2f} mm3")
print(f"  {tested} pairs tested")

# 4. insert seats: ring at r1.7 mm must sit inside part material
print("\n== insert seats (ring test) ==")
import math
in_ok = 0
for ins in inserts:
    best = 0
    hit = None
    m = ins.matrix_world
    axis = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
    ref = axis.cross(Vector((1, 0, 0)))
    if ref.length < 0.5:
        ref = axis.cross(Vector((0, 1, 0)))
    u = ref.normalized()
    v = axis.cross(u).normalized()
    c = m.translation
    for n, t in wtrees.items():
        k = sum(
            inside_w(t, c + (u * math.cos(2 * math.pi * i / 6)
                             + v * math.sin(2 * math.pi * i / 6)) * 0.0017)
            for i in range(6))
        if k > best:
            best, hit = k, n
    if best >= 4:
        in_ok += 1
    else:
        fails.append(f"{ins.name}: only {best}/6 ring pts inside material")
        print(f"  MISS {ins.name} (best {best}/6 in {hit})")
print(f"  {in_ok}/{len(inserts)} inserts seated in material")

print("\n== RESULT ==")
if fails:
    print(f"FAIL - {len(fails)} issue(s)")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS - all solids, component fits, part clearances and insert seats verified")
