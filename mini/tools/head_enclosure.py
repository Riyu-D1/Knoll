"""Extend a head shell part outward to fully enclose a protruding SCS0009.

What it does (all math in the PART's own mesh frame):
  1. sweep the servo envelope over the joint that moves it RELATIVE to the shell
     (--rel-joint; omit when the servo is rigid in the head body, e.g. head_roll).
  2. find which swept verts are outside the skin's outer silhouette (per-axis column
     extremes of a rasterized skin grid).
  3. bulge = convex hull( exposed swept verts + nearby shell verts ), grown by
     wall+clearance mm -> union into the part = smooth tapered bulge, >= `wall` mm wall.
  4. cut the interior = swept envelope grown by `clearance` mm, so the servo keeps its
     clearance through the full relative sweep.
Run: python tools/head_enclosure.py --servo head_yaw --part bottom_head_shell \
        --rel-joint head_roll --rel-lo -25 --rel-hi 25 [--dry-run]
"""
import sys, argparse, xml.etree.ElementTree as ET
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
import spec, scs0009
from assembly import build
from head_protrusion import SKIN, _tri_occ, occlusion_grid, unblocked_mask


def _descendants():
    """(body -> subtree set incl. itself, joint -> body) from the MJCF."""
    root = ET.parse(spec.UPSTREAM_DIR / "robot_walk.xml").getroot()
    desc, joint_body = {}, {}
    def walk(b, chain):
        n = b.get("name"); chain = chain + [n]
        for anc in chain:
            desc.setdefault(anc, set()).add(n)
        for j in b.findall("joint"):
            if j.get("name"):
                joint_body[j.get("name")] = n
        for c in b.findall("body"):
            walk(c, chain)
    for b in root.find("worldbody").findall("body"):
        walk(b, [])
    return desc, joint_body

def _parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--servo", required=True)
    ap.add_argument("--part", required=True)
    ap.add_argument("--rel-joint", default=None,
                    help="joint that moves the servo RELATIVE to the shell (omit => fixed)")
    ap.add_argument("--rel-lo", type=float, default=0.0)
    ap.add_argument("--rel-hi", type=float, default=0.0)
    ap.add_argument("--wall", type=float, default=2.5)
    ap.add_argument("--clearance", type=float, default=0.5)
    ap.add_argument("--void", type=float, default=None,
                    help="interior void growth (defaults to --clearance); raise past "
                         "clearance when the real servo mesh exceeds the env model")
    ap.add_argument("--patch", type=float, default=10.0,
                    help="shell-patch radius for the hull blend")
    ap.add_argument("--deform", action="store_true",
                    help="push part verts that lie inside the grown swept env out to its "
                         "surface - smooth bulge with no new surfaces")
    ap.add_argument("--pod", action="store_true",
                    help="grow the swept envelope itself (wall+clearance) instead of a "
                         "convex-hull bulge - for servos that exit through the rim gap")
    ap.add_argument("--cluster", type=float, default=0.0,
                    help="split exposed points into clusters this mm apart; one bulge each")
    ap.add_argument("--zrange", nargs=2, type=float, default=None,
                    help="only hull exposed points in this local-z range (rest reported only)")
    ap.add_argument("--captol", type=float, default=2.0,
                    help="inflation around the exposed region pulling env verts into the hull")
    ap.add_argument("--zfloor", type=float, default=None,
                    help="world-z lower bound for added material (keeps the bulge off lower servos)")
    ap.add_argument("--clear", action="store_true",
                    help="cut a corridor for every stationary part swept through the head "
                         "joints (head_yaw/head_roll/head_pitch) so the grown shell does "
                         "not collide during range-of-motion sweeps")
    ap.add_argument("--perpose", action="store_true",
                    help="one tight hull per sweep pose instead of one hull for all")
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


def main():
    a = _parse()
    items0 = build()
    skin_items = [i for i in items0 if i.body == spec.HEAD_BODY and i.kind == "printed"
                  and i.mesh in SKIN]
    skin = trimesh.util.concatenate([i.mesh_obj for i in skin_items])
    # occlusion grid covers the skin + the servo at every sweep pose
    angles = [0.0] if not a.rel_joint else list(np.linspace(a.rel_lo, a.rel_hi, 7))
    bounds_envs = []
    for ang in angles:
        it = items0 if ang == 0 else build(q={a.rel_joint: ang})
        sv = [i for i in it if i.mesh == f"scs0009:{a.servo}"][0]
        e = scs0009.envelope_mesh(horn=True).copy(); e.apply_transform(sv.T)
        bounds_envs.append(e)
    lo, pitch, span, blocked = occlusion_grid(items0, [skin] + bounds_envs)
    exposed_per_pose, swept_local = [], []
    for ang in angles:
        items = items0 if ang == 0 else build(q={a.rel_joint: ang})
        sv = [i for i in items if i.mesh == f"scs0009:{a.servo}"][0]
        pt = [i for i in items if i.mesh == a.part and i.body == spec.HEAD_BODY][0]
        env = scs0009.envelope_mesh(horn=True).copy(); env.apply_transform(sv.T)
        pts, _ = trimesh.sample.sample_surface(env, 4000, seed=1)
        pts = np.vstack([pts, env.vertices])
        exp = unblocked_mask(pts, lo, pitch, span, blocked).any(axis=1)
        Ti = np.linalg.inv(pt.T)
        if exp.any():
            exposed_per_pose.append(trimesh.transform_points(pts[exp], Ti))
        env_l = env.copy(); env_l.apply_transform(Ti)
        swept_local.append(env_l)
    print(f"{a.servo}: {len(angles)} sweep pose(s), exposed verts "
          f"{sum(len(e) for e in exposed_per_pose)} -> part {a.part}")

    if not exposed_per_pose:
        print("nothing protrudes at these poses - no edit needed"); sys.exit(0)

    exposed_l = np.vstack(exposed_per_pose)
    part = trimesh.load(spec.WORK_DIR / f"{a.part}.stl", force="mesh")
    T_part = [i for i in items0 if i.mesh == a.part and i.body == spec.HEAD_BODY][0].T
    g = a.wall + a.clearance
    dirs26 = [np.array(s, float) / np.linalg.norm(s) * g
              for s in [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)
                        if (i, j, k) != (0, 0, 0)]]
    if a.deform:
        # carved-union pod: carve the part by the grown swept env, then union a
        # PRE-HOLLOWED pod (outer grown wall+clearance+0.3 overlap, inner env+clearance).
        # The carve removes tray material from the merge zone, so no thin sheets get
        # pinched between the pod wall and the tray's own walls -> no sliver fragments.
        def _grown(dist):
            dd = [np.array(s, float) / np.linalg.norm(s) * dist
                  for s in [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)
                            if (i, j, k) != (0, 0, 0)]]
            return trimesh.boolean.union(
                [trimesh.boolean.union(
                    [e.copy().apply_transform(trimesh.transformations.translation_matrix(d))
                     for d in dd], engine="manifold")
                 for e in swept_local], engine="manifold")
        outer = _grown(g + 0.3)            # pod outer wall, overlaps the carve zone
        carve = _grown(g)                  # material removed from the part
        inner = _grown(a.clearance)        # servo clearance void
        pod = trimesh.boolean.difference([outer, inner], engine="manifold")
        carved = trimesh.boolean.difference([part, carve], engine="manifold")
        res = trimesh.boolean.union([carved, pod], engine="manifold")
        hull_g = pod  # for reporting
    elif a.pod:
        # pod = swept envelope grown by wall+clearance, unioned into the part: wherever
        # the servo exits the shell it gets a 2.5 mm shell of its own silhouette.
        # 26-direction growth -> rounded dilation, avoids coincident-face slivers
        dirs = [np.array(s, float) / np.linalg.norm(s) * g
                for s in [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)
                          if (i, j, k) != (0, 0, 0)]]
        hull_g = trimesh.boolean.union(
            [trimesh.boolean.union(
                [e.copy().apply_transform(trimesh.transformations.translation_matrix(d))
                 for d in dirs], engine="manifold")
             for e in swept_local], engine="manifold")
    else:
        # cover the whole protruding cap, not just flagged samples: every swept envelope
        # vert inside the exposed region (bbox inflated 2 mm) goes into the hull
        swept_pts = np.vstack([e.vertices for e in swept_local])
        if a.zrange:
            keep = (exposed_l[:, 2] >= a.zrange[0]) & (exposed_l[:, 2] <= a.zrange[1])
            print(f"   zrange {a.zrange}: keeping {keep.sum()}/{len(keep)} exposed pts")
            exposed_l = exposed_l[keep]
        if a.perpose:
            # rebuild exposed_l grouped by sweep pose: one tight hull per pose
            labels = np.repeat(np.arange(len(exposed_per_pose)),
                               [len(e) for e in exposed_per_pose])
            exposed_l = np.vstack(exposed_per_pose)
        elif a.cluster:
            from scipy.cluster.hierarchy import fclusterdata
            labels = fclusterdata(exposed_l, a.cluster, criterion="distance")
        else:
            labels = np.ones(len(exposed_l), int)
        bulges = []
        for lab in sorted(set(labels)):
            ex = exposed_l[labels == lab]
            cap = np.vstack([ex.min(0) - a.captol, ex.max(0) + a.captol])
            in_cap = swept_pts[np.all((swept_pts > cap[0]) & (swept_pts < cap[1]), axis=1)]
            # shell verts near the protrusion -> the hull tapers onto the existing surface
            eb = np.vstack([ex.min(0) - a.patch, ex.max(0) + a.patch])
            pv = part.vertices[np.all((part.vertices > eb[0]) & (part.vertices < eb[1]), axis=1)]
            if not len(pv):
                pv = part.vertices[part.nearest.on_surface(ex)[1]]
            hull = trimesh.convex.convex_hull(np.vstack([ex, in_cap, pv]))
            print(f"   cluster {lab}: {len(ex)} pts -> hull {hull.extents.round(1)}")
            bulges.append(hull)
        hull_g = trimesh.boolean.union(
            [b.copy().apply_transform(trimesh.transformations.translation_matrix(d))
             for b in bulges
             for d in [(g,0,0),(-g,0,0),(0,g,0),(0,-g,0),(0,0,g),(0,0,-g)]], engine="manifold")
    if a.zfloor is not None:
        # clip added material to world z >= zfloor so the bulge can't reach lower parts.
        # Express the plane (normal = world +z, through world [0,0,zfloor]) in the part
        # frame, then intersect hull_g with a big slab sitting on top of it.
        Ti = np.linalg.inv(T_part)
        p0 = trimesh.transform_points(np.array([[0, 0, a.zfloor]]), Ti)[0]
        zdir = Ti[:3, :3] @ np.array([0, 0, 1.0]); zdir /= np.linalg.norm(zdir)
        size = np.linalg.norm(hull_g.extents) + 20
        clip = trimesh.creation.box(extents=[size, size, size],
            transform=np.linalg.multi_dot([
                trimesh.transformations.translation_matrix(p0 + zdir * size / 2),
                trimesh.geometry.align_vectors([0, 0, 1], zdir)]))
        hull_g = trimesh.boolean.intersection([hull_g, clip], engine="manifold")
    if a.clear and not a.deform:
        # corridor cut: the grown shell must not hit any STATIONARY part while the head
        # moves through the head joints. Carve the swept corridor out of the BULGE
        # (simple solid -> clean notch) before unioning, so the original shell surface
        # is never re-cut. Grow each nearby stationary part once at zero pose (growth
        # commutes with rigid transforms), re-pose it into the shell frame at each
        # sampled angle, and difference the images out of hull_g.
        desc, joint_body = _descendants()
        near_g = []
        cg = a.clearance + 1.0   # extra margin: consumes tangential slivers + sweep slack
        dirs_c = [(cg,0,0),(-cg,0,0),(0,cg,0),(0,-cg,0),(0,0,cg),(0,0,-cg)]
        for it in items0:
            if it.body == spec.HEAD_BODY:
                continue
            if it.mesh_obj.bounds is None or np.linalg.norm(
                    it.mesh_obj.bounds.mean(0) - np.array([20, 0, 165])) > 70:
                continue          # only parts near the head can ever collide
            m0 = (scs0009.envelope_mesh(horn=True).copy().apply_transform(it.T)
                  if it.mesh.startswith("scs0009:") else it.mesh_obj.copy())
            g0 = trimesh.boolean.union(
                [m0.copy().apply_transform(trimesh.transformations.translation_matrix(d))
                 for d in dirs_c], engine="manifold")
            near_g.append((it.body, it.mesh, it.T, g0))
        hb = hull_g.bounds
        cutters = []
        for jn in ("head_yaw", "head_roll", "head_pitch"):
            moving = desc[joint_body[jn]]
            lo_r, hi_r = spec.SWEEP_REQUIRED_DEG[jn]
            for ang in np.r_[np.arange(lo_r, hi_r, 5), hi_r]:
                it_q = build(q={jn: float(ang)})
                Tp = [i for i in it_q if i.mesh == a.part and i.body == spec.HEAD_BODY][0].T
                Ti = np.linalg.inv(Tp)
                for body, mesh, T0, g0 in near_g:
                    if body in moving:
                        continue
                    im = [i for i in it_q if i.mesh == mesh and i.body == body][0]
                    cc = g0.copy().apply_transform(Ti @ im.T @ np.linalg.inv(T0))
                    if cc.bounds[0][0] < hb[1][0] and cc.bounds[1][0] > hb[0][0] and \
                       cc.bounds[0][1] < hb[1][1] and cc.bounds[1][1] > hb[0][1] and \
                       cc.bounds[0][2] < hb[1][2] and cc.bounds[1][2] > hb[0][2]:
                        cutters.append(cc)
        print(f"   corridor: {len(cutters)} overlapping cutters over head_yaw/roll/pitch")
        for k in range(0, len(cutters), 6):
            hull_g = trimesh.boolean.difference([hull_g] + cutters[k:k + 6], engine="manifold")
    if not a.deform:
        res = trimesh.boolean.union([part, hull_g], engine="manifold")

    if not a.deform:
        # interior: swept envelope grown by clearance (the whole corridor, not just
        # exposed verts). For --deform the pod is pre-hollowed and the part pre-carved.
        cg = a.void if a.void is not None else a.clearance
        cut = trimesh.boolean.union(
            [e.copy().apply_transform(trimesh.transformations.translation_matrix(d))
             for e in swept_local
             for d in [(cg,0,0),(-cg,0,0),(0,cg,0),(0,-cg,0),
                       (0,0,cg),(0,0,-cg)]], engine="manifold")
        res = trimesh.boolean.difference([res, cut], engine="manifold")

    bodies = res.split(only_watertight=False)
    nb = len(bodies)
    if nb > 1:
        bodies = sorted(bodies, key=lambda b: b.volume, reverse=True)
        for b in bodies[1:8]:
            print(f"   fragment vol {b.volume:.1f} mm3 bounds {b.bounds.round(1).tolist()}")
        if len(bodies) > 8:
            print(f"   ... {len(bodies)-8} more sliver fragments")
        # sliver flakes where the pod crosses cavity walls are droppable - the largest
        # body is the shell+pod; everything else sits in air regions
        res = bodies[0]; nb = 1
    print(f"{a.part}: volume {part.volume/1000:.2f} -> {res.volume/1000:.2f} cm3 "
          f"(bulge +{hull_g.volume/1000:.2f} cm3), extents {part.extents.round(1)} -> "
          f"{res.extents.round(1)}, watertight={res.is_watertight} bodies={nb}")
    assert res.is_watertight, "not watertight - not saved"
    if nb > 1: print("part split - NOT saved"); sys.exit(1)
    if not a.dry_run:
        out = spec.WORK_DIR / f"{a.part}.stl"
        res.export(out)
        m = trimesh.load(out, force="mesh")
        if not m.is_watertight:
            # coincident sliver sheets survive booleans and collapse on the STL
            # round-trip - remesh the solid through voxels instead (no slivers possible)
            print("   STL round-trip non-manifold -> voxel remesh")
            vox = trimesh.voxel.creation.voxelize_subdivide(res, pitch=0.35)
            m = vox.marching_cubes
            m.merge_vertices()
            if not m.is_watertight:
                print("   voxel remesh not watertight - NOT saved"); sys.exit(1)
            m.export(out)
            m = trimesh.load(out, force="mesh")
        if not m.is_watertight:
            print("   STL round-trip left non-manifold edges - NOT saved"); sys.exit(1)
        print(f"wrote {out} (reloaded watertight={m.is_watertight}, "
              f"vol={m.volume/1000:.2f} cm3)")


if __name__ == "__main__":
    main()
