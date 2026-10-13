import json, struct, os, sys

def _repo_root(start=None):
    p = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isdir(os.path.join(p, "work", "assets")):
            return p
        q = os.path.dirname(p)
        if q == p:
            raise RuntimeError("找不到仓库根（应包含 work/assets）")
        p = q

def _assets_dir():
    cands = []
    try:
        cands.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass
    cands.append(os.getcwd())
    for c in cands:
        try:
            return os.path.join(_repo_root(c), "work", "assets")
        except RuntimeError:
            continue
    raise RuntimeError("找不到 work/assets，请从仓库目录内运行本脚本")

# 默认校验 work/assets/redpanda_head.glb，也可传入任意 GLB 路径
p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_assets_dir(), "redpanda_head.glb")
d=open(p,'rb').read(); off=12; js=None
while off<len(d):
    cl,ct=struct.unpack("<II",d[off:off+8])
    if ct==0x4E4F534A: js=json.loads(d[off+8:off+8+cl].decode())
    off+=8+cl
print("file : %s" % os.path.basename(p))
print("size : %.2f MB" % (len(d)/1048576))
print("ext  : used=%s required=%s" % (js.get("extensionsUsed"), js.get("extensionsRequired")))
print("nodes=%d meshes=%d materials=%s" % (len(js.get("nodes",[])), len(js.get("meshes",[])),
      [m.get("name") for m in js.get("materials",[])]))
print("images: %s" % [i.get("name") for i in js.get("images",[])])
print("skins=%d animations=%d" % (len(js.get("skins",[])), len(js.get("animations",[]))))
names=None
for m in js["meshes"]:
    tn=(m.get("extras") or {}).get("targetNames") or []
    print("  mesh '%s': %d prims, %d morphs" % (m.get("name"), len(m["primitives"]), len(tn)))
    if tn: names=tn
ARK=set("""eyeBlinkLeft eyeBlinkRight eyeSquintLeft eyeSquintRight eyeWideLeft eyeWideRight eyeLookDownLeft eyeLookDownRight eyeLookInLeft eyeLookInRight eyeLookOutLeft eyeLookOutRight eyeLookUpLeft eyeLookUpRight browDownLeft browDownRight browInnerUp browOuterUpLeft browOuterUpRight cheekPuff cheekSquintLeft cheekSquintRight noseSneerLeft noseSneerRight mouthClose mouthFunnel mouthPucker mouthLeft mouthRight mouthSmileLeft mouthSmileRight mouthFrownLeft mouthFrownRight mouthDimpleLeft mouthDimpleRight mouthStretchLeft mouthStretchRight mouthRollLower mouthRollUpper mouthShrugLower mouthShrugUpper mouthPressLeft mouthPressRight mouthLowerDownLeft mouthLowerDownRight mouthUpperUpLeft mouthUpperUpRight jawOpen jawForward jawLeft jawRight tongueOut""".split())
if names:
    s=set(names)
    print("ARKit: %d/52  missing=%s  extra=%s" % (len(s&ARK), sorted(ARK-s), sorted(s-ARK)))
