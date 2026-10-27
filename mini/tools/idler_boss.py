"""Idler support for a yoke joint (the SCS0009 has no rear idler boss, the XL330 did).
Adds a coaxial pin (6700ZZ inner race, Ø10 x --len mm [U]) to the HOLDER part, starting at the servo case
bottom, and cuts a Ø15.1 x 4 mm bearing seat (6700ZZ OD 15 press fit [U]) + Ø11 through-clearance into the
YOKE part, both on the shaft axis. Run AFTER the yoke idler arm has been stretched clear of the case.
Usage: python tools/idler_boss.py --servo left_ankle --holder leg --yoke ankle_left [--len 6] [--dry-run]"""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh, spec, scs0009
from trimesh.transformations import rotation_matrix
from assembly import build
ap = argparse.ArgumentParser()
for k in ("--servo", "--holder", "--yoke"): ap.add_argument(k, required=True)
ap.add_argument("--len", type=float, default=6.0); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
items = build()
sv = [i for i in items if i.mesh == f"scs0009:{a.servo}"][0]
ho = [i for i in items if i.mesh == a.holder and i.body == sv.body][0]
yo = [i for i in items if i.mesh == a.yoke][0]
case_bot = scs0009.frame_numbers()["case_bot"]   # servo-local x of the case bottom
def cyl(r, x0, x1):   # cylinder along servo-local X from x0 to x1
    c = trimesh.creation.cylinder(radius=r, height=x1 - x0, sections=64)
    c.apply_transform(rotation_matrix(np.pi / 2, [0, 1, 0])); c.apply_translation([(x0 + x1) / 2, 0, 0]); return c
pin = cyl(4.95, case_bot - 1.0, case_bot + a.len)      # overlaps 1 mm into the cradle floor
seat = cyl(7.55, case_bot + 0.6, case_bot + 0.6 + 4.0)
thru = cyl(5.5, case_bot + 0.3, case_bot + a.len + 30)
out = {}
for it, add, sub in ((ho, pin, None), (yo, None, [seat, thru])):
    p = spec.WORK_DIR / f"{it.mesh}.stl"; m = trimesh.load(p, force="mesh"); v0 = m.volume
    L = np.linalg.inv(it.T) @ sv.T
    if add is not None:
        g = add.copy(); g.apply_transform(L); m = trimesh.boolean.union([m, g], engine="manifold")
    if sub:
        for s in sub:
            g = s.copy(); g.apply_transform(L); m = trimesh.boolean.difference([m, g], engine="manifold")
    nb = len(m.split(only_watertight=False))
    print(f"{it.mesh}: volume {v0/1000:.2f} -> {m.volume/1000:.2f} cm3 watertight={m.is_watertight} bodies={nb}")
    assert m.is_watertight
    if nb > 1: print("WARNING: disconnected pieces (the pin does not touch the cradle, or the yoke arm is not on the axis) - NOT saved"); sys.exit(1)
    out[p] = m
if not a.dry_run:
    for p, m in out.items(): m.export(p); print("wrote", p)
