"""Render the assembly to PNGs (no GPU, no display needed). Run: python tools/render_views.py [--q joint=deg ...] [--out renders]
Writes renders/front.png, side.png, top.png, iso.png. Servos are drawn red, BDX head parts blue, everything else grey.
Use the PNGs so the human can eyeball the result between sessions; they are not a pass/fail check."""
import sys, argparse
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import spec
from assembly import build

ap = argparse.ArgumentParser(); ap.add_argument("--q", nargs="*", default=[]); ap.add_argument("--out", default=str(spec.ROOT / "renders"))
a = ap.parse_args()
q = {k: float(v) for k, v in (s.split("=") for s in a.q)}
items = build(q=q)
out = __import__("pathlib").Path(a.out); out.mkdir(parents=True, exist_ok=True)
views = {"front": (0, 0), "side": (0, -90), "top": (90, -90), "iso": (25, -135)}
for name, (el, az) in views.items():
    fig = plt.figure(figsize=(7, 8)); ax = fig.add_subplot(111, projection="3d")
    for it in items:
        tri = it.mesh_obj.triangles
        if len(tri) > 15000:
            tri = tri[np.linspace(0, len(tri) - 1, 15000).astype(int)]   # thin out faces for speed
        col = "tab:red" if it.kind == "servo" else ("tab:blue" if it.mesh in spec.BDX_HEAD_PARTS else "0.7")
        pc = Poly3DCollection(tri, facecolor=col, edgecolor="none", alpha=0.9 if it.kind == "servo" else 0.55)
        ax.add_collection3d(pc)
    allv = np.vstack([i.mesh_obj.vertices for i in items]); c = (allv.max(0) + allv.min(0)) / 2; r = (allv.max(0) - allv.min(0)).max() / 2
    ax.set_xlim(c[0]-r, c[0]+r); ax.set_ylim(c[1]-r, c[1]+r); ax.set_zlim(c[2]-r, c[2]+r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(el, az); ax.set_xlabel("X fwd mm"); ax.set_ylabel("Y left mm"); ax.set_zlabel("Z up mm")
    ax.set_title(f"Knoll Mini {name}  S={spec.S}  q={q or 'zero'}")
    fig.savefig(out / f"{name}.png", dpi=90); plt.close(fig)
    print("wrote", out / f"{name}.png")
