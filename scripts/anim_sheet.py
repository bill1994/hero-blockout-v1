"""Animation contact sheet for rebuild_v2.blend.

Renders a fixed 3/4 view at N frames spread across the full 1..327 range and
stitches them into a single grid image, so the whole grab-and-drop cycle can be
reviewed at a glance.

Usage:
  blender -b --python scripts/anim_sheet.py -- <outdir> [cols]

Always pass an ABSOLUTE outdir: relative paths silently fail to write.
"""
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
OUTDIR = args[0] if args else r"G:\DSHProject\BlenderMcp\renders\anim"
COLS = int(args[1]) if len(args) > 1 else 4

BLEND = r"G:\DSHProject\BlenderMcp\rebuild_v2.blend"
FRAMES = [1, 46, 91, 136, 181, 226, 271, 327]
SIZE = 600

os.makedirs(OUTDIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND)
scene = bpy.context.scene

# The authoring file keeps a few parts on the outliner eye (hide_set), which is
# viewport-only but still makes visible_get() lie. Clear it so the framing bbox
# sees the real silhouette.
for ob in bpy.data.objects:
    if ob.type == 'MESH' and not ob.hide_render and not ob.hide_viewport:
        if ob.hide_get():
            ob.hide_set(False)

for ob in list(bpy.data.objects):
    if ob.type in {'CAMERA', 'LIGHT'}:
        bpy.data.objects.remove(ob, do_unlink=True)
bpy.context.view_layer.update()


def visible_mesh_bbox():
    mn = Vector((1e18, 1e18, 1e18))
    mx = Vector((-1e18, -1e18, -1e18))
    found = False
    for ob in scene.objects:
        if ob.type != 'MESH' or ob.hide_render:
            continue
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

world = bpy.data.worlds.new("SheetWorld")
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

cam_data = bpy.data.cameras.new("SheetCam")
cam_data.lens = 55
cam = bpy.data.objects.new("SheetCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

d = Vector((1.0, -1.15, 0.62)).normalized()
cam.location = center + d * radius * 3.05
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()

engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items}
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
scene.render.resolution_x = SIZE
scene.render.resolution_y = SIZE
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
try:
    scene.eevee.taa_render_samples = 48
except Exception:
    pass
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass

tiles = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    path = os.path.join(OUTDIR, "anim_f%03d.png" % frame)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED " + path)
    tiles.append(path)

# --- stitch with numpy (no PIL in this environment) ----------------------
rows = (len(tiles) + COLS - 1) // COLS
sheet = np.zeros((rows * SIZE, COLS * SIZE, 4), dtype=np.float32)
for i, path in enumerate(tiles):
    img = bpy.data.images.load(path)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
    r, c = divmod(i, COLS)
    # Blender image data is bottom-up; place tiles accordingly.
    top = (rows - 1 - r) * SIZE
    sheet[top:top + SIZE, c * SIZE:(c + 1) * SIZE] = px
    bpy.data.images.remove(img)

out = bpy.data.images.new("anim_sheet", width=COLS * SIZE, height=rows * SIZE, alpha=True)
out.pixels = sheet.ravel().tolist()
out.filepath_raw = os.path.join(os.path.dirname(OUTDIR.rstrip("\\/")), "anim_sheet.png")
out.file_format = 'PNG'
out.save()
print("SHEET " + out.filepath_raw)
