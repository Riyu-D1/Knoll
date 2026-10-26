# Software System Architecture — Knoll Mk1

**Date:** 2026-10-26 · **Status:** Architecture specification for implementation agents. Patterns are informed by the reference stack (Apache-2.0 — studied, not copied); all interfaces and code are original.

---

## 1. Layered architecture

```
┌─────────────────────────────────────────────────────────────┐
│ L4  Clients (optional): gamepad · phone/desktop app ·       │
│     dashboard · future AI agent · training tools            │
│        │  bounded intent API (never raw motor commands)     │
├─────────────────────────────────────────────────────────────┤
│ L3  Robot runtime (SBC, Linux):                             │
│     motiond — 50 Hz policy loop, behaviour/state machine    │
│     safetyd — watchdog + health gate (own process, no deps) │
│     configd — wifi, identity, pairing                       │
│     updated — signed-ish releases, A/B swap, rollback       │
│     mcpd/api — JSON-RPC IPC over unix sockets (one socket/  │
│       service, NDJSON) + optional BLE/WebSocket transports  │
├─────────────────────────────────────────────────────────────┤
│ L2  Motion bridge (SBC↔MCU wire protocol):                  │
│     length-prefixed binary frames over UART-USB or UART;    │
│     cmd: joint targets + mode; evt: telemetry + faults      │
├─────────────────────────────────────────────────────────────┤
│ L1  Real-time controller (MCU, bare-metal/RTOS):            │
│     owns servo bus UART + IMU SPI/I2C; 50–100 Hz loop:      │
│     sync_read servos+IMU → queue to L3 / execute last       │
│     valid cmd → sync_write; ENFORCES joint limits, clamp    │
│     rates, watchdog torque-off — even if L3 is dead         │
├─────────────────────────────────────────────────────────────┤
│ L0  Servos (serial bus, 1–2 UARTs) + IMU + power mgmt       │
└─────────────────────────────────────────────────────────────┘
```

**Non-negotiable rules (safety invariants):**
1. **L1 owns the motors.** Everything above proposes; L1 disposes (clamps to limits, rate-limits, torque-off on watchdog/estop). Mirrors the reference's `safety`-owns-`RobotIo` principle — enforced by architecture, not convention: nothing else has a handle to the servo UART.
2. **Watchdog:** L1 torque-limits (never hard-drops under load — drop = collapse → torque *ramp-down*) if no heartbeat cmd from L3 within 150 ms, and torque-off within 500 ms.
3. **Bounded intents only:** clients speak intents (`move(vx,vy,wz)`, `posture(name)`, `recover`, `stop`) and joint targets go through the same validation path as policy outputs. There is NO API that writes raw servo registers from above L1.
4. **Safe without cloud:** all shipped behaviours run fully on-device; network only adds clients. AI assistant is a client like any other, subject to identical bounds.
5. **Survivable failure:** configd/updated/safetyd have no dependency on motiond — a dead control loop still allows reconfigure/update/rollback (reference pattern, worth copying at concept level).

## 2. Process responsibilities (L3, Linux userland)

| Service | Owns | Talks to | Failure isolation |
|---|---|---|---|
| `motiond` | 50 Hz loop: read L1 telemetry → policy/FSM → targets → L1; behaviour state machine (IDLE/STAND/WALK/SIT/FALLEN/RECOVER/ESTOP); obs building; policy hot-swap behind fixed obs contract | MCU bridge, IMU via L1, other daemons' queries | restartable; L1 keeps robot safe meanwhile (torque ramp → lie still) |
| `safetyd` | independent watchdog of motiond health; thermal/voltage thresholds → demand safe posture; exposes `robot.health` | motiond (heartbeats), power monitor | minimal deps; the process updated asks before/after updates |
| `configd` | wifi creds (via NetworkManager/wpa_supplicant), robot name, pairing | OS networking | survives everything |
| `updated` | release verify → swap symlink → health gate → rollback; keeps per-board config outside releases | github/USB release bundle, safetyd | survives motiond death |
| `bridged` | the MCU UART link: framing, CRC, resync, link stats; exposes telemetry+command channel to motiond over socket | L1 MCU | if it dies, L1 watchdog safes the robot anyway |
| `mediad` (optional) | camera stream + snapshots | v4l2 | independent |
| `gamed` (optional) | BLE/USB gamepad → intents | motiond intents | independent |

Simplification for v1: `bridged` may fold into `motiond` as a non-blocking thread IF the 50 Hz loop keeps its own runtime and the socket layer can never block the tick (reference does exactly this: tokio task isolation). Decide at implementation; document the choice.

## 3. Intent & telemetry contract (versioned)

`intent` (client → motiond), JSON-RPC 2.0, NDJSON, one object/line:
```json
{"method":"robot.move","params":{"vx":0.05,"vy":0.0,"wz":0.3,"head":[0,0]}}
{"method":"robot.posture","params":{"name":"sit"}}
{"method":"robot.recover"}   // only legal from FALLEN state
{"method":"robot.stop"}      // immediate controlled stop; "robot.estop" = instant torque ramp-down
{"method":"robot.enable","params":{"on":true}}
{"method":"robot.state.subscribe","params":{"hz":10}}
```
`telemetry` (L1 → L3 binary frame → motiond → clients as `robot.state`):
```json
{"t":1234,"joints":{"pos":[...],"vel":[...],"load":[...],"temp":[...]},
 "imu":{"quat":[w,x,y,z],"gyro":[...]},"batt":{"v":7.4,"pct":62},
 "state":"WALK","faults":[]}
```
**Fixed obs contract** (adopt reference principle): one observation layout shared by all policies (proprioception + command slots, zero-padded when unused) so policies hot-swap without runtime changes. Proposed: 48-dim proprio (pos/vel/last-action history, gravity vector, phase clock) + cmd slots [twist(3), posture(4), misc(6)] = 61-dim — same class, our own layout defined in `policy-contract.md` (roadmap item).

## 4. State machine (motiond)

```
POWER_ON → CALIBRATE → IDLE_SAFE (torque on, hold) ⇄ STAND
STAND ⇄ WALK ⇄ SIT ⇄ STAND
any → FALLEN (IMU: |up-axis| tilt > 60° for >300 ms, or free-fall+impact)
FALLEN → classify pose (supine/prone/left/right/sitting-ish) → RECOVER(policy|script per class)
RECOVER → STAND (success) | → FALLEN-retry ≤3 | → LIMP (torque off, beep, log)
any → ESTOP (torque ramp 200 ms → off; requires explicit re-enable)
LOW_BATTERY(<20%) → demand SIT → IDLE_SAFE; CRITICAL(<10%) → ESTOP
THERMAL(any servo > limit) → degrade speed → demand SIT → ESTOP
```

Deterministic (no ML): calibration, joint limits, posture interpolation primitives, fall detection/classification (IMU thresholds), watchdog, battery/thermal gates.
Learned (policy): walking, get-up recovery (Stage E+), expressive motion. Sit/stand ships deterministic first, policy later if it earns its place on metrics.

## 5. Firmware (L1) spec

- Loop: 100 Hz target (50 Hz min) — sync_read all servos + IMU → DMA frame up → apply latest cmd targets → sync_write.
- Enforces: per-joint min/max pos, max vel, max temp (from servo regs), bus fault counters, cmd watchdog (150/500 ms), torque ramp-down profile.
- Config: joint table flashed from a signed-by-tool config blob; calibration offsets in MCU flash; `calib` mode assists horn-offset routine.
- Update: USB/UART bootloader; version handshake with bridged; refuses mismatched protocol.
- Language: Rust (embassy or rtic) or C (FreeRTOS) — decide on MCU pick (RP2350 → either; ESP32-S3 → Rust/esp-idf). Rust preferred for parity with team skills and safety, not required.

## 6. AI-assistant interface (v2-ready, safe-by-design now)

- External agents reach motiond through the SAME intent API + a declarative `capability manifest` (`GET robot.capabilities` → states, intents, bounds, constraints).
- Rate-limited, intent-validated, logged to the robot journal. Assistant cannot extend bounds; new behaviours ship as policies/actions, not prompt hacks.
- Fully offline-capable baseline: on-device "assistant" v1 = command grammar + telemetry answers; cloud LLM is an optional client.

## 7. Logging, diagnostics, test hooks

- `vetbook.json`-equivalent: lifetime event log (faults, falls, recoveries, temps, update history) — invaluable for a repairable DIY fleet.
- Telemetry sinks: ring buffer on-device (~24 h), optional MQTT/UDP stream, sim-side CSV replay tool (shared format sim↔real — enables the sim-vs-real diff metrics in the validation plan).
- Fakes: `motiond --sim` talks identical protocol to MuJoCo model; `bridged --loopback` for CI; servo-bus replay files for firmware HIL tests.

## 8. OS & packaging (preliminary, pending Agent D compute pick)

- Linux (Debian/Armbian-class), systemd units per daemon, read-only-friendly root except /var/lib.
- Update = whole-bundle swap (`/opt/knoll/releases/<ver>` + `current` symlink + health gate + boot counter) — the reference's proven model at hobby scale.
- No ROS dependency for v1 (daemon+socket design keeps it lean; ROS2 bridge = optional client later). Justification: 50 Hz loop + small team → simpler stack wins; revisit if community demands.
