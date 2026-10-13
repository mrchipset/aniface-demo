import bpy, os, numpy as np
OUT=r"."; W=H=512
pos = np.load(os.path.join(OUT,"head_uvpos.npy"))
mask = np.load(os.path.join(OUT,"head_uvmask.npy"))
src = bpy.data.images["Image_0"]
px = np.array(src.pixels[:], np.float32).reshape(H,W,4)[:,:,:3]
L = px[:,:,0]*0.299+px[:,:,1]*0.587+px[:,:,2]*0.114
shade = (0.80+0.40*L)[...,None]

# ---- 1. 平滑位置图（消除 Voronoi 锯齿）----
for _ in range(6):
    acc = np.zeros_like(pos); cnt = np.zeros((H,W),np.float32)
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        acc += np.where(np.roll(mask,(dy,dx),(0,1))[...,None], np.roll(pos,(dy,dx),(0,1)), 0)
        cnt += np.roll(mask,(dy,dx),(0,1))
    ok = mask & (cnt>0)
    pos[ok] = (pos[ok]*1.0 + acc[ok]/cnt[ok][...,None])/2.0
X,Y,Z = pos[:,:,0],pos[:,:,1],pos[:,:,2]

# ---- 2. 保护原贴图的五官（暗部）----
feature = (L < 0.38) & mask
prot = feature.copy()
for _ in range(7):                       # dilate
    p = prot.copy()
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
        p |= np.roll(prot,(dy,dx),(0,1))
    prot = p
prot &= mask
print("protected texels: %d / %d" % (int(prot.sum()), int(mask.sum())))

# ---- 3. 上色 ----
DARK  = np.array([0.22,0.10,0.06],  np.float32)
RUST  = np.array([0.84,0.38,0.11],  np.float32)
CREAM = np.array([0.97,0.955,0.925],np.float32)
front = mask & (Y < -0.02)
out = np.broadcast_to(RUST,(H,W,3)).copy()

EX, EZ = 0.13, 0.05
def ell(cx,cz,rx,rz):
    d = ((X-cx)/rx)**2 + ((Z-cz)/rz)**2
    return d <= 1.0
mark = ( ell(EX,0.185,0.095,0.055) | ell(-EX,0.185,0.095,0.055)      # 眉上白斑
       | ((np.abs(X)<0.05) & (Z>0.13) & (Z<0.31))                    # 额中白纹
       | (ell(0.27,-0.03,0.10,0.10) | ell(-0.27,-0.03,0.10,0.10)) )  # 眼颊白斑
out[front & mark & ~prot] = CREAM
# 眼周保持深色（原贴图暗部）
out[front & ell(EX,EZ,0.135,0.115) & mask] = np.where(feature[front & ell(EX,EZ,0.135,0.115) & mask][:,None], DARK, out[front & ell(EX,EZ,0.135,0.115) & mask])
out[front & ell(-EX,EZ,0.135,0.115) & mask] = np.where(feature[front & ell(-EX,EZ,0.135,0.115) & mask][:,None], DARK, out[front & ell(-EX,EZ,0.135,0.115) & mask])
# 白吻
muz = front & (Z < -0.02) & (np.abs(X) < 0.24) & ~prot
out[muz] = CREAM
out[front & (L<0.10)] = np.array([0.05,0.045,0.045], np.float32)
out = np.clip(out*shade,0,1)

im = bpy.data.images.get("RedPandaBase5") or bpy.data.images.new("RedPandaBase5",width=W,height=H,alpha=False)
im.pixels.foreach_set(np.concatenate([out,np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
im.filepath_raw=os.path.join(OUT,"redpanda_base5.png"); im.file_format='PNG'; im.save()
print("saved redpanda_base5.png")
for m in bpy.data.materials:
    if m.use_nodes:
        for nd in m.node_tree.nodes:
            if nd.type=='TEX_IMAGE' and nd.image and nd.image.name.startswith("RedPandaBase"): nd.image=im
import math
sc=bpy.context.scene; cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=560; sc.render.resolution_y=560
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx,cy,cz=0.0,0.04,0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"rp4_f.png"),(cx,cy-D,cz+0.02),(math.radians(90),0,0)))
