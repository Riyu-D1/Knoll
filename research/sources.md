# Sources & Evidence Register — Knoll Mk1

**Access date for all:** 2026-10-26. Confidence: **V**=verified primary source · **L**=likely/strong inference · **E**=estimate/indicative · **U**=unverified claim noted for completeness.

---

## A. Reference product (Microduck)

| Claim | Source | Conf |
|---|---|---|
| 25 cm, ~780 g, 15 motors, camera+LiDAR(8×8 ToF)+2 IMU, 50 Hz loop, $399 pre-tax/ship, 4 colourways, pre-order Aug 27 2026, ship before Christmas 2026 (later revised: new orders after ~April 2027) | pollen-robotics.com/microduck + /press-kit + store | V |
| NOT open hardware — open source covers software only | press kit "Open source = software" | V |
| RK3566 (Radxa Zero 3W), Armbian; 1 GB RAM/32 GB storage; removable NP-F550 ≈1 h battery; 2× NFC antennas; gamepad included | robotd-design.md; store spec (Agent A) | V/L |
| Rust daemon workspace; JSON-RPC over unix sockets; robotd owns bus+safety; signed A/B updates w/ health-gate rollback; vetbook.json lifetime log | microduck repo docs/design/architecture.md, robotd-design.md | V |
| 15 servos + IMU on ONE UART @1 Mbps Dynamixel protocol v2; IMU = custom imu_to_dxl board serving SFLP quaternion (BNO08x-class) | robotd-design.md §1.1 | V/L |
| Legs = 5 DOF (hip_yaw, hip_roll, hip_pitch, knee, ankle); head 4 (neck_p, head_p, head_yaw, head_roll); 14 policy joints + beak | microduck_rl README joint layout | V |
| XL330-family servos, overvolted on raw 2S (6.6–8.2 V vs 6.0 V rating; shutdown bit cleared) | microduck_rl BAM M6 note + Agent A findings | V |
| Training: mjlab (MuJoCo Warp) + rsl_rl PPO; ONNX w/ baked normalizer; BAM M6 actuator model; ±1–2° backlash hinge; DR set incl. 60–120 ms cmd delay, V sag, CoM ±15 mm, IMU misalign 6° | microduck_rl README + AGENTS.md + src files | V |
| VelStand recovery recipe: experts distilled; spawn curriculum; 93–95% sim get-up after push-falls | microduck_rl docs/velstand_policy.md (via Agent E) | V (sim metric — real not independently published) |
| UK pricing: robot €340; packs €33; dev pack €99.99 | store (Agent A) | V |
| Hardware files CC BY-SA-NC where referenced; mech/elec CAD unreleased; elec_RPI_Robot_HAT IS open (Apache-2.0, KiCad, 4-layer) | microduck_rl LICENSE note; Agent A | V |
| Community clones: fanhao375/microduck-replica (15× Feetech HD-1910, STM32G031 imu_to_dxl clone — walk/roll/get-up verified); Rhoban microban (30 cm, 19× XL330-M288, Pi Zero 2 W, ~$550–600, full BOM) | Agent A notes-microduck.md | L |

## B. Open Duck Mini & community prior art

| Claim | Source | Conf |
|---|---|---|
| ODM v2: ~42 cm, 14× STS3215 7.4 V + 2×9 g, Pi Zero 2 W, BNO055, 2 foot switches, 2S 18650+BMS, ~500 g PLA 15% infill, BOM <$400 (community ~$200) | github.com/apirrone/Open_Duck_Mini; opensourcerobotics.dev/robots/open-duck-mini | V |
| ODM control: 50 Hz ONNX on PiZ2W; actions = home+a·0.25 slew 5.24 rad/s; servo kp=30 P-only; ~77-D obs; imitation reward via PlaCo gait polys; BAM-identified feetech_sts3215_7_4V params → MJCF | Open_Duck_Playground joystick.py/v2_rl_walk_mujoco.py (Agent E) | V |
| Sim2real failure case: sim-winning policy failed on HW — loose screws→asymmetric backlash, joint-zero mismatch vs home keyframe; "SysID > DR for systematic bias" | zhenghaoxu.com/duck%20writeup.pdf (Purdue) | V |

## C. Actuators (datasheets/prices)

| Claim | Source | Conf |
|---|---|---|
| STS3215-C001: stall 19.5 kg·cm @7.4 V; **rated 5 kg·cm @7.4 V**; input 4–7.4 V; 1.91 N·m stall; 52 rpm; 2.5 A stall; 12-bit mag enc; 55 g; life >100k @1/5 stall | Feetech datasheet A/0 (feetech.cn PDF + core-electronics translated) | V |
| STS3215 product page lists rated 6.5 kg·cm @6 V vs datasheet 4 — **vendor self-inconsistency; datasheet used** | feetech.cn product page | V (conflict documented) |
| STS3215-C018 12 V: stall 30 kg·cm, **rated 10 kg·cm**, £24.32 | feetech.cn + uk.robotshop.com | V |
| ST3020: 25 kg·cm @12 V, **input 6–14 V**, 40.2×20.2×40 mm, £19.40; Feetech ST-3020-C001 wiki 20 kg·cm @7.4 V | waveshare.com/wiki/ST3020_Servo + ftservo.github.io + thepihut.com | V (rated torque unpublished — E) |
| STS3032: 4.5 kg·cm stall/1.5 rated @6 V, 20 g, £24.30–29.45 | evelta datasheet PDF + rchobby-models.co.uk | V |
| XL330-M288: 0.52 N·m stall @5 V, 18 g, £27.20; M077: 0.215 N·m £22.19 | Robotis e-manual + robotis.co.uk (RoboSavvy) | V |
| XL430-W250: 1.5 N·m stall @12 V, 57 g, £27.20 (needs 3S) | e-manual + robotis.co.uk | V |
| XC430-W240: 1.9 N·m, metal gears, £111.38 | e-manual + robosavvy.co.uk | V |
| LX-16A/LX-15D/LX-224/HTS-35H: stall-only figures, potentiometer feedback, fixed 115200 baud, ~£8–18 | hiwonder.com + eBay UK | V |
| LDX-218 PWM ~£9 no feedback | hiwonder.com | E/L |
| Servo price channels: STS3215 £6.85–14 in CN 6-packs; £19.65–29 UK singles; AliExpress collects UK VAT <£135 | eBay/AliExpress/RobotShop/OnBuy listings | V |
| rustypot (Pollen's Rust servo lib) supports STS3215/STS3250/SCS0009/SM8512BL + Dynamixel | github.com/pollen-robotics/rustypot | V |
| SO-ARM101 uses 6× STS3215 | Seeed datasheet bundle cdn.robotshop.com | V |

## D. Electronics & power

| Claim | Source | Conf |
|---|---|---|
| Pico 2 W £5.20 ex VAT (£6.24 inc); Pico 2 £4–4.75 | rapidonline.com, shop.pimoroni.com | V |
| Pi Zero 2 W £12–14.40; 0.6 W idle/~2.9 W max; intermittent stock | thepihut.com, shop.pimoroni.com, cnx-software.com power measurements | V |
| BNO085 breakout £26.99–28.40; BMI270 £17.80; ICM-20948 £21.50 | thepihut.com, shop.sb-components.co.uk | V |
| Half-duplex servo bus: SN74LVC1G126+1G125, 3.3 V, GPIO TXEN; 5264-3A connectors; SMAJ TVS | Waveshare open schematics (files.waveshare.com Bus_Servo_Adapter_A.pdf) | V |
| MP1584 fixed-5V 3A £0.76–3.64; AO4407 rev-pol; XT30; battery options £9.95–17.99 | bitsboxuk.com, 247geek.co.uk, howesmodels.co.uk, scotiarc.co.uk, ampsplus.co.uk, kunkune.co.uk | V/E |
| JLCPCB 2-layer qty5 ~£4–8 landed; collects UK VAT <£135 | jlcpcb.com + chiptron.eu shipping data | V |

## E. Control/RL/recovery literature

| Claim | Source | Conf |
|---|---|---|
| MuJoCo free Oct 2021, Apache-2.0 May 2022 | deepmind.google blog; github.com/google-deepmind/mujoco | V |
| mjlab = MuJoCo Warp + Isaac-Lab-style API; microduck trains ~1–2 h @4096 envs; HF Jobs offload | github.com/mujocolab/mjlab + microduck_rl | V |
| BAM actuator models M1–M6 + pendulum SysID; pre-id params incl. feetech_sts3215_7_4V, xl330 | arXiv:2410.08650; bam.readthedocs.io; github.com/Rhoban/bam | V |
| FRASA: CrossQ get-up, CPU MuJoCo 13–37 min, real robot 2.14 s prone/2.68 s supine vs champion-KFB 3.15/5.06 s; joint-increment actions rate-robust (train 20 Hz, deploy 100 Hz) | arXiv:2410.08655; github.com/Rhoban/frasa (ICRA 2025) | V |
| HumanUP: two-phase curriculum, 78.3% real G1 get-up | arXiv:2502.12152 (RSS 2025) | V |
| UHG: one policy, 7 morphologies, zero-shot | github.com/utra-robosoccer/unified-humanoid-getup | V |
| NimbRo scripted get-up (classify pose→keyframe) since 2006 | ais.uni-bonn.de/nimbro/papers/IAS9.pdf | V |
| Disney BDX: RL conditioned on animator commands → mascot-quality motion | arXiv:2501.05204 (RSS 2024) | V |
| mujoco_playground: biped envs + Go1 fall-recovery, zero-shot sim2real demos | arXiv:2502.08844 | V |
| TorchRL MicroDuckEnv + closed-form gait baseline | docs.pytorch.org/rl/stable/tutorials/microduck.html | V |
| Isaac Gym deprecated; Gazebo Classic EOL Jan 2025 | developer.nvidia.com; gazebosim.org | V |

## F. Manufacturing & materials

| Claim | Source | Conf |
|---|---|---|
| PLA/PETG/ASA measured properties (stiffness 3300/1900/2300 MPa; layer adhesion 55/46/29%; Charpy 5/8.6/18 kJ/m²) | cnckitchen.com/blog/comparing-pla-petg-amp-asa-feat-prusament | V |
| Creep under clamped load: all filaments stress-relax; PETG worst-tensile-creep reports contested | mytechfun.com/video/143; 3dprinting.stackexchange.com/19813; MDPI Polymers 17(15)2075 | V (conflict documented) |
| Voron structural print spec (4–6 walls, 40–60% infill, gyroid) | docs.siboor.com Voron 2.4r2 build guide | V |
| Hole shrink 0.1–0.2 mm; fits ±0.1–0.3 mm on hobby FDM; press-fit guidance | help.makelab.com; machinistcalcs.com; 3dprintcalcs.uk | V |
| Filament UK prices: eSUN PETG-CF £20.99/kg, PLA £10.99, TPU £14.99, PAHT-CF £45.99 | esun3dstore.uk; uk.store.bambulab.com | V |
| Hardware UK prices: M3 kit £8.40, inserts £5/50, 6700ZZ £5.65/8, MR126ZZ £0.57, dowels ~£0.15, 25T horns £4.99 | monkeyjamsshed, jb3d.uk, 3djake.uk, rapidonline, ebay GWR, rccontrolfreak | V |
| Batteries: 2S LiPo 2200 £15.50–17; 2S1P 18650 £16.99–17.99; B3 £7–18 | modelhelicopters.co.uk, ampsplus.co.uk, Amazon UK, ebay | V |
| Open Duck Mini assembly patterns (bench-config servos, modular limbs, battery swap, TPU soles) | github.com/apirrone/Open_Duck_Mini guide | V |
| ToddlerBot: ~10 h/plate prints, electric screwdriver for ~100 screws, zero-point jigs | hshi74.github.io/toddlerbot | V |

## G. Conflicts & unresolved

| Topic | Conflict | Resolution used |
|---|---|---|
| STS3215 rated torque | feetech.cn page 6.5 kg·cm vs datasheet 4 kg·cm | datasheet (conservative) |
| Creep: PETG vs PLA worst | community contradictory | engineering rule: metal carries clamp load, material-agnostic |
| Microduck "15 motors" vs 14 policy joints | press kit counts beak servo; policy controls 14 | both reported |
| "LiDAR" marketing vs actual 8×8 ToF | product page says LiDAR; architecture doc says ToF matrix | ToF (VL53L5CX-class) |
| Microduck HW licence vs "files not released" | CC BY-SA-NC declared + press kit says closed | files unreleased + NC regardless → clean-room |
| ST3020 continuous torque | unpublished | estimate 20–30% stall + P1.4 bench gate |

## H. Never-invented / unknown (explicitly unverified as of 2026-10-26)

Microduck exact servo variant, battery chemistry/capacity, camera model, second IMU location, real-world fall-recovery success rates, retail BOM cost; ST3020 continuous rating; our robot's any measured performance (nothing built yet).
