import bpy, os, numpy as np
OUT=r"<HOME>\tmp\blender"
W=H=512
pos = np.load(os.path.join(OUT,"head_uvpos.npy"))
mask = np.load(os.path.join(OUT,"head_uvmask.npy"))
src = bpy.data.images["Image_0"]
px = np.array(src.pixels[:], np.float32).reshape(H,W,4)[:,:,:3]
L = px[:,:,0]*0.299+px[:,:,1]*0.587+px[:,:,2]*0.114
shade = (0.80 + 0.40*L)[...,None]

DARK   = np.array([0.19,0.085,0.055], np.float32)
RUST   = np.array([0.82,0.37,0.11],  np.float32)
CREAM  = np.array([0.96,0.945,0.915],np.float32)

X = pos[:,:,0]; Y = pos[:,:,1]; Z = pos[:,:,2]
front = np.where(mask, Y < -0.02, False)          # 只画正面
out = np.broadcast_to(RUST, (H,W,3)).copy()
out[front] = RUST
EX, EZ = 0.13, 0.05                                # 眼睛中心 (world x,z)

def ell(cx, cz, rx, rz, feather=0.02):
    if rx<=0 or rz<=0: return np.zeros((H,W), bool)
    d = ((X-cx)/rx)**2 + ((Z-cz)/rz)**2
    return d <= 1.0

eye_patch = ell(EX,EZ,0.125,0.105) | ell(-EX,EZ,0.125,0.105)
brow      = ell(EX,0.165,0.105,0.048) | ell(-EX,0.165,0.105,0.048)
bridge    = (np.abs(X) < 0.055) & (Z > 0.10) & (Z < 0.33)
muzzle    = (Z < -0.015) & (np.abs(X) < 0.26)
cheek     = ell(0.255,-0.02,0.115,0.115) | ell(-0.255,-0.02,0.115,0.115)

sel = front
out[sel & eye_patch] = DARK
out[sel & (brow | bridge | muzzle | cheek)] = CREAM
# 保留原贴图里极暗的部分（瞳孔、鼻头）
out[(L<0.10) & mask] = np.array([0.04,0.035,0.035], np.float32)
out = np.clip(out*shade, 0, 1)

im = bpy.data.images.get("RedPandaBase4") or bpy.data.images.new("RedPandaBase4", width=W, height=H, alpha=False)
im.pixels.foreach_set(np.concatenate([out, np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
im.filepath_raw=os.path.join(OUT,"redpanda_base4.png"); im.file_format='PNG'; im.save()
print("saved redpanda_base4.png")
print("painted texels: eye=%d brow=%d bridge=%d muzzle=%d cheek=%d (front=%d)" % (
  int((front&eye_patch).sum()),int((front&brow).sum()),int((front&bridge).sum()),
  int((front&muzzle).sum()),int((front&cheek).sum()), int(front.sum())))

for m in bpy.data.materials:
    if not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image and nd.image.name.startswith("RedPandaBase"):
            nd.image = im
import math
sc=bpy.context.scene; cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=560; sc.render.resolution_y=560
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx,cy,cz=0.0,0.04,0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"rp3_f.png"),(cx,cy-D,cz+0.02),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"rp3_34.png"),(cx+D*0.7,cy-D*0.7,cz+0.10),(math.radians(80),0,math.radians(45))))
