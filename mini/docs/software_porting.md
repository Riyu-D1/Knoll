# Knoll Mini — software porting note (Session 5, simulation)

Scope: what it takes to get a walking policy running on the real robot. No
training was done or started here. Numbers marked [U] are unverified.

## (a) Policy transfer — retraining required
The upstream mjlab policy was trained for XL330 dynamics: kp 0.55, forcerange
±0.96 N·m, damping 0.053, armature 0.0018. The Knoll Mini runs SCS0009 with
forcerange ±0.226 N·m — the policy **will not transfer as-is**. Unknowns to
identify on the real servo [U]: position-gain equivalent (the SCS protocol
exposes P/I/D registers, not a kp), damping, armature/rotor inertia, friction,
backlash, and bus latency.

Simple ID procedure: command a position step over the bus, log goal position +
servo-reported position + current at 100 Hz; fit a second-order
(spring–damper–armature) actuator model per joint; repeat for a couple of load
cases. Then set those parameters in `scene_knoll_mini.xml` and retrain in mjlab.

## (b) Compute — ESP32-S3, no Linux
Options: (1) tiny MLP on-device via TFLite Micro / ESP-NN — deterministic
latency, no radio dependency, but the ~240 MHz MCU limits policy size;
(2) off-board inference from a PC over Wi-Fi at ~10–20 ms latency [U] — keeps
the full mjlab policy but adds a hard dependency on the link.
Recommendation: start with **off-board Wi-Fi inference** for bring-up (fastest
path, lets you iterate policies without reflashing), then quantize the working
policy to an on-device TFLite Micro MLP as the target. Keep an on-device
stand/fall-recovery reflex either way.

## (c) Servo bus
Feetech SCS (SCServo) protocol, half-duplex TTL at 1 Mbps, 14 servos on one
daisy chain. Each servo ships as ID 1 — the 14 IDs must be assigned one by one
with the FE-URT-1 USB adapter before chaining (SPEC §8). The ESP32-S3 drives the
bus through a 74LVC1G125/126 tri-state buffer [U, test on bench]. Expect
~1–3 ms per ping round trip; a 14-servo read of pos+current at 50–100 Hz is
feasible but budget the UART carefully.

## (d) IMU
BNO085 in the trunk at the unchanged `imu` site/frame — same orientation
convention as upstream, so the policy's IMU observations map directly.
(MPU-6050 is the cheaper fallback.)

## (e) What stays the same
Joint names, order, axes and limits are unchanged (except `head_yaw`, already
clipped to ±150°, and the dropped mouth servo → 14 actuators). The mjlab task
code can be pointed at `mini/model/scene_knoll_mini.xml` directly; actuator
names are identical to upstream.

## (f) Risks
- **Potentiometer feedback:** deadband + noisy position sensing vs XL330's
  magnetic encoder — expect jitter on the observation channel; filter on-device.
- **300° servo range** vs the joint ranges used: fine for all mini joints
  (max needed is ±150°), but the head_yaw ±150° runs near the pot ends.
- **Torque margin:** static STAND torques are small (max 0.028 N·m at the
  knees, 0 joints over the 0.069 N·m rated), but walking needs ~2–3× static
  [U]. Margin `0.226/(3·static)`: knees 2.72, all other leg joints ≥ 18.
  Knees are the first STS3032 (0.44 N·m stall, same mounting family [U] —
  check footprint before buying) upgrade candidates if the real robot stalls.
- **Latency:** SCS bus reads + Wi-Fi round trip add 10–20 ms [U] to the control
  loop vs the simulated instant actuation — include latency in the retrain.

---

```
Original design and STL: Pollen Robotics / Microduck.
STEP reconstruction, repairs, validation and CAD sheets: tianjin66 and project contributors.
Source: https://github.com/tianjin66/microduck-step-3d-models-ai-stl
Licence: CC BY-NC-SA 4.0 — https://creativecommons.org/licenses/by-nc-sa/4.0/
Changes: uniformly scaled by 0.72; servo pockets/cradles re-cut for Feetech SCS0009; local stretches
(see SPEC.md 5.3); bearing seats changed to 6700ZZ; head shells swept-relieved internally for the
SCS0009 neck cradle (Session 3's BDX head rejected; outside shape unchanged).
```
