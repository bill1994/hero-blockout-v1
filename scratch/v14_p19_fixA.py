"""P19 revision A: fix the grey product + rebuild the interior per BUILD_NOTES.

Three fixes:
 1. MAT_Product2 was neutral 0.520 grey - the only desaturated object in a
    four-colour warm palette.  ->  amber, lighter than the chute so it separates.
 2. Machine_Chute (amber sliding surface) only reached x 1.58 and then became a
    CREAM rail, so looking into the mouth read white instead of amber.
    BUILD_NOTES:1308 says the product rides the amber floor to xc 2.09 and the
    dark rail beyond -> extend amber to 2.30 and make the tail MAT_Arm_Dark.
 3. Cream side rails now run the full length so the amber always reads as a
    liner inside a cream hull (the reference relationship).
"""
import bpy
import math
from mathutils import Vector

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_fixA.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

# ---- product colour (linear, Blender base colour)
PRODUCT_AMBER = (0.620, 0.278, 0.092, 1.0)

# ---- geometry contract
TR_X0, TR_X1 = 0.860, 2.300
TR_IY, TR_FLOOR, TR_RIM, TR_WALL = 0.380, 1.074, 1.556, 0.035

RAIL_SX0, RAIL_SX1 = 0.860, 2.320
RAIL_SY0, RAIL_SY1 = 0.416, 0.510
RAIL_SZ0, RAIL_SZ1 = 1.000, 1.320

LIP_X0, LIP_X1 = 1.500, 1.600
LIP_HY, LIP_Z0, LIP_Z1 = 0.520, 0.970, 1.597
LIP_IY, LIP_IZ0, LIP_IZ1 = 0.418, 1.030, 1.558

DARK_X0, DARK_X1 = 2.300, 2.800
KNEE_X, KNEE_Z, TAIL_Z = 2.480, 1.056, 0.950
DARK_HY, DARK_TH = 0.420, 0.120

BAND_X0, BAND_X1 = 0.900, 0.930
BAND_Z0, BAND_Z1 = 1.600, 2.090
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


def tube_ring(x0, x1, oy, oz0, oz1, iy, iz0, iz1, r_out=0.085, r_in=0.045, seg=7):
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


def rounded_bar(x0, x1, y0, y1, z0, z1, r, nx=2, seg=5):
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


def top_z(x):
    if x <= KNEE_X:
        return KNEE_Z
    t = min(max((x - KNEE_X) / (DARK_X1 - KNEE_X), 0.0), 1.0)
    return KNEE_Z + (TAIL_Z - KNEE_Z) * (t * t * (3 - 2 * t))


def dark_rail(x0, x1, nx, hy, th):
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


def reparent(obj, parent):
    if obj.parent == parent:
        return
    mw = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = mw


W("=== P19 revision A3 (close the see-through sliver) ===")

# ---- 1. product colour
mp = bpy.data.materials.get("MAT_Product2")
if mp and mp.use_nodes:
    for n in mp.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            old = n.inputs["Base Color"].default_value
            W(f"MAT_Product2 base {tuple(round(v,3) for v in old[:3])} -> {PRODUCT_AMBER[:3]}")
            n.inputs["Base Color"].default_value = PRODUCT_AMBER
    mp.diffuse_color = PRODUCT_AMBER

# ---- 2. amber sliding surface, full length to 2.30
chute = ensure("Machine_Chute")
v, f = u_trough(TR_X0, TR_X1, 22, TR_FLOOR, TR_IY, TR_WALL, TR_RIM)
assign(chute, to_local(chute, v), f, "MAT_Color_Amber")
W(f"Machine_Chute x {TR_X0}-{TR_X1} v={len(v)} f={len(f)}")

# ---- 3. cream side rails, full length, low so amber stays visible
for nm, y0, y1 in (("P1_OutletRailL", RAIL_SY0, RAIL_SY1), ("P1_OutletRailR", -RAIL_SY1, -RAIL_SY0)):
    o = ensure(nm)
    v, f = rounded_bar(RAIL_SX0, RAIL_SX1, y0, y1, RAIL_SZ0, RAIL_SZ1, 0.042, nx=4)
    assign(o, to_local(o, v), f, "MAT_Body")
W("cream rails x 0.86-2.32")

# ---- 4. cream lip ring
lip = ensure("P1_OutletCollar")
v, f = tube_ring(LIP_X0, LIP_X1, LIP_HY, LIP_Z0, LIP_Z1, LIP_IY, LIP_IZ0, LIP_IZ1)
assign(lip, to_local(lip, v), f, "MAT_Body")
W("cream lip ring x 1.50-1.60")

# ---- 5. dark rail tail (charcoal, per BUILD_NOTES)
dk = ensure("P1_ChuteRail")
v, f = dark_rail(DARK_X0, DARK_X1, 14, DARK_HY, DARK_TH)
assign(dk, to_local(dk, v), f, "MAT_Arm_Dark")
W(f"dark rail x {DARK_X0}-{DARK_X1} mat=MAT_Arm_Dark")

# ---- 6. amber riser on the body face
band = ensure("P2_OutletBand")
vb = [(BAND_X0, -BAND_HY, BAND_Z0), (BAND_X1, -BAND_HY, BAND_Z0), (BAND_X1, BAND_HY, BAND_Z0), (BAND_X0, BAND_HY, BAND_Z0),
      (BAND_X0, -BAND_HY, BAND_Z1), (BAND_X1, -BAND_HY, BAND_Z1), (BAND_X1, BAND_HY, BAND_Z1), (BAND_X0, BAND_HY, BAND_Z1)]
fb = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
assign(band, to_local(band, vb), fb, "MAT_Color_Amber")

out_empty = bpy.data.objects.get("Machine_OutputChute")
body = bpy.data.objects.get("Machine_Body")
if out_empty:
    reparent(chute, out_empty)
if body:
    for o in (bpy.data.objects["P1_OutletRailL"], bpy.data.objects["P1_OutletRailR"],
              lip, dk, band):
        reparent(o, body)

for nm in ("Machine_Chute", "P1_OutletRailL", "P1_OutletRailR",
           "P1_OutletCollar", "P1_ChuteRail", "P2_OutletBand"):
    o = bpy.data.objects[nm]
    for m in list(o.modifiers):
        if m.type == "SUBSURF":
            o.modifiers.remove(m)
    for p in o.data.polygons:
        p.use_smooth = True

bpy.context.view_layer.update()
for nm in ("Machine_Chute", "P1_OutletRailL", "P1_OutletRailR",
           "P1_OutletCollar", "P1_ChuteRail", "P2_OutletBand"):
    o = bpy.data.objects[nm]
    vs = [o.matrix_world @ q.co for q in o.data.vertices]
    W(f"{nm}: x[{min(q.x for q in vs):.3f},{max(q.x for q in vs):.3f}] "
      f"y[{min(q.y for q in vs):.3f},{max(q.y for q in vs):.3f}] "
      f"z[{min(q.z for q in vs):.3f},{max(q.z for q in vs):.3f}] "
      f"mat={o.active_material.name if o.active_material else None}")

bpy.ops.wm.save_as_mainfile(filepath=r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend")
W("SAVED")
