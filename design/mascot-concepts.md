# Mascot Concepts — Original Character Design

**Date:** 2026-10-26 · **v1.1 redirect:** 2026-10-29 — direction changed to **agile biped-droid** (torso + actuated head + 2-DOF arms), name "Knoll" retained, moss/dome cues dropped. New concepts: `design/renders/droid-v0/` (Variant A recommended). The dome-creature concept below is kept for record — it was scored soundly but rejected at visual review as reading "static, not agile".
**Status:** Concept-stage. Proportions are CAD-ready *starting points*, not verified geometry. Any renders produced are concept visualisations only.

---

## 0. Design principles applied

From character/consumer-robot design practice (Big Hero 6, EVE/BD-X lineage, Anki Cozmo, Eilik, Lovot):

1. **Silhouette test** — must be recognisable as a black shape at thumbnail size.
2. **Baby schema** — large head/body ratio, low-set face, rounded forms read as "character" not "machine".
3. **One hero feature** — a single distinctive motif people draw from memory (Microduck: the flat bill).
4. **Expressive cheapness** — LED/dot-matrix eyes give more expressiveness per £ than extra face servos.
5. **Shell = service cover** — every exterior part unbolts; no glue in the load path; colour via filament or user-printed shells (customisation is a feature).
6. **Recovery-aware geometry** — surfaces the robot will lie on during get-up must be smooth, snag-free, and keep servo horns off the ground.

**What we deliberately avoid:** a duck bill, Microduck's proportions (its shell silhouette, colourway set), and any "duck" naming. Bird-like is allowed; duck is not.

---

## Concept A — "PIP" — the kiwi-chick

**Identity:** a round, flightless kiwi-chick — curious, pecky, stubborn. Personality: industrious little forager.

| Element | Direction |
|---|---|
| Silhouette | Egg-shaped body IS the head (head/torso fused, no neck joint); long thin downward-curving beak; two oversized flat feet; tiny stub wings |
| Proportions | Body ø≈130–150 mm; beak +50–60 mm forward; leg ~120 mm; foot 80×90 mm |
| Face | Two 8×8 LED-matrix eyes set low + wide apart; beak is decoration only (fixed) |
| Hero feature | The thin curved beak — unmistakably non-duck (kiwi/ibis lineage) |
| Sensors | Camera/eyes in face band; status LED ring around beak base; USB-C + battery door in tail |
| Colours | Cream body / brown beak+feet (natural kiwi); optional teal or coral accent shells |
| Mechanical fit | Maximum internal volume per gram; lowest CoM (battery low in belly); beak is TPU or on a breakaway screw — it must not snag during face-down recovery |
| Printability | Best of the three: two shell halves + beak + feet; all < 180 mm |
| Trade-off | Fixed head = less expressiveness than B/C; beak needs a snag test in Stage D recovery sims |

## Concept B — "KNOLL" — the moss-dome creature

**Identity:** a little walking terrarium — a dome-shelled moss creature (bulbasaur-turtle lineage), calm and determined. Personality: unhurried, unbothered, indestructible.

| Element | Direction |
|---|---|
| Silhouette | Smooth dome (flattened hemisphere) on two big feet; face punched low into the dome front; optional magnetic "sprout" or mushroom cap on top |
| Proportions | Dome ≈170×160 mm footprint, ~140 mm dome height; total standing ~26–28 cm; foot 80×90 mm |
| Face | Dot-matrix eyes low on the dome + a shallow embossed smile line; eyes double as status display |
| Hero feature | The dome + sprout — reads instantly at silhouette; sprout is the user-customisable slot (magnetic pogo pads → community toppers) |
| Sensors | Eyes hide the IMU/status board; small camera aperture between eyes (optional); ToF could mount as a "third eye" (optional); all ports on a rear service panel under a hatch |
| Colours | Shell sage-green/terracotta/graphite; belly + feet charcoal; sprout accent |
| Mechanical fit | Dome is a structural exoskeleton AND the drop bumper — protects in falls; legs tuck under rim; whole top lifts off for service in seconds; get-up benefits from rocking on the dome (rounded back aids roll-to-prone) |
| Printability | Dome is one big print (~170 mm fits common printers) or split in 3 panels; flat face plate prints separately for colour swap |
| Trade-off | Dome adds ~40–60 g of shell vs Pip; face-down falls land on the face plate → face plate is sacrificial/replaceable; dome must not contact ground during leg tuck — rim clearance to be verified in CAD |

## Concept C — "SPRIG" — the antenna-bot

**Identity:** a friendly little robot-sprout — explicitly a robot but warm: rounded-square torso, separate head with a single sprung antenna, LED-visor face.

| Element | Direction |
|---|---|
| Silhouette | Rounded-cube torso + pill-shaped head on a 2-DOF neck + single antenna with glowing tip; broad feet |
| Proportions | Torso ~110×90×70 mm; head ø≈80 mm at +60 mm above torso; total ~28–30 cm |
| Face | Full-width 8×32 LED visor (scrolling eyes, battery bar, expressions) |
| Hero feature | Antenna + visor — most expressive option |
| Sensors | Camera behind visor; antenna tip = RGB status LED; rear I/O panel |
| Colours | Graphite + one accent (lime/amber/sky) |
| Mechanical fit | Worst of the three mechanically: head+neck mass raises CoM; neck servos add cost + failure points; antenna must survive falls (make it a flexible filament wick) |
| Printability | More parts, tighter clearances, visor window needs diffusion layer |
| Trade-off | Max expressiveness, min structural simplicity; highest cost & mass |

---

## Scoring matrix (weights justified below)

| Criterion | Weight | Why this weight |
|---|---|---|
| Mechanical feasibility & CoM | 20 | Self-recovery and balance dominate everything; a cute robot that can't stand up is a failed robot |
| Recognisability / silhouette | 15 | It's a mascot — this is the product |
| Printability (hobby FDM) | 15 | Core DIY constraint |
| Repairability / modularity | 15 | Mission requirement |
| Originality vs Microduck | 15 | Legal + ethical requirement |
| Mass impact | 10 | Every gram costs torque margin and battery |
| Cost impact | 10 | Mission objective |

Scores 1–5 (5 best), weighted:

| Concept | Feas ×20 | Recog ×15 | Print ×15 | Repair ×15 | Orig ×15 | Mass ×10 | Cost ×10 | **Total /500** |
|---|---|---|---|---|---|---|---|---|
| A Pip (kiwi) | 5 | 4 | 5 | 4 | 4 | 5 | 5 | **455** |
| B Knoll (dome) | 5 | 5 | 4 | 5 | 5 | 4 | 4 | **465** |
| C Sprig (antenna-bot) | 3 | 4 | 3 | 3 | 4 | 3 | 4 | **335** |

## Selected concept: **KNOLL** (working name)

Knoll wins on the combined merits: the dome is simultaneously the mascot identity, the structural exoskeleton, the fall bumper and the 5-second service cover — one part doing four jobs. Its rounded back is also the best get-up geometry of the three (roll-to-prone recoveries rock on the dome rather than snagging a neck or beak).

- **Name note:** "Knoll" is a working name; a trademark/community-name check is a roadmap item before public release. Internal codename: `knoll-mk1`.
- **Fallback:** Concept A (Pip) — if dome printing proves impractical on 180 mm printers or face-plate ground contact tests poorly in Stage D, Pip's simpler shell splits smaller and costs less.
- **Expression budget:** 2-DOF neck is rejected for v1 (mass, cost, recovery risk); expressiveness comes from the matrix eyes, body motion, and the magnetic topper slot. A head mechanism is a documented v2 option (electrical + mounting provisions reserved — see electronics doc).

## Selected concept — v1 art direction lock

- Overall: dome ~170×160 mm, total height 26–28 cm, feet oversized and slightly splayed
- Face: two 8×8 red or white LED matrices as eyes behind smoked face plate; shallow smile emboss
- Topper: magnetic 4-pin pogo slot (5V + I²C spare) at dome apex — first-party topper is a 3-leaf sprout
- Service: single hatch in rear dome = USB-C, SD, power switch, charge port; battery slides out through the same hatch on a printed sled
- Colourways: Sage (green dome/moss sprout), Terracotta, Graphite — user prints their own; accent = topper + smile trim
- Pinch mitigation: leg openings shrouded by dome skirt so fingers can't reach the hip pinch zone; servo horns recessed

## Concept visualisations

First rendered concept set produced on branch `design/knoll-shell-v0` → `design/renders/shell-v0/` (three shell variants, Blender 4.5 headless, concept visualisation only). ASCII orthographics below are proportion diagrams only — not engineering geometry. Roadmap P0.2 creates real CAD; any future images must be labelled "concept visualisation, not verified geometry".

**Knoll (selected) — front / side / three-quarter:**

```
   FRONT                SIDE               THREE-QUARTER
    __,-,                __,-·-·._           __,-·-._
  ,'sprout|           _,'_sprout|_ `-._    ,'_sprout| `-.
 / _ _ _ _ \         /  _  _  _  \    \  /  _  _  _    `\
| (o)   (o) |       |  (o) matrix |  /  | (o)  matrix .  \
|  \_____/  |       |   smile     | |   |   smile    |  | |
 `-,_____,-' dome    \___________/  |    \___________. . /
   |skirt |           |hatch      |/      |            |/
  _|_____|_           |___________|       |____________|
 /  |   |  \ feet      | leg  leg |        |  |     |   \
|___|   |___|          |________|          |__|     |____|
```

**Pip (kiwi, runner-up):** egg body, thin curved beak, big feet — `((•))` eyes on the egg, `>` beak. **Sprig:** boxy torso + pill head + `|` antenna + `[===]` visor.
