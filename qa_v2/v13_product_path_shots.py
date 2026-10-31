"""Visual evidence for the product-path gate.

Renders the scene's own camera (Cam_Hero) at the frames the gate complains about,
so "the product floats" can be seen instead of trusted. Read-only: builds nothing
persistent, never saves the .blend.

Usage:
    blender --background <blend> --python qa_v2/v13_product_path_shots.py -- \
        --outdir review/v13 --prefix gate --frames 289,294,300 [--res 900]
"""

import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUTDIR = os.path.abspath(arg("--outdir", "review/v13"))
PREFIX = arg("--prefix", "gate")
FRAMES = [int(f) for f in arg("--frames", "289,294,300").split(",")]
RES = int(arg("--res", "900"))
CAM = arg("--cam", "Cam_Hero")
os.makedirs(OUTDIR, exist_ok=True)

sc = bpy.context.scene

_engines = {e.identifier for e in
            bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    if candidate in _engines:
        sc.render.engine = candidate
        break

sc.render.resolution_x = RES
sc.render.resolution_y = RES
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
try:
    sc.eevee.taa_render_samples = 32
except AttributeError:
    pass
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"

cam = bpy.data.objects.get(CAM) or sc.camera
if cam is None:
    raise SystemExit("no camera: %r and scene.camera is unset" % CAM)
sc.camera = cam
print("CAMERA %s  lens %.1f  loc %s" % (
    cam.name, cam.data.lens if cam.data else -1,
    [round(v, 3) for v in cam.matrix_world.translation]))

for f in FRAMES:
    sc.frame_set(f)
    path = os.path.join(OUTDIR, "%s_f%04d.png" % (PREFIX, f))
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("SHOT f%d -> %s" % (f, path))

print("DONE %d shots" % len(FRAMES))
