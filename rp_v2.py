import bpy, os, math, numpy as np
OUT=r"<HOME>\tmp\blender"

# ---------- 1. 收紧脸部投影 ----------
ob = bpy.data.objects["head_geo.002"]; me = ob.data
mw = ob.matrix_world.copy()
co = [mw @ v.co for v in me.vertices]
xs=[p.x for p in co]; zs=[p.z for p in co]
U0,U1 = 0.17, 0.85
V_TOP, V_BOT = 0.83, 0.11
Z0, Z1 = min(zs), max(zs)
uv = me.uv_layers["FaceUV"]
for poly in me.polygons:
    for li in poly.loop_indices:
        p = co[me.loops[li].vertex_index]
        u = (p.x - min(xs))/(max(xs)-min(xs))
        t = (p.z - Z0)/(Z1 - Z0)
        uv.data[li].uv = (U0 + u*(U1-U0), V_BOT + t*(V_TOP-V_BOT))
print("projection: u[%.2f,%.2f] v[%.2f,%.2f]" % (U0,U1,V_BOT,V_TOP))

# ---------- 2. 耳朵/毛簇贴图：深色改成奶白边缘 ----------
src = bpy.data.images["Image_0"]
W,H = src.size
px = np.array(src.pixels[:], dtype=np.float32).reshape(H,W,4)
rgb = px[:,:,:3]
L = rgb[:,:,0]*0.299 + rgb[:,:,1]*0.587 + rgb[:,:,2]*0.114
mx = rgb.max(axis=2); mn = rgb.min(axis=2); sat = mx-mn
CREAM=(0.95,0.94,0.91); RUST=(0.62,0.24,0.07); ORNG=(0.86,0.42,0.12)
o = np.zeros_like(rgb)
for ch,(a,b,c) in enumerate(zip(CREAM,RUST,ORNG)):
    o[:,:,ch] = np.where(L<0.34, a, np.where(L<0.72, b, c))
grey = sat < 0.12
o = np.where(grey[...,None], o, rgb)
o = np.clip(o*(0.80+0.40*L)[...,None], 0, 1)
ear = bpy.data.images.get("RedPandaEar")
if ear is None:
    ear = bpy.data.images.new("RedPandaEar", width=W, height=H, alpha=False)
ear.pixels.foreach_set(np.concatenate([o, np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
ear.filepath_raw = os.path.join(OUT,"redpanda_ear.png"); ear.file_format='PNG'; ear.save()
n=0
for m in bpy.data.materials:
    if m.use_nodes and m.name.startswith("MAT_Racoon.003"):
        for nd in m.node_tree.nodes:
            if nd.type=='TEX_IMAGE' and nd.image and nd.image.name.startswith("Image_0"):
                nd.image = ear; n+=1
print("ear material rewired:", n, "nodes")

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
print("front:", shot(os.path.join(OUT,"rp_f.png"),(cx,cy-D,cz+0.02),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"rp_34.png"),(cx+D*0.7,cy-D*0.7,cz+0.10),(math.radians(80),0,math.radians(45))))
