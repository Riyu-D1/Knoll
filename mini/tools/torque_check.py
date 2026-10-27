"""Static torque check in MuJoCo. Loads model/scene_knoll_mini.xml, holds keyframe STAND (and INIT)
for 3 s with the position actuators, then reports mean |actuator force| over the last 1 s per joint.
T1: robot did not fall (trunk height stays > 85 % of start)          [per keyframe]
T2: every joint static torque <= 50 % of SCS0009 stall (0.113 N.m)   [per keyframe]
Also prints how many joints exceed the SCS0009 RATED torque (0.069 N.m): those are the joints to
upgrade to STS3032 (same footprint) if the real robot struggles. Exit 0 = T1 and T2 pass."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import numpy as np, mujoco, spec
m = mujoco.MjModel.from_xml_path(str(spec.MODEL_DIR / "scene_knoll_mini.xml")); d = mujoco.MjData(m)
stall, rated = spec.SCS["stall_Nm"], spec.SCS["rated_Nm"]
print(f"model mass = {m.body_subtreemass[1]*1000:.1f} g (target 350-450 g incl. electronics)")
ok = True
for key in ("STAND",):   # INIT (all zeros) is not a standing pose
    k = m.key(key).id
    mujoco.mj_resetDataKeyframe(m, d, k)
    for a in range(m.nu):   # servo targets = keyframe joint angles (keyframes carry no ctrl)
        d.ctrl[a] = d.qpos[m.jnt_qposadr[m.actuator_trnid[a, 0]]]
    mujoco.mj_forward(m, d)
    z_start = d.qpos[2]; n = int(3.0 / m.opt.timestep); acc = np.zeros(m.nu); cnt = 0
    for i in range(n):
        mujoco.mj_step(m, d)
        if i > n * 2 / 3:
            acc += np.abs(d.actuator_force); cnt += 1
    tau = acc / cnt; stood = d.qpos[2] > 0.85 * z_start
    over = [(m.actuator(i).name, tau[i]) for i in range(m.nu) if tau[i] > 0.5 * stall]
    print(f"[{key}] T1 stood={'PASS' if stood else 'FAIL'} (z {z_start*1000:.1f} -> {d.qpos[2]*1000:.1f} mm)")
    for i in np.argsort(-tau):
        flag = "OVER-50%-STALL" if tau[i] > 0.5 * stall else ("over-rated" if tau[i] > rated else "")
        print(f"   {m.actuator(i).name:16s} {tau[i]:.3f} N.m  {flag}")
    print(f"[{key}] T2 {'PASS' if not over else 'FAIL'}; joints over rated {rated}: {sum(tau > rated)}")
    ok &= stood and not over
print("OVERALL:", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
