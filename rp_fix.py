import bpy, os, numpy as np
OUT=r"<HOME>\tmp\blender"

# ---------- 1. 撤掉照片投影：所有 head 面回到 MAT_Racoon.004 ----------
ob = bpy.data.objects["head_geo.002"]; me = ob.data
names=[m.name if m else "" for m in me.materials]
ip = names.index("RPPhoto") if "RPPhoto" in names else None
base_i = names.index("MAT_Racoon.004")
n=0
if ip is not None:
    for p in me.polygons:
        if p.material_index == ip: p.material_index = base_i; n+=1
print("reverted %d polygons from RPPhoto -> MAT_Racoon.004" % n)

# ---------- 2. 重新生成小熊猫配色（更偏红熊猫而非浣熊）----------
src = bpy.data.images["Image_0"]
W,H = src.size
px = np.array(src.pixels[:], dtype=np.float32).reshape(H,W,4)
rgb = px[:,:,:3]
L = rgb[:,:,0]*0.299 + rgb[:,:,1]*0.587 + rgb[:,:,2]*0.114

DARK  = (0.20, 0.09, 0.06)      # 深红棕（代替纯黑眼罩）
RUST  = (0.80, 0.36, 0.11)      # 主体锈橘
WHITE = (0.95, 0.93, 0.90)      # 白脸/白吻/白耳缘
o = np.zeros_like(rgb)
for ch in range(3):
    o[:,:,ch] = np.where(L<0.27, DARK[ch], np.where(L<0.70, RUST[ch], WHITE[ch]))
o = np.clip(o*(0.82+0.36*L)[...,None], 0, 1)     # 保留原有烘焙明暗

im = bpy.data.images.get("RedPandaBase3") or bpy.data.images.new("RedPandaBase3", width=W, height=H, alpha=False)
im.pixels.foreach_set(np.concatenate([o, np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
im.filepath_raw=os.path.join(OUT,"redpanda_base3.png"); im.file_format='PNG'; im.save()
print("base texture:", os.path.getsize(os.path.join(OUT,"redpanda_base3.png")), "bytes")

# 耳机用更白一点的版本
E_DARK=(0.93,0.92,0.89); E_RUST=(0.72,0.30,0.09); E_LIGHT=(0.97,0.96,0.94)
e = np.zeros_like(rgb)
for ch in range(3):
    e[:,:,ch] = np.where(L<0.34, E_DARK[ch], np.where(L<0.72, E_RUST[ch], E_LIGHT[ch]))
e = np.clip(e*(0.82+0.36*L)[...,None], 0, 1)
ie = bpy.data.images.get("RedPandaEar3") or bpy.data.images.new("RedPandaEar3", width=W, height=H, alpha=False)
ie.pixels.foreach_set(np.concatenate([e, np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
ie.filepath_raw=os.path.join(OUT,"redpanda_ear3.png"); ie.file_format='PNG'; ie.save()

for m in bpy.data.materials:
    if not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image:
            if nd.image.name.startswith("RedPandaBase"): nd.image = im
            elif nd.image.name.startswith("RedPandaEar"): nd.image = ie
print("textures ->", [(m.name, [nd.image.name for nd in m.node_tree.nodes if nd.type=='TEX_IMAGE']) for m in bpy.data.materials if m.use_nodes and m.name.startswith("MAT_Racoon")])

# ---------- 3. 渲染 ----------
import math
sc=bpy.context.scene
w=bpy.data.worlds.get("PolyHaven studio_kontrast_03")
if w: sc.world=w
cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=560; sc.render.resolution_y=560
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx,cy,cz=0.0,0.04,0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"rp2_f.png"),(cx,cy-D,cz+0.02),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"rp2_34.png"),(cx+D*0.7,cy-D*0.7,cz+0.10),(math.radians(80),0,math.radians(45))))
