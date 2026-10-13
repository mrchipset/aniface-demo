import bpy, os, numpy as np, math
OUT=r"."; W=H=512
me = bpy.data.objects["head_geo.002"].data
d = np.load(os.path.join(OUT,"head_uvmap.npz"))
pos, mask, nrm = d["pos"], d["mask"], d["nrm"]
X,Y,Z = pos[:,:,0], pos[:,:,1], pos[:,:,2]

base = bpy.data.images["RedPandaBase3"]
buf = np.zeros((H*W*4,), np.float32); base.pixels.foreach_get(buf)
img = buf.reshape(H,W,4)[:,:,:3].astype(np.float32)

front = mask & (nrm[:,:,1] < -0.15)
CREAM = np.array([0.97,0.955,0.925], np.float32)
DARKRUST = np.array([0.26,0.11,0.06], np.float32)

def disc(cx, cz, rx, rz, feather=0.35):
    dd = np.sqrt(((X-cx)/rx)**2 + ((Z-cz)/rz)**2)
    return np.clip((1.0-dd)/feather, 0.0, 1.0).astype(np.float32)

EX, EZ = 0.175, 0.02
w_brow = np.maximum(disc( EX, EZ+0.105, 0.115, 0.075), disc(-EX, EZ+0.105, 0.115, 0.075))
w_fore = np.clip((1.0 - np.abs(X)/0.075), 0, 1) * np.clip((Z-0.12)/0.05, 0, 1) * np.clip((0.32-Z)/0.06, 0, 1)
w_cheek = np.maximum(disc( 0.30, -0.06, 0.10, 0.11), disc(-0.30, -0.06, 0.10, 0.11))
w_cream = np.clip(w_brow + w_fore + w_cheek, 0, 1) * front
w_eye   = np.maximum(disc( EX, EZ, 0.155, 0.135), disc(-EX, EZ, 0.155, 0.135)) * front

wc = w_cream[:,:,None].astype(np.float32)
we = w_eye[:,:,None].astype(np.float32)
out = img*(1-wc) + CREAM[None,None,:]*wc
out = out*(1-we) + DARKRUST[None,None,:]*we
out = np.clip(out, 0, 1).astype(np.float32)

print("painted: cream texels=%d  eye texels=%d  front=%d" % (
    int((w_cream>0.5).sum()), int((w_eye>0.5).sum()), int(front.sum())))
im = bpy.data.images.get("RedPandaBase7")
if im is None: im = bpy.data.images.new("RedPandaBase7", width=W, height=H, alpha=False)
flat = np.concatenate([out, np.ones((H,W,1),np.float32)], axis=2).astype(np.float32).reshape(-1)
im.pixels.foreach_set(flat)
im.filepath_raw=os.path.join(OUT,"redpanda_base7.png"); im.file_format='PNG'; im.save()
print("saved redpanda_base7.png")
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
