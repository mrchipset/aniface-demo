import bpy, os, math
OUT=r"<HOME>\tmp\blender"
ob = bpy.data.objects.get("ICTFaceModel")
print("object:", ob)
if ob is None:
    print("MISSING"); raise SystemExit
try:
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT'); print("forced OBJECT mode")
except Exception as e:
    print("mode fix:", e)
me = ob.data
sk = me.shape_keys
print("verts=%d polys=%d shape_keys=%s mats=%d" % (len(me.vertices), len(me.polygons), len(sk.key_blocks) if sk else 0, len(me.materials)))
print("slots:", [m.name if m else None for m in me.materials])
from collections import Counter
cnt = Counter(p.material_index for p in me.polygons)
names = {i:(m.name if m else None) for i,m in enumerate(me.materials)}
print("poly material distribution:")
for i,c in sorted(cnt.items()):
    print("   %-22s %5d" % (names.get(i), c))
print("scene world:", bpy.context.scene.world.name if bpy.context.scene.world else None)
print("camera:", bpy.context.scene.camera.name if bpy.context.scene.camera else None)
