# PCB Specification — Knoll Control Board "KCB-1"

**Date:** 2026-10-26 · **Status:** Requirements + schematic architecture specified. NO schematic captured yet; no ERC run; no layout — this document is the brief for the PCB implementation agent. Claims about passing checks will be added only when actually run.

---

## 1. Board purpose & form factor

One custom 2-layer PCB ("Knoll Control Board") that replaces breadboard wiring for: power input/protection, servo-rail distribution, half-duplex bus interfaces, Pico 2 W carrier, BNO085, LED-eye driver, expansion. Pico 2 and Pi Zero 2 W mount as socketed modules (hobbyist-friendly, replaceable).

- Target envelope: **~55 × 85 mm**, 2-layer, 1.6 mm, hand-solderable (through-hole + 0805/SOT-23 only), mounts on 4× M3 standoffs to chassis plate.
- Fab: JLCPCB economy — ≤100 mm 2-layer qty 5 ≈ £4–8 landed UK (verified, notes-manufacturing §5). Keep to one design per order.
- Assembly: hand-solder; no JLC-PCBA needed for v1 (all packages hobbyist-weldable).

## 2. Functional block diagram

```
 BAT-IN (XT30) ──► E-STOP sense pad ──► FUSE 10A ──► AO4407 P-FET ──► SVRAIL bus bar
                                                              │
        ┌─────────────────────────────────────────────────────┼────────────────┐
        ▼                                                     ▼                ▼
   5264×5 BUS A (L leg)                                5264×5 BUS B (R leg)   BUCK 5V/3A module
        ▲                                                     ▲            (MP1584-fixed, socketed)
   100Ω+TVS+74LVC1G126/125                             same                    │
        ▲                                                     │        ┌───────┴────────┐
   UART0+TXEN (Pico 2 W, socketed DIP) ◄──USB-CDC pads──► 40-pin │   5V rail: Pi header, │
   UART1+TXEN ──────────────────────────────────────────► GPIO │   LED eyes, aux        │
   I2C0 ──► BNO085 (Qwiic + pads)                              │   LDO 3.3V: Pico VSYS  │
   ADC0 ──► VBAT ÷11 divider (100k/10k)                        │   → RP2350+IMU+buffers │
   GPIO ──► foot switches ×4, estop-read, status LED, buzzer   └────────────────────────┘
   Expansion header: UART2 pads? (PIO UART), I2C1, 4 GPIO, 5V, 3V3, GND
   Debug: SWD 3-pin · test pads: SVRAIL,5V,3V3,GND×4,DATA_A,DATA_B,TXEN_A,TXEN_B,VSENSE
```

## 3. Schematic architecture (per-sheet)

| Sheet | Contents | Key parts |
|---|---|---|
| 1 PWR-IN | XT30 footprint, e-stop switch pads, 10 A mini-blade fuse holder, AO4407 rev-pol (gate pulled to GND via 100 k; body diode oriented so forward = protected), input TVS SMBJ15A, bulk 470 µF 16 V | Amass XT30, Littelfuse 0297 holder, AO4407A |
| 2 SERVO-DIST | SVRAIL copper pour/bus bar, 10× 5264-3A sockets (5 per bus), 220 µF per bus, branch pads for aux | Molex KK254-compatible 5264-3A |
| 3 BUS-PHY | 2× (SN74LVC1G126 + SN74LVC1G125) at 3.3 V, TXEN GPIO each, 10 k pull-ups, 100 Ω series, SMAJ5.0A TVS per DATA | per Waveshare reference; VCC-option jumper 3V3/5V |
| 4 MCU | Pico 2 W socket (2×20 2.54 mm), decoupling, SWD header, USB micro-B pad option, reset | Raspberry Pi Pico 2 W |
| 5 IMU+EYES | BNO085 via Qwiic JST-SH + 0.1" pads + 10 k I²C pull-ups; 2× 8×8 matrix connector (SPI or chained WS2812 5 V) | Adafruit footprint-compatible |
| 6 5V/3V3 | MP1584 fixed-5V module socket OR onboard TPS5430-class option (layout for module v1); AP2112K-3.3 LDO for logic | module = replaceable |
| 7 SENSE/EXP | VBAT divider→ADC0, 5V-rail sense→ADC1, foot-switch header (GPIO10-13 + RC), e-stop read, buzzer, expansion header (topper dock: 5V+I²C+2GPIO+mag pads) | — |
| 8 SBC | 5 V power + USB link pads for Pi Zero 2 W (socketed 2×20), camera FFC keepout zone | Pi is off-board module on standoffs |

## 4. Connector & pin map (Pico 2 W)

| Function | Pins | Notes |
|---|---|---|
| UART0 TX/RX → Bus A | GP0/GP1 | TXEN = GP2 |
| UART1 TX/RX → Bus B | GP4/GP5 | TXEN = GP6 |
| I²C0 → BNO085 | GP8 SDA / GP9 SCL | 0x28 |
| ADC0 VBAT sense | GP26 | ÷11 divider, ~0.68–0.76 V @6–8.4 V |
| ADC1 5V-rail sense | GP27 | ÷2 divider |
| Foot switches ×4 | GP10–13 | pull-ups + RC debounce |
| E-stop read | GP14 | reads hard-cut state |
| Status LED / buzzer | GP15/GP22 | buzzer = fall + low-batt alarms |
| Expansion/topper | GP16–19 + I²C1 GP20/21 | sprout dock + future neck servo PWM on GP28 |
| SWD | SWDIO/SWCLK/GND | 3-pin debug |

## 5. Layout constraints (preliminary — verify in layout review)

1. **Current geometry:** SVRAIL carries 10 A bounded — ≥3 mm trace or copper pour, star from fuse; keep DATA lines clear of the pour's return path bends.
2. Servo connector row on board edge (cables exit toward legs); power entry opposite edge toward battery hatch.
3. IMU on centreline of robot (board placement near plate centre); foam-tape isolation pad under breakout.
4. Bulk caps near each bus's first connector; TVS at connectors (ESD entry point).
5. Camera FFC + USB-OTG cables get keepout/routing channels; no tall parts under Pi.
6. All SMD bottom-side optional; every net labelled on silk; board marked with polarity + "NOT JST-XH" warning on servo row.
7. DFM for JLC 2-layer: ≥0.15 mm trace/space, ≥0.3 mm drills, all parts in JLC basic library where possible (for optional PCBA later).

## 6. Design-for-test

- Labelled 2.54 mm test-pad row: SVRAIL, 5V, 3V3, GND×4, DATA_A/B, TXEN_A/B, VSENSE.
- Populate options (0 Ω/jumpers): buffer VCC 3V3/5V; UART-link vs USB-link; IMU pull-up enable; bulk-cap x2 footprints.
- Bring-up order (validation E-tests): board rails @100 mA limit → MCU loopback → 1 servo → bus @ current limit → battery → E4 peak-current sets fuse.

## 7. Verification plan for the PCB work package

- [ ] Schematic review vs this spec + datasheet pin checks (Pico, AO4407 orientation, LVC logic)
- [ ] ERC clean report (KiCad) — attach output
- [ ] DRC clean at JLC minimums — attach output
- [ ] Current-capacity check: trace width calc for 10 A documented (IPC-2221)
- [ ] Connector pinout verified against a REAL ST3020 pigtail (5264 `GND|DATA|V+`) before release
- [ ] Fit check against chassis-plate STEP (mounting holes, cable exits, dome clearance)
- [ ] First-board bring-up log per §6

## 8. What this document deliberately does NOT claim

No schematic exists yet; no ERC/DRC results; no simulation; component footprints unverified against physical parts; prices for the small discretes are estimates. Those are WPs P1.5/P2.3 in the roadmap.
