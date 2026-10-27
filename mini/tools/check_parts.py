"""Printability check for every STL in parts/current. Exit 0 = all PASS.
P1 watertight + positive volume   P2 fits a 220x220x250 mm bed (any orientation of the bbox)
P3 extents look like millimetres (largest side between 3 and 200 mm)
P4 thin walls: 10th-percentile local wall thickness (ray test, 1500 samples) >= 1.2 mm for
   structural parts, >= 0.9 mm for cosmetic parts (spec.COSMETIC_PARTS). Fix thin plates with
   tools/thicken_plate.py or by adding a cradle; never by scaling the whole part.
Parts listed in spec.NON_PRINTED are ignored. Use --only name1,name2 to test a subset."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh, spec
only = None
if "--only" in sys.argv: only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
ok = True
for f in sorted(spec.WORK_DIR.glob("*.stl")):
    n = f.stem
    if n in spec.NON_PRINTED or n.startswith("elec_") or n.startswith("hardware_") or (only and n not in only): continue
    m = trimesh.load(f, force="mesh")
    p1 = m.is_watertight and m.volume > 0
    e = np.sort(m.extents)[::-1]
    p2 = e[0] <= 250 and e[1] <= 220 and e[2] <= 220
    p3 = 3 <= e[0] <= 200
    pts, fi = trimesh.sample.sample_surface(m, 1500, seed=0)
    nrm = m.face_normals[fi]
    loc, ri, _ = m.ray.intersects_location(pts - nrm * 0.01, -nrm, multiple_hits=False)
    th = np.linalg.norm(loc - pts[ri], axis=1) if len(ri) else np.array([0.0])
    t3 = float(np.percentile(th, 10)); p4 = t3 >= (0.9 if n in spec.COSMETIC_PARTS else 1.2)
    good = p1 and p2 and p3 and p4; ok &= good
    print(f"{'PASS' if good else 'FAIL'} {n:26s} watertight={m.is_watertight} ext={m.extents.round(1)} wall_p10={t3:.2f}mm"
          + ("" if p4 else "  <-- thin") + ("" if p3 else "  <-- units?"))
print("OVERALL:", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
