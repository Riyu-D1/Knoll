"""STEP 1 of the head-enclosure session: measure which head/neck servos stick out of the head shell.

A servo surface point "sticks out" iff it can be seen from at least one world axis direction:
rasterize every part's triangles (whole robot minus servos/elec placeholders) into an occupancy
grid (cell = any triangle AABB touches it), then precompute per direction whether a surface cell
exists further out (six cumsum masks). A sample with an unblocked direction = visible; a sample
inside solid material or inside the helmet cavity has all six directions blocked = hidden.
"How far out" = closest point on the concatenated SKIN meshes (shells/face/jaw/eye — interior
mounts excluded), offset vector decomposed onto the 6 world sides.
Servos sitting mostly in the neck/trunk region are reported separately - not part of the fix.
Run: python tools/head_protrusion.py [--samples 3000] [--pitch 0.5] [--q head_roll=20]
"""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
import spec, scs0009
from assembly import build

SIDES = [("back", -1, 0, 0), ("front", +1, 0, 0), ("left", 0, +1, 0), ("right", 0, -1, 0),
         ("top", 0, 0, +1), ("bottom", 0, 0, -1)]
HEAD_SERVOS = ["neck_pitch", "head_pitch", "head_yaw", "head_roll"]
SKIN = {"top_head_shell", "bottom_head_shell", "face_part", "jaw", "jaw_soft",
        "soft_mouth_top", "noenoeil"}          # exterior skin; motor_support/lens stay inside
MARGIN = 8.0


def _tri_occ(mesh, origin, span, pitch, occ):
    """Mark every grid cell touched by a triangle's AABB (surface occupancy, no rays)."""
    if mesh.bounds is None:
        return
    tri = mesh.triangles                                    # (n,3,3)
    lo = np.clip(np.floor((tri.min(axis=1) - origin) / pitch).astype(int), 0, span)
    hi = np.clip(np.floor((tri.max(axis=1) - origin) / pitch).astype(int) + 1, 0, span)
    keep = np.all(hi > lo, axis=1)
    for a, b_ in zip(lo[keep], hi[keep]):
        occ[a[0]:b_[0], a[1]:b_[1], a[2]:b_[2]] = True


def _blocked_masks(occ):
    """blocked[k] = True where SIDES[k] direction from the cell hits an occupied cell further
    out. SIDES order: -x,+x,+y,-y,+z,-z."""
    out = []
    for ax, sgn in ((0, -1), (0, +1), (1, +1), (1, -1), (2, +1), (2, -1)):
        cum = occ.cumsum(ax)
        if sgn < 0:
            out.append(cum - occ.astype(np.int32) > 0)         # occupied below this index
        else:
            total = np.expand_dims(np.take(cum, occ.shape[ax] - 1, ax), ax)
            out.append(total - cum > 0)                        # occupied above this index
    return out


def occlusion_grid(items, bounds_meshes, pitch=0.5):
    """occupancy grid + 6 axis-blocked masks over ALL parts (minus servos/elec).
    bounds_meshes: extra meshes that decide the grid extent (skin + servo envs).
    returns (lo, pitch, span, blocked list in SIDES order)."""
    cat = trimesh.util.concatenate(bounds_meshes)
    lo, hi = [b.astype(float) for b in cat.bounds]
    lo -= MARGIN; hi += MARGIN
    span = np.ceil((hi - lo) / pitch).astype(int) + 1
    occ = np.zeros(span, bool)
    for i in items:
        if i.kind != "servo" and not i.mesh.startswith("elec_"):
            _tri_occ(i.mesh_obj, lo, span, pitch, occ)
    return lo, pitch, span, _blocked_masks(occ)


def unblocked_mask(pts_world, lo, pitch, span, blocked):
    """(n,6) — True where the direction from the point to outside is free."""
    ij = np.round((pts_world - lo) / pitch).astype(int)
    inb = np.all((ij >= 0) & (ij < np.array(span)), axis=1)
    out = np.zeros((len(pts_world), 6), bool)
    for k, b in enumerate(blocked):
        ok = inb.copy(); ok[inb] = ~b[ij[inb, 0], ij[inb, 1], ij[inb, 2]]
        out[:, k] = ok | ~inb                            # out-of-grid = unblocked
    return out


def analyze(q=None, samples=3000, pitch=0.5):
    items = build(q=q or {})
    skin_items = [i for i in items if i.body == spec.HEAD_BODY and i.kind == "printed"
                  and i.mesh in SKIN]
    skin = trimesh.util.concatenate([i.mesh_obj for i in skin_items])
    envs = {}
    for i in items:
        if i.kind == "servo" and i.mesh.split(":")[1] in HEAD_SERVOS:
            e = scs0009.envelope_mesh(horn=True).copy(); e.apply_transform(i.T)
            envs[i.mesh.split(":")[1]] = (i.body, e)
    lo, pitch, span, blocked = occlusion_grid(
        items, [skin] + [e for _, e in envs.values()], pitch)

    out = {}
    for jn, (body, env) in envs.items():
        pts, _ = trimesh.sample.sample_surface(env, samples, seed=1)
        pts = np.vstack([pts, env.vertices])
        unblocked = unblocked_mask(pts, lo, pitch, span, blocked)
        visible = unblocked.any(axis=1)
        vis = np.where(visible)[0]
        growth = {n: 0.0 for n, *_ in SIDES}
        if len(vis):
            cps, _, _ = skin.nearest.on_surface(pts[vis])
            v = pts[vis] - cps
            for k, (n, dx, dy, dz) in enumerate(SIDES):
                d = np.array([dx, dy, dz]); ax = int(np.nonzero(d)[0][0])
                sel = unblocked[vis, k]
                if sel.any():
                    growth[n] = max(0.0, float((v[sel, ax] * d[ax]).max()))
        out[jn] = dict(body=body, n=len(pts), air=int(len(vis)),
                       growth=growth, points=pts[vis] if len(vis) else np.zeros((0, 3)),
                       env_bounds=env.bounds.copy())
    return skin, out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=3000)
    ap.add_argument("--pitch", type=float, default=0.5)
    ap.add_argument("--q", nargs="*", default=[])
    a = ap.parse_args()
    q = {k: float(v) for k, v in (s.split("=") for s in a.q)}
    skin, res = analyze(q, a.samples, a.pitch)
    hb = skin.bounds
    print(f"head skin bbox {hb[0].round(1)} .. {hb[1].round(1)}")
    print(f"{'servo':12s} {'body':16s} {'visible':>8s} | mm past skin surface: "
          + " ".join(f"{n:>6s}" for n, *_ in SIDES) + "   where")
    for jn, r in res.items():
        g = " ".join(f"{r['growth'][n]:6.2f}" for n, *_ in SIDES)
        sides = [n for n, *_ in SIDES if r["growth"][n] > 0.3]
        eb = r["env_bounds"]; below = eb[1][2] < hb[0][2] + 15
        tag = "  [neck region]" if below else ""
        print(f"{jn:12s} {r['body']:16s} {r['air']:5d}/{r['n']:<5d} | {g}   "
              + (",".join(sides) or "enclosed") + tag)
