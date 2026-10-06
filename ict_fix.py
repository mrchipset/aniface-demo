import bpy, math, os

obj = bpy.data.objects["ICTFaceModel"]
# unhide every collection, then hide objects except the head
for col in bpy.data.collections:
    col.hide_viewport = False; col.hide_render = False
bpy.context.scene.collection.hide_viewport = False
for o in bpy.data.objects:
    o.hide_viewport = o.hide_render = (o.name != "ICTFaceModel")
obj.hide_viewport = obj.hide_render = False
obj.hide_set(False)

me = obj.data
co = [v.co.copy() for v in me.vertices]
xs=[p.x for p in co]; ys=[p.y for p in co]; zs=[p.z for p in co]
print("bbox min:", [round(min(a),4) for a in (xs,ys,zs)])
print("bbox max:", [round(max(a),4) for a in (xs,ys,zs)])
print("size  X=%.4f Y=%.4f Z=%.4f" % (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)))

sc = bpy.context.scene
cam = bpy.data.objects.get("HeadCam")
if cam is None:
    cd = bpy.data.cameras.new("HeadCam"); cam = bpy.data.objects.new("HeadCam", cd)
    sc.collection.objects.link(cam)
cam.data.lens = 50
sc.camera = cam

def render_to(path, loc, rot):
    cam.location = loc; cam.rotation_euler = rot
    sc.render.filepath = path
    sc.render.resolution_x = 480; sc.render.resolution_y = 600
    sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
    bpy.ops.render.render(write_still=True)
    return os.path.exists(path)

D = 0.9
r1 = render_to(r"<HOME>\tmp\blender\ict_f.png", (0.0,-D,0.02), (math.radians(90),0,0))
r2 = render_to(r"<HOME>\tmp\blender\ict_s.png", (D,0.0,0.02), (math.radians(90),0,math.radians(90)))
print("rendered front:", r1, " side:", r2)
