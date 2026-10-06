import bpy, math, os, mathutils

h = bpy.data.objects["ICTFaceModel"]; me = h.data
mw = h.matrix_world

LM68 = [1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]
chin_i = LM68[8]
eye_idx = LM68[36:48]          # eye contour
def wpos(i): return mw @ me.vertices[i].co
chin = wpos(chin_i)
eye_z = sum((mw @ me.vertices[i].co).z for i in eye_idx)/len(eye_idx)
co = [mw @ v.co for v in me.vertices]
zs=[p.z for p in co]; xs=[p.x for p in co]
top_z = max(zs)
print("mesh chin:", [round(v,4) for v in chin], "| eye_z:", round(eye_z,4), "| top_z:", round(top_z,4))

# photo
img = bpy.data.images[os.path.basename(r"<HOME>\Downloads\photo.jpg")]
W,H = img.size; px=list(img.pixels)
def get(x,y):
    i=(y*W+x)*4; return px[i],px[i+1],px[i+2]
# background = corner colour
bgr,bgg,bgb = get(2,H-2)
def is_fg(x,y):
    r,g,b = get(x,y)
    return abs(r-bgr)+abs(g-bgg)+abs(b-bgb) > 0.14
# row widths (top-down) to find head vs shoulders
rows=[]
for yt in range(0,H,4):
    y = H-1-yt
    cnt = sum(1 for x in range(0,W,4) if is_fg(x,y))
    rows.append((yt,cnt))
head_top_yt = next((yt for yt,c in rows if c>2), 0)
maxc = max(c for _,c in rows)
# shoulder jump: first yt (below 30% ) where count > 1.6x median head width
head_widths = [c for yt,c in rows if yt < H*0.5]
med = sorted(head_widths)[len(head_widths)//2] if head_widths else 1
shoulder_yt = next((yt for yt,c in rows if yt > H*0.35 and c > 1.7*med), int(H*0.75))
print("photo: bg=%.2f,%.2f,%.2f | head_top_yt=%d | median head width=%d | shoulder_yt=%d (max %d)" % (bgr,bgg,bgb,head_top_yt,med,shoulder_yt,maxc))
# left/right at eye level
eye_yt = int(head_top_yt + (shoulder_yt-head_top_yt)*0.45)
yy = H-1-eye_yt
xs_fg = [x for x in range(W) if is_fg(x,yy)]
L = min(xs_fg) if xs_fg else 0; R = max(xs_fg) if xs_fg else W-1
print("photo eye-line y=%d  x[%d,%d]" % (eye_yt, L, R))

# photo anchor v (v measured from bottom)
v_top   = 1.0 - head_top_yt/H
v_chin  = 1.0 - (shoulder_yt - (shoulder_yt-head_top_yt)*0.13)/H
v_eye   = 1.0 - eye_yt/H
print("photo anchors v_top=%.3f v_eye=%.3f v_chin=%.3f" % (v_top, v_eye, v_chin))

# solve linear map: v = a + b*z  using (chin -> v_chin) and (eye -> v_eye)
bz = (v_chin - v_eye) / (chin.z - eye_z)
az = v_chin - bz*chin.z
# u map: mesh x -> photo u, using head width at eye level
uL, uR = L/W, R/W
xu = [p.x for p in co]
X0, X1 = min(xu), max(xu)
bx = (uR-uL)/(X1-X0); ax = uL - bx*X0
print("map: v = %.3f + %.3f*z ; u = %.3f + %.3f*x" % (az,bz,ax,bx))

uv = me.uv_layers["PhotoUV"]
for poly in me.polygons:
    for li in poly.loop_indices:
        p = co[me.loops[li].vertex_index]
        uv.data[li].uv = (min(max(ax+bx*p.x,0),1), min(max(az+bz*p.z,0),1))
uv.active = True; uv.active_render = True

sc = bpy.context.scene; cam = sc.camera
cam.data.lens = 55
sc.render.resolution_x=480; sc.render.resolution_y=600
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cam.location=(0,-0.85,0.01); cam.rotation_euler=(math.radians(90),0,0)
sc.render.filepath = r"<HOME>\tmp\blender\ict_align.png"
bpy.ops.render.render(write_still=True)
print("ok", os.path.getsize(r"<HOME>\tmp\blender\ict_align.png"))
