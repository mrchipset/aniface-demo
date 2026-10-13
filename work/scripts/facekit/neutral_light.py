import bpy, os, math
OUT=r"."
sc=bpy.context.scene
w = bpy.data.worlds.get("PolyHaven studio_kontrast_03")
if w is None:
    for cand in bpy.data.worlds:
        if "studio" in cand.name.lower(): w=cand; break
print("worlds:", [x.name for x in bpy.data.worlds], "-> using", w.name if w else None)
if w: sc.world = w
# make faces matte-ish for a flat look
for mn in ("PhotoFace","SkinTone","HairTone"):
    m=bpy.data.materials.get(mn)
    if m and m.use_nodes:
        b=next((n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED"),None)
        if b: b.inputs["Roughness"].default_value = 0.85
cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=520; sc.render.resolution_y=640
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"ict_neutral_f.png"),(0,-0.80,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"ict_neutral_34.png"),(0.52,-0.62,0.04),(math.radians(82),0,math.radians(40))))
