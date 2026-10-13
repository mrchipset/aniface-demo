import bpy
sc = bpy.context.scene
print("=== render-visible objects (hide_render False) ===")
for o in bpy.data.objects:
    if not o.hide_render and o.type == 'MESH':
        c = [o.matrix_world @ __import__("mathutils").Vector(b) for b in o.bound_box]
        cx = [round((min(p[i] for p in c)+max(p[i] for p in c))/2,3) for i in range(3)]
        sz = [round(max(p[i] for p in c)-min(p[i] for p in c),3) for i in range(3)]
        print(f"   {o.name:28s} center={cx} size={sz}")
print()
cam = sc.camera
print("camera:", cam.name if cam else None, "| loc", [round(v,3) for v in cam.location], "| rot(deg)", [round(__import__("math").degrees(v),1) for v in cam.rotation_euler], "| lens", cam.data.lens)
h = bpy.data.objects["ICTFaceModel"]
print("head matrix_world scale:", [round(v,4) for v in h.matrix_world.to_scale()])
print("head visible_get (viewport):", h.visible_get())
print("collections of head:", [c.name for c in h.users_collection])
print("scene engine:", sc.render.engine, "| film_transparent:", sc.render.film_transparent)
print("world:", sc.world.name if sc.world else None)
