# Manufacturing & Sourcing Notes — MASCOT bipedal mascot robot

**Workstream:** Manufacturing / cost engineering
**Date checked:** 2026-10-26 (all prices GBP, UK suppliers, VAT-inclusive unless marked `ex VAT`)
**Price-type key:** `verified` = live listing seen this session; `indicative` = real listing, price may drift/depend on variant; `estimate` = engineering estimate, no live listing

**Scope assumption (aligned to brief):** ~26–32 cm, ~1 kg biped, 10–14 × 7.4 V (2S) serial smart servos, FDM-only manufacture, hobby tools, DIY build target < £320 all-in.

**Closest reference builds used for calibration:**
- **Open Duck Mini v2** (apirrone/Open_Duck_Mini): 42 cm duck biped, 14× Feetech STS3215 7.4 V bus servos + 2× 9g antenna servos, ~500 g PLA at 15% infill + TPU foot soles, Pi Zero 2 W, BNO055, 2S 18650 pack w/ BMS + XT30, M3 heat-set inserts throughout, full BOM < $400. https://github.com/apirrone/Open_Duck_Mini , https://opensourcerobotics.dev/robots/open-duck-mini/
- **ToddlerBot** (Stanford): 0.56 m, 3.4 kg humanoid, entirely 3D-printed, < $6k with ~90% of cost in motors+compute, ~10 h per print plate on a Bambu X1C, recommends an electric screwdriver for assembly. https://toddlerbot.github.io/ , https://hshi74.github.io/toddlerbot/sections/01_hardware.html
- **Voron print spec** (the de-facto FDM structural standard): ABS, 0.2 mm layers, 0.4 mm forced extrusion width, 4 walls, 5 top/bottom layers, 40% infill (grid/gyroid/honeycomb/cubic). https://docs.siboor.com/siboor-2.4-r2-aug/the-build/printed-parts

---

## 1. Filament engineering for robot structure

### 1.1 Measured material properties (Prusament, CNC Kitchen — verified test data)
Source: https://www.cnckitchen.com/blog/comparing-pla-petg-amp-asa-feat-prusament

| Material | Stiffness | Flat-hook strength | Layer-adhesion strength | Impact (Charpy) | Softening |
|---|---|---|---|---|---|
| PLA | ~3300 MPa | 73 kg | 40 kg (55% of flat) | 5 kJ/m² (brittle) | ~60 °C |
| PETG | ~1900 MPa (≈58% of PLA) | 55 kg but never snaps — stretches | 25 kg (46%) | 8.6 kJ/m² | ~80 °C |
| ASA | ~2300 MPa | 57 kg | **17 kg (29% — worst)** | **18 kJ/m² (best)** | ~110 °C |

### 1.2 Creep under sustained joint load — the honest picture
Creep data in the community is **contradictory; flag both sides**:

- MyTechFun's instrumented creep tests (PLA/PETG/ASA/Nylon, 6-day constant-load tests incl. an M5-screw-clamped specimen — the closest analogue to our clamped servo joints): https://www.mytechfun.com/video/143
- PETG is repeatedly reported as the *worst* common filament for sustained tensile creep: it keeps stretching where ASA/ABS deform then stabilise (https://3dprinting.stackexchange.com/questions/19813/). A Bambu forum thread claims the reverse for PLA (https://forum.bambulab.com/t/pla-vs-petg-hf-deformation-under-load/212834) — treat forum claims as indicative, not verified.
- Peer-reviewed PETG FFF creep work confirms nonlinear creep at ≥50% of ultimate stress, strongly anisotropic with print direction: https://www.mdpi.com/2073-4360/17/15/2075 and https://doi.org/10.1016/j.engfailanal.2025.110120
- Thrinter's clip test (PLA vs PETG vs ABS vs Taulman 910 nylon): all permanently deformed under 24 h clip load; PLA crept visibly but retained clamping function — https://thrinter.com/creep-abs-pla-petg-alloy-910/

**Engineering interpretation for this robot:** every candidate polymer stress-relaxes under a clamped screw joint. The fix is **design, not material choice**: pass bending loads through metal (shafts, dowel pins, washers, through-bolts into heat-set inserts) and never let a plastic surface carry sustained clamping pressure directly. Carbon-fibre fill measurably raises modulus ~1.5–2× and reduces creep (fibres share the load) at modest cost.

### 1.3 Candidate materials — verdicts

| Material | Pros | Cons | Verdict |
|---|---|---|---|
| **PLA / PLA+** | Stiffest cheap option, easiest print, dimensionally accurate, proven at scale on this robot class (Open Duck Mini = plain PLA 15% infill) | Brittle (5 kJ/m²): drop damage, crack at screw bosses; poor heat | **Baseline/MVP structural** — works, but fragile under falls |
| **PETG** | Tough/ductile — fails gracefully, good layer adhesion, easy print, cheapest credible structural | ~60% of PLA stiffness; worst tensile creep of the trio; strings | **Good for cosmetic shell and semi-structural**; design around creep in joints |
| **ASA** | Best impact of unfilled trio, best heat/UV | Worst layer adhesion (29%), warps — wants enclosure; styrene fumes | Skip unless builder has an enclosure; no compelling gain over PETG-CF |
| **PLA-CF** | ~2× stiffness of PLA, prints like PLA, matte finish hides layers | Still brittle-ish; abrasive (needs hardened nozzle) | Good upgrade for slim stiff links |
| **PETG-CF** | Best printability/strength/toughness compromise, much stiffer than PETG, better creep, low warp, no enclosure needed | Abrasive; matte black only-ish | **Recommended primary structural** |
| **PAHT-CF / PA6-CF (nylon)** | Best creep + toughness + heat (~150 °C class) — the "proper engineering" choice | £46–92/kg, must be dried, PAHT-CF wants enclosure + hardened ≥0.4 mm nozzle | Optional premium tier; overkill for v1 |

### 1.4 UK filament prices (checked 2026-10-26)

| Filament | Price/kg | Supplier | URL | Type |
|---|---|---|---|---|
| eSUN PETG-Basic 1 kg | £10.99 | esun3dstore.uk | https://esun3dstore.uk/collections/petg | verified |
| eSUN PETG 1 kg | from £13.99 | esun3dstore.uk | same | verified |
| eSUN PETG-CF 1 kg | from £20.99 (list £32.99) | esun3dstore.uk | https://esun3dstore.uk/collections/engineering-filament | verified |
| eSUN PETG-CF 1 kg | £24.21–32.99 | Amazon UK | https://www.amazon.co.uk/eSUN-Filament-Printing-Materials-Printers/dp/B0DD3R7M47 | verified |
| eSUN PETG-CF 1 kg | £26.50 | 3DJake UK | https://www.3djake.uk/esun/petg-cf-antique-brass | verified |
| eSUN PLA-CF 1 kg | from £22.99 | esun3dstore.uk | https://esun3dstore.uk/collections/engineering-filament | verified |
| eSUN ABS-CF 1 kg | from £18.99 | esun3dstore.uk | same | verified |
| eSUN PA-CF 1 kg | £45.99 | esun3dstore.uk | same | verified |
| eSUN ASA+ 1 kg | from £21.99 | esun3dstore.uk | https://esun3dstore.uk/collections/engineering-filament | verified |
| eSUN PLA-ST (super tough) 1 kg | from £22.99 | esun3dstore.uk | same | verified |
| Bambu PLA Basic / PETG HF / ABS, 1 kg | £17.99–20.99 (£11.99–17.99/roll in 4–8-roll bulk) | uk.store.bambulab.com | https://uk.store.bambulab.com/pages/promotions/filament-bulk-sale | verified |
| Bambu PA6-CF | from £37.99 (500 g class) | uk.store.bambulab.com | https://uk.store.bambulab.com/collections/pa-pet | verified |
| Bambu PAHT-CF | from £45.99 (500 g spool; £99/kg at 3DJake) | uk.store.bambulab.com / 3djake.uk | https://uk.store.bambulab.com/products/paht-cf | verified |
| Prusament PETG 1 kg | £25–30 | EDS3D / Neill's Materials | https://eds3d.co.uk/shop/p/prusament-pla-jzwdg-tzktp-zlthr-gdxpw-2yhwy-e3dmy-n7dm3 | verified |

### 1.5 Material recommendation (with justification)

**Recommended split — "Tier 1 (default BOM)" ≈ £12–15 of filament total:**
- **Structural load-path parts** (servo brackets, leg links, hip/knee/ankle joint blocks, torso frame, foot skeleton): **eSUN PETG-CF @ ~£21/kg** — prints on any open printer at 240–260 °C, ~2× PETG stiffness, tough (won't shatter on the inevitable demo-table fall), markedly better creep than unfilled PETG. ~350–400 g needed → ~£8.
- **Cosmetic shell / head / covers / colour accents:** **PLA Basic or PETG £11–14/kg** — detail and colour are what matter; keep it out of the load path. ~150–250 g → ~£3.
- **Feet soles / bumpers / cable grommets:** **TPU 95A** ~£14–20/kg, ~30–40 g → ~£1. (Open Duck Mini does exactly this: TPU foot pads at 40% infill.)

**Tier 0 (absolute-cheapest viable):** whole robot in eSUN PETG-Basic £10.99/kg or PLA £10–13/kg → ~£7–8 total. Validated by Open Duck Mini running plain PLA at this exact scale. Accept brittle-drop risk and joint creep; mitigate with design (§2).

**Tier 2 (premium):** PAHT-CF/PA6-CF for high-stress joint parts only (~200 g → £10–20 extra). Not recommended for v1 — drying + enclosure demands hurt DIY accessibility.

⚠️ Any CF filament needs a hardened-steel nozzle (a £5–15 consumable — add to tools if the builder's printer is brass-nozzled).

---

## 2. Print design rules for structural parts

Baseline recipe adapted from the Voron structural spec (industry standard, verified) + Open Duck Mini practice:

| Parameter | Structural parts | Cosmetic parts |
|---|---|---|
| Layer height | 0.2 mm | 0.16–0.24 mm |
| Wall count (0.4 nozzle) | **4–6 (≥1.6–2.4 mm)** | 2–3 |
| Top/bottom layers | 5 | 4–5 |
| Infill | **40–60% gyroid/grid/cubic** (joint blocks → 60–100% local) | 10–15% |
| Material | PETG-CF (or PETG/PLA MVP) | PLA |

**Load-path rules:**
- **Orientation beats infill.** Layer lines are the weak axis (vertical-printed hooks held only 29–55% of flat strength — CNC Kitchen). Orient each part so primary joint loads run **along** the layers, never peeling them. For a leg link, print lying flat so servo tension compresses/shears layers in-plane.
- **Joint loads through metal:** dowel pins/shafts span the joint; the servo horn's M3 bolts go into **heat-set inserts or captive nyloc nuts**, never raw plastic threads.
- **Stress-relaxation allowance:** under every screw head/nut bearing on plastic, use a **metal washer** to spread load (stops the local creep-cratering that loosens joints). Flanged or Form-A washers everywhere a screw touches plastic.
- **Heat-set inserts:** Voron-spec **M3×5×4 mm** (Ø5.7 mm knurl) as default; M2.5×~4 for small parts. Boss OD ≥ 2× insert OD (≥ ~9 mm for M3), hole ~Ø4.0–4.2 mm printed for the M3 insert. Accu lists recommended hole Ø4.0 mm −0/+0.1 and min wall 1.8 mm for their M3 heat-fix insert — consistent: https://www.accu.co.uk/brass-threaded-inserts/845137-HTBI-M3-BR
- **Hole shrinkage:** FDM holes print ~0.1–0.2 mm undersize; vertical holes print rounder than horizontal ones. Compensate in CAD (+0.1–0.2 mm) or drill/ream after printing. https://help.makelab.com/help/article/how-to-design-holes-threads-and-inserts-for-3d-printing
- **Fits (per Makelab + press-fit calculators, verified):**
  - Press fit (bearing bores): ~0.05 mm interference target → draw bore ≈ +0.15–0.30 mm over bearing OD (compensating shrink). e.g. 6700ZZ (15 mm OD) → design ~15.2–15.3 mm bore, then verify with a test coupon. PLA/PLA-CF can split on press fits ≥32 mm bore — prefer slip-fit + retainer plate there. https://machinistcalcs.com/guides/bearing-fit-chart/ , https://3dprintcalcs.uk/mechanical/press-fit-calculator/
  - Slip fit (mating shells, servo case pockets): 0.2–0.3 mm per side
  - Moving parts (hinges, spacers on shafts): 0.3–0.4 mm per side
  - Achievable dimensional accuracy on a tuned Bambu/Prusa: **±0.1–0.15 mm**; assume ±0.3 mm worst-case on an untuned Ender.
- **Bearings:** prefer **slip-fit bore + printed retainer flange or M3 bolt + washer clamping the outer race** over true press-fit (print-to-print scatter of ±0.08 mm makes press fits inconsistent — machinistcalcs source above). Press-fit only where disassembly isn't needed.
- **Print-in-place:** avoid in load paths (weak layer plane at the joint). Fine for cable clips and cosmetic hinges. This is a screw-together robot — Open Duck Mini and ToddlerBot both are.
- **No glue in load paths, ever.** Glue (or friction) joints silently fail under vibration; only threadlocker on metal-to-metal threads.

### Print-time estimate per part class
(Basis: ~0.2 mm layers, ~25–40 g/h effective on a Bambu/Prusa-class machine; total build ~500–700 g filament, calibrated from Open Duck Mini's ~500 g and ToddlerBot's ~10 h/plate.)

| Part class | Est. mass each | Est. print time each | Qty | Subtotal |
|---|---|---|---|---|
| Servo bracket / joint block (hip, knee, ankle) | 15–30 g | 1.5–3 h | ~10–14 | 15–35 h (batch 3–4/plate) |
| Leg links / shank+thigh shells | 30–60 g | 3–6 h | 4 | 12–24 h |
| Torso / pelvis frame | 60–100 g | 5–9 h | 1–2 | 5–18 h |
| Feet (skeleton + TPU sole) | 20–40 g | 2–4 h | 2 | 4–8 h |
| Head + neck mounts | 20–40 g | 2–4 h | 1 set | 2–4 h |
| Cosmetic shell, covers, accents | 80–150 g | 6–12 h | 1 set | 6–12 h |
| **Total** | **~500–700 g** | — | — | **~30–60 h ≈ 4–7 printer-days** |

(These are estimates, not measurements. Order of magnitude confirmed by both reference builds.)

---

## 3. Standard hardware BOM — real UK prices (2026-10-26)

CSV format per brief: `category, item, part_number, manufacturer, qty, unit_price_gbp, source_url, supplier, price_date, price_type, mass_g, notes, alternative`

```csv
category,item,part_number,manufacturer,qty,unit_price_gbp,source_url,supplier,price_date,price_type,mass_g,notes,alternative
filament,PETG-CF 1.75mm 1kg,PETG-CF,eSUN,1,20.99,https://esun3dstore.uk/collections/engineering-filament,eSUN UK store,2026-10-26,verified,1000,structural parts ~400g needed,Bambu PET-CF £41.99 / Prusament PETG £25-30
filament,PLA Basic 1kg,PLA-B,eSUN,1,10.99,https://esun3dstore.uk/,eSUN UK store,2026-10-26,indicative,1000,cosmetic shell ~200g needed,Bambu PLA Basic refill £13.99-17.99
filament,TPU 95A 1kg,TPU-95A,eSUN,1,14.99,https://esun3dstore.uk/,eSUN UK store,2026-10-26,indicative,1000,feet soles+bumpers ~40g needed,any 95A TPU
fasteners,M3 cap/button head screw+nut+washer kit 300-340pc,assorted,A2 stainless,1,8.40,https://www.monkeyjamsshed.co.uk/product/assorted-m3-socket-cap-bolts-nuts-hex-nyloc-washers-allen-key-set-a2-70-stainless-steel-300-pieces/,Monkeyjams Shed,2026-10-26,verified,335,"M3x8/10/12/16/20 + hex+nyloc nuts + washers — covers ~all joints",FlyingTech 340pc £11.99 / Amazon £6.55
fasteners,M2.5 fixing kit 120pc,M2.5A-KIT,stainless,1,3.50,https://www.componentshop.co.uk/hardware/fixing-kits.html,Component Shop,2026-10-26,verified,~50,small brackets+PCB mounts,nylon M2-M5 510pc kit £~8 (FlyingTech)
fasteners,M2 screws pack,M2 socket head,generic,1,3.00,https://www.ebay.co.uk/,eBay UK,2026-10-26,estimate,~30,servo horn screws (servos ship with some),included in M2.5 kit if mixed
inserts,Heat-set inserts M3x5x4 (Voron spec) 50pc,HSI-M3-5x4,generic brass,1,5.00,https://jb3d.uk/product/50-threaded-heat-set-inserts-m3-x-d4-6-x-l4-0/,JB3D,2026-10-26,verified,100,~30-40 inserts per robot,Pi Hut £5.90/50; ruthex 100pc £8.25; CNCKitchen Voron 100pc £11.05 (3DJake)
inserts,Heat-set inserts M2.5 50pc,HSI-M2.5,generic brass,1,5.00,https://www.3djake.uk/3d-printer-accessories/threaded-inserts,3DJake,2026-10-26,indicative,50,small parts,ruthex assortment M2-M5 £27.50
bearings,Ball bearing 6700ZZ 10x15x4 8pc,6700ZZ,3DJAKE,1,5.65,https://www.3djake.uk/3djake/ball-bearing,3DJake,2026-10-26,verified,~20,joint idler shafts (4-6 needed),ModelFixings 4pc £6.40; 6700-2RS £7.20/4
bearings,Ball bearing MR126ZZ 6x12x4,MR126ZZ,Reely,10,0.57,https://www.rapidonline.com/reely-mr-126-zz-rc-car-style-ball-bearings-12mm-od-6mm-bore-50-6564,Rapid Electronics,2026-10-26,verified,~3,£0.475 ex VAT @10+; small joint/shaft support,MR126ZZ £2.50+ Sevlow; 623ZZ 8pc £4.50 3DJake
bearings,Ball bearing MR105ZZ 5x10x4 8pc,MR105ZZ,3DJAKE,1,4.50,https://www.3djake.uk/3djake/ball-bearing,3DJake,2026-10-26,verified,~12,alt small-joint size,F695ZZ flanged £7.29/8
shafts,Hardened dowel pins 3mm/4mm x 16-30mm,DIN6325,GWR Fasteners,20,0.15,https://www.ebay.co.uk/itm/291500687921,eBay UK (GWR),2026-10-26,verified,~2,joint pivot shafts — pack prices £3.91 mixed,WDS from £0.26 ea; FusionFixings from £0.11 ea
servo_hw,Metal 25T servo horn (Feetech-spline),FK-AB-3,Feetech-compat,4,4.99,https://www.rccontrolfreak.co.uk/product/25t-m3-metal-aluminium-rc-servo-arm-horn-for-futaba-savox-xcore-hl-hsp,RC Control Freak,2026-10-26,verified,5,replace plastic horns at high-load joints,ukrctech £3.00; scorchedparts 7075 £7.00
servo_hw,Servo horn screw set (M2+M3 centre),included,Feetech,1,0.00,https://armdojo.com/products/feetech-sts3215-metal-servo-horns-25t,ArmDojo,2026-10-26,indicative,~10,ships with horns/servos,buy M2 kit
connectors,JST-XH 2.54mm kit w/ pre-crimped 22AWG leads 74+40pc,XH-KIT,Keszoox,1,22.73,https://www.amazon.co.uk/Keszoox-Connector-Pre-Crimped-Housing-Adapter/dp/B0BWVP8BDD,Amazon UK,2026-10-26,verified,190,"servo-bus power splits, sensor lines; no crimper needed",JST-PH pre-wired leads £0.50-0.75 ea (Component Shop)
connectors,JST-PH 2.0mm pre-wired leads 10prs,PH2-22AWG,generic,1,8.40,https://www.amazon.co.uk/10Pairs-Silicone-Connector-Battery-Inductrix/dp/B0D5RB3RD1,Amazon UK,2026-10-26,verified,~40,battery+small signal leads,OdicForce JST-XH leads £0.90
wire,Silicone wire kit 20AWG 6x7m + shrink + ties,20AWG-KIT,Plusivo,1,17.49,https://uk.robotshop.com/products/plusivo-20awg-hook-up-wire-kit-6-colors-7m-each,RobotShop UK,2026-10-26,verified,~400,"main power runs; kit includes heat shrink+ties",Fermerry 20AWG £11.19 Amazon; 22-28AWG kit £15.05 (Grelly)
wire,Silicone wire 22-26AWG assorted,22AWG,generic,1,12.00,https://www.amazon.co.uk/,Amazon UK,2026-10-26,estimate,~200,servo signal extensions,from Plusivo kit above
consumables,Heat shrink assortment box,HS-BOX,generic,1,6.00,https://www.amazon.co.uk/,Amazon UK,2026-10-26,estimate,~100,all solder joints,often bundled in wire kit
consumables,Cable ties + spiral wrap,CT-100,generic,1,4.00,https://www.amazon.co.uk/,Amazon UK,2026-10-26,estimate,~50,harness dressing,cable raceways printed instead
consumables,Nylon/PTFE flat washer kit M2-M10 640pc,NW-640,Sutemribor,1,8.00,https://www.amazon.co.uk/Sutemribor-Washers-Screws-Bolts-Assorted/dp/B0CNYKW9G2,Amazon UK,2026-10-26,verified,~150,joint friction washers + screw-head load spread,PTFE washer packs ~£5-8
consumables,Threadlocker Loctite 243 5-10ml,243,Loctite,1,7.00,https://www.screwfix.com/,Screwfix/Amazon,2026-10-26,indicative,~15,metal-metal threads only (never on plastic or inserts),2021 distributor list: £7.95/24ml
consumables,Dielectric/silicone grease small,GREASE,generic,1,4.00,https://www.amazon.co.uk/,Amazon UK,2026-10-26,estimate,~20,joint sliding faces (optional),skip v1
```

**Estimated hardware+filament subtotal: ≈ £100–120** (one robot, with spares baked in via kit sizes).

---

## 4. Servo sourcing — UK-friendly channels

**Target actuator class:** 7.4 V serial smart servos with position/temp/load feedback (per brief). Three credible families:

| Servo | Spec | UK price each (×12 qty) | Supplier | URL | Type |
|---|---|---|---|---|---|
| **Feetech STS3215-C001** 7.4 V, 19 kg·cm stall, 12-bit mag encoder, metal gears, dual shaft, 25T | The de-facto LeRobot/OpenDuck standard | £19.65–20.20 | OnBuy UK | https://www.onbuy.com/gb/p/sts3215-c001-19kg-74v-dual-axis-ttl-string-servo-ttl-serial-bus-robot-servo-for-so-arm100-robotic-arm~p277045569/ | verified |
| same | | £22.31 | eBay UK (CN stock) | https://www.ebay.co.uk/itm/205649410600 | verified |
| same | | €19.80 (~£17) | RobotShop EU | https://eu.robotshop.com/products/feetech-74v-19kg-magnetic-encoding-servo-sts3215-c001 | verified |
| same, 6-pack | | **~£6.85/ea** (£36.59+£4.48 ship, US/CN stock) | eBay UK | https://www.ebay.co.uk/itm/277520581660 | verified |
| **Feetech STS3215-C018** 12 V, 30 kg·cm stall | More torque; needs 3S/12V rail — conflicts w/ 2S plan | £24.32–25.00 | uk.robotshop.com / rchobby-models.co.uk | https://uk.robotshop.com/products/feetech-12v-30kgcm-magnetic-encoding-servo-sts3215 | verified |
| **Dynamixel XL330-M288-T** (12 V) | lighter duty | £27.20 inc VAT (£22.67 ex) | robotis.co.uk (RoboSavvy UK) | https://robotis.co.uk/dynamixel-catg/dynamixel-x/xl-series.html | verified |
| **Dynamixel XL430-W250-T** | 12 V, 1.5 N·m stall | £27.20 inc VAT | robotis.co.uk | https://robotis.co.uk/dynamixel-xl430-w250-t.html | verified |
| **Hiwonder LX-15D** 17 kg·cm | RGB, dual port | €17.90 + €19.95 UK shipping | openelab.io | https://openelab.io/products/lx-15d-bus-servo | verified |
| Hiwonder LX-224 20 kg / LX-824 17 kg | potentiometer feedback (not mag encoder) | $15.99 / $13.99 + shipping | hiwonder.com | https://www.hiwonder.com/products/lx-224 | verified |
| Waveshare/generic 20 kg·cm bus servo (ST-series compatible) | | £21.20 | The Pi Hut | https://thepihut.com/products/serial-bus-servo-20kg-cm | verified |
| Feetech STS3032 4.5 kg·cm 6 V | small — head/antenna joints | £24.30–29.45 | rchobby-models.co.uk | https://rchobby-models.co.uk/feetech-sts3032-c036-6v-dual-shaft-ttl-servo | verified |

**Bus adapter / programmer:** Waveshare Bus Servo Adapter (A) — USB-C + UART, drives whole daisy chain — **£10.90 Amazon UK** (https://www.amazon.co.uk/Waveshare-Serial-Servo-Driver-Board/dp/B0CJBKQ8LJ); FeeTech FE-URT-2 official programmer £13.14 RobotShop (https://uk.robotshop.com/products/feetech-fe-urt-2-usb-to-ttl-485-bus-programmer).

**Channel guidance:**
- **Best value:** eBay/AliExpress multi-packs of STS3215-C001 (~£7–14/servo in 6-packs). Lead time 1–3 weeks; **AliExpress collects UK VAT at checkout for orders <£135 — no surprise fees on delivery** (https://www.aliexpress.com/s/blog-ssr/article/navigating_aliexpress_tariffs_a_complete_guide_to-481062). Over £135, courier collects VAT + duty + ~£10–15 handling.
- **UK stock, next-day-ish:** RC Hobby-Models, The Pi Hut, OnBuy, Amazon UK (~£20–29/servo).
- **Dynamixel:** RoboSavvy/robotis.co.uk is genuine UK stock — XL330/XL430 ~£27 is surprisingly competitive, but they're 11–12 V parts → would force a 3S rail. Flag to electronics workstream; if we stay 7.4 V, Feetech wins.
- **Budget-reality check:** 12× STS3215 @ ~£8–14 (CN multi-pack) = **£85–170**; @ UK single prices = £240–350 → **servo channel choice alone decides whether we hit <£320**. Recommend BOM baseline = CN multi-pack ~£100 + 1 spare, UK single-unit as expedient alternative.

---

## 5. PCB fabrication — realistic UK costs

- **JLCPCB:** 2-layer ≤100×100 mm, qty 5 = **$2** (~£1.60). Shipping to UK: Global Standard Direct Line from **$1.50**, EuroPacket **$6.50**, DHL ~**$21.50** (discounted rates, ≤5 boards ≤100×100). **All-in for 5× 50×80 mm boards: ≈ £4–8 economy, ~£20 express.** For UK orders <£135 JLCPCB collects VAT at checkout → no doorstep fees. Sources: https://jlcpcb.com/cheapest-PCB-way , https://chiptron.eu/jlcpcb-reduces-shipping-costs-pcb-order-with-shipping-worth-bad-beer/ , https://jlcpcb.com/help/article/customs,-duties-and-taxes
- Gotcha (EEVblog, verified anecdote): combining multiple designs in one cart inflates shipping disproportionately — **order each design separately** (~£7.78/5-board set delivered).
- **PCBWay:** comparable (~$5/5 boards + similar shipping; slightly higher typical). Indicative.
- **Qty 10–20 per-unit:** JLCPCB boards land ~**£0.50–1.50/board** at qty 10–20 economy (discount shipping tiers apply to qty ≤5; standard shipping above — estimate).
- UK fab alternative: ~£30/board at qty 5 — 10–20× JLC (RISC OS forum quote). Only if lead-time-for-sovereignty matters.
- **Assembly:** keep it hand-solderable (through-hole/0805+); JLCPCB SMT assembly doubles lead time and adds ~$8 setup + parts — not needed for a 1-board power/distribution PCB.

---

## 6. Battery sourcing (UK)

| Option | Detail | Price | Supplier/URL | Type |
|---|---|---|---|---|
| 2S LiPo 2200 mAh 30C | ~112 g, hobby standard | £15.50–16.99 | ManiaX modelhelicopters.co.uk / Radient activescalemodels.co.uk | verified (https://modelhelicopters.co.uk/products/maniax-7-4v-2200mah-30c-lipo-rx-battery-pack-mx2200-2s-30-rx-mx2200-2s-30-rx) |
| 2S LiPo 1300–1800 mAh | lighter | £12.99–15.99 | pegasusmodels.co.uk | verified |
| 2S1P 18650 Li-ion pack 3500 mAh w/ protection PCB | ~100 g, safer chemistry, +USB-charge-friendly | £17.99 | ampsplus.co.uk | verified (https://www.ampsplus.co.uk/ampsplus-2s1p-7-4v-8-4v-3500mah-battery-pack) |
| 2S1P 18650 2600 mAh w/ BMS + JST-PH | drop-in | £16.99 | Amazon UK (Aolikes) | verified |
| DIY: 2× NCR18650B (3400 mAh) + 2S BMS | Open Duck Mini's approach; needs spot welding or holders | 2×£4.45 + £2.90 | micronradiocontrol.co.uk + kunkune.co.uk | verified (https://www.micronradiocontrol.co.uk/liion.html , https://kunkune.co.uk/shop/uncategorized/2s-8a-7-4v-8-4v-18650-li-ion-lithium-battery-charger-protection-board-bms/) |
| Balance charger B3 (2–3S) | basic, UK plug | £6.98–17.99 | eBay/kombatkit/seriousrc | verified |
| iMAX B6 clone | multi-chemistry 80 W | £25.99 | boatchargesolutions.co.uk | verified |
| LiPo safe charging bag | | ~£6–10 | Amazon UK | estimate |

**Recommendation:** runtime target ≥45 min at ~15–25 W system draw → need ~15–20 Wh → **2S LiPo 2200 mAh (16.3 Wh) or 2S 18650 (19–25 Wh)**. 18650 pack preferred for a *mascot handled by the public* (Li-ion cell + PCB protection is safer than a soft LiPo pouch), quick-swap bay + XT30 (Open Duck pattern). Budget **~£35** for battery + charger if the builder has neither.

---

## 7. Tools a hobbyist needs (assume absent → cost to acquire)

| Tool | Price | Supplier/URL | Type | Needed for |
|---|---|---|---|---|
| Soldering iron (Pinecil V2, USB-C PD) | £50–68 | testclips.co.uk / findsworth.co.uk | verified | all solder joints |
| Soldering iron (basic 60 W mains kit alternative) | £15–25 | Amazon UK | estimate | budget option |
| Heat-set insert tip adapter (LDO, fits standard iron) + 50× M3 inserts | £6.95 | onetwo3d.co.uk | verified | inserts |
| Pinecil insert tip set M2–M8 | £19.99 | testclips.co.uk | verified | inserts (Pinecil owners) |
| All-in-one: Vibit 100 W iron + 451 inserts M2–M6 | £28.88 | Amazon UK | verified | iron + inserts in one |
| Hex driver set 1.5/2/2.5/3 mm | £10.79 | emodels.co.uk | verified | M2.5/M3 socket heads |
| Digital calipers 75–150 mm | £15.86–32 | bolthole.co.uk / Toolstation / Machine-DRO | verified | hole/bearing fit checks |
| Wire strippers + flush cutters | ~£8–12 | Amazon UK | estimate | harness work |
| LiPo charging bag | ~£6–10 | Amazon UK | estimate | safe charging |
| Multimeter (basic) | ~£10–15 | Amazon UK | estimate | polarity/continuity |
| JST-XH crimper (SN-28B/IWISS style) | ~£12–18 | Amazon UK | estimate | only if not using pre-crimped leads |
| Hardened nozzle (for CF filament) | £5–15 | 3DJake/printer vendor | indicative | only if printing CF |
| Electric screwdriver (low torque) | ~£15–25 | Amazon UK | estimate | optional — ToddlerBot recommends |

**Full tool budget if starting from zero: ~£120–170** (or ~£70 with budget options). Most buyers already own ~half.

---

## 8. Assembly & serviceability design patterns (from comparable open robots)

Patterns worth copying wholesale:

1. **Modular limb assemblies** (Open Duck Mini): each leg = self-contained chain of 5 servo+bracket subassemblies bolted to a trunk; a leg unbolts with ~6 screws. Feet = separate TPU sole part. → Adopt: legs/head as sealed modules on the servo bus connector.
2. **Configure servos BEFORE assembly** (Open Duck guide): set IDs/baud via the £10.90 Waveshare adapter before anything is bolted in — every servo tested individually on the bench. Bake this into our assembly doc as step 0.
3. **Servo bus daisy-chain with strain relief:** servos ship with short leads; route through printed cable channels with **slack loops at every flexing joint** (hip pitch/knee are the worst). Never route a cable across a joint axis so it wraps tight — this is the #1 observed failure class on small bipeds (see §9).
4. **Heat-set inserts at every serviceable joint** (both reference builds): nothing threads into raw plastic.
5. **Battery user-replaceable from outside** (Open Duck: battery lid + XT30 + switch): no tools needed to swap the pack.
6. **Zero-point/mechanical calibration aids** (ToddlerBot "plug-and-play zero-point"): print alignment jigs/witness marks so joints go together at known angles; document a cal pose.
7. **Electric screwdriver for ~100 screws** (ToddlerBot): assembly ergonomics matter — our BOM should keep total screw count ≤ ~80.
8. **Panels before guts:** cosmetic shells attach to a structural frame LAST via M3 inserts — electronics/servo access without peeling cosmetics.
9. **No glue in load paths**; PTFE/nylon washers as bearing surfaces on sliding joint faces; threadlocker only on metal-metal.
10. **Sacrificial-by-design parts:** TPU foot soles and horn-side link shells are the drop-fuses — cheap, fast to reprint, designed to absorb abuse before servo gears do.

---

## 9. Consumables & spares — what breaks first

| Rank | Failure point | Why | Repair procedure | Spare kit cost |
|---|---|---|---|---|
| 1 | **Servo cable fatigue at hip/knee flex** | constant flex cycles; thinnest copper on the robot | cut dead section, re-terminate (servo leads are JST); add slack loop + heat-shrink strain relief; swap lead (~£1) | 5× spare leads ~£5 |
| 2 | **Plastic servo horn / spline strip** | drop + stall torque | replace with 25T metal horn (£3–5), M3 centre screw + threadlocker | 2× metal horns ~£8 |
| 3 | **Servo gearbox tooth strip** (esp. hip pitch/knee — highest load, drop shock) | overload/fall | gearbox-swap kit or whole-servo swap; STS3215 gear sets exist ~£5–9 on CN marketplaces (indicative); whole servo ~£8–22 | **1–2 spare servos £8–44** |
| 4 | **TPU foot sole wear / foot shell cracks** | floor contact, falls | reprint sole (30–40 g, ~2 h); keep STL+profile | ~£1 filament |
| 5 | **Heat-set insert pull-out / boss crack at servo mounts** | over-torque or under-sized boss | oversize boss ≥9 mm; if pulled, epoxy a new insert, or step up to M3 in a redesigned hole | ~£1 |
| | (runner-up) JST connector latch fatigue; LiPo swelling (age) | repeated swaps; charge abuse | replace connector; retire pack in salt-water discharge per LiPo disposal practice | spare pack £16–18 |

**Sensible spare kit ≈ £35–60:** 1–2 spare servos, 2 metal horns, ~5 servo leads, 1 extra TPU sole print's worth of filament, handful of inserts+screws (already surplus from kits).

---

## Cost roll-up (12-servo build, indicative)

| Line | £ |
|---|---|
| Servos 12× STS3215 (CN multi-pack) + 1 spare | ~100–110 |
| Bus adapter | 10.90 |
| Filament (PETG-CF + PLA + TPU) | ~12–15 |
| Hardware kit (§3 minus filament) | ~55–70 |
| Battery + charger | ~33–35 |
| PCB (JLCPCB economy) | ~5–8 |
| **Build total** | **≈ £215–250** |
| Tools if starting from zero | +£70–170 |

**Fits the <£320 target with ~£70+ margin** — provided servos come from the CN multi-pack channel. UK-singles servo sourcing alone (~£300+) would blow the budget; flag in brief risk register.

## Open questions for other workstreams
- **Electronics:** 7.4 V Feetech vs 12 V Dynamixel rail decision changes every servo/BMS line item.
- **Engineering:** confirm joint torque needs — if hip/knee need >19 kg·cm stall, STS3215-C001 may be undersized → consider 12 V C018 variant (30 kg·cm) or Hiwonder HX-20L class; that pushes bus to 12 V.
- **Validation:** instrument a 2-week clamped-joint creep coupon test (M3 screw + washer into PETG-CF boss) to sanity-check §1.2 before freezing joint geometry.
