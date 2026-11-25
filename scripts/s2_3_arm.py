"""S2.3 - four stubby fingers, a proper arm root blob, and an arm that stops
at the reference height.

Three separate faults, measured against the reference:

1. fingers: v7 has three, the reference has four. Rebuilt as four 2-segment
   fingers fanned in the XZ plane below the palm (root radius 0.016 tapering to
   0.007), tips at x -0.176..-0.106 / z 0.615..0.680 against the reference's
   -0.19..-0.10 / 0.62..0.71. Named A..D left to right so the stage-3 pairing
   Finger_L -> A+D, Finger_R -> B+C stays a two-sided grip.
2. arm root: the reference's outermost point is x -0.5005 (tripo_part_1, the
   leg blob), ours was -0.468. The leg is rebuilt as a 3-ring loft - narrow on
   the base platter, bulging out to -0.5005 at z 0.59, tapering again at the
   top - so it reads as a chunky shoulder blob instead of a knife blade.
3. height: ours topped out at z 0.769 (the elbow ball, r 0.044 at z 0.725),
   the reference at 0.754 (part_4's tube). The elbow drops to z 0.709 so the
   0.044 ball tops out at 0.753; the wrist stays at 0.706 so the finger
   cluster keeps its height.

Deviation from reference/v4_rigspec.json is recorded in reference/v5_rigspec.json.
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

SRC = os.path.join(ROOT, "versions", "rebuild_v7_s2c.blend")
DST = os.path.join(ROOT, "versions", "rebuild_v7_s2d.blend")

SHOULDER = Vector((-0.4180, -0.0500, 0.6150))
ELBOW = Vector((-0.2260, -0.0370, 0.7090))
WRIST = Vector((-0.1630, -0.0360, 0.7060))
PALM = Vector((-0.1500, -0.0340, 0.6980))

SHOULDER_R = 0.058
ELBOW_R = 0.044
UPPER_R = 0.044
FINGER_ROOT_R = 0.016
FINGER_MID_R = 0.0115
FINGER_TIP_R = 0.007
FINGER_ARC_R = 0.026
FINGER_ANGLES = (-45.0, -15.0, 15.0, 45.0)
FINGER_Y = (-0.012, -0.004, 0.004, 0.012)

# leg blob, bottom to top: z, x0a, x0b, y0a, y0b. The left edge follows the
# reference silhouette measured row by row off ref_front.png:
#   z 0.50 -> -0.4349, z 0.55 -> -0.4589, z 0.60 -> -0.4877, z 0.65 -> -0.4956
# so the blob leans out as it rises and is widest at the shoulder, not at
# mid height (a bulge at 0.61 put 40 mm of extra leg into the silhouette).
LEG_RINGS = (
    (0.4455, -0.4300, -0.3350, -0.0990, -0.0070),
    (0.5200, -0.4400, -0.3270, -0.1000, -0.0050),
    (0.6000, -0.4877, -0.3250, -0.1000, -0.0050),
    (0.6820, -0.5005, -0.3350, -0.0900, -0.0150),
)

SEGMENT_VERTS = 8


def mat(name):
    return bpy.data.materials.get(name)


def tris_of(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def link(name, bm, material):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def tube(name, p0, p1, r, material, verts=SEGMENT_VERTS):
    """Open-ended round tube between two points, quads only."""
    quat = (p1 - p0).to_track_quat("Z", "Y")
    bm = bmesh.new()
    rings = []
    for p in (p0, p1):
        ring = []
        for k in range(verts):
            a = 2.0 * math.pi * k / verts
            ring.append(bm.verts.new(p + quat @ Vector((r * math.cos(a), r * math.sin(a), 0.0))))
        rings.append(ring)
    for k in range(verts):
        k2 = (k + 1) % verts
        bm.faces.new((rings[0][k], rings[0][k2], rings[1][k2], rings[1][k]))
    return link(name, bm, material)


def cone_seg(name, p0, p1, r0, r1, material, verts=SEGMENT_VERTS):
    """Tapered segment, closed with triangle fans so no ngons are added."""
    quat = (p1 - p0).to_track_quat("Z", "Y")
    bm = bmesh.new()
    rings = []
    for p, r in ((p0, r0), (p1, r1)):
        ring = []
        for k in range(verts):
            a = 2.0 * math.pi * k / verts
            ring.append(bm.verts.new(p + quat @ Vector((r * math.cos(a), r * math.sin(a), 0.0))))
        rings.append(ring)
    for k in range(verts):
        k2 = (k + 1) % verts
        bm.faces.new((rings[0][k], rings[0][k2], rings[1][k2], rings[1][k]))
    c0 = bm.verts.new(p0)
    c1 = bm.verts.new(p1)
    for k in range(verts):
        k2 = (k + 1) % verts
        bm.faces.new((c0, rings[0][k2], rings[0][k]))
        bm.faces.new((c1, rings[1][k], rings[1][k2]))
    return link(name, bm, material)


def sphere(name, c, r, material, segs=10, rings=6):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    bmesh.ops.translate(bm, verts=bm.verts, vec=c)
    return link(name, bm, material)


def blob(name, rings, material):
    """Loft a stack of 4-point rectangular rings, capped top and bottom."""
    bm = bmesh.new()
    loops = []
    for z, xa, xb, ya, yb in rings:
        loops.append([bm.verts.new(Vector((x, y, z))) for x, y in
                      ((xa, ya), (xb, ya), (xb, yb), (xa, yb))])
    for i in range(len(loops) - 1):
        lo, hi = loops[i], loops[i + 1]
        for k in range(4):
            k2 = (k + 1) % 4
            bm.faces.new((lo[k], lo[k2], hi[k2], hi[k]))
    bm.faces.new(tuple(reversed(loops[0])))
    bm.faces.new(tuple(loops[-1]))
    return link(name, bm, material)


def drop(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return 0
    n = tris_of(ob)
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me.users == 0:
        bpy.data.meshes.remove(me)
    return n


stage_lock.verify(SRC)
bpy.ops.wm.open_mainfile(filepath=SRC)

m_shell = mat("M_Shell")
m_metal = mat("M_Metal")
m_dark = mat("M_ShellDk")

before = sum(tris_of(o) for o in bpy.data.objects if o.type == "MESH")

# --- 1. fingers ----------------------------------------------------------
removed = 0
for tag in "ABC":
    for s in ("s1", "s2"):
        removed += drop("Arm_Finger_%s_%s" % (tag, s))
print("[s2.3] removed %d finger tris" % removed)

tips = {}
for k, tag in enumerate("ABCD"):
    phi = math.radians(FINGER_ANGLES[k])
    radial = Vector((math.sin(phi), 0.0, -math.cos(phi)))
    root = PALM + radial * FINGER_ARC_R + Vector((0.0, FINGER_Y[k], 0.0))
    knee = root + radial * 0.024 + Vector((0.0, 0.0, -0.010))
    tip = knee + radial * 0.012 + Vector((0.0, 0.0, -0.018))
    cone_seg("Arm_Finger_%s_s1" % tag, root, knee, FINGER_ROOT_R, FINGER_MID_R, m_metal)
    cone_seg("Arm_Finger_%s_s2" % tag, knee, tip, FINGER_MID_R, FINGER_TIP_R, m_dark)
    tips[tag] = tip
    print("[s2.3] finger %s phi %5.1f  root (%.4f,%.4f,%.4f)  tip (%.4f,%.4f,%.4f)"
          % (tag, FINGER_ANGLES[k], root.x, root.y, root.z, tip.x, tip.y, tip.z))

# --- 2. arm root blob ----------------------------------------------------
drop("Arm_Riser")
leg = blob("Arm_Riser", LEG_RINGS, m_shell)
bev = leg.modifiers.new(name="Bevel", type="BEVEL")
bev.width = 0.014
bev.segments = 3
bev.limit_method = "ANGLE"
bpy.context.view_layer.objects.active = leg
leg.select_set(True)
bpy.ops.object.modifier_apply(modifier=bev.name)
leg.select_set(False)

# --- 3. joints, upper arm, forearm --------------------------------------
drop("Arm_Shoulder_Joint")
sphere("Arm_Shoulder_Joint", SHOULDER, SHOULDER_R, m_shell)

drop("Arm_Elbow_Joint")
sphere("Arm_Elbow_Joint", ELBOW, ELBOW_R, m_shell)

drop("Arm_UpperArm")
tube("Arm_UpperArm", SHOULDER, ELBOW, UPPER_R, m_shell)

# the wrist and gripper stay put; only the forearm box follows the elbow down
fa = bpy.data.objects.get("Arm_Forearm")
if fa is not None:
    me = fa.data
    zs = [vv.co.z for vv in me.vertices]
    dz = (ELBOW.z + WRIST.z) / 2.0 - (max(zs) + min(zs)) / 2.0
    for vv in me.vertices:
        vv.co.z += dz
    me.update()
    print("[s2.3] forearm shifted %.4f in z" % dz)

# the reference's palm block spans z 0.673..0.743; ours sat 10 mm lower, which
# showed up as a 25 mm dip in the silhouette column at x -0.12
gr = bpy.data.objects.get("Arm_Gripper")
if gr is not None:
    for vv in gr.data.vertices:
        vv.co.z += 0.010
    gr.data.update()
    print("[s2.3] gripper raised 0.0100")

bpy.context.view_layer.update()

# --- verification --------------------------------------------------------
ws = {}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    for vv in o.data.vertices:
        p = o.matrix_world @ vv.co
        for tag, hit in (("xmin", p.x < ws.get("xmin", (9,))[0]),
                         ("xmax", p.x > ws.get("xmax", (-9,))[0]),
                         ("zmax", p.z > ws.get("zmax", (-9,))[0]),
                         ("zmin", p.z < ws.get("zmin", (9,))[0])):
            if hit:
                ws[tag] = (p.x if tag in ("xmin", "xmax") else p.z, o.name)
print("[s2.3] scene extremes %s" % {k: (round(val[0], 4), val[1]) for k, val in ws.items()})

fx = [o for o in bpy.data.objects if o.name.startswith("Arm_Finger_")]
fx_min = min((o.matrix_world @ vv.co).x for o in fx for vv in o.data.vertices)
fx_max = max((o.matrix_world @ vv.co).x for o in fx for vv in o.data.vertices)
fz_min = min((o.matrix_world @ vv.co).z for o in fx for vv in o.data.vertices)
fz_max = max((o.matrix_world @ vv.co).z for o in fx for vv in o.data.vertices)
print("[s2.3] finger cluster x %.4f..%.4f  z %.4f..%.4f  (reference -0.19..-0.10 / 0.62..0.71)"
      % (fx_min, fx_max, fz_min, fz_max))
print("[s2.3] finger tips %s" % {k: (round(t.x, 4), round(t.y, 4), round(t.z, 4))
                                 for k, t in tips.items()})

after = sum(tris_of(o) for o in bpy.data.objects if o.type == "MESH")
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
quads = sum(1 for o in meshes for p in o.data.polygons if len(p.vertices) == 4)
ngons = sum(1 for o in meshes for p in o.data.polygons if len(p.vertices) > 4)
print("[s2.3] tris %d -> %d  quads %d  ngons %d  objects %d"
      % (before, after, quads, ngons, len(meshes)))

bpy.ops.wm.save_as_mainfile(filepath=DST)
stage_lock.record(DST)
print("[s2.3] wrote %s" % DST)
