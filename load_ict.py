import bpy, os, json, sys, time

FOLDER = r"<HOME>\tmp\blender\ICT-FaceKit\FaceXModel"
t0 = time.time()

with open(os.path.join(FOLDER, "vertex_indices.json")) as f:
    cfg = json.load(f)
exprs = cfg["expressions"]
print("config expressions:", len(exprs))
print(exprs)

def import_obj(path):
    before = {o.name for o in bpy.data.objects}
    bpy.ops.wm.obj_import(filepath=path)
    new = [o for o in bpy.data.objects if o.name not in before]
    if not new:
        raise RuntimeError("import produced no object: " + path)
    return new[0]

# fresh: delete previous ICT import if any
bpy.ops.object.select_all(action='DESELECT')
for o in list(bpy.data.objects):
    if o.name.startswith("ICTFaceModel") or o.name in exprs:
        bpy.data.objects.remove(o, do_unlink=True)

base = import_obj(os.path.join(FOLDER, "generic_neutral_mesh.obj"))
base.name = "ICTFaceModel"
base.data.name = "ICTFaceModelMesh"
print("base verts:", len(base.data.vertices), "polys:", len(base.data.polygons),
      "uv:", [u.name for u in base.data.uv_layers], "mats:", [m.name if m else None for m in base.data.materials])

shape_objs = []
missing = []
for name in exprs:
    p = os.path.join(FOLDER, name + ".obj")
    if not os.path.exists(p):
        missing.append(name); continue
    o = import_obj(p)
    o.name = name
    shape_objs.append(o)

counts = {o.name: len(o.data.vertices) for o in shape_objs}
uniq = set(counts.values())
print("loaded expression objs:", len(shape_objs), "| missing:", missing)
print("distinct vertex counts among expressions:", uniq, "| base:", len(base.data.vertices))

bpy.ops.object.select_all(action='DESELECT')
for o in shape_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.ops.object.join_shapes()
bpy.ops.object.delete()

sk = base.data.shape_keys
print("shape keys:", len(sk.key_blocks) if sk else 0)
if sk:
    print("names:", [k.name for k in sk.key_blocks])
print("elapsed: %.1fs" % (time.time()-t0))
