"""S2.1b - widen the hopper throat so the collar stops poking through it.

Measured (radial rays from the hopper axis, first hit):
  ours      z 0.4878 -> r 0.0829..0.0839
  reference z 0.4878 -> r 0.1065..0.1098
  ours      z 0.5100 -> r 0.1015..0.1028
  reference z 0.5100 -> r 0.1198..0.1228

The v7 lathe is a single straight inner cone, r 0.062 @ z 0.462 to r 0.176 @
z 0.589 (slope 0.898). The reference inner wall is two-slope: 0.682 above, then
it turns steeply into the throat. Splitting the profile at (0.107, 0.4878)
reproduces the measured radii and puts the 0.088 collar 19 mm inside the wall,
which is exactly what the reference does - the floor disc at z 0.4878 stays, it
is the plugged bottom seen down the mouth.
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

SRC = os.path.join(ROOT, "versions", "rebuild_v7_s2b.blend")
DST = os.path.join(ROOT, "versions", "rebuild_v7_s2c.blend")

SEG = 20
CX, CY = -0.1183, 0.0022

# (r, z) walked as a closed loop: bottom annulus -> outer wall -> rim flare ->
# rim top -> inner wall. Radii are the measured reference walls (16-ray radial
# probe on ReferenceModel.blend, mm):
#   z 0.4878  inner 106..110  outer 119..122
#   z 0.5100  inner 120..123  outer 133..136
#   z 0.5500  inner 143..147  outer 158..162
#   z 0.5850  inner 162..165  outer 175..176
# i.e. a cone of roughly constant 12.5 mm wall thickness. v7 instead used a
# 0.783 outer against a 0.898 inner, which cross at z 0.532 and leave the tube
# inside-out above that height.
PROFILE = [
    (0.0844, 0.4450),   # inner bottom, 3 mm inside the body top (no coplanar face)
    (0.0959, 0.4450),   # outer bottom
    (0.1754, 0.5850),   # outer wall top
    (0.1760, 0.5890),   # rim outer edge
    (0.1665, 0.5890),   # rim inner edge
]
INNER = (3, 4)          # rim top and inner wall get the dark material


def tris_of(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


stage_lock.verify(SRC)
bpy.ops.wm.open_mainfile(filepath=SRC)

ob = bpy.data.objects["Machine_Hopper"]
mw = ob.matrix_world
rot = mw.to_3x3()
scale = mw.to_scale()
bad = [(i, j) for i in range(3) for j in range(3)
       if abs(rot[i][j] - (1.0 if i == j else 0.0)) > 1e-6]
if bad or any(abs(s - 1.0) > 1e-6 for s in scale):
    sys.exit("[s2.1b] hopper object has rotation/scale %s %s, lathe math would be wrong"
             % (bad, list(scale)))

MI = mw.inverted()
axis = MI @ Vector((CX, CY, 0.0))
lz = lambda z: (MI @ Vector((0.0, 0.0, z))).z

old = ob.data
smooth = sum(1 for p in old.polygons if p.use_smooth) > len(old.polygons) / 2
mats = [m for m in old.materials]
tri_before = tris_of(ob)
print("[s2.1b] hopper local axis (%.4f, %.4f)  smooth=%s  mats=%s"
      % (axis.x, axis.y, smooth, [m.name if m else None for m in mats]))

bm = bmesh.new()
rings = []
for r, z in PROFILE:
    ring = []
    for k in range(SEG):
        a = 2.0 * math.pi * k / SEG
        ring.append(bm.verts.new(Vector((axis.x + r * math.cos(a),
                                         axis.y + r * math.sin(a),
                                         lz(z)))))
    rings.append(ring)

faces = []
for i in range(len(PROFILE)):
    j = (i + 1) % len(PROFILE)
    ri, rj = rings[i], rings[j]
    for k in range(SEG):
        k2 = (k + 1) % SEG
        f = bm.faces.new((ri[k], ri[k2], rj[k2], rj[k]))
        f.smooth = smooth
        f.material_index = 1 if i in INNER else 0
        faces.append(f)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

new = bpy.data.meshes.new("Machine_Hopper_mesh")
bm.to_mesh(new)
bm.free()
for m in mats:
    new.materials.append(m)
new.update()

ob.data = new
bpy.data.meshes.remove(old)
bpy.context.view_layer.update()

# verification: radial first hit along the hopper axis
from mathutils.bvhtree import BVHTree  # noqa: E402

trees = {}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    m2 = o.matrix_world
    trees[o.name] = BVHTree.FromPolygons([m2 @ v.co for v in o.data.vertices],
                                         [tuple(p.vertices) for p in o.data.polygons],
                                         all_triangles=False)
print("[s2.1b] radial first hit from the hopper axis")
for z in (0.4700, 0.4800, 0.4878, 0.4900, 0.4950, 0.5100, 0.5500):
    hits = []
    for k in range(16):
        a = 2.0 * math.pi * k / 16
        d = Vector((math.cos(a), math.sin(a), 0.0))
        best = None
        for name, tree in trees.items():
            loc, nor, idx, dist = tree.ray_cast(Vector((CX, CY, z)), d, 0.6)
            if loc is not None:
                rr = (Vector((loc.x, loc.y, z)) - Vector((CX, CY, z))).length
                if best is None or rr < best[0]:
                    best = (rr, name)
        if best:
            hits.append(best)
    if hits:
        rs = sorted(h[0] for h in hits)
        names = sorted(set(h[1] for h in hits))
        print("   z %.4f  r %.4f..%.4f  (%s)" % (z, rs[0], rs[-1], ",".join(names)))

tri_after = tris_of(ob)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
total = sum(tris_of(o) for o in meshes)
quads = sum(1 for o in meshes for p in o.data.polygons if len(p.vertices) == 4)
ngons = sum(1 for o in meshes for p in o.data.polygons if len(p.vertices) > 4)
print("[s2.1b] hopper tris %d -> %d (scene %d, quads %d, ngons %d)"
      % (tri_before, tri_after, total, quads, ngons))

bpy.ops.wm.save_as_mainfile(filepath=DST)
stage_lock.record(DST)
print("[s2.1b] wrote %s" % DST)
