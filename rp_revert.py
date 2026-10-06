import bpy, os, math
OUT=r"<HOME>\tmp\blender"
base = bpy.data.images["RedPandaBase3"]; ear = bpy.data.images["RedPandaEar3"]
for m in bpy.data.materials:
    if not m.use_nodes: continue
    for nd in m.node_tree.nodes:
        if nd.type=='TEX_IMAGE' and nd.image:
            if nd.image.name.startswith("RedPandaBase"): nd.image = base
            elif nd.image.name.startswith("RedPandaEar"): nd.image = ear
print("reverted to RedPandaBase3 / RedPandaEar3 (clean palette version)")
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
print("front:", shot(os.path.join(OUT,"final_f.png"),(cx,cy-D,cz+0.02),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"final_34.png"),(cx+D*0.7,cy-D*0.7,cz+0.10),(math.radians(80),0,math.radians(45))))
