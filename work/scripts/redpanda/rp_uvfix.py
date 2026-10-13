import bpy, os, math
OUT=r"."
for name in ("head_geo.002","ears_geo","hair_geo","tufts_geo"):
    ob = bpy.data.objects.get(name)
    if not ob: continue
    me = ob.data
    print(name, "uv layers:", [l.name for l in me.uv_layers], "| active_render =", me.uv_layers.active_render.name if me.uv_layers else None)
    base = me.uv_layers.get("UVMap")
    if base:
        base.active = True
        base.active_render = True
    print("   -> set active_render to", me.uv_layers.active_render.name)

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
