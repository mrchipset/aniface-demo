import json, struct
p=r"redpanda_head.glb"
d=open(p,'rb').read(); off=12; js=None
while off<len(d):
    cl,ct=struct.unpack("<II",d[off:off+8])
    if ct==0x4E4F534A: js=json.loads(d[off+8:off+8+cl].decode())
    off+=8+cl
print("size: %.2f MB" % (len(d)/1048576))
print("extensionsUsed:", js.get("extensionsUsed"))
print("extensionsRequired:", js.get("extensionsRequired"))
print("nodes:", len(js.get("nodes",[])), "| meshes:", len(js.get("meshes",[])), "| materials:", [m.get("name") for m in js.get("materials",[])])
print("images:", [(i.get("name"), i.get("mimeType")) for i in js.get("images",[])])
print("skins:", len(js.get("skins",[])))
tot=0; names=None
for m in js["meshes"]:
    tn=(m.get("extras") or {}).get("targetNames") or []
    if tn: names=tn; tot=len(tn)
    print("  mesh '%s': %d primitives, %d morphs" % (m.get("name"), len(m["primitives"]), len(tn)))
ARK=set("""eyeBlinkLeft eyeBlinkRight eyeSquintLeft eyeSquintRight eyeWideLeft eyeWideRight eyeLookDownLeft eyeLookDownRight eyeLookInLeft eyeLookInRight eyeLookOutLeft eyeLookOutRight eyeLookUpLeft eyeLookUpRight browDownLeft browDownRight browInnerUp browOuterUpLeft browOuterUpRight cheekPuff cheekSquintLeft cheekSquintRight noseSneerLeft noseSneerRight mouthClose mouthFunnel mouthPucker mouthLeft mouthRight mouthSmileLeft mouthSmileRight mouthFrownLeft mouthFrownRight mouthDimpleLeft mouthDimpleRight mouthStretchLeft mouthStretchRight mouthRollLower mouthRollUpper mouthShrugLower mouthShrugUpper mouthPressLeft mouthPressRight mouthLowerDownLeft mouthLowerDownRight mouthUpperUpLeft mouthUpperUpRight jawOpen jawForward jawLeft jawRight tongueOut""".split())
print("morphs total:", tot)
if names:
    s=set(names)
    print("ARKit matched: %d/52 | missing: %s | extra: %s" % (len(s&ARK), sorted(ARK-s), sorted(s-ARK)))
    print("tongueOut present:", "tongueOut" in s)
