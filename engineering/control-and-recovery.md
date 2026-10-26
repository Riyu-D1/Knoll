# Control, Self-Recovery & Simulation Architecture — Knoll Mk1

**Date:** 2026-10-26 · **Status:** Architecture + staged plan defined. All external claims cited (see `engineering/notes-control.md` for full evidence and `research/sources.md`). None of our own performance figures exist yet — everything below is a target or a cited reference result.

---

## 1. What the evidence says (reference class, verified)

Two independent open projects solved exactly this problem; both converged on the same architecture — our design follows the same pattern deliberately:

| | Open Duck Mini (apirrone) | Microduck (Pollen/HF) |
|---|---|---|
| Robot | ~42 cm, ~1.4 kg-class | 25 cm, 780 g |
| Servos | **14× Feetech STS3215 7.4 V** (same family we selected) | 14× XL330 + beak servo |
| Compute | **Pi Zero 2 W** (our pick) | RK3566 SBC |
| Policy | 50 Hz, ONNX, position targets `home + a·0.25`, slew 5.24 rad/s, servo kp=30 P-only | 50 Hz, ONNX `[1,61]→[1,14]`, normalizer baked in |
| Sim | MuJoCo MJX (playground fork) + PPO | mjlab (MuJoCo Warp) + rsl_rl PPO, ~1–2 h @4096 envs |
| Actuator model | BAM identified params → MJCF fields | BAM M6 voltage-law model, delay 60–120 ms, battery sag DR, ±1° backlash hinges |
| Recovery | — | VelStand: walk+stand experts distilled; 93–95% sim get-up after push-falls |

Cited recovery literature with real-robot results: **FRASA** (ICRA 2025): learned get-up beats the RoboCup-champion scripted routine — 2.14 s prone / 2.68 s supine vs 3.15/5.06 s, trained on **CPU MuJoCo in 13–37 min**; **HumanUP** (RSS 2025): 78.3% real-robot get-up via two-phase curriculum; NimbRo IAS-9 (2006): the deterministic classify-pose→scripted-get-up baseline still used across RoboCup.

## 2. Simulator decision: MuJoCo — full stop

Both references independently chose MuJoCo; BAM (identified servo dynamics incl. pre-fitted params for `feetech_sts3215_7_4V`) lives in its ecosystem; CPU eval runs on any laptop; GPU scales via MJX-Playground or mjlab. Rejected: Isaac Gym (deprecated), Isaac Lab (NVIDIA-heavy overkill at 1 kg), PyBullet (weakest contact/actuator fidelity), Gazebo (wrong tool for batch RL).

**Training stack:** gait family = mjlab + rsl_rl PPO (CUDA GPU or `--hf-jobs`); **get-up agent = MuJoCo CPU + SB3 CrossQ (FRASA recipe — GPU-free, <40 min)**; export = ONNX with obs-normalizer baked in, only deployment path. GPU-less contributors can still train recovery + scripted baselines.

## 3. Control architecture (deployed)

```
 SBC (Pi Zero 2 W)                          MCU (RP2350)
┌────────────────────────────────┐   UART/USB ┌──────────────────────────┐
│ motiond 50 Hz:                 │◄──────────►│ real-time node:          │
│  FSM (IDLE/STAND/WALK/SIT/     │  binary    │  2× servo bus @1Mbaud    │
│  FALLEN/RECOVER/ESTOP)         │  frames    │  BNO085 read             │
│  obs assembly (fixed contract) │            │  joint-limit + slew clamp│
│  ONNX policies (walk, standup) │            │  WATCHDOG: no cmd >150ms │
│  deadman on intents            │            │   → torque ramp-down     │
│  fall verdict (gravity vec)    │            │  low-V derate → cutoff   │
│  pose classifier (back/front/  │            │  temp derate             │
│   side/sit) → recovery select  │            │  owns bus — sole writer  │
└────────────────────────────────┘            └───────────┬──────────────┘
                                                          ▼
                                          Bus A: L leg ×5 · Bus B: R leg ×5 (+aux)
```

**Deterministic (never learned):** joint/rate clamps on every command, deadman, fall verdict (projected-gravity vs −z + dwell), pose classification, battery→sit→cut, temp derate, stale-IMU watchdog, loop-rate watchdog, ONNX shape/NaN gate, calibration & home-keyframe check, startup interpolation.
**Learned:** velocity gait, get-up, expressive tricks — each an ONNX behind the shared obs contract.

Position-servo reality (design consequence): no torque control → compliance = written kp values (ODM: kp=30 P-only); "limp fall" = torque-off; recovery motions must live inside the servo torque-speed curve (forcerange in sim must be honest).

## 4. Sim-to-real method (adopted wholesale from the evidence)

1. **Actuator identification before training:** BAM pendulum SysID on OUR servo (pre-id params exist for `feetech_sts3215_7_4V`; ST3020 needs the bench procedure — roadmap P1.4). Export → MJCF `damping/kp/frictionloss/armature/forcerange`.
2. **Latency explicit:** cmd delay 60–120 ms DR; obs delays per-term; encoder bias ±0.015 rad.
3. **Backlash as physics:** passive ±1° hinge per joint; obs read through play; re-measure after wear.
4. **DR set (converged reference values):** foot friction ×[0.7,1.3], trunk CoM ±15 mm cap, mass/inertia ±5%, armature ±10%, battery V + sag, IMU misalign ~6°, pushes ±0.3 m/s curriculum, joint/IMU noise.
5. **SysID > DR for systematic error:** measure real mass/CoM/zeros; randomize around measured. Purdue's duck writeup is the cautionary tale — a sim-winning policy failed on hardware from loose screws + wrong joint zeros.
6. **Two model variants:** `walk` (feet-only contacts) and `ground` (body can lie — dome collision as sphere-cap for get-up).
7. **Rehearsal gate:** every ONNX runs CPU-MuJoCo + on-device latency check before it touches the bus.
8. **Real2sim2real:** log real obs+actions @50 Hz → replay through policy → diff → refit model.

## 5. Staged plan with gates (mirrors validation/test-plan.md)

| Stage | Content | Exit gate |
|---|---|---|
| 0 SysID | IDs/offsets, zeros vs home keyframe, BAM fit, per-joint backlash, real mass/CoM | sim vs bench step-response overlays match in shape |
| 1 Supported stand | harness hold, obs pipeline live @50 Hz, replay-through-policy sanity | 60 s hold, tracking <3° RMS |
| 2 Free stand | stand policy behind deadman+fall-verdict | sim ≥90% under pushes → real 60 s + gentle-push recovery |
| 3 Sit↔stand | scripted KFB first; measure real SIT_Z/STAND_Z → feed back | 10/10 KFB; ≥9/10 policy |
| 4 Gait | velocity PPO + imitation reward | sim 95% tracking → real 2 m straight, ±90° turns, 5/5 pushes |
| 5 Recovery (KFB) | classify→scripted get-up per pose; permanent fallback | ≥8/10 back+front on flat |
| 6 Learned recovery | CrossQ get-up (FRASA) → optional StandUp expert → unified velstand | sim ≥90% across spawn battery → real ≥8/10 prone, ≥7/10 supine |
| 7 Soak | 50+ mixed falls, backlash retrain, re-SysID | ≥80% recovery across matrix; temps in limits |

## 6. Metrics (targets anchored to citations)

- Recovery success per pose class, N≥20: report per-class % (HumanUP real: 78.3%; microduck sim: 93–95% — ours published honestly, likely lower first pass)
- Time-to-stand: target ≤4 s (FRASA kid-size: 2.1–2.7 s)
- Rise violence: |a_z| and |ω| p50 during get-up; servo-impact contacts
- Joint tracking RMS error; drift = backlash growth indicator
- Servo ΔT per event + soak; energy per recovery (bus V×I integral)
- Loop rate achieved + policy inference p50/p95/p99 on-device

## 7. Honest risks (ranked)

1. **Hobby-servo sim2real gap = THE risk** — mitigate with BAM SysID before training, measured-params DR, early hardware eval.
2. **No torque control** — compliance only via kp writes; limp-fall rehearsed early.
3. **Backlash grows** — train on backlash model from day 1; threadlocker SOP; re-SysID schedule.
4. **Bus bandwidth** — half-duplex reads cost command slots; temp decimated to ~2 Hz; obs-delay DR must match the real read pattern.
5. **Reward hacking/"do-nothing" attractors** — the dominant training failure per both references; copy published recipes literally before improvising; budget 2–5 reward iterations per skill.
6. **ST3020 ≠ pre-identified BAM model** — STS3215-7.4V params exist; our primary servo needs a bench identification (P1.4) or adopt STS3215 params + verify — flagged, cheap to close.
