"""P1a: rebuild Machine_Body from a 1.16-half-width box to a 0.90 rounded shape,
re-target the outlet cutter, add the three junction pieces, re-seat the side panels.

Why a rebuild and not a scale: the body is an 8-vertex box whose silhouette comes from
two EXACT booleans (OutletCut, WindowCut) and a 0.012 bevel. Scaling the base mesh in X
leaves the cutters where they were, so the outlet would stop being cut at all and the
window would land off-centre. The base mesh is replaced outright and the outlet cutter is
moved with the new right face.

Shape: rounded box, built as rings. Plan outline is a rounded rectangle (superellipse-ish
corner radius R_XY); vertical faces get a fillet of radius R_Z at top and bottom. This is
the section 8 "bevel + weighted normals" branch of the design doc, chosen because the
existing asset already ships a Bevel + Smooth-by-Angle stack and a boolean-driven shell,
and because a rebuilt section can be re-derived from parameters if P2 needs the window
enlarged.

Junction pieces (section 12 Q1): shoulder bay bridges the 0.26 gap the narrowed left face
leaves to the arm root; chute seat sleeves the outlet opening out to the chute mouth at
x = 1.16 (which stays frozen); the hopper seat is the existing top plate narrowed to the
new body width. All three parent to Machine_Body so they inherit its animated wobble.

Never saves over the input: pass --out to a scratch path.

Usage:
    blender --background <blend> --python qa_v2/v13_p1a_shell.py -- \
        --out <scratch.blend> [--dry-run] [--half-x 0.90] [--r-xy 0.20] [--r-z 0.10]
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


OUT = arg("--out", None)
DRY = "--dry-run" in argv
HALF_X = float(arg("--half-x", "0.90"))
R_XY = float(arg("--r-xy", "0.20"))
R_Z = float(arg("--r-z", "0.10"))
CORNER_SEG = int(arg("--corner-seg", "5"))
FILLET_STEPS = int(arg("--fillet-steps", "3"))

BODY = "Machine_Body"
CUT_OUTLET = "Cutter_Outlet"

sc = bpy.context.scene
sc.frame_set(1)
body = bpy.data.objects[BODY]

old = {
    "half_x": round(max(abs(v) for v in (body.data.vertices[i].co.x
                                         for i in range(len(body.data.vertices)))), 4),
    "base_verts": len(body.data.vertices),
    "modifiers": [m.name for m in body.modifiers],
}
mat = bpy.data.materials.get("MAT_Body")


# ------------------------------------------------------------ mesh helpers ----
def rounded_rect(hx, hy, r, seg):
    """Perimeter points of a rounded rectangle, CCW."""
    r = max(0.004, min(r, min(hx, hy) - 0.004))
    ix, iy = hx - r, hy - r
    corners = ((ix, iy, 0.0), (-ix, iy, math.pi * 0.5),
               (-ix, -iy, math.pi), (ix, -iy, math.pi * 1.5))
    pts = []
    for cx, cy, a0 in corners:
        for i in range(seg + 1):
            a = a0 + (math.pi * 0.5) * i / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def build_rounded_box(bm, hx, hy, hz, r_xy, r_z, seg, steps):
    """Rings from bottom to top, with quarter-round fillets at both z ends."""
    rings = []

    def ring(z, inset):
        pts = rounded_rect(hx - inset, hy - inset, max(0.004, r_xy - inset), seg)
        vs = [bm.verts.new((x, y, z)) for x, y in pts]
        rings.append(vs)

    r_z = max(0.004, min(r_z, hz * 0.45))
    ring(-hz, r_z)
    for i in range(1, steps + 1):
        h = r_z * i / steps
        t = r_z - math.sqrt(max(0.0, r_z * r_z - (r_z - h) ** 2))
        ring(-hz + h, t)
    for i in range(steps, 0, -1):
        h = r_z * i / steps
        t = r_z - math.sqrt(max(0.0, r_z * r_z - (r_z - h) ** 2))
        ring(hz - h, t)
    ring(hz, r_z)

    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return rings


# ------------------------------------------------------------ rebuild body ----
me = body.data
bm = bmesh.new()
bm.from_mesh(me)
bm.clear()
# local space: the body's matrix has z translation +1.0; keep the local box as-is
local_hz = 0.90
build_rounded_box(bm, HALF_X, 0.80, local_hz, R_XY, R_Z, CORNER_SEG, FILLET_STEPS)
bm.to_mesh(me)
bm.free()
me.update()

new_base_verts = len(me.vertices)

# ------------------------------------------------------- move outlet cutter ----
cutter = bpy.data.objects.get(CUT_OUTLET)
cutter_shift = None
if cutter is not None:
    old_cx = cutter.matrix_world.translation.x
    dx = HALF_X - 1.16          # -0.26
    cutter.location.x += dx
    cutter_shift = {"from": round(old_cx, 4), "to": round(cutter.location.x, 4),
                    "dx": round(dx, 4)}


# --------------------------------------------------------- junction pieces ----
def make_piece(name, center, half, r_xy, r_z, parent=body):
    o = bpy.data.objects.get(name)
    if o is not None:
        bpy.data.objects.remove(o, do_unlink=True)
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm2 = bmesh.new()
    build_rounded_box(bm2, half[0], half[1], half[2], r_xy, r_z,
                      CORNER_SEG, FILLET_STEPS)
    bm2.to_mesh(mesh)
    bm2.free()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(o)
    o.location = Vector(center)
    if mat:
        o.data.materials.append(mat)
    if parent is not None:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


# shoulder bay: must reach past the arm mount's inner end (Arm_Mount ends at x -1.18)
bay = make_piece("P1_ShoulderBay", (-1.05, 0.0, 1.00), (0.15, 0.50, 0.35), 0.10, 0.06)

# chute seat: sleeve from the new right face out to the frozen chute mouth at x=1.16
seat = make_piece("P1_ChuteSeat", (1.03, 0.0, 0.975), (0.13, 0.74, 0.535), 0.10, 0.05)

# open the seat to the same opening the body's outlet cut makes (y +-0.62, z 0.52..1.43)
seat_cutter = bpy.data.objects.get("P1_Cutter_SeatOpen")
if seat_cutter is not None:
    bpy.data.objects.remove(seat_cutter, do_unlink=True)
cmesh = bpy.data.meshes.new("P1_Cutter_SeatOpen_mesh")
cbm = bmesh.new()
bmesh.ops.create_cube(cbm, size=1.0)
cbm.to_mesh(cmesh)
cbm.free()
seat_cutter = bpy.data.objects.new("P1_Cutter_SeatOpen", cmesh)
bpy.context.scene.collection.objects.link(seat_cutter)
seat_cutter.location = (1.03, 0.0, 0.975)
# bmesh create_cube(size=1.0) is a unit cube, so scale == full dimension.
# Opening must match the body's outlet cut: y +-0.62, z 0.52..1.43.
seat_cutter.scale = (0.50, 1.24, 0.91)
seat_cutter.hide_render = True
seat_cutter.hide_viewport = True
seat_cutter.display_type = "WIRE"
b = seat.modifiers.new("SeatOpen", "BOOLEAN")
b.operation = "DIFFERENCE"
b.solver = "EXACT"
b.object = seat_cutter

# --------------------------------------------------------- re-seat panels ----
reseated = {}
dx_face = 1.16 - HALF_X      # 0.26
for name, sign in (("Machine_Panel_L", +1.0),
                   ("Machine_Panel_R_Top", -1.0),
                   ("Machine_Panel_R_SideF", -1.0),
                   ("Machine_Panel_R_SideB", -1.0)):
    o = bpy.data.objects.get(name)
    if o is None:
        continue
    before = round(o.location.x, 4)
    o.location.x += sign * dx_face
    reseated[name] = {"from": before, "to": round(o.location.x, 4)}

# top plate under the hopper: narrow in x only
top = bpy.data.objects.get("Machine_Panel_Top")
if top is not None:
    sx = (HALF_X + 0.04) / 1.20
    top.scale.x = round(sx, 5)
    reseated["Machine_Panel_Top"] = {"scale_x": round(sx, 5)}

# ------------------------------------------------------- narrow base + feet ----
# The base was 2.40 wide against a 1.80 shell; it would hang 0.3 out each side.
# Scale the mesh in local x about the origin rather than the object, because the
# base's location is animated (its x is in the loop-endpoint list).
narrowed = {}
for name in ("Machine_Base", "Machine_Feet"):
    o = bpy.data.objects.get(name)
    if o is None:
        continue
    if o.data.users != 1:
        narrowed[name] = "SKIPPED shared mesh (%d users)" % o.data.users
        continue
    s = HALF_X / 1.20
    for v in o.data.vertices:
        v.co.x *= s
    o.data.update()
    narrowed[name] = {"mesh_x_scale": round(s, 5)}

# --------------------------------------------------- protrusion audit ----
# Anything still reaching outside the new shell in x, that is not supposed to.
EXEMPT = {"Machine_Chute", "Machine_OutputChute", "Machine_Detail",
          "Cutter_Outlet", "Cutter_Window", "P1_Cutter_SeatOpen"}
outsiders = []
dg0 = bpy.context.evaluated_depsgraph_get()
for o in bpy.data.objects:
    if o.type != "MESH" or o.name in EXEMPT:
        continue
    if o.name.startswith("Arm_") or o.name.startswith("P1_") or o.name.startswith("Product"):
        continue
    ev = o.evaluated_get(dg0)
    xs = [(ev.matrix_world @ Vector(c)).x for c in ev.bound_box]
    lo, hi = min(xs), max(xs)
    if hi > HALF_X + 0.05 and lo > HALF_X - 0.02:
        outsiders.append({"name": o.name, "x": [round(lo, 3), round(hi, 3)],
                          "side": "right"})
    elif lo < -(HALF_X + 0.05) and hi < -(HALF_X - 0.02):
        outsiders.append({"name": o.name, "x": [round(lo, 3), round(hi, 3)],
                          "side": "left"})

# ---------------------------------------------------------------- report ----
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
bme = ev.to_mesh()
bme.calc_loop_triangles()
body_stats = {"eval_verts": len(bme.vertices), "eval_tris": len(bme.loop_triangles)}
ev.to_mesh_clear()

out = {
    "blend_in": os.path.abspath(bpy.data.filepath),
    "out": os.path.abspath(OUT) if OUT else None,
    "params": {"half_x": HALF_X, "r_xy": R_XY, "r_z": R_Z,
               "corner_seg": CORNER_SEG, "fillet_steps": FILLET_STEPS},
    "before": old,
    "after": {"base_verts": new_base_verts, **body_stats},
    "outlet_cutter": cutter_shift,
    "pieces": [o.name for o in (bay, seat)],
    "reseated": reseated,
    "narrowed": narrowed,
    "outsiders": outsiders,
    "dry_run": DRY,
}
print("P1A SHELL %s" % ("DRY" if DRY else "APPLY"))
print("  body base verts %d -> %d   eval %s" % (
    old["base_verts"], new_base_verts, body_stats))
print("  outlet cutter: %s" % cutter_shift)
print("  pieces: %s  (seat boolean: %s)" % (out["pieces"], b.object.name))
print("  reseated: %s" % reseated)
print("  narrowed: %s" % narrowed)
print("  still outside the shell in x: %d" % len(outsiders))
for x in outsiders:
    print("    %-26s %-6s x %s" % (x["name"], x["side"], x["x"]))

if not DRY:
    dest = OUT or bpy.data.filepath
    os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(dest))
    print("SAVED %s" % os.path.abspath(dest))
    with open(os.path.splitext(os.path.abspath(dest))[0] + "_p1a_report.json",
              "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
