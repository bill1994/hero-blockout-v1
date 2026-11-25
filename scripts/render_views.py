"""Render the fixed five-view A/B sheet for this model.

One contract, one place: orthographic workbench, STUDIO light, MATERIAL colour,
cavity bopth, AA 16, ortho_scale 1.15, 720 px, view centre (-0.0005, 0, 0.377).
That gives 627 px/m (720 / 1.15), which is what the reference views were shot
at, so renders from any stage can be compared pixel for pixel.

Run:
  blender --background --factory-startup --python scripts/render_views.py -- \
      versions/rebuild_v7_s2a.blend renders/ab_s2a s2a
"""

import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CENTER = Vector((-0.0005, 0.0, 0.377))
ORTHO = 1.15
SIZE = 720

VIEWS = {
    "front": (CENTER + Vector((0.0, -3.0, 0.0)), ORTHO),
    "right": (CENTER + Vector((3.0, 0.0, 0.0)), ORTHO),
    "top": (CENTER + Vector((0.0, 0.0, 3.0)), ORTHO),
    "iso": (CENTER + Vector((-1.7, -1.7, 1.35)), ORTHO),
    "armclose": (Vector((-0.30, -0.04, 0.665)) + Vector((-0.8, -1.1, 0.55)), 0.52),
}


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    blend = argv[0] if argv else os.path.join("versions", "rebuild_v7_s2a.blend")
    outdir = argv[1] if len(argv) > 1 else os.path.join("renders", "ab")
    prefix = argv[2] if len(argv) > 2 else "view"
    return blend, outdir, prefix


def setup_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False

    sh = scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_cavity = True
    sh.cavity_type = "BOTH"
    sh.show_object_outline = False
    sh.show_shadows = True
    sh.background_type = "VIEWPORT"
    sh.background_color = (0.05, 0.05, 0.06)
    try:
        scene.display.render_aa = "16"
    except (AttributeError, TypeError):
        pass
    return scene


def add_camera():
    cam_data = bpy.data.cameras.new("AB_Cam")
    cam_data.type = "ORTHO"
    cam = bpy.data.objects.new("AB_Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def shoot(cam, scene, loc, ortho, path):
    cam.location = loc
    direction = CENTER - loc
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.ortho_scale = ortho
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    blend, outdir, prefix = args()
    if not os.path.isabs(blend):
        blend = os.path.join(ROOT, blend)
    if not os.path.isabs(outdir):
        outdir = os.path.join(ROOT, outdir)
    os.makedirs(outdir, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=blend)
    scene = setup_scene()
    cam = add_camera()

    for name, (loc, ortho) in VIEWS.items():
        path = os.path.join(outdir, "%s_%s.png" % (prefix, name))
        shoot(cam, scene, loc, ortho, path)
        print("@@RENDER@@ %s %d B" % (path, os.path.getsize(path)))


main()
