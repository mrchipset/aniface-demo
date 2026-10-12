import bpy, os, numpy as np
OUT=r"."
src = bpy.data.images["Image_0"]
W,H = src.size
px = np.array(src.pixels[:], dtype=np.float32).reshape(H, W, 4)
rgb = px[:,:,:3]
L = rgb[:,:,0]*0.299 + rgb[:,:,1]*0.587 + rgb[:,:,2]*0.114
mx = rgb.max(axis=2); mn = rgb.min(axis=2)
sat = mx - mn

# red panda palette
DARK  = (0.075, 0.065, 0.070)
RUST  = (0.42, 0.16, 0.06)
ORNG  = (0.80, 0.34, 0.09)
ORNG2 = (0.90, 0.50, 0.18)
WHITE = (0.94, 0.93, 0.90)

out = np.zeros_like(rgb)
# default: grey-scale regions (low saturation) -> palette remap
grey = sat < 0.12
out[...,0] = np.where(L<0.30, DARK[0], np.where(L<0.46, RUST[0], np.where(L<0.80, ORNG[0], WHITE[0])))
out[...,1] = np.where(L<0.30, DARK[1], np.where(L<0.46, RUST[1], np.where(L<0.80, ORNG[1], WHITE[1])))
out[...,2] = np.where(L<0.30, DARK[2], np.where(L<0.46, RUST[2], np.where(L<0.80, ORNG[2], WHITE[2])))
# keep already-saturated pixels (unused clothing islands) as-is
out = np.where(grey[...,None], out, rgb)
# slight shading preservation: multiply by (0.75 + 0.5*L) to keep baked depth
shade = (0.78 + 0.42*L)[...,None]
out = np.clip(out*shade, 0, 1)

new = bpy.data.images.new("RedPandaBase", width=W, height=H, alpha=False)
buf = np.concatenate([out, np.ones((H,W,1),dtype=np.float32)], axis=2).reshape(-1)
new.pixels.foreach_set(buf)
new.filepath_raw = os.path.join(OUT,"redpanda_base.png"); new.file_format='PNG'
new.save()
print("new base texture saved:", os.path.getsize(os.path.join(OUT,"redpanda_base.png")), "bytes")

# rewire materials
n=0
for m in bpy.data.materials:
    if not m.use_nodes: continue
    if not (m.name.startswith("MAT_Racoon")): continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image and nd.image.name.startswith("Image_0"):
            nd.image = new; n+=1
print("rewired %d texture nodes to RedPandaBase" % n)
