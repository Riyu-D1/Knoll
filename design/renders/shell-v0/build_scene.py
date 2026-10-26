# Knoll Mk1 — shell-v0 concept scene builder
# Blender 4.5 headless:  blender --background --python build_scene.py [-- --renders all|list]
# Builds 3 shell variants + proxy legs/chassis, materials, studio light, cameras.
# All dimensions in METRES, derived from design/mechanical-architecture.md.
# CONCEPT VISUALISATION ONLY — not validated mechanical geometry.

import bpy, math, os, sys
from mathutils import Vector

# ---------------- parameters (edit these) ----------------
P = dict(
    dome_w=0.170, dome_d=0.160,          # dome footprint (from brief)
    skirt_h=0.020,                        # cylindrical rim band height
    dome_cap_h=0.115,                     # ellipsoid cap above skirt  (skirt+cap = 135)
    chassis_z=0.143, chassis_r=0.075, chassis_h=0.006,
    dome_base_z=0.140,
    hip_x=0.040, hip_z=0.140,             # hip spacing ±40mm
    knee_z=0.085, ankle_z=0.020,
    leg_splay=0.004,                      # slight outward x offset knee->ankle
    foot_w=0.085, foot_l=0.095, foot_h=0.026,
    foot_yaw=math.radians(8),
    face_z=0.205,                         # face plate centre (front = -Y)
    face_w=0.058, face_h=0.034, face_t=0.005, face_tilt=math.radians(-12),
    eye_w=0.020, eye_h=0.020, eye_gap=0.040, eye_z=0.212, eye_t=0.004,
    hatch_w=0.052, hatch_h=0.038, hatch_z=0.205, hatch_y=0.0755,
    face_y=-0.0765,
    topper_z=0.272,                       # apex = 140+20+115 = 275mm
)

PALETTES = {
    "sage":      dict(dome=(0.30,0.42,0.24,1), face=(0.020,0.024,0.020,1), accent=(0.60,0.33,0.22,1),
                      feet=(0.09,0.095,0.095,1), sole=(0.03,0.03,0.03,1), legs=(0.20,0.21,0.21,1),
                      sprout=(0.18,0.40,0.12,1), chassis=(0.08,0.08,0.09,1)),
    "graphite":  dict(dome=(0.20,0.20,0.21,1), face=(0.03,0.03,0.035,1), accent=(0.72,0.52,0.10,1),
                      feet=(0.08,0.08,0.09,1), sole=(0.03,0.03,0.03,1), legs=(0.18,0.18,0.19,1),
                      sprout=(0.72,0.52,0.10,1), chassis=(0.08,0.08,0.09,1)),
    "terracotta":dict(dome=(0.52,0.27,0.16,1), face=(0.04,0.04,0.04,1), accent=(0.80,0.72,0.58,1),
                      feet=(0.09,0.09,0.10,1), sole=(0.03,0.03,0.03,1), legs=(0.18,0.18,0.19,1),
                      sprout=(0.80,0.72,0.58,1), chassis=(0.08,0.08,0.09,1)),
}

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

# ---------------- helpers ----------------
def clear():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
    for c in list(bpy.data.collections):
        if c.name != "Collection": bpy.data.collections.remove(c)

def mat(name, col, rough=0.55, metal=0.0, emit=None, emit_s=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = emit
        b.inputs["Emission Strength"].default_value = emit_s
    return m

def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in [ch.name for ch in bpy.context.scene.collection.children]:
        try: bpy.context.scene.collection.children.link(c)
        except RuntimeError: pass
    return c

def move_to_coll(ob, cname):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    coll(cname).objects.link(ob)

def bevel(ob, w, seg=3):
    m = ob.modifiers.new("Bevel", 'BEVEL'); m.width = w; m.segments = seg
    return ob

def cube(name, loc, scale, material, bev=0.0, rot=(0,0,0), collname=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev: bevel(o, bev)
    o.data.materials.append(material)
    if collname: move_to_coll(o, collname)
    return o

def sphere(name, loc, scale, material, rot=(0,0,0), seg=48, rings=24, collname=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    if collname: move_to_coll(o, collname)
    return o

def cyl(name, loc, r, depth, material, rot=(0,0,0), collname=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    if collname: move_to_coll(o, collname)
    return o

def torus(name, loc, major, minor, material, rot=(0,0,0), scale=(1,1,1), collname=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
        major_segments=48, minor_segments=12, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    if collname: move_to_coll(o, collname)
    return o

def strut(name, p1, p2, w, h, material, bev=0.008, collname=None):
    p1, p2 = Vector(p1), Vector(p2); d = p2-p1
    o = cube(name, (p1+p2)/2, (w/2, h/2, d.length/2), material, bev, collname=collname)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z','Y')
    return o

def curve_arc(name, center, radius, a0, a1, material, bevel_d=0.0018, plane='XZ', tilt=(0,0,0), collname=None):
    """Smile-arc: bevelled polyline curve from angle a0..a1 (radians)."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions='3D'; cu.bevel_depth=bevel_d; cu.bevel_resolution=3
    sp = cu.splines.new('POLY'); n=24; sp.points.add(n-1)
    for i in range(n):
        a = a0 + (a1-a0)*i/(n-1); x=math.cos(a)*radius; z=math.sin(a)*radius
        p = sp.points[i]
        if plane=='XZ': p.co=(x,0,z,1)
        else: p.co=(x,z,0,1)
    o = bpy.data.objects.new(name, cu); o.location=center; o.rotation_euler=tilt
    o.data.materials.append(material)
    (coll(collname) if collname else bpy.context.scene.collection).objects.link(o)
    return o

def text_label(name, body, loc, size, material, rot=(math.pi/2,0,0), collname=None, align='CENTER'):
    cu = bpy.data.curves.new(name,'FONT'); cu.body=body; cu.size=size; cu.align_x=align
    o = bpy.data.objects.new(name, cu); o.location=loc; o.rotation_euler=rot
    o.data.materials.append(material)
    (coll(collname) if collname else bpy.context.scene.collection).objects.link(o)
    return o

def camera(name, loc, look_at, lens=70, ortho=None, clip_start=None, clip_end=None):
    cd = bpy.data.cameras.new(name)
    if ortho: cd.type='ORTHO'; cd.ortho_scale=ortho
    else: cd.lens=lens
    if clip_start: cd.clip_start=clip_start
    if clip_end: cd.clip_end=clip_end
    o = bpy.data.objects.new(name, cd); o.location=loc
    o.rotation_euler = (Vector(look_at)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.collection.objects.link(o)
    return o

def area_light(name, loc, energy, size, color):
    ld = bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size; ld.color=color
    o = bpy.data.objects.new(name, ld); o.location=loc
    o.rotation_euler = (Vector((0,0,0.15))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.collection.objects.link(o); return o

# ---------------- robot builders ----------------
def build_legs(x0, y0, pal, style, collname):
    """Proxy legs per mechanical-architecture.md: hip ±40mm @z140, knee z85, ankle z20."""
    x_hip, x_knee, x_ank = P['hip_x'], P['hip_x']+P['leg_splay'], P['hip_x']+2*P['leg_splay']
    for side, s in (("L",-1),("R",1)):
        hx, kx, ax = s*x_hip+x0, s*x_knee+x0, s*x_ank+x0
        # hip block + joints (cylinders axis X)
        cube(f"LEG_{side}_HIPBLK",(hx,y0,P['hip_z']),(0.021,0.018,0.016),pal['legs'],0.004,collname=collname)
        cyl(f"LEG_{side}_HIPJ",(hx,y0,P['hip_z']),0.013,0.046,pal['chassis'],rot=(0,math.pi/2,0),collname=collname)
        strut(f"LEG_{side}_FEMUR",(hx,y0,P['hip_z']),(kx,y0,P['knee_z']),0.026,0.036,pal['legs'],collname=collname)
        cyl(f"LEG_{side}_KNEE",(kx,y0,P['knee_z']),0.013,0.046,pal['chassis'],rot=(0,math.pi/2,0),collname=collname)
        strut(f"LEG_{side}_SHANK",(kx,y0,P['knee_z']),(ax,y0,P['ankle_z']),0.024,0.032,pal['legs'],collname=collname)
        cyl(f"LEG_{side}_ANKLE",(ax,y0,P['ankle_z']),0.012,0.044,pal['chassis'],rot=(0,math.pi/2,0),collname=collname)
        fz = P['foot_h']/2
        fy = y0-0.006
        if style=='A':   # soft stone foot
            o = sphere(f"FOOT_{side}",(ax,fy,fz+0.002),(P['foot_w']/2,P['foot_l']/2,P['foot_h']/2),pal['feet'],collname=collname)
        elif style=='B': # angular tech foot
            o = cube(f"FOOT_{side}",(ax,fy,fz+0.002),(P['foot_w']/2,P['foot_l']/2,P['foot_h']/2),pal['feet'],0.008,collname=collname)
        else:            # C sculptural river-stone, toe forward
            o = sphere(f"FOOT_{side}",(ax,fy-0.010,fz+0.004),(P['foot_w']*0.55,P['foot_l']/2,P['foot_h']/2),pal['feet'],collname=collname)
        o.rotation_euler[2] = s*P['foot_yaw']
        # sole
        so = cyl(f"FOOT_{side}_SOLE",(ax,fy,0.004),P['foot_w']/2*0.92,0.008,pal['sole'],collname=collname)
        so.scale.y = P['foot_l']/P['foot_w']; so.rotation_euler[2]=s*P['foot_yaw']

def build_dome(x0, y0, pal, variant, collname, exploded=False):
    """Skirt cylinder + ellipsoid cap. Variant B adds panel grooves/screws; C adds cowl."""
    ez = 0.10 if exploded else 0.0           # exploded lift of shell
    zb = P['dome_base_z']+ez
    cyl("SHELL_DOME_SKIRT",(x0,y0,zb+P['skirt_h']/2),P['dome_w']/2,P['skirt_h'],pal['dome'],collname=collname).scale.y=P['dome_d']/P['dome_w']
    cap = sphere("SHELL_DOME",(x0,y0,zb+P['skirt_h']), (P['dome_w']/2,P['dome_d']/2,P['dome_cap_h']),pal['dome'],collname=collname)
    # cut ellipsoid at skirt top -> true dome cap (lower half is not hidden by skirt)
    cut = cube("DOME_CUTTER",(x0,y0,zb+P['skirt_h']-1.0),(2.0,2.0,1.0),pal['chassis'])
    mod = cap.modifiers.new("Cut",'BOOLEAN'); mod.operation='DIFFERENCE'; mod.object=cut
    bpy.context.view_layer.objects.active = cap
    bpy.ops.object.modifier_apply(modifier='Cut')
    bpy.data.objects.remove(cut)
    if variant=='B':
        # panel seams: curves hugging the ellipsoid surface along meridians
        for ang in (60, -60, 180):
            phi = math.radians(ang)
            rx, ry, h = P['dome_w']/2, P['dome_d']/2, P['dome_cap_h']
            r_h = rx*ry/math.sqrt((ry*math.cos(phi))**2 + (rx*math.sin(phi))**2)
            pts = []
            for i in range(25):
                t = math.radians(8 + 80*i/24)
                hh = (r_h*math.sin(t) + 0.0012)*1.0
                zz = zb + P['skirt_h'] + h*math.cos(t)
                pts.append((x0 + hh*math.sin(phi), y0 - hh*math.cos(phi), zz, 1))
            cu = bpy.data.curves.new(f"SEAM_{ang}",'CURVE'); cu.dimensions='3D'
            cu.bevel_depth=0.0009; cu.bevel_resolution=2
            sp = cu.splines.new('POLY'); sp.points.add(len(pts)-1)
            for i,p in enumerate(pts): sp.points[i].co = p
            so = bpy.data.objects.new(f"SEAM_{ang}", cu); so.data.materials.append(pal['face'])
            coll(collname).objects.link(so)
        torus("SEAM_RING",(x0,y0,zb+P['skirt_h']+0.001),P['dome_w']/2*0.99,0.0012,pal['face'],scale=(1,P['dome_d']/P['dome_w'],1),collname=collname)
        # rim screws
        for i in range(6):
            a=math.radians(i*60+30)
            cyl(f"RIMSCREW_{i}",(x0+math.sin(a)*P['dome_w']/2*0.985, y0-math.cos(a)*P['dome_d']/2*0.985, zb+P['skirt_h']/2),
                0.0022,0.004,pal['chassis'],rot=(math.pi/2,0,-a),collname=collname)
    if variant=='C':
        # sculptural brow shelf shading the face (flattened cap over face top)
        sphere("BROW",(x0,P['face_y']-0.003,zb+0.070),(0.034,0.007,0.0050),pal['dome'],
               rot=(P['face_tilt'],0,0),collname=collname)

def build_face(x0, y0, pal, variant, collname, exploded=False):
    ey = -0.065 if exploded else 0.0
    th = P['face_tilt']; ct, st = math.cos(th), math.sin(th)
    fw, fh = P['face_w'], P['face_h']
    if variant=='C': fw, fh = 0.066, 0.042          # deeper recessed face
    fy = P['face_y'] + (0.0015 if variant=='A' else 0.0)
    def ppoint(dx, dz, proud=0.0015):
        yl = -(P['face_t']/2 + proud)
        return (x0+dx, fy+ey+y0 + yl*ct - dz*st, P['face_z'] + yl*st + dz*ct)
    fp = cube("FACE_PLATE",(x0,fy+ey+y0,P['face_z']),(fw/2,P['face_t']/2,fh/2),
              pal['face'],0.006,rot=(th,0,0),collname=collname)
    if variant=='B':
        for sx in (-1,1):
            cyl(f"FACE_SCREW_{sx}",ppoint(sx*(fw/2-0.005),-(fh/2-0.006),0.0006),
                0.0016,0.003,pal['chassis'],rot=(math.pi/2+th,0,0),collname=collname)
    # eyes: LED matrix squares seated on the tilted plate face
    for side,s in (("L",-1),("R",1)):
        eo = cube(f"EYES_{side}",ppoint(s*P['eye_gap']/2,0.003),(P['eye_w']/2,P['eye_t']/2,P['eye_h']/2),
                  pal['eyes'],0.004,rot=(th,0,0),collname=collname)
    # smile arc below eyes, on plate surface
    sx0, sy0, sz0 = ppoint(0,-0.008,0.0010)
    curve_arc("SMILE",(sx0,sy0,sz0),0.010,math.radians(215),math.radians(325),pal['eyes'],
              bevel_d=0.0015,tilt=(th,0,0),collname=collname)

def build_topper(x0, y0, pal, variant, collname, exploded=False):
    ez = 0.15 if exploded else 0.0
    tz = P['topper_z']+ez
    if variant=='A':      # 3-leaf sprout
        cyl("TOPPER_STEM",(x0,y0,tz+0.009),0.0045,0.020,pal['sprout'],collname=collname)
        for i,a in enumerate((0,math.radians(120),math.radians(240))):
            leaf = sphere(f"TOPPER_LEAF{i}",(x0+math.cos(a)*0.012,y0+math.sin(a)*0.012,tz+0.024),
                          (0.019,0.0085,0.004),pal['sprout'],rot=(0.5,-math.cos(a)*0.5,-a),collname=collname)
    elif variant=='B':    # geometric mushroom on visible mag puck
        cyl("TOPPER_PUCK",(x0,y0,tz+0.002),0.010,0.005,pal['chassis'],collname=collname)
        cyl("TOPPER_STEM",(x0,y0,tz+0.013),0.004,0.018,pal['accent'],collname=collname)
        sphere("TOPPER_CAP",(x0,y0,tz+0.026),(0.016,0.016,0.009),pal['accent'],seg=24,rings=12,collname=collname)
    else:                 # C button mushroom, sculptural
        cyl("TOPPER_STEM",(x0,y0,tz+0.010),0.0055,0.020,pal['accent'],collname=collname)
        sphere("TOPPER_CAP",(x0,y0,tz+0.024),(0.015,0.015,0.011),pal['accent'],collname=collname)

def build_hatch(x0, y0, pal, collname, exploded=False):
    ey = 0.05 if exploded else 0.0
    # upright panel flush-ish on rear dome, top leaning in to match surface slope
    cube("REAR_HATCH",(x0,P['hatch_y']+ey+y0,P['hatch_z']),(P['hatch_w']/2,0.0025,P['hatch_h']/2),
         pal['dome'],0.004,rot=(math.radians(28),0,0),collname=collname)

def build_chassis(x0, y0, pal, collname):
    cyl("CHASSIS_PROXY",(x0,y0,P['chassis_z']),P['chassis_r'],P['chassis_h'],pal['chassis'],collname=collname)

def build_variant(tag, x0, variant, palette='sage', exploded=False):
    pc = PALETTES[palette]
    pal = {k: mat(f"M_{tag}_{k}", v) for k, v in pc.items()}
    pal['eyes'] = mat(f"M_{tag}_eyes", (0.06,0.10,0.07,1), rough=0.3,
                      emit=(0.45,0.95,0.60,1), emit_s=7.0)
    cn = f"VAR_{tag}"
    build_chassis(x0,0,pal,cn)
    build_legs(x0,0,pal,variant,cn)
    build_dome(x0,0,pal,variant,cn,exploded)
    build_face(x0,0,pal,variant,cn,exploded)
    build_topper(x0,0,pal,variant,cn,exploded)
    build_hatch(x0,0,pal,cn,exploded)
    return cn

# ---------------- scene assembly ----------------
def studio():
    # world
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = w; w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.75,0.77,0.80,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.15
    # ground
    gm = mat("GROUND",(0.72,0.73,0.75,1),0.85)
    cube("GROUND",(0,0,-0.01),(4,4,0.01),gm,0.0)
    area_light("KEY",(-0.55,-0.55,0.85),90,0.5,(1.0,0.96,0.90))
    area_light("FILL",(0.65,-0.25,0.45),40,0.6,(0.85,0.90,1.0))
    area_light("RIM",(0.0,0.65,0.75),65,0.4,(1.0,1.0,1.0))
    sc = bpy.context.scene
    sc.view_settings.exposure = -1.0
    sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=1100; sc.render.resolution_y=900
    sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
    sc.render.resolution_percentage=100

def render(cam, path, res=(1100,900)):
    sc=bpy.context.scene; sc.camera=cam; sc.render.resolution_x,sc.render.resolution_y=res
    sc.render.filepath=path; bpy.ops.render.render(write_still=True)
    print("WROTE", path)

# ---------------- build ----------------
clear()
studio()

OFF = 0.30
labels = {}
build_variant("A", -OFF, 'A')
build_variant("B",  0.0, 'B')
build_variant("C", +OFF, 'C')
# exploded copies far right; colorways far left
build_variant("X", 1.30, 'B', exploded=True)     # exploded modular (recommended)
for i,pal in enumerate(("sage","graphite","terracotta")):
    build_variant(f"COL{i}", -1.20+i*0.30, 'B', palette=pal)

ink = mat("INK",(0.12,0.12,0.13,1),0.7)
LBL_COLS = {"cmp":"LBL_CMP","col":"LBL_COL","exp":"LBL_EXP"}
for t,x in (("A",-OFF),("B",0.0),("C",+OFF)):
    text_label(f"LBL_{t}",t,(x,-0.175,0.002),0.030,ink,collname="LBL_CMP")
for i,t in enumerate(("SAGE","GRAPHITE","TERRACOTTA")):
    text_label(f"LBLC_{i}",t,(-1.20+i*0.30,-0.175,0.002),0.020,ink,collname="LBL_COL")
text_label("LBLX","EXPLODED — proposed separations, unverified",
           (1.30,-0.16,0.002),0.020,ink,collname="LBL_EXP")

def show_labels(key):
    for k,cn in LBL_COLS.items():
        bpy.data.collections[cn].hide_render = (k != key)

ALL_VARCOLS = ["VAR_A","VAR_B","VAR_C","VAR_X","VAR_COL0","VAR_COL1","VAR_COL2"]
def show_only(keep):
    for cn in ALL_VARCOLS:
        bpy.data.collections[cn].hide_render = (cn not in keep)

# cameras (ortho_scale = horizontal extent for landscape frames)
c_cmp   = camera("CAM_CMP",(0,-1.05,0.24),(0,0,0.14),ortho=0.95)
c_heroA = camera("CAM_HEROA",(-OFF-0.24,-0.42,0.30),(-OFF,0,0.145),lens=62)
c_heroB = camera("CAM_HEROB",(0.24,-0.42,0.30),(0,0,0.145),lens=62)
c_heroC = camera("CAM_HEROC",(OFF+0.24,-0.42,0.30),(OFF,0,0.145),lens=62)
c_expl  = camera("CAM_EXPL",(1.30-0.45,-0.78,0.46),(1.30,0,0.24),lens=55)
c_col   = camera("CAM_COL",(-0.90,-1.05,0.28),(-0.90,0,0.13),ortho=0.95)
c_eyes  = camera("CAM_EYES",(-0.10,-0.42,0.24),(-0.0,-0.05,0.20),lens=80)
c_top   = camera("CAM_TOP",(0.13,-0.30,0.42),(0,0,0.27),lens=75)
c_seam  = camera("CAM_SEAM",(0.26,0.40,0.30),(0,0,0.16),lens=60)

def ortho_cams(x0, tag):
    d=0.9
    return {
     'front': camera(f"CAM_O_{tag}F",(x0,-d,0.16),(x0,0,0.14),ortho=0.40,clip_start=0.60,clip_end=1.10),
     'side':  camera(f"CAM_O_{tag}S",(x0-d,0,0.16),(x0,0,0.14),ortho=0.40,clip_start=0.60,clip_end=1.10),
     'rear':  camera(f"CAM_O_{tag}R",(x0,d,0.16),(x0,0,0.14),ortho=0.40,clip_start=0.60,clip_end=1.10),
     '34':    camera(f"CAM_O_{tag}Q",(x0-d*0.62,-d*0.62,0.30),(x0,0,0.14),ortho=0.42,clip_start=0.50,clip_end=1.45),
    }

os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT),"knoll-shell-v0.blend"))

# ---------------- render set ----------------
which = "all"
if "--" in sys.argv:
    args = sys.argv[sys.argv.index("--")+1:]
    for key in ("renders","--renders"):
        if key in args: which = args[args.index(key)+1]

def do(name): return which in ("all", name)

show_labels("none")
show_only(ALL_VARCOLS)
if do("comparison"):
    show_only(["VAR_A","VAR_B","VAR_C"]); show_labels("cmp")
    render(c_cmp, f"{OUT}/comparison.png",(1500,720)); show_labels("none")
if do("heroes"):
    for cam,col,nm in ((c_heroA,"VAR_A","a"),(c_heroB,"VAR_B","b"),(c_heroC,"VAR_C","c")):
        show_only([col]); render(cam, f"{OUT}/hero-variant-{nm}.png")
if do("ortho"):
    for tag,x,vc in (("a",-OFF,"VAR_A"),("b",0.0,"VAR_B"),("c",OFF,"VAR_C")):
        show_only([vc])
        for vn,c in ortho_cams(x,tag).items():
            render(c, f"{OUT}/ortho-{tag}-{vn}.png",(760,760))
if do("exploded"):
    show_only(["VAR_X"]); show_labels("exp")
    render(c_expl, f"{OUT}/exploded-b.png",(1100,900)); show_labels("none")
if do("colorways"):
    show_only(["VAR_COL0","VAR_COL1","VAR_COL2"]); show_labels("col")
    render(c_col,  f"{OUT}/colorways.png",(1400,760)); show_labels("none")
if do("details"):
    show_only(["VAR_B"])
    render(c_eyes, f"{OUT}/detail-eyes.png",(800,640))
    render(c_top,  f"{OUT}/detail-topper.png",(800,640))
    render(c_seam, f"{OUT}/detail-seam.png",(800,640))
show_only(ALL_VARCOLS)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT),"knoll-shell-v0.blend"))
print("DONE")
