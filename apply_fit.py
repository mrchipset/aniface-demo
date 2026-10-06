import bpy, numpy as np, json, mathutils, math

fit = json.load(open(r"<HOME>\tmp\blender\ict_fit.json"))
c = np.array(fit["identity_coefficients"], dtype=np.float64)
neutral = np.load(r"<HOME>\tmp\blender\ict_neutral.npy")
ids = np.load(r"<HOME>\tmp\blender\ict_ids.npy")
D = ids - neutral[None,:,:]
print("coeffs: K=%s |c|=%.2f" % (fit["K"], np.linalg.norm(c[:fit["K"]])))

h = bpy.data.objects["ICTFaceModel"]; me = h.data
kb0 = me.shape_keys.key_blocks["Basis"]
bl = np.array([[v.co.x, v.co.y, v.co.z] for v in kb0.data])
print("blender Basis bbox:", np.round(bl.min(0),4), np.round(bl.max(0),4))

# determine which axis mapping reproduces the blender coords from the OBJ
S = (bl.max(0)-bl.min(0))
O = (neutral.max(0)-neutral.min(0))
print("blender extents:", np.round(S,4), " obj extents:", np.round(O,1))
# hypothesis: blender = scale * (obj.x, -obj.z, obj.y) + off
scale = S[2]/O[1]
test = np.column_stack([neutral[:,0], -neutral[:,2], neutral[:,1]]) * scale
test -= (test.min(0)+test.max(0))/2
blm = bl - (bl.min(0)+bl.max(0))/2
err = np.abs(test - blm).mean()
print("hypothesis (x,-z,y) scale=%.6f  mean abs err = %.5f" % (scale, err))
alt = np.column_stack([neutral[:,0], neutral[:,1], neutral[:,2]]) * scale
alt -= (alt.min(0)+alt.max(0))/2
print("hypothesis identity         mean abs err = %.5f" % np.abs(alt - blm).mean())

# combined identity delta in OBJ convention -> convert -> scale
K = fit["K"]
delta_obj = (c[:K][:,None,None] * D[:K]).sum(0)          # (N,3)
delta_bl = np.column_stack([delta_obj[:,0], -delta_obj[:,2], delta_obj[:,1]]) * scale
print("delta magnitude: mean %.4f m, max %.4f m (head is %.3f m tall)" % (
      np.linalg.norm(delta_bl,axis=1).mean(), np.linalg.norm(delta_bl,axis=1).max(),
      float(bl.max(0)[2]-bl.min(0)[2])))

# apply to every shape key block
for kb in me.shape_keys.key_blocks:
    for i, pt in enumerate(kb.data):
        pt.co = pt.co + mathutils.Vector((float(delta_bl[i,0]), float(delta_bl[i,1]), float(delta_bl[i,2])))
me.update(); bpy.context.view_layer.update()
print("applied identity to %d shape key blocks" % len(me.shape_keys.key_blocks))
