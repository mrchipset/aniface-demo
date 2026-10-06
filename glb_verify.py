import json, struct, os
p=r"<HOME>\tmp\blender\aniface_head.glb"
d=open(p,'rb').read(); off=12; js=None
while off<len(d):
    cl,ct=struct.unpack("<II",d[off:off+8])
    if ct==0x4E4F534A: js=json.loads(d[off+8:off+8+cl].decode())
    off+=8+cl
print("size: %.2f MB" % (len(d)/1048576))
print("generator:", js["asset"].get("generator"))
print("extensionsUsed:", js.get("extensionsUsed"))
print("extensionsRequired:", js.get("extensionsRequired"))
print("nodes:", len(js.get("nodes",[])), "meshes:", len(js.get("meshes",[])), "primitives:",
      sum(len(m["primitives"]) for m in js["meshes"]))
print("skins:", len(js.get("skins",[])), "animations:", len(js.get("animations",[])))
print("materials:", [m.get("name") for m in js.get("materials",[])])
names = (js["meshes"][0].get("extras") or {}).get("targetNames")
print("morph targetNames (%d):" % (len(names) if names else 0))
print("  ", names)
ARK=set("""eyeBlinkLeft eyeBlinkRight eyeSquintLeft eyeSquintRight eyeWideLeft eyeWideRight eyeLookDownLeft eyeLookDownRight eyeLookInLeft eyeLookInRight eyeLookOutLeft eyeLookOutRight eyeLookUpLeft eyeLookUpRight browDownLeft browDownRight browInnerUp browOuterUpLeft browOuterUpRight cheekPuff cheekSquintLeft cheekSquintRight noseSneerLeft noseSneerRight mouthClose mouthFunnel mouthPucker mouthLeft mouthRight mouthSmileLeft mouthSmileRight mouthFrownLeft mouthFrownRight mouthDimpleLeft mouthDimpleRight mouthStretchLeft mouthStretchRight mouthRollLower mouthRollUpper mouthShrugLower mouthShrugUpper mouthPressLeft mouthPressRight mouthLowerDownLeft mouthLowerDownRight mouthUpperUpLeft mouthUpperUpRight jawOpen jawForward jawLeft jawRight tongueOut""".split())
if names:
    s=set(names)
    print("ARKit matched: %d/52 | missing: %s | extra: %s" % (len(s&ARK), sorted(ARK-s), sorted(s-ARK)))
# node bounds
n=js["nodes"][0]
print("node:", n.get("name"), "| children:", len(n.get("children",[])))
