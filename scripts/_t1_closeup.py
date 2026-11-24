"""T1 close-up QA renders: front-ortho detail of the pill and the nameplate.
Temporary camera + light only; never saved over rebuild_v2.blend."""
import bpy
import math
import os

ROOT = r"G:\DSHProject\BlenderMcp"
OUT = os.path.join(ROOT, "renders", "insp")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "rebuild_v2.blend"))
sc = bpy.context.scene
sc.frame_set(1)
_eng = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items}
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in _eng else 'BLENDER_EEVEE'
sc.render.resolution_x = 760
sc.render.resolution_y = 760
sc.render.film_transparent = False
try:
    sc.eevee.taa_render_samples = 48
except Exception:
    pass

cam_data = bpy.data.cameras.new("TMP_QACam")
cam_data.type = 'ORTHO'
cam = bpy.data.objects.new("TMP_QACam", cam_data)
sc.collection.objects.link(cam)
cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
sc.camera = cam

ld = bpy.data.lights.new("TMP_QALight", 'AREA')
ld.energy = 55.0
ld.size = 2.6
ld.color = (1.0, 1.0, 1.0)
lo = bpy.data.objects.new("TMP_QALight", ld)
sc.collection.objects.link(lo)
lo.location = (-0.4, -3.2, 1.7)
lo.rotation_euler = (math.radians(80.0), 0.0, 0.0)

SHOTS = [
    ("qa_front_pill", (-0.30, -3.6, 0.46), 1.20),
    ("qa_front_plate", (-0.60, -3.6, 2.42), 0.58),
    ("qa_front_full", (-0.05, -3.6, 1.45), 2.70),
]

for tag, loc, scale in SHOTS:
    cam.location = loc
    cam_data.ortho_scale = scale
    sc.render.filepath = os.path.join(OUT, tag + ".png")
    bpy.ops.render.render(write_still=True)
    print("QA WROTE %s ortho=%.2f" % (sc.render.filepath, scale))

# perspective 3/4 close-up of the lower-left front, matches how the detail is seen
cam_data.type = 'PERSP'
cam_data.lens = 85.0
cam.location = (-1.85, -2.55, 1.05)
cam.rotation_euler = (math.radians(78.5), 0.0, math.radians(-36.0))
sc.render.filepath = os.path.join(OUT, "qa_34_pill.png")
bpy.ops.render.render(write_still=True)
print("QA WROTE %s" % sc.render.filepath)

# perspective 3/4 close-up of the upper-left front for the nameplate
cam.location = (-2.05, -2.35, 2.75)
cam.rotation_euler = (math.radians(86.0), 0.0, math.radians(-40.0))
sc.render.filepath = os.path.join(OUT, "qa_34_plate.png")
bpy.ops.render.render(write_still=True)
print("QA WROTE %s" % sc.render.filepath)

print("QA DONE (temporary rig not saved)")
