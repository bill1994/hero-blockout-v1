"""P1c: window width, base band, and fastener reduction.

Three items left over from P1 besides the contact sheet.

1. Window: section 6 P1 asks for ~0.64 of front width. At 1.80 shell width the window
   is 0.5879; it needs 1.1520, i.e. x * 1.0886. The hole is made by a boolean cutter, so
   the cutter, the frame, the glow, the cavity and the noise meshes all have to scale
   together or the frame stops matching its own opening. Scaling is done in WORLD space
   about x = 0, per vertex, so animated objects keep their keys and origins untouched.

2. Base band: section 4.3 measures the base at 0.0444 of body height against the
   reference 0.1576 (0.284 m). Rather than stretching the existing bottom plate (which
   would swallow the feet), a dark band is added that wraps the shell's lower 0.18 m -
   the "charcoal low band" of section 5.2 item 7 - leaving the plate and feet alone.

3. Fasteners: 672 screw faces are spread over the front. Section 5.2 item 9 wants a few
   small flush bolts instead. The old object is removed and 8 flush bolts are generated
   (4 front corners, 4 back), outside the window frame's footprint.

Read-only unless --apply. Runs after v13_p1a_shell.py and v13_p1b_dress.py.

Usage:
    blender --background <p1a scratch.blend> --python qa_v2/v13_p1c_details.py -- \
        [--out <blend>] [--report <json>] [--no-apply]
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


APPLY = "--no-apply" not in argv
OUT = arg("--out", None)
REPORT = arg("--report", None)

WINDOW_FACTOR = 1.0886
WINDOW_PARTS = ["Cutter_Window", "Machine_WindowFrame", "Machine_WindowGlow",
                "Machine_WindowCavity", "Machine_Window",
                "Machine_WindowNoise1", "Machine_WindowNoise2"]

BODY = "Machine_Body"
BAND_NAME = "P1_BaseBand"
BAND_X, BAND_Y = 0.925, 0.825
BAND_Z = (0.10, 0.284)
BAND_MAT = "MAT_Arm_Dark"

SCREWS = "Machine_Screws"
BOLT_R, BOLT_H = 0.018, 0.008
BOLT_MAT = "MAT_Arm_Dark"
BOLT_FRONT_Y = -0.80
BOLT_BACK_Y = 0.80
BOLT_XZ = [(-0.78, 0.30), (0.78, 0.30), (-0.78, 1.70), (0.78, 1.70)]

sc = bpy.context.scene
body = bpy.data.objects.get(BODY)
if body is None:
    raise SystemExit("P1C FATAL: no %s" % BODY)


# ---------------------------------------------------------------- helpers ----
def scale_world_x(obj, factor, pivot=0.0):
    """Scale an object's vertices in world X about `pivot`, leaving keys alone."""
    mw = obj.matrix_world.copy()
    inv = mw.inverted()
    for v in obj.data.vertices:
        w = mw @ v.co
        w.x = pivot + (w.x - pivot) * factor
        v.co = inv @ w
    obj.data.update()


def rounded_rect(hx, hy, r, seg):
    r = max(0.002, min(r, min(hx, hy) - 0.002))
    ix, iy = hx - r, hy - r
    corners = ((ix, iy, 0.0), (-ix, iy, math.pi * 0.5),
               (-ix, -iy, math.pi), (ix, -iy, math.pi * 1.5))
    pts = []
    for cx, cy, a0 in corners:
        for i in range(seg + 1):
            a = a0 + (math.pi * 0.5) * i / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def build_band(bm, hx, hy, z0, z1, r, seg):
    lo = rounded_rect(hx, hy, r, seg)
    vlo = [bm.verts.new((x, y, z0)) for x, y in lo]
    vhi = [bm.verts.new((x, y, z1)) for x, y in lo]
    n = len(vlo)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vlo[i], vlo[j], vhi[j], vhi[i]))
    bm.faces.new(list(reversed(vlo)))
    bm.faces.new(vhi)


def make_band():
    o = bpy.data.objects.get(BAND_NAME)
    if o is not None:
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(BAND_NAME + "_mesh")
    bm = bmesh.new()
    build_band(bm, BAND_X, BAND_Y, BAND_Z[0], BAND_Z[1], 0.22, 6)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(BAND_NAME, me)
    sc.collection.objects.link(o)
    m = bpy.data.materials.get(BAND_MAT)
    if m:
        me.materials.append(m)
    o.parent = body
    o.matrix_parent_inverse = body.matrix_world.inverted()
    return o


def make_bolt(name, x, y, z, normal_y):
    o = bpy.data.objects.get(name)
    if o is not None:
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12,
                          radius1=BOLT_R, radius2=BOLT_R * 0.86, depth=BOLT_H)
    # default axis is +Z; lay it along Y and sink it flush into the face
    for v in bm.verts:
        v.co = Vector((v.co.x, v.co.z, v.co.y))
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.location = (x, y + normal_y * (BOLT_H / 2.0 - 0.001), z)
    m = bpy.data.materials.get(BOLT_MAT)
    if m:
        me.materials.append(m)
    o.parent = body
    o.matrix_parent_inverse = body.matrix_world.inverted()
    return o


# ------------------------------------------------------------ window widen ----
window = {}
for name in WINDOW_PARTS:
    o = bpy.data.objects.get(name)
    if o is None:
        window[name] = "missing"
        continue
    if o.data.users != 1:
        window[name] = "SKIPPED shared mesh (%d users)" % o.data.users
        continue
    before = [round(min((o.matrix_world @ v.co).x for v in o.data.vertices), 4),
              round(max((o.matrix_world @ v.co).x for v in o.data.vertices), 4)]
    if APPLY:
        scale_world_x(o, WINDOW_FACTOR)
    window[name] = {"x_before": before,
                    "x_after": [round(v * WINDOW_FACTOR, 4) for v in before] if APPLY else None}

# -------------------------------------------------------------- base band ----
band = make_band() if APPLY else None

# --------------------------------------------------------------- fasteners ----
screw_faces = None
so = bpy.data.objects.get(SCREWS)
if so is not None:
    screw_faces = len(so.data.polygons)
    if APPLY:
        bpy.data.objects.remove(so, do_unlink=True)

bolts = []
if APPLY:
    for i, (x, z) in enumerate(BOLT_XZ):
        bolts.append(make_bolt("P1_Bolt_F%d" % i, x, BOLT_FRONT_Y, z, -1.0).name)
        bolts.append(make_bolt("P1_Bolt_B%d" % i, x, BOLT_BACK_Y, z, +1.0).name)

out = {
    "blend": os.path.abspath(bpy.data.filepath),
    "applied": APPLY,
    "window_factor": WINDOW_FACTOR,
    "window": window,
    "base_band": {"name": BAND_NAME, "x": BAND_X, "y": BAND_Y, "z": list(BAND_Z),
                  "height": round(BAND_Z[1] - BAND_Z[0], 4),
                  "height_ratio": round((BAND_Z[1] - BAND_Z[0]) / 1.80, 4)},
    "screws": {"removed_faces": screw_faces, "bolts": bolts},
}

print("P1C DETAILS %s" % ("APPLY" if APPLY else "DRY"))
print("  window x * %.4f" % WINDOW_FACTOR)
for k, v in window.items():
    print("    %-22s %s" % (k, v))
print("  base band: z %.3f..%.3f (h=%.3f, %.4f of body height; ref 0.1576)" % (
    BAND_Z[0], BAND_Z[1], BAND_Z[1] - BAND_Z[0], (BAND_Z[1] - BAND_Z[0]) / 1.8))
print("  screws: removed %s faces, added %d bolts" % (screw_faces, len(bolts)))

if REPORT:
    os.makedirs(os.path.dirname(os.path.abspath(REPORT)) or ".", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("WROTE %s" % os.path.abspath(REPORT))

if APPLY:
    dest = os.path.abspath(OUT) if OUT else bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(filepath=dest)
    print("SAVED %s" % dest)
