import bpy, math, os, mathutils

h = bpy.data.objects["ICTFaceModel"]
me = h.data
dg = bpy.context.evaluated_depsgraph_get()

def eval_bbox():
    bpy.context.view_layer.update()
    ev = h.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mw = h.matrix_world
    c = [mw @ mathutils.Vector(b) for b in ev.bound_box]
    lo = [min(p[i] for p in c) for i in range(3)]
    hi = [max(p[i] for p in c) for i in range(3)]
    return lo, hi

lo, hi = eval_bbox()
size = [hi[i]-lo[i] for i in range(3)]
print("BEFORE eval size:", [round(v,3) for v in size])

TARGET_H = 0.26
s = TARGET_H / size[2]
ctr = [ (lo[i]+hi[i])/2 * s for i in range(3) ]
print("scale factor:", s)

sk = me.shape_keys
print("shape keys:", len(sk.key_blocks) if sk else 0)
blocks = list(sk.key_blocks) if sk else []
targets = blocks if blocks else [None]
for kb in (blocks if blocks else []):
    data = kb.data
    for pt in data:
        pt.co = pt.co * s - mathutils.Vector(ctr)
# also base verts (harmless if overridden)
for v in me.vertices:
    v.co = v.co * s - mathutils.Vector(ctr)
me.update()
bpy.context.view_layer.update()
h.location = (0.0, 0.0, 0.0)

lo, hi = eval_bbox()
size = [hi[i]-lo[i] for i in range(3)]
print("AFTER  eval size:", [round(v,4) for v in size], " center:", [round((lo[i]+hi[i])/2,4) for i in range(3)])

sc = bpy.context.scene
cam = sc.camera
cam.data.lens = 55
sc.render.resolution_x = 480; sc.render.resolution_y = 600
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(path, loc, rot):
    cam.location = loc; cam.rotation_euler = rot
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return os.path.getsize(path) if os.path.exists(path) else 0
D = 0.85
print("front(-Y):", shot(r"ict_f.png", (0,-D,0.01), (math.radians(90),0,0)))
print("back(+Y) :", shot(r"ict_b.png", (0, D,0.01), (math.radians(90),0,math.radians(180))))
