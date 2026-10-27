"""Write model/knoll_mini.xml + model/scene_knoll_mini.xml from the upstream Microduck MJCF:
positions x S, STRETCH applied, every XL330 -> SCS0009 (spun by SERVO_ROLL_DEG), mouth servo and old
electronics removed, joint ranges clipped to +-150 deg, actuator forcerange = SCS0009 stall torque,
body masses recomputed from the printed STLs (PETG) + servos + spec.ELECTRONICS.
Run: python tools/build_mjcf.py   then   python -c "import mujoco;mujoco.MjModel.from_xml_path('model/scene_knoll_mini.xml')" """
import sys, os, copy, xml.etree.ElementTree as ET
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
from trimesh.transformations import quaternion_matrix, quaternion_from_matrix, rotation_matrix
import spec, scs0009
from assembly import _servo_joint, joints_world, build

S = spec.S
DROP = {"pcb__raspberry_pi_zero_2_w", "elec_rpi_robot_hat_pcb", "np_f970", "speaker", "lens"} | set(spec.REMOVED_PARTS)
if spec.HEAD_MODE == "bdx":
    DROP |= set(spec.HEAD_REPLACE_PARTS)
tree = ET.parse(spec.UPSTREAM_DIR / "robot_walk.xml"); root = tree.getroot()
spec.MODEL_DIR.mkdir(parents=True, exist_ok=True)
(spec.ROOT / "parts" / "lib").mkdir(parents=True, exist_ok=True)
scs0009.envelope_mesh().export(spec.ROOT / "parts" / "lib" / "scs0009_envelope.stl")
rel = lambda p: os.path.relpath(p, spec.MODEL_DIR)

def T(e, s=S):
    p = np.array([float(x) for x in (e.get("pos") or "0 0 0").split()]) * 1000 * s
    q = [float(x) for x in (e.get("quat") or "1 0 0 0").split()]
    M = quaternion_matrix(q); M[:3, 3] = p; return M
fmt = lambda v: " ".join(f"{x:.6g}" for x in v)
J = joints_world()
smap = {d["body"]: np.array(d["delta_mm"], float) for d in spec.STRETCH}
# per-body mass bookkeeping
items = build()
mass_g = {}
for it in items:
    if it.kind == "printed":
        mass_g[it.body] = mass_g.get(it.body, 0) + it.mesh_obj.volume / 1000 * spec.PETG_DENSITY_G_CM3 * spec.PRINT_FILL_FACTOR
    elif it.kind == "servo":
        mass_g[it.body] = mass_g.get(it.body, 0) + spec.SCS["mass_g"]
    elif it.mesh.startswith("seeed_bearing"):
        mass_g[it.body] = mass_g.get(it.body, 0) + 2.0
for e in spec.ELECTRONICS:
    mass_g[e[0]] = mass_g.get(e[0], 0) + e[2]

def walk(b, Mworld_parent):
    name = b.get("name")
    L = T(b)
    if name in smap:   # add world delta expressed in parent frame
        L[:3, 3] += Mworld_parent[:3, :3].T @ smap[name]
    b.set("pos", fmt(L[:3, 3] / 1000))   # every body pos: scaled (+ stretch), metres
    M = Mworld_parent @ L
    for e in list(b):
        tag = e.tag
        if tag in ("geom", "site", "camera", "inertial") and e.get("pos") is not None:
            e.set("pos", fmt(np.array([float(x) for x in e.get("pos").split()]) * S))
        if tag == "geom" and e.get("mesh"):
            mn = e.get("mesh")
            if mn in DROP:
                b.remove(e); continue
            if mn == "xl330":
                G = M @ _geom_T(e)   # pos already scaled above
                jn = _servo_joint(G, J)
                if jn is None:
                    b.remove(e); continue      # mouth servo
                r = spec.SERVO_ROLL_DEG.get(jn, 0)
                Q = quaternion_matrix([float(x) for x in (e.get("quat") or "1 0 0 0").split()]) @ rotation_matrix(np.radians(r), [1, 0, 0])
                e.set("quat", fmt(quaternion_from_matrix(Q))); e.set("mesh", "scs0009")
                e.set("name", f"servo_{jn}")
        if tag == "inertial":
            m_old = float(e.get("mass")); m_new = mass_g.get(name, m_old * 1000 * S**3) / 1000
            e.set("mass", f"{m_new:.6g}")
            fi = np.array([float(x) for x in e.get("fullinertia").split()]) * S**2 * (m_new / m_old)
            e.set("fullinertia", fmt(fi))
        if tag == "joint" and e.get("range"):
            lo, hi = [float(x) for x in e.get("range").split()]
            lim = np.radians(150)
            e.set("range", f"{max(lo, -lim):.6g} {min(hi, lim):.6g}")
    if spec.HEAD_MODE == "bdx" and name == spec.HEAD_BODY:
        for n in spec.BDX_HEAD_PARTS:
            if (spec.WORK_DIR / f"{n}.stl").exists():
                ET.SubElement(b, "geom", {"type": "mesh", "class": "visual", "mesh": n, "rgba": "0.9 0.9 0.88 1"})
    for b_, n in spec.EXTRA_PARTS:
        if b_ == name:
            ET.SubElement(b, "geom", {"type": "mesh", "class": "visual", "mesh": n, "rgba": "0.8 0.5 0.2 1"})
    for e in spec.ELECTRONICS:
        if e[0] == name and (spec.WORK_DIR / f"{e[1]}.stl").exists():
            ET.SubElement(b, "geom", {"type": "mesh", "class": "visual", "mesh": e[1], "rgba": "0.1 0.4 0.1 1"})
    for c in b.findall("body"):
        walk(c, M)

def _geom_T(e):
    # pos was already multiplied by S at this point
    p = np.array([float(x) for x in (e.get("pos") or "0 0 0").split()]) * 1000
    q = [float(x) for x in (e.get("quat") or "1 0 0 0").split()]
    Mx = quaternion_matrix(q); Mx[:3, 3] = p; return Mx

wb = root.find("worldbody")
for b in wb.findall("body"):
    walk(b, np.eye(4))
# assets
comp = root.find("compiler"); comp.set("meshdir", rel(spec.ROOT / "parts"))
asset = root.find("asset")
for m in list(asset.findall("mesh")):
    stem = os.path.splitext(m.get("file"))[0]
    m.set("name", stem)
    if stem in DROP or stem == "xl330":
        asset.remove(m); continue
    if stem in spec.NON_PRINTED:
        m.set("file", os.path.relpath(spec.UPSTREAM_DIR / "assets" / f"{stem}.stl", spec.ROOT / "parts")); m.set("scale", fmt([S] * 3))
    else:
        m.set("file", f"current/{stem}.stl"); m.set("scale", "0.001 0.001 0.001")
ET.SubElement(asset, "mesh", {"name": "scs0009", "file": "lib/scs0009_envelope.stl", "scale": "0.001 0.001 0.001"})
extra = (spec.BDX_HEAD_PARTS if spec.HEAD_MODE == "bdx" else []) + [e[1] for e in spec.ELECTRONICS] + [n for _, n in spec.EXTRA_PARTS]
for n in extra:
    if (spec.WORK_DIR / f"{n}.stl").exists():
        ET.SubElement(asset, "mesh", {"name": n, "file": f"current/{n}.stl", "scale": "0.001 0.001 0.001"})
for d in root.iter("default"):
    for pz in d.findall("position"):
        if pz.get("forcerange"):
            pz.set("forcerange", f"-{spec.SCS['stall_Nm']} {spec.SCS['stall_Nm']}")
# trunk start height so the soles touch the floor
allm = trimesh.util.concatenate([i.mesh_obj for i in items])
z0 = 0.12 * S - allm.bounds[0][2] / 1000 + 0.0005
wb.find("body").set("pos", f"0 0 {z0:.5f}")
root.set("model", "knoll_mini")
ET.indent(tree); tree.write(spec.MODEL_DIR / "knoll_mini.xml")
# scene
sc = ET.parse(spec.UPSTREAM_DIR / "scene_walk.xml").getroot()
sc.find("include").set("file", "knoll_mini.xml")
jnames = [j.get("name") for j in root.iter("joint") if j.get("name")]   # qpos order after the freejoint
for k in sc.iter("key"):
    q = k.get("qpos").split()
    qdeg = {n: np.degrees(float(v)) for n, v in zip(jnames, q[7:])}
    lo = trimesh.util.concatenate([i.mesh_obj for i in build(q=qdeg)]).bounds[0][2]
    q[2] = f"{0.12 * S - lo / 1000 + 0.0003:.5f}"   # soles 0.3 mm above the floor in this pose
    k.set("qpos", " ".join(q))
ET.ElementTree(sc).write(spec.MODEL_DIR / "scene_knoll_mini.xml")
print("wrote", spec.MODEL_DIR / "knoll_mini.xml", "and scene_knoll_mini.xml; trunk z0 =", round(z0, 4), "m")
print("body masses g:", {k: round(v, 1) for k, v in mass_g.items()}, "total", round(sum(mass_g.values()), 1))
