import bpy, os, numpy as np
OUT=r"."; W=H=512
d = np.load(os.path.join(OUT,"head_uvmap.npz")); mask = d["mask"]
src = bpy.data.images["Image_0"]
px = np.array(src.pixels[:], np.float32).reshape(H,W,4)[:,:,:3]
L = px[:,:,0]*0.299+px[:,:,1]*0.587+px[:,:,2]*0.114

yy, xx = np.mgrid[0:H, 0:W]
# 脸的岛屿在贴图左上（PNG 上方）-> 高 vrow
face_area = mask & (xx < 300) & (yy > 300)
dark = face_area & (L < 0.12)
print("face-area dark texels:", int(dark.sum()))
if dark.sum() > 10:
    xs = xx[dark]; ys = yy[dark]
    mid = (xs.min()+xs.max())/2
    l = xs < mid; r = ~l
    print("left pupil  uv px: x=%.0f vrow=%.0f  (n=%d)" % (xs[l].mean(), ys[l].mean(), l.sum()))
    print("right pupil uv px: x=%.0f vrow=%.0f  (n=%d)" % (xs[r].mean(), ys[r].mean(), r.sum()))
    print("pupil x range [%d,%d] vrow range [%d,%d]" % (xs.min(),xs.max(),ys.min(),ys.max()))
# 脸岛屿的整体范围
fy, fx = np.where(face_area)
print("face island bbox: x[%d,%d] vrow[%d,%d]" % (fx.min(),fx.max(),fy.min(),fy.max()))
