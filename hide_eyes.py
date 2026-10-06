import bpy, os, math
OUT=r"<HOME>\tmp\blender"
me = bpy.data.objects["ICTFaceModel"].data
HIDE = ("M_ScleraLeft","M_IrisLeft","M_ScleraRight","M_IrisRight",
        "M_LacrimalFluid","M_EyeBlend","M_EyeOcclusion","M_EyeLashes")
def matches(n):
    return any(n == h or n.startswith(h + ".") for h in HIDE)
done=[]
for m in me.materials:
    if m and matches(m.name):
        m.use_nodes = True
        try:
            for n in list(m.node_tree.nodes):
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs["Alpha"].default_value = 0.0
            # make sure alpha is wired to output
            print("alpha=0 set on", m.name)
        except Exception as e:
            print("node fail", m.name, e)
        for attr, val in (("blend_method","BLEND"), ("surface_render_method","BLENDED"),
                          ("shadow_method","NONE")):
            try: setattr(m, attr, val)
            except Exception: pass
        m.use_backface_culling = False
        done.append(m.name)
print("transparent materials:", done)
sc=bpy.context.scene; cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=520; sc.render.resolution_y=640
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"ict_now_f.png"),(0,-0.80,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"ict_now_34.png"),(0.52,-0.62,0.04),(math.radians(82),0,math.radians(40))))
