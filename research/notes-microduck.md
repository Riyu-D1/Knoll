# Microduck — deep research notes

**Analyst:** research workstream · **Date accessed throughout:** 2026-10-26
**Scope:** Pollen Robotics / Hugging Face "Microduck" — product, firmware repo, RL stack,
ancestor projects (Open Duck Mini, microduck_runtime, microban), community reconstructions,
licensing, UK availability. Builds on `design/shared-design-brief.md`; the baseline rows
already verified there (25 cm / <800 g / 15 motors / 50 Hz / $399 / "not open hardware")
are not re-litigated here — this file adds what is underneath them.

**Reading guide to confidence:**
- `verified` — read directly from Pollen's own source code / official pages, or a datasheet.
- `likely` — strong convergent evidence, at least two independent paths, but not an official statement.
- `unverified` — single-source, community-derived, or inference. Flagged inline.

---

## 0. TL;DR — the ten facts that most affect MASCOT

1. **Motors: 15× Robotis Dynamixel XL330-M288-T** (Dynamixel Protocol 2.0, 1 Mbps TTL
   half-duplex, one UART). Sub-variant not officially named; identification rests on the
   BAM identified model + code comments + community visual ID. ~£25–42/unit retail →
   **15 units cost more than the $399 robot.** Motor choice is the dominant cost lever.
2. **They run the XL330 over-volted:** servo rail = raw 2S Li-ion (6.6–8.2 V used range)
   vs the XL330's rated 3.7–6.0 V; the input-voltage shutdown bit is deliberately cleared
   in firmware. Cheap way to get torque, real wear/heat cost.
3. **Compute:** alpha/dev = off-the-shelf **Radxa Zero 3W** (RK3566, quad A55, 0.8 TOPS
   NPU) + Pollen's own **"RPI Robot HAT"** — which is **fully open source** (KiCad,
   Gerbers, BOM, STEP; Apache-2.0). Production "beta" = custom **Seeed-made RK3566
   board** (eMMC, Yocto OS). So the compute is commodity; only two small boards are custom.
4. **Battery:** off-the-shelf **Sony NP-F550** camcorder pack (2S Li-ion, ~7.2 V, user-
   swappable), ~1 h runtime, **no fuel gauge, no ADC** — SoC read from the servos.
   No on-board charger on the HAT; charging is external (charger pack sold separately).
5. **"LiDAR" is a tiny ST multizone ToF:** **VL53L5CX** (field units) / **VL53L8CX**
   (production board), 8×8 zones, ~15 Hz, used for gimmicks (theremin) not locomotion.
6. **Two IMUs:** control IMU = **LSM6DSV16X** on a custom "imu_to_dxl" board that is a
   *Dynamixel slave at ID 200 on the servo bus* (on-chip SFLP quaternion). Head IMU =
   **BMI088** on the HAT (alpha, unused by default) / second LSM6DSV16X on beta's "face
   board". Camera = **IMX219** (alpha) / **GC2093** (beta).
7. **Control:** single 50 Hz Rust loop (`robotd`), 2 bus transactions/tick, ONNX policies
   `obs[1,61] → act[1,14]`, targets = home_pose + 0.9×action, low-pass 0.5 head / 0.7 legs,
   P-gain 200 (I=D=0). Whole contract documented → **the obs/action interface is
   reproducible** (community policies already exist on HF Hub).
8. **Training stack:** `microduck_rl` = **mjlab** (MuJoCo Warp, CUDA GPU) + **PPO (rsl_rl)**
   + **BAM "M6" identified XL330 actuator model** (voltage law, back-EMF, Coulomb/Stribeck,
   load friction) + domain rand (battery 6.5–8.2 V, sag, 3–6-step delay, friction scale)
   + ±1° backlash-hinge variants. NOT stable-baselines3, NOT plain MJX-Playground.
9. **Lineage is public:** Open Duck Mini v2 (apirrone) = 14× **Feetech STS3215** + BNO055 +
   Pi Zero 2W, ~42 cm/2.1 kg, ~€398 BOM, public Onshape; Rhoban **microban** = 19×
   XL330-M288-T + same HAT + Pi Zero 2W, ~$550–600, full public BOM. Both prove the
   capability class on different actuators. A Chinese community (**microduck-replica**)
   has already cloned Microduck mechanics onto **15× Feetech HD-1910** (~¥95 ≈ £10 ea)
   and validated walk + forward-roll + get-up on hardware.
10. **Licensing:** software Apache-2.0; **MJCF/STL meshes in microduck_rl are CC BY-SA-NC**
    (study/reference OK; do NOT copy into our product). `imu_to_dxl` firmware, mechanical
    CAD, and the beta board design remain closed.

---

## 1. Reference spec table

| Feature | Published / derived value | Evidence URL | Confidence | Implications for our design |
|---|---|---|---|---|
| SoC | Rockchip RK3566 (quad Cortex-A55, Mali-G52, 0.8 TOPS INT8 NPU) | github.com/pollen-robotics/microduck README ("handful of daemons on a Rockchip RK3566") | verified | Pi-class A55 compute is enough for 50 Hz ONNX + 720p WebRTC; cheaper SoM or Pi Zero 2W works if we drop vision |
| Compute board (alpha/dev) | Radxa Zero 3W (stock, Pi-Zero form factor, 65×30 mm), Armbian, vendor kernel 6.1 | robotd-params/src/board.rs ("Radxa Zero 3W with the prototype's HAT"); docs/robot/install-dev.md; @tspy teardown (independent) | verified | Same board buyable in UK (~£30–45); runs the official runtime as-is if we match wiring |
| Compute board (production "beta") | Custom RK3566 board manufactured/designed with **Seeed** (`seeed,microduck` DT compat), 1 GB RAM + 32 GB eMMC | board.rs comment "Seeed's RK3566 main board"; store spec "Rockchip RK3566 + AI accelerator, 1GB RAM + 32GB storage"; microduck_yocto machine `microduck-beta` | likely (which board ships at retail unconfirmed) | Pollen moved off the hobbyist board for production; our DIY design can legitimately stay on a stock SBC |
| Actuator | 15× Dynamixel XL330 (Protocol 2.0, TTL half-duplex, 1 Mbps) | duck-control/src/bus.rs `Xl330Controller`; deploy/robotd.toml | verified (family) | The protocol stack (rustypot) is Pollen's own Apache-2.0 crate — reusable |
| Actuator sub-model | XL330-**M288-T** (288.35:1, 18 g, 20×34×26 mm, stall 0.42/0.52/0.60 N·m @3.7/5/6 V, rated 3.7–6.0 V) | microduck_rl BAM cfg `motor_name="xl330"` → BAM's identified model is XL330-M288-T (github.com/Rhoban/bam); X post @Allyakutaku; e-manual robotis.com/docs/en/dxl/x/xl330-m288/ | likely | "Enough torque at 18 g" is rare — Unitree S288 (19.5 g, same ratio) is the closest alternative but is 3S/12.6 V + own protocol |
| Servo supply | Raw 2S pack straight to servo rail — **over-volted** (6.6–8.2 V used; cleared `shutdown` input-voltage bit; default Max Voltage Limit 7.0 V stays) | duck-control/src/model.rs comments; robotd-design.md §2.1; replica's reading of official dynamixel.kicad_sch (J13/J14 → +BATT) | verified | Don't copy this: pick 7.4 V-rated servos (STS3215 class) and skip the over-volt liability |
| Bus topology | 16 devices on one UART: right leg 10–14, left leg 20–24, neck/head/mouth 30–34, IMU board 200 | docs/design/robotd-design.md §1.1; bus.rs | verified | One 1 Mbps half-duplex UART carries 15 servos + IMU at 50 Hz — proven; simplifies our wiring |
| DOF breakdown | 5 per leg (hip yaw/roll/pitch, knee, ankle) + 4 head (neck_pitch, head_pitch, head_yaw, head_roll) + 1 mouth; **policy controls 14, mouth excluded** | duck-control/src/model.rs (JOINT_NAMES, MOUTH_INDEX=9); robotd-design.md §2.2 | verified | Validates our 10–14 DOF target; a beak/grabber joint can live outside the policy |
| Joint ranges | hip_yaw −25°/+30°; hip_roll ±22°; hip_pitch/knee/ankle/head_pitch ±90°; neck_pitch −90°/+60°; head_yaw ±170°; head_roll ±25°; mouth −5°/+30° | kinematics/assets/alpha/robot_walk.xml; model.rs MOUTH_* | verified (sim model) | Real reference numbers for DIY joint-limit choices |
| Policy contract | obs[1,61] = gyro(3)+proj_gravity(3)+joint_pos(14)+joint_vel(14)+last_action(14)+cmd(13 = twist3+head4+body6); act[1,14]; 50 Hz | robotd-design.md §2.2; robotd.toml | verified | Mirror the contract → can trial community/official ONNX policies on our hardware |
| Policy impl | ONNX Runtime ≥1.23, dlopen'd; feed-forward + explicit-state LSTM (model_api=2) supported | docs/recurrent-policies.md; robotd.toml | verified | ORT on CPU is all we need; a 61→14 MLP at 50 Hz is trivial compute |
| Shipped policies | 7 slots: walk/velstand, stand(legacy), sitstand, ground_pick, kick L/R, roulade, + roller mode; ONNX on HF Hub `pollen-robotics/microduck-policies` (Apache-2.0, ~37k dl) | robotd.toml; huggingface.co/pollen-robotics/microduck-policies | verified | Study their reward structure in microduck_rl; policies themselves are retrainable reference |
| Action post-processing | targets = home + action_scale×out (0.9 walk/0.8 roller); low-pass head 0.5 legs 0.7 (must match training); voltage_adapt scales by 7.4/V_measured | robotd.toml [policy] | verified | The low-pass is baked into the sim2real recipe — a detail DIY clones miss; copy the *method* |
| Firmware gains | Position P gain 200 (kI=kD=0 written), standing ×0.8, limp 50; knee homing_offset −512 counts (−45°) | model.rs EXPECTED_REGISTERS / KNEE_HOMING_OFFSET | verified | Shows servo-level tuning matters as much as the policy |
| Battery | Sony NP-F550 (2S Li-ion camcorder pack, 7.2 V nom.; generic ~1500–2600 mAh, ~95–102 g); removable, ~1 h life; **no gauge/ADC** — voltage via servos; auto sit+off at 6.6 V EMA | model.rs battery section; store page "Removable NP-F550 battery (approx. 1 hour)"; replica mesh analysis | verified | Commodity ~£15–30 part; user-replaceable 2S pack is a good pattern; we may add a real gauge |
| Charging | External (dual-slot charger in $39/€33 pack); no charge circuit on the HAT (`pwr_supply_charge.kicad_sch` is an orphan sheet) | replica hardware-teardown §4; elec_RPI_Robot_HAT production BOM | verified | Decide early: onboard USB-C charge (nicer UX, more PCB) vs external pack charging |
| "LiDAR" | ST VL53L5CX (rev 0x02, I²C 0x29 — "most ducks in the field") / VL53L8CX (rev 0x0C, SPI on beta), 8×8 zones, ~15 Hz | tof/src/sensor.rs; tof/vendor/{vl53l5cx,vl53l8cx} vendored ST ULD | verified | ~£6–10 module; used for gimmicks (theremin), not balance — optional for MVP |
| Control IMU | LSM6DSV16X on custom "imu_to_dxl" v2 board = Dynamixel slave, ID 200, serves gyro(6B)+SFLP quat fp16(6B) at reg 124 in the same sync_read | duck-control/src/imu.rs; robotd-design.md §1.1 | verified | Elegant (no 2nd bus) but a custom board; simpler for us: IMU on I²C/SPI direct |
| Head IMU | alpha: BMI088 on HAT (0x19/0x68, Madgwick on CPU, off by default — costs ~4% core at 100 Hz); beta: 2nd LSM6DSV16X on face board read by robotd | tof/src/imu.rs; robotd.toml [head_imu] | verified | Second IMU is for camera/gaze, not balance — droppable for MVP |
| Camera | alpha: Sony IMX219 (RPi Cam v2 class, M12 ~3.05 mm lens, ~62° HFOV, pinned 1080p30, mounted 90°-rotated); beta: GalaxyCore GC2093 (Seeed module, rkaiq AE) | mediad/src/sensor.rs; board.rs camera_sensor() | verified | IMX219 is ubiquitous (~£10–25). Vision adds ISP/NPU complexity — cost-driver |
| Audio | TLV320AIC3104 codec (0x18) + speaker + MEMS mic; pet-detect ONNX classifier listens for petting | deploy/audio/*; robotd.toml [audio]; replica BOM cross-check U2=TLV320AIC3104IRHBR | verified | Speaker+mic = personality on the cheap; a buzzer/MAX98357 does 80% of it |
| NFC | 2 antennas (head + beak); drivers exist for ST25R100 and NXP CLRC663 (st25r100_* examples suggest ST part is primary) | nfc/src/{st25r100,clrc663}.rs; store spec "2 NFC antennas" | likely (chip model) | Tag-detect accessories (ball, polaroid); low priority for MVP |
| LEDs (beta) | Face board GPIO LEDs: RGB "flashlight", camera-active, status G/R, network G/B, 3-step battery gauge | duck-ipc-proto/src/led.rs | verified (beta) | Cheap charisma; trivially included |
| Wi-Fi/BT | AIC8800 module on zero3 (Armbian); BLE for app/gamepad (btd/padd), Wi-Fi for WebRTC | board.rs DT compat `radxa,zero3w-aic8800ds2`; architecture.md | verified | Whatever SBC we pick needs BT (gamepad) + Wi-Fi (telemetry) |
| IPC | JSON-RPC 2.0 NDJSON over Unix sockets; per-daemon sockets under /run; API v23+; NOT protobuf (crate name is misleading) | duck-ipc-proto/src/lib.rs | verified | Architecture lesson: typed intents→one owning control loop; we can simplify |
| Updater | Signed releases → atomic dir swap → health-gated auto-rollback; sources: GitHub releases + HF Hub; RAUC A/B on Yocto for production | updater/src/*; microduck_yocto README | verified | OTA+rollback is a real product feature; for DIY, git+systemd units suffice |
| Thermal | RK3566 fanless: vision detector capped at 2 Hz — flat out hits 95 °C, throttles to 408 MHz | robotd.toml [duck_detector]; robotd-design.md §2.1 | verified | Compute headroom is thermal-limited; our MCU+SBC split dodges this |
| Mass | 780 g (store page; press says <800 g); MJCF model total ≈737 g; envelope ≈144×141×264 mm | store.pollen-robotics.com/products/microduck; open-microduck model-derived table | verified | Our 0.9–1.3 kg target is honest: XL330-class mass is the main enabler |
| Size | 25 cm tall | press kit | verified | — |
| Retail price | $399 USD ex-tax/ship; UK/EU charged in **EUR €340**; packs €33/€33/€99.99; ships to UK; backlog → new orders ship **after ~Apr 2027** | store.pollen-robotics.com (region selector lists United Kingdom → EUR) | verified | ~£295–340 landed + VAT ambiguity; our <£320 target sits plausibly under it; availability gap helps us |
| Openness | Software Apache-2.0; mechanical+electronic CAD closed (press kit explicit); HAT board IS open (Apache-2.0 KiCad); rl-repo meshes CC BY-SA-NC | press kit "open source = software"; elec_RPI_Robot_HAT LICENSE; microduck_rl README licence note | verified | Their STLs are reference-only (NC). Our all-open stance is a real differentiator |

---

## 2. System architecture (what the repo actually shows)

### 2.1 Repo: `github.com/pollen-robotics/microduck` (Apache-2.0, ~12.2k★, 1400 commits)

Rust workspace, no framework. Daemons (one unix socket each, JSON-RPC 2.0 NDJSON):

| Daemon | Owns | Notes for us |
|---|---|---|
| `robotd` | the 50 Hz loop, motor bus, safety, policies, `robot.health` | Only writer to the bus — borrow-checker-enforced (`safety` holds `RobotIo`) |
| `updaterd` | signed release verify/install/rollback | health gate = achieved-rate/stall/bus-error thresholds in robotd.toml |
| `configd` | Wi-Fi (NetworkManager/D-Bus), identity, pairing PIN | |
| `btd` | BLE GATT transport for a subset of the API | unencrypted by default per design docs |
| `padd` / `netpadd` | gamepad → intents (BLE/USB / UDP LAN) | pad can carry IMU head-steering (Switch-Pro-clone pads) |
| `mediad` | camera+mic pipeline, WebRTC H.264, console, `media.stream` fallback | GStreamer + Rockchip MPP hw-encode; rtpgccbwe congestion ~7.6% core |
| `tofd` | ToF sensor + head-IMU I²C bus owner | publishes 8×8 frames; nothing reads it by default |
| `nfcd` | NFC reader(s) | ST25R100/CLRC663 drivers |
| `robotctl`/`duckctl` | CLI over the same sockets / BLE from a laptop | one API for app, CLI, gamepad, scripts |

Libraries: `duck-control` (model/bus/IMU/obs/policy/safety — pure, testable),
`duck-ipc-proto` (wire types, serde only), `kinematics` (MJCF FK, head/hand chains),
`odometry` (foot-contact odom), `sounds` (synth voice, chorale), `pet-detect`,
`duck-detect` (RKNN/ONNX object det), `robotd-params` (TOML schema).

**Tick** (robotd-design.md §1.4): 50 Hz tokio interval (`MissedTickBehavior::Skip`);
read = one fast `sync_read` (prot2 0x8A) over IMU+15 servos regs 124–136 → obs →
ONNX → targets → `safety.apply` → one `sync_write`; 1 Hz slow read for bus voltage +
per-joint temperature. Servo EEPROM asserted at startup: `return_delay_time=0`,
`baud_rate=3` (1 Mbps), `pwm_slope=255`, `shutdown=52` (voltage-fault bit cleared).
Fast sync read requires **XL330 firmware ≥ v46**. Deadman 500 ms; battery-EMA empty →
graceful sit + poweroff; `limp_fall` predictive softening (gyro-extrapolated gravity,
300 ms lookahead, gain 200→50, still-detection, 600 ms pose ramp).

### 2.2 Boards & wiring (alpha, the documented one)

```
Radxa Zero 3W ──40-pin──► Pollen RPI Robot HAT ──JST-EH 3P──► 15×XL330 + imu_to_dxl(ID200)
  │  /dev/ttyS2 (UART2 M0, 1 Mbps, 3.3V TTL half-duplex; direction auto-switched on HAT)
  ├─ MIPI CSI ─ IMX219 (0x10)
  ├─ i2c3 M0 pins3/5 (400 kHz): codec 0x18, BMI088 0x19/0x68, Stemma J5→ToF 0x29
  └─ i2s3 + 12 MHz MCLK → TLV320AIC3104 → speaker / MEMS mic
NP-F550 → HAT → servos direct (+BATT, TH1 100R); buck AP63205 → 5 V for SBC; LM5050 ideal diode
```

Note: i2c3-M0 on pins 3/5 conflicts with the FUSB302 USB-C PD controller — their overlay
remuxes it, so **USB-C PD negotiation is sacrificed** (5 V dumb charging still works;
the robot is not powered that way anyway). UART2 also carries Armbian's getty by default —
must be masked.

### 2.3 Production "beta" board (partially visible in code)

`seeed,microduck` / `pollen,microduck-beta` device trees; Seeed rkaiq IQ file; GC2093
camera upright; VL53L8CX on SPI (L5 has no SPI); face board w/ LSM6DSV16X + GPIO LED
indicators (flashlight/camera/network/status/battery gauge); NFC antennas head+beak;
eMMC, Yocto image `microduck_yocto` (Rockchip BSP kernel 6.1, RAUC A/B, rauc-signed).
**Beta schematic/CAD/firmware NOT published.**

### 2.4 imu_to_dxl — the one custom piece that matters

MCU (unidentified — firmware closed) + LSM6DSV16X + half-duplex front-end, answering
Dynamixel prot2 reads at ID 200, register block at 124: gyro i16 ×3 (±500 dps,
17.5 mdps/LSB) + fp16 quaternion xyz (w reconstructed). Community reconstruction uses
STM32G031F8P6 + LSM6DSV16XTR + SN74LVC2G241 + HT7533-1 (microduck-replica `hardware/`).
For MASCOT a plain I²C IMU is simpler — but the trick means *one* sync_read feeds the
policy everything; worth remembering if we reuse their policy obs layout.

---

## 3. RL / simulation stack

### 3.1 `github.com/pollen-robotics/microduck_rl` (Apache-2.0; meshes CC BY-SA-NC)

- Framework: **mjlab** (`github.com/mujocolab/mjlab`, MuJoCo + **Warp** GPU backend) —
  needs CUDA; `--hf-jobs` path trains on Hugging Face Jobs instead of local GPU.
- Algorithm: **PPO via rsl_rl** (mjlab's bundled agent). ~1–2 h for a usable gait at
  4096 envs per README.
- Actuator realism is the core of their sim2real: **BAM M6** (`github.com/Rhoban/bam`,
  Apache-2.0; ICRA 2025 paper) — voltage control law → PWM → current → torque, back-EMF,
  Coulomb+Stribeck+load-dependent friction, identified on a **physical XL330-M288-T**.
  Config: `kp_fw=200`, `vin_range 6.5–8.2`, `vin_drop_gain 0–0.2`, `vin_min 6.0`,
  command delay 3–6 ticks, per-env friction scale; backlash variants insert a
  `passive_<j>_backlash` hinge (±1°) and feed encoder *through* the play.
- Fallback native-PD params exist in `joints_properties.xml` (e.g. damping 0.053,
  frictionloss 0.0048, armature 0.0018, kp 0.55, forcerange ±0.96 N·m — a sim limit,
  not the vendor stall figure).
- Observation/command contract is shared across all tasks (61/14) → runtime hot-swap.
- Tasks: Velocity (flat/rough), VelStand (walk+fall-recover), StandUp, SitStand,
  GroundPick, BallKick (70 mm/15 g ball), Roulade, Rollers family (skate/crouch/
  slope/standup/spin/swizzle) — plus `-Backlash` twins.
- Models: MJCF from **Onshape via onshape-to-robot** (Rhoban tool); walk /
  allcollisions / rollers / backlash variants; scenes incl. an "apartment" world.
- Export: `scripts/export.py` bakes obs-normalisation into ONNX; `infer_policy.py`
  rehearsals in CPU MuJoCo with keyboard; LSTM (explicit h/c) export supported.
- CLAUDE.md (15 kB) documents their reward-design playbook — worth reading closely
  when we write our own env.

### 3.2 On-robot inference & update distribution

- ONNX Runtime dlopen'd (≥1.23); policies live in `/opt/robot/policies/current`,
  swappable via `robotctl policy load SLOT <hf-repo>` — Hub repo
  `pollen-robotics/microduck-policies` is the official set (slots:
  walk/stand/sitstand/ground_pick/kick_left/kick_right/roulade).
- `microduck-arena` (HF Space + repo): server-side policy racing on fixed courses,
  5 perturbed seeds; community policies tagged `microduck-policy` + `manifest.json`.
- `microduck-challenges`: ready-to-train env folders (sprint-2m, hill-climb-1m5,
  roller-sprint-2m, got-a-talent). `microduck-simulator` Space = MuJoCo twin demo.
- `duck-sim` runs the *real daemons* against MuJoCo bodies (`duck-body` in microduck_rl)
  — full-stack dev without hardware; supports N containerised ducks.
- Onboard vision: `duck_detect` = yolo11n@320 INT8 RKNN on the 0.8-TOPS NPU, 2 Hz
  (thermal cap); training pipeline `duck_detector` public (dataset+model on Hub).
- Pet-detection (petting classifier) on the mic; pickup-detector ONNX pauses the
  policy when carried; posture classifier decides seated vs standing start.

### 3.3 microduck_runtime (the pre-commercial prototype)

`github.com/apirrone/microduck_runtime` (search-indexed; repo intermittently 404s —
treat as semi-public): Python/C/Rust runtime for variants v1/v1.5/v1.6 on **Pi Zero 2W
or Radxa Zero 3W**, 15 XL330, IMU options BMI088/BNO055/BNO08x or imu_to_dxl
v1 (LSM6DS3TR-C + host Madgwick) / v2 (LSM6DSV16X SFLP). Cameras: IMX500 (v1/v1.5),
IMX708 Wide = RPi Cam 3 Wide (v1.6). This is the "prototype" every doc references;
the 50 Hz rate was chosen on the Pi and never re-derived on the Radxa.

---

## 4. Ancestors & sibling projects (where the real BOMs live)

### 4.1 Open Duck Mini v2 — `github.com/apirrone/Open_Duck_Mini` (v2 branch, Apache-2.0)

The community project Microduck descends from (same engineer, Antoine Pirrone, now
Pollen; HF+Pollen sponsored). Public Onshape CAD, print/assembly guides, Tnkr guide,
Discord. Published BOM (Google Sheet, accessed 2026-10-26):

| Item | Part | Qty | ~Cost |
|---|---|---|---|
| Servos | **Feetech STS3215 7.4 V (19 kg·cm)** | 14 | €14 ea = €196 |
| Head/expression | 9 g servos | 2 | €6.7 |
| Compute | Raspberry Pi Zero 2W + SD | 1 | €26+10 |
| Servo adapter | Waveshare Bus Servo Adapter | 1 | €5 |
| IMU | BNO055 | 1 | ~€40 (sheet notes cheaper wanted) |
| Power | 2×18650 (Molicel P30B 3000 mAh) + 2S BMS + 5 V UBEC + XT30 + USB-C charger | set | ~€37 |
| Misc | feet switches SS-10 ×4, M3 inserts, PLA ~500 g, TPU feet, bearings, cables | — | ~€50 |
| **Total** | | | **€398 base / €432 with expression pack** (speaker, amp, LEDs, mic, RPi cam) |

~42 cm extended, model mass ≈2107 g. RL: **MuJoCo Playground (MJX)** +
`Open_Duck_Playground` env (joystick task, Disney-BDX imitation reward via
`Open_Duck_reference_motion_generator`), BAM `feetech_sts3215_7_4V` identified model
(already in BAM's bundled library — directly reusable if we pick STS3215-class).
Same ID scheme (legs 20-24/10-14, head 30-33) — the lineage is literal.

v1 (main): ~35 cm, switched to XC330-M288-T legs (more voltage headroom than XL330 —
consistent with the over-volting problem they already had), Isaac Gym + AWD.

### 4.2 Rhoban microban — `github.com/Rhoban/microban`

~30 cm open biped, **19× XL330-M288-T**, Pi Zero 2W + **the same Pollen RPI Robot HAT**,
2×18650+BMS holder, ~$550–600 all-in, STL+STEP CAD published, full BOM doc
(`docs/bom.md`), GPLv3 software / CC BY-NC-SA hardware. Closest "open" datapoint to an
XL330-class microbiped — and evidence the HAT is a general-purpose board (also used
by Pollen's Grabette on Pi 4).

### 4.3 Community microduck clones (proving DIY feasibility)

- **`fanhao375/microduck-replica`** (+ `microduck-replica-cad`, CN/EN docs): complete
  reconstruction — assembly/exploded drawings, CAD-importable STPs of the 33 printed
  parts, reproduction PCBs (bus-IMU, servo hub, battery board), system image +
  web console. **Feetech HD-1910 (15×, ~¥95≈£10 ea) build validated on hardware:**
  stand, walk, forward roll, get-up. XL330 variant CAD also published.
  Shopping list ~¥139 print + parts incl. Radxa ¥309, HAT fab ¥120, imu_to_dxl ¥80.
  Also hosts the best electronics teardown (hardware-teardown.en.md) — verified
  against the official KiCad BOM (exact designators match).
- **`SaberOnGo/open-microduck`**: English docs tracking the same reconstruction;
  model mass 737.2 g, envelope 144×141×264 mm.
- **@tspy X teardown (2026-08-31)** + long-form article (2094963381220622638):
  independent hardware confirmation incl. Radxa Zero 3W; DIY cost >$500 quoted.
- **duck.whatled.com**: 203-article line-by-line code/electronics explainer series (CN).

---

## 5. Licensing & open artifacts — precise scope

| Artifact | Licence | Status |
|---|---|---|
| pollen-robotics/microduck (runtime, daemons, docs) | Apache-2.0 | full source |
| microduck_rl code | Apache-2.0 | full source |
| microduck_rl MJCF + 47 STL meshes | **CC BY-SA-NC** | reference only — no commercial reuse |
| elec_RPI_Robot_HAT | Apache-2.0 | **KiCad9 schematic+PCB, Gerbers, BOM, PnP, STEP** — fab-able today (4-layer, SMT needed; needs lib_KiCAD repo for symbols) |
| elec_battery_mngt | public repo | "2S BMS + USB-ish charger" KiCad projects — likely the duck's charge/battery boards' cousins |
| bmi088-rs, lsm6ds3tr-rs, rustypot | Pollen crates | open drivers they wrote and we can reuse |
| tof/vendor (ST VL53LxCX ULD) | ST package licence / BSD-3 fallback | redistributable-with-conditions |
| microduck_yocto | public | production OS (kas/Yocto wrynose, RAUC) |
| duck_detector | public | yolo11n training pipeline + dataset + model on Hub |
| microduck-policies + arena reference policies | Apache-2.0 on HF Hub | runnable reference gaits |
| imu_to_dxl firmware | **closed** | protocol/behaviour documented in code; community reimpl exists |
| Mechanical CAD (editable), beta-board design, whole-robot BOM, assembly docs | **not published** | press kit: "not open-source hardware" |

---

## 6. UK availability & pricing (checked 2026-10-26)

- Store lists **United Kingdom** in launch regions (US/CA/EU/UK/NO/CH/JP/KR); UK is
  billed in **EUR: robot €340** (≈£295 pre-shipping/VAT handling unclear), accessory
  & charger packs €33 each, dev pack €99.99. US headline $399 ex tax & shipping.
- Banner: "community ordered a lot of ducks … pre-orders ship after **April 2027**";
  launch deliveries were targeted "before Christmas 2026". Community-reported
  **>$1 M first-7-hours** sales (unverified, replica docs).
- In the box: robot, battery, USB-C cable, game controller. Gamepad included confirmed.

---

## 7. What is NOT publicly disclosed (honest gaps)

- **Exact servo sub-variant** — everything says XL330; M288-T is an evidence-chain
  conclusion (BAM model identified on M288-T + 6.0 V rating match + visual ID),
  not a Pollen statement. Confidence: likely.
- **Beta-board schematic, servo power path on beta** (does production regulate the
  servo rail? unknown — alpha demonstrably does not), production speaker/mic parts.
- **Which board retail units ship** (Radxa+HAT "alpha" vs Seeed "beta"); store's
  "1 GB/32 GB" is consistent with either direction. Likely beta for production.
- **imu_to_dxl firmware & MCU**, face-board/NFC PCB details, NP-F550 capacity as shipped
  (generic F550s span 1500–2600 mAh).
- **Servo lifetime/heat data** under over-volting — community notes report warm servos;
  Pollen sell a dev pack with 3 spare motors, which hints at expected wear.
- Mouth servo variant (assumed same XL330; unverified), roller-skate wheel part numbers.

---

## 8. Implications for MASCOT (hand-off to design workstreams)

1. **Servo decision is THE decision.** XL330-M288-T at retail ($23.9–42) makes 15× alone
   ≈$360–630 — structurally impossible under £320. Proven alternates:
   - Feetech STS3215 7.4 V (~£11–18 ea, ODM v2 + LeRobot-standard, BAM model exists)
   - Feetech HD-1910 (~£10 ea, validated on duck geometry by microduck-replica)
   - Feetech STS3032 (20 g class, 4.5 kg·cm @6 V — only for head/mouth joints if mixed)
   - Unitree S288: mechanically near-identical to XL330 (288.35:1, M2) but 3S/12.6 V,
     own 6 Mbps protocol, ambiguous torque spec → not a drop-in.
   Both cheap options are bigger/heavier than XL330 → expect our 26–32 cm / 0.9–1.3 kg
   envelope (consistent with ODM v2 = 42 cm/2.1 kg on STS3215 — we'll land between).
2. **Don't over-volt.** Microduck's over-volting XL330s is a cost hack, not a pattern.
   Picking native-7.4 V servos also kills their voltage_adapt complexity.
3. **Copy the architecture, not the parts:** single half-duplex serial bus carrying
   servos (+optionally IMU) at 50 Hz on ONE UART; intents→single control task;
   health = achieved-rate thresholds; deadman; predictive limp-fall (gyro-extrapolated
   gravity, gain drop, still-detect, pose ramp) — all implementable on an MCU or small
   SBC, all documented in their design docs.
4. **Reproduce the policy contract** (61 obs / 14 actions layout is public) → access to
   official+community ONNX policies as a smoke-test and possibly a walking baseline.
5. **Reuse the training recipe:** mjlab+PPO+BAM identified actuator + voltage/sag/delay/
   friction DR + backlash hinges. If we pick STS3215, `feetech_sts3215_7_4V` params
   already exist in BAM. CUDA-less path: HF Jobs or MJX-Playground-style training
   (ODM v2 used Playground successfully).
6. **Compute:** Pi Zero 2W already proved 50 Hz policy + bus I/O (ODM v2, microduck
   prototype). Camera/WebRTC/NPU are what forced the RK3566 — decide vision scope
   before picking compute; an MCU real-time layer + optional SBC keeps cost low.
7. **Sensors:** single 6-axis IMU (LSM6DSV16X-class with on-chip fusion, or BNO055) is
   all balance needs; ToF/second-IMU/NFC/audio are accessory-tier, not MVP.
8. **Battery:** NP-F550 (commodity, swappable, ~£15–30) vs 2×18650+BMS — both proven
   patterns; either way, servo-reported bus voltage makes a fuel gauge optional.
9. **Community precedent:** microduck-arena convention (HF repo + `microduck-policy`
   tag + manifest.json + pinned revision) is a ready-made distribution format we can
   be compatible with; replica communities show demand for buildable kits.
10. **Watch-outs they hit, free:** UART getty holding the servo port; fast-sync-read
    firmware floor (v46); return_delay_time default eating 40% of tick budget;
    factory D≠0 damping the loop; thermal throttling of a fanless A55 under vision;
    STL assets are NC — never lift them, use for measurement only.

### 8b. Corrections to `design/shared-design-brief.md` baseline rows

| Brief says | Finding | Suggested update |
|---|---|---|
| "Hardware: NOT open hardware" | True for mech CAD + beta board + imu_to_dxl, but the **servo/power/audio HAT is fully published Apache-2.0** (KiCad+Gerbers), and rl repo ships MJCF+STL under **CC BY-SA-NC** | Reword to "mechanical design closed; one carrier PCB open; sim meshes NC — no released CAD may be copied into our product" |
| "LiDAR" (sensor row) | ST **VL53L5CX/L8CX multizone ToF**, 8×8 @15 Hz — 'LiDAR' is marketing shorthand | Rename to "8×8 ToF depth sensor" in our comparison rows |
| "2 IMUs" | Asymmetric: bus-mounted SFLP IMU feeds the 50 Hz loop; head IMU is for camera/gaze and off by default on alpha | Reflect asymmetric roles |
| "15 motors" | 15 physical, **14 in policy action space** — mouth is joint 9, script-driven | Keep both numbers: "15 DOF / 14 policy joints" |
| "$399" | Also **UK channel at €340**, order backlog → post-Apr-2027 shipping | Update pricing row; availability gap strengthens DIY rationale |
| "50 Hz loop" | Confirmed, plus documented detail: 2 transactions/tick, kP 200, low-pass contract | Enrich with the obs/act contract (61→14) |
| Preliminary targets (26–32 cm, 0.9–1.3 kg, 10–14 DOF, 2S bus, MCU+SBC, <£320) | All remain coherent: ODM v2 (42 cm/2.1 kg on STS3215) and Microduck (25 cm/0.78 kg on XL330) bracket our envelope; a native-7.4 V servo keeps the 2S bus without over-volting; Pi-Zero-class compute is proven sufficient when vision is minimal | No change needed to targets; servo shortlist should anchor on STS3215-class |

---

## 9. Source list (all accessed 2026-10-26)

Primary (Pollen):
- github.com/pollen-robotics/microduck — README.md; docs/design/{architecture,robotd-design}.md;
  docs/{faq,recurrent-policies,robot/simulation}.md; deploy/robotd.toml;
  duck-control/src/{bus,model,imu}.rs; robotd-params/src/board.rs; mediad/src/sensor.rs;
  tof/src/{sensor,imu}.rs; duck-ipc-proto/src/{lib,led}.rs; kinematics/assets/alpha/robot_walk.xml
- github.com/pollen-robotics/microduck_rl — README.md; src/mjlab_microduck/robot/microduck_constants.py;
  actuator/friction_dr_bam.py
- github.com/pollen-robotics/elec_RPI_Robot_HAT — README.md (KiCad, releases A1→D1)
- github.com/pollen-robotics/microduck_yocto — README.md
- github.com/pollen-robotics/elec_battery_mngt — README.md
- github.com/pollen-robotics/duck_detector — README.md
- github.com/pollen-robotics/microduck-arena, /microduck-challenges — READMEs
- pollen-robotics.com/microduck (+ /press-kit); store.pollen-robotics.com/products/microduck
- huggingface.co/pollen-robotics/microduck-policies; spaces microduck-simulator/-arena/-policy-playground/-console

Lineage / adjacent:
- github.com/apirrone/Open_Duck_Mini (v2 branch README; BOM sheet docs.google.com/
  spreadsheets/d/1gq4iWWHEJVgAA_eemkTEsshXqrYlFxXAPwO515KpCJc); docs/sim2real.md
- github.com/apirrone/Open_Duck_Mini_Runtime (v2 README); /Open_Duck_Playground;
  /Open_Duck_reference_motion_generator; /microduck_runtime (intermittent 404)
- github.com/Rhoban/bam (README + bam.readthedocs.io identified-actuator tables);
  github.com/Rhoban/microban (README, docs/bom.md)
- github.com/mujocolab/mjlab (referenced framework)

Community reconstructions / teardown:
- github.com/fanhao375/microduck-replica — README.en.md, docs/hardware-teardown.en.md,
  docs/actuator-selection.en.md, BOM/README.md (+ -cad repo)
- github.com/SaberOnGo/open-microduck — docs/en/hardware/community-bom-reconstruction.md
- X @tspy article 2094963381220622638 (2026-09-02; via nitter mirror + dormon.net reprint);
  X @Allyakutaku 2095331280233926948 (motor visual ID)
- duck.whatled.com/learn/deep (203-part series, CN)

Datasheets / third-party:
- emanual.robotis.com/docs/en/dxl/x/xl330-m288/ (via replica citation + spec cross-checks)
- Sony NP-F550 specs: sony.com.au; Duracell Direct UK (Neewer F550 £28); Hawk-Woods DV-F550
- ST VL53L5CX/L8CX ULD (vendored in tof/vendor); ST AN6065 (ST25R100 antenna design)
