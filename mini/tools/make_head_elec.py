"""Session 4: electronics placeholders for the ORIGINAL Microduck head (HEAD_MODE=microduck).
Writes parts/current/elec_*.stl, all authored in the jaw_soft body frame (mm), matching
spec.ELECTRONICS names/masses. Replaces the BDX-head versions (now in parts/attic_bdx/).
Layout (jaw frame: +x = world up, +z = world backward; face at z ~ -53, eye axis (x 11, y 0)):
  elec_xiao_esp32s3_sense  XIAO board 21x17.5x6 right of the lens holder + OV2640 cube at the
                           eye axis behind the m12 holder, joined by a flex-ribbon stub
  elec_eye_rings_x2        two identical Ø26/Ø18 x2.4 WS2812 halo rings stacked around the
                           lens barrel behind the eye puck (noenoeil)
  elec_vl53l0x             ToF board behind the face's right-side window
  elec_max98357_speaker    Ø22x4 speaker disc lying flat in the upper-front dome
  elec_buck_5v             6x15x20 buck board in the dome's right interior wedge
Run: python tools/make_head_elec.py  (then re-run sweeps + the pairwise audit)"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, trimesh
import spec

def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b

def annulus(r_out, r_in, t):
    return trimesh.boolean.difference(
        [trimesh.creation.cylinder(radius=r_out, height=t, sections=64),
         trimesh.creation.cylinder(radius=r_in, height=t + 2, sections=64)], engine="manifold")

EYE = (11.0, 0.0)   # eye axis in jaw frame (x, y)

def build():
    out = {}
    board = box(-4.0, 17.0, -25.25, -7.75, -36.75, -30.25)      # XIAO mainboard, vertical, right of eye axis
    board = trimesh.boolean.difference([board, box(13.0, 18.0, -26.0, -22.5, -34.0, -29.5)], engine="manifold")  # corner clears dome wall
    ribbon = box(9.0, 13.0, -7.8, -3.9, -35.5, -33.5)           # flex ribbon board->camera
    camera = box(7.0, 15.0, -4.0, 4.0, -39.6, -34.6)            # OV2640 cube at the eye axis
    out["elec_xiao_esp32s3_sense"] = trimesh.boolean.union([board, ribbon, camera], engine="manifold")

    rings = []
    for zc in (-41.7, -38.7):                                   # two stacked halo rings, 0.6 mm apart
        r = annulus(13.0, 9.0, 2.4)                             # Ø26/Ø18 x 2.4 mm  (12-LED mini ring [U])
        r.apply_translation([EYE[0], EYE[1], zc]); rings.append(r)
    out["elec_eye_rings_x2"] = trimesh.boolean.union(rings, engine="manifold")

    out["elec_vl53l0x"] = box(4.5, 15.0, 14.0, 25.0, -42.5, -39.5)   # 10.5x11x3 at the right ToF window

    sp = trimesh.creation.cylinder(radius=11.0, height=4.0, sections=48)
    sp.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    sp.apply_translation([14.0, 0.0, 8.0])
    out["elec_max98357_speaker"] = sp                            # Ø22x4 flat disc, membrane up

    out["elec_buck_5v"] = box(-11.0, -5.0, 12.0, 30.0, 0.5, 15.5)    # 6x18x15 flat on the left flank
    return out

if __name__ == "__main__":
    for name, m in build().items():
        p = spec.WORK_DIR / f"{name}.stl"
        m.export(p)
        print(f"{name:30s} watertight={m.is_watertight} vol={m.volume/1000:.2f} cm3 bounds={m.bounds.round(1).tolist()}")
        print("   wrote", p)
