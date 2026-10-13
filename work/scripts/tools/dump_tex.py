import bpy, os

def _assets():
    """定位仓库根下的 work/assets，从任何目录运行都能找到。"""
    cands = []
    if "__file__" in globals():
        cands.append(os.path.dirname(os.path.abspath(__file__)))
    cands.append(os.getcwd())
    for c in cands:
        p = os.path.abspath(c)
        while True:
            if os.path.isdir(os.path.join(p, "work", "assets")):
                return os.path.join(p, "work", "assets")
            q = os.path.dirname(p)
            if q == p:
                break
            p = q
    raise RuntimeError("找不到 work/assets，请从仓库目录内运行本脚本")

OUT = _assets()
for im in bpy.data.images:
    if im.size[0]==0: continue
    print("image:", im.name, im.size[:], im.colorspace_settings.name)
    if im.name.startswith("Image_") and im.size[0]>=64:
        p=os.path.join(OUT,"racc_tex_%s.png" % im.name.replace(".","_"))
        im.filepath_raw = p; im.file_format='PNG'
        try:
            im.save(); print("   saved ->", p, os.path.getsize(p))
        except Exception as e: print("   save failed", e)
mats = set()
for o in bpy.data.objects:
    if o.type=='MESH' and o.name in ("head_geo.002","ears_geo"):
        for m in o.data.materials:
            if m: mats.add(m.name)
print("materials in use:", mats)
for mn in mats:
    m = bpy.data.materials[mn]
    if not m.use_nodes: continue
    for n in m.node_tree.nodes:
        if n.type=='TEX_IMAGE':
            print("  %s: TEX %s (img=%s) linked_to=%s" % (mn, n.name, n.image.name if n.image else None,
                  [l.to_node.type+"."+l.to_socket.name for l in n.outputs['Color'].links]))
        if n.type=='VERTEX_COLOR':
            print("  %s: VERTEX_COLOR node present" % mn)

