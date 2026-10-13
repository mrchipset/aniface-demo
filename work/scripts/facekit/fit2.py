import numpy as np, json

neutral = np.load("ict_neutral.npy"); ids = np.load("ict_ids.npy")
D = ids - neutral[None,:,:]
LM68 = [1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]
CORR = [(0,127),(2,234),(8,152),(14,454),(16,356),(17,70),(19,105),(21,107),(22,336),(24,334),(26,300),
        (27,168),(30,4),(31,129),(35,358),(36,33),(39,133),(42,362),(45,263),(37,159),(41,145),
        (44,386),(46,374),(48,61),(54,291),(51,13),(57,14),(62,17),(66,0)]
idx = np.array([LM68[a] for a,_ in CORR]); mp_idx = np.array([b for _,b in CORR])
P0 = neutral[idx]; Di_all = D[:, idx, :]
Q = np.load("mp_landmarks.npy")[mp_idx]
Qx, Qy = Q[:,0], Q[:,1]
X0, Z0 = P0[:,0], P0[:,2]

head_scale = neutral[:,2].max()-neutral[:,2].min()
print("head height (model units): %.1f" % head_scale)

def fit(K, lam, iters=60):
    Di = Di_all[:K]
    c = np.zeros(K)
    s = (Qx.max()-Qx.min())/(X0.max()-X0.min()); tx = Qx.mean()-s*X0.mean(); ty = Qy.mean()+s*Z0.mean()
    for it in range(iters):
        Xm = X0 + Di[:,:,0].T @ c; Zm = Z0 + Di[:,:,2].T @ c
        A = np.zeros((2*len(Xm),3)); b = np.zeros(2*len(Xm))
        A[0::2,0]=Xm; A[0::2,1]=1; b[0::2]=Qx
        A[1::2,0]=-Zm; A[1::2,2]=1; b[1::2]=Qy
        (s,tx,ty),_,_,_ = np.linalg.lstsq(A,b,rcond=None)
        Xt=(Qx-tx)/s; Zt=(ty-Qy)/s
        A2 = np.concatenate([Di[:,:,0], Di[:,:,2]], axis=1).T     # (58,K)
        b2 = np.concatenate([Xt-X0, Zt-Z0])
        cn,_,_,_ = np.linalg.lstsq(np.vstack([A2, lam*np.eye(K)]), np.concatenate([b2, np.zeros(K)]), rcond=None)
        d = np.abs(cn-c).max(); c = cn
        if d < 1e-9: break
    Xm = X0 + Di[:,:,0].T @ c; Zm = Z0 + Di[:,:,2].T @ c
    rmse = np.sqrt(((s*Xm+tx-Qx)**2 + (-s*Zm+ty-Qy)**2).mean())
    return c, s, tx, ty, rmse

print("\n K   lam    rmse(px)  |c|   max|c|   face-height-dev")
best=None
for K in (20, 30, 40, 60):
    for lam in (0.5, 2, 5, 20, 100):
        c,s,tx,ty,rmse = fit(K, lam)
        full = np.zeros(100); full[:K]=c
        dev = (D[:K].transpose(1,0,2) @ c)
        hdev = (full[:K].reshape(1,-1) @ D[:K].reshape(K,-1)).reshape(-1,3)
        hh = neutral[:,2].max()-neutral[:,2].min()
        newh = (neutral[:,2]+D[:K, :, 2].T@c).max()-(neutral[:,2]+D[:K,:,2].T@c).min()
        print(" %3d %5g  %7.2f  %5.2f  %6.2f    %+.1f%%" % (K,lam,rmse,np.linalg.norm(c),np.abs(c).max(),100*(newh-hh)/hh))
        if best is None or (np.linalg.norm(c)<8 and rmse<best[0]): best=(rmse,K,lam,c,s,tx,ty,np.linalg.norm(c))
print()
print("BEST: rmse=%.2f K=%d lam=%g |c|=%.2f" % (best[0],best[1],best[2],best[7]))
c,s,tx,ty = best[3],best[4],best[5],best[6]
full=np.zeros(100); full[:best[1]]=c
json.dump({"identity_coefficients": full.tolist(), "K": best[1], "lambda": best[2],
           "scale": float(s), "tx": float(tx), "ty": float(ty)}, open("ict_fit.json","w"))
print("saved ict_fit.json")
