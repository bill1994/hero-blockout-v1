"""S2.1 - cut a real louvre pocket into the back face and rebuild the vent grille.

Stage 1 placed five louvre slats at y 0.199..0.2112, i.e. 20 mm *inside* the
solid body (back plane y = 0.231). Nothing ever rendered the back, so nobody
noticed the vents were invisible. Reference has seven slats (tripo_part_51..57)
sitting in a real recess.

This stage rebuilds the back face as a picture frame (4 quads) around the vent
opening, extrudes a 41 mm pocket (4 walls + floor), and replaces the five old
slats with seven at the reference pitch. All new geometry is quads - no
boolean, no bisect, so the surrounding bevel is untouched.
"""

import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

ROOT = r"G:\DSHProject\BlenderMcp"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import stage_lock  # noqa: E402

SRC = os.path.join(ROOT, "versions", "rebuild_v7_s2a.blend")
DST = os.path.join(ROOT, "versions", "rebuild_v7_s2b.blend")

# opening, taken 5 mm wide of the slat footprint
X0, X1 = -0.2200, -0.0700
Z0, Z1 = 0.0880, 0.2110
POCKET_D = 0.0410

# slats: reference tripo_part_51..57 sit at pitch 0.014667; at 0.024 tall they
# overlap into one solid slab, so these are 8 mm fins standing on the pocket
# floor and leaving a 6.7 mm gap - that is what reads as a louvre grille
SLAT_W = 0.1382
SLAT_H = 0.0080
SLAT_Y0, SLAT_Y1 = 0.1900, 0.2060
SLAT_PITCH = 0.014667
SLAT_N = 7
SLAT_ZC0 = 0.1055


def tris_of(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


stage_lock.verify(SRC)
bpy.ops.wm.open_mainfile(filepath=SRC)

body = bpy.data.objects["Machine_Body"]
me = body.data
tri_before = tris_of(body)
poly_before = len(me.polygons)

# dark inner surface so the louvres read against shadow; slot must exist before
# the bmesh pass, because material_index is written there
dark = bpy.data.materials.get("M_ShellDk")
dark_idx = None
if dark is not None:
    names = [(m.name if m else "") for m in me.materials]
    if dark.name not in names:
        me.materials.append(dark)
        names.append(dark.name)
    dark_idx = names.index(dark.name)
    print("[s2.1] dark slot %d (%s)" % (dark_idx, dark.name))

bm = bmesh.new()
bm.from_mesh(me)

backs = [f for f in bm.faces if f.normal.y > 0.99]
if len(backs) != 1:
    sys.exit("[s2.1] expected exactly one +Y face on the body, found %d" % len(backs))
back = backs[0]
if len(back.verts) != 4:
    sys.exit("[s2.1] back face is not a quad (%d verts)" % len(back.verts))
BACK_Y = back.calc_center_median().y
BACK_W = (body.matrix_world @ back.calc_center_median()).y
MI = body.matrix_world.inverted()
to_local = lambda p: MI @ Vector(p)
local_depth = MI.to_3x3() @ Vector((0.0, -POCKET_D, 0.0))
outer = [v for v in back.verts]
print("[s2.1] back face local y %.4f world y %.4f area %.5f"
      % (BACK_Y, BACK_W, back.calc_area()))
print("[s2.1] body matrix loc %s" % (["%.4f" % c for c in body.matrix_world.translation],))

ws = [body.matrix_world @ v.co for v in back.verts]
bx0, bx1 = min(p.x for p in ws), max(p.x for p in ws)
bz0, bz1 = min(p.z for p in ws), max(p.z for p in ws)
print("[s2.1] back flat region x %.4f..%.4f z %.4f..%.4f" % (bx0, bx1, bz0, bz1))
if not (bx0 + 0.002 <= X0 and X1 <= bx1 - 0.002 and bz0 + 0.002 <= Z0 and Z1 <= bz1 - 0.002):
    sys.exit("[s2.1] vent opening (%.3f..%.3f, %.3f..%.3f) does not fit the flat back"
             % (X0, X1, Z0, Z1))

# opening corners on the back plane, in body-local space
ic = [bm.verts.new(to_local((x, BACK_W, z)))
      for x, z in ((X0, Z0), (X1, Z0), (X1, Z1), (X0, Z1))]
bm.verts.index_update()

# order outer corners CCW around the face centre
ctr = Vector((sum(v.co.x for v in outer) / 4.0, BACK_Y,
              sum(v.co.z for v in outer) / 4.0))
outer.sort(key=lambda v: math.atan2(v.co.z - ctr.z, v.co.x - ctr.x))

# for each outer edge pick the two opening corners on that side
new_faces = []
for k in range(4):
    oa, ob = outer[k], outer[(k + 1) % 4]
    mid = (oa.co + ob.co) / 2.0
    side = sorted(ic, key=lambda v: (v.co - mid).length)[:2]
    ia = min(side, key=lambda v: (v.co - oa.co).length)
    ib = side[1] if side[0] is ia else side[0]
    try:
        new_faces.append(bm.faces.new((oa, ob, ib, ia)))
    except ValueError:
        sys.exit("[s2.1] frame quad %d already exists" % k)

# pocket: walls + floor
fc = [bm.verts.new(v.co + local_depth) for v in ic]
for k in range(4):
    ia, ib = ic[k], ic[(k + 1) % 4]
    fa, fb = fc[k], fc[(k + 1) % 4]
    new_faces.append(bm.faces.new((ia, ib, fb, fa)))
floor = bm.faces.new((fc[0], fc[1], fc[2], fc[3]))

bmesh.ops.delete(bm, geom=[back], context="FACES_ONLY")
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

# the body is flat-shaded in v7; keep that, otherwise the whole model's cavity
# response shifts and every A/B view lights up for no geometric reason
smooth_any = any(f.smooth for f in bm.faces)
walls = new_faces[4:] + [floor]
for f in new_faces + [floor]:
    f.smooth = smooth_any
if dark_idx is not None:
    for f in walls:
        f.material_index = dark_idx
print("[s2.1] smooth flag on body: %s" % smooth_any)

bm.to_mesh(me)
bm.free()
me.update()

bpy.context.view_layer.objects.active = body
body.select_set(False)

# --- louvres -------------------------------------------------------------
old = [bpy.data.objects.get("P3e_BackVent_%d" % i) for i in range(5)]
slat_mat = None
for ob in old:
    if ob is not None and ob.data.materials:
        slat_mat = ob.data.materials[0]
        break
for ob in old:
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)

for k in range(SLAT_N):
    zc = SLAT_ZC0 + k * SLAT_PITCH
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
    ob = bpy.context.active_object
    ob.name = "P3e_BackVent_%d" % k
    ob.scale = (SLAT_W, SLAT_Y1 - SLAT_Y0, SLAT_H)
    ob.location = ((X0 + X1) / 2.0, (SLAT_Y0 + SLAT_Y1) / 2.0, zc)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bev = ob.modifiers.new(name="Bevel", type="BEVEL")
    bev.width = 0.0015
    bev.segments = 1
    bev.limit_method = "ANGLE"
    bpy.ops.object.modifier_apply(modifier=bev.name)
    if slat_mat is not None:
        ob.data.materials.append(slat_mat)

# a small frame lip so the grille reads as recessed from the back
bpy.ops.object.select_all(action="DESELECT")

tri_after = tris_of(body)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
total_tris = sum(tris_of(o) for o in meshes)
quads = sum(1 for o in meshes for p in o.data.polygons if len(p.vertices) == 4)
ngons = sum(1 for o in meshes for p in o.data.polygons if len(p.vertices) > 4)
print("[s2.1] body polys %d -> %d, tris %d -> %d (+%d)"
      % (poly_before, len(me.polygons), tri_before, tri_after, tri_after - tri_before))
print("[s2.1] scene tris %d  quads %d  ngons %d  objects %d"
      % (total_tris, quads, ngons, len(meshes)))
print("[s2.1] slats %d  z %.4f..%.4f"
      % (SLAT_N, SLAT_ZC0, SLAT_ZC0 + (SLAT_N - 1) * SLAT_PITCH))

bpy.ops.wm.save_as_mainfile(filepath=DST)
stage_lock.record(DST)
print("[s2.1] wrote %s" % DST)
