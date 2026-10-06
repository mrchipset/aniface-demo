import bpy, os, numpy as np
OUT=r"<HOME>\tmp\blender"; W=H=512
ob = bpy.data.objects["head_geo.002"]; me = ob.data
mw = ob.matrix_world.copy()
uvl = me.uv_layers["UVMap"].data
wc = [mw @ v.co for v in me.vertices]

pos  = np.full((H,W,3), np.nan, dtype=np.float32)
face = np.full((H,W), -1, dtype=np.int32)     # 记录三角形序号，便于查法线

def raster(tri_uv, tri_p, fid):
    xs = [p[0]*W for p in tri_uv]; ys = [p[1]*H for p in tri_uv]
    x0,x1 = int(np.floor(min(xs))), int(np.ceil(max(xs)))
    y0,y1 = int(np.floor(min(ys))), int(np.ceil(max(ys)))
    x0=max(x0,0); y0=max(y0,0); x1=min(x1,W-1); y1=min(y1,H-1)
    if x1<x0 or y1<y0: return
    X,Y = np.meshgrid(np.arange(x0,x1+1)+0.5, np.arange(y0,y1+1)+0.5)
    ax,ay = xs[0],ys[0]; bx,by = xs[1],ys[1]; cx,cy = xs[2],ys[2]
    den = (by-cy)*(ax-cx) + (cx-bx)*(ay-cy)
    if abs(den) < 1e-9: return
    wa = ((by-cy)*(X-cx) + (cx-bx)*(Y-cy))/den
    wb = ((cy-ay)*(X-cx) + (ax-cx)*(Y-cy))/den
    wc_ = 1-wa-wb
    ins = (wa>=-1e-4)&(wb>=-1e-4)&(wc_>=-1e-4)
    if not ins.any(): return
    sub = pos[y0:y1+1, x0:x1+1]
    for ch in range(3):
        v = wa*tri_p[0][ch] + wb*tri_p[1][ch] + wc_*tri_p[2][ch]
        sub[:,:,ch] = np.where(ins, v, sub[:,:,ch])
    pos[y0:y1+1, x0:x1+1] = sub
    fs = face[y0:y1+1, x0:x1+1]
    face[y0:y1+1, x0:x1+1] = np.where(ins, fid, fs)

tris=0
for pi, poly in enumerate(me.polygons):
    li = list(poly.loop_indices)
    uvs = [(uvl[l].uv[0], uvl[l].uv[1]) for l in li]
    p3  = [wc[me.loops[l].vertex_index] for l in li]
    for k in range(1, len(li)-1):
        raster([uvs[0],uvs[k],uvs[k+1]], [p3[0],p3[k],p3[k+1]], pi); tris+=1
# 法线（世界空间）也存一份，用于判断"是否朝向正前方"
nrm = np.zeros((H,W,3), np.float32)
for pi, poly in enumerate(me.polygons):
    m = (face==pi)
    if m.any():
        n = (mw.to_3x3().inverted().transposed() @ poly.normal).normalized()
        nrm[m] = (n.x, n.y, n.z)
cov = ~np.isnan(pos[:,:,0])
print("rasterized triangles:", tris)
print("UV island coverage: %.1f%%  (%d texels)" % (100*cov.mean(), int(cov.sum())))
ys,xs = np.where(cov)
print("island bbox in tex: x[%d,%d] v-row[%d,%d]" % (xs.min(),xs.max(),ys.min(),ys.max()))
out = {"pos":pos, "mask":cov, "nrm":nrm}
np.savez(os.path.join(OUT,"head_uvmap.npz"), **out)
print("saved head_uvmap.npz")
