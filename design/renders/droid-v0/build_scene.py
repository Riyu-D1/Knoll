# Knoll Mk1 — droid-v0 concept scene builder (agile biped archetype)
# Blender 4.5 headless:  blender --background --python build_scene.py -- --renders all|subset
# 15-DOF visual proxy: 5/leg + 2/arm + 1 neck. All dims METRES.
# CONCEPT VISUALISATION ONLY — not validated mechanical geometry.

import bpy, math, os, sys
from mathutils import Vector

P = dict(
    # legs (unchanged joint heights vs mechanical-architecture.md)
    hip_x=0.040, hip_z=0.140, knee_z=0.085, ankle_z=0.020,
    knee_fwd=-0.008, ankle_fwd=0.004,          # athletic slightly-loaded stance
    foot_w=0.080, foot_l=0.095, foot_h=0.024, foot_yaw=math.radians(8),
    # torso/head
    torso_w=0.095, torso_d=0.082, torso_h=0.105, torso_z=0.198,  # capsule centre
    waist_z=0.152,
    neck_z=0.252, head_w=0.074, head_d=0.070, head_h=0.064, head_z=0.285,
    # arms: shoulder pitch+roll at ±0.052, z~0.232
    shoulder_x=0.052, shoulder_z=0.230,
    elbow_z=0.190, wrist_z=0.158,
    # face
    face_z=0.287, face_y=-0.036, face_w=0.052, face_h=0.030, face_t=0.004, face_tilt=math.radians(-6),
    eye_w=0.016, eye_h=0.016, eye_gap=0.030, eye_t=0.003,
)

PALETTES = {
    "sage":      dict(body=(0.62,0.66,0.60,1), trim=(0.20,0.32,0.15,1), accent=(0.30,0.42,0.24,1),
                      face=(0.020,0.024,0.020,1), feet=(0.10,0.10,0.11,1), legs=(0.30,0.31,0.31,1),
                      joints=(0.09,0.09,0.10,1), chassis=(0.08,0.08,0.09,1)),
    "graphite":  dict(body=(0.22,0.22,0.24,1), trim=(0.75,0.55,0.12,1), accent=(0.75,0.55,0.12,1),
                      face=(0.03,0.03,0.035,1), feet=(0.09,0.09,0.10,1), legs=(0.24,0.24,0.26,1),
                      joints=(0.08,0.08,0.09,1), chassis=(0.08,0.08,0.09,1)),
    "terracotta":dict(body=(0.70,0.50,0.38,1), trim=(0.40,0.22,0.15,1), accent=(0.40,0.22,0.15,1),
                      face=(0.04,0.04,0.04,1), feet=(0.10,0.10,0.10,1), legs=(0.26,0.24,0.24,1),
                      joints=(0.09,0.08,0.08,1), chassis=(0.08,0.08,0.09,1)),
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
    m = ob.modifiers.new("Bevel",'BEVEL'); m.width=w; m.segments=seg; return ob

def cube(name, loc, scale, material, bev=0.0, rot=(0,0,0), collname=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bev: bevel(o,bev)
    o.data.materials.append(material)
    if collname: move_to_coll(o,collname)
    return o

def sphere(name, loc, scale, material, rot=(0,0,0), seg=40, rings=20, collname=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    if collname: move_to_coll(o,collname)
    return o

def capsule(name, p1, p2, r, material, collname=None):
    """Cylinder + end spheres between two points — reads as a limb."""
    p1,p2=Vector(p1),Vector(p2); d=p2-p1
    o=cyl(name+"_mid",(p1+p2)/2,r,d.length,material,collname=collname)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=d.to_track_quat('Z','Y')
    sphere(name+"_a",p1,(r,r,r),material,collname=collname)
    sphere(name+"_b",p2,(r,r,r),material,collname=collname)

def cyl(name, loc, r, depth, material, rot=(0,0,0), collname=None):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(material)
    if collname: move_to_coll(o,collname)
    return o

def strut(name, p1, p2, w, h, material, bev=0.006, collname=None):
    p1,p2=Vector(p1),Vector(p2); d=p2-p1
    o=cube(name,(p1+p2)/2,(w/2,h/2,d.length/2),material,bev,collname=collname)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=d.to_track_quat('Z','Y')
    return o

def curve_arc(name, center, radius, a0, a1, material, bevel_d=0.0016, tilt=(0,0,0), collname=None):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=bevel_d; cu.bevel_resolution=3
    sp=cu.splines.new('POLY'); n=24; sp.points.add(n-1)
    for i in range(n):
        a=a0+(a1-a0)*i/(n-1); sp.points[i].co=(math.cos(a)*radius,0,math.sin(a)*radius,1)
    o=bpy.data.objects.new(name,cu); o.location=center; o.rotation_euler=tilt
    o.data.materials.append(material)
    (coll(collname) if collname else bpy.context.scene.collection).objects.link(o); return o

def text_label(name, body, loc, size, material, rot=(math.pi/2,0,0), collname=None):
    cu=bpy.data.curves.new(name,'FONT'); cu.body=body; cu.size=size; cu.align_x='CENTER'
    o=bpy.data.objects.new(name,cu); o.location=loc; o.rotation_euler=rot
    o.data.materials.append(material)
    (coll(collname) if collname else bpy.context.scene.collection).objects.link(o); return o

def camera(name, loc, look_at, lens=70, ortho=None, clip_start=None, clip_end=None):
    cd=bpy.data.cameras.new(name)
    if ortho: cd.type='ORTHO'; cd.ortho_scale=ortho
    else: cd.lens=lens
    if clip_start: cd.clip_start=clip_start
    if clip_end: cd.clip_end=clip_end
    o=bpy.data.objects.new(name,cd); o.location=loc
    o.rotation_euler=(Vector(look_at)-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.collection.objects.link(o); return o

def area_light(name, loc, energy, size, color):
    ld=bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.shape='DISK'; ld.size=size; ld.color=color
    o=bpy.data.objects.new(name,ld); o.location=loc
    o.rotation_euler=(Vector((0,0,0.15))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.collection.objects.link(o); return o

# ---------------- robot builders ----------------
def build_legs(x0, y0, pal, style, collname):
    hx=P['hip_x']; kz=P['knee_z']; az=P['ankle_z']; kf=P['knee_fwd']; af=P['ankle_fwd']
    for side,s in (("L",-1),("R",1)):
        X=lambda v: s*v+x0
        cube(f"LEG_{side}_HIPBLK",(X(hx),y0,P['hip_z']),(0.019,0.017,0.014),pal['joints'],0.004,collname=collname)
        cyl(f"LEG_{side}_HIPJ",(X(hx),y0,P['hip_z']),0.011,0.042,pal['joints'],rot=(0,math.pi/2,0),collname=collname)
        strut(f"LEG_{side}_FEMUR",(X(hx),y0,P['hip_z']),(X(hx+0.004),y0+kf,kz),0.016,0.026,pal['legs'],collname=collname)
        cyl(f"LEG_{side}_KNEE",(X(hx+0.004),y0+kf,kz),0.011,0.040,pal['joints'],rot=(0,math.pi/2,0),collname=collname)
        strut(f"LEG_{side}_SHANK",(X(hx+0.004),y0+kf,kz),(X(hx+0.008),y0+af,az),0.014,0.022,pal['legs'],collname=collname)
        cyl(f"LEG_{side}_ANKLE",(X(hx+0.008),y0+af,az),0.010,0.038,pal['joints'],rot=(0,math.pi/2,0),collname=collname)
        axv,fy,fz = X(hx+0.008), y0-0.002, P['foot_h']/2
        if style=='A':   # rounded shoe
            o=sphere(f"FOOT_{side}",(axv,fy-0.008,fz),(P['foot_w']/2,P['foot_l']/2,P['foot_h']/2),pal['feet'],collname=collname)
        elif style=='B': # angular runner
            o=cube(f"FOOT_{side}",(axv,fy,fz+0.002),(P['foot_w']/2,P['foot_l']/2,P['foot_h']/2),pal['feet'],0.007,collname=collname)
        else:            # sculpted shoe, toe forward
            o=sphere(f"FOOT_{side}",(axv,fy-0.012,fz+0.002),(P['foot_w']*0.52,P['foot_l']/2,P['foot_h']/2),pal['feet'],collname=collname)
        o.rotation_euler[2]=s*P['foot_yaw']
        so=cyl(f"FOOT_{side}_SOLE",(axv,fy,0.0035),P['foot_w']/2*0.9,0.007,pal['chassis'],collname=collname)
        so.scale.y=P['foot_l']/P['foot_w']; so.rotation_euler[2]=s*P['foot_yaw']

def build_torso(x0, y0, pal, variant, collname, exploded=False):
    ez = 0.075 if exploded else 0.0
    tw,th,td,tz = P['torso_w'],P['torso_h'],P['torso_d'],P['torso_z']+ez
    if variant=='B':
        cube("TORSO",(x0,y0,tz),(tw/2,td/2,th/2),pal['body'],0.020,collname=collname)
        cube("TORSO_WAIST",(x0,y0,P['waist_z']+ez),(tw*0.36,td*0.42,0.012),pal['trim'],0.005,collname=collname)
        # chest service panel + fasteners
        cube("CHEST_PANEL",(x0,y0-td/2-0.001,tz+0.008),(tw*0.30,0.003,th*0.22),pal['trim'],0.004,rot=(0,0,0),collname=collname)
        for sx in (-1,1):
            cyl(f"CHEST_SCREW_{sx}",(x0+sx*tw*0.26,y0-td/2-0.004,tz+0.008),0.0016,0.003,pal['joints'],rot=(math.pi/2,0,0),collname=collname)
        # shoulder caps with visible fasteners
        for s in (-1,1):
            cyl(f"SHOULDER_CAP{s}",(x0+s*(tw/2+0.004),y0,P['shoulder_z']+ez),0.014,0.010,pal['joints'],rot=(0,math.pi/2,0),collname=collname)
    elif variant=='C':
        # tapered organic torso: upper chest + waist
        sphere("TORSO",(x0,y0,tz+0.010),(tw*0.56,td*0.55,th*0.42),pal['body'],collname=collname)
        sphere("WAIST",(x0,y0,P['waist_z']+ez+0.010),(tw*0.40,td*0.44,th*0.30),pal['body'],collname=collname)
        torus_ring=None
        cyl("WAIST_RING",(x0,y0,P['waist_z']+ez+0.012),tw*0.42,0.008,pal['trim'],collname=collname).scale.y=td/tw
    else:
        sphere("TORSO",(x0,y0,tz),(tw*0.55,td*0.55,th/2),pal['body'],collname=collname)
        cyl("BELT",(x0,y0,P['waist_z']+ez),tw*0.50,0.010,pal['trim'],collname=collname).scale.y=td/tw

def build_head(x0, y0, pal, variant, collname, exploded=False):
    ez = 0.12 if exploded else 0.0
    hz = P['head_z']+ez
    # neck pitch servo + stub
    cyl("NECK_SERVO",(x0,y0,P['neck_z']+ez),0.011,0.024,pal['joints'],collname=collname)
    cyl("NECK_STUB",(x0,y0-0.004,P['neck_z']+ez+0.016),0.008,0.026,pal['legs'],rot=(P['face_tilt']*1.5,0,0),collname=collname)
    hw,hh,hd = P['head_w'],P['head_h'],P['head_d']
    if variant=='B':
        cube("HEAD",(x0,y0,hz),(hw/2,hd/2,hh/2),pal['body'],0.014,rot=(P['face_tilt'],0,0),collname=collname)
    elif variant=='C':
        sphere("HEAD",(x0,y0-0.002,hz),(hw*0.54,hd*0.52,hh*0.58),pal['body'],collname=collname)
        # subtle helmet part line
        curve_arc("HELMET_LINE",(x0,y0-0.002,hz),hw*0.545,math.radians(60),math.radians(120),
                  pal['trim'],bevel_d=0.0011,tilt=(math.pi/2,0,0),collname=collname)
    else:
        sphere("HEAD",(x0,y0-0.002,hz),(hw*0.55,hd*0.52,hh/2),pal['body'],collname=collname)
    # face: dark visor plate + LED eyes (+ smile on A)
    th=P['face_tilt']; ct,st=math.cos(th),math.sin(th)
    fy=P['face_y']
    def ppoint(dx,dz,proud=0.0015):
        yl=-(P['face_t']/2+proud)
        return (x0+dx, fy+y0+yl*ct-dz*st, P['face_z']+ez+yl*st+dz*ct)
    fw = P['face_w'] if variant!='C' else 0.058
    cube("FACE_VISOR",ppoint(0,0,-P['face_t']/2),(fw/2,P['face_t']/2,P['face_h']/2),pal['face'],0.007,rot=(th,0,0),collname=collname)
    if variant=='B':
        # single wide eye-bar: engineered read
        cube("EYES_BAR",ppoint(0,0.003),(0.022,0.0028,0.0055),pal['eyes'],0.0025,rot=(th,0,0),collname=collname)
    else:
        for side,s in (("L",-1),("R",1)):
            cube(f"EYES_{side}",ppoint(s*P['eye_gap']/2,0.002),(P['eye_w']/2,P['eye_t']/2,P['eye_h']/2),
                 pal['eyes'],0.0035,rot=(th,0,0),collname=collname)
    if variant=='A':
        sx0,sy0,sz0=ppoint(0,-0.009,0.001)
        curve_arc("SMILE",(sx0,sy0,sz0),0.009,math.radians(215),math.radians(325),pal['eyes'],
                  bevel_d=0.0013,tilt=(th,0,0),collname=collname)

def build_arms(x0, y0, pal, variant, collname, exploded=False):
    for side,s in (("L",-1),("R",1)):
        ex = s*0.014 if exploded else 0.0
        sx = x0+s*(P['shoulder_x'])+ex
        sz = P['shoulder_z']
        # shoulder: pitch servo (axis X) + roll disc
        sphere(f"ARM_{side}_SHOULDER",(sx,y0,sz),(0.013,0.013,0.013),pal['joints'],collname=collname)
        # slightly bent, hands forward-down: agile ready pose
        el = (sx+s*0.010, y0-0.006, P['elbow_z'])
        wr = (sx+s*0.004, y0-0.018, P['wrist_z'])
        hd = (sx+s*0.002, y0-0.024, P['wrist_z']-0.016)
        if variant=='B':
            strut(f"ARM_{side}_UPPER",(sx,y0,sz),el,0.013,0.013,pal['legs'],0.004,collname=collname)
            sphere(f"ARM_{side}_ELBOW",el,(0.009,0.009,0.009),pal['joints'],collname=collname)
            strut(f"ARM_{side}_FORE",el,wr,0.011,0.011,pal['legs'],0.004,collname=collname)
            cube(f"ARM_{side}_HAND",hd,(0.009,0.011,0.010),pal['feet'],0.004,collname=collname)
        else:
            capsule(f"ARM_{side}_UPPER",(sx,y0,sz),el,0.0068,pal['body'] if variant=='C' else pal['legs'],collname=collname)
            sphere(f"ARM_{side}_ELBOW",el,(0.0085,0.0085,0.0085),pal['joints'],collname=collname)
            capsule(f"ARM_{side}_FORE",el,wr,0.0060,pal['body'] if variant=='C' else pal['legs'],collname=collname)
            sphere(f"ARM_{side}_HAND",hd,(0.011,0.009,0.013),pal['feet'],collname=collname)

def build_variant(tag,x0,variant,palette='sage',exploded=False):
    pc=PALETTES[palette]
    pal={k:mat(f"M_{tag}_{k}",v) for k,v in pc.items()}
    pal['eyes']=mat(f"M_{tag}_eyes",(0.06,0.10,0.07,1),rough=0.3,emit=(0.45,0.95,0.60,1),emit_s=10.0)
    cn=f"VAR_{tag}"
    build_legs(x0,0,pal,variant,cn)
    build_torso(x0,0,pal,variant,cn,exploded)
    build_head(x0,0,pal,variant,cn,exploded)
    build_arms(x0,0,pal,variant,cn,exploded)
    return cn

# ---------------- scene ----------------
def studio():
    w=bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world=w; w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.75,0.77,0.80,1)
    w.node_tree.nodes["Background"].inputs[1].default_value=0.15
    gm=mat("GROUND",(0.72,0.73,0.75,1),0.85)
    cube("GROUND",(0,0,-0.01),(4,4,0.01),gm,0.0)
    area_light("KEY",(-0.55,-0.55,0.85),90,0.5,(1.0,0.96,0.90))
    area_light("FILL",(0.65,-0.25,0.45),40,0.6,(0.85,0.90,1.0))
    area_light("RIM",(0.0,0.65,0.75),65,0.4,(1.0,1.0,1.0))
    sc=bpy.context.scene
    sc.view_settings.exposure=-1.0
    sc.render.engine='BLENDER_EEVEE_NEXT'
    sc.render.image_settings.file_format='PNG'; sc.render.film_transparent=False
    sc.render.resolution_percentage=100

def render(cam,path,res=(1100,900)):
    sc=bpy.context.scene; sc.camera=cam; sc.render.resolution_x,sc.render.resolution_y=res
    sc.render.filepath=path; bpy.ops.render.render(write_still=True)
    print("WROTE",path)

clear(); studio()

OFF=0.32
build_variant("A",-OFF,'A'); build_variant("B",0.0,'B'); build_variant("C",OFF,'C')
build_variant("X",1.35,'B',exploded=True)
for i,pal_ in enumerate(("sage","graphite","terracotta")):
    build_variant(f"COL{i}",-1.25+i*0.32,'B',palette=pal_)

ink=mat("INK",(0.10,0.10,0.11,1),0.7)
LBL_COLS={"cmp":"LBL_CMP","col":"LBL_COL","exp":"LBL_EXP"}
for t,x in (("A",-OFF),("B",0.0),("C",OFF)):
    text_label(f"LBL_{t}",t,(x,-0.19,0.002),0.030,ink,collname="LBL_CMP")
for i,t in enumerate(("SAGE","GRAPHITE","TERRACOTTA")):
    text_label(f"LBLC_{i}",t,(-1.25+i*0.32,-0.19,0.002),0.020,ink,collname="LBL_COL")
text_label("LBLX","EXPLODED — unverified",(1.35,-0.13,0.002),0.020,ink,collname="LBL_EXP")

def show_labels(key):
    for k,cn in LBL_COLS.items(): bpy.data.collections[cn].hide_render=(k!=key)

ALL_VARCOLS=["VAR_A","VAR_B","VAR_C","VAR_X","VAR_COL0","VAR_COL1","VAR_COL2"]
def show_only(keep):
    for cn in ALL_VARCOLS: bpy.data.collections[cn].hide_render=(cn not in keep)

# cameras
c_cmp=camera("CAM_CMP",(0,-1.05,0.26),(0,0,0.15),ortho=0.98)
c_heroA=camera("CAM_HEROA",(-OFF-0.27,-0.52,0.35),(-OFF,0,0.16),lens=55)
c_heroB=camera("CAM_HEROB",(0.27,-0.52,0.35),(0,0,0.16),lens=55)
c_heroC=camera("CAM_HEROC",(OFF+0.27,-0.52,0.35),(OFF,0,0.16),lens=55)
c_expl=camera("CAM_EXPL",(1.35-0.48,-0.80,0.48),(1.35,0,0.26),lens=55)
c_col=camera("CAM_COL",(-0.93,-1.05,0.30),(-0.93,0,0.14),ortho=0.98)
c_face=camera("CAM_FACE",(-0.08,-0.42,0.30),(0,-0.02,0.28),lens=80)
c_arm=camera("CAM_ARM",(0.22,-0.40,0.26),(0.04,0,0.19),lens=75)
c_rear=camera("CAM_SEAM",(0.28,0.42,0.34),(0,0,0.17),lens=60)

def ortho_cams(x0,tag):
    d=0.95
    return {
     'front':camera(f"CAM_O_{tag}F",(x0,-d,0.17),(x0,0,0.15),ortho=0.42,clip_start=0.60,clip_end=1.15),
     'side':camera(f"CAM_O_{tag}S",(x0-d,0,0.17),(x0,0,0.15),ortho=0.42,clip_start=0.60,clip_end=1.15),
     'rear':camera(f"CAM_O_{tag}R",(x0,d,0.17),(x0,0,0.15),ortho=0.42,clip_start=0.60,clip_end=1.15),
     '34':camera(f"CAM_O_{tag}Q",(x0-d*0.62,-d*0.62,0.34),(x0,0,0.15),ortho=0.44,clip_start=0.55,clip_end=1.55),
    }

os.makedirs(OUT,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT),"knoll-droid-v0.blend"))

which="all"
if "--" in sys.argv:
    args=sys.argv[sys.argv.index("--")+1:]
    for key in ("renders","--renders"):
        if key in args: which=args[args.index(key)+1]
def do(name): return which in ("all",name)

show_labels("none"); show_only(ALL_VARCOLS)
if do("comparison"):
    show_only(["VAR_A","VAR_B","VAR_C"]); show_labels("cmp")
    render(c_cmp,f"{OUT}/comparison.png",(1500,720)); show_labels("none")
if do("heroes"):
    for cam,colc,nm in ((c_heroA,"VAR_A","a"),(c_heroB,"VAR_B","b"),(c_heroC,"VAR_C","c")):
        show_only([colc]); render(cam,f"{OUT}/hero-variant-{nm}.png")
if do("ortho"):
    for tag,x,vc in (("a",-OFF,"VAR_A"),("b",0.0,"VAR_B"),("c",OFF,"VAR_C")):
        show_only([vc])
        for vn,c in ortho_cams(x,tag).items():
            render(c,f"{OUT}/ortho-{tag}-{vn}.png",(760,760))
if do("exploded"):
    show_only(["VAR_X"]); show_labels("exp")
    render(c_expl,f"{OUT}/exploded-b.png",(1100,900)); show_labels("none")
if do("colorways"):
    show_only(["VAR_COL0","VAR_COL1","VAR_COL2"]); show_labels("col")
    render(c_col,f"{OUT}/colorways.png",(1400,760)); show_labels("none")
if do("details"):
    show_only(["VAR_B"])
    render(c_face,f"{OUT}/detail-face.png",(800,640))
    render(c_arm,f"{OUT}/detail-arm.png",(800,640))
    render(c_rear,f"{OUT}/detail-rear.png",(800,640))
show_only(ALL_VARCOLS)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(OUT),"knoll-droid-v0.blend"))
print("DONE")
