import bpy
print("=== 逐材质检查贴图节点的连接 ===")
for m in bpy.data.materials:
    if not m or not m.use_nodes or not m.name.startswith("MAT_Racoon"): continue
    print("--", m.name)
    for nd in m.node_tree.nodes:
        if nd.type != 'TEX_IMAGE': continue
        outs = []
        for l in nd.outputs['Color'].links:
            outs.append(l.to_node.name + "." + l.to_socket.name)
        for l in nd.outputs['Alpha'].links:
            outs.append("Alpha->" + l.to_node.name + "." + l.to_socket.name)
        print("     node=%-12s image=%-18s -> %s" % (nd.name, nd.image.name if nd.image else None, outs or "(未连接)"))
