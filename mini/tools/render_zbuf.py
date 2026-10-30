"""True z-buffer shaded renderer (numpy, orthographic, per-face lambert, back-face culling).
Unlike render_solid.py (matplotlib painter's sort -> see-through shells, stray diagonal
lines, wrong occlusion on >50k-face parts), this rasterises properly.

Usage:
  python tools/render_zbuf.py file1.stl [file2.stl ...] --out DIR [--views front,back,...]
  python tools/render_zbuf.py --assembly --bodies jaw_soft,neck,neck_pitch,yaw_roll_motion --out DIR
  python tools/render_zbuf.py --assembly --bodies ... --section "y<=0" --views front,iso --out DIR

Frames: head part STLs are authored in the jaw_soft frame: x=up(lx), y=left(ly), z=back(lz).
Use --frame head (default for STL lists) or --frame world (assembly default: x fwd,y left,z up).
--section "a<=v" keeps the a<=v half (axis in the render frame); section surfaces are capped.
"""
import sys, argparse, pathlib
import numpy as np, trimesh
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("stls", nargs="*")
ap.add_argument("--out", required=True)
ap.add_argument("--views", default="front,back,left,right,top,bottom,iso,iso2")
ap.add_argument("--assembly", action="store_true")
ap.add_argument("--bodies", default="")          # comma list; empty = whole robot
ap.add_argument("--frame", default="", choices=["", "head", "world"])
ap.add_argument("--section", default="")        # e.g. "y<=0", "x>=-10"
ap.add_argument("--size", type=int, default=800)
a = ap.parse_args()

sys.path.insert(0, str(pathlib.Path(__file__).parent))

PAL = {"top": (0.80, 0.72, 0.55), "bottom": (0.72, 0.66, 0.52), "ant": (0.35, 0.35, 0.38),
       "eye": (0.20, 0.45, 0.80), "servo": (0.55, 0.12, 0.12), "elec": (0.25, 0.50, 0.25),
       "plate": (0.76, 0.70, 0.55), "lens": (0.20, 0.45, 0.80), "other": (0.60, 0.60, 0.62)}

def color_for(name, kind=""):
    n = name.lower()
    if kind == "servo": return PAL["servo"]
    if "ant" in n: return PAL["ant"]
    if "lens" in n or "eye" in n: return PAL["eye"]
    if "plate" in n: return PAL["plate"]
    if "elec" in n: return PAL["elec"]
    if "top_" in n: return PAL["top"]
    if "bottom_" in n: return PAL["bottom"]
    return PAL["other"]

meshes = []   # (name, mesh, rgb)
if a.assembly:
    import assembly, spec
    items = assembly.build()
    keep = set(a.bodies.split(",")) if a.bodies else None
    for it in items:
        if keep is not None and it.body not in keep: continue
        meshes.append((it.mesh, it.mesh_obj, color_for(it.mesh, it.kind)))
    frame = a.frame or "world"
else:
    for f in a.stls:
        m = trimesh.load(f, force="mesh")
        meshes.append((pathlib.Path(f).stem, m, color_for(pathlib.Path(f).stem)))
    frame = a.frame or "head"
if not meshes: sys.exit("nothing to render")

# ---- optional section cut -------------------------------------------------
if a.section:
    import re
    mm = re.match(r"([xyz])\s*(<=|>=|<|>)\s*(-?[\d.]+)", a.section)
    if not mm: sys.exit("bad --section, use e.g. 'y<=0'")
    ax = "xyz".index(mm.group(1)); val = float(mm.group(3))
    n = np.zeros(3); n[ax] = -1.0 if "<" in mm.group(2) else 1.0   # keep <v or >v side
    o = np.zeros(3); o[ax] = val
    cut = []
    for name, m, c in meshes:
        try:
            s = m.slice_plane(o, n, cap=True)
            cut.append((name + "|cut", s, c))
        except Exception as e:
            print("section skip", name, e)
    meshes = cut

# ---- views -----------------------------------------------------------------
V_HEAD = {  # jaw_soft frame: x up, z back (-z = face direction), y left
    "front": ((0, 0, -1), (1, 0, 0)), "back": ((0, 0, 1), (1, 0, 0)),
    "left": ((0, 1, 0), (1, 0, 0)), "right": ((0, -1, 0), (1, 0, 0)),
    "top": ((1, 0, 0), (0, 0, 1)), "bottom": ((-1, 0, 0), (0, 0, -1)),
    "iso": ((0.55, -0.60, -0.58), (1, 0, 0)), "iso2": ((0.55, 0.60, 0.58), (1, 0, 0)),
    "iso3": ((-0.55, -0.60, -0.58), (1, 0, 0)),
}
V_WORLD = {  # world: x fwd (face), y left, z up
    "front": ((1, 0, 0), (0, 0, 1)), "back": ((-1, 0, 0), (0, 0, 1)),
    "left": ((0, 1, 0), (0, 0, 1)), "right": ((0, -1, 0), (0, 0, 1)),
    "top": ((0, 0, 1), (1, 0, 0)), "bottom": ((0, 0, -1), (-1, 0, 0)),
    "iso": ((0.80, -0.55, 0.55), (0, 0, 1)), "iso2": ((-0.80, 0.55, 0.55), (0, 0, 1)),
    "iso3": ((0.80, 0.55, 0.55), (0, 0, 1)),
}
VIEWS = V_HEAD if frame == "head" else V_WORLD

V = np.vstack([m.vertices for _, m, _ in meshes])
ctr = (V.max(0) + V.min(0)) / 2
R = np.abs(V - ctr).max() * 1.06
L = np.array([0.4, 0.5, 0.8]); L /= np.linalg.norm(L)

def render(dirv, up, S, name):
    dn = np.array(dirv, float); dn /= np.linalg.norm(dn)
    up = np.array(up, float); r = np.cross(up, dn); r /= np.linalg.norm(r)
    u = np.cross(dn, r); u /= np.linalg.norm(u)
    img = np.ones((S, S, 3)); zb = np.full((S, S), -1e9)
    for mn, m, col in meshes:
        P = m.vertices - ctr
        X = P @ r; Y = P @ u; Z = P @ dn
        px = (X / R * 0.5 + 0.5) * (S - 1); py = (1 - (Y / R * 0.5 + 0.5)) * (S - 1)
        fn = m.face_normals
        vis = fn @ dn > 0
        for i in np.nonzero(vis)[0]:
            t = m.faces[i]
            x = px[t]; y = py[t]; z = Z[t]
            x0 = int(max(0, np.floor(x.min()))); x1 = int(min(S - 1, np.ceil(x.max())))
            y0 = int(max(0, np.floor(y.min()))); y1 = int(min(S - 1, np.ceil(y.max())))
            if x1 < x0 or y1 < y0: continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
            d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(d) < 1e-12: continue
            al = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
            be = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
            g = 1 - al - be
            ins = (al >= -1e-6) & (be >= -1e-6) & (g >= -1e-6)
            zz = al * z[0] + be * z[1] + g * z[2]
            sub = zb[y0:y1 + 1, x0:x1 + 1]; ok = ins & (zz > sub)
            sub[ok] = zz[ok]
            sh = 0.25 + 0.75 * max(0, fn[i] @ L) + 0.15 * max(0, fn[i] @ dn)
            img[y0:y1 + 1, x0:x1 + 1][ok] = np.clip(np.array(col) * sh, 0, 1)
    Image.fromarray((img * 255).astype("uint8")).save(name)

out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
for vn in a.views.split(","):
    if vn not in VIEWS: print("skip unknown view", vn); continue
    d, u = VIEWS[vn]
    render(d, u, a.size, str(out / f"{vn}.png"))
    print("wrote", out / f"{vn}.png")
