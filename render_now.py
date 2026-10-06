import bpy, os, math
OUT=r"<HOME>\tmp\blender"
sc=bpy.context.scene; cam=sc.camera
cam.data.lens=55
sc.render.resolution_x=520; sc.render.resolution_y=640
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"ict_now_f.png"),(0,-0.80,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"ict_now_34.png"),(0.52,-0.62,0.04),(math.radians(82),0,math.radians(40))))
