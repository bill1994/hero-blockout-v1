"""S2.2 - the chute is 24 mm too shallow in depth, and its side rails sit on the
wrong line.

Reference measurements (reference/parts_20261124.json):
  tripo_part_7  chute body  y -0.153..+0.092  (0.2446 deep)
  tripo_part_10 left rail   y -0.138..-0.117  z 0.043..0.148
  tripo_part_11 right rail  y +0.059..+0.083  z 0.043..0.148
Our s2e: chute y -0.1408..+0.0802 (0.221), rails straddling the outer edge.

So: widen the chute about its centre line and move each rail onto the measured
band. Tri counts must not move - this is a pure reshape.

  blender -b --factory-startup --python scripts/s2_2_chute.py
"""

import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import stage_lock  # noqa: E402

SRC = "versions/rebuild_v7_s2e.blend"
DST = "versions/rebuild_v7_s2f.blend"

CHUTE_Y = (-0.1440, 0.0880)
RAIL_L = (-0.1380, -0.1170)
RAIL_R = (0.0590, 0.0830)

stage_lock.verify(SRC, "s2_2 input")
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, SRC))
sc = bpy.context.scene

before = {}
for o in sc.objects:
    if o.type == "MESH":
        before[o.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)


def world_ys(obj):
    return [ (obj.matrix_world @ v.co).y for v in obj.data.vertices ]


def fit_y(obj, target, label):
    """Scale/translate the object's vertices in world y so its extent hits target."""
    ys = world_ys(obj)
    lo, hi = min(ys), max(ys)
    tlo, thi = target
    s = (thi - tlo) / (hi - lo)
    c0 = (lo + hi) / 2.0
    c1 = (tlo + thi) / 2.0
    mw = obj.matrix_world
    mi = mw.inverted()
    for v in obj.data.vertices:
        w = mw @ v.co
        w.y = c1 + (w.y - c0) * s
        v.co = mi @ w
    obj.data.update()
    ys = world_ys(obj)
    print("@@FIT@@ %-18s %+.4f..%+.4f -> %+.4f..%+.4f  (scale %.4f)"
          % (label, lo, hi, min(ys), max(ys), s))


fit_y(sc.objects["Machine_Chute"], CHUTE_Y, "Machine_Chute")
fit_y(sc.objects["P1_OutletLip_L"], RAIL_L, "P1_OutletLip_L")
fit_y(sc.objects["P1_OutletLip_R"], RAIL_R, "P1_OutletLip_R")

after = {}
for o in sc.objects:
    if o.type == "MESH":
        after[o.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)
if before != after:
    sys.exit("[s2_2] tri counts changed")

lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for o in sc.objects:
    if o.type != "MESH":
        continue
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        for i in range(3):
            lo[i] = min(lo[i], w[i])
            hi[i] = max(hi[i], w[i])
print("@@EXT@@ x %.4f..%.4f  y %.4f..%.4f  z %.4f..%.4f"
      % (lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))
print("@@TOTAL@@ tris %d  objects %d" % (sum(after.values()), len(after)))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, DST))
stage_lock.record(DST)
print("@@SAVED@@ %s" % DST)
