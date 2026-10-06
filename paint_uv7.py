import bpy, os, numpy as np, math
OUT=r"<HOME>\tmp\blender"; W=H=512
me = bpy.data.objects["head_geo.002"].data
d = np.load(os.path.join(OUT,"head_uvmap.npz"))
pos, mask, nrm = d["pos"], d["mask"], d["nrm"]
X = np.nan_to_num(pos[:,:,0]); Y = np.nan_to_num(pos[:,:,1]); Z = np.nan_to_num(pos[:,:,2])
nY = np.nan_to_num(nrm[:,:,1])
base = bpy.data.images["RedPandaBase3"]
buf = np.zeros((H*W*4,), np.float32); base.pixels.foreach_get(buf)
img = buf.reshape(H,W,4)[:,:,:3].astype(np.float32)
front = mask & (nY < -0.15)

def disc(cx,cz,rx,rz,feather=0.30):
    dd = np.sqrt(((X-cx)/rx)**2 + ((Z-cz)/rz)**2)
    return np.clip((1.0-dd)/feather,0,1).astype(np.float32)
EX, EZ = 0.175, 0.02
eye_zone = np.maximum(disc(EX,EZ,0.19,0.17), disc(-EX,EZ,0.19,0.17))
w  = np.maximum(disc( EX, EZ+0.115, 0.10, 0.040), disc(-EX, EZ+0.115, 0.10, 0.040))
w  = np.maximum(w, np.clip((1-np.abs(X)/0.062),0,1)*np.clip((Z-0.16)/0.05,0,1)*np.clip((0.30-Z)/0.07,0,1))
w  = np.maximum(w, np.maximum(disc( 0.30,-0.085,0.085,0.095), disc(-0.30,-0.085,0.085,0.095)))
w  = np.where(front, w*(1-eye_zone), 0.0).astype(np.float32)

# 形态学开运算：去掉孤立斑点（接缝虚线）
def dil(b):
    o = b.copy()
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        o |= np.roll(b,(dy,dx),(0,1))
    return o
def ero(b):
    o = b.copy()
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        o &= np.roll(b,(dy,dx),(0,1))
    return o
solid = dil(ero(w > 0.30))                      # opening
w = np.where(solid, w, 0.0).astype(np.float32)
for _ in range(2):
    acc = np.zeros_like(w); cnt = np.zeros_like(w)
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
        acc += np.roll(w,(dy,dx),(0,1)); cnt += np.roll((w>0).astype(np.float32),(dy,dx),(0,1))
    w = np.where(cnt>0, w*0.5 + (acc/np.maximum(cnt,1))*0.5, w)
w = np.nan_to_num(np.clip(w,0,1))
CREAM = np.array([0.975,0.96,0.93], np.float32)
out = np.clip(img*(1-w[:,:,None]) + CREAM[None,None,:]*w[:,:,None], 0, 1).astype(np.float32)
print("solid cream texels: %d (去斑前 %d)" % (int((w>0.5).sum()), int((w>0.5).sum())))
im = bpy.data.images.get("RedPandaBase11")
if im is None: im = bpy.data.images.new("RedPandaBase11", width=W, height=H, alpha=False)
im.pixels.foreach_set(np.concatenate([out,np.ones((H,W,1),np.float32)],axis=2).astype(np.float32).reshape(-1))
im.filepath_raw=os.path.join(OUT,"redpanda_base11.png"); im.file_format='PNG'; im.save()
# 所有主体材质指向它（耳朵保持 Ear3）
ear = bpy.data.images["RedPandaEar3"]
for m in bpy.data.materials:
    if not m or not m.use_nodes: continue
    tag = "003" if m.name.startswith("MAT_Racoon.003") else "004"
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image:
            if "Base" in nd.image.name or "Ear" in nd.image.name:
                nd.image = ear if tag=="003" else im
sc=bpy.context.scene; cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=620; sc.render.resolution_y=620
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx0,cy0,cz0=0.0,0.04,0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"paint_f.png"),(cx0,cy0-D,cz0+0.02),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"paint_34.png"),(cx0+D*0.7,cy0-D*0.7,cz0+0.10),(math.radians(80),0,math.radians(45))))

PARTS=["head_geo.002","ears_geo","hair_geo","tufts_geo","raccoon_head"]
bpy.ops.object.select_all(action='DESELECT')
for n in PARTS:
    o=bpy.data.objects.get(n)
    if o: o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects["head_geo.002"]
p=os.path.join(OUT,"redpanda_head.glb")
if os.path.exists(p): os.remove(p)
base_kw=dict(filepath=p, export_format='GLB', use_selection=True, export_yup=True,
             export_skins=False, export_texcoords=True, export_normals=True, export_morph=True)
for i,kw in enumerate([dict(base_kw, export_morph_normal=False, export_meshopt_compression_enable=True),
                       dict(base_kw, export_morph_normal=False), dict(base_kw)]):
    try:
        bpy.ops.export_scene.gltf(**kw); print("export v%d -> %.2f MB" % (i, os.path.getsize(p)/1048576)); break
    except TypeError as e: print("v%d unsupported: %s" % (i, str(e)[:80]))
