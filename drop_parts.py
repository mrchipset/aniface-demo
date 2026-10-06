import bpy, os
OUT=r"<HOME>\tmp\blender"
ob = bpy.data.objects["AnifaceHead"]; me = ob.data
print("before verts=%d polys=%d" % (len(me.vertices), len(me.polygons)))
DROP=("M_GumsTongue","M_Teeth","M_ScleraLeft","M_IrisLeft","M_ScleraRight","M_IrisRight",
      "M_LacrimalFluid","M_EyeBlend","M_EyeOcclusion","M_EyeLashes")
def is_drop(n): return any(n==d or n.startswith(d+".") for d in DROP)
targets={i for i,m in enumerate(me.materials) if m and is_drop(m.name)}
print("target slots:", sorted(targets))

bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True); bpy.context.view_layer.objects.active=ob
bpy.context.tool_settings.mesh_select_mode=(False,False,True)   # FACE mode
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='DESELECT')                       # <-- the fix
bpy.ops.object.mode_set(mode='OBJECT')

for p in me.polygons:
    if p.material_index in targets:
        p.select=True
        for vi in p.vertices: me.vertices[vi].select=True
sel = sum(1 for p in me.polygons if p.select)
print("faces flagged:", sel, "of", len(me.polygons))

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.delete(type='FACE')
bpy.ops.object.mode_set(mode='OBJECT')
me.update(); bpy.context.view_layer.update()
nv, np_ = len(me.vertices), len(me.polygons)
print("after  verts=%d polys=%d  shapekeys=%d" % (nv, np_, len(me.shape_keys.key_blocks)))
if nv == 0 or np_ == 0:
    print("!!! EMPTY - aborting export (rerun pipeline.py)"); raise SystemExit
