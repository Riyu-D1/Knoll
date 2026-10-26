# Validation & Test Plan — Knoll Mk1

**Date:** 2026-10-26 · **Status:** Acceptance criteria defined; all tests pending hardware/sim implementation. Nothing on this page is claimed as performed.

---

## 0. Test philosophy

- Every claim in the docs maps to a test here; a capability is only "done" when its gate passes N times under stated conditions.
- Sim-first: no real-robot milestone without its sim counterpart, and sim↔real diffs logged via shared telemetry format.
- All trials recorded (video + telemetry CSV) into the robot journal; success rate quoted as `passes/trials`, never anecdotes.

## Stage gates (A→F, mirroring control-and-recovery.md)

### Stage A — Actuator bring-up & calibration
| # | Test | Pass criterion |
|---|---|---|
| A1 | Bus scan finds all 10 servos + IMU @1 Mbps | 10/10 IDs respond, 0 CRC errors over 10⁴ reads |
| A2 | Per-servo position accuracy after horn-offset calib | commanded vs read pos ≤ ±2° at 5 test angles/servo |
| A3 | Limit enforcement: command beyond soft limit | L1 clamps; no motion past stop; fault logged |
| A4 | Watchdog: kill L3 link mid-command | torque ramp-down begins ≤150 ms; off ≤500 ms; robot stays still |
| A5 | Thermal read sanity | all servos report temp; values plausible vs ambient |

### Stage B — Supported standing & posture
| # | Test | Pass criterion |
|---|---|---|
| B1 | Static stand 10 min (tethered power allowed) | no fall; max joint tracking err ≤5°; servo temps <60°C |
| B2 | Sit↔stand×20 cycles | ≥19/20 clean transitions; ≤3 s each; no servo overtemp |
| B3 | Gentle push test (lateral, ~1 N·s impulse — measured by marked pendulum) | recovers stance without stepping ≥8/10 (or documented lesser result) |
| B4 | CoM check: robot balances statically on scale of feet vs model | measured CoM within ±10 mm of sim model (else fix model) |

### Stage C — Gait & movement
| # | Test | Pass criterion |
|---|---|---|
| C1 | Walk forward 3 m straight | reaches within ±15 cm lateral drift; ≥9/10 |
| C2 | Velocity tracking: commanded 0.03/0.05/0.08 m·s⁻¹ | actual within ±20% after 1 m |
| C3 | Turn in place ±90° | within ±20° of commanded, ≥8/10 |
| C4 | 15 min continuous walk battery test | completes without thermal ESTOP; record mAh consumed → runtime figure |
| C5 | Carpet + hardfloor + low-pile mat | pass C1 on each (or document which surface fails) |

### Stage D — Recovery from defined resting poses (scripted or learned)
| # | Test | Pass criterion |
|---|---|---|
| D1 | Laid flat on back → recover | stands in ≤15 s, ≥8/10 trials |
| D2 | Laid face-down → recover | same |
| D3 | Laid on left/right side → recover | same |
| D4 | "Knockover" from stand (gentle push to fall) → robot detects FALLEN, classifies, recovers | correct class ≥9/10; full recovery ≥7/10 |
| D5 | Damage check after 20 falls | no cracked prints, no stripped horns; face plate unscarred or replaced as designed |

### Stage E — Expanded learned behaviours
| # | Test | Pass criterion |
|---|---|---|
| E1 | Unified walk+recover policy (if trained) | D-criteria hold without scripted fallback |
| E2 | Random perturbation during walk (push, tilt board ±10°) | stays up or recovers ≥7/10 |

### Stage F — Robustness & characterisation (data, not gates — publish honestly)
- F1 repeat D1–D4 on: carpet/hardwood/mat; battery 100%/40%/15%; +100 g/+200 g payload; room temp vs warm servos
- F2 servo wear: 500 get-up cycles sample → gear play check (backlash measured, reported vs new)
- F3 brownout: walk to battery cutoff → verify brownout behaviour (safe collapse, not twitching)
- F4 drop table honesty: report any breakage from accidental drops as field-failure notes

## Electrical verification (pre-power checklist, then live)

- E1 visual + continuity: no shorts VCC-GND on each rail; fuse values correct; polarity markings
- E2 first power with 100 mA current-limited bench supply → logic rails 3.3V±5%, 5V±5%
- E3 servo bus powered separately first: single servo responds, then full bus
- E4 worst-case current: command all-servo aggressive move on bench supply → record peak; must be < 80% of fuse/regulator/battery-C rating → **this test sets the final fuse value**
- E5 brownout threshold: measure voltage at SBC/MCU during peak servo event; no rail sag below spec
- E6 thermal: 10 min loaded run → board temps <60°C, regulator <70°C (finger/IR check)
- E7 reverse polarity / wrong connector: prove protection (must not blow board)
- E8 E-stop path: mechanical cut removes motor power, logic stays alive for telemetry

## Mechanical verification before first power-on

- M1 all fasteners torqued per list; inserts seated; threadlocker where specified
- M2 joint range sweep by hand: smooth through range, no binding, no cable snag
- M3 backlash measurement per joint (dial or camera): record — feeds the sim backlash model
- M4 mass check: whole robot within ±5% of mass model; CoM hang-test vs sim

## Definition-of-done for the public claims we may make

- "walks" ⇐ C1–C5 pass · "sits/stands" ⇐ B2 · "gets back up" ⇐ D1–D4 with per-pose rates published · "X hours battery" ⇐ C4 measured · "robust" ⇐ F1 table published with honest numbers.
