import bpy, os, numpy as np, math
OUT=r"<HOME>\tmp\blender"; W=H=512
# 1) 还原贴图
me = bpy.data.objects["head_geo.002"].data
base = bpy.data.images["RedPandaBase3"]
for m in me.materials:
    if not m or not use_nodes if False else (m and m.use_nodes):
        pass
for m in me.materials:
    if not m or not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image and (nd.image.name=="UVGrid" or nd.image.name=="RedPandaBase3"):
            nd.image = base
print("restored RedPandaBase3")

# 2) 在 UV 上绘制（脸岛：x 0~100, vrow 355~500；瞳孔 ≈ (12,382) 与 (26,368)）
img = np.array(base.pixels[:], np.float32).reshape(H,W,4)[:,:,:3].copy()
yy, xx = np.mgrid[0:H, 0:W]
CREAM = np.array([0.97,0.955,0.925], np.float32)
RUST  = np.array([0.84,0.38,0.11], np.float32)

def blob(cx, cy, rx, ry, feather=6.0):
    d = np.sqrt(((xx-cx)/rx)**2 + ((yy-cy)/ry)**2)
    return np.clip((1.0-d)*rx/feather, 0, 1)      # 0..1 权重

w_brow  = np.maximum(blob(11, 412, 16, 9), blob(30, 400, 15, 9))      # 眉上白斑（两个瞳孔各自的上方）
w_fore  = blob(21, 452, 13, 26, 5.0)                                   # 额中白纹
w_comb  = np.clip(w_brow*0.95 + w_fore*0.95, 0, 1)[...,None]

out = img*(1-w_comb) + CREAM*w_comb
out = np.clip(out, 0, 1)
im = bpy.data.images.get("RedPandaBase6") or bpy.data.images.new("RedPandaBase6", width=W, height=H, alpha=False)
im.pixels.foreach_set(np.concatenate([out, np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
im.filepath_raw=os.path.join(OUT,"redpanda_base6.png"); im.file_format='PNG'; im.save()
print("painted redpanda_base6.png  (眉斑@(11,412)/(30,400)  额纹@(21,452))")
for m in me.materials:
    if not m or not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image and nd.image.name.startswith("RedPandaBase"):
            nd.image = im
sc=bpy.context.scene; cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=620; sc.render.resolution_y=620
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx0,cy0,cz0=0.0,0.04,0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"paint_f.png"),(cx0,cy0-D,cz0+0.02),(math.radians(90),0,0)))
