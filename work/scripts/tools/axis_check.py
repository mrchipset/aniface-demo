import bpy, mathutils
ob = bpy.data.objects["head_geo.002"]
mw = ob.matrix_world.copy()
print("head_geo.002 matrix_world:")
for r in mw:
    print("   [%7.4f %7.4f %7.4f %7.4f]" % (r[0],r[1],r[2],r[3]))
ident = all(abs(mw[i][j] - (1.0 if i==j else 0.0)) < 1e-6 for i in range(4) for j in range(4))
print("  is identity:", ident)

# 局部坐标 -> 世界坐标 的轴映射
for name, v in (("local +X",(1,0,0)), ("local +Y",(0,1,0)), ("local +Z",(0,0,1))):
    w = (mw.to_3x3() @ mathutils.Vector(v))
    print("  %s -> world (%.3f, %.3f, %.3f)" % (name, w.x, w.y, w.z))

# 局部包围盒 / 世界包围盒
me = ob.data
lmin = [min(v.co[i] for v in me.vertices) for i in range(3)]
lmax = [max(v.co[i] for v in me.vertices) for i in range(3)]
print("  local bbox min:", [round(v,3) for v in lmin], "max:", [round(v,3) for v in lmax])
co = [mw @ v.co for v in me.vertices]
wmin = [min(p[i] for p in co) for i in range(3)]; wmax = [max(p[i] for p in co) for i in range(3)]
print("  world bbox min:", [round(v,3) for v in wmin], "max:", [round(v,3) for v in wmax])

# 正面的法线方向：取世界 -Y 侧最多的面 = 正脸；看它的局部法线指向
front_local = [0,0,0]; n=0
for p in me.polygons:
    wn = (mw.to_3x3() @ p.normal)
    if wn.y < -0.5:
        front_local[0]+=p.normal.x; front_local[1]+=p.normal.y; front_local[2]+=p.normal.z; n+=1
print("  世界-侧朝向的面数:", n, " 其局部法线均值:", [round(v/max(n,1),3) for v in front_local])
