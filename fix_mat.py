import bpy, os, math, numpy as np
OUT = r"."
PHOTO = os.environ.get("PHOTO", "photo.jpg")
me = bpy.data.objects["ICTFaceModel"].data
img = bpy.data.images[os.path.basename(PHOTO)]
W,H = img.size; px=list(img.pixels)
def get(x,y):
    i=(y*W+x)*4; return px[i],px[i+1],px[i+2]
def avg(xt,yt,rad=10):
    cx=int(xt*W); cy=int(yt*H); a=[0,0,0]; n=0
    for y in range(max(0,cy-rad),min(H,cy+rad+1)):
        for x in range(max(0,cx-rad),min(W,cx+rad+1)):
            r,g,b=get(x,y); a[0]+=r;a[1]+=g;a[2]+=b;n+=1
    return tuple(v/n for v in a)
skin = avg(0.34,0.56)   # cheek
hair = avg(0.50,0.88)   # hair (bottom-up fraction)
print("skin:", [round(v,3) for v in skin], " hair:", [round(v,3) for v in hair])

msk = bpy.data.materials["SkinTone"]
next(n for n in msk.node_tree.nodes if n.type=="BSDF_PRINCIPLED").inputs["Base Color"].default_value=(*skin,1)
mh = bpy.data.materials["HairTone"]
next(n for n in mh.node_tree.nodes if n.type=="BSDF_PRINCIPLED").inputs["Base Color"].default_value=(*hair,1)

def slot(prefix):
    for i,m in enumerate(me.materials):
        if m and (m.name==prefix or m.name.startswith(prefix+".")): return i
i_face=slot("M_Face"); i_back=slot("M_BackHead")
ip=[i for i,m in enumerate(me.materials) if m and m.name=="PhotoFace"][0]
isk=[i for i,m in enumerate(me.materials) if m and m.name=="SkinTone"][0]
ih=[i for i,m in enumerate(me.materials) if m and m.name=="HairTone"][0]

n_photo=n_skin=0
for poly in me.polygons:
    if poly.material_index==i_face:
        if poly.normal.z < -0.05: poly.material_index=ip; n_photo+=1
        else: poly.material_index=isk; n_skin+=1
    elif poly.material_index==i_back:
        poly.material_index=ih
print("photo polys: %d  skin polys: %d" % (n_photo, n_skin))

sc=bpy.context.scene; cam=sc.camera; cam.data.lens=55
sc.render.resolution_x=480; sc.render.resolution_y=600
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
print("front:", shot(os.path.join(OUT,"ict_fit_f.png"),(0,-0.85,0.01),(math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"ict_fit_34.png"),(0.55,-0.65,0.05),(math.radians(82),0,math.radians(40))))
