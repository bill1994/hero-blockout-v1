"""S2.3c - rebuild the claw. The S2.3 version reads as a bundle of thin sticks:
each finger was 48 mm long with a 7 mm tip and the palm was a 52 mm cube, while
the reference fingers are ~95 mm long with a 12 mm tip hanging off a chunky
wrist block (scratch/probe_hand.py, PCA of tripo_part_8/9/21..26).

Measured finger spans (root -> tip, metres):
  A  (-0.179,-0.049,0.695) -> (-0.133,-0.072,0.614)   parts 8 + 23
  B  (-0.177,-0.019,0.691) -> (-0.124,+0.017,0.644)   parts 9 + 26
  C  (-0.186,-0.033,0.690) -> (-0.160,-0.019,0.604)   parts 21 + 24
  D  (-0.155,-0.036,0.698) -> (-0.087,-0.038,0.660)   parts 22 + 25
Each finger becomes ONE object with a knuckle bend (3 rings, 6 sides), which is
also what the v14 rig does - one rigid object per finger.

  blender -b --factory-startup --python scripts/s2_3c_claw.py
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import stage_lock  # noqa: E402

SRC = "versions/rebuild_v7_s2f.blend"
DST = "versions/rebuild_v7_s2g.blend"

PALM_C = Vector((-0.183, -0.033, 0.700))
PALM_R = 0.0360
KNUCKLES = [
    ("Arm_Knuckle_L", Vector((-0.172, -0.048, 0.692)), 0.0265),
    ("Arm_Knuckle_R", Vector((-0.172, -0.018, 0.690)), 0.0255),
]

FINGERS = [
    ("A", Vector((-0.176, -0.049, 0.692)), Vector((-0.158, -0.060, 0.663)),
     Vector((-0.146, -0.069, 0.630))),
    ("B", Vector((-0.174, -0.019, 0.690)), Vector((-0.152, -0.004, 0.668)),
     Vector((-0.136, 0.010, 0.640))),
    ("C", Vector((-0.183, -0.033, 0.688)), Vector((-0.170, -0.028, 0.655)),
     Vector((-0.163, -0.022, 0.622))),
    ("D", Vector((-0.160, -0.036, 0.696)), Vector((-0.128, -0.037, 0.680)),
     Vector((-0.100, -0.038, 0.662))),
]
R_ROOT = 0.0200
R_KNEE = 0.0165
R_TIP = 0.0125
SIDES = 6
KNEE_T = 0.45

stage_lock.verify(SRC, "s2_3c input")
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, SRC))
sc = bpy.context.scene
coll = sc.collection

old = [o for o in sc.objects if o.name.startswith("Arm_Finger_")]
gripper = sc.objects["Arm_Gripper"]
finger_mat = old[0].data.materials[0] if old and old[0].data.materials else None
palm_mat = gripper.data.materials[0] if gripper.data.materials else None
tris_before = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
                  for o in sc.objects if o.type == "MESH")

for o in old:
    bpy.data.objects.remove(o, do_unlink=True)


def frame(tangent):
    t = tangent.normalized()
    up = Vector((0.0, 0.0, 1.0))
    if abs(t.dot(up)) > 0.95:
        up = Vector((0.0, 1.0, 0.0))
    u = t.cross(up).normalized()
    v = t.cross(u).normalized()
    return u, v


def make_finger(name, root, knee, tip, mat):
    pts = [root, knee, tip]
    radii = [R_ROOT, R_KNEE, R_TIP]

    bm = bmesh.new()
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        if i == 0:
            tan = pts[1] - pts[0]
        elif i == len(pts) - 1:
            tan = pts[-1] - pts[-2]
        else:
            tan = (pts[i + 1] - pts[i - 1])
        u, v = frame(tan)
        ring = []
        for k in range(SIDES):
            a = 2.0 * math.pi * k / SIDES
            ring.append(bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * r))
        rings.append(ring)
    bm.verts.ensure_lookup_table()

    for i in range(len(rings) - 1):
        for k in range(SIDES):
            k2 = (k + 1) % SIDES
            bm.faces.new((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    for f in bm.faces:
        f.smooth = True
        f.material_index = 0

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


for tag, root, knee, tip in FINGERS:
    ob = make_finger("Arm_Finger_%s" % tag, root, knee, tip, finger_mat)
    for poly in ob.data.polygons:
        poly.use_smooth = True

# ---- hand cluster: wrist ball + knuckles, no box -------------------------
bpy.ops.object.select_all(action="DESELECT")
gripper.select_set(True)
bpy.context.view_layer.objects.active = gripper
bpy.data.objects.remove(gripper, do_unlink=True)


def ball(name, center, radius, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4,
                                         radius=radius, location=center)
    ob = bpy.context.object
    ob.name = name
    ob.data.name = name
    if mat:
        ob.data.materials.append(mat)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    return ob


palm = ball("Arm_Gripper", PALM_C, PALM_R, palm_mat)
for kname, kc, kr in KNUCKLES:
    ball(kname, kc, kr, palm_mat)

bpy.context.view_layer.update()

tris_after = sum(sum(len(p.vertices) - 2 for p in o.data.polygons)
                 for o in sc.objects if o.type == "MESH")
print("@@CLAW@@ tris %d -> %d   objects %d"
      % (tris_before, tris_after, len([o for o in sc.objects if o.type == "MESH"])))

lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for o in sc.objects:
    if o.type != "MESH":
        continue
    for vv in o.data.vertices:
        w = o.matrix_world @ vv.co
        for i in range(3):
            lo[i] = min(lo[i], w[i])
            hi[i] = max(hi[i], w[i])
print("@@EXT@@ x %.4f..%.4f  y %.4f..%.4f  z %.4f..%.4f"
      % (lo.x, hi.x, lo.y, hi.y, lo.z, hi.z))

for o in sc.objects:
    if o.type == "MESH" and (o.name.startswith("Arm_Finger") or o.name == "Arm_Gripper"):
        ws = [o.matrix_world @ vv.co for vv in o.data.vertices]
        print("@@PART@@ %-18s x %+.4f..%+.4f  y %+.4f..%+.4f  z %+.4f..%+.4f"
              % (o.name, min(w.x for w in ws), max(w.x for w in ws),
                 min(w.y for w in ws), max(w.y for w in ws),
                 min(w.z for w in ws), max(w.z for w in ws)))

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, DST))
stage_lock.record(DST)
print("@@SAVED@@ %s" % DST)
