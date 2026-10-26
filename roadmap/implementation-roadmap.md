# Implementation Roadmap — Knoll Mk1

**Date:** 2026-10-26 · For downstream engineering agents. Dependency-ordered work packages; each WP lists inputs, outputs, and its verification gate from `validation/test-plan.md`.

---

## Phase 0 — Foundations (no hardware spend yet)
| WP | Task | Depends on | Output | Gate |
|---|---|---|---|---|
| P0.1 | Lock shared brief v1.0: final servo pick → mass budget, dims, voltage, DOF | actuator-study, this doc | updated shared-design-brief.md | review |
| P0.2 | CAD skeleton: chassis plate, hip block, leg struts with servo placeholders (STEP, parametric) | P0.1 | `mech/` CAD v0 | dims vs joint table |
| P0.3 | MuJoCo MJCF model from CAD (mass/inertia honest) + simple sim scene | P0.2 | `rl/robot.xml` v0 | loads, joints move, mass ±5% |
| P0.4 | Repo scaffold + licences + NOTICE | licensing doc | public-ready skeleton | checklist |

## Phase 1 — Bench proof (buy: 1 servo, MCU board, IMU, bench PSU)
| WP | Task | Output | Gate |
|---|---|---|---|
| P1.1 | Servo protocol driver on RP2350 (sync read/write, 1 Mbaud, error handling) | `firmware/bus` | single servo moves, reads pos/temp/voltage — A1 subset |
| P1.2 | IMU bring-up (BNO085 UART/SPI) + quaternion stream | `firmware/imu` | quaternion vs rotation sanity |
| P1.3 | L1↔L3 wire protocol + loopback test | `runtime/bridge` | 100 Hz roundtrip, CRC, resync test |
| P1.4 | **Servo characterisation rig:** step responses, deadband, backlash, max continuous torque guess vs heat, current draw | `docs/servo-report.md` → feeds BAM-style actuator model | measured params recorded |
| P1.5 | Schematic capture in KiCad (control PCB) | `pcb/` v0 | ERC clean, peer review |

## Phase 2 — Structure & power (buy: servos ×10, battery, PCB fab, print)
| WP | Task | Output | Gate |
|---|---|---|---|
| P2.1 | Leg prototype ×1 (printed, 5 servos) — range sweep, backlash measure, cable test | leg asm | M2/M3 |
| P2.2 | Full chassis + both legs + dome — dry assembly, mass check | robot shell | M1/M4 |
| P2.3 | PCB fab+assemble (JLCPCB) → power-tree bring-up on bench supply | control PCB | E1–E4 (peak current measurement fixes fuse) |
| P2.4 | Calibration routine + joint table flash | `firmware/calib` | A1–A5 all pass |
| P2.5 | Deterministic stand + sit (interpolated postures, CoM checked) | `runtime/postures` | B1–B4 |

## Phase 3 — Simulation & gait (parallel to P2 hardware bring-up where possible)
| WP | Task | Output | Gate |
|---|---|---|---|
| P3.1 | Actuator model in MuJoCo fitted to P1.4 measurements (+ backlash hinge model) | `rl/actuator` | sim vs bench step response overlay |
| P3.2 | PPO walk task (velocity tracking) + domain randomisation set | `rl/tasks/walk` | sim gait + deployable ONNX |
| P3.3 | Policy deploy path on device (ONNX Runtime, obs contract) | `runtime/policy` | policy runs @50 Hz on SBC |
| P3.4 | Real walk + tune loop | walking robot | C1–C5 |

## Phase 4 — Recovery & robustness
| WP | Task | Output | Gate |
|---|---|---|---|
| P4.1 | Fall detect + pose classification (IMU, deterministic) | `runtime/fall` | D4-classification part |
| P4.2 | StandUp task in sim per pose class (scripted first, policy second) | `rl/tasks/standup` | sim recovery ≥80% |
| P4.3 | Real recovery + safety (mats, kill practice) | get-up robot | D1–D5 |
| P4.4 | Robustness matrix runs (surfaces/payload/battery) | `docs/robustness.md` | F1–F4 published honestly |

## Phase 5 — Polish & release
| WP | Task | Output |
|---|---|---|
| P5.1 | Face/eyes + personality layer, gamepad UX, docs site | delightful robot |
| P5.2 | Update/rollback machinery + signed-ish releases | `updated` |
| P5.3 | Community release: CAD, PCB, BOM, build guide, quickstart, sim | public repo |
| P5.4 | v2 option spike: ankle_roll? neck? ToF? camera behaviours? | v2 decision memo |

## Critical path & risk notes
- **Longest lead:** servo choice → PCB (pinout depends on bus topology) → fab (~2 wks) — decide servo family FIRST.
- **Highest technical risk:** sim2real on cheap serial servos — P1.4 characterisation is deliberately BEFORE bulk purchase commitment (buy 1 servo first!).
- **Cost gate:** if servo pick busts budget (see electronics notes flag), P0.1 revisits: 10-vs-12 DOF, mixed servo tiers, or China-direct sourcing — cost model has the sensitivity table.
- **Do not parallelise:** MJCF before real mass/inertia; walking policy before actuator model fitted; recovery before gait stable.
