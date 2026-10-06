import bpy, math, os, mathutils

h = bpy.data.objects["ICTFaceModel"]
me = h.data
me.update()                          # <-- the fix: invalidate the mesh
bpy.context.view_layer.update()      # refresh bound_box / depsgraph

c = [h.matrix_world @ mathutils.Vector(b) for b in h.bound_box]
print("bound_box center:", [round((min(p[i] for p in c)+max(p[i] for p in c))/2,4) for i in range(3)])
print("bound_box size  :", [round(max(p[i] for p in c)-min(p[i] for p in c),4) for i in range(3)])

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
print("front(-Y):", shot(r"<HOME>\tmp\blender\ict_f.png", (0.0,-D,0.01), (math.radians(90),0,0)))
print("back(+Y) :", shot(r"<HOME>\tmp\blender\ict_b.png", (0.0, D,0.01), (math.radians(90),0,math.radians(180))))
