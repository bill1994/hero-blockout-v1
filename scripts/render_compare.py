"""Render comparison shots: Tripo reference (multi-view) vs p19 hero animation.

Usage: blender -b --python render_compare.py -- <target> <outdir>
  target: tripo | p19
"""
import bpy
import sys
import math
import os
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
target = args[0] if args else "tripo"
outdir = args[1] if len(args) > 1 else r"G:\DSHProject\BlenderMcp\renders"
os.makedirs(outdir, exist_ok=True)

FILES = {
    "tripo": r"G:\DSHProject\BlenderMcp\ReferenceModel.blend",
    "p19": r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend",
    "v2": r"G:\DSHProject\BlenderMcp\rebuild_v2.blend",
}

bpy.ops.wm.open_mainfile(filepath=FILES[target])

scene = bpy.context.scene

# drop whatever camera/lights exist, we build our own rig
for ob in list(bpy.data.objects):
    if ob.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(ob, do_unlink=True)

bpy.context.view_layer.update()


def visible_mesh_bbox():
    mn = Vector((1e18, 1e18, 1e18))
    mx = Vector((-1e18, -1e18, -1e18))
    found = False
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        if ob.hide_render:
            continue
        try:
            if not ob.visible_get():
                continue
        except Exception:
            pass
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
        found = True
    if not found:
        raise RuntimeError("no visible mesh")
    return mn, mx


mn, mx = visible_mesh_bbox()
center = (mn + mx) * 0.5
radius = max((mx - mn).length * 0.5, 1e-6)

world = bpy.data.worlds.new("RenderWorld")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.045, 0.048, 0.055, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
scene.world = world


def add_area(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(ob)
    ob.location = loc
    d = center - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


k = radius
add_area("Key", center + Vector((-1.6, -2.0, 2.2)) * k, 300 * k * k, 2.2 * k)
add_area("Fill", center + Vector((2.4, -1.4, 0.6)) * k, 95 * k * k, 3.0 * k, (0.82, 0.88, 1.0))
add_area("Rim", center + Vector((0.4, 2.6, 1.8)) * k, 170 * k * k, 2.0 * k, (1.0, 0.95, 0.88))

cam_data = bpy.data.cameras.new("CompareCam")
cam_data.lens = 55
cam = bpy.data.objects.new("CompareCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def place(dir_vec, dist_mul=2.95):
    d = Vector(dir_vec).normalized()
    cam.location = center + d * radius * dist_mul
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()


scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in {
    e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items
} else 'BLENDER_EEVEE'
scene.render.resolution_x = 900
scene.render.resolution_y = 900
scene.render.film_transparent = False
try:
    scene.eevee.taa_render_samples = 48
except Exception:
    pass
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass

VIEWS = [("34", (1.0, -1.15, 0.62), 2.95)]
if target == "tripo":
    VIEWS += [("front", (0, -1, 0.06), 2.85), ("side", (-1, 0, 0.06), 2.85), ("top", (0, -0.001, 1), 2.7)]
else:
    VIEWS += [("front", (0, -1, 0.04), 2.85), ("side", (-1, 0, 0.04), 2.85)]

FRAMES = [1] if target == "tripo" else [1, 120, 220]

for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    for name, d, mul in VIEWS:
        place(d, mul)
        path = os.path.join(outdir, "%s_f%03d_%s.png" % (target, frame, name))
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print("RENDERED " + path)
