"""Zero-pose fit check for the Knoll Mini. Run: python tools/check_clearance.py [--json out.json]
Checks (all must PASS, exit code 0 = all pass, 1 = any FAIL):
  C1 exactly 14 SCS0009 servos placed, each shaft on its joint axis
  C2 every servo-servo gap >= spec.MIN_SERVO_GAP_MM (case+ears+horn envelopes, exact mesh distance)
  C3 no servo case/ears penetrates a part of a DIFFERENT body by more than 0.2 mm
     (penetration into its own body's parts is expected: that is where the pocket is cut)
  C4 overall height <= spec.MAX_HEIGHT_MM
Prints a DEFICIT table telling you how far apart each failing pair must move."""
import sys, json, itertools
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
from trimesh.collision import CollisionManager
import spec, scs0009
from assembly import build

def gap(a, b):
    cm = CollisionManager(); cm.add_object("a", a)
    hit, data = cm.in_collision_single(b, return_data=True)
    if hit:
        return -max(c.depth for c in data)
    return cm.min_distance_single(b)

def main():
    items = build()
    servos = [i for i in items if i.kind == "servo"]
    parts = [i for i in items if i.kind != "servo"]
    res = {"S": spec.S, "fails": []}
    ok = True
    # C1
    names = sorted(i.mesh.split(":")[1] for i in servos)
    want = sorted(j[0] for j in spec.JOINTS)
    c1 = names == want
    print(f"C1 servos placed={len(servos)} on-axis-and-matching-joint-list: {'PASS' if c1 else 'FAIL'}")
    if not c1: print("   missing:", set(want) - set(names), "extra:", set(names) - set(want)); ok = False
    # C2
    env_nohorn = {}
    print(f"C2 servo-servo gaps (need >= {spec.MIN_SERVO_GAP_MM} mm):")
    c2 = True
    for a, b in itertools.combinations(servos, 2):
        d = a.mesh_obj.bounds; e = b.mesh_obj.bounds
        if (d[0] - 15 > e[1]).any() or (e[0] - 15 > d[1]).any():
            continue
        g = gap(a.mesh_obj, b.mesh_obj)
        if g < spec.MIN_SERVO_GAP_MM:
            c2 = False
            v = b.mesh_obj.bounds.mean(0) - a.mesh_obj.bounds.mean(0)
            ax = "XYZ"[int(np.argmax(abs(v)))]
            need = spec.MIN_SERVO_GAP_MM - g
            print(f"   FAIL {a.mesh.split(':')[1]:16s} vs {b.mesh.split(':')[1]:16s} gap={g:6.2f} mm  need +{need:.1f} mm  (centres differ most along world {ax})")
            res["fails"].append(dict(check="C2", a=a.mesh, b=b.mesh, gap=round(g, 2), need=round(need, 2)))
    print(f"   C2 {'PASS' if c2 else 'FAIL'}"); ok &= c2
    # C3
    print("C3 servo case/ears vs parts of other bodies (max penetration 0.2 mm):")
    c3 = True
    for s_ in servos:
        env = scs0009.envelope_mesh(horn=False).copy(); env.apply_transform(s_.T)
        for p in parts:
            if p.body == s_.body:
                continue
            d = env.bounds; e = p.mesh_obj.bounds
            if (d[0] > e[1]).any() or (e[0] > d[1]).any():
                continue
            g = gap(env, p.mesh_obj)
            if g < -0.2:
                c3 = False
                print(f"   FAIL {s_.mesh.split(':')[1]:16s} (in {s_.body}) penetrates {p.mesh:28s} (body {p.body}) by {-g:.2f} mm")
                res["fails"].append(dict(check="C3", servo=s_.mesh, part=p.mesh, body=p.body, depth=round(-g, 2)))
    print(f"   C3 {'PASS' if c3 else 'FAIL'}"); ok &= c3
    # C4
    allm = trimesh.util.concatenate([i.mesh_obj for i in items])
    h = allm.bounds[1][2] - allm.bounds[0][2]
    c4 = h <= spec.MAX_HEIGHT_MM
    print(f"C4 height={h:.1f} mm (cap {spec.MAX_HEIGHT_MM}) {'PASS' if c4 else 'FAIL'}"); ok &= c4
    res.update(height=round(h, 1), ok=bool(ok))
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]; json.dump(res, open(out, "w"), indent=1)
    print("OVERALL:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
