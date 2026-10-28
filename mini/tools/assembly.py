"""Forward-kinematics assembly of the Knoll Mini at zero pose, in mm, straight from the upstream
Microduck MJCF (robot_walk.xml). Positions are scaled by spec.S, then spec.STRETCH offsets are
applied. Printed parts are loaded from parts/current/<mesh>.stl (already in mm and already scaled).
Every XL330 is replaced by the SCS0009 envelope; the mouth servo is dropped.
Import it: `from assembly import build; items = build()` -> list of Item."""
import sys, xml.etree.ElementTree as ET
from dataclasses import dataclass
import numpy as np, trimesh
from trimesh.transformations import quaternion_matrix, translation_matrix, rotation_matrix
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import spec, scs0009

@dataclass
class Item:
    body: str          # MJCF body name
    mesh: str          # mesh name (e.g. 'trunk_base', 'scs0009:left_hip_yaw')
    T: np.ndarray      # 4x4 transform mesh-local -> world (mm)
    mesh_obj: trimesh.Trimesh  # mesh already transformed to world
    kind: str          # 'printed' | 'servo' | 'other'

def _T(e, s):
    p = np.array([float(x) for x in (e.get("pos") or "0 0 0").split()]) * 1000.0 * s
    q = [float(x) for x in (e.get("quat") or "1 0 0 0").split()]
    return translation_matrix(p) @ quaternion_matrix(q)

def joints_world(s=None, stretch=None):
    """dict joint -> (anchor_mm, axis_world, body)"""
    return _walk(s, stretch, want_meshes=False)[1]

def _stretch_map(stretch):
    return {d["body"]: np.array(d["delta_mm"], float) for d in (spec.STRETCH if stretch is None else stretch)}

BODY_POSE = {}   # body name -> 4x4 world pose (mm) from the last _walk()

def _walk(s=None, stretch=None, want_meshes=True, part_dir=None, roll_override=None, q=None):
    q = q or {}
    s = spec.S if s is None else s
    smap = _stretch_map(stretch)
    root = ET.parse(spec.UPSTREAM_DIR / "robot_walk.xml").getroot()
    part_dir = spec.WORK_DIR if part_dir is None else part_dir
    items, J = [], {}
    cache = {}
    def load(name):
        if name not in cache:
            if name in spec.NON_PRINTED:
                m = trimesh.load(spec.UPSTREAM_DIR / "assets" / f"{name}.stl", force="mesh")
                m.apply_scale(1000.0 * s)
            else:
                m = trimesh.load(part_dir / f"{name}.stl", force="mesh")
            cache[name] = m
        return cache[name]
    def walk(b, M):
        L = _T(b, s)
        name = b.get("name")
        if name in smap:   # world-axis delta applied at this body
            M = translation_matrix(smap[name]) @ M @ L
        else:
            M = M @ L
        for j in b.findall("joint"):   # every Microduck hinge sits at its body origin with local axis Z
            if j.get("type") == "hinge" and j.get("name") in q:
                M = M @ rotation_matrix(np.radians(q[j.get("name")]), [0, 0, 1])
        BODY_POSE[name] = M.copy()
        for j in b.findall("joint"):
            if j.get("type") == "hinge":
                J[j.get("name")] = (M[:3, 3].copy(), M[:3, :3] @ np.array([0, 0, 1.0]), name)
        if want_meshes:
            for g in b.findall("geom"):
                if g.get("type") != "mesh" or g.get("class") in ("self_collision_only", "collision"):
                    continue
                mn = g.get("mesh")
                G = M @ _T(g, s)
                if mn == "xl330":
                    jn = _servo_joint(G, J_all)
                    if jn is None:      # mouth servo -> dropped
                        continue
                    roll = spec.SERVO_ROLL_DEG.get(jn, 0) if roll_override is None else roll_override.get(jn, 0)
                    G = G @ rotation_matrix(np.radians(roll), [1, 0, 0])   # spin about own shaft (local X)
                    m = scs0009.envelope_mesh().copy(); m.apply_transform(G)
                    items.append(Item(name, f"scs0009:{jn}", G, m, "servo"))
                    continue
                if mn in ("pcb__raspberry_pi_zero_2_w", "elec_rpi_robot_hat_pcb", "np_f970", "speaker", "lens"):
                    continue        # old electronics, replaced (see SPEC.md section 7)
                if mn == "seeed_bearing__configuration_default" and name == spec.HEAD_BODY:
                    continue        # session 4: roll idler is a plain printed bushing (SPEC 5.4)
                if mn in spec.REMOVED_PARTS:
                    continue
                if spec.HEAD_MODE == "bdx" and mn in spec.HEAD_REPLACE_PARTS:
                    continue        # old Microduck head shells, replaced by the BDX head
                m = load(mn).copy(); m.apply_transform(G)
                items.append(Item(name, mn, G, m, "other" if mn in spec.NON_PRINTED else "printed"))
        if want_meshes:   # parts authored directly in this body's frame (BDX head, electronics)
            extra = [(n, None) for n in spec.BDX_HEAD_PARTS if spec.HEAD_MODE == "bdx" and name == spec.HEAD_BODY]
            extra += [(e[1], e) for e in spec.ELECTRONICS if e[0] == name]
            extra += [(n, None) for b_, n in spec.EXTRA_PARTS if b_ == name]
            for n, e in extra:
                f = part_dir / f"{n}.stl"
                if not f.exists():
                    continue
                m = trimesh.load(f, force="mesh").copy(); m.apply_transform(M)
                items.append(Item(name, n, M.copy(), m, "other" if e else "printed"))
        for c in b.findall("body"):
            walk(c, M)
    J_all = {}
    if want_meshes:
        J_all = _walk(s, stretch, want_meshes=False, q=q)[1]
    for b in root.find("worldbody").findall("body"):
        walk(b, np.eye(4))
    return items, J

def _servo_joint(G, J):
    """Servo raw frame: shaft = local X axis through origin. Return the joint whose axis is that line."""
    Gi = np.linalg.inv(G)
    best = None
    for jn, (p, a, _) in J.items():
        pl = (Gi @ np.r_[p, 1])[:3]; al = Gi[:3, :3] @ a
        if abs(abs(al[0]) - 1) < 1e-3 and np.hypot(pl[1], pl[2]) < 0.5:
            d = abs(pl[0])
            if best is None or d < best[0]:
                best = (d, jn)
    return None if best is None else best[1]

def build(s=None, stretch=None, part_dir=None, roll_override=None, q=None):
    """q = {joint_name: degrees}; missing joints are 0."""
    return _walk(s, stretch, True, part_dir, roll_override, q)[0]

if __name__ == "__main__":
    items = build()
    allm = trimesh.util.concatenate([i.mesh_obj for i in items])
    b = allm.bounds
    print(f"S={spec.S} items={len(items)} servos={sum(i.kind=='servo' for i in items)}")
    print("bbox min", b[0].round(1), "max", b[1].round(1), "height_mm", round(b[1][2] - b[0][2], 1))
    for i in items:
        if i.kind == "servo":
            print("SERVO", i.mesh, "in", i.body, "centre", i.mesh_obj.bounds.mean(0).round(1))
