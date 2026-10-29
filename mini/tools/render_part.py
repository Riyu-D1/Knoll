"""Render one STL (or several) from standard angles with flat lambert shading.
Run: python tools/render_part.py file1.stl [file2.stl ...] --out DIR [--views front,side,tq,top,bottom,back]
Units: STL is assumed mm. Views: front(-x? no: looks at -z? see VIEWS), uses same lambert
style as render_solid.py so renders are comparable."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ap = argparse.ArgumentParser()
ap.add_argument("stls", nargs="+")
ap.add_argument("--out", required=True)
ap.add_argument("--views", default="front,back,left,right,top,bottom,tq")
ap.add_argument("--color", default="0.86,0.78,0.62")
a = ap.parse_args()

KEY = np.array([0.45, -0.55, 0.70]); KEY /= np.linalg.norm(KEY)
FILL = np.array([-0.6, 0.35, 0.35]); FILL /= np.linalg.norm(FILL)
BASE = np.array([float(x) for x in a.color.split(",")])

# axes: STL local — for head parts the jaw_soft frame: lx=up, ly=left, lz=back
VIEWS = {  # name: (elev, azim)  matplotlib camera
    "front":  (8, 0),     # looking from -lz ... matplotlib azim 0 looks along -x? tuned below
    "back":   (12, 180),
    "left":   (10, 90),
    "right":  (10, -90),
    "top":    (85, -25),
    "bottom": (-65, -25),
    "tq":     (18, -25),
    "tq2":    (18, 155),
}

def shade(mesh):
    n = mesh.face_normals.astype(float)
    lam = np.clip(n @ KEY, 0, 1) * 0.75 + np.clip(n @ FILL, 0, 1) * 0.25 + 0.18
    return np.clip(BASE[None, :] * lam[:, None], 0, 1)

out = __import__("pathlib").Path(a.out); out.mkdir(parents=True, exist_ok=True)
for f in a.stls:
    m = trimesh.load(f, force="mesh")
    stem = __import__("pathlib").Path(f).stem
    c = (m.bounds[0] + m.bounds[1]) / 2
    r = (m.bounds[1] - m.bounds[0]).max() / 2 * 1.15
    col = shade(m)
    for name in a.views.split(","):
        el, az = VIEWS[name]
        fig = plt.figure(figsize=(7, 7))
        ax = fig.add_subplot(111, projection="3d")
        tri = m.triangles
        if len(tri) > 60000:
            tri = tri[np.linspace(0, len(tri) - 1, 60000).astype(int)]
        pc = Poly3DCollection(tri, facecolor=col[:len(tri)], edgecolor="none")
        ax.add_collection3d(pc)
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_axis_off()
        ax.set_title(f"{stem} {name}")
        fig.savefig(out / f"{stem}_{name}.png", dpi=100, bbox_inches="tight", pad_inches=0.05)
        plt.close(fig)
    print("rendered", stem, "vol=%.1f cm3 wt=%s" % (m.volume / 1000, m.is_watertight))
