"""S2.3b - close the two biggest front-silhouette gaps found after S2.3.

1. The body's right wall. A ray probe of the reference (scratch/probe_body_profile.py)
   shows tripo_part_0's right face sitting at x 0.062 (z 0.04) rising to 0.074
   (z 0.40) - a slightly drafting wall, not the flat 0.098 our beveled box has.
   We shift the whole right bevel ring inward by 24.5 mm, which keeps the ring's
   shape intact (uniform translate) and only narrows the connecting faces.

2. The finger cluster sits 0.6094..0.6881 where the reference is 0.62..0.71, so
   the four fingers rise 18 mm and the gripper block 10 mm. Raising the gripper
   more would push z_max past the elbow.

  blender -b --factory-startup --python scripts/s2_3b_body_fingers.py
"""

import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import stage_lock  # noqa: E402

SRC = "versions/rebuild_v7_s2d.blend"
DST = "versions/rebuild_v7_s2e.blend"

WALL_SHIFT = -0.0245          # world metres, inward
WALL_LOCAL_X = 0.2189         # local x of the bevel-ring start (world 0.0499)
FINGER_DZ = 0.0180
GRIPPER_DZ = 0.0100

stage_lock.verify(SRC, "s2_3b input")
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, SRC))
sc = bpy.context.scene

FINGER_OBJS = ["Arm_Finger_%s_%s" % (f, s)
               for f in "ABCD" for s in ("s1", "s2")]

before = {}
for o in sc.objects:
    if o.type == "MESH":
        before[o.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)


def scene_bbox():
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
    return lo, hi


# ---- 1. body right wall ---------------------------------------------------
body = sc.objects["Machine_Body"]
me = body.data
mw = body.matrix_world
mi = mw.inverted()
moved = 0
for v in me.vertices:
    if v.co.x >= WALL_LOCAL_X:
        w = mw @ v.co
        v.co = mi @ (w + Vector((WALL_SHIFT, 0.0, 0.0)))
        moved += 1
print("@@BODY@@ shifted %d verts of %d by %+.4f in x" % (moved, len(me.vertices), WALL_SHIFT))
me.update()

# sanity: the wall must be straight, so only two distinct x values near it
xs = sorted({round(v.co.x, 5) for v in me.vertices if v.co.x > 0.15})
print("@@BODY@@ local x after shift: %s" % xs)

# ---- 2. fingers and gripper ----------------------------------------------
for name in FINGER_OBJS:
    o = sc.objects.get(name)
    if o is None:
        sys.exit("[s2_3b] missing object %s" % name)
    o.location.z += FINGER_DZ
grip = sc.objects["Arm_Gripper"]
grip.location.z += GRIPPER_DZ
bpy.context.view_layer.update()
print("@@HAND@@ fingers +%.4f, gripper +%.4f" % (FINGER_DZ, GRIPPER_DZ))

# ---- 3. verification ------------------------------------------------------
after = {}
for o in sc.objects:
    if o.type == "MESH":
        after[o.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)
if before != after:
    diff = {k: (before.get(k), after.get(k)) for k in set(before) | set(after)
            if before.get(k) != after.get(k)}
    sys.exit("[s2_3b] tri counts changed: %s" % diff)

lo, hi = scene_bbox()
print("@@EXT@@ x %.4f..%.4f  y %.4f..%.4f  z %.4f..%.4f"
      % (lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))
for name in ["Machine_Body", "Arm_Gripper"] + FINGER_OBJS:
    o = sc.objects[name]
    ws = [o.matrix_world @ v.co for v in o.data.vertices]
    print("@@PART@@ %-20s x %+.4f..%+.4f  z %+.4f..%+.4f"
          % (name, min(w.x for w in ws), max(w.x for w in ws),
             min(w.z for w in ws), max(w.z for w in ws)))

tris = sum(after.values())
print("@@TOTAL@@ tris %d  objects %d" % (tris, len(after)))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, DST))
stage_lock.record(DST)
print("@@SAVED@@ %s" % DST)
