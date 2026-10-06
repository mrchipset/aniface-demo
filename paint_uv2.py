import bpy, os, numpy as np, math
OUT=r"<HOME>\tmp\blender"; W=H=512
me = bpy.data.objects["head_geo.002"].data
base = bpy.data.images["RedPandaBase3"]

src_px = np.zeros((H*W*4,), dtype=np.float32)
base.pixels.foreach_get(src_px)
img = src_px.reshape(H,W,4)[:,:,:3].astype(np.float32)
print("base image loaded:", img.shape, img.dtype)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
CREAM = np.array([0.97,0.955,0.925], dtype=np.float32)

def blob(cx, cy, rx, ry, feather=6.0):
    d = np.sqrt(((xx-cx)/rx)**2 + ((yy-cy)/ry)**2).astype(np.float32)
    w = np.clip((1.0-d)*float(rx)/feather, 0.0, 1.0)
    return w.astype(np.float32)

w = np.maximum(blob(11,412,16,9), blob(30,400,15,9))
w = np.maximum(w, blob(21,452,13,26,5.0))
wc = w[:,:,None].astype(np.float32)
print("paint weights: max=%.2f sum=%.0f" % (wc.max(), wc.sum()))

out = (img*(1.0-wc) + CREAM[None,None,:]*wc).astype(np.float32)
alpha = np.ones((H,W,1), dtype=np.float32)
buf = np.concatenate([np.clip(out,0,1), alpha], axis=2).astype(np.float32).reshape(-1)
print("buffer:", buf.shape, buf.dtype)

im = bpy.data.images.get("RedPandaBase6")
if im is None:
    im = bpy.data.images.new("RedPandaBase6", width=W, height=H, alpha=False)
im.pixels.foreach_set(buf)
im.filepath_raw = os.path.join(OUT,"redpanda_base6.png"); im.file_format='PNG'; im.save()
print("saved redpanda_base6.png", os.path.getsize(os.path.join(OUT,"redpanda_base6.png")))

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
