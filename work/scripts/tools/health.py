import bpy, os, math

def _assets():
    """定位仓库根下的 work/assets，从任何目录运行都能找到。"""
    cands = []
    if "__file__" in globals():
        cands.append(os.path.dirname(os.path.abspath(__file__)))
    cands.append(os.getcwd())
    for c in cands:
        p = os.path.abspath(c)
        while True:
            if os.path.isdir(os.path.join(p, "work", "assets")):
                return os.path.join(p, "work", "assets")
            q = os.path.dirname(p)
            if q == p:
                break
            p = q
    raise RuntimeError("找不到 work/assets，请从仓库目录内运行本脚本")

OUT = _assets()
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
