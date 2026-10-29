"""Single source of truth for the Knoll Mini (Microduck x0.72) build. Every tool imports this.
Units: millimetres. Frame: Microduck MJCF world frame at zero pose (all joints 0),
+X forward (face direction), +Y robot-left, +Z up. Scaling is about the world origin.
Change numbers ONLY here, and log the change in mini/SPEC.md section 'Change log'."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]            # .../mini
THIRD = ROOT / "third_party"
UPSTREAM_DIR = THIRD / "microduck_rl" / "src" / "mjlab_microduck" / "robot" / "microduck"
UPSTREAM_COMMIT = "29e887ecfbf5d37144759e5a9f8a176dfb83d547"
STL_REPO_DIR = THIRD / "microduck-step-3d-models-ai-stl" / "01_STL_original"
SCALED_DIR = ROOT / "parts" / "scaled"     # session 0 output, never edited afterwards
WORK_DIR = ROOT / "parts" / "current"      # the parts the model uses; sessions 1-3 overwrite files here
MODEL_DIR = ROOT / "model"

S = 0.72                     # global scale factor (nominal height 264 mm * 0.72 = 190 mm)
MAX_HEIGHT_MM = 200.0        # hard cap after stretches
MIN_SERVO_GAP_MM = 2.0       # min distance between any two servo envelopes (case + ears)

# Feetech SCS0009 (datasheet 2020-11-23: 23.2 x 12.1 x 25.25 mm, 13.2 g, 20T spline OD 3.95 mm).
# Values marked UNVERIFIED must be measured with calipers on a real servo before printing.
SCS = dict(
    case_w=12.1,        # local X
    case_l=23.2,        # local Z (long side, ears stick out along this)
    case_h=25.25,       # local Y (along shaft), case bottom to case top
    shaft_off=5.7,      # shaft axis is 5.7 mm from case centre toward +Z  (research value, UNVERIFIED)
    spline_h=3.2,       # spline boss above case top (UNVERIFIED)
    horn_t=2.0,         # horn plate thickness (UNVERIFIED)
    horn_d=18.0,        # round horn diameter (UNVERIFIED)
    ear_span=32.5,      # tip-to-tip across ears along Z (UNVERIFIED)
    ear_t=2.0,          # ear thickness along Y (UNVERIFIED)
    ear_top_below_case_top=4.0,  # (UNVERIFIED)
    ear_hole_pitch=28.5, ear_hole_d=2.0,  # M2 self-tapping (UNVERIFIED)
    cable_exit_clear=4.0,  # keep 4 mm free below case bottom for the cable
    fit_clearance=0.3,     # pocket = envelope + 0.3 mm per side (PETG, 0.4 nozzle)
    mass_g=13.2, stall_Nm=0.226, rated_Nm=0.069, range_deg=300,
)
# XL330 raw-STL frame facts (verified 2026-10-27 by FK contact counting; this is the frame assembly.py uses):
# shaft = local X axis through (y=0, z=0); horn/output side is -X, boss tip at x = -14.5 mm (full scale).
# Case spans y -10..+10, z -24.5..+9.5. The SCS0009 horn top is placed at x = -14.5*S so the driven
# part's horn interface does not move; the SCS case then sticks ~10.6 mm further toward +X than the XL330.
XL_HORN_TIP_X = -14.5

# 14 actuated joints. Positions = joint anchor in world mm at zero pose, FULL scale (multiply by S).
# limits in degrees. servo_in = body whose part holds the servo case; horn_to = body the horn drives.
JOINTS = [
 # name,            pos_full_mm,            axis_world,   servo_in,          horn_to,         lim_deg
 ("left_hip_yaw",   (6.0, 17.5, 115.0),   (0,0,-1),  "trunk_base",      "yaw2roll",      (-25, 30)),
 ("left_hip_roll",  (22.5, 17.5, 102.5),  (1,0,0),   "yaw2roll",        "hip_l",         (-22, 22)),
 ("left_hip_pitch", (4.0, 42.5, 102.5),   (0,1,0),   "upper_leg_left",  "hip_l",         (-90, 90)),
 ("left_knee",      (-31.8, 38.5, 80.5),  (0,-1,0),  "upper_leg_left",  "leg",           (-90, 90)),
 ("left_ankle",     (-31.8, 64.5, 38.5),  (0,1,0),   "leg",             "ankle_left",    (-90, 90)),
 ("right_hip_yaw",  (6.0, -17.5, 115.0),  (0,0,-1),  "trunk_base",      "bearing_roll",  (-30, 25)),
 ("right_hip_roll", (22.5, -17.5, 102.5), (1,0,0),   "bearing_roll",    "hip_l_2",       (-22, 22)),
 ("right_hip_pitch",(4.0, -42.5, 102.5),  (0,-1,0),  "upper_leg_right", "hip_l_2",       (-90, 90)),
 ("right_knee",     (-31.8, -38.5, 80.5), (0,1,0),   "upper_leg_right", "leg_2",         (-90, 90)),
 ("right_ankle",    (-31.8, -64.5, 38.5), (0,-1,0),  "leg_2",           "ankle_right",   (-90, 90)),
 ("neck_pitch",     (26.0, 14.5, 152.4),  (0,-1,0),  "neck",            "trunk_base",    (-90, 60)),
 ("head_pitch",     (26.0, 14.5, 202.4),  (0,1,0),   "neck",            "neck_pitch",    (-90, 90)),
 ("head_yaw",       (26.0, 0.0, 221.1),   (0,0,1),   "yaw_roll_motion", "neck_pitch",    (-150, 150)),  # was +-170, SCS0009 is 300 deg
 ("head_roll",      (8.1, 0.0, 235.6),    (-1,0,0),  "jaw_soft",        "yaw_roll_motion",(-25, 25)),
]
DROPPED_SERVOS = ["mouth (xl330 in body jaw_soft at world (33.0, 25.6, 238.6) full scale)"]

# Local stretches. Each entry moves body `body` (and everything below it) by delta_mm, given in
# WORLD axes at zero pose, applied AFTER scaling. Only move a body along its own joint axis or
# along an axis that keeps every servo shaft on its joint axis (the check script verifies this).
# Filled in by session 1 / session 2 from the clearance report. Keep each |delta| <= 10 mm.
STRETCH = [   # pre-verified on 2026-10-27 with check_clearance.py: C2 (servo-servo) PASS with these
    {"body": "yaw2roll",     "delta_mm": (0.0, 0.0, -2.5)},  # left leg chain down 2.5 mm along hip_yaw axis: hip_yaw vs hip_roll servo
    {"body": "bearing_roll", "delta_mm": (0.0, 0.0, -2.5)},  # right leg chain, same
    {"body": "neck",         "delta_mm": (3.0, 0.0, 0.0)},   # neck pivot 3 mm forward: hip_yaw servos vs neck_pitch servo
]

# Spin of each SCS0009 about its OWN shaft axis (degrees, 0/90/180/270), relative to how the XL330
# sat. Spinning about the shaft keeps the joint axis and the horn face unchanged, so kinematics are
# untouched. Used to turn the long side + ears of a servo away from a neighbour.
SERVO_ROLL_DEG = {   # pre-verified on 2026-10-27 (tools/search_layout.py)
    "left_knee": 90, "right_knee": 90,   # knee vs hip_pitch servo clash (-2.2 mm) removed
    "neck_pitch": 270,                   # neck_pitch vs head_pitch servo clash (-12.1 mm) removed
    "left_ankle": 90, "right_ankle": 270,  # session 1 fix: mirrored pair clears ankle<->knee servo
    #   case clash AND ankle<->hip_roll (verified: 0.00 mm max depth over knee -45..+45 both sides).
    #   Same-sign 90/90 or 270/270 fail on the opposite side. 180: case pokes out below the sole.
    #   Knee safe range: FULL -45..+45 PASS both sides after re-cutting leg/ankle/sole/foot for the
    #   rotated envelopes (leg.stl is shared by bodies leg+leg_2 -> corridors cut via both T maps).

}

HEAD_MODE = "bdx"        # session 8A: BDX head (tools/make_head_bdx.py); session-3 bdx stayed rejected
HEAD_BODY = "jaw_soft"   # everything in this body is the head
HEAD_KEEP_PARTS = ["motor_support"]   # head-side interface: head_roll servo cradle + bearing seat
HEAD_REPLACE_PARTS = ["top_head_shell", "bottom_head_shell", "face_part", "jaw", "jaw_soft",
                      "soft_mouth_top", "noenoeil"]   # m12_lens_holder stays (camera axis part)
NON_PRINTED = ["xl330", "np_f970", "pcb__raspberry_pi_zero_2_w", "elec_rpi_robot_hat_pcb", "speaker",
               "lens", "seeed_bearing__configuration__22x16x4", "seeed_bearing__configuration_default"]

# Thin-wall rule (check_parts.py P4): structural >= 1.2 mm, cosmetic >= 0.9 mm (10th percentile).
COSMETIC_PARTS = ["left_shell", "right_shell", "banana_pcb_locker", "top_head_shell", "bottom_head_shell",
                  "face_part", "soft_mouth_top", "m12_lens_holder", "noenoeil", "jaw", "jaw_soft",
                  "head_eye_lens_l", "head_antenna_left", "head_antenna_right",
                  "trunk_shell", "trunk_cover_left", "trunk_cover_rear"]
# Session-8A BDX head (tools/make_head_bdx.py; session-3 bdx_* names archived in parts/attic_bdx/).
# Parts authored in the jaw_soft frame, loaded only when HEAD_MODE == "bdx".
BDX_HEAD_PARTS = ["top_head_shell", "bottom_head_shell", "head_eye_lens_l",
                  "head_antenna_left", "head_antenna_right"]
# Extra (non-printed) electronics placeholders: (body, stl name in parts/current, mass_g). Session 3/5 fill.
ELECTRONICS = [   # masses are ESTIMATES (unverified); the STL is optional (mass counts either way)
    ("trunk_base", "elec_battery_2s_450", 32.0),   # 2S 450 mAh LiPo with XT30 lead
    ("trunk_base", "elec_ubec_6v_5a", 10.0),
    ("trunk_base", "elec_bno085", 3.0),
    ("trunk_base", "elec_bus_hub_and_wiring", 18.0),
    ("trunk_base", "hardware_screws_inserts", 15.0),
    ("jaw_soft", "elec_xiao_esp32s3_sense", 10.0),   # board + camera daughterboard
    ("jaw_soft", "elec_eye_rings_x2", 6.0),
    ("jaw_soft", "elec_max98357_speaker", 8.0),
    ("jaw_soft", "elec_vl53l0x", 1.5),
    ("jaw_soft", "elec_buck_5v", 2.0),
]
# Parts authored directly in a body's frame (mm), treated as printed: (body, stl name in parts/current).
EXTRA_PARTS = [("neck", "neck_frame"),   # session 2: merge_body_frame.py --hull, replaces neck
               ("trunk_base", "trunk_shell"),        # session C: designed trunk enclosure
               ("trunk_base", "trunk_cover_left"),   # session C: left access panel
               ("trunk_base", "trunk_cover_rear")]   # session C: rear battery bay cover
# Upstream printed parts no longer used (their STL moves to parts/attic/). Skipped by assembly + MJCF.
REMOVED_PARTS = ["neck",   # session 2: two tiny XL330 plates -> one SCS0009 bracket (neck_frame)
                 "left_shell", "right_shell", "banana_pcb_locker"]   # session C: -> attic_refine/
PETG_DENSITY_G_CM3 = 1.27
PRINT_FILL_FACTOR = 0.55   # 3 walls + 20 % infill, approx fraction of solid mass

# ---- range-of-motion requirement used by tools/sweep_check.py (degrees, joint-angle convention of the MJCF)
# Every joint must move through at least this range with no NEW collision (> 0.5 mm deeper than at 0 deg).
# Do not shrink these without the user's written OK - shrinking them changes what the robot can do.
SWEEP_REQUIRED_DEG = {j[0]: (-45, 45) for j in JOINTS}
SWEEP_REQUIRED_DEG.update({"head_yaw": (-120, 120), "head_roll": (-25, 25)})
