# Knoll Mini — assembly (Session 6)

Assemble bottom-up: feet -> legs -> trunk -> neck -> head -> cabling ->
power-on -> first motion. Part names below are the exact STLs in
`mini/parts/current/`; quantities and orientations are in
`print_list.md`. Servo IDs per `wiring.md`. **Do not power any joint
until step 9.**

## 1. Print everything

PETG, 0.2 mm layers, 3 walls, 20 % gyroid infill, no raft; brim on small
parts. Orientation per `print_list.md`. Dry-run the fit of one
`yaw2roll` cradle on a spare SCS0009 before printing the batch.

## 2. Heat-set inserts

Press M2 heat-set inserts into every part-to-part screw boss while the
iron is hot and the part is held square, ~1 mm proud:

- `trunk_base` — bosses for `left_shell` / `right_shell` and the
  battery-tray cover.
- `neck_frame` — bosses where `yaw_roll_motion` and the head cradle
  plates close up.
- `motor_support`, `top_head_shell`, `bottom_head_shell` — the head
  shell and face closure bosses.
- `power_support` — cover fastenings.

The Ø1.6 mm servo-ear pilot holes (all cradle STLs: `yaw2roll`,
`bearing_roll`, `hip_l`, `leg`, `upper_leg_*`, `neck_frame`,
`yaw_roll_motion`, `motor_support`) are **self-tapping** — M2 screws cut
their own thread, no insert.

## 3. Prepare the servos

One at a time on the FE-URT-1: set ID (table in `wiring.md`), set
1 Mbit/s, then **command 150° (the centre of the 300° range) before any
horn goes on**. Fit horns so the servo is centred in each cradle's
neutral pose. Label each servo's wire with its ID — they all look alike.

## 4. Legs, foot up

Per leg (mirror the two sides):

- Screw `sole_left`/`sole_right` onto `foot_left`/`foot_right`.
- Seat `ankle_left`/`ankle_right` (IDs 9/10 horns) on the foot, then the
  `leg` cradle — M2 ear screws into the Ø1.6 pilots, 6700ZZ bearing
  (10×15×4) and its idler pin on the opposite stub.
- `upper_leg_left`/`upper_leg_right` hold the knee (IDs 7/8) and hip_pitch
  (IDs 5/6) servos; close them over the `leg` output with the
  `upper_leg_rigidity_plate` (×2) sandwich.
- `hip_l` (×2) carries each hip_roll output; hip_roll servos (IDs 3/4)
  sit in the `yaw2roll` and `bearing_roll` cradles — bearing + idler pin
  in `bearing_roll`, driven stub in `yaw2roll`.
- Hip_yaw servos (IDs 1/2) mount in `trunk_base` and drive the
  `yaw2roll`/`bearing_roll` pair.

## 5. Trunk electronics

In/around `trunk_base` + `power_support`:

- Battery tray: 2S pack strapped under `trunk_base`; route the XT30 lead
  to the **fuse holder at the pack**, then the switch on `power_support`.
- UBEC (6 V) fixed to `power_support`; solder the servo hub (three
  branches: L leg, R leg, neck cable — see `wiring.md`).
- BNO085 on a flat pad inside `trunk_base`, axes aligned with the robot
  frame (+X fwd, +Y left, +Z up) — note its orientation for firmware.
- Close with `left_shell` / `right_shell` into the step-2 inserts.

## 6. Neck

`neck_frame` carries the neck_pitch servo (ID 11) and the head_pitch
servo (ID 12); `neck_pitch` is its output link. Fit both servos centred,
run the five-conductor head bundle (6V, GND, BUS, SDA, SCL) up through
the frame now — it is much harder later. `yaw_roll_motion` (the
head_yaw cradle, ID 13) stacks on top.

## 7. Head

- `motor_support` mounts the head_roll servo (ID 14) and the head
  electronics plate (all `elec_*` placeholders live in the head):
  the head 5 V buck fed by the 6 V neck pair, the XIAO ESP32-S3 Sense
  (camera facing out through `m12_lens_holder`), the 74LVC1G125/126 bus
  buffer, MAX98357A + Ø20–28 mm 8 Ω speaker, VL53L0X behind `noenoeil`,
  both WS2812 rings behind the eye diffusers, onboard mic facing out.
  `banana_pcb_locker` retains the PCB strip.
- Dress the neck bundle (6V, GND, BUS, SDA, SCL) with its >=60 mm
  service loop behind `motor_support`.
- Close `bottom_head_shell` then `top_head_shell`; `face_part`, `jaw`
  (fixed — no jaw servo), `jaw_soft` and `soft_mouth_top` last.

## 8. Cable routing

- Servo leads follow their chains; slack only where a joint needs it.
- Nothing crosses a horn sweep or a 6700ZZ seat.
- The head bundle must let head_yaw sweep end to end by hand with power
  OFF before you ever move it powered.

## 9. Power-on checklist

1. Fuses and switch OFF; every connector inspected for shorts.
2. UBEC jumper = 6 V, buck = 5 V — **measure both rails unloaded with a
   multimeter: 6.0 V and 5.0 V ±0.1 V.** Wrong rail = dead servos/XIAO.
3. Power the servo rail alone; all 14 servos should hold position, not
   twitch-run. Kill power on any chatter or hot servo.
4. Power the logic rail; XIAO boots; bus scan finds 14 IDs; I2C scan
   finds 0x28 and 0x29.

## 10. First motion

Prop the robot so its feet hang free. Move **one joint at a time** at
low torque / small angle (±10°) and confirm the joint that moves is the
one addressed (catches ID wiring mistakes). Then a slow whole-body
centring sweep — all servos to 150° — before any standing attempt.
Watch the head service loop through head_yaw travel.

## Safety

- **LiPo:** balance-charge only, never unattended, in a LiPo bag; no
  charging inside the robot. Below 3.3 V/cell stop; store ~3.8 V/cell;
  never puncture or crush; the 5 A fuse lives **at the pack**.
- **Soldering:** ventilate, eye protection, iron in a stand. Heat-set
  inserts are applied at iron temperature — they and the plastic around
  them stay burn-hot for a minute.
- **Regulators:** set and measure UBEC (6.0 V) and buck (5.0 V) before
  connecting loads, and re-check after any rewire.
- **Pinch points:** knees, ankles, hips and the neck/head gap all close
  hard under servo power. Fingers out whenever the rail is live; first
  tests always feet-free.

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
