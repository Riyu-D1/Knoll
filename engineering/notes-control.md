# Control & Self-Recovery Architecture — Research Notes

**Status:** research findings, 2026-10-26. Every number below is cited; our own robot's
parameters are planning targets, not measurements.

**Scope:** ~26–32 cm, ~1 kg bipedal mascot, 10–14 serial smart servos on a 7.4 V (2S) bus
with position/temp/load feedback, ~50 Hz command rate feasible. The reference class is
Open Duck Mini (ODM) and Pollen/Hugging-Face Microduck.

---

## 1. How the reference class does it

### 1.1 Open Duck Mini (apirrone)

*Repos:* robot hub `github.com/apirrone/Open_Duck_Mini` (v2 branch), runtime
`github.com/apirrone/Open_Duck_Mini_Runtime`, training
`github.com/apirrone/Open_Duck_Playground` (fork of DeepMind `mujoco_playground`),
reference gaits `github.com/apirrone/Open_Duck_reference_motion_generator`.

**Hardware (v2):** ~42 cm legs-extended, BOM < $400 (community builds ~$200). 14×
**Feetech STS3215 (7.4 V)** bus servos + 2× 9 g antenna servos, Raspberry Pi Zero 2 W,
Waveshare Bus Servo Adapter (A), BNO055-class IMU (read raw: gyro+accel), two foot
contact switches. Sources: opensourcerobotics.dev/robots/open-duck-mini,
github.com/apirrone/Open_Duck_Mini README, microduck.intemotech.com/guide.

**Sim + training:** MuJoCo MJX via a `mujoco_playground`-derived framework; PPO (the
playground's RSL-RL-style JAX trainer). `ctrl_dt=0.02` (50 Hz policy), `sim_dt=0.002`
(500 Hz physics), `action_repeat=1`.

- **Action space:** `motor_targets = home_ctrl + action * 0.25` — absolute **position
  targets**, rate-limited to `max_motor_velocity = 5.24 rad/s` per control step
  (`joystick.py`). At runtime the same targets go to the servos' internal position
  loops; servo gains set to **kp=30, kd=0** (P-only) on legs, head kp lowered to 8
  (`v2_rl_walk_mujoco.py`, `Rustypot HWI`).
- **Observation (actor):** gyro(3), accel(3), command(7), `dof_pos − home` (10 leg
  joints), `dof_vel*0.05` (10), last-3 actions (30), current motor_targets (10), foot
  contact booleans (2), gait phase `[cos,sin]` (2) → ~77 D for the 10-joint legs
  config (14-joint variant used at runtime). Privileged critic adds lin-vel, gravity,
  global ang-vel, root height, actuator forces, foot velocities, air time, reference
  motion.
- **Imitation reward:** reference gait from a parametric walk engine (PlaCo), fit to
  per-velocity polynomials (`polynomial_coefficients.pkl`), implementing the
  imitation term from Disney's BDX paper (below). `USE_IMITATION_REWARD=True` default.
- **Reward scales:** `tracking_lin_vel 2.5, tracking_ang_vel 6.0, torques −1e-3,
  action_rate −0.5, stand_still −0.2, alive 20, imitation 1.0`, `tracking_sigma 0.01`.
- **Noise/delay in training:** action delay 0–3 env steps (0–60 ms), IMU delay 0–3,
  joint-pos noise 0.03/0.05/0.08 rad (hip/knee/ankle), joint-vel noise 2.5 rad/s,
  gravity 0.1, gyro 0.1, accel 0.05; random pushes 0.1–1.0 m/s every 5–10 s.
- **Backlash:** dedicated `flat_terrain_backlash` task — unactuated hinge joints in
  series with each servo model gear play; policy obs read `qpos_servo + qpos_backlash`
  because the real encoder sits output-side.
- **Actuator model:** Rhoban's **BAM** identified parameters for `feetech_sts3215_7_4V`
  exported to MJCF actuator/joint fields: `damping, kp, frictionloss, armature,
  forcerange` (`docs/sim2real.md`, `bam.to_mujoco`).
- **Deployment:** ONNX on the Pi Zero 2 W at 50 Hz; optional `LowPassActionFilter`;
  per-robot `duck_config.json` (joint offsets, IMU orientation, `pitch_bias`);
  pre-flight checklist = joint zeros, IMU orientation, feet switches
  (runtime `checklist.md`).

**Published negative result worth reading end-to-end:** "Lessons from Sim-to-Real on
a 15-DOF Bipedal Robot" (Z. Xu, Purdue; zhenghaoxu.com/duck%20writeup.pdf): a PPO
policy beating the author's baseline on 11/14 *sim* metrics failed on hardware. Root
causes: loose screws → asymmetric per-joint backlash (systematic, not zero-mean),
joint zeros not matching `keyframe("home")`, reward overfitting. Key lessons:
**verify every joint zero against the sim home keyframe; SysID beats wider DR;
evaluate on hardware early; DR cannot fix systematic bias.**

### 1.2 Microduck (Pollen Robotics / Hugging Face)

*Repos:* runtime `github.com/pollen-robotics/microduck` (Rust workspace, Apache-2.0),
training `github.com/pollen-robotics/microduck_rl` (Apache-2.0). Product page +
press kit: pollen-robotics.com/microduck.

**Hardware:** 25 cm, ~800 g, 14× **Dynamixel XL330** servos driving the policy
joints (press kit says "15 motors" — the extra one is the passive-linkage beak/jaw,
not part of the 14-D action space), Rockchip RK3566 SBC, camera + LiDAR + 2× IMU.

**Training stack:** **mjlab** (`github.com/mujocolab/mjlab` — "Isaac Lab API powered
by MuJoCo Warp") + PPO via `rsl_rl`; CUDA GPU required, ~1–2 h for a usable gait at
4096 envs; `--hf-jobs` offloads to Hugging Face Jobs (no local GPU needed). Export =
ONNX `[1,61] → [1,14]` with the obs normalizer **baked into the graph** — hand-converted
checkpoints are explicitly refused. LSTM policies supported on-device (model_api 2,
`docs/recurrent-policies.md`).

- **Obs contract:** 61 D actor obs shared across the whole policy family →
  hot-swappable: 48 proprio (`base_ang_vel` 3 + `projected_gravity`/`raw_accel` 3 +
  `joint_pos` 14 + `joint_vel` 14 + `last_action` 14) + 13 command block
  `[twist(3), head_pose(4), body_pose(6)]`, unused slots zero-padded but kept "alive"
  with tiny sampling ranges (dead-weights lesson).
- **Actuator model:** **BAM M6** for XL330 — voltage-control law, back-EMF,
  Coulomb/Stribeck/**load-dependent** friction; `kp_fw=200` firmware stiffness.
  DR: `vin ∈ [6.5, 8.2] V`, load sag `V_drop = gain·Σ|τ|`, `gain ∈ [0,0.2]`,
  `vin_min 6.0`; **actuator command delay 3–6 env steps = 60–120 ms** (the serial-bus
  write→effect latency); friction DR via actuator `friction_scale` ±10 %
  (`microduck_constants.py`, `friction_dr_bam.py`).
- **Obs delays/noise (2026-07 audit):** IMU terms delay 0–1 step (±20 ms), `joint_vel`
  fixed 1-step delay; noise `ang_vel ±0.03`, `gravity ±0.01`, `joint_pos ±0.001`,
  `joint_vel ±0.25`; per-joint **encoder bias** ±0.015 rad.
- **DR set:** foot friction ×[0.7, 1.3]; trunk CoM ±15 mm (ramped 3→15 mm; >15 mm
  pushes CoM outside foot support → trains hyper-reactive corrections — their audit
  capped it); head-assembly CoM ±10 mm; mass+inertia ×[0.95,1.05] via pseudo-inertia;
  armature ×[0.9,1.1]; IMU mounting misalignment **6°** (real IMU measured ~5°
  systematic pitch error + estimator drift — 2° was too narrow); pushes ±0.3 m/s
  every 3–6 s (curriculum 0 → ±0.08 → ±0.3). **kp/kd DR is OFF** under BAM.
- **Backlash:** ±1° passive hinge per servo joint, generated by `add_backlash.py`;
  encoder & firmware-PD read *through* the play (`BacklashEncoderBamActuator`).
  Every main task has a `-Backlash-` twin; production velstand runs
  `Rough-Backlash`.
- **Task list (published):** Velocity (walk), **VelStand** (walk + protective fall +
  get-up in ONE policy), StandUp (face-down/face-up/sit → stand), SitStand,
  GroundPick, BallKick, Roulade, 5 roller tasks. Runtime hot-swaps policies behind
  the shared obs contract; "falls protectively" is trained (a servo-impact contact
  sensor on the XL330 housings feeds protection costs).
- **Physics sanity noted in AGENTS.md:** a 25 cm robot tumbles at 3.5–5.5 rad/s
  *naturally* — don't cap rotation rates with human-scale intuition; put
  anti-violence pressure on |a_z| impacts, action_rate, support gates.

**Reward-design playbook (AGENTS.md — the distilled sim2real recipe, highly
recommended reading):** every penalty term must log ≤ 0 (sign bug double-negated
into rewarding impacts twice); no jackpot rewards (slew/rate-limit "reach X"
rewards); potential-based shaping (pay Δcos(tilt), not presence in a bad state);
motion-blocker regularizers (body_ang_vel, ang momentum) stay LOW during skill
discovery — "any attempt-tax active while a hard skill is explored makes 'do
nothing' win"; multiplicative goal composites beat additive stacks at goal states;
measure target heights off the real robot in sim (a 5 mm-wrong STAND_Z made the goal
impossible); smoke test = 64 envs × 5 iters catches ~95 % of config errors.

**Runtime (`robotd`, 50 Hz loop on RK3566):** deterministic safety layer — command
**deadman switch** ("no intent arrived recently → velocity zeroed"), **`fallen`
verdict from the IMU projected-gravity vector** vs `[0,0,−1]`, "limp-fall" mode,
battery-empty → **sits down and cuts servo power**, per-servo temperature
monitoring ("hottest servo" in `robotctl health`), safety clamps on every outgoing
command, loop-rate watchdog ("control loop at 43.9 Hz" flagged unhealthy), stale-IMU
detection. `scripts/duck-sim` runs the real daemons against a simulated body —
hardware-in-the-loop CI for the whole stack. (`docs/robot/cheatsheet.md`)

**VelStand recipe** (`docs/velstand_policy.md`): walk teacher (`alpha_walking`,
trained in the velocity env) + stand teacher (`alpha_stand`, trained in the standup
env) **distilled by BC into one student** alongside PPO (walk BC anchor keeps the
gait; stand expert supplies get-up labels). Wide spawns: random-joint prone 50 %,
uniform-SO(3) 25 %, sit 5 %. A "stay-there" attractor in the teacher was fixed by
**joint-masking the teacher's obs above 75° tilt** (it then labels get-up from
orientation alone): face-up get-up with random joints went 55 % → 93–100 %, rise
gentler (|ω| p50 was ~11 rad/s). Sim eval: **93–95 % get-up after push-falls** at
1.0–1.2 m/s; checkpoint choice matters (yaw asymmetry varies between checkpoints
with identical training metrics — always run the probe battery before picking).
Known limits honestly logged: body-crouch axis unlearned, slow in-place yaw weak.

### 1.3 Related HF/community stacks

- **TorchRL ships `MicroDuckEnv`** (docs.pytorch.org/rl/stable/tutorials/microduck.html):
  task-as-data env with reward registry, PPO-with-GRU example, and a **hand-written
  closed-form gait controller** (`MicroDuckGaitActor`, phase oscillator) usable as a
  classical baseline/fallback. Backends: `mujoco` (CPU), `mjx`, `mujoco-torch`.
- **mujoco_playground** (DeepMind, arXiv:2502.08844): locomotion envs for Berkeley
  Humanoid, Robotis OP3, Unitree G1/H1, Booster T1; **Go1 fall-recovery env**;
  demonstrated zero-shot sim2real on Go1 joystick/fall-recovery/handstand and on
  Berkeley Humanoid/G1/Booster locomotion. `pip install`, single GPU, "minutes".
- **Disney BDX paper** — Grandia, Knoop, Hopkins et al., "Design and Control of a
  Bipedal Robotic Character", RSS 2024 (arXiv:2501.05204): RL policy conditioned on
  animator-supplied commands imitates artist-directed reference motion — the
  imitation-reward scheme ODM adopts; it's the reason these mascot-class robots
  *waddle* rather than just walk.

---

## 2. Simulator choice for a DIY biped

| Sim | Status / license | Parallel RL | Servo-dynamics fidelity | Hobbyist hardware | Verdict |
|---|---|---|---|---|---|
| **MuJoCo** (CPU) + **MJX / MuJoCo Warp** (GPU) | Free since Oct 2021, Apache-2.0 since May 2022 (github.com/google-deepmind/mujoco) | CPU fine for prototyping & SAC-scale training (FRASA trained get-up in 13–37 min); MJX (JAX) or Warp → 1000s of envs on one GPU | Best-in-class: soft contact model suits small compliant feet; BAM maps identified servo params directly into MJCF or runs as custom actuator (both ODM & Microduck do this) | CPU install is `pip install mujoco`; GPU training needs CUDA for Warp (mjlab) — no CUDA → HF Jobs or MJX/Playground path | **Recommended** |
| Isaac Gym | **Deprecated/legacy** — NVIDIA download page: "no longer supported, use Isaac Lab" (developer.nvidia.com/isaac-gym/download) | GPU-only, NVIDIA Pascal+ 8 GB | PhysX actuator models weaker for cheap servos; ODM has a legacy Isaac env but the community moved to MJX | NVIDIA-only, EOL | Avoid for new work |
| Isaac Lab (on Isaac Sim/PhysX; v3 multi-backend incl. Newton) | Active, open source; heavyweight install | GPU-only, RTX-class | Good, but heavy; Berkeley Humanoid Lite uses it | Needs NVIDIA GPU + large install; overkill at 1 kg scale | Viable but heavier than needed |
| MuJoCo Playground (MJX, JAX) | Apache-2.0, DeepMind | GPU/TPU single-device; CPU possible but slow | Same MuJoCo physics; biped envs incl. OP3, Berkeley Humanoid | JAX install friction on some platforms | Good alternative to mjlab |
| PyBullet | BSD, but effectively maintenance-mode; CPU only | Poor (per-env processes) | Contact/actuator fidelity weakest of the list; legacy inertia for hobbyists | Any laptop | Only for quick kinematics checks |
| Gazebo Classic / modern Gazebo | Classic **EOL Jan 2025** (gazebosim.org); modern Gazebo is ROS-centric sim, not a parallel-RL engine | No | Adequate physics, no batch RL path | ROS shops | Wrong tool for policy training |

**Recommendation: MuJoCo, full stop.** It is what both reference projects converged
on *independently*; the identified-actuator ecosystem (BAM params for XL330 **and
STS3215-7.4 V** — exactly our voltage class) lives there; CPU inference/eval runs on
any laptop; GPU training scales via MJX-Playground or mjlab; and the whole
debug → train → ONNX-export → CPU-deploy loop is proven on near-identical hardware.

Training-stack options, ranked by fit:
1. **mjlab (MuJoCo Warp) + rsl_rl PPO** — what Microduck uses; manager-based env
   cfg, DR/events/curricula built-in, needs CUDA GPU (or HF Jobs).
2. **mujoco_playground (MJX/JAX) + its PPO** — what ODM uses; lighter, JAX required.
3. **MuJoCo CPU + stable-baselines3 CrossQ/SAC** — what FRASA uses; **trains a
   recovery policy in <40 min on CPU** — ideal for the get-up task and for
   GPU-less contributors.
4. TorchRL `MicroDuckEnv` — useful reference for task-registry/GRU design and a
   free classical gait baseline.

---

## 3. Sim-to-real methodology for position-servo bipeds

**Actuator reality:** a serial "smart servo" in position mode is a DC motor +
gearbox + encoder + onboard MCU running its own P(D) loop. We **cannot command
torque**; we command target positions (and can set internal kp/kd registers, speed
limits, voltage-dependent behaviour). Both reference projects therefore:

- Model the servo as an **identified actuator**, not an ideal PD. BAM ("Extended
  Friction Models for the Physics Simulation of Servo Actuators", Duclusaud,
  Passault, Padois, Ly — arXiv:2410.08650; docs bam.readthedocs.io) supplies models
  M1–M6 (M6 = voltage control + back-EMF + load-dependent friction, what Microduck
  runs) and a **pendulum test-bench SysID procedure** with pre-identified params
  for `xl330`, `xl320`, `mx64`, `mx106`, **`feetech_sts3215_7_4V`**, `waveshare_st3025`.
  ODM path: identify once → `bam.to_mujoco` → set `damping, kp, frictionloss,
  armature, forcerange` on the MJCF position actuator. Microduck path: run BAM M6
  as the sim actuator (policy still outputs position targets; the model internally
  does voltage→torque→internal-P).
- Treat **latency explicitly**: actuator command delay 3–6 policy steps (60–120 ms)
  in Microduck's BAM cfg; obs delays per term (IMU 0–1 step ≈ ±20 ms, joint_vel 1
  step); per-joint **encoder bias** ±0.015 rad; IMU **mounting misalignment** DR ~6°
  because a real bolted-down IMU has several degrees of systematic error (obs-level
  DR teaches tolerance to magnitude; **systematic bias must be calibrated on the
  real robot**, AGENTS.md).
- Treat **backlash as physics**: passive hinge in series with each joint (±1°,
  `add_backlash.py`), encoder reads through the play; both projects ship
  `-Backlash-` task twins. Cheap-servo wear *increases* play over time — the duck
  writeup shows loosening screws made backlash asymmetric per joint and broke
  transfer; threadlocker is a control-systems decision.
- **DR that both projects converged on:** CoM offset (trunk ±15 mm cap, head ±10 mm),
  mass+inertia ±5 %, armature/reflected inertia ±10 %, joint friction ±10 %, foot
  friction ×[0.7,1.3], battery voltage range + load sag, pushes ±0.3 m/s @3–6 s,
  encoder bias, IMU misalignment, obs noise, action/obs delays.
- **SysID > DR for systematic errors** (duck writeup): measure each joint's real
  response, per-joint backlash profile, real mass/CoM; then randomize *around
  measured* parameters, not generic ones. Verify joint zeros vs
  `keyframe("home").ctrl` before every deployment.
- **Deployment rehearsal**: drive the exported ONNX in CPU MuJoCo against the same
  actuator model (`infer_policy.py` in both projects; microduck's
  `policy-rehearsal` measures p50/p95/p99 inference latency on the actual SBC).
- **Position-increment actions are rate-robust:** FRASA trained get-up at 20 Hz and
  deployed at 100 Hz with no retraining by making actions *joint-velocity
  increments* rather than absolute targets (arXiv:2410.08655 §V-D). Also: they
  **reduced kp on both sim and real servos** to kill tremors — a legitimate
  sim2real move for P-only servo loops.
- **Real2sim2real loop** (writeup §8.2): log obs+actions at 50 Hz on the real
  robot, replay obs through the policy offline, diff sim-vs-real joint
  trajectories, update the model, retrain.

---

## 4. Self-recovery: literature and prior art

**Scripted/keyframe (KFB) tradition — the safe baseline:**
- Stückler, Schwenk, Behnke et al., "Reliable Standing-up Routines for a Humanoid
  Robot" (NimbRo, IAS-9 2006, ais.uni-bonn.de/nimbro/papers/IAS9.pdf): detect fall
  via attitude estimate, **classify resting pose (prone/supine)**, run a
  hand-designed per-pose get-up trajectory; demonstrated on real robot at RoboCup
  2005. This is still how most RoboCup kid-size teams do it; keyframes need
  periodic re-tuning as motors wear (FRASA intro confirms).
- NimbRo IROS-2018 workshop slides (ais.uni-bonn.de/behnke/talks): fall survival —
  land on cushioned contact points, relax joints; push recovery precedes get-up.

**Learned recovery (results on real robots):**
- **FRASA** (Gaspard, Duclusaud, Passault, Daniel, Ly — Rhoban/LaBRI; ICRA 2025,
  arXiv:2410.08655; code github.com/Rhoban/frasa): one CrossQ agent unifies
  fall-recovery + stand-up on Sigmaban kid-size. Trains in **13–37 min** (CPU
  MuJoCo, ~235–575 k steps). Action = symmetric joint-velocity increments (sagittal
  symmetry halves the action space); state = bilateral-averaged `q, q̇, q_des`,
  trunk pitch + rate, last-k actions. Real results vs the RoboCup-2023 champion KFB
  routine: prone get-up **2.14 s vs 3.15 s**, supine **2.68 s vs 5.06 s**; post-
  disturbance re-stabilization 40–51 % of KFB time; 20 trials/side.
- **UHG — Unified Humanoid Get-Up** (RoboCup 2025,
  github.com/utra-robosoccer/unified-humanoid-getup): extends FRASA to **one policy
  across 7 robot morphologies** (Wolfgang, NUGUS, Bez1-3, OP3-Rot), generalized
  reward, zero-shot cross-morphology recovery; Gym/MuJoCo + SB3 CrossQ.
- **HumanUP** (He, Dong, Chen, Gupta — UIUC/SFU; RSS 2025, arXiv:2502.12152;
  humanoid-getup.github.io): two-phase curriculum — phase 1 discovers a get-up
  trajectory under relaxed smoothness/limits, phase 2 refines it into slow, smooth,
  robust motion. On a real Unitree G1 across 6 terrains: **78.3 % get-up success**
  (vs 41.7 % manufacturer controller), 98.3 % prone→supine rollover; posture
  randomization over initial fallen configs is the key ingredient.
- **HiFAR** (Chen, Wang, Luo, Cai, Zhao — Tsinghua; hi-far.github.io): multi-stage
  curriculum for high-dynamics humanoid fall recovery, real-robot eval.
- **"Learning to Get Up"** (SIGGRAPH 2022, doi 10.1145/3528233.3530697): staged RL —
  strong model first, then progressively weaker, then slower — discovers diverse
  prone/supine strategies without mocap; informed HumanUP's curriculum.
- **MuJoCo Playground Go1 fall-recovery env** — shipped, sim2real-validated
  reference implementation of a learned stand-up task (arXiv:2502.08844).

**Microduck's production answer** — the most relevant recipe for us (§1.2):
spawn-state curriculum (standing/sitting → face-down → face-up, easy→hard over
~2500 iters; flat 25/25/25/25 from step 0 under-trains the hard poses into
"do-nothing"), reverse-curriculum spawns (face-up with ±90° partial roll;
near-done starts) because flat-supine→prone has a flat reward landscape, rewards =
`com_upward_velocity` bootstrap + two-layer upright (cos(tilt) far-field + sharp
Gaussian near-field, z-gated against the "crouch low and vertical" exploit) +
multiplicative standing composite + |a_z| gentle-rise cap 0.005 + late-introduced
(iter 3000) arrival-damping/joint-torque-rate smoothing. Then **distill the stand
expert + walk expert into one velstand policy** that also "falls protectively".

**Fall detection & pose classification (deterministic, not learned):**
- `fallen` verdict: projected gravity vs `[0,0,−1]` beyond a tilt threshold +
  dwell time (microduck runtime does exactly this; NimbRo 2006 same idea);
  stale-IMU watchdog matters because a frozen estimator reports a plausible
  attitude forever (microduck counts stale reads).
- Rest-pose class from gravity vector + joint encoders: back / front / side /
  sitting — pick recovery policy per class (the classify-then-script KFB pattern
  is our deterministic MVP; the learned velstand subsumes it later).

---

## 5. Classical vs learned split

**Must be deterministic (never in a policy):**

| Function | Why deterministic | Reference implementation |
|---|---|---|
| Joint limit clamps & rate clamps on every outgoing command | Safety invariant; policies exploit any gap | microduck `robotd` "safety clamps things constantly"; ODM 5.24 rad/s target slew |
| Watchdog / deadman switch on command source | Lost gamepad/SSH must not freeze gait mid-step | microduck "deadman — no intent arrived recently, velocity zeroed" |
| Fall detection + fallen-state entry (cut torque / damp / limp) | A thrashing 1 kg robot strips its own gears | microduck `fallen` verdict + "limp-fall" switch; NimbRo joint relaxation on landing |
| Battery monitor → sit-down → power cut | LiPo below safe V; brownout mid-motion is worse | microduck `BATTERY_EMPTY_V` sit-and-cut |
| Servo temperature monitor → torque-limit/standdown | Hobby servos cook during recovery drilling | microduck "hottest servo" health row |
| Servo calibration (ID, offsets, zero vs `home` keyframe) | #1 documented sim2real failure | ODM `duck_config.json` offsets; writeup §4 |
| Startup posture interpolation (boot → home over ~2 s) | Cold-start torque spike / snap | ODM `turn_on()` + sleep; standard keyframe ease |
| Stale-sensor & loop-rate watchdogs | Silent sensor death looks fine to the policy | microduck stale-read counters, "control loop at 43.9 Hz" unhealthy |
| ONNX contract validation (shape, NaN, constant output) | Bad policy file must never reach the bus | microduck publish gate `[1,61]→[1,14]` + smoke inference |

**Benefits from learning:** walking (velocity/heading tracking), get-up from
arbitrary fallen poses, protective fall behavior, expressive tricks — all proven on
real 25–42 cm servos-only bipeds by the references above.

**Recommended loop architecture** (matches both references):

```
            ┌───────────────────── ON-ROBOT (SBC: Pi-class / RK3566-class) ──────────────┐
            │                                                                            │
 IMU 100-500 Hz ──► attitude est. (gravity vec, rates) ──┐                                │
 Servo pos/vel/temp/load ~50-100 Hz ──► state mirror ────┤                                │
 Foot switches / ToF (opt.) ────────────────────────────┤                                │
                                                        ▼                                │
   gamepad/ BLE ──► intent mux ──►  ┌───────────────────────────────────────────┐        │
   app/CLI commands ─────────────► │ SUPERVISOR FSM (deterministic)             │        │
                                   │ IDLE→STAND→WALK↔SIT↔FALLEN→RECOVER→SAFE    │        │
                                   │  • deadman, watchdogs, fall verdict        │        │
                                   │  • pose classifier (back/front/side/sit)   │        │
                                   │  • policy slot select (walk/stand/trick)   │        │
                                   └──────┬───────────────┬────────────────────┘        │
                                          │ command +     │ on FALLEN: class →          │
                                          │ 61-D obs      │ recovery policy (or KFB)    │
                                          ▼               ▼                             │
                                   ┌────────────────────────────┐                       │
                                   │ ONNX policy @50 Hz          │  walk / velstand /    │
                                   │ (normalizer baked in)       │  get-up / tricks      │
                                   └────────────┬───────────────┘                       │
                                                ▼ raw 14-D actions                      │
                                   ┌────────────────────────────┐                       │
                                   │ SAFETY LAYER (deterministic)│  joint-limit &        │
                                   │ slew clamp, temp de-rate,   │  velocity clamp,      │
                                   │ fallen→limp, lowV→sit+cut   │  LPF (only if trained │
                                   └────────────┬───────────────┘  with it!)            │
                                                ▼                                        │
                                   serial servo bus @50–100 Hz                           │
                                   (write goal pos / kp; read pos/vel/temp/load)         │
            └───────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼   inside each servo: internal P(D) loop
                                         ~1 kHz+ closes position → torque
```

Rates: IMU fusion at 100–500 Hz feeding a 50 Hz policy is plenty (both refs run
policy at 50 Hz; FRASA proved policy-rate mismatch is survivable: train 20 Hz,
deploy 100 Hz, with increment-style actions). Keep servo telemetry reads
interleaved with command writes — the bus is half-duplex and each read costs a
command slot; budget ~50 Hz total and share it (that's why obs delays are
randomized).

---

## 6. Staged development plan

Entry criteria are *gates*: do not advance until met. "Sim-vs-real" = compare
logged real joint/IMU traces against sim rollouts of the same policy, per
writeup §8.2.

| # | Stage | What | Entry criteria → exit metrics | Validation |
|---|---|---|---|---|
| 0 | **Calibration & SysID** | Servo IDs/offsets; every joint zero vs `keyframe("home")`; BAM-style identification: step responses at several loads (pendulum or leg-lift), per-joint backlash measurement, real mass/CoM (scale + balance) | All joints track step commands; measured params exported to MJCF | Sim step-response vs real step-response overlay per joint (target: shape match, not just final angle) |
| 1 | **Supported standing** | Robot held by harness/gantry, feet on ground: servo P-hold + IMU read; verify obs pipeline produces sane 61-D-ish vector in real time at 50 Hz | 60 s hold, no saturation, joint tracking err < ~3° RMS | Log obs on real robot → replay through trained policy offline (ONNX) → confirm sane actions before powering the bus ("rehearsal") |
| 2 | **Free standing** | PPO stand/hold policy trained in sim with full DR; deploy behind deadman + fall verdict | Sim: holds 60 s under ±0.3 m/s pushes ≥ 90 % of evals → Real: stands unassisted 60 s, recovers from gentle pushes | Sim-vs-real tilt & joint-vel PSD comparison; tune encoder bias + IMU misalignment calibration from real logs |
| 3 | **Sit ↔ stand** | KFB sit/stand trajectories first (deterministic), then learned `SitStand` policy; measure real SIT_Z/STAND_Z equilibria, feed back into sim targets | KFB: 10/10 sits & stands; policy: ≥ 9/10 transitions, |a_z| spikes within servo-safe bound | Compare real trunk-height trace vs sim; the measured Z replaces assumed Z in rewards (microduck's 5 mm lesson) |
| 4 | **Walking gait** | Velocity-tracking PPO policy: imitation reward from parametric gait (PlaCo-style polys) or scratch with the ODM reward set | Sim: tracks vx/ψ̇ within σ for 20 s episodes ≥ 95 % → Real: walks 2 m straight, turns ±90°, survives 5/5 gentle pushes | Log real obs+actions @50 Hz; replay-obs through policy to isolate perception vs actuation gap; tighten DR to measured params |
| 5 | **Predefined-pose recovery (KFB)** | Deterministic: fall verdict → pose classify (gravity vec + joints) → per-class scripted get-up (NimbRo/FRASA-KFB pattern). Also the permanent fallback if learned recovery regresses | ≥ 8/10 get-ups per class (back, front) on flat floor; aborts safely if stuck (retry counter, temp cap) | Scripted trajectories debugged in sim first (spawn from prone/supine keyframes); real trial log per class |
| 6 | **Learned recovery** | Option A (cheap): FRASA-style CrossQ get-up agent (CPU-trainable in <1 h, symmetric 5-DoF actions). Option B (ambitious): microduck-style StandUp expert → distill into unified velstand policy | Sim: ≥ 90 % get-up across spawn battery (prone/supine/random-SO3, random joints) → Real: ≥ 8/10 prone, ≥ 7/10 supine, time-to-stand ≤ ~2× sim | Per-spawn-class eval battery in sim *and* on robot; the microduck "rise battery"; watch |ω| during rise (their p50 was 11 rad/s pre-fix) |
| 7 | **Robustness & soak** | Backlash-model retrain; rough-terrain variant; push battery; 20+ falls/day soak | N=50 falls mixed classes ≥ 80 % recovered; servo temps < thermal limit throughout; no stripped gears | Long-run temp/loop-rate logs; repeat SysID after soak (backlash grows — re-measure) |

Cross-stage rules learned from the references: smoke-test every training change
(64 envs × 5 iters); never deploy a policy that hasn't passed CPU-MuJoCo ONNX
rehearsal; every wandb penalty term must be ≤ 0; measure equilibrium heights on
the real robot rather than trusting keyframes; **pick checkpoints by the probe
battery, not by training curves** (identical metrics hid yaw asymmetry between
microduck checkpoints).

---

## 7. Metrics that matter

| Metric | How measured | Reference target |
|---|---|---|
| Recovery success per starting pose | N ≥ 20 trials per class (back/front/side/sit), sim battery mirrored on hardware | FRASA-style: report per-class %; HumanUP: 78 % real, 98 % rollover; microduck sim: 93–95 % after push-falls |
| Time-to-stand | fall-verdict → `upright && stable` timestamp | FRASA: 2.1 s prone / 2.7 s supine on kid-size; expect 2–4 s at our scale |
| Joint tracking error | RMS |cmd − measured| per joint during gait & recovery | use during stage-0/1; rising trend = backlash growth |
| Rise violence | max |a_z|, |ω| p50 during get-up; servo-impact contact count | microduck tracked |ω| p50 ~11 rad/s pre-fix; lower is better |
| Energy per recovery | ∫(Σ τ·ω) or bus current × V integral per event | compare KFB vs learned; temperature proxy below |
| Servo temp rise | per-servo temp before/after event & soak ΔT | microduck "hottest servo" health metric; cap trials on temp |
| Repeatability | success rate drift over N ≥ 50 trials & across days | catches wear/backlash drift (re-run SysID on drift) |
| Loop-rate quality | achieved control Hz, p50/p95/p99 policy inference latency on-device | 50 Hz nominal; microduck flags < nominal as unhealthy |
| Command-vs-applied divergence | what supervisor asked vs what safety layer applied | microduck monitor shows both; divergence named (deadman, clamps) |
| Push-fall rate during walking | falls per 100 pushes at fixed impulse | velstand probes: 0–9 % fall rate v7 on flat+backlash |

---

## 8. Honest risks

1. **Hobby-servo sim2real gap is THE risk.** Both duck projects spent most effort
   here, not on RL. Position-servo dynamics (internal P loop, deadband, backlash,
   temperature-dependent torque, voltage sag) dominate the gap — Microduck models
   down to the voltage-control law for this reason. Mitigate: BAM identification
   on OUR servo model before any training (params exist for STS3215-7.4 V and
   XL330 — pick a servo whose BAM params exist, or budget a week for the pendulum
   SysID bench).
2. **No torque control.** Consequences: (a) compliance is only as good as the
   internal kp we can write — ODM runs kp=30 (P-only, kd=0) and FRASA *reduced* kp
   on real+sim together to stop tremors; (b) "limp/damped" fall protection means
   actively writing goals or torque-off, not impedance — practice the limp-fall
   path early; (c) recovery motions must stay inside servo torque-speed curves —
   a learned policy can demand a physically impossible step-response if forcerange
   is wrong in sim.
3. **Backlash grows with use.** 3D-printed gear trains and hobby servos wear;
   ±1° today, asymmetric 3°+ after weeks (duck writeup). Options: train on the
   backlash model from day one (both refs do), re-measure periodically, add
   threadlocker to the build SOP.
4. **Bus bandwidth.** Half-duplex serial: writing 10–14 goals + reading pos/vel/
   temp/load at 50 Hz is feasible (both refs do it) but leaves little headroom;
   sensor reads may need decimation (e.g., temp at 2 Hz) — and each read pattern
   should match what the obs-delay DR assumed.
5. **Compute split.** ONNX at 50 Hz is trivial for a Pi-class CPU (ODM does it on
   a Pi Zero 2 W); the risk is Python jitter — microduck chose Rust daemons.
   Budget: deterministic MCU servo-bridge + SBC policy host (our brief's split
   arch) mirrors this nicely: the MCU owns clamps/watchdog/servo bus; the SBC owns
   obs assembly + ONNX + FSM.
6. **GPU-less training.** mjlab/Warp needs CUDA. Options: HF Jobs (microduck
   supports `--hf-jobs`), Colab, rented 4060-class GPU (duck writeup used Vast.ai),
   MJX/JAX on any GPU, or **CPU MuJoCo + CrossQ for the get-up task (FRASA: 37 min)**.
   Walking policies want GPU-parallel envs (millions of steps); episodic recovery
   does not.
7. **Reward hacking / "do-nothing" attractors** are the dominant training failure
   (both AGENTS.md and the standup cfg comments: any attempt-tax during discovery
   freezes recovery). Budget 2–5 reward-iteration cycles per new skill and copy
   the published recipes literally before improvising.
8. **Single IMU, no foot sensors on our MVP?** Microduck gets away with proprio
   only; ODM uses foot switches (obs includes 2 contact bits). If we skip foot
   switches, obs must drop those dims — fine, but train without them from the
   start; a contact bit that lies (bouncy switch) is worse than none.

## 9. Recommended stack (summary)

- **Physics:** MuJoCo; MJCF from onshape-to-robot-style export with measured
  masses; two model variants — `walk` (feet-only collisions) and `groundcontact`
  (curated body collisions so the robot can actually lie down).
- **Actuator:** BAM — start from pre-identified params for the chosen servo
  (STS3215-7.4 V or XL330), verify on a 1-joint pendulum bench, then choose:
  (a) BAM→MJCF fields (ODM, simpler) or (b) BAM-as-actuator voltage model
  (Microduck, higher fidelity, needs mjlab-style actuator plugin).
- **Training:** mjlab + rsl_rl PPO on any CUDA GPU or HF Jobs for the gait/velstand
  family; MuJoCo CPU + SB3 CrossQ for the dedicated get-up agent (FRASA recipe);
  ONNX export with baked obs-normalizer as the only deployment path.
- **Runtime:** split-arch — MCU owns servo bus + deterministic safety (clamps,
  watchdogs, limp-fall, battery sit-down, temp de-rate); SBC owns FSM, obs
  assembly, ONNX at 50 Hz; `duck-sim`-style daemon-vs-sim integration test in CI.
- **Behaviors:** KFB sit/stand + per-pose-class scripted get-up as the v1
  fallback; learned velocity gait; then StandUp expert → distilled velstand as
  the flagship "falls protectively and gets back up" behavior.

## Source list

- Open Duck Mini: github.com/apirrone/Open_Duck_Mini, /Open_Duck_Mini_Runtime,
  /Open_Duck_Playground (`playground/open_duck_mini_v2/joystick.py`, `base.py`),
  /Open_Duck_reference_motion_generator; docs/sim2real.md;
  opensourcerobotics.dev/robots/open-duck-mini
- Microduck: github.com/pollen-robotics/microduck (+ docs/robot/cheatsheet.md,
  docs/recurrent-policies.md, docs/policy-manifest.md),
  github.com/pollen-robotics/microduck_rl (README, AGENTS.md,
  docs/velstand_policy.md, src/mjlab_microduck/tasks/microduck_*_env_cfg.py,
  robot/microduck_constants.py); pollen-robotics.com/microduck
- mjlab: github.com/mujocolab/mjlab; mujocolab.github.io/mjlab
- MuJoCo: github.com/google-deepmind/mujoco (Apache-2.0 since May 2022;
  deepmind.google blog Oct 2021); mujoco_playground arXiv:2502.08844
- BAM: github.com/Rhoban/bam; bam.readthedocs.io; paper arXiv:2410.08650
- FRASA: arXiv:2410.08655 (ICRA 2025); github.com/Rhoban/frasa
- UHG: github.com/utra-robosoccer/unified-humanoid-getup (RoboCup 2025)
- HumanUP: arXiv:2502.12152 (RSS 2025); humanoid-getup.github.io
- HiFAR: hi-far.github.io/paper.pdf
- Learning to Get Up: doi 10.1145/3528233.3530697 (SIGGRAPH 2022)
- NimbRo KFB get-up: ais.uni-bonn.de/nimbro/papers/IAS9.pdf; IROS-2018 slides
  ais.uni-bonn.de/behnke/talks/IROS_2018_Workshop_Humanoid_Falling_Sven_Behnke.pdf
- Disney BDX: arXiv:2501.05204 (RSS 2024)
- Sim-to-real failure analysis: zhenghaoxu.com/duck%20writeup.pdf
- TorchRL MicroDuckEnv: docs.pytorch.org/rl/stable/tutorials/microduck.html
- Isaac Gym deprecation: developer.nvidia.com/isaac-gym/download; Isaac Lab 3.0:
  isaac-sim.github.io/IsaacLab; Gazebo Classic EOL: gazebosim.org
- ToddlerBot (SysID-driven zero-shot transfer): arXiv:2502.00893;
  Berkeley Humanoid Lite: lite.berkeley-humanoid.org (RSS 2025),
  github.com/HybridRobotics/berkeley-humanoid-lite
