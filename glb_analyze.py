import json, struct, os
from collections import defaultdict
p = r"<HOME>\tmp\blender\aniface_head.glb"
data = open(p,'rb').read()
magic, ver, length = struct.unpack("<III", data[:12])
off=12; js=None
while off < len(data):
    clen, ctype = struct.unpack("<II", data[off:off+8])
    if ctype == 0x4E4F534A: js = json.loads(data[off+8:off+8+clen].decode("utf-8"))
    off += 8+clen
print("file size: %.1f MB" % (len(data)/1048576))
print("meshes:", len(js.get("meshes",[])), "| nodes:", len(js.get("nodes",[])), "| materials:", len(js.get("materials",[])), "| images:", len(js.get("images",[])))
print("extensionsUsed:", js.get("extensionsUsed"))
print("extensionsRequired:", js.get("extensionsRequired"))
tot = defaultdict(int)
for m in js["meshes"]:
    for pr in m["primitives"]:
        for k,acc in pr["attributes"].items():
            a=js["accessors"][acc]; tot[k]+= a["count"]*({"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}.get(a["type"],3))*4
        nt=len(pr.get("targets",[]))
        for t in pr.get("targets",[]):
            for k,acc in t.items():
                a=js["accessors"][acc]; tot["MORPH_"+k]+= a["count"]*({"VEC3":3,"VEC4":4}.get(a["type"],3))*4
        if "indices" in pr:
            a=js["accessors"][pr["indices"]]; tot["INDICES"]+= a["count"]*4
print("mesh data breakdown (MB):")
for k,v in sorted(tot.items(), key=lambda x:-x[1]):
    print("   %-16s %8.2f" % (k, v/1048576))
print("   %-16s %8.2f" % ("TOTAL", sum(tot.values())/1048576))
for i,im in enumerate(js.get("images",[])):
    bv=js["bufferViews"][im["bufferView"]]
    print("image[%d] %s %.2f MB" % (i, im.get("mimeType"), bv["byteLength"]/1048576))
print("morph target count per primitive:", [len(pr.get("targets",[])) for m in js["meshes"] for pr in m["primitives"]])
mn = js["meshes"][0]
tn = (mn.get("extras") or {}).get("targetNames")
print("targetNames on mesh[0]:", (tn[:6] if tn else None))
