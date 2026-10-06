import bpy, os, numpy as np, mathutils
OUT=r"<HOME>\tmp\blender"
ob = bpy.data.objects["head_geo.002"]; me = ob.data
mw = ob.matrix_world.copy()
W=H=512
uv = me.uv_layers["UVMap"]
pos = np.full((H,W,3), np.nan, dtype=np.float32)
mask = np.zeros((H,W), dtype=bool)
for poly in me.polygons:
    for li in poly.loop_indices:
        u,v = uv.data[li].uv
        x = int((u % 1.0)*W); y = int((v % 1.0)*H)
        x = min(max(x,0),W-1); y = min(max(y,0),H-1)
        p = mw @ me.vertices[me.loops[li].vertex_index].co
        pos[y,x] = (p.x,p.y,p.z); mask[y,x]=True
print("coverage initial: %.1f%%" % (100*mask.mean()))
for _ in range(10):
    empty = ~mask
    if not empty.any(): break
    acc = np.zeros_like(pos); cnt = np.zeros((H,W),np.float32)
    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
        shifted = np.roll(pos, (dy,dx), axis=(0,1))
        m2 = np.roll(mask, (dy,dx), axis=(0,1))
        acc += np.where(m2[...,None], shifted, 0); cnt += m2
    fill = empty & (cnt>0)
    pos[fill] = acc[fill]/cnt[fill][...,None]
    mask |= fill
print("coverage final: %.1f%%" % (100*mask.mean()))

# ---- find near-black blobs (pupils) in the ORIGINAL texture ----
src = bpy.data.images["Image_0"]
px = np.array(src.pixels[:], np.float32).reshape(H,W,4)[:,:,:3]
L = px[:,:,0]*0.299+px[:,:,1]*0.587+px[:,:,2]*0.114
black = (L < 0.07) & mask
print("near-black texels:", int(black.sum()))
# simple flood-fill labeling
lab = np.zeros((H,W), np.int32); cur=0; comps=[]
import collections
for y0 in range(H):
    for x0 in range(W):
        if black[y0,x0] and lab[y0,x0]==0:
            cur+=1; q=collections.deque([(y0,x0)]); lab[y0,x0]=cur; pix=[]
            while q:
                y,x=q.popleft(); pix.append((y,x))
                for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                    ny,nx=y+dy,x+dx
                    if 0<=ny<H and 0<=nx<W and black[ny,nx] and lab[ny,nx]==0:
                        lab[ny,nx]=cur; q.append((ny,nx))
            if len(pix)>=6:
                ys=[p[0] for p in pix]; xs=[p[1] for p in pix]
                cy=int(np.mean(ys)); cx=int(np.mean(xs))
                comps.append((len(pix), cx, cy, pos[cy,cx].tolist()))
comps.sort(reverse=True)
print("blobs (size, u_px, v_px, world_xyz):")
for c in comps[:8]:
    print("   size=%4d  uv_px=(%3d,%3d)  world=(%.3f, %.3f, %.3f)" % (c[0],c[1],c[2],c[3][0],c[3][1],c[3][2]))
np.save(os.path.join(OUT,"head_uvpos.npy"), pos); np.save(os.path.join(OUT,"head_uvmask.npy"), mask)
print("saved position map")
