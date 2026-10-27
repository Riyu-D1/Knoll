"""SCS0009 geometry placed in the Microduck XL330 mesh-local frame (raw xl330.stl frame), AFTER scaling.
XL330 raw frame (measured): shaft axis = local X through (y=0, z=0); horn/output side = -X
(horn boss tip at x=-14.5 mm full scale); body spans y +-10, z -24.5..+9.5 (shaft near +Z end).
Rule used here: the SCS0009 horn top face sits exactly where the XL330 horn tip was after scaling
(x = -14.5*S), so every driven part keeps its horn-mating face. The SCS0009 case then extends
toward +X. Shaft stays on the joint axis. Case is offset toward -Z (shaft near the +Z end).
Functions return trimesh meshes in that frame (mm). CLI writes parts/lib/*.stl."""
import sys, numpy as np, trimesh
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import spec

def _box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b

def frame_numbers(s=None):
    s = spec.S if s is None else s
    c = spec.SCS
    horn_top = -14.5 * s                       # horn face, -X side
    case_top = horn_top + c["horn_t"] + c["spline_h"]
    case_bot = case_top + c["case_h"]
    zc = -c["shaft_off"]                        # case centre along Z
    ear_x0 = case_top + c["ear_top_below_case_top"]
    return dict(horn_top=horn_top, case_top=case_top, case_bot=case_bot, zc=zc,
                ear_x0=ear_x0, ear_x1=ear_x0 + c["ear_t"])

def envelope_mesh(s=None, grow=0.0, horn=True):
    """Case + ears (+ spline + horn disc if horn=True). grow = extra clearance per side (mm)."""
    c, f, g = spec.SCS, frame_numbers(s), grow
    parts = [
        _box(f["case_top"] - g, f["case_bot"] + g, -c["case_w"] / 2 - g, c["case_w"] / 2 + g,
             f["zc"] - c["case_l"] / 2 - g, f["zc"] + c["case_l"] / 2 + g),
        _box(f["ear_x0"] - g, f["ear_x1"] + g, -c["case_w"] / 2 - g, c["case_w"] / 2 + g,
             f["zc"] - c["ear_span"] / 2 - g, f["zc"] + c["ear_span"] / 2 + g),
    ]
    if not horn:
        return trimesh.boolean.union(parts, engine="manifold")
    sp = trimesh.creation.cylinder(radius=3.0 + g, height=c["spline_h"] + 0.01, sections=32)
    sp.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    sp.apply_translation([f["case_top"] - c["spline_h"] / 2, 0, 0]); parts.append(sp)
    hd = trimesh.creation.cylinder(radius=c["horn_d"] / 2 + g, height=c["horn_t"], sections=48)
    hd.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    hd.apply_translation([f["horn_top"] + c["horn_t"] / 2, 0, 0]); parts.append(hd)
    return trimesh.boolean.union(parts, engine="manifold")

def cutter_mesh(s=None):
    """What to SUBTRACT from the holding part: case + ears + 0.3 mm clearance, a cable channel
    out of the case bottom (+X), and 2x M2 pilot holes (d=1.6) through the ears along X.
    The horn/spline region is NOT cut (it belongs to the driven part)."""
    c, f, g = spec.SCS, frame_numbers(s), spec.SCS["fit_clearance"]
    case = _box(f["case_top"] - g, f["case_bot"] + g, -c["case_w"] / 2 - g, c["case_w"] / 2 + g,
                f["zc"] - c["case_l"] / 2 - g, f["zc"] + c["case_l"] / 2 + g)
    # insertion: case slides in from the horn side, so the ear slot is open toward -X
    ears = _box(f["case_top"] - 6.0, f["ear_x1"] + g, -c["case_w"] / 2 - g, c["case_w"] / 2 + g,
                f["zc"] - c["ear_span"] / 2 - g, f["zc"] + c["ear_span"] / 2 + g)
    cable = _box(f["case_bot"] - 1.0, f["case_bot"] + c["cable_exit_clear"], -2.5, 2.5,
                 f["zc"] - 4.0, f["zc"] + 4.0)
    holes = []
    for zz in (f["zc"] - c["ear_hole_pitch"] / 2, f["zc"] + c["ear_hole_pitch"] / 2):
        h = trimesh.creation.cylinder(radius=0.8, height=10.0, sections=16)
        h.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
        h.apply_translation([f["ear_x1"] + 4.0, 0, zz]); holes.append(h)
    return trimesh.boolean.union([case, ears, cable] + holes, engine="manifold")

def cradle_mesh(s=None, wall=2.0):
    """Material to ADD to the holding part before cutting: envelope (case+ears) grown by
    clearance+wall, without the horn side face (open toward -X)."""
    c, f = spec.SCS, frame_numbers(s)
    g = spec.SCS["fit_clearance"] + wall
    return _box(f["case_top"], f["case_bot"] + g, -c["case_w"] / 2 - g, c["case_w"] / 2 + g,
                f["zc"] - c["ear_span"] / 2 - g + wall, f["zc"] + c["ear_span"] / 2 + g - wall)

if __name__ == "__main__":
    out = spec.ROOT / "parts" / "lib"; out.mkdir(parents=True, exist_ok=True)
    for name, m in [("scs0009_envelope", envelope_mesh()), ("scs0009_cutter", cutter_mesh()),
                    ("scs0009_cradle", cradle_mesh())]:
        m.export(out / f"{name}.stl")
        print(f"{name:18s} watertight={m.is_watertight} extents={m.extents.round(2)} bounds={m.bounds.round(2).tolist()}")
    print("frame numbers (mm, XL330 raw frame, scaled):", {k: round(v, 2) for k, v in frame_numbers().items()})
