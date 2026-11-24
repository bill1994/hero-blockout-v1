import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"G:\DSHProject\BlenderMcp\export\hero_v2.glb")
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
v = t = 0
for ob in meshes:
    me = ob.data
    v += len(me.vertices)
    t += sum(len(p.vertices) - 2 for p in me.polygons)
acts = list(bpy.data.actions)
anims = [a for a in acts if a.name != "CubeAction"]
print("VAL meshes=%d verts=%d tris=%d materials=%d images=%d actions=%d" % (
    len(meshes), v, t, len(bpy.data.materials), len(bpy.data.images), len(acts)))
names = sorted(a.name for a in acts)
print("VAL actions=" + ", ".join(names[:24]))
for a in acts[:3]:
    try:
        print("VAL rng %-28s %s" % (a.name, [round(x,1) for x in a.frame_range]))
    except Exception as ex:
        print("VAL rng ERR", ex)
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE']
print("VAL armatures=%d" % len(arm))