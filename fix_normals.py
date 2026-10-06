import bpy, os, math
OUT=r"<HOME>\tmp\blender"
ob=bpy.data.objects["ICTFaceModel"]; me=ob.data

# recalc normals outward (edit mode)
bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
bpy.context.view_layer.objects.active=ob
try:
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    print("normals recalculated")
except Exception as e:
    print("normal recalc failed:", e)
    try: bpy.ops.object.mode_set(mode='OBJECT')
    except: pass

idx={m.name:i for i,m in enumerate(me.materials) if m}
ip=idx["PhotoFace"]; isk=idx["SkinTone"]; ih=idx["HairTone"]
face=[p for p in me.polygons if p.material_index in (ip,isk)]
import statistics
print("front-half mean normal.z after recalc: %+.3f" % statistics.mean(
    p.normal.z for p in face if p.center.z < (min(v.co.z for v in me.vertices)+max(v.co.z for v in me.vertices))/2))

nph=0
for p in face:
    if p.normal.z < 0.0: p.material_index=ip; nph+=1
    else: p.material_index=isk
print("photo=%d skin=%d" % (nph, len(face)-nph))

sc=bpy.context.scene; cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=520; sc.render.resolution_y=640
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"ict_neutral_f.png"),(0,-0.80,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"ict_neutral_34.png"),(0.52,-0.62,0.04),(math.radians(82),0,math.radians(40))))
