"""Generate the BDX-style head parts (parametric, trimesh + manifold). Session 3 tunes the numbers in P only.
Head frame H used for the numbers below: X forward, Y left, Z up, origin = jaw_soft body origin (mm).
(jaw_soft body frame: +x up, +y left, -z forward -> conversion done at export.)
Writes parts/current/bdx_head_top.stl, bdx_head_bottom.stl, bdx_face_plate.stl (chin), bdx_eye_bezel_l/r.stl,
all in the jaw_soft body frame. Run: python tools/make_bdx_head.py   then set spec.HEAD_MODE = "bdx"."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh, spec
from trimesh.transformations import rotation_matrix, translation_matrix
U = lambda ms: trimesh.boolean.union(ms, engine="manifold")
D = lambda a, b: trimesh.boolean.difference([a, b], engine="manifold")
I = lambda a, b: trimesh.boolean.intersection([a, b], engine="manifold")

P = dict(                      # all mm / degrees, head frame H.  [U] = taste, tune freely within the limits in SPEC 7
    dome_c=(12.0, 0.0, 5.0), dome_r=(45.0, 48.0, 30.0),   # big rounded helmet (fwd, side, up radii)
    lean_deg=12.0,             # forward lean of the whole head shape (nose down)
    wall=1.8,
    brow_z=22.0, brow_h=6.0, brow_out=4.5,                 # brow ridge band height and how far it stands out
    chin_c=(36.0, 0.0, -13.0), chin_r=(18.0, 26.0, 9.0),  # small lower face / jaw
    cut_bottom_z=-16.0,        # flat bottom (neck enters from below)
    neck_hole_d=46.0,          # opening in the bottom for neck / yaw_roll_motion
    split_z=0.0,               # top/bottom split plane
    eye_y=22.0, eye_z=8.0, eye_hole_d=38.0,                # 12-LED WS2812 ring OD 37 [U]: hole = OD + 1
    bezel_od=45.0, bezel_t=2.5,
    cam=(0.0, -6.0, 8.0),      # camera window: y, z, diameter (between/below the eyes)
    tof=(12.0, -9.0, 6.0),     # ToF window: y, z, diameter
    grille_x=-25.0, grille_d=2.0,
    posts=[(-16.0, 3.0), (-25.0, 3.0)],   # (x, z) of the 2+2 side posts that screw into motor_support
    ms_y=(11.0, -22.0),        # motor_support side faces (+y, -y) in this frame: its solid back block (world x -20..-4) has faces y=+11/-22
)

def ell(c, r, sub=5):
    m = trimesh.creation.icosphere(subdivisions=sub); m.apply_scale(r); m.apply_translation(c); return m
def cyl(p0, p1, d):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    m = trimesh.creation.cylinder(radius=d / 2, segment=[p0, p1], sections=48); return m
def box(lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    return trimesh.creation.box(extents=hi - lo, transform=translation_matrix((lo + hi) / 2))
lean = rotation_matrix(np.radians(P["lean_deg"]), [0, 1, 0], point=P["dome_c"])

c, r, w = np.array(P["dome_c"]), np.array(P["dome_r"]), P["wall"]
dome = ell(c, r); dome_in = ell(c, r - w)
big = ell(c, r + P["brow_out"])
brow = I(big, box((c[0], -80, P["brow_z"] - P["brow_h"] / 2), (c[0] + 80, 80, P["brow_z"] + P["brow_h"] / 2)))
chin = ell(P["chin_c"], P["chin_r"]); chin_in = ell(P["chin_c"], np.array(P["chin_r"]) - w)
outer = U([dome, brow, chin]); inner = U([dome_in, chin_in])
for m in (outer, inner): m.apply_transform(lean)
shell = D(outer, inner)
# side posts to motor_support (+ pilot holes), added before cuts
for (x, z) in P["posts"]:
    for y0, sgn in ((P["ms_y"][0] - 0.5, 1), (P["ms_y"][1] + 0.5, -1)):
        shell = U([shell, I(cyl((x, y0, z), (x, sgn * 60, z), 6.0), outer)])
        shell = D(shell, cyl((x, y0 - sgn * 6, z), (x, sgn * 70, z), 1.6))
# bosses joining top and bottom halves
for th in (40, 140, 220, 320):
    t = np.radians(th); bx = c[0] + (r[0] - w - 2.0) * np.cos(t); by = (r[1] - w - 2.0) * np.sin(t)
    b = cyl((bx, by, P["split_z"] - 6), (bx, by, P["split_z"] + 6), 6.0); b.apply_transform(lean)
    h = cyl((bx, by, P["split_z"] - 7), (bx, by, P["split_z"] + 7), 1.6); h.apply_transform(lean)
    shell = D(U([shell, I(b, outer)]), h)
# openings
shell = D(shell, box((-200, -200, -200), (200, 200, P["cut_bottom_z"])))
shell = D(shell, cyl((c[0] - 5, 0, -60), (c[0] - 5, 0, 0), P["neck_hole_d"]))
bez = []
for s_ in (1, -1):
    y, z = s_ * P["eye_y"], P["eye_z"]
    shell = D(shell, cyl((c[0], y, z), (c[0] + 90, y, z), P["eye_hole_d"]))
    loc, _, _ = outer.ray.intersects_location([[c[0], y, z]], [[1.0, 0, 0]])
    xs = float(loc[:, 0].max())                     # front surface at the eye centre
    ring = D(cyl((xs - 6, y, z), (xs + P["bezel_t"], y, z), P["bezel_od"]),
             cyl((xs - 7, y, z), (xs + P["bezel_t"] + 1, y, z), P["eye_hole_d"] - 4))
    bez.append(D(ring, inner))                      # flat proud bezel, trimmed to the inside of the shell
cy, cz, cd = P["cam"]; shell = D(shell, cyl((c[0], cy, cz), (c[0] + 90, cy, cz), cd))
ty, tz, td = P["tof"]; shell = D(shell, cyl((c[0], ty, tz), (c[0] + 90, ty, tz), td))
for gy in (-6, 0, 6):
    for gz in (0, 6, 12):
        shell = D(shell, cyl((P["grille_x"], gy, gz), (P["grille_x"] - 60, gy, gz), P["grille_d"]))
top = I(shell, box((-200, -200, P["split_z"]), (200, 200, 200)))
bot = I(shell, box((-200, -200, -200), (200, 200, P["split_z"])))
chin_part = I(bot, box((P["chin_c"][0] - 8, -200, -200), (200, 200, P["split_z"])))   # removable face plate
bot = D(bot, box((P["chin_c"][0] - 8, -200, -200), (200, 200, P["split_z"])))
H2J = np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1]], float)   # H(x fwd,y,z up) -> jaw_soft(x up,y,z back)
for name, m in (("bdx_head_top", top), ("bdx_head_bottom", bot), ("bdx_face_plate", chin_part),
                ("bdx_eye_bezel_l", bez[0]), ("bdx_eye_bezel_r", bez[1])):
    m = m.copy(); m.apply_transform(H2J)
    nb = len(m.split(only_watertight=False))
    print(f"{name:18s} watertight={m.is_watertight} bodies={nb} vol={m.volume/1000:.1f} cm3 extents={m.extents.round(1)}")
    m.export(spec.WORK_DIR / f"{name}.stl")
print("done. Now set HEAD_MODE = 'bdx' in tools/spec.py and run check_clearance / sweep_check / render_views.")
