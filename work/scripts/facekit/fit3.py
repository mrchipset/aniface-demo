import os, numpy as np, json

# --- 切到 work/assets（本脚本按裸文件名读写中间数据）---
def _assets_dir():
    def root(c):
        p = os.path.abspath(c)
        while True:
            if os.path.isdir(os.path.join(p, "work", "assets")):
                return p
            q = os.path.dirname(p)
            if q == p:
                raise RuntimeError()
            p = q
    cands = []
    try:
        cands.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass
    cands.append(os.getcwd())
    for c in cands:
        try:
            return os.path.join(root(c), "work", "assets")
        except RuntimeError:
            continue
    raise RuntimeError("找不到 work/assets，请从仓库目录内运行本脚本")

os.chdir(_assets_dir())

neutral = np.load("ict_neutral.npy"); ids = np.load("ict_ids.npy")
D = ids - neutral[None,:,:]
print("raw OBJ extents: x=%.1f y=%.1f z=%.1f  (y should be the height axis)" % tuple(neutral.max(0)-neutral.min(0)))

LM68 = [1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]
CORR = [(0,127),(2,234),(8,152),(14,454),(16,356),(17,70),(19,105),(21,107),(22,336),(24,334),(26,300),
        (27,168),(30,4),(31,129),(35,358),(36,33),(39,133),(42,362),(45,263),(37,159),(41,145),
        (44,386),(46,374),(48,61),(54,291),(51,13),(57,14),(62,17),(66,0)]
idx = np.array([LM68[a] for a,_ in CORR]); mp_idx = np.array([b for _,b in CORR])
P0 = neutral[idx]; Di_all = D[:, idx, :]
Q = np.load("mp_landmarks.npy")[mp_idx]; Qx, Qy = Q[:,0], Q[:,1]

# CORRECT axes: OBJ is Y-up -> horizontal = x, vertical = y(up), depth = z
X0 = P0[:,0]; Y0 = P0[:,1]
print("model X range %.1f..%.1f | Y(up) range %.1f..%.1f" % (X0.min(),X0.max(),Y0.min(),Y0.max()))
print("photo  X range %.0f..%.0f | Y(down) range %.0f..%.0f" % (Qx.min(),Qx.max(),Qy.min(),Qy.max()))

def fit(K, lam, iters=80):
    Di = Di_all[:K]
    c = np.zeros(K)
    s = (Qx.max()-Qx.min())/(X0.max()-X0.min())
    tx = Qx.mean()-s*X0.mean(); ty = Qy.mean()+s*Y0.mean()
    for it in range(iters):
        Xm = X0 + Di[:,:,0].T @ c; Ym = Y0 + Di[:,:,1].T @ c
        A = np.zeros((2*len(Xm),3)); b = np.zeros(2*len(Xm))
        A[0::2,0]=Xm; A[0::2,1]=1; b[0::2]=Qx
        A[1::2,0]=-Ym; A[1::2,2]=1; b[1::2]=Qy      # image v is down, model Y is up
        (s,tx,ty),_,_,_ = np.linalg.lstsq(A,b,rcond=None)
        Xt=(Qx-tx)/s; Yt=(ty-Qy)/s
        A2 = np.concatenate([Di[:,:,0], Di[:,:,1]], axis=1).T
        b2 = np.concatenate([Xt-X0, Yt-Y0])
        cn,_,_,_ = np.linalg.lstsq(np.vstack([A2, lam*np.eye(K)]), np.concatenate([b2, np.zeros(K)]), rcond=None)
        if np.abs(cn-c).max() < 1e-9: c = cn; break
        c = cn
    Xm = X0 + Di[:,:,0].T@c; Ym = Y0 + Di[:,:,1].T@c
    rmse = np.sqrt(((s*Xm+tx-Qx)**2 + (-s*Ym+ty-Qy)**2).mean())
    hh = neutral[:,1].max()-neutral[:,1].min()
    newh = (neutral[:,1]+D[:K,:,1].T@c).max()-(neutral[:,1]+D[:K,:,1].T@c).min()
    return c,s,tx,ty,rmse,100*(newh-hh)/hh

print("\n  K   lam   rmse(px)  |c|  max|c|  height-dev")
rows=[]
for K in (15,25,40,60):
    for lam in (0.5,2,5,20):
        c,s,tx,ty,rmse,hdev = fit(K,lam)
        rows.append((rmse,K,lam,c,s,tx,ty,np.linalg.norm(c),hdev))
        print(" %3d %5g  %6.2f  %5.2f %6.2f   %+.1f%%" % (K,lam,rmse,np.linalg.norm(c),np.abs(c).max(),hdev))
ok=[r for r in rows if np.linalg.norm(r[7])<6 and abs(r[8])<12]
best=min(ok,key=lambda r:r[0]) if ok else min(rows,key=lambda r:r[0])
print("\nCHOSEN: rmse=%.2f px  K=%d lam=%g  |c|=%.2f  height-dev=%+.1f%%" % (best[0],best[1],best[2],best[7],best[8]))
full=np.zeros(100); full[:best[1]]=best[3]
json.dump({"identity_coefficients":full.tolist(),"K":best[1],"lambda":best[2],
           "scale":float(best[4]),"tx":float(best[5]),"ty":float(best[6])}, open("ict_fit.json","w"))
print("saved ict_fit.json")
