import bpy, os, json, numpy as np, mathutils, math

FOLDER = r"ICT-FaceKit\FaceXModel"
PHOTO  = os.environ.get("PHOTO", "photo.jpg")
OUT    = r"."

cfg = json.load(open(os.path.join(FOLDER,"vertex_indices.json")))
exprs = cfg["expressions"]

# remove previous
for o in list(bpy.data.objects):
    if o.name == "ICTFaceModel" or o.name in exprs:
        bpy.data.objects.remove(o, do_unlink=True)

def imp(path):
    before = {o.name for o in bpy.data.objects}
    bpy.ops.wm.obj_import(filepath=path)
    return [o for o in bpy.data.objects if o.name not in before][0]

base = imp(os.path.join(FOLDER,"generic_neutral_mesh.obj")); base.name="ICTFaceModel"
base.data.name="ICTFaceModelMesh"
shp=[]
for n in exprs:
    o = imp(os.path.join(FOLDER, n+".obj")); o.name=n; shp.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in shp: o.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.ops.object.join_shapes(); bpy.ops.object.delete()
me = base.data
print("shape keys:", len(me.shape_keys.key_blocks))

# verify local coords == raw OBJ coords
neutral = np.load(os.path.join(OUT,"ict_neutral.npy"))
kb0 = me.shape_keys.key_blocks["Basis"]
loc = np.array([[v.co.x,v.co.y,v.co.z] for v in kb0.data])
print("local vs OBJ max abs diff: %.6f  (should be ~0)" % np.abs(loc-neutral).max())
print("local extents:", np.round(loc.max(0)-loc.min(0),2))

# ---- apply identity (raw units) ----
ids = np.load(os.path.join(OUT,"ict_ids.npy")); D = ids-neutral[None,:,:]
fit = json.load(open(os.path.join(OUT,"ict_fit.json"))); c = np.array(fit["identity_coefficients"])
K = fit["K"]
delta = (c[:K][:,None,None]*D[:K]).sum(0)          # raw units, local axes
print("identity delta(raw): mean %.3f max %.3f  (head y-extent %.1f)" % (
      np.linalg.norm(delta,axis=1).mean(), np.linalg.norm(delta,axis=1).max(), loc[:,1].max()-loc[:,1].min()))
for kb in me.shape_keys.key_blocks:
    for i,pt in enumerate(kb.data):
        pt.co = mathutils.Vector((pt.co.x+float(delta[i,0]), pt.co.y+float(delta[i,1]), pt.co.z+float(delta[i,2])))

# ---- scale + centre (local Y is up) ----
cur = np.array([[v.co.x,v.co.y,v.co.z] for v in me.shape_keys.key_blocks["Basis"].data])
sY = 0.26/(cur[:,1].max()-cur[:,1].min())
ctr = mathutils.Vector(((cur[:,0].min()+cur[:,0].max())/2, (cur[:,1].min()+cur[:,1].max())/2, (cur[:,2].min()+cur[:,2].max())/2))*sY
for kb in me.shape_keys.key_blocks:
    for pt in kb.data:
        pt.co = pt.co*sY - ctr
me.update(); bpy.context.view_layer.update()
print("scale %.6f applied" % sY)
cur = np.array([[v.co.x,v.co.y,v.co.z] for v in me.shape_keys.key_blocks["Basis"].data])
print("final local extents: x=%.3f y=%.3f z=%.3f" % tuple(cur.max(0)-cur.min(0)))
np.save(os.path.join(OUT,"ict_local_final.npy"), cur)

# ---- materials + photo UV ----
LM68=[1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]
chin = cur[LM68[8]]; eyes = cur[LM68[36:48]]
eye_y = eyes[:,1].mean(); eye_xL = eyes[:,0].min(); eye_xR = eyes[:,0].max()
y_min, y_max = cur[:,1].min(), cur[:,1].max()
print("local chin y=%.4f eye_y=%.4f top=%.4f" % (chin[1], eye_y, y_max))

img = bpy.data.images.get(os.path.basename(PHOTO)) or bpy.data.images.load(PHOTO, check_existing=True)
W,H = img.size
v_chin, v_eye = 0.287, 0.610
bz = (v_chin-v_eye)/(chin[1]-eye_y); az = v_chin - bz*chin[1]
EYE_SPAN = 0.62; L,R = 177,632
bx = (EYE_SPAN*(R-L))/W/(eye_xR-eye_xL); ax = (L/W + (R-L)/W*((1-EYE_SPAN)/2)) - bx*eye_xL
print("map v=%.3f%+.3f*y  u=%.3f%+.3f*x" % (az,bz,ax,bx))

uvname="PhotoUV"; uv = me.uv_layers.get(uvname) or me.uv_layers.new(name=uvname)
uv.active=True; uv.active_render=True
for poly in me.polygons:
    for li in poly.loop_indices:
        p = cur[me.loops[li].vertex_index]
        uv.data[li].uv=(min(max(ax+bx*p[0],0),1), min(max(az+bz*p[1],0),1))

px = list(img.pixels)
def get(x,y):
    i=(y*W+x)*4; return px[i],px[i+1],px[i+2]
def avg(xt,yt,rad=8):
    cx=int(xt*W); cy=int(yt*H); a=[0,0,0]; n=0
    for y in range(max(0,cy-rad),min(H,cy+rad+1)):
        for x in range(max(0,cx-rad),min(W,cx+rad+1)):
            r,g,b=get(x,y); a[0]+=r;a[1]+=g;a[2]+=b;n+=1
    return tuple(v/n for v in a)
skin = avg(0.34,0.45); hair = avg(0.50,0.95)
print("skin",[round(v,3) for v in skin],"hair",[round(v,3) for v in hair])

mp = bpy.data.materials.get("PhotoFace") or bpy.data.materials.new("PhotoFace")
mp.use_nodes=True; nt=mp.node_tree; nt.nodes.clear()
tex=nt.nodes.new("ShaderNodeTexImage"); tex.image=img; tex.location=(-500,0)
uvn=nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map=uvname; uvn.location=(-750,0)
bs=nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Roughness"].default_value=0.55
on=nt.nodes.new("ShaderNodeOutputMaterial"); on.location=(200,0)
nt.links.new(uvn.outputs["UV"],tex.inputs["Vector"]); nt.links.new(tex.outputs["Color"],bs.inputs["Base Color"])
nt.links.new(bs.outputs["BSDF"], on.inputs["Surface"])
msk = bpy.data.materials.get("SkinTone") or bpy.data.materials.new("SkinTone"); msk.use_nodes=True
b2=next(n for n in msk.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
b2.inputs["Base Color"].default_value=(*skin,1); b2.inputs["Roughness"].default_value=0.6
mh = bpy.data.materials.get("HairTone") or bpy.data.materials.new("HairTone"); mh.use_nodes=True
b3=next(n for n in mh.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
b3.inputs["Base Color"].default_value=(*hair,1); b3.inputs["Roughness"].default_value=0.45

def find_slot(prefix):
    for _i,_m in enumerate(me.materials):
        if _m and (_m.name == prefix or _m.name.startswith(prefix + ".")):
            return _i
    return None
i_face = find_slot("M_Face"); i_back = find_slot("M_BackHead")
print("slots:", [m.name if m else None for m in me.materials])
print("i_face =", i_face, " i_back =", i_back)
ip=len(me.materials); me.materials.append(mp)
isk=len(me.materials); me.materials.append(msk)
ih=len(me.materials); me.materials.append(mh)
nf=0
for poly in me.polygons:
    if poly.material_index==i_face:
        if poly.normal.z < -0.12: poly.material_index=ip; nf+=1
        else: poly.material_index=isk
    elif poly.material_index==i_back:
        poly.material_index=ih
print("photo polys:", nf, "| slots:", len(me.materials))

for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY'}: o.hide_viewport=o.hide_render=(o.name!="ICTFaceModel")
for col in bpy.data.collections: col.hide_viewport=col.hide_render=False

sc=bpy.context.scene; cam=sc.camera
cam.data.lens=55; sc.render.resolution_x=480; sc.render.resolution_y=600
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"ict_fit_f.png"),(0,-0.85,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"ict_fit_34.png"),(0.55,-0.65,0.05),(math.radians(82),0,math.radians(40))))

