import bpy, os, math
OUT=r"."
me = bpy.data.objects["ICTFaceModel"].data
idx={m.name:i for i,m in enumerate(me.materials) if m}
ip=idx["PhotoFace"]; isk=idx["SkinTone"]; ih=idx["HairTone"]
face=[p for p in me.polygons if p.material_index in (ip,isk)]

cz=[p.center.z for p in face]; nz=[p.normal.z for p in face]
zc=(min(v.co.z for v in me.vertices)+max(v.co.z for v in me.vertices))/2
front=[p for p in face if p.center.z < zc]
back =[p for p in face if p.center.z >= zc]
import statistics
print("centroid z center=%.3f | front-half polys=%d back-half=%d" % (zc,len(front),len(back)))
print("front-half: mean normal.z = %+.3f" % statistics.mean(p.normal.z for p in front))
print("back-half : mean normal.z = %+.3f" % statistics.mean(p.normal.z for p in back))
# the most-forward and most-backward polygons
p_f = min(face, key=lambda p: p.center.z); p_b = max(face, key=lambda p: p.center.z)
print("most forward poly: center.z=%.3f normal=(%.2f,%.2f,%.2f) area=%.4f" % (p_f.center.z, *p_f.normal, p_f.area))
print("most backward poly: center.z=%.3f normal=(%.2f,%.2f,%.2f)" % (p_b.center.z, *p_b.normal))
# nose tip vertex
nz_min_v = min(me.vertices, key=lambda v: v.co.z)
print("nose-ish vertex: (%.3f, %.3f, %.3f)" % tuple(nz_min_v.co))

# ASSIGN by centroid depth (front half + slight margin)
T = zc + 0.03*(max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices))
n=0
for p in face:
    if p.center.z < T: p.material_index=ip; n+=1
    else: p.material_index=isk
print("assigned photo=%d skin=%d (T=%.3f)" % (n, len(face)-n, T))

sc=bpy.context.scene; cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=480; sc.render.resolution_y=600
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"ict_fit_f.png"),(0,-0.85,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"ict_fit_34.png"),(0.55,-0.65,0.05),(math.radians(82),0,math.radians(40))))

