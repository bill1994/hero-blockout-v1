"""P19 v3 - sloped cradle tail that follows the product's real descent.

Only changes P1_ChuteRail: flat z=1.074 up to x=2.30, then slopes down to
z=0.950 at x=2.80, so the falling product never intersects it.
"""
import bpy
import math
from mathutils import Vector

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_build3.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

FLOOR   = 1.074
RAIL_X0, RAIL_X1 = 1.42, 2.80
KNEE_X  = 2.30
KNEE_Z  = 1.074
TAIL_Z  = 0.950
RAIL_HY = 0.470
RAIL_TH = 0.055


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


def top_z(x):
    if x <= KNEE_X:
        return KNEE_Z
    t = (x - KNEE_X) / (RAIL_X1 - KNEE_X)
    t = min(max(t, 0.0), 1.0)
    # smooth ease so the tail curls under instead of kinking
    return KNEE_Z + (TAIL_Z - KNEE_Z) * (t * t * (3 - 2 * t))


def loft_slab(x0, x1, nx, hy, th):
    """Slab swept along X whose top surface follows top_z(x)."""
    verts = []
    for i in range(nx + 1):
        x = x0 + (x1 - x0) * i / nx
        zt = top_z(x)
        zb = zt - th
        verts.extend([(x, -hy, zb), (x, hy, zb), (x, hy, zt), (x, -hy, zt)])
    faces = []
    for i in range(nx):
        a, b = i * 4, (i + 1) * 4
        faces.append((a + 0, b + 0, b + 1, a + 1))   # bottom
        faces.append((a + 3, a + 2, b + 2, b + 3))   # top
        faces.append((a + 1, b + 1, b + 2, a + 2))   # +y side
        faces.append((a + 0, a + 3, b + 3, b + 0))   # -y side
    faces.append((0, 1, 2, 3))
    last = nx * 4
    faces.append((last + 3, last + 2, last + 1, last + 0))
    return verts, faces


W("=== P19 build v3: sloped cradle tail ===")
rail = ensure("P1_ChuteRail")
v, f = loft_slab(RAIL_X0, RAIL_X1, 16, RAIL_HY, RAIL_TH)
assign(rail, v, f, "MAT_Body")
W(f"P1_ChuteRail v={len(v)} f={len(f)}")
W(f"  rail top: x={RAIL_X0}->z {top_z(RAIL_X0):.3f} ; x={KNEE_X}->z {top_z(KNEE_X):.3f} ; "
  f"x={RAIL_X1}->z {top_z(RAIL_X1):.3f}")

body = bpy.data.objects.get("Machine_Body")
if body and rail.parent != body:
    mw = rail.matrix_world.copy()
    rail.parent = body
    rail.matrix_parent_inverse = body.matrix_world.inverted()
    rail.matrix_world = mw

bpy.context.view_layer.update()
vs = [rail.matrix_world @ v.co for v in rail.data.vertices]
W(f"  world bbox x[{min(p.x for p in vs):.3f},{max(p.x for p in vs):.3f}] "
  f"y[{min(p.y for p in vs):.3f},{max(p.y for p in vs):.3f}] "
  f"z[{min(p.z for p in vs):.3f},{max(p.z for p in vs):.3f}]")

bpy.ops.wm.save_as_mainfile(filepath=r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend")
W("SAVED p19 v3")
