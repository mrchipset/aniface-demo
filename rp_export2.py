import bpy, os
OUT=r"<HOME>\tmp\blender"
# drop the unused FaceUV layer
me = bpy.data.objects["head_geo.002"].data
if me.uv_layers.get("FaceUV"):
    me.uv_layers.remove(me.uv_layers["FaceUV"]); print("removed FaceUV layer")
print("uv layers now:", [l.name for l in me.uv_layers], "| active_render:", me.uv_layers.active_render.name)

PARTS=["head_geo.002","ears_geo","hair_geo","tufts_geo","raccoon_head"]
bpy.ops.object.select_all(action='DESELECT')
for n in PARTS:
    o=bpy.data.objects.get(n)
    if o: o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["head_geo.002"]

p=os.path.join(OUT,"redpanda_head.glb")
if os.path.exists(p): os.remove(p)
base=dict(filepath=p, export_format='GLB', use_selection=True, export_yup=True,
          export_skins=False, export_texcoords=True, export_normals=True, export_morph=True)
for i,kw in enumerate([dict(base, export_morph_normal=False, export_meshopt_compression_enable=True),
                       dict(base, export_morph_normal=False), dict(base)]):
    try:
        bpy.ops.export_scene.gltf(**kw); print("export v%d -> %.2f MB" % (i, os.path.getsize(p)/1048576)); break
    except TypeError as e: print("v%d unsupported: %s" % (i, str(e)[:80]))
