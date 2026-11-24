"""T1b close-up QA: name badge + outlet end stop. Temporary rig, never saved."""
import bpy
import math
import os
from mathutils import Vector

ROOT = r"G:\DSHProject\BlenderMcp"
OUT = os.path.join(ROOT, "renders", "insp")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "rebuild_v2.blend"))
sc = bpy.context.scene
sc.frame_set(1)
_eng = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items}
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in _eng else 'BLENDER_EEVEE'
sc.render.resolution_x = 900
sc.render.resolution_y = 700
sc.render.film_transparent = False
try:
    sc.eevee.taa_render_samples = 64
except Exception:
    pass
try:
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception:
    pass

cam_data = bpy.data.cameras.new("TMP_QACam")
cam = bpy.data.objects.new("TMP_QACam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam


def area(name, loc, rot, energy, size):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    sc.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


area("TMP_Key", (-1.6, -3.0, 3.6), (math.radians(58), 0, math.radians(-26)), 320, 2.6)
area("TMP_Fill", (2.6, -2.4, 1.9), (math.radians(80), 0, math.radians(46)), 120, 3.0)
area("TMP_Rim", (0.6, 2.6, 3.2), (math.radians(126), 0, math.radians(190)), 160, 2.4)


def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# tag, kind, camera location, aimed-at target, ortho_scale, lens
SHOTS = [
    ("qa_plate_front", 'ORTHO', (-0.420, -3.60, 2.564), (-0.420, 0.0, 2.564), 0.84, 55),
    ("qa_plate_34", 'PERSP', (-1.70, -2.10, 2.980), (-0.420, -0.80, 2.564), 0.84, 85),
    ("qa_chute_front", 'ORTHO', (2.30, -3.60, 1.200), (2.30, 0.0, 1.200), 1.80, 55),
    ("qa_chute_34", 'PERSP', (4.05, -2.30, 2.150), (2.55, 0.0, 1.150), 1.80, 60),
    ("qa_full_front", 'ORTHO', (0.45, -6.00, 1.560), (0.45, 0.0, 1.560), 4.60, 55),
]

for tag, kind, loc, target, oscale, lens in SHOTS:
    cam_data.type = kind
    cam_data.ortho_scale = oscale
    cam_data.lens = lens
    cam.location = loc
    aim(cam, target)
    sc.render.filepath = os.path.join(OUT, tag + ".png")
    bpy.ops.render.render(write_still=True)
    print("QA WROTE %s" % sc.render.filepath)

print("QA DONE (temporary rig not saved)")
