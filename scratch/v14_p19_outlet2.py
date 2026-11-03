"""P19 outlet rebuild v2 - reference-faithful SHORT mouth + LONG cream cradle.

Fixes v1: collar moved clear of the product's rising sweep (f255+),
          trough top lowered to fit the body bore, rail flattened,
          floor lowered to 1.074 so the product never dips through it.

Layout (world units, body face at x=+0.90, body bore z 1.023..1.452):
  amber trough   x 0.86 -> 1.42   floor 1.074, inner half-width 0.400, wall 0.055, top 1.448
  cream hull     x 0.84 -> 1.46   low outer wall, keeps amber visible from the side
  cream collar   x 1.15 -> 1.42   thick rim framing the mouth (inner clears trough outer)
  cream cradle   x 1.42 -> 2.70   flat shelf the product rides out on
  amber band     x 0.900-> 0.930  rising leg on the body face, z 1.55..2.09
Product: 0.70 x 0.70 x 0.40, rides z 1.076..1.495, +X travel.
"""
import bpy
import math
from mathutils import Vector

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_build2.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

FLOOR    = 1.074
IW       = 0.400
WALL     = 0.055
WTOP     = 1.448
X0, X1   = 0.86, 1.42
HULL_W   = 0.062
HULL_TOP = 1.230
COLL_X0, COLL_X1 = 1.15, 1.42
COLL_OY, COLL_OZ0, COLL_OZ1 = 0.545, 0.960, 1.625
COLL_IY, COLL_IZ0, COLL_IZ1 = 0.462, 1.005, 1.560
RAIL_X0, RAIL_X1 = 1.42, 2.70
RAIL_HY, RAIL_TH = 0.470, 0.055
BAND_X0, BAND_X1 = 0.900, 0.930
BAND_Z0, BAND_Z1 = 1.550, 2.090
BAND_HY = 0.072


def assign(obj, verts, faces, mat):
    old = obj.data
    me = bpy.data.meshes.new(obj.name + "_m")
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    obj.data = me
    obj.data.materials.clear()          # plan 8.5: swapping data drops slots
    m = bpy.data.materials.get(mat)
    if m is None:
        raise RuntimeError("missing material " + mat)
    obj.data.materials.append(m)
    for p in obj.data.polygons:
        p.material_index = 0
        p.use_smooth = True
    if old.users == 0:
        bpy.data.meshes.remove(old)


def ensure(name):
    o = bpy.data.objects.get(name)
    if o is None:
        me = bpy.data.meshes.new(name + "_m")
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
    return o


def to_local(obj, verts):
    inv = obj.matrix_world.inverted()
    return [inv @ Vector(v) for v in verts]


def u_channel(x0, x1, nx, floor, hw, wall, ztop):
    prof = [(-hw, floor), (hw, floor), (hw, ztop), (hw + wall, ztop),
            (hw + wall, floor - wall), (-hw - wall, floor - wall), (-hw - wall, ztop), (-hw, ztop)]
    verts = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        for (y, z) in prof:
            verts.append((x, y, z))
    n = len(prof)
    faces = []
    for i in range(nx):
        a, b = i * n, (i + 1) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    faces.append(tuple(range(n - 1, -1, -1)))
    last = nx * n
    faces.append(tuple(range(last, last + n)))
    return verts, faces


def frame_ring(x0, x1, oy, oz0, oz1, iy, iz0, iz1, r_out=0.085, r_in=0.055, seg=7):
    def ring(hw, z0, z1, r):
        r = min(r, hw * 0.85, (z1 - z0) * 0.40)
        cx, cz0, cz1 = hw - r, z0 + r, z1 - r
        pts = []
        for i in range(seg + 1):
            a = -math.pi / 2 + (math.pi / 2) * i / seg
            pts.append((cx + r * math.cos(a), cz0 + r * math.sin(a)))
        for i in range(seg + 1):
            a = (math.pi / 2) * i / seg
            pts.append((cx + r * math.cos(a), cz1 + r * math.sin(a)))
        for i in range(seg + 1):
            a = math.pi / 2 + (math.pi / 2) * i / seg
            pts.append((-cx + r * math.cos(a), cz1 + r * math.sin(a)))
        for i in range(seg + 1):
            a = math.pi + (math.pi / 2) * i / seg
            pts.append((-cx + r * math.cos(a), cz0 + r * math.sin(a)))
        return pts

    O = ring(oy, oz0, oz1, r_out)
    I = ring(iy, iz0, iz1, r_in)
    n = len(O)
    verts = []
    for x in (x0, x1):
        for (y, z) in O:
            verts.append((x, y, z))
        for (y, z) in I:
            verts.append((x, y, z))
    o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
    faces = []
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((o0 + j, i0 + j, i0 + j2, o0 + j2))
        faces.append((o1 + j2, i1 + j2, i1 + j, o1 + j))
        faces.append((o0 + j, o0 + j2, o1 + j2, o1 + j))
        faces.append((i0 + j2, i0 + j, i1 + j, i1 + j2))
    return verts, faces


def box(x0, x1, y0, y1, z0, z1):
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


def reparent(obj, parent):
    if obj.parent == parent:
        return
    mw = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = mw


W("=== P19 build v2 ===")

chute = ensure("Machine_Chute")
v, f = u_channel(X0, X1, 22, FLOOR, IW, WALL, WTOP)
assign(chute, to_local(chute, v), f, "MAT_Color_Amber")
W(f"Machine_Chute v={len(v)} f={len(f)}")

seat = ensure("P1_ChuteSeat")
v, f = u_channel(X0 - 0.02, X1 + 0.04, 16, FLOOR - 0.014, IW + WALL + 0.004, HULL_W, HULL_TOP)
assign(seat, to_local(seat, v), f, "MAT_Body")
W(f"P1_ChuteSeat v={len(v)} f={len(f)}")

col = ensure("P1_OutletCollar")
v, f = frame_ring(COLL_X0, COLL_X1, COLL_OY, COLL_OZ0, COLL_OZ1,
                  COLL_IY, COLL_IZ0, COLL_IZ1)
assign(col, to_local(col, v), f, "MAT_Body")
W(f"P1_OutletCollar v={len(v)} f={len(f)}")

rail = ensure("P1_ChuteRail")
v, f = box(RAIL_X0, RAIL_X1, -RAIL_HY, RAIL_HY, FLOOR - RAIL_TH, FLOOR)
assign(rail, to_local(rail, v), f, "MAT_Body")
W(f"P1_ChuteRail v={len(v)} f={len(f)}")

band = ensure("P2_OutletBand")
v, f = box(BAND_X0, BAND_X1, -BAND_HY, BAND_HY, BAND_Z0, BAND_Z1)
assign(band, to_local(band, v), f, "MAT_Color_Amber")
W(f"P2_OutletBand v={len(v)} f={len(f)}")

out_empty = bpy.data.objects.get("Machine_OutputChute")
body = bpy.data.objects.get("Machine_Body")
if out_empty:
    reparent(chute, out_empty)
if body:
    for o in (seat, col, rail, band):
        reparent(o, body)

for o in (chute, seat, col, rail, band):
    for m in list(o.modifiers):
        if m.type == "SUBSURF":
            o.modifiers.remove(m)
    for p in o.data.polygons:
        p.use_smooth = True

bpy.context.view_layer.update()
for name in ("Machine_Chute", "P1_ChuteSeat", "P1_OutletCollar", "P1_ChuteRail", "P2_OutletBand"):
    o = bpy.data.objects[name]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    W(f"{name}: x[{min(p.x for p in vs):.3f},{max(p.x for p in vs):.3f}] "
      f"y[{min(p.y for p in vs):.3f},{max(p.y for p in vs):.3f}] "
      f"z[{min(p.z for p in vs):.3f},{max(p.z for p in vs):.3f}]")

bpy.ops.wm.save_as_mainfile(filepath=r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend")
W("SAVED p19 v2")
