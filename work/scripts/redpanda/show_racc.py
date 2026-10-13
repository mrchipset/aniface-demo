import bpy
RACC = {"head_geo.002","ears_geo","hair_geo","tufts_geo"}
for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY'}:
        o.hide_viewport = o.hide_render = (o.name not in RACC)
for col in bpy.data.collections:
    col.hide_viewport = col.hide_render = False
print("visible:", [o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_viewport])
