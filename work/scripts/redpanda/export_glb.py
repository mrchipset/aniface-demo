import bpy, os
OUT = r"."
ob = bpy.data.objects["ICTFaceModel"]
ob.name = "AnifaceHead"
me = ob.data
sk = me.shape_keys
print("before:", len(sk.key_blocks), "keys")

def find(n):
    for k in sk.key_blocks:
        if k.name == n: return k
    return None

def merge(name, a, b):
    ka, kb = find(a), find(b)
    if not (ka and kb):
        print("  merge skip (missing):", a, b); return
    basis = find("Basis")
    n = len(ka.data)
    new = ob.shape_key_add(name=name, from_mix=False)
    for i in range(n):
        new.data[i].co = ka.data[i].co + kb.data[i].co - basis.data[i].co
    ob.shape_key_remove(ka); ob.shape_key_remove(kb)
    print("  merged %s + %s -> %s" % (a, b, name))

merge("browInnerUp", "browInnerUp_L", "browInnerUp_R")
merge("cheekPuff",  "cheekPuff_L",  "cheekPuff_R")

renames = {}
for k in list(sk.key_blocks):
    n = k.name
    if n.endswith("_L"): renames[n] = n[:-2] + "Left"
    elif n.endswith("_R"): renames[n] = n[:-2] + "Right"
for old, new in renames.items():
    kb = find(old)
    if kb: kb.name = new
print("renamed %d keys" % len(renames))

ARKSET = set("""eyeBlinkLeft eyeBlinkRight eyeSquintLeft eyeSquintRight eyeWideLeft eyeWideRight
eyeLookDownLeft eyeLookDownRight eyeLookInLeft eyeLookInRight eyeLookOutLeft eyeLookOutRight
eyeLookUpLeft eyeLookUpRight browDownLeft browDownRight browInnerUp browOuterUpLeft browOuterUpRight
cheekPuff cheekSquintLeft cheekSquintRight noseSneerLeft noseSneerRight mouthClose mouthFunnel
mouthPucker mouthLeft mouthRight mouthSmileLeft mouthSmileRight mouthFrownLeft mouthFrownRight
mouthDimpleLeft mouthDimpleRight mouthStretchLeft mouthStretchRight mouthRollLower mouthRollUpper
mouthShrugLower mouthShrugUpper mouthPressLeft mouthPressRight mouthLowerDownLeft mouthLowerDownRight
mouthUpperUpLeft mouthUpperUpRight jawOpen jawForward jawLeft jawRight tongueOut""".split())
final = [k.name for k in sk.key_blocks]
body = [n for n in final if n != "Basis"]
print("final keys: %d (Basis + %d)" % (len(final), len(body)))
print("ARKit-matched: %d / 52" % len([n for n in body if n in ARKSET]))
print("missing vs aniface list:", sorted(ARKSET - set(body)))
print("extra (not in aniface list):", sorted(set(body) - ARKSET))

# export
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True); bpy.context.view_layer.objects.active = ob
p = os.path.join(OUT, "aniface_head.glb")
kw = dict(filepath=p, export_format='GLB', use_selection=True,
          export_morph=True, export_morph_normal=True,
          export_draco_mesh_compression_enable=False, export_yup=True,
          export_skins=False, export_texcoords=True, export_normals=True)
try:
    bpy.ops.export_scene.gltf(**kw)
except TypeError as e:
    print("retry with fewer args:", e)
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', use_selection=True, export_morph=True)
print("exported:", os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else 0, "bytes")
