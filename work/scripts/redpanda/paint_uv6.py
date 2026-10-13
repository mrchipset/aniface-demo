import bpy, os, numpy as np, math
OUT=r"."; W=H=512
me = bpy.data.objects["head_geo.002"].data
d = np.load(os.path.join(OUT,"head_uvmap.npz"))
pos, mask, nrm = d["pos"], d["mask"], d["nrm"]
# ★ 关键修复：NaN -> 0，并用 mask 显式控制
X = np.nan_to_num(pos[:,:,0], nan=0.0); Y = np.nan_to_num(pos[:,:,1], nan=0.0); Z = np.nan_to_num(pos[:,:,2], nan=0.0)
nY = np.nan_to_num(nrm[:,:,1], nan=0.0)
base = bpy.data.images["RedPandaBase3"]
buf = np.zeros((H*W*4,), np.float32); base.pixels.foreach_get(buf)
img = buf.reshape(H,W,4)[:,:,:3].astype(np.float32)

front = mask & (nY < -0.15)
CREAM = np.array([0.975,0.96,0.93], np.float32)
def disc(cx,cz,rx,rz,feather=0.30):
    dd = np.sqrt(((X-cx)/rx)**2 + ((Z-cz)/rz)**2)
    return np.clip((1.0-dd)/feather, 0.0, 1.0).astype(np.float32)

EX, EZ = 0.175, 0.02
eye_zone = np.maximum(disc(EX,EZ,0.19,0.17), disc(-EX,EZ,0.19,0.17))
w  = np.maximum(disc( EX, EZ+0.115, 0.105, 0.040), disc(-EX, EZ+0.115, 0.105, 0.040))
w  = np.maximum(w, np.clip((1.0-np.abs(X)/0.062),0,1)*np.clip((Z-0.16)/0.05,0,1)*np.clip((0.30-Z)/0.07,0,1))
w  = np.maximum(w, np.maximum(disc( 0.30,-0.085,0.085,0.095), disc(-0.30,-0.085,0.085,0.095)))
w  = np.where(front, w*(1.0-eye_zone), 0.0).astype(np.float32)     # 显式归零，杜绝 NaN
for _ in range(3):
    acc = np.zeros_like(w); cnt = np.zeros_like(w)
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        acc += np.roll(w,(dy,dx),(0,1)); cnt += np.roll((w>0).astype(np.float32),(dy,dx),(0,1))
    w = np.where(cnt>0, w*0.4 + (acc/np.maximum(cnt,1))*0.6, w)
w = np.nan_to_num(w, nan=0.0, posinf=0.0, neginf=0.0)
w = np.where(front, np.clip(w,0,1), 0.0).astype(np.float32)
print("cream texels(>0.5): %d | NaN in w: %d | weight range [%.3f, %.3f]" % (
    int((w>0.5).sum()), int(np.isnan(w).sum()), w.min(), w.max()))
wc = w[:,:,None].astype(np.float32)
out = img*(1.0-wc) + CREAM[None,None,:]*wc
out = np.nan_to_num(out, nan=0.5, posinf=1.0, neginf=0.0)
out = np.clip(out,0,1).astype(np.float32)
im = bpy.data.images.get("RedPandaBase10")
if im is None: im = bpy.data.images.new("RedPandaBase10", width=W, height=H, alpha=False)
im.pixels.foreach_set(np.concatenate([out,np.ones((H,W,1),np.float32)],axis=2).astype(np.float32).reshape(-1))
im.filepath_raw=os.path.join(OUT,"redpanda_base10.png"); im.file_format='PNG'; im.save()
for m in me.materials:
    if not m or not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image and nd.image.name.startswith("RedPandaBase"): nd.image = im
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
