import bpy, math, os, mathutils

h = bpy.data.objects["ICTFaceModel"]; me = h.data
basis = me.shape_keys.key_blocks["Basis"].data
mw = h.matrix_world
co = [mw @ basis[i].co for i in range(len(basis))]

LM68 = [1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]
chin = co[LM68[8]]
eyes = [co[i] for i in LM68[36:48]]
eye_z = sum(p.z for p in eyes)/len(eyes)
eye_xL = min(p.x for p in eyes); eye_xR = max(p.x for p in eyes)
zs=[p.z for p in co]; top_z=max(zs)

W,H = 827,1063
L,R,eye_yt,head_top_yt,shoulder_yt = 177,632,415,48,864
v_chin = 1.0 - (shoulder_yt-(shoulder_yt-head_top_yt)*0.13)/H
v_eye  = 1.0 - eye_yt/H
# vertical: map chin->v_chin, eyes->v_eye
bz=(v_chin-v_eye)/(chin.z-eye_z); az=v_chin-bz*chin.z
# horizontal: eye corners span ~62% of head width
EYE_SPAN = 0.62
bx = (EYE_SPAN*(R-L))/W / (eye_xR-eye_xL)
ax = (L/W + (R-L)/W*((1-EYE_SPAN)/2)) - bx*eye_xL
print("map v=%.3f%+.3f*z | u=%.3f%+.3f*x" % (az,bz,ax,bx))

uv = me.uv_layers["PhotoUV"]
for poly in me.polygons:
    for li in poly.loop_indices:
        p = co[me.loops[li].vertex_index]
        uv.data[li].uv=(min(max(ax+bx*p.x,0),1), min(max(az+bz*p.z,0),1))
uv.active=True; uv.active_render=True

sc=bpy.context.scene; cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=480; sc.render.resolution_y=600
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(path, loc, rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=path
    bpy.ops.render.render(write_still=True); return os.path.getsize(path)
print("front:", shot(r"ict_align.png",(0,-0.85,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(r"ict_align34.png",(0.55,-0.65,0.05),(math.radians(82),0,math.radians(40))))
