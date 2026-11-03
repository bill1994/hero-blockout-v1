"""P19 v5 - final reading of the reference outlet.

Evidence:
  top view  -> amber FILLS the opening, framed by cream  => open-top trough,
               cream side rails + a thick cream end lip
  side view -> amber is the outermost surface over a band => cream rails are LOW,
               so the amber wall stays visible above them
  hero      -> chunky cream lip at the mouth

So: amber U trough (open top) + low cream side rails + thick cream end lip
    + amber riser on the body face + cream cradle carrying the product out.
"""
import bpy
import math
from mathutils import Vector

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_build5.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

# amber trough
TR_X0, TR_X1 = 0.86, 1.58
TR_IY, TR_FLOOR, TR_RIM, TR_WALL = 0.380, 1.074, 1.500, 0.035
# cream side rails (LOW so amber stays the outermost surface)
RAIL_SY0, RAIL_SY1 = 0.417, 0.520
RAIL_SZ0, RAIL_SZ1 = 1.000, 1.320
RAIL_SX0, RAIL_SX1 = 0.860, 1.600
# thick cream end lip
LIP_X0, LIP_X1 = 1.500, 1.600
LIP_HY, LIP_Z0, LIP_Z1 = 0.520, 0.980, 1.600
# amber riser on the body face
BAND_X0, BAND_X1 = 0.900, 0.930
BAND_Z0, BAND_Z1 = 1.600, 2.090
BAND_HY = 0.070
# cream cradle
CR_X0, CR_X1 = 1.580, 2.460
KNEE_X, KNEE_Z, TAIL_Z = 2.200, 1.074, 0.960
CR_HY, CR_TH = 0.440, 0.050
CR_WALL_Z = 1.180


def ensure(name):
    o = bpy.data.objects.get(name)
    if o is None:
        me = bpy.data.meshes.new(name + "_m")
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
    return o


def assign(obj, verts, faces, mat):
    old = obj.data
    me = bpy.data.meshes.new(obj.name + "_m")
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    obj.data = me
    obj.data.materials.clear()
    m = bpy.data.materials.get(mat)
    if m is None:
        raise RuntimeError("missing " + mat)
    obj.data.materials.append(m)
    for p in obj.data.polygons:
        p.material_index = 0
        p.use_smooth = True
    if old.users == 0:
        bpy.data.meshes.remove(old)


def to_local(obj, verts):
    inv = obj.matrix_world.inverted()
    return [inv @ Vector(v) for v in verts]


def u_trough(x0, x1, nx, floor, hw, wall, ztop):
    prof = [(-hw, floor), (hw, floor), (hw, ztop), (hw + wall, ztop),
            (hw + wall, floor - wall), (-hw - wall, floor - wall),
            (-hw - wall, ztop), (-hw, ztop)]
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


def rounded_bar(x0, x1, y0, y1, z0, z1, r, nx=2, seg=5):
    """Box with rounded vertical-and-horizontal edges, swept along X."""
    def prof():
        pts = []
        for i in range(seg + 1):
            a = -math.pi / 2 + (math.pi / 2) * i / seg
            pts.append((y1 - r + r * math.cos(a), z0 + r + r * math.sin(a)))
        for i in range(seg + 1):
            a = (math.pi / 2) * i / seg
            pts.append((y1 - r + r * math.cos(a), z1 - r + r * math.sin(a)))
        for i in range(seg + 1):
            a = math.pi / 2 + (math.pi / 2) * i / seg
            pts.append((y0 + r + r * math.cos(a), z1 - r + r * math.sin(a)))
        for i in range(seg + 1):
            a = math.pi + (math.pi / 2) * i / seg
            pts.append((y0 + r + r * math.cos(a), z0 + r + r * math.sin(a)))
        return pts

    P = prof()
    n = len(P)
    verts = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        for (y, z) in P:
            verts.append((x, y, z))
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


def tube_ring(x0, x1, oy, oz0, oz1, iy, iz0, iz1, r_out=0.085, r_in=0.045, seg=7):
    """Thick rounded-rect ring along X - the outlet lip."""
    def ring(hw, z0, z1, r):
        r = min(r, hw * 0.80, (z1 - z0) * 0.38)
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


def top_z(x):
    if x <= KNEE_X:
        return KNEE_Z
    t = min(max((x - KNEE_X) / (CR_X1 - KNEE_X), 0.0), 1.0)
    return KNEE_Z + (TAIL_Z - KNEE_Z) * (t * t * (3 - 2 * t))


def cradle(x0, x1, nx, hy, th, wall_z):
    """Shelf with low side walls, top following top_z(x)."""
    prof = [(-hy, -th), (hy, -th), (hy, wall_z - top_z(x0)), (hy - 0.055, wall_z - top_z(x0)),
            (hy - 0.055, 0.0), (-hy + 0.055, 0.0), (-hy + 0.055, wall_z - top_z(x0)),
            (-hy, wall_z - top_z(x0))]
    verts = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        zt = top_z(x)
        for (y, dz) in prof:
            verts.append((x, y, zt + dz))
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


def reparent(obj, parent):
    if obj.parent == parent:
        return
    mw = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = mw


W("=== P19 build v5 ===")

chute = ensure("Machine_Chute")
v, f = u_trough(TR_X0, TR_X1, 10, TR_FLOOR, TR_IY, TR_WALL, TR_RIM)
assign(chute, to_local(chute, v), f, "MAT_Color_Amber")
W(f"Machine_Chute v={len(v)} f={len(f)}")

rail_l = ensure("P1_OutletRailL")
v, f = rounded_bar(RAIL_SX0, RAIL_SX1, RAIL_SY0, RAIL_SY1, RAIL_SZ0, RAIL_SZ1, 0.045, nx=3)
assign(rail_l, to_local(rail_l, v), f, "MAT_Body")

rail_r = ensure("P1_OutletRailR")
v2, f2 = rounded_bar(RAIL_SX0, RAIL_SX1, -RAIL_SY1, -RAIL_SY0, RAIL_SZ0, RAIL_SZ1, 0.045, nx=3)
assign(rail_r, to_local(rail_r, v2), f2, "MAT_Body")
W(f"side rails v={len(v)}+{len(v2)}")

lip = ensure("P1_OutletCollar")
# a RING, not a solid bar - the product must pass through the hole
LIP_IY, LIP_IZ0, LIP_IZ1 = 0.418, 1.030, 1.558
v, f = tube_ring(LIP_X0, LIP_X1, LIP_HY, LIP_Z0, LIP_Z1,
                 LIP_IY, LIP_IZ0, LIP_IZ1, 0.085, 0.045, seg=7)
assign(lip, to_local(lip, v), f, "MAT_Body")
W(f"P1_OutletCollar(lip) v={len(v)} f={len(f)}")

band = ensure("P2_OutletBand")
vb = [(BAND_X0, -BAND_HY, BAND_Z0), (BAND_X1, -BAND_HY, BAND_Z0), (BAND_X1, BAND_HY, BAND_Z0), (BAND_X0, BAND_HY, BAND_Z0),
      (BAND_X0, -BAND_HY, BAND_Z1), (BAND_X1, -BAND_HY, BAND_Z1), (BAND_X1, BAND_HY, BAND_Z1), (BAND_X0, BAND_HY, BAND_Z1)]
fb = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
assign(band, to_local(band, vb), fb, "MAT_Color_Amber")

cr = ensure("P1_ChuteRail")
v, f = cradle(CR_X0, CR_X1, 18, CR_HY, CR_TH, CR_WALL_Z)
assign(cr, to_local(cr, v), f, "MAT_Body")
W(f"P1_ChuteRail v={len(v)} f={len(f)}")

seat = bpy.data.objects.get("P1_ChuteSeat")
if seat:
    seat.hide_render = True
    seat.hide_viewport = True

out_empty = bpy.data.objects.get("Machine_OutputChute")
body = bpy.data.objects.get("Machine_Body")
if out_empty:
    reparent(chute, out_empty)
if body:
    for o in (rail_l, rail_r, lip, band, cr):
        reparent(o, body)

for o in (chute, rail_l, rail_r, lip, band, cr):
    for m in list(o.modifiers):
        if m.type == "SUBSURF":
            o.modifiers.remove(m)
    for p in o.data.polygons:
        p.use_smooth = True

bpy.context.view_layer.update()
for name in ("Machine_Chute", "P1_OutletRailL", "P1_OutletRailR", "P1_OutletCollar", "P1_ChuteRail", "P2_OutletBand"):
    o = bpy.data.objects[name]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    W(f"{name}: x[{min(p.x for p in vs):.3f},{max(p.x for p in vs):.3f}] "
      f"y[{min(p.y for p in vs):.3f},{max(p.y for p in vs):.3f}] "
      f"z[{min(p.z for p in vs):.3f},{max(p.z for p in vs):.3f}]")

bpy.ops.wm.save_as_mainfile(filepath=r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend")
W("SAVED p19 v5")
