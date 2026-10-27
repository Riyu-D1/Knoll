# Originality & Licensing — Knoll Mk1

**Date:** 2026-10-26 · **Status:** Recommendation (not legal advice; re-verify before public release).

---

## 1. Recommended licence stack

| Asset | Licence | Rationale |
|---|---|---|
| Mechanical CAD, drawings, STL | **CERN-OHL-S v2** *(original Knoll designs only — see note below)* | Reciprocal open-hardware licence purpose-built for physical designs; forces derivatives of the *robot hardware* to stay open — our differentiation vs Microduck's closed HW |
| PCB / electronics design files | **CERN-OHL-S v2** | Same reciprocal argument; KiCad project + gerbers published |
| Firmware (MCU) + robot software | **Apache-2.0** | Permissive maximises adoption + contributions, matches the ecosystem norm (Microduck itself, onshape-to-robot, mjlab) |
| Simulation + training code | **Apache-2.0** | Same reasoning; enables reuse in papers |
| Trained policy weights + configs | **Apache-2.0 or CC-BY-4.0** | Weights aren't clearly "software" in every jurisdiction; dual CC-BY-4.0 is safest for artefacts |
| Docs, build guide, images | **CC-BY-SA-4.0** | Standard docs licence; reciprocal keeps translations/improvements shareable |
| Character artwork, name, logo, "Knoll" mark | **CC-BY-SA-4.0 for art; name/logo retained as trademark (recommended)** | Keeps the *project's identity* protectable while art stays remixable; prevents clone products trading on our name |
| Third-party components in BOM | their own terms | We re-distribute no vendor firmware/binaries except as licences permit |

> **Exception:** hardware meshes derived from Microduck are CC BY-NC-SA 4.0. See mini/LICENSE-MESHES.md. The CERN-OHL-S / Apache-2.0 rows above apply to original Knoll designs and code only, never to the Microduck-derived meshes under `mini/parts/` (non-commercial, share-alike).

**Permissive vs reciprocal trade-off:** Apache-2.0 for code maximises reuse (a company can build atop our stack → goodwill + contributions flow back through the community anyway). For *hardware*, CERN-OHL-S reciprocity is the point: anyone selling Knoll-derived designs must publish their changes — that is precisely the "open hardware equivalent" market position Microduck leaves open. Trademark retention on the name is how permissive projects (Arduino, Raspberry Pi) still protect their brand.

## 2. Originality checklist (evidence required before release claims)

- [ ] Body geometry: original proportions (dome-biped ≈170×160 mm shell, fused head, sprout topper) — unrelated to Microduck's shell geometry; CAD built from our own dimensioned spec, not from scans/imports of their files.
- [ ] Character: "moss-dome creature", name/logo original; **no duck bill, no Microduck colourways, no "duck" in naming**; trademark/name search before release (UK IPO + USPTO + GitHub/HF name squat check).
- [ ] Joints/enclosures: leg layout converges on 5-DOF biped (a generic engineering solution used across the field — Open Duck Mini, BDX-likes, RoboCup — not protectable expression) but all struts, hip blocks, shells, mounts are our own geometry.
- [ ] PCB: own schematic/layout; servo-bus interface is standard circuitry (tri-state buffer + UART) — no copied layout.
- [ ] Software: original implementation; reference repos used as *architectural study only* (Apache-2.0 permits reuse with attribution, but we re-implement; any third-party dep is credited in NOTICE).
- [ ] No copied assets: no Pollen/HF images, logos, MJCF models, policies, STLs, or "Microduck" naming; our MJCF is generated from our own CAD via onshape-to-robot-class pipeline (that tool is OSS by Rhoban, check licence — GPL/LGPL noted for compliance).
- [ ] Attribution: NOTICE file credits inspirations generically (e.g., "inspired by the open-duck class of research robots") and lists all third-party OSS deps + licences.
- [ ] No implied affiliation: docs state plainly "an independent community design inspired by the capabilities of small RL bipeds; not affiliated with Pollen Robotics or Hugging Face".

## 3. Third-party licence watchlist (populate as components land)

| Item | Licence | Constraint for us |
|---|---|---|
| microduck / microduck_rl (reference) | Apache-2.0 sw; HW CC BY-SA-NC + files unreleased | Study OK; do NOT copy code/assets; MJCF/models off-limits (NC) |
| MuJoCo / mjlab / rsl_rl | Apache-2.0 / per-repo | Fine to use & modify with attribution |
| ONNX Runtime | MIT | Fine |
| KiCad libraries, JLCPCB parts | various | Verify symbol/footprint licences in PCB stage |
| onshape-to-robot / CAD exporters | check per-tool (GPL family common) | GPL tools used as *tools* don't contaminate our CAD, but linking their code does — keep at arm's length (CLI use) |
| Servo vendor SDKs (Feetech/Hiwonder) | usually MIT-ish but verify | Prefer our own protocol implementation — serial-servo protocols are simple and documented |
| BNO085 fusion firmware | Bosch proprietary blob (in-module) | Use module as-is; no re-distribution issues |
| Raspberry Pi / Radxa images | per-vendor | Pin our own image build or document stock OS |

## 4. Community release plan (roadmap cross-ref)

Repo layout proposal: `knoll/` monorepo — `mech/` (CAD+STL, CERN-OHL-S), `pcb/` (CERN-OHL-S), `firmware/`, `runtime/`, `rl/` (Apache-2.0), `docs/` (CC-BY-SA), `brand/` (CC-BY-SA art + trademark note). One LICENSE per subtree + NOTICE.
