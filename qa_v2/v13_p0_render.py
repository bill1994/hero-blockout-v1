"""P0 acceptance renders: front / right / back / top of the machine.

Loads the given .blend read-only, builds a throwaway orthographic camera rig and
a neutral three-point light setup, renders four views, and never saves the file.

Usage:
    blender --background <blend> --python qa_v2/v13_p0_render.py -- \
        --outdir review/v13 --prefix p0 [--frame 1]
"""

import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUTDIR = os.path.abspath(arg("--outdir", "review/v13"))
PREFIX = arg("--prefix", "p0")
FRAME = int(arg("--frame", "1"))
RES = int(arg("--res", "900"))
os.makedirs(OUTDIR, exist_ok=True)

sc = bpy.context.scene
sc.frame_set(FRAME)

# ---------------------------------------------------------------- render setup
_engines = {e.identifier for e in
            bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
    if candidate in _engines:
        sc.render.engine = candidate
        break
print("ENGINE %s" % sc.render.engine)

sc.render.resolution_x = RES
sc.render.resolution_y = RES
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
try:
    sc.eevee.taa_render_samples = 48
except AttributeError:
    pass
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"

# neutral studio world so silhouettes read against a flat backdrop
world = bpy.data.worlds.new("P0_AuditWorld")
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.055, 0.058, 0.062, 1.0)
bg.inputs[1].default_value = 1.0
sc.world = world

# ------------------------------------------------------------- scene bounds
dg = bpy.context.evaluated_depsgraph_get()
lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for o in sc.objects:
    if o.type != "MESH" or o.hide_render:
        continue
    ev = o.evaluated_get(dg)
    for c in ev.bound_box:
        w = ev.matrix_world @ Vector(c)
        for i in range(3):
            lo[i] = min(lo[i], w[i])
            hi[i] = max(hi[i], w[i])

center = (lo + hi) / 2.0
size = hi - lo
span = max(size.x, size.y, size.z) * 1.15

# Framing must be identical across frames when two renders are compared (loop
# endpoint checks). Allow pinning it explicitly; otherwise auto-frame.
_pin_span = arg("--span")
_pin_center = arg("--center")
if _pin_span:
    span = float(_pin_span)
if _pin_center:
    cx, cy, cz = [float(v) for v in _pin_center.split(",")]
    center = Vector((cx, cy, cz))
    print("PINNED center=%s span=%.4f" % (tuple(round(v, 4) for v in center), span))

print("BOUNDS lo=%s hi=%s center=%s span=%.4f"
      % (tuple(round(v, 4) for v in lo), tuple(round(v, 4) for v in hi),
         tuple(round(v, 4) for v in center), span))

# --------------------------------------------------------------- light rig
def add_sun(name, rot_deg, energy):
    d = bpy.data.lights.new(name, "SUN")
    d.energy = energy
    d.angle = math.radians(12)
    ob = bpy.data.objects.new(name, d)
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    sc.collection.objects.link(ob)
    return ob


def add_area(name, loc, rot_deg, energy, size_):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.size = size_
    ob = bpy.data.objects.new(name, d)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    sc.collection.objects.link(ob)
    return ob


for o in list(sc.objects):
    if o.type == "LIGHT" and o.name.startswith(("P0_",)):
        bpy.data.objects.remove(o, do_unlink=True)

add_sun("P0_Key", (52, 0, 35), 4.0)
add_area("P0_Fill", (center.x - span, center.y - span, center.z + span * 0.6),
         (65, 0, -45), 320.0, span)
add_area("P0_Rim", (center.x + span, center.y + span * 0.8, center.z + span * 0.8),
         (60, 0, 135), 260.0, span)

# ----------------------------------------------------------------- cameras
def add_cam(name, loc, rot_deg, ortho_scale):
    cd = bpy.data.cameras.new(name)
    cd.type = "ORTHO"
    cd.ortho_scale = ortho_scale
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    sc.collection.objects.link(ob)
    return ob


D = span * 3.0  # far enough that ortho clipping is never an issue
views = [
    ("front", (center.x, center.y - D, center.z), (90, 0, 0)),
    ("right", (center.x + D, center.y, center.z), (90, 0, 90)),
    ("back", (center.x, center.y + D, center.z), (90, 0, 180)),
    ("top", (center.x, center.y, center.z + D), (0, 0, 0)),
]

written = []
for idx, (name, loc, rot) in enumerate(views):
    cam = add_cam("P0_Cam_%s" % name, loc, rot, span)
    sc.camera = cam
    path = os.path.join(OUTDIR, "%s_%s.png" % (PREFIX, name))
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if os.path.exists(path):
        written.append((name, path, os.path.getsize(path)))

# restore nothing on disk - this script never saves the blend
for name, path, sz in written:
    print("RENDERED %-6s %s  %d bytes" % (name, path, sz))

report = {
    "blend": bpy.data.filepath,
    "frame": FRAME,
    "bounds_lo": [round(v, 4) for v in lo],
    "bounds_hi": [round(v, 4) for v in hi],
    "span": round(span, 4),
    "renders": [{"view": n, "path": p, "bytes": s} for n, p, s in written],
}
result = report
print("REPORT %r" % (report,))
