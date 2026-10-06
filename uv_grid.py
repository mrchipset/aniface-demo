import bpy, os, numpy as np
OUT=r"<HOME>\tmp\blender"; W=H=512
yy, xx = np.mgrid[0:H, 0:W]
cell = 32
cx = xx // cell; cy = yy // cell
check = ((cx + cy) % 2).astype(np.float32)
# 用色相编码位置：红随 x 增大、绿随 y 增大，蓝=棋盘
img = np.zeros((H,W,3), np.float32)
img[:,:,0] = 0.15 + 0.85*(xx/W)
img[:,:,1] = 0.15 + 0.85*(yy/H)
img[:,:,2] = 0.25 + 0.5*check
# 网格线
grid = ((xx % cell)==0) | ((yy % cell)==0)
img[grid] = np.array([1.0,1.0,1.0])
gl = ((xx % (cell*4))==0) | ((yy % (cell*4))==0)
img[gl] = np.array([0.0,0.0,0.0])
img = np.clip(img,0,1)
im = bpy.data.images.get("UVGrid") or bpy.data.images.new("UVGrid", width=W, height=H, alpha=False)
im.pixels.foreach_set(np.concatenate([img, np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
im.filepath_raw=os.path.join(OUT,"uv_grid.png"); im.file_format='PNG'; im.save()
print("uv_grid.png saved")

# 临时把 head_geo 的贴图换成网格
me = bpy.data.objects["head_geo.002"].data
saved=[]
for m in me.materials:
    if not m or not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image:
            saved.append((m.name, nd.image.name)); nd.image = im
print("swapped:", saved)

import math
sc=bpy.context.scene
w=bpy.data.worlds.get("PolyHaven studio_kontrast_03")
if w: sc.world=w
cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=620; sc.render.resolution_y=620
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx0,cy0,cz0=0.0,0.04,0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"uvgrid_f.png"),(cx0,cy0-D,cz0+0.02),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"uvgrid_34.png"),(cx0+D*0.7,cy0-D*0.7,cz0+0.10),(math.radians(80),0,math.radians(45))))
