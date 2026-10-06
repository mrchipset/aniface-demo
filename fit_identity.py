import numpy as np, os, json, time

FM = r"<HOME>\tmp\blender\ICT-FaceKit\FaceXModel"
LM68 = [1225,1888,1052,367,1719,1722,2199,1447,966,3661,4390,3927,3924,2608,3272,4088,3443,268,493,1914,2044,1401,3615,4240,4114,2734,2509,978,4527,4942,4857,1140,2075,1147,4269,3360,1507,1542,1537,1528,1518,1511,3742,3751,3756,3721,3725,3732,5708,5695,2081,0,4275,6200,6213,6346,6461,5518,5957,5841,5702,5711,5533,6216,6207,6470,5517,5966]

# (ict68 index, mediapipe index)
CORR = [(0,127),(2,234),(8,152),(14,454),(16,356),
        (17,70),(19,105),(21,107),(22,336),(24,334),(26,300),
        (27,168),(30,4),(31,129),(35,358),
        (36,33),(39,133),(42,362),(45,263),
        (37,159),(41,145),(44,386),(46,374),
        (48,61),(54,291),(51,13),(57,14),(62,17),(66,0)]

def read_verts(path):
    vs=[]
    with open(path,'r') as f:
        for line in f:
            if line[:2]=='v ':
                p=line.split()
                vs.append((float(p[1]),float(p[2]),float(p[3])))
    return np.array(vs, dtype=np.float64)

t0=time.time()
neutral = read_verts(os.path.join(FM,"generic_neutral_mesh.obj"))
print("neutral:", neutral.shape, "%.1fs" % (time.time()-t0))
ids=[]
for i in range(100):
    p=os.path.join(FM,"identity%03d.obj"%i)
    if os.path.exists(p): ids.append(read_verts(p))
ids=np.array(ids)
print("identity modes:", ids.shape, "%.1fs" % (time.time()-t0))
np.save("ict_neutral.npy", neutral); np.save("ict_ids.npy", ids)
D = ids - neutral[None,:,:]            # deltas
print("delta norm mean: %.4f" % np.linalg.norm(D.reshape(100,-1),axis=1).mean())

idx = np.array([LM68[a] for a,_ in CORR])
mp_idx = np.array([b for _,b in CORR])
P0 = neutral[idx]                      # (29,3)
Di = D[:, idx, :]                      # (100,29,3)
Q  = np.load("mp_landmarks.npy")[mp_idx]   # (29,2)

# orientation check
print("model X: ict36=%.4f ict45=%.4f (36 should be right eye)" % (P0[list(mp_idx).index(33)][0], P0[list(mp_idx).index(263)][0]))
print("photo X: MP33=%.0f MP263=%.0f" % (Q[list(mp_idx).index(33)][0], Q[list(mp_idx).index(263)][0]))

X0, Z0 = P0[:,0], P0[:,2]
Qx, Qy = Q[:,0], Q[:,1]
cx, cy = Qx.mean(), Qy.mean()
s = (Qx.max()-Qx.min()) / (X0.max()-X0.min())
tx, ty = cx - s*X0.mean(), cy + s*Z0.mean()

c = np.zeros(100)
lam = 1.0
for it in range(40):
    # --- solve similarity (s, tx, ty) given c ---
    Xm = X0 + Di[:,:,0].T @ c
    Zm = Z0 + Di[:,:,2].T @ c
    # u = s*X + tx ; v = -s*Z + ty
    A = np.zeros((2*len(Xm),3)); b = np.zeros(2*len(Xm))
    A[0::2,0]=Xm; A[0::2,1]=1; b[0::2]=Qx
    A[1::2,0]=-Zm; A[1::2,2]=1; b[1::2]=Qy
    sol,_,_,_ = np.linalg.lstsq(A,b,rcond=None)
    s, tx, ty = sol
    # --- solve c given similarity ---
    Xt = (Qx - tx)/s ; Zt = (ty - Qy)/s
    # Di[:,:,0] is (100,29) -> we need rows per mode
    Ax = Di[:,:,0]      # (100,29)
    Az = Di[:,:,2]
    A2 = np.vstack([Ax, Az])                      # (200,100) as (100, 2*29)? careful
    b2 = np.concatenate([Xt - X0, Zt - Z0])       # (58,)
    A2 = np.concatenate([Ax, Az], axis=1).T       # (58,100)
    Reg = lam*np.eye(100)
    cnew,_,_,_ = np.linalg.lstsq(np.vstack([A2, Reg]), np.concatenate([b2, np.zeros(100)]), rcond=None)
    dc = np.abs(cnew-c).max(); c = cnew
    if it % 8 == 0 or dc < 1e-6:
        Xm = X0 + Di[:,:,0].T @ c; Zm = Z0 + Di[:,:,2].T @ c
        ru = s*Xm + tx - Qx ; rv = -s*Zm + ty - Qy
        err = np.sqrt((ru**2+rv**2).mean())
        print("it%02d lam=%.4g  s=%.1f tx=%.1f ty=%.1f  rmse=%.2f px  dc=%.2g" % (it,lam,s,tx,ty,err,dc))
    if it == 20: lam = 0.1
    if it == 32: lam = 0.01

Xm = X0 + Di[:,:,0].T @ c; Zm = Z0 + Di[:,:,2].T @ c
ru = s*Xm + tx - Qx ; rv = -s*Zm + ty - Qy
print("FINAL rmse: %.2f px   s=%.2f tx=%.1f ty=%.1f" % (np.sqrt((ru**2+rv**2).mean()), s, tx, ty))
print("coeff norm |c| = %.2f  max|c| = %.2f" % (np.linalg.norm(c), np.abs(c).max()))
json.dump({"identity_coefficients": c.tolist(), "scale": float(s), "tx": float(tx), "ty": float(ty)}, open("ict_fit.json","w"))
print("saved ict_fit.json")
