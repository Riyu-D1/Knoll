"""Replace small upstream parts of ONE body by a single new bracket authored in that body's frame.
Typical use (neck: two tiny XL330 plates -> one SCS0009 bracket):
  python tools/merge_body_frame.py --body neck --out neck_frame --parts neck --cradle-joints neck_pitch head_pitch [--hull] [--dry-run]
Result = union( every instance of --parts in that body, a 2 mm cradle per --cradle-joints servo )
  [--hull: plus the convex hull of all cradles, to tie them together]  minus the SCS0009 cutters of those servos.
Writes parts/current/<out>.stl (body-frame mm). Afterwards YOU edit spec.py:
  EXTRA_PARTS += [(body, out)];  REMOVED_PARTS += <parts>;  then `git mv` the replaced STLs to parts/attic/."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh, spec, scs0009, assembly
ap = argparse.ArgumentParser()
ap.add_argument("--body", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--parts", nargs="*", default=[]); ap.add_argument("--cradle-joints", nargs="+", required=True)
ap.add_argument("--hull", action="store_true"); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
items = assembly.build()
inv = np.linalg.inv(assembly.BODY_POSE[a.body])
geo, cradles, cutters = [], [], []
for it in items:
    if it.body == a.body and it.mesh in a.parts:
        m = it.mesh_obj.copy(); m.apply_transform(inv); geo.append(m)
for jn in a.cradle_joints:
    sv = [i for i in items if i.mesh == f"scs0009:{jn}"][0]
    assert sv.body == a.body, f"servo {jn} is in body {sv.body}, not {a.body}"
    L = inv @ sv.T
    c = scs0009.cradle_mesh().copy(); c.apply_transform(L); cradles.append(c)
    k = scs0009.cutter_mesh().copy(); k.apply_transform(L); cutters.append(k)
parts = geo + cradles
if a.hull:
    parts.append(trimesh.util.concatenate(cradles).convex_hull)
if a.hull and len(geo) and len(trimesh.boolean.union(parts, engine="manifold").split(only_watertight=False)) > 1:
    parts.append(trimesh.util.concatenate(geo + cradles).convex_hull)   # plates still loose: hull everything
m = trimesh.boolean.union(parts, engine="manifold")
for k in cutters:
    m = trimesh.boolean.difference([m, k], engine="manifold")
nb = len(m.split(only_watertight=False))
print(f"{a.out}: volume {m.volume/1000:.2f} cm3 (~{m.volume/1000*spec.PETG_DENSITY_G_CM3*spec.PRINT_FILL_FACTOR:.1f} g) extents {m.extents.round(1)} watertight={m.is_watertight} bodies={nb}")
assert m.is_watertight
if nb > 1: print("WARNING: disconnected pieces - re-run with --hull. NOT saved."); sys.exit(1)
if not a.dry_run:
    m.export(spec.WORK_DIR / f"{a.out}.stl"); print("wrote", spec.WORK_DIR / f"{a.out}.stl")
