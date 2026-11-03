"""P19 outlet rebuild - reference-faithful mouth + long cream cradle.

Design contract (all world units, body face at x=+0.90):
  amber trough   x 0.60 -> 1.78   interior floor z=1.085, half-width 0.400
  cream hull     x 0.82 -> 1.86   wraps under + outside, low walls
  cream collar   x 1.52 -> 1.86   thick rim framing the mouth (top z=1.520)
  amber vertical band  on the body face, z 1.55 -> 2.09
  cream cradle   x 1.80 -> 2.64   thin shelf under the product
Product rides at z 1.086..1.486, half-width 0.350, travelling +X.
"""
import bpy
import bmesh
import math
from mathutils import Vector

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_build.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

# ---------------------------------------------------------------- contract
FLOOR   = 1.085      # trough interior floor == product bottom - 0.001
IW      = 0.400      # trough interior half width  (product 0.350 + clearance)
WALL    = 0.055      # trough wall thickness
WTOP    = 1.500      # trough wall top
X0, X1  = 0.60, 1.78 # trough span
HULL_W  = 0.062      # cream hull thickness
HULL_TOP= 1.200      # cream hull low wall top (keeps amber visible from the side)
COLL_X0, COLL_X1 = 1.52, 1.86
COLL_OY, COLL_OZ0, COLL_OZ1 = 0.520, 1.000, 1.520   # collar outer half-width / z range
COLL_IY, COLL_IZ0, COLL_IZ1 = 0.412, 1.030, 1.492   # collar inner (opening)
RAIL_X0, RAIL_X1 = 1.80, 2.64
RAIL_HW  = 0.440
RAIL_TOP = 1.200
BAND_X   = 0.920
BAND_Z0, BAND_Z1 = 1.550, 2.090
BAND_HY  = 0.072


def new_mesh_obj(name, verts, faces, mat):
    """Replace obj mesh, keeping object/parent/material slot (plan 8.5 trap)."""
    obj = bpy.data.objects.get(name)
    created = False
    if obj is None:
        me = bpy.data.meshes.new(name + "_mesh")
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        created = True
    old = obj.data
    me = bpy.data.meshes.new(name + "_mesh_new")
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(verbose=False)
    me.update()
    obj.data = me
    # material slots are silently dropped when swapping data - re-add explicitly
    obj.data.materials.clear()
    m = bpy.data.materials.get(mat)
    if m is None:
        raise RuntimeError("material missing: " + mat)
    obj.data.materials.append(m)
    for p in obj.data.polygons:
        p.material_index = 0
        p.use_smooth = True
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return obj, created


def world_to_local(obj, verts):
    inv = obj.matrix_world.inverted()
    return [inv @ Vector(v) for v in verts]


def u_channel(x0, x1, nx, floor, hw, wall, ztop, flare=0.0):
    """Open-top U channel swept along X, with closed cross-section ring."""
    prof = []
    # ring points, counter-clockwise in (y, z)
    prof.append((-hw, floor))
    prof.append(( hw, floor))
    prof.append(( hw, ztop))
    prof.append(( hw + wall, ztop))
    prof.append(( hw + wall, floor - wall))
    prof.append((-hw - wall, floor - wall))
    prof.append((-hw - wall, ztop))
    prof.append((-hw, ztop))

    verts = []
    for i in range(nx + 1):
        t = i / nx
        x = x0 + (x1 - x0) * t
        f = flare * t            # outward flare toward the far end
        for (y, z) in prof:
            sy = 1.0 + (f if abs(y) > 0.001 else 0.0)
            verts.append((x, y * sy, z + (f * 0.10 if z > floor + 0.01 else 0.0)))

    n = len(prof)
    faces = []
    for i in range(nx):
        a = i * n
        b = (i + 1) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    # end caps (ring n-gons)
    faces.append(tuple(range(n - 1, -1, -1)))
    last = nx * n
    faces.append(tuple(range(last, last + n)))
    return verts, faces


def rounded_rect_frame(x0, x1, oy, oz0, oz1, iy, iz0, iz1, corner=0.075, seg=6):
    """Thick picture frame in the YZ plane, extruded along X."""
    def ring(hw, z0, z1, r):
        pts = []
        r = min(r, hw * 0.9, (z1 - z0) * 0.45)
        cx = hw - r
        cz0 = z0 + r
        cz1 = z1 - r
        # right side going up
        for i in range(seg + 1):
            a = -math.pi / 2 + (math.pi / 2) * i / seg
            pts.append((cx + r * math.cos(a), cz0 + r * math.sin(a)))
        for i in range(seg + 1):
            a = 0 + (math.pi / 2) * i / seg
            pts.append((cx + r * math.cos(a), cz1 + r * math.sin(a)))
        for i in range(seg + 1):
            a = math.pi / 2 + (math.pi / 2) * i / seg
            pts.append((-cx + r * math.cos(a), cz1 + r * math.sin(a)))
        for i in range(seg + 1):
            a = math.pi + (math.pi / 2) * i / seg
            pts.append((-cx + r * math.cos(a), cz0 + r * math.sin(a)))
        return pts

    outer = ring(oy, oz0, oz1, corner)
    inner = ring(iy, iz0, iz1, corner * 0.7)
    n = len(outer)
    verts = []
    for x in (x0, x1):
        for (y, z) in outer:
            verts.append((x, y, z))
        for (y, z) in inner:
            verts.append((x, y, z))
    o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
    faces = []
    for j in range(n):
        j2 = (j + 1) % n
        # front face ring (x0) - connect outer to inner
        faces.append((o0 + j, i0 + j, i0 + j2, o0 + j2))
        # back face ring (x1)
        faces.append((o1 + j2, i1 + j2, i1 + j, o1 + j))
        # outer wall
        faces.append((o0 + j, o0 + j2, o1 + j2, o1 + j))
        # inner wall
        faces.append((i0 + j2, i0 + j, i1 + j, i1 + j2))
    return verts, faces


def slab(x0, x1, hy, z0, z1):
    verts = [
        (x0, -hy, z0), (x1, -hy, z0), (x1, hy, z0), (x0, hy, z0),
        (x0, -hy, z1), (x1, -hy, z1), (x1, hy, z1), (x0, hy, z1),
    ]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


def box(x0, x1, y0, y1, z0, z1):
    verts = [
        (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
        (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),
    ]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


# ---------------------------------------------------------------- build
W("=== P19 outlet build ===")

# 1. amber trough
chute = bpy.data.objects["Machine_Chute"]
v, f = u_channel(X0, X1, 26, FLOOR, IW, WALL, WTOP, flare=0.06)
new_mesh_obj("Machine_Chute", world_to_local(chute, v), f, "MAT_Color_Amber")
W(f"Machine_Chute: verts={len(v)} faces={len(f)}")

# 2. cream hull under + outside the trough (low walls so amber stays visible)
seat = bpy.data.objects["P1_ChuteSeat"]
v2, f2 = u_channel(X0 - 0.02, X1 + 0.08, 20, FLOOR - 0.012, IW + WALL + 0.004,
                   HULL_W, HULL_TOP, flare=0.05)
new_mesh_obj("P1_ChuteSeat", world_to_local(seat, v2), f2, "MAT_Body")
W(f"P1_ChuteSeat: verts={len(v2)} faces={len(f2)}")

# 3. cream collar framing the mouth
v3, f3 = rounded_rect_frame(COLL_X0, COLL_X1, COLL_OY, COLL_OZ0, COLL_OZ1,
                            COLL_IY, COLL_IZ0, COLL_IZ1)
col = bpy.data.objects.get("P1_OutletCollar")
if col:
    new_mesh_obj("P1_OutletCollar", v3, f3, "MAT_Body")
else:
    me = bpy.data.meshes.new("P1_OutletCollar_mesh")
    col = bpy.data.objects.new("P1_OutletCollar", me)
    bpy.context.scene.collection.objects.link(col)
    new_mesh_obj("P1_OutletCollar", v3, f3, "MAT_Body")
W(f"P1_OutletCollar: verts={len(v3)} faces={len(f3)}")

# 4. cream cradle extending under the product beyond the mouth
v4, f4 = u_channel(RAIL_X0, RAIL_X1, 10, FLOOR - 0.012, RAIL_HW, 0.050, RAIL_TOP, flare=0.02)
rail = bpy.data.objects.get("P1_ChuteRail")
if rail is None:
    me = bpy.data.meshes.new("P1_ChuteRail_mesh")
    rail = bpy.data.objects.new("P1_ChuteRail", me)
    bpy.context.scene.collection.objects.link(rail)
new_mesh_obj("P1_ChuteRail", v4, f4, "MAT_Body")
W(f"P1_ChuteRail: verts={len(v4)} faces={len(f4)}")

# 5. amber vertical band on the body face (the reference's rising amber leg)
v5, f5 = box(BAND_X, BAND_X + 0.030, -BAND_HY, BAND_HY, BAND_Z0, BAND_Z1)
band = bpy.data.objects.get("P2_OutletBand")
if band is None:
    me = bpy.data.meshes.new("P2_OutletBand_mesh")
    band = bpy.data.objects.new("P2_OutletBand", me)
    bpy.context.scene.collection.objects.link(band)
new_mesh_obj("P2_OutletBand", v5, f5, "MAT_Color_Amber")
W(f"P2_OutletBand: verts={len(v5)} faces={len(f5)}")

# ---------------------------------------------------------------- parenting
out_empty = bpy.data.objects.get("Machine_OutputChute")
body = bpy.data.objects.get("Machine_Body")
chute = bpy.data.objects["Machine_Chute"]
seat = bpy.data.objects["P1_ChuteSeat"]
col = bpy.data.objects["P1_OutletCollar"]
rail = bpy.data.objects["P1_ChuteRail"]
band = bpy.data.objects["P2_OutletBand"]

def reparent(obj, parent):
    if obj.parent == parent:
        return
    mw = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = mw

if out_empty:
    reparent(chute, out_empty)
if body:
    for o in (seat, col, rail, band):
        reparent(o, body)
W("parenting ok")

# ---------------------------------------------------------------- smoothing
for o in (chute, seat, col, rail, band):
    for m in list(o.modifiers):
        if m.type == "SUBSURF":
            o.modifiers.remove(m)
    if not any(m.type == "NODES" for m in o.modifiers):
        pass
    for p in o.data.polygons:
        p.use_smooth = True
    if hasattr(o.data, "use_auto_smooth"):
        o.data.use_auto_smooth = True

W("subsurf removed (was the 112% triangle regression)")

# ---------------------------------------------------------------- report
bpy.context.view_layer.update()
for name in ("Machine_Chute", "P1_ChuteSeat", "P1_OutletCollar", "P1_ChuteRail", "P2_OutletBand"):
    o = bpy.data.objects[name]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    W(f"{name}: x[{min(p.x for p in vs):.3f},{max(p.x for p in vs):.3f}] "
      f"y[{min(p.y for p in vs):.3f},{max(p.y for p in vs):.3f}] "
      f"z[{min(p.z for p in vs):.3f},{max(p.z for p in vs):.3f}]")

bpy.ops.wm.save_as_mainfile(filepath=r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend")
W("SAVED p19")
