import json, struct, os, math
p = r"redpanda_head.glb"
d=open(p,'rb').read(); off=12; js=None; bin=None
while off<len(d):
    cl,ct=struct.unpack("<II",d[off:off+8])
    ch=d[off+8:off+8+cl]
    if ct==0x4E4F534A: js=json.loads(ch.decode())
    off+=8+cl
print("=== 节点 ===")
for i,n in enumerate(js["nodes"]):
    print("  [%d] name=%-16s mesh=%s children=%s" % (i, n.get("name"), n.get("mesh"), n.get("children")))
    for k in ("translation","rotation","scale","matrix"):
        if k in n: print("       %s = %s" % (k, [round(x,5) for x in n[k]]))
print("\n=== 网格 POSITION 的局部包围盒（accessor min/max）===")
for m in js["meshes"]:
    for pr in m["primitives"]:
        acc = js["accessors"][pr["attributes"]["POSITION"]]
        print("  %-16s min=%s max=%s" % (m.get("name"),
              [round(v,4) for v in acc.get("min",[])], [round(v,4) for v in acc.get("max",[])]))
print("\n=== 结论 ===")
print("  若节点无 rotation 且 POSITION 的 min/max 如上述，则网格局部坐标即最终坐标。")
