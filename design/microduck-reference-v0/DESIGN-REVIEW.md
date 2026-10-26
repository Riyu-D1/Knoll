
## 9. CAD deliverables (added)

`cad/` now holds the full robot as real CAD, built by `build_cad.py`
(FreeCAD 1.1 headless): `microduck-assembly-meshes.FCStd` (10 MB —
exact STL geometry, kinematic `App::Part` tree, joint datum cylinders),
`microduck-assembly-solids.FCStd` (29 MB — 75%-decimated BRep solids for
direct editing), and `microduck-assembly.step.gz` (27 MB — AP214 for
Fusion/Onshape/SolidWorks). Bbox verified identical to the Blender build
(X −51.8..92.3, Y ±70.5, Z 13.5..277.4 mm); all 14 joint positions
cross-checked against `parts-manifest.csv`.

Caveats: solids are faceted (mesh→shape) — parametric-quality surfaces
exist only in Pollen's original Onshape doc (linked in THIRD-PARTY-NOTICES).
Full-resolution solids can be regenerated locally with `--mode solids
--decimate 0` (~450 MB STEP, ~10 min).
