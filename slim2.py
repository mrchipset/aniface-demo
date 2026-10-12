import bpy, os, math
OUT=r"."
ob=bpy.data.objects["AnifaceHead"]
sc=bpy.context.scene; cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=520; sc.render.resolution_y=640
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"slim_f.png"),(0,-0.80,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"slim_34.png"),(0.52,-0.62,0.04),(math.radians(82),0,math.radians(40))))

p=os.path.join(OUT,"aniface_head.glb")
if os.path.exists(p): os.remove(p)
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active=ob
base=dict(filepath=p, export_format='GLB', use_selection=True, export_yup=True,
          export_skins=False, export_texcoords=True, export_normals=True, export_morph=True)
for i,kw in enumerate([dict(base, export_morph_normal=False, export_meshopt_compression_enable=True),
                       dict(base, export_morph_normal=False), dict(base)]):
    try:
        bpy.ops.export_scene.gltf(**kw)
        print("export v%d -> %.2f MB" % (i, os.path.getsize(p)/1048576)); break
    except TypeError as e: print("v%d unsupported: %s" % (i, str(e)[:90]))
