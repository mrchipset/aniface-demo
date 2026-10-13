import bpy, os, math
OUT=r"."
fix = bpy.data.images.get("Image_1.001") or bpy.data.images.get("Image_1")
m = bpy.data.materials["MAT_Racoon.004"]
for nd in m.node_tree.nodes:
    if nd.type=='TEX_IMAGE' and nd.name == "Image Texture.001":
        print("  修正前:", nd.image.name, "-> 修正为:", fix.name)
        nd.image = fix
print("=== 修正后 ===")
for mm in bpy.data.materials:
    if mm and mm.use_nodes and mm.name.startswith("MAT_Racoon"):
        print("  %-18s %s" % (mm.name, [nd.image.name for nd in mm.node_tree.nodes if nd.type=='TEX_IMAGE']))

sc=bpy.context.scene
w=bpy.data.worlds.get("PolyHaven studio_kontrast_03")
if w: sc.world=w
cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=620; sc.render.resolution_y=620
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx,cy,cz=0.0,0.04,0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"final_f.png"),(cx,cy-D,cz+0.02),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"final_34.png"),(cx+D*0.7,cy-D*0.7,cz+0.10),(math.radians(80),0,math.radians(45))))

PARTS=["head_geo.002","ears_geo","hair_geo","tufts_geo","raccoon_head"]
bpy.ops.object.select_all(action='DESELECT')
for n in PARTS:
    o=bpy.data.objects.get(n)
    if o: o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects["head_geo.002"]
p=os.path.join(OUT,"redpanda_head.glb")
if os.path.exists(p): os.remove(p)
bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', use_selection=True, export_yup=True,
    export_skins=False, export_texcoords=True, export_normals=True, export_morph=True,
    export_morph_normal=False, export_meshopt_compression_enable=True)
print("export -> %.2f MB" % (os.path.getsize(p)/1048576))
