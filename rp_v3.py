import bpy, os, math
OUT=r"."
# --- ears/hair/tufts -> white-edged texture ---
ear = bpy.data.images.get("RedPandaEar")
n=0
if ear:
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        if not m.name.startswith("MAT_Racoon.003"): continue
        for nd in m.node_tree.nodes:
            if nd.type=='TEX_IMAGE' and nd.image and ("Image_0" in nd.image.name or "RedPandaBase" in nd.image.name):
                nd.image = ear; n+=1
        print(" ", m.name, "->", [nd.image.name for nd in m.node_tree.nodes if nd.type=='TEX_IMAGE'])
print("rewired to RedPandaEar:", n)

# --- tighten the face projection (drop photo background) ---
ob = bpy.data.objects["head_geo.002"]; me = ob.data
mw = ob.matrix_world.copy()
co = [mw @ v.co for v in me.vertices]
xs=[p.x for p in co]; zs=[p.z for p in co]
U0,U1 = 0.20, 0.82
V_TOP, V_BOT = 0.86, 0.19
Z0,Z1 = min(zs), max(zs)
uv = me.uv_layers["FaceUV"]
for poly in me.polygons:
    for li in poly.loop_indices:
        p = co[me.loops[li].vertex_index]
        u=(p.x-min(xs))/(max(xs)-min(xs)); t=(p.z-Z0)/(Z1-Z0)
        uv.data[li].uv = (U0+u*(U1-U0), V_BOT+t*(V_TOP-V_BOT))
print("projection u[%.2f,%.2f] v[%.2f,%.2f]" % (U0,U1,V_BOT,V_TOP))

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
