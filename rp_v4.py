import bpy, os, numpy as np
OUT=r"<HOME>\tmp\blender"
src = bpy.data.images["Image_0"]
W,H = src.size
px = np.array(src.pixels[:], dtype=np.float32).reshape(H,W,4)
rgb = px[:,:,:3]
L = rgb[:,:,0]*0.299 + rgb[:,:,1]*0.587 + rgb[:,:,2]*0.114

def build(palette, name):
    dark, mid, light = palette
    o = np.zeros_like(rgb)
    for ch in range(3):
        o[:,:,ch] = np.where(L<0.30, dark[ch], np.where(L<0.74, mid[ch], light[ch]))
    o = np.clip(o*(0.80+0.42*L)[...,None], 0, 1)     # keep baked shading
    im = bpy.data.images.get(name)
    if im is None: im = bpy.data.images.new(name, width=W, height=H, alpha=False)
    im.pixels.foreach_set(np.concatenate([o, np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
    im.filepath_raw = os.path.join(OUT, name + ".png"); im.file_format='PNG'; im.save()
    print("built", name, "->", os.path.getsize(os.path.join(OUT,name+".png")), "bytes")
    return im

# head fur: dark eye/nose patches, rust-orange, cream white
base = build([(0.07,0.06,0.06), (0.72,0.30,0.09), (0.93,0.91,0.87)], "RedPandaBase2")
# ears / tufts: cream edge, rust, light cream
ear  = build([(0.93,0.92,0.89), (0.66,0.26,0.08), (0.96,0.95,0.92)], "RedPandaEar2")

for m in bpy.data.materials:
    if not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image:
            nm = nd.image.name
            if nm.startswith("RedPandaBase"): nd.image = base
            elif nm.startswith("RedPandaEar"): nd.image = ear
print("materials -> textures:")
for m in bpy.data.materials:
    if m.use_nodes and m.name.startswith("MAT_Racoon"):
        print("  ", m.name, [nd.image.name for nd in m.node_tree.nodes if nd.type=='TEX_IMAGE'])

import math
sc=bpy.context.scene; cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=560; sc.render.resolution_y=560
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx,cy,cz=0.0,0.04,0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"rp_f.png"),(cx,cy-D,cz+0.02),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"rp_34.png"),(cx+D*0.7,cy-D*0.7,cz+0.10),(math.radians(80),0,math.radians(45))))
