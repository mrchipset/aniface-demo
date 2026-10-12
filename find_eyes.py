import bpy, os, numpy as np
OUT=r"."; W=H=512
d = np.load(os.path.join(OUT,"head_uvmap.npz"))
pos, mask, nrm = d["pos"], d["mask"], d["nrm"]
src = bpy.data.images["Image_0"]
px = np.array(src.pixels[:], np.float32).reshape(H,W,4)[:,:,:3]
L = px[:,:,0]*0.299+px[:,:,1]*0.587+px[:,:,2]*0.114

front = mask & (nrm[:,:,1] < -0.25)          # 朝向正前（-Y）
print("front texels: %d" % int(front.sum()))

X,Y,Z = pos[:,:,0], pos[:,:,1], pos[:,:,2]
pup = front & (L < 0.12)
if pup.sum() > 20:
    xs = X[pup]; zs = Z[pup]
    print("dark-front texels: %d  x range [%.3f,%.3f]  z range [%.3f,%.3f]" % (pup.sum(), xs.min(), xs.max(), zs.min(), zs.max()))
    left  = xs[xs < -0.02]; right = xs[xs > 0.02]
    mid   = xs[np.abs(xs) <= 0.02]
    print("  x<-0.02: n=%d mean=%.3f | |x|<=0.02: n=%d | x>0.02: n=%d mean=%.3f" % (
        len(left), left.mean() if len(left) else 0, len(mid), len(right), right.mean() if len(right) else 0))
    if len(left): print("  left cluster z mean = %.3f" % zs[xs<-0.02].mean())
    if len(right): print("  right cluster z mean = %.3f" % zs[xs>0.02].mean())
print()
print("front region extents: x[%.3f,%.3f]  z[%.3f,%.3f]" % (X[front].min(),X[front].max(),Z[front].min(),Z[front].max()))
print("head bbox: x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]" % (
  X[mask].min(),X[mask].max(),Y[mask].min(),Y[mask].max(),Z[mask].min(),Z[mask].max()))
