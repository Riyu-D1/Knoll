
## CAD (FreeCAD / STEP)

`cad/` contains the same assembly as a real CAD model, built by
`build_cad.py` (FreeCAD ≥1.0, headless `freecadcmd`):

| File | Contents | Size |
|---|---|---|
| `microduck-assembly-meshes.FCStd` | **Reference of record** — exact STL geometry (mm), `App::Part` per MJCF body (kinematic tree preserved), `Mesh::Feature` per part, JOINTS datum cylinders | ~10 MB |
| `microduck-assembly-solids.FCStd` | Same structure with BRep solids (meshes decimated 75% to keep size sane) — for direct solid editing | ~29 MB |
| `microduck-assembly.step.gz` | STEP AP214 (mm) of the solids build — import into Fusion/Onshape/SolidWorks | ~27 MB |

Structure mirrors the MJCF: `microduck` → `body_<name>` App::Parts
(trunk_base, yaw2roll, hip_l, upper_leg_*, leg, ankle_*, neck,
neck_pitch, yaw_roll_motion, jaw_soft, bearing_roll, hip_l_2, ...) →
`p_<part>` placements. **Re-posing a joint = editing that body's
Placement** — axes/ranges are on the red `J_*` cylinders.

```bash
freecadcmd build_cad.py -- --md-dir <robot dir> --out . --mode meshes
freecadcmd build_cad.py -- --md-dir <robot dir> --out . --mode solids --decimate 0.75
```

Note: BRep solids here are faceted conversions of the STL shells — fine
for measuring, sectioning and interference checks, but they're not
parametric. Remodelling a part = replace its `p_<part>` object; keep the
body Placement.
