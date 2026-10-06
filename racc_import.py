import bpy, os
OUT=r"<HOME>\tmp\blender"
# remove previous raccoon parts
for o in list(bpy.data.objects):
    if o.name.startswith(("head_geo","ears_geo","hair_geo","tufts_geo","raccoon_head")):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
before={o.name for o in bpy.data.objects}
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT,"raccoon_head_small.glb"))
new=[o for o in bpy.data.objects if o.name not in before]
print("imported:", [o.name for o in new])
import mathutils
for o in new:
    if o.type=='MESH':
        c=[o.matrix_world @ mathutils.Vector(b) for b in o.bound_box]
        ctr=[round((min(p[i] for p in c)+max(p[i] for p in c))/2,3) for i in range(3)]
        sz=[round(max(p[i] for p in c)-min(p[i] for p in c),3) for i in range(3)]
        sk=o.data.shape_keys
        print("  %-14s verts=%5d polys=%5d  center=%s size=%s  shapekeys=%d  mats=%s" % (
            o.name, len(o.data.vertices), len(o.data.polygons), ctr, sz,
            len(sk.key_blocks) if sk else 0, [m.name if m else None for m in o.data.materials]))
        if sk:
            names=[k.name for k in sk.key_blocks]
            print("      keys:", names[:6], "...", names[-3:], "(total %d)" % len(names))
    else:
        print("  %-14s type=%s loc=%s" % (o.name, o.type, [round(v,3) for v in o.location]))
