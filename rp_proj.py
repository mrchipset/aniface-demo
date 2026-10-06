import bpy, os, math, numpy as np
OUT=r"<HOME>\tmp\blender"
ob = bpy.data.objects["head_geo.002"]
me = ob.data
mw = ob.matrix_world.copy()
co = [mw @ v.co for v in me.vertices]
xs=[p.x for p in co]; ys=[p.y for p in co]; zs=[p.z for p in co]
print("head_geo bbox x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]" % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))

img = bpy.data.images.get("redpanda_ref.png") or bpy.data.images.load(os.path.join(OUT,"redpanda_ref.png"), check_existing=True)
W,H = img.size
print("ref:", W, H)

# planar UV from the front (-Y): u <- x, v <- z
uv = me.uv_layers.get("FaceUV") or me.uv_layers.new(name="FaceUV")
uv.active = True; uv.active_render = True
U0,U1 = 0.06, 0.94          # photo u range for the head width
# photo v (from bottom): top-of-fur 0.88, chin 0.06
V_TOP, V_BOT = 0.88, 0.06
Z0, Z1 = min(zs), max(zs)
for poly in me.polygons:
    for li in poly.loop_indices:
        p = co[me.loops[li].vertex_index]
        u = (p.x - min(xs))/(max(xs)-min(xs))
        t = (p.z - Z0)/(Z1 - Z0)
        uv.data[li].uv = (U0 + u*(U1-U0), V_BOT + t*(V_TOP-V_BOT))

mp = bpy.data.materials.get("RPPhoto") or bpy.data.materials.new("RPPhoto")
mp.use_nodes=True; nt=mp.node_tree; nt.nodes.clear()
tex=nt.nodes.new("ShaderNodeTexImage"); tex.image=img
uvn=nt.nodes.new("ShaderNodeUVMap"); uvn.uv_map="FaceUV"
bs=nt.nodes.new("ShaderNodeBsdfPrincipled"); bs.inputs["Roughness"].default_value=0.85
on=nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
nt.links.new(bs.outputs["BSDF"], on.inputs["Surface"])

# keep existing (remapped) material for the rest
base_i = 0
ip = len(me.materials); me.materials.append(mp)
print("materials now:", [m.name for m in me.materials], "| base slot 0 =", me.materials[0].name)

nph=0
for poly in me.polygons:
    wn = (mw.to_3x3().inverted().transposed() @ poly.normal).normalized()
    if wn.y < -0.05:
        poly.material_index = ip; nph += 1
    else:
        poly.material_index = base_i
print("photo polys:", nph, "of", len(me.polygons))

sc=bpy.context.scene
w = bpy.data.worlds.get("PolyHaven studio_kontrast_03")
if w: sc.world = w
cam=sc.camera; cam.data.lens=50
sc.render.resolution_x=560; sc.render.resolution_y=560
sc.render.image_settings.file_format="PNG"; sc.render.image_settings.color_mode="RGB"
cx,cy,cz = 0.0, 0.04, 0.11
def shot(p,loc,rot):
    cam.location=loc; cam.rotation_euler=rot; sc.render.filepath=p
    bpy.ops.render.render(write_still=True); return os.path.getsize(p)
D=1.15
print("front:", shot(os.path.join(OUT,"rp_f.png"), (cx, cy-D, cz+0.02), (math.radians(90),0,0)))
print("3/4  :", shot(os.path.join(OUT,"rp_34.png"), (cx+D*0.7, cy-D*0.7, cz+0.10), (math.radians(80),0,math.radians(45))))
