"""Session 0: copy the 30 tianjin66 STLs (mm, Microduck per-part frames), scale by spec.S about
each part's own origin (= scaling the whole robot about the world origin, because the MJCF
geom positions are scaled by the same S), and write parts/scaled/<name>.stl and
parts/current/<name>.stl (current is only written if it does not exist yet; use --force to reset)."""
import sys, shutil, hashlib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import spec, trimesh
force = "--force" in sys.argv
spec.SCALED_DIR.mkdir(parents=True, exist_ok=True); spec.WORK_DIR.mkdir(parents=True, exist_ok=True)
files = sorted(spec.STL_REPO_DIR.glob("*.stl"))
assert len(files) == 30, f"expected 30 STLs in {spec.STL_REPO_DIR}, found {len(files)}"
for f in files:
    name = f.name.split("__")[0]
    m = trimesh.load(f, force="mesh")
    up = trimesh.load(spec.UPSTREAM_DIR / "assets" / f"{name}.stl", force="mesh"); up.apply_scale(1000)
    same = abs(m.volume - up.volume) / up.volume < 0.01 and (abs(m.bounds - up.bounds) < 0.05).all()
    m.apply_scale(spec.S)
    out = spec.SCALED_DIR / f"{name}.stl"; m.export(out)
    cur = spec.WORK_DIR / f"{name}.stl"
    if force or not cur.exists():
        shutil.copy(out, cur)
    print(f"{name:26s} matches_upstream={same} watertight={m.is_watertight} extents_mm={m.extents.round(1)} vol_cm3={m.volume/1000:.2f}")
print("DONE scaled", len(files), "parts by S =", spec.S)
