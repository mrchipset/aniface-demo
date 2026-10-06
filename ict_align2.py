import bpy, math, os, mathutils

h = bpy.data.objects["ICTFaceModel"]; me = h.data
basis = me.shape_keys.key_blocks["Basis"].data
mw = h.matrix_world
co = [mw @ basis[i].co for i in range(len(basis))]
zs=[p.z for p in co]; xs=[p.x for p in co]
print("Basis bbox z: %.4f .. %.4f  x: %.4f .. %.4f" % (min(zs),max(zs),min(xs),max(xs)))

LM68 = [1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]
chin = co[LM68[8]]
eyes = [co[i] for i in LM68[36:48]]
eye_z = sum(p.z for p in eyes)/len(eyes)
eye_xL = min(p.x for p in eyes); eye_xR = max(p.x for p in eyes)
top_z = max(zs)
print("mesh: chin z=%.4f | eye_z=%.4f | top_z=%.4f | eye x range %.4f..%.4f" % (chin.z, eye_z, top_z, eye_xL, eye_xR))

PHOTO = r"<HOME>\Downloads\photo.jpg"
img = bpy.data.images[os.path.basename(PHOTO)]
W,H = img.size; px=list(img.pixels)
def get(x,y):
    i=(y*W+x)*4; return px[i],px[i+1],px[i+2]
bgr,bgg,bgb = get(2,H-2)
def is_fg(x,y):
    r,g,b=get(x,y); return abs(r-bgr)+abs(g-bgg)+abs(b-bgb) > 0.14
rows=[]
for yt in range(0,H,4):
    y=H-1-yt
    rows.append((yt, sum(1 for x in range(0,W,4) if is_fg(x,y))))
head_top_yt = next((yt for yt,c in rows if c>2),0)
hw=[c for yt,c in rows if yt<H*0.5]; med=sorted(hw)[len(hw)//2] if hw else 1
shoulder_yt = next((yt for yt,c in rows if yt>H*0.35 and c>1.7*med), int(H*0.75))
eye_yt = int(head_top_yt + (shoulder_yt-head_top_yt)*0.45)
yy=H-1-eye_yt
xs_fg=[x for x in range(W) if is_fg(x,yy)]
L,R = (min(xs_fg), max(xs_fg)) if xs_fg else (0,W-1)
v_chin = 1.0 - (shoulder_yt - (shoulder_yt-head_top_yt)*0.13)/H
v_eye  = 1.0 - eye_yt/H
print("photo: top=%d shoulder=%d eye=%d  x[%d,%d]  v_chin=%.3f v_eye=%.3f" % (head_top_yt,shoulder_yt,eye_yt,L,R,v_chin,v_eye))

bz = (v_chin - v_eye)/(chin.z - eye_z); az = v_chin - bz*chin.z
# u: use eye-corner x span -> photo face width at eye line
bx = (R-L)/W / max(eye_xR-eye_xL, 1e-6)
ax = L/W - bx*eye_xL
print("map: v=%.3f%+.3f*z  u=%.3f%+.3f*x" % (az,bz,ax,bx))
for nm, idx in (("chin", LM68[8]), ("eyeL", LM68[45]), ("eyeR", LM68[36]), ("top", None)):
    z = top_z if idx is None else co[idx].z
    print("   check %-5s z=%.3f -> v=%.3f" % (nm, z, az+bz*z))

uv = me.uv_layers["PhotoUV"]
for poly in me.polygons:
    for li in poly.loop_indices:
        p = co[me.loops[li].vertex_index]
        uv.data[li].uv = (min(max(ax+bx*p.x,0),1), min(max(az+bz*p.z,0),1))
uv.active=True; uv.active_render=True

sc=bpy.context.scene; cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=480; sc.render.resolution_y=600
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(path, loc, rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=path
    bpy.ops.render.render(write_still=True); return os.path.getsize(path)
print("front:", shot(r"<HOME>\tmp\blender\ict_align.png",(0,-0.85,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(r"<HOME>\tmp\blender\ict_align34.png",(0.5,-0.7,0.05),(math.radians(80),0,math.radians(35))))
