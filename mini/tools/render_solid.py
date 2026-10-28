"""Opaque shaded render of the Knoll Mini assembly to PNGs (no GPU/display needed).
Run: python tools/render_solid.py [--q joint=deg ...] [--out renders/solid] [--views front,side,three_quarter,head]
Shading: per-face lambert (key light + fill + ambient) on trimesh Poly3DCollection triangles,
painter-sorted by depth so the assembly reads as solid. Servos dark red, head parts warm grey.
Views are camera presets; 'head' is a close-up on the jaw_soft-body bounding box."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import spec
from assembly import build

ap = argparse.ArgumentParser()
ap.add_argument("--q", nargs="*", default=[])
ap.add_argument("--out", default=str(spec.ROOT / "renders" / "solid"))
ap.add_argument("--views", default="front,side,three_quarter,head")
a = ap.parse_args()
q = {k: float(v) for k, v in (s.split("=") for s in a.q)}
items = build(q=q)
out = __import__("pathlib").Path(a.out); out.mkdir(parents=True, exist_ok=True)

KEY = np.array([0.45, -0.55, 0.70]); KEY /= np.linalg.norm(KEY)     # main light
FILL = np.array([-0.6, 0.35, 0.35]); FILL /= np.linalg.norm(FILL)  # weak fill

def base_color(it):
    if it.kind == "servo":
        return np.array([0.55, 0.12, 0.12])
    if it.body == "jaw_soft":
        return np.array([0.86, 0.78, 0.62])      # head parts: warm tan
    if it.kind == "other":
        return np.array([0.35, 0.55, 0.35])      # bearings/hardware: green
    return np.array([0.62, 0.65, 0.70])          # body: cool grey

def shade(mesh, base):
    n = mesh.face_normals.astype(float)
    lam = np.clip(n @ KEY, 0, 1) * 0.75 + np.clip(n @ FILL, 0, 1) * 0.25 + 0.18
    return np.clip(base[None, :] * lam[:, None], 0, 1)

VIEWS = {  # name: (elev, azim, zoom_target, zoom_radius or None)
    "front":         (8, 180, "all", None),
    "side":          (6, 90, "all", None),
    "three_quarter": (18, -142, "all", None),
    "head":          (10, 168, "jaw_soft", None),
}
allv = np.vstack([i.mesh_obj.vertices for i in items])
c_all = (allv.max(0) + allv.min(0)) / 2
r_all = (allv.max(0) - allv.min(0)).max() / 2
head_v = np.vstack([i.mesh_obj.vertices for i in items if i.body == "jaw_soft"])
c_h = (head_v.max(0) + head_v.min(0)) / 2
r_h = (head_v.max(0) - head_v.min(0)).max() / 2 * 1.35

for name in a.views.split(","):
    el, az, target, _ = VIEWS[name]
    c, r = (c_h, r_h) if target == "jaw_soft" else (c_all, r_all)
    fig = plt.figure(figsize=(7.5, 8.5))
    ax = fig.add_subplot(111, projection="3d")
    tris, cols = [], []
    for it in items:
        tri = it.mesh_obj.triangles
        if len(tri) > 40000:
            tri = tri[np.linspace(0, len(tri) - 1, 40000).astype(int)]
        tris.append(tri)
        col = shade(it.mesh_obj, base_color(it))
        cols.append(col if len(col) == len(tri) else np.repeat(col, len(tri) // len(col) + 1, 0)[:len(tri)])
    T = np.vstack(tris); C = np.vstack(cols)
    pc = Poly3DCollection(T, facecolor=C, edgecolor="none")
    ax.add_collection3d(pc)
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az)
    ax.set_axis_off()
    ax.set_title(f"Knoll Mini {name}  S={spec.S}  q={q or 'zero'}  (head = original microduck x0.72)")
    fig.savefig(out / f"{name}.png", dpi=110, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("wrote", out / f"{name}.png")
