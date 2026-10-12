import bpy, os, numpy as np
OUT=r"."; W=H=512
d = np.load(os.path.join(OUT,"head_uvmap.npz"))
pos, mask, nrm = d["pos"], d["mask"], d["nrm"]
src = bpy.data.images["Image_0"]
px = np.array(src.pixels[:], np.float32).reshape(H,W,4)[:,:,:3]
L = px[:,:,0]*0.299+px[:,:,1]*0.587+px[:,:,2]*0.114
front = mask & (nrm[:,:,1] < -0.25)
pup = front & (L < 0.12)

ys,xs = np.where(pup)
print("pupil-region UV bbox: x[%d,%d]  vrow[%d,%d]   (u = x/%d, v = vrow/%d)" % (xs.min(),xs.max(),ys.min(),ys.max(),W,H))
print("   u [%.3f, %.3f]   v [%.3f, %.3f]" % (xs.min()/W, xs.max()/W, ys.min()/H, ys.max()/H))
print("   centroid: u=%.3f v=%.3f" % (xs.mean()/W, ys.mean()/H))
fy,fx = np.where(front)
print("front-region UV bbox: u[%.3f,%.3f] v[%.3f,%.3f]" % (fx.min()/W, fx.max()/W, fy.min()/H, fy.max()/H))

dbg = px.copy()*0.35
dbg[front] = dbg[front]*0.4 + np.array([0.0,0.5,0.0])
dbg[pup]   = np.array([1.0,0.0,0.0])
d2 = (L<0.30) & mask
dbg[d2 & ~front] = np.array([0.0,0.0,0.6])
im = bpy.data.images.new("uv_debug", width=W, height=H, alpha=False)
im.pixels.foreach_set(np.concatenate([dbg, np.ones((H,W,1),np.float32)],axis=2).reshape(-1))
im.filepath_raw=os.path.join(OUT,"uv_debug.png"); im.file_format='PNG'; im.save()
print("saved uv_debug.png  (绿=正面, 红=瞳孔区, 蓝=背面/侧面暗部)")
