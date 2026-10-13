import bpy, math, mathutils, os

PHOTO = os.environ.get("PHOTO", "photo.jpg")
obj = bpy.data.objects["ICTFaceModel"]

# ---- isolate ----
for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY'}:
        o.hide_viewport = o.hide_render = (o.name != "ICTFaceModel")
for c in bpy.context.scene.collection.children:
    c.hide_viewport = c.hide_render = True
bpy.context.scene.collection.children  # noop
obj.hide_viewport = obj.hide_render = False
for col in bpy.data.collections:
    col.hide_viewport = col.hide_render = True

# ---- normalize transform ----
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = obj.data
zs = [v.co.z for v in me.vertices]; ys=[v.co.y for v in me.vertices]; xs=[v.co.x for v in me.vertices]
h = max(zs)-min(zs)
TARGET_H = 0.26                      # realistic head height (m)
s = TARGET_H / h
for v in me.vertices:
    v.co = v.co * s
cx = (max(xs)+min(xs))/2*s; cy=(max(ys)+min(ys))/2*s; cz=(max(zs)+min(zs))/2*s
for v in me.vertices:
    v.co -= mathutils.Vector((cx, cy, cz))
obj.location = (0.0, 0.0, 0.0)
co = [v.co.copy() for v in me.vertices]
xs=[p.x for p in co]; ys=[p.y for p in co]; zs=[p.z for p in co]
print("scaled head: size %.3f x %.3f x %.3f m" % (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)))
print("slot names:", [m.name if m else None for m in me.materials])

# ---- photo analysis ----
img = bpy.data.images.get(os.path.basename(PHOTO))
if img is None:
    img = bpy.data.images.load(PHOTO, check_existing=True)
W,H = img.size
px = list(img.pixels)
def get(x,y):
    i=(y*W+x)*4; return px[i],px[i+1],px[i+2]
minx,maxx,miny,maxy = W,0,H,0
for y in range(0,H,2):
    for x in range(0,W,2):
        r,g,b = get(x,y)
        if not (r>0.93 and g>0.93 and b>0.93):
            minx=min(minx,x); maxx=max(maxx,x); miny=min(miny,y); maxy=max(maxy,y)
print("person bbox: x[%d,%d] y[%d,%d]  img %dx%d" % (minx,maxx,miny,maxy,W,H))
def avg(xt,yt_from_top,rad=6):
    cx=int(minx+(maxx-minx)*xt); cy=int(maxy-(maxy-miny)*yt_from_top)
    acc=[0,0,0]; n=0
    for y in range(max(0,cy-rad),min(H,cy+rad+1)):
        for x in range(max(0,cx-rad),min(W,cx+rad+1)):
            r,g,b=get(x,y); acc[0]+=r;acc[1]+=g;acc[2]+=b;n+=1
    return tuple(c/n for c in acc)
skin=avg(0.34,0.55); hair=avg(0.50,0.05)
print("skin:",[round(c,3) for c in skin],"hair:",[round(c,3) for c in hair])

# ---- planar UV from front (-Y) ----
uvname="PhotoUV"
uv = me.uv_layers.get(uvname) or me.uv_layers.new(name=uvname)
uv.active = True; uv.active_render = True
# face box in the photo (fractions of person bbox): top 0..0.66 vertically
pu0,pu1 = 0.10, 0.90
pv1,pv0 = 0.66, 0.005            # v from bottom: top of head=0.66? -> converted below
# head mesh: map z of head to v, x to u
Z0 = min(zs) + 0.06*(max(zs)-min(zs))     # exclude tiny neck stub
Z1 = max(zs)
X0, X1 = min(xs), max(xs)
for poly in me.polygons:
    for li in poly.loop_indices:
        p = co[me.loops[li].vertex_index]
        u = (p.x - X0)/(X1-X0)
        t = (p.z - Z0)/(Z1-Z0)
        # photo v: y from top 0.06 (top of head) .. 0.68 (chin/collar)
        vu0, vu1 = 1.0-0.68, 1.0-0.06
        v = vu0 + t*(vu1-vu0)
        uv.data[li].uv = (min(max(pu0+u*(pu1-pu0),0.0),1.0), min(max(v,0.0),1.0))

# ---- materials ----
mp = bpy.data.materials.get("PhotoFace") or bpy.data.materials.new("PhotoFace")
mp.use_nodes=True; nt=mp.node_tree; nt.nodes.clear()
tex=nt.nodes.new("ShaderNodeTexImage"); tex.image=img; tex.location=(-500,0)
uvn=nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map=uvname; uvn.location=(-750,0)
bs=nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.location=(-100,0)
bs.inputs["Roughness"].default_value=0.55
on=nt.nodes.new("ShaderNodeOutputMaterial"); on.location=(200,0)
nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
nt.links.new(bs.outputs["BSDF"], on.inputs["Surface"])

msk = bpy.data.materials.get("SkinTone") or bpy.data.materials.new("SkinTone")
msk.use_nodes=True
b2=next(n for n in msk.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
b2.inputs["Base Color"].default_value=(*skin,1); b2.inputs["Roughness"].default_value=0.6

mh = bpy.data.materials.get("HairTone") or bpy.data.materials.new("HairTone")
mh.use_nodes=True
b3=next(n for n in mh.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
b3.inputs["Base Color"].default_value=(*hair,1); b3.inputs["Roughness"].default_value=0.45

def slot_index(name):
    for i,m in enumerate(me.materials):
        if m and m.name==name: return i
    return None
i_photo = len(me.materials); me.materials.append(mp)
i_skin  = len(me.materials); me.materials.append(msk)
i_hair  = len(me.materials); me.materials.append(mh)
print("new material indices:", i_photo, i_skin, i_hair, "| total slots:", len(me.materials))

i_face = slot_index("M_Face"); i_back = slot_index("M_BackHead")
print("M_Face slot:", i_face, " M_BackHead slot:", i_back)

nfront=0
for poly in me.polygons:
    if poly.material_index == i_face:
        if poly.normal.y < -0.15:      # faces -Y (front)
            poly.material_index = i_photo; nfront+=1
        else:
            poly.material_index = i_skin
    elif poly.material_index == i_back:
        poly.material_index = i_hair
print("photo polys:", nfront)

# ---- camera + render ----
cam = bpy.data.objects.get("HeadCam")
if cam is None:
    cd = bpy.data.cameras.new("HeadCam"); cam = bpy.data.objects.new("HeadCam", cd)
    bpy.context.scene.collection.objects.link(cam)
cam.data.lens = 70
cam.location = (0.0, -0.75, 0.01)
cam.rotation_euler = (math.radians(90), 0.0, 0.0)
sc = bpy.context.scene; sc.camera = cam
out = r"ict_pass1.png"
sc.render.filepath = out
sc.render.resolution_x = 560; sc.render.resolution_y = 700
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
bpy.ops.render.render(write_still=True)
print("rendered:", os.path.exists(out), os.path.getsize(out) if os.path.exists(out) else 0)
