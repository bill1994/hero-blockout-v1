"""P19 v4 - correct reading of the reference:
   CREAM THICK-WALL SPOUT = the outer body of the outlet (protrudes from the face)
   AMBER LINER            = sits inside that bore (floor + side walls)
   CREAM CRADLE           = continues outward, carries the product to the exit

Previous v2/v3 made the collar opening WIDER than the trough, so the amber
shrank to slivers and the whole thing read as "a frame plus a board".
"""
import bpy
import math
from mathutils import Vector

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_build4.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

# ---- contract
SPOUT_X0, SPOUT_X1 = 0.86, 1.56          # cream spout body
SPOUT_OY, SPOUT_OZ0, SPOUT_OZ1 = 0.520, 1.000, 1.600
BORE_Y, BORE_Z0, BORE_Z1 = 0.415, 1.025, 1.520   # inner bore of the spout
LINER_Y, LINER_FLOOR, LINER_TOP = 0.395, 1.074, 1.485
LINER_WALL = 0.020

RAIL_X0, RAIL_X1 = 1.54, 2.78
KNEE_X, KNEE_Z, TAIL_Z = 2.32, 1.074, 0.950
RAIL_HY, RAIL_TH = 0.455, 0.055

BAND_X0, BAND_X1 = 0.900, 0.930
BAND_Z0, BAND_Z1 = 1.640, 2.090
BAND_HY = 0.070


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


def tube(x0, x1, nx, oy, oz0, oz1, iy, iz0, iz1, r_out=0.105, r_in=0.055, seg=8):
    """Thick rounded-rect tube along X - the cream spout body."""
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
        faces.append((o0 + j, i0 + j, i0 + j2, o0 + j2))   # front rim
        faces.append((o1 + j2, i1 + j2, i1 + j, o1 + j))   # back rim
        faces.append((o0 + j, o0 + j2, o1 + j2, o1 + j))   # outer wall
        faces.append((i0 + j2, i0 + j, i1 + j, i1 + j2))   # bore wall
    return verts, faces


def u_liner(x0, x1, nx, floor, hw, wall, ztop):
    """Amber U liner filling the spout bore."""
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


def top_z(x):
    if x <= KNEE_X:
        return KNEE_Z
    t = min(max((x - KNEE_X) / (RAIL_X1 - KNEE_X), 0.0), 1.0)
    return KNEE_Z + (TAIL_Z - KNEE_Z) * (t * t * (3 - 2 * t))


def cradle(x0, x1, nx, hy, th):
    verts = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        zt = top_z(x)
        zb = zt - th
        verts.extend([(x, -hy, zb), (x, hy, zb), (x, hy, zt), (x, -hy, zt)])
    faces = []
    for i in range(nx):
        a, b = i * 4, (i + 1) * 4
        faces.append((a + 0, b + 0, b + 1, a + 1))
        faces.append((a + 3, a + 2, b + 2, b + 3))
        faces.append((a + 1, b + 1, b + 2, a + 2))
        faces.append((a + 0, a + 3, b + 3, b + 0))
    faces.append((0, 1, 2, 3))
    last = nx * 4
    faces.append((last + 3, last + 2, last + 1, last + 0))
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


W("=== P19 build v4: cream spout + amber liner + cradle ===")

# 1. cream spout body (the thing that reads as the outlet in the reference)
col = ensure("P1_OutletCollar")
v, f = tube(SPOUT_X0, SPOUT_X1, 4, SPOUT_OY, SPOUT_OZ0, SPOUT_OZ1,
            BORE_Y, BORE_Z0, BORE_Z1)
assign(col, to_local(col, v), f, "MAT_Body")
W(f"P1_OutletCollar v={len(v)} f={len(f)}")

# 2. amber liner inside the bore
chute = ensure("Machine_Chute")
v, f = u_liner(SPOUT_X0 - 0.02, SPOUT_X1 - 0.02, 8, LINER_FLOOR, LINER_Y, LINER_WALL, LINER_TOP)
assign(chute, to_local(chute, v), f, "MAT_Color_Amber")
W(f"Machine_Chute v={len(v)} f={len(f)}")

# 3. cream cradle carrying the product outward
rail = ensure("P1_ChuteRail")
v, f = cradle(RAIL_X0, RAIL_X1, 16, RAIL_HY, RAIL_TH)
assign(rail, to_local(rail, v), f, "MAT_Body")
W(f"P1_ChuteRail v={len(v)} f={len(f)}")

# 4. amber riser on the body face
band = ensure("P2_OutletBand")
v, f = box(BAND_X0, BAND_X1, -BAND_HY, BAND_HY, BAND_Z0, BAND_Z1)
assign(band, to_local(band, v), f, "MAT_Color_Amber")
W(f"P2_OutletBand v={len(v)} f={len(f)}")

# 5. retire the old flat seat (the spout now does its job)
seat = bpy.data.objects.get("P1_ChuteSeat")
if seat:
    seat.hide_render = True
    seat.hide_viewport = True
    W("P1_ChuteSeat hidden (superseded by the spout body)")

out_empty = bpy.data.objects.get("Machine_OutputChute")
body = bpy.data.objects.get("Machine_Body")
if out_empty:
    reparent(chute, out_empty)
if body:
    for o in (col, rail, band):
        reparent(o, body)

for o in (chute, col, rail, band):
    for m in list(o.modifiers):
        if m.type == "SUBSURF":
            o.modifiers.remove(m)
    for p in o.data.polygons:
        p.use_smooth = True

bpy.context.view_layer.update()
for name in ("P1_OutletCollar", "Machine_Chute", "P1_ChuteRail", "P2_OutletBand"):
    o = bpy.data.objects[name]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    W(f"{name}: x[{min(p.x for p in vs):.3f},{max(p.x for p in vs):.3f}] "
      f"y[{min(p.y for p in vs):.3f},{max(p.y for p in vs):.3f}] "
      f"z[{min(p.z for p in vs):.3f},{max(p.z for p in vs):.3f}]")

bpy.ops.wm.save_as_mainfile(filepath=r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend")
W("SAVED p19 v4")
