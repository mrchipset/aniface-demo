import bpy, os
OUT = r"<HOME>\tmp\blender"
ob = bpy.data.objects["AnifaceHead"]; me = ob.data
print("before: verts=%d polys=%d" % (len(me.vertices), len(me.polygons)))

DROP = ("M_GumsTongue","M_Teeth","M_ScleraLeft","M_IrisLeft","M_ScleraRight","M_IrisRight",
        "M_LacrimalFluid","M_EyeBlend","M_EyeOcclusion","M_EyeLashes")
def is_drop(n): return any(n==d or n.startswith(d+".") for d in DROP)
targets = {i for i,m in enumerate(me.materials) if m and is_drop(m.name)}
print("dropping slots:", sorted(targets))

bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons: p.select = (p.material_index in targets)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.delete(type='FACE')
bpy.ops.object.mode_set(mode='OBJECT')
me.update(); bpy.context.view_layer.update()
print("after : verts=%d polys=%d  shapekeys=%d" % (len(me.vertices), len(me.polygons), len(me.shape_keys.key_blocks)))

p = os.path.join(OUT, "aniface_head.glb")
if os.path.exists(p): os.remove(p)
base = dict(filepath=p, export_format='GLB', use_selection=True, export_yup=True,
            export_skins=False, export_texcoords=True, export_normals=True)
variants = [
    dict(base, export_morph=True, export_morph_normal=False, export_meshopt_compression_enable=True),
    dict(base, export_morph=True, export_morph_normal=False),
    dict(base, export_morph=True),
]
for i,kw in enumerate(variants):
    try:
        bpy.ops.export_scene.gltf(**kw)
        print("variant %d OK -> %.1f MB" % (i, os.path.getsize(p)/1048576))
        break
    except TypeError as e:
        print("variant %d unsupported: %s" % (i, str(e)[:120]))
