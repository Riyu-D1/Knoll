"""Targeted sweep clearance for the refined leg parts.

Runs the same moving-vs-static contact sweep as sweep_check.py, but only for the
leg joints, and instead of just reporting collisions it carves them: for every
NEW contact pair the swept cutter (the *other* item's mesh, or the SCS0009 case
envelope) is subtracted from MY part, at exactly the angles where it collided.

Interface keep-zones (horn wafers, bearing rings, designed boss discs) are
protected by subtracting the keep zones from the cutter before the boolean.

Usage: ~/Knoll-cad-venv/bin/python tools/leg_clearance.py [--rounds 3] [--dry-run]
"""
import sys, argparse, xml.etree.ElementTree as ET
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
from trimesh.collision import CollisionManager
import spec, scs0009
from assembly import build
import make_legs as ML   # keep-zone helpers, manifold booleans, finish()

ap = argparse.ArgumentParser()
ap.add_argument("--rounds", type=int, default=3)
ap.add_argument("--step", type=float, default=10.0)
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

MINE = {"yaw2roll", "bearing_roll", "hip_l", "upper_leg_left", "upper_leg_right",
        "leg", "ankle_left", "ankle_right", "foot_left", "foot_right",
        "sole_left", "sole_right"}
LEG_JOINTS = [j[0] for j in spec.JOINTS
              if j[0].startswith(("left_hip", "right_hip", "left_knee", "right_knee",
                                  "left_ankle", "right_ankle"))]

# --- moving sets (copied from sweep_check.py) ------------------------------
root = ET.parse(spec.UPSTREAM_DIR / "robot_walk.xml").getroot()
joint_body, desc = {}, {}
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
rng = {j.get("name"): [np.degrees(float(x)) for x in j.get("range").split()]
       for j in root.iter("joint") if j.get("name") and j.get("range")}

def contacts_at(q, moving, items=None):
    items = items if items is not None else build(q=q)
    A, B = CollisionManager(), CollisionManager()
    for k, it in enumerate(items):
        (A if it.body in moving else B).add_object(f"{k}|{it.mesh}|{it.body}", it.mesh_obj)
    hit, names, data = A.in_collision_other(B, return_names=True, return_data=True)
    out = {}
    for c in (data or []):
        key = tuple(sorted(x.split("|", 1)[1] for x in c.names))
        out[key] = max(out.get(key, 0), c.depth)
    return out

def find_item(items, mesh, body):
    for it in items:
        if it.mesh == mesh and it.body == body:
            return it
    return None

def cutter_for(tok, item, Ti):
    """world cutter -> local of target item. tok is (mesh, body)."""
    mesh, body = tok
    if mesh.startswith("scs0009:"):
        sv = find_item(ITEMS, mesh, body)
        c = scs0009.envelope_mesh(grow=0.4, horn=True).copy()
        return [c.apply_transform(Ti @ sv.T)]
    src = find_item(ITEMS, mesh, body)
    if src is None:
        return []
    return [src.mesh_obj.copy().apply_transform(Ti)]

ITEMS = None
for rnd in range(a.rounds):
    ITEMS = build()
    plan = {}          # (target_mesh) -> list of (item, [local cutters])
    remaining = []
    for jn in LEG_JOINTS:
        moving = desc[joint_body[jn]]
        lo_r, hi_r = spec.SWEEP_REQUIRED_DEG[jn]
        lo, hi = max(lo_r, rng[jn][0]), min(hi_r, min(rng[jn][1], 150))
        base = contacts_at({}, moving, ITEMS)
        angles = sorted(set(np.r_[np.arange(lo, hi, a.step), hi].round(1)) - {0.0})
        # which pairs collide at which angle
        hits = {}      # pair -> set of angles
        for ang in angles:
            for key, dpt in contacts_at({jn: ang}, moving).items():
                if dpt > base.get(key, 0) + 0.5:
                    hits.setdefault(key, set()).add(ang)
        for (mk, sk), angs in hits.items():
            mmesh, mbody = mk.split("|"); smesh, sbody = sk.split("|")
            # targets: carve every side of the overlap that is mine - a collision
            # sitting inside one part's keep-zone can only be cleared from the
            # other part's face.
            pairs = []
            if mmesh in MINE:
                pairs.append(((mmesh, mbody), (smesh, sbody)))
            if smesh in MINE:
                pairs.append(((smesh, sbody), (mmesh, mbody)))
            if not pairs:
                remaining.append((jn, mk, sk))
                continue
            # densify: the reported hit angles come from a coarse contact sweep -
            # pad +-5 deg and cut at 5 deg steps so intermediate poses are covered.
            cut_angles = set()
            for ang in angs:
                cut_angles.update(np.arange(ang - 5.0, ang + 5.1, 5.0).round(2))
            for tgt_tok, cut_tok in pairs:
                for ang in sorted(cut_angles):
                    items_q = build(q={jn: ang})
                    tgt_q = find_item(items_q, *tgt_tok)
                    cut_src = find_item(items_q, *cut_tok)
                    if cut_tok[0].startswith("scs0009:"):
                        c = scs0009.envelope_mesh(grow=0.4, horn=True).copy()
                        c.apply_transform(cut_src.T)
                    else:
                        c = cut_src.mesh_obj.copy()
                    plan.setdefault(tgt_tok[0], []).append(
                        (tgt_tok, c.copy().apply_transform(np.linalg.inv(tgt_q.T))))
        print(f"round {rnd} {jn}: {len(hits)} new pairs")
    if not plan and not remaining:
        print("CLEAR: no new contacts")
        break
    if remaining:
        for r in remaining:
            print("   SKIP (no mine part):", r)
    if a.dry_run:
        for k, v in plan.items():
            print(f"   would cut {k}: {len(v)} cutters")
        break
    # apply grouped cuts per shared STL
    by_mesh = {}
    for mesh, jobs in plan.items():
        by_mesh.setdefault(mesh, []).extend(jobs)
    for mesh, jobs in by_mesh.items():
        items = ML.instances(mesh)
        if not items:
            continue
        # union cutters transformed into ONE canonical local frame (instance 0),
        # transforming each job's local cutter through the instance's local->local
        ref = items[0]
        locs = []
        for tgt_tok, c_local in jobs:
            tgt = find_item(ITEMS, *tgt_tok)
            if tgt.mesh != mesh:
                continue
            locs.append(c_local)
        if not locs:
            continue
        cut = ML.union_all([c for c in locs])   # ONE solid - manifold needs watertight inputs
        # protect keep zones: subtract them from the cutter
        zones = []
        for it in items:
            # only the real interface zones are protected; cosmetic boss discs get
            # swept-trimmed to the clearance radius on purpose
            zones += ML.horn_keeps_local(it) + ML.bearing_keeps_local(it)
        if zones:
            try:
                z = ML.union_all(zones)
                cut2 = trimesh.boolean.difference([cut, z], engine="manifold")
                if cut2 is not None and cut2.is_volume:
                    cut = cut2
            except Exception as e:
                print(f"   {mesh}: keep-zone protect failed ({e}); cutting anyway")
        part = trimesh.load(ML.WORK / f"{mesh}.stl", force="mesh")
        for name_m, m in (("part", part), ("cut", cut)):
            if not m.is_volume:
                fixed = ML.meshfix(m)
                if fixed is not None and fixed.is_volume:
                    if name_m == "part":
                        part = fixed
                    else:
                        cut = fixed
        if not part.is_volume or not cut.is_volume:
            print(f"   {mesh}: still non-volume (part={part.is_volume} cut={cut.is_volume}) - skipped")
            continue
        try:
            res = trimesh.boolean.difference([part, cut], engine="manifold")
        except Exception as e:
            res = None
            print(f"   {mesh}: difference error ({e})")
        if res is None:
            print(f"   {mesh}: difference failed - skipped")
            continue
        if a.dry_run:
            continue
        ML.finish(mesh, res, note=f"after targeted cuts ({len(locs)} cutters)")
print("done")
