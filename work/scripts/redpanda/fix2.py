import bpy, os, math
OUT = r"."
me = bpy.data.objects["ICTFaceModel"].data
idx = {}
for i,m in enumerate(me.materials):
    if m: idx[m.name]=i
ip=idx["PhotoFace"]; isk=idx["SkinTone"]; ih=idx["HairTone"]
print("slots:", {k:v for k,v in idx.items() if k in ("PhotoFace","SkinTone","HairTone")})

face_polys = [p for p in me.polygons if p.material_index in (ip, isk)]
print("recoverable face polys:", len(face_polys), "of", len(me.polygons))
nz = [p.normal.z for p in face_polys]
import statistics
print("normal.z: min %.2f  p10 %.2f  median %.2f  p90 %.2f  max %.2f" % (
    min(nz), sorted(nz)[len(nz)//10], statistics.median(nz), sorted(nz)[9*len(nz)//10], max(nz)))
buckets = {}
for v in nz:
    b = round(v*10)/10
    buckets[b]=buckets.get(b,0)+1
print("histogram:", dict(sorted(buckets.items())))

T = -0.05
nph=0
for p in face_polys:
    if p.normal.z < T: p.material_index = ip; nph+=1
    else: p.material_index = isk
print("with T=%.2f -> photo %d / skin %d" % (T, nph, len(face_polys)-nph))

sc=bpy.context.scene; cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=480; sc.render.resolution_y=600
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"ict_fit_f.png"),(0,-0.85,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"ict_fit_34.png"),(0.55,-0.65,0.05),(math.radians(82),0,math.radians(40))))
