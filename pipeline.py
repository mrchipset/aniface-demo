import bpy, os, json, math, mathutils, numpy as np

FOLDER = r"ICT-FaceKit\FaceXModel"
OUT    = r"."
PHOTO  = os.environ.get("PHOTO", "photo.jpg")

cfg = json.load(open(os.path.join(FOLDER,"vertex_indices.json")))
exprs = cfg["expressions"]
for o in list(bpy.data.objects):
    if o.name in ("ICTFaceModel","AnifaceHead") or o.name in exprs:
        bpy.data.objects.remove(o, do_unlink=True)

def imp(path):
    b={o.name for o in bpy.data.objects}
    bpy.ops.wm.obj_import(filepath=path)
    return [o for o in bpy.data.objects if o.name not in b][0]

base = imp(os.path.join(FOLDER,"generic_neutral_mesh.obj")); base.name="AnifaceHead"
shp=[]
for n in exprs:
    o=imp(os.path.join(FOLDER,n+".obj")); o.name=n; shp.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in shp: o.select_set(True)
bpy.context.view_layer.objects.active=base
bpy.ops.object.join_shapes(); bpy.ops.object.delete()
me = base.data
print("[1] shape keys:", len(me.shape_keys.key_blocks), "verts:", len(me.vertices))

# identity
neutral = np.load(os.path.join(OUT,"ict_neutral.npy"))
ids = np.load(os.path.join(OUT,"ict_ids.npy")); D = ids-neutral[None,:,:]
fit = json.load(open(os.path.join(OUT,"ict_fit.json"))); c=np.array(fit["identity_coefficients"]); K=fit["K"]
delta = (c[:K][:,None,None]*D[:K]).sum(0)
for kb in me.shape_keys.key_blocks:
    for i,pt in enumerate(kb.data):
        pt.co = mathutils.Vector((pt.co.x+delta[i,0], pt.co.y+delta[i,1], pt.co.z+delta[i,2]))
print("[2] identity applied (K=%d |c|=%.2f)" % (K, np.linalg.norm(c[:K])))

# scale + centre (local Y is up)
cur = np.array([[v.co.x,v.co.y,v.co.z] for v in me.shape_keys.key_blocks["Basis"].data])
sY = 0.26/(cur[:,1].max()-cur[:,1].min())
ctr = mathutils.Vector(((cur[:,0].min()+cur[:,0].max())/2,(cur[:,1].min()+cur[:,1].max())/2,(cur[:,2].min()+cur[:,2].max())/2))*sY
for kb in me.shape_keys.key_blocks:
    for pt in kb.data: pt.co = pt.co*sY - ctr
me.update(); bpy.context.view_layer.update()
cur = np.array([[v.co.x,v.co.y,v.co.z] for v in me.shape_keys.key_blocks["Basis"].data])
print("[3] scaled x%.5f -> extents x=%.3f y=%.3f z=%.3f" % (sY, *(cur.max(0)-cur.min(0))))

# normals outward
bpy.ops.object.select_all(action='DESELECT'); base.select_set(True)
bpy.context.view_layer.objects.active=base
try:
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    print("[4] normals recalculated")
except Exception as e:
    print("[4] normals failed:", e)
    try: bpy.ops.object.mode_set(mode='OBJECT')
    except: pass

# UV projection using landmarks (BEFORE any deletion)
LM68=[1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]
chin = cur[LM68[8]]; eyes = cur[LM68[36:48]]
ey = eyes[:,1].mean(); exl=eyes[:,0].min(); exr=eyes[:,0].max()
v_chin,v_eye=0.287,0.610
bz=(v_chin-v_eye)/(chin[1]-ey); az=v_chin-bz*chin[1]
EYE_SPAN=0.62; L,R=177,632
bx=(EYE_SPAN*(R-L))/827/(exr-exl); ax=(L/827+(R-L)/827*((1-EYE_SPAN)/2))-bx*exl
uv = me.uv_layers.get("PhotoUV") or me.uv_layers.new(name="PhotoUV")
uv.active=True; uv.active_render=True
for poly in me.polygons:
    for li in poly.loop_indices:
        p=cur[me.loops[li].vertex_index]
        uv.data[li].uv=(min(max(ax+bx*p[0],0),1), min(max(az+bz*p[1],0),1))
print("[5] UV map v=%.3f%+.3f*y u=%.3f%+.3f*x" % (az,bz,ax,bx))

# materials
img = bpy.data.images.get(os.path.basename(PHOTO)) or bpy.data.images.load(PHOTO, check_existing=True)
W,H=img.size; px=list(img.pixels)
def get(x,y):
    i=(y*W+x)*4; return px[i],px[i+1],px[i+2]
def avg(xt,yt,rad=10):
    cx=int(xt*W); cy=int(yt*H); a=[0,0,0]; n=0
    for y in range(max(0,cy-rad),min(H,cy+rad+1)):
        for x in range(max(0,cx-rad),min(W,cx+rad+1)):
            r,g,b=get(x,y); a[0]+=r;a[1]+=g;a[2]+=b;n+=1
    return tuple(v/n for v in a)
skin=avg(0.34,0.56); hair=avg(0.50,0.88)
mp = bpy.data.materials.get("PhotoFace") or bpy.data.materials.new("PhotoFace")
mp.use_nodes=True; nt=mp.node_tree; nt.nodes.clear()
tex=nt.nodes.new("ShaderNodeTexImage"); tex.image=img
uvn=nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map="PhotoUV"
bs=nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Roughness"].default_value=0.75
on=nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(uvn.outputs["UV"],tex.inputs["Vector"]); nt.links.new(tex.outputs["Color"],bs.inputs["Base Color"])
nt.links.new(bs.outputs["BSDF"],on.inputs["Surface"])
for nm,col,rough in (("SkinTone",skin,0.8),("HairTone",hair,0.5)):
    m=bpy.data.materials.get(nm) or bpy.data.materials.new(nm); m.use_nodes=True
    b=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value=(*col,1); b.inputs["Roughness"].default_value=rough
def slot(pfx):
    for i,m in enumerate(me.materials):
        if m and (m.name==pfx or m.name.startswith(pfx+".")): return i
names=[m.name if m else "" for m in me.materials]
# reuse existing PhotoFace slots if present
ip = names.index("PhotoFace") if "PhotoFace" in names else len(me.materials)
if ip==len(me.materials): me.materials.append(mp)
isk = names.index("SkinTone") if "SkinTone" in names else len(me.materials)
if isk==len(me.materials): me.materials.append(bpy.data.materials["SkinTone"])
ih = names.index("HairTone") if "HairTone" in names else len(me.materials)
if ih==len(me.materials): me.materials.append(bpy.data.materials["HairTone"])
i_face=slot("M_Face"); i_back=slot("M_BackHead")
nph=0
for p in me.polygons:
    if p.material_index==i_face:
        p.material_index = ip if p.normal.z < 0.0 else isk
        nph += (p.material_index==ip)
    elif p.material_index==i_back:
        p.material_index=ih
print("[6] photo polys=%d  skin=%d  (i_face=%s i_back=%s)" % (nph, len(me.polygons)-nph, i_face, i_back))

# rename shape keys to ARKit
sk=me.shape_keys
def find(n):
    for k in sk.key_blocks:
        if k.name==n: return k
    return None
def merge(name,a,b):
    ka,kb2=find(a),find(b)
    if not(ka and kb2): return
    basis=find("Basis"); new=base.shape_key_add(name=name, from_mix=False)
    for i in range(len(ka.data)):
        new.data[i].co = ka.data[i].co + kb2.data[i].co - basis.data[i].co
    base.shape_key_remove(ka); base.shape_key_remove(kb2)
merge("browInnerUp","browInnerUp_L","browInnerUp_R")
merge("cheekPuff","cheekPuff_L","cheekPuff_R")
for k in list(sk.key_blocks):
    if k.name.endswith("_L"): k.name=k.name[:-2]+"Left"
    elif k.name.endswith("_R"): k.name=k.name[:-2]+"Right"
body=[k.name for k in sk.key_blocks if k.name!="Basis"]
ARKSET=set("""eyeBlinkLeft eyeBlinkRight eyeSquintLeft eyeSquintRight eyeWideLeft eyeWideRight eyeLookDownLeft eyeLookDownRight eyeLookInLeft eyeLookInRight eyeLookOutLeft eyeLookOutRight eyeLookUpLeft eyeLookUpRight browDownLeft browDownRight browInnerUp browOuterUpLeft browOuterUpRight cheekPuff cheekSquintLeft cheekSquintRight noseSneerLeft noseSneerRight mouthClose mouthFunnel mouthPucker mouthLeft mouthRight mouthSmileLeft mouthSmileRight mouthFrownLeft mouthFrownRight mouthDimpleLeft mouthDimpleRight mouthStretchLeft mouthStretchRight mouthRollLower mouthRollUpper mouthShrugLower mouthShrugUpper mouthPressLeft mouthPressRight mouthLowerDownLeft mouthLowerDownRight mouthUpperUpLeft mouthUpperUpRight jawOpen jawForward jawLeft jawRight tongueOut""".split())
print("[7] keys=%d  ARKit-matched=%d/52  missing=%s  extra=%s" % (len(body), len([n for n in body if n in ARKSET]), sorted(ARKSET-set(body)), sorted(set(body)-ARKSET)))

# export (no morph normals; try meshopt)
p=os.path.join(OUT,"aniface_head.glb")
if os.path.exists(p): os.remove(p)
bpy.ops.object.select_all(action='DESELECT'); base.select_set(True); bpy.context.view_layer.objects.active=base
base_=dict(filepath=p, export_format='GLB', use_selection=True, export_yup=True,
           export_skins=False, export_texcoords=True, export_normals=True, export_morph=True)
for i,kw in enumerate([dict(base_, export_morph_normal=False, export_meshopt_compression_enable=True),
                       dict(base_, export_morph_normal=False),
                       dict(base_)]):
    try:
        bpy.ops.export_scene.gltf(**kw); print("[8] export variant %d -> %.1f MB" % (i, os.path.getsize(p)/1048576)); break
    except TypeError as e: print("[8] variant %d unsupported: %s" % (i, str(e)[:100]))
