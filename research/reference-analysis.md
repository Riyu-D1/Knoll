# Reference Analysis — Pollen Robotics / Hugging Face Microduck

**Date compiled:** 2026-10-26
**Status:** Verified against primary sources (official product page, press kit, GitHub repos). Conflicts and undisclosed items explicitly flagged.

---

## 1. Verified reference specification

| Feature | Published value | Evidence | Confidence | Implication for our design |
|---|---|---|---|---|
| Height | 25 cm | press kit fact sheet | Verified | Our 26–32 cm target is comparable class; slightly larger eases DIY tolerances |
| Mass | "under 800 g" / "~800 g" | press kit; microduck_rl README | Verified (approx) | Hard to beat at DIY scale; we accept ~0.9–1.3 kg and must be honest about it |
| Motor count | 15 | press kit | Verified | |
| Actuated joints in policy | 14 (5 per leg + 4 neck/head) | microduck_rl README joint layout | Verified | 15th servo is the mouth/beak; legs are 5-DOF: hip_yaw, hip_roll, hip_pitch, knee, ankle — **no ankle roll** |
| Actuator type | Dynamixel XL330 class, "Dynamixel protocol v2" bus @ 1 Mbps | robotd-design.md; microduck_rl BAM M6 "for the Dynamixel XL330" | Verified (protocol + family); exact variant (M077 vs M288) undisclosed | XL330 = ~18 g micro servo; retail ~$25–35 ea → ~$400+ in servos alone at retail. Confirms our cost advantage must come from a cheaper servo family (Feetech-class) at comparable capability |
| Servo bus topology | 15 servos + IMU board on ONE UART, 1 Mbps, sync_read + sync_write per 50 Hz tick | robotd-design.md | Verified | Validates single-bus half-duplex architecture for ~15 servos @ 50 Hz; our MCU must do the same |
| IDs / joint map | legs: L 20–24, R 30–34; neck/head/mouth 10–14; IMU id 200 | robotd-design.md | Verified | — |
| IMU | Custom `imu_to_dxl` board serving "on-chip SFLP quaternion" on Dynamixel bus (id 200). SFLP = Bosch BNO08x "Sensor Fusion Low Power" game-rotation-vector feature | robotd-design.md | Likely (BNO085/086 strongly implied by SFLP); second IMU location undisclosed | A fused-orientation BNO085-class IMU is the reference bar; we can use a $12 breakout instead of a custom bridge board |
| Camera | present, ~1.8 MiB raw frames, WebRTC streaming via `mediad` | press kit, architecture.md | Verified; sensor model undisclosed | Camera is for teleop/streaming & future perception, NOT required for locomotion (policy obs = proprioception only, 61-dim) → we can make camera optional in v1 |
| Depth sensor | 8×8 ToF matrix in head, I²C/SPI, own daemon `tofd` | architecture.md | Verified (8×8 zones ⇒ ST VL53L5CX class) | Optional upgrade for us — not used by shipped locomotion policies |
| Compute | Rockchip RK3566 SBC, "only the Radxa" (Radxa Zero 3 class), Armbian | robotd-design.md, install docs | Verified | Pi Zero 2 W or Radxa Zero 3 both viable for us; RK3566 quad A55 ≈ Pi-Zero-2W class. RL inference of small MLP is trivial CPU load |
| Control loop | 50 Hz, one UART, sync_read 16 devices → policy → sync_write | robotd-design.md | Verified | Sets the bar: 50 Hz whole-robot loop is achievable on MCU + SBC |
| Policy stack | mjlab (MuJoCo Warp) + rsl_rl PPO → ONNX → onboard runtime | microduck_rl README | Verified | Directly replicable with open tools; ONNX Runtime runs on Pi-class CPU |
| Obs contract | 61-dim actor obs = 48 proprioception + commands [twist(3), head_pose(4), body_pose(6)]; shared across all policies → hot-swap | microduck_rl README | Verified | Excellent pattern to adopt: fixed obs contract across policies |
| Actuator sim fidelity | BAM M6 model (voltage law, back-EMF, Coulomb/Stribeck/load friction) + per-env DR on voltage, sag, delay, friction; ±1–2° backlash modelled as passive hinge | microduck_rl README | Verified | The honest core of their sim2real; we must model Feetech-class servos similarly (position-servo emulation differs — see our control doc) |
| Behaviours shipped | walk (velocity+head cmds), sit/stand, ball kick, ground pick (beak grab), forward roll ("roulade"), roller-skate modes, stand-up from face-down/face-up/sitting (incl. unified VelStand walk+recover) | product page + task registry | Verified as trained tasks; real-world reliability not independently published | Our staged recovery plan can mirror the task split (StandUp env = get-up from defined poses — matches our Stage D) |
| Software licence | Apache-2.0 | repo | Verified | We can study/derive architecture; we cannot copy code into a differently-licensed work without attribution, and must not reuse their MJCF/robot geometry |
| Hardware licence | "Hardware design files ... CC BY-SA-NC" (in RL repo) BUT press kit: "mechanical and electronic design files are not [open]" | microduck_rl LICENSE note vs press kit | Conflict documented: files themselves unreleased; licence declared for when/if they appear. Non-commercial regardless | We cannot reuse their CAD/STL even if they leak to repos (NC + closed). Reinforces clean-room mechanical design — which we're doing anyway |
| Price | $399 before taxes & shipping; dev pack (3 spare motors etc.) $119; charger $39 | store | Verified | US retail ≈ £315 + 20% VAT + shipping ≈ ~£400 landed UK. **Our recommended-build target: < £320 all-in** |
| Update system | signed releases, atomic swap, health-gated auto-rollback, boot counter | architecture.md | Verified | We adopt a simplified version (A/B rootfs or git-style rollback on SBC) |
| IPC | JSON-RPC 2.0 over unix sockets, NDJSON; every client same API | architecture.md | Verified | Pattern to emulate: one bounded intent API, many transports |
| Safety architecture | `safety` module owns the bus; policies/clients *propose* targets, never send | robotd-design.md | Verified | Copy the PRINCIPLE exactly: single owner of motor output |
| Failure transparency | "the runtime ... exploratory and will be rewritten"; robotctl must work on a broken robot | architecture.md | Verified | Good-honesty model; our docs likewise separate shipped vs aspirational |

## 2. What is advertised vs verified vs unknown

- **Verified:** all software architecture above, task list, sensor classes, compute class, motor count, size/mass band.
- **Advertised but unverified under all conditions:** "gets back up" (shown face-up→stand in demo; arbitrary falls not claimed or proven), push recovery (one clip), battery runtime (**not published anywhere** — unknown), durability/drop ratings (none published), age rating (provisional).
- **Undisclosed:** exact servo variant (XL330-M077-T vs M288-T), battery chemistry/capacity, camera sensor, second IMU location, exact mass, BOM, CAD, PCB, motor gear material, retail margin vs BOM.
- **Deliberately closed:** mechanical + electronic design files (press kit says explicitly not open hardware). ⇒ The market gap we fill: **a genuinely open-hardware equivalent**.

## 3. Capability class target for our robot (what "comparable" means)

Must-have parity (defensible claim):
1. Stable walking with velocity commands on flat indoor surfaces
2. Sit ↔ stand transitions
3. Self-recovery from tested fall poses (back, front, side) — staged, measured
4. Teleoperation via gamepad + optional phone/desktop
5. Fused IMU balance feedback in the loop
6. Sim-first development: physics twin, domain randomisation, policy hot-swap
7. Expressive character (head motion, status light/sound) — beak/mouth grab is OPTIONAL, not parity-critical

Explicitly out of scope for v1 (Microduck has, we defer): roller-skate accessory, ball-kick task, camera-based behaviours, ToF navigation, choir/sound features beyond a buzzer, LLM assistant beyond an API stub.

## 4. Cost baseline

Microduck at $399 + shipping; UK landed ≈ £400 incl. VAT. Its servo bill alone (15× XL330-class at retail ≈ $375–525) explains most of the price — plausible only via OEM pricing. **Our lever: equivalent-capability serial servos at ~⅓ retail XL330 cost (Feetech STS3215-class ≈ $13–18 ea), open PCB, no retail margin.** Target recommended build < £320 GBP all-in — see `bom/cost-model.md`.

## 5. Sources for this document

Primary: product page, press kit/fact sheet, github.com/pollen-robotics/microduck (README, docs/design/architecture.md, docs/design/robotd-design.md), github.com/pollen-robotics/microduck_rl README. Full register with access dates in `research/sources.md`. Secondary corroboration (Open Duck Mini, teardowns) pending — see `research/notes-microduck.md` (Agent A output).
