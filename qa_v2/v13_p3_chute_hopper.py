"""P3a: chute split into a short scoop plus a low rail, and the hopper rebuilt as a bowl.

Chute (section 4.5 ruling)
    Support length stays frozen at x 1.16..3.40 - the product needs it from f232 to
    f289, and shortening it would leave the product in the air for 36 frames. What
    changes is the read: x 1.16..2.10 becomes a short cream scoop with an orange
    interior, and x 2.10..3.40 becomes a low, narrow, dark rail.
    The channel floor stays at **z 0.705**, because qa_v2/v13_p1_seat_contact.py seated
    every contact frame against that surface; moving it would invalidate 38 keys.

Hopper (section 5.2 item 4)
    The current object is a thin-walled open cone (visible through to the far wall) in
    MAT_Arm grey. Rebuilt as a cream bowl: solid pedestal (r 0.28) whose top face at
    **z 2.35 is the orb's rest plane**, a flaring bowl above it, and a thick rolled rim.
    The pedestal top and the bowl's inner radius there are measured after the rebuild,
    because the orb sits on them (f156, 189 frames near the axis).

    The hopper carries its own z animation (26 keys, Q4's loop closure), so the mesh is
    built in local space about its object origin at z 2.45, not in world space - writing
    world coordinates into a translated object is the mistake that silently moved the
    window cutter in P2.

Usage:
    blender --background <blend> --python qa_v2/v13_p3_chute_hopper.py -- \
        [--out <blend>] [--report <json>] [--no-apply]
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


APPLY = "--no-apply" not in argv
OUT = arg("--out", None)
REPORT = arg("--report", None)

# chute
SCOOP_X = (1.16, 2.10)
RAIL_X = (2.10, 3.40)
CH_Y = 0.68
CH_FLOOR_TOP = 0.705
CH_BOTTOM = 0.505
CH_WALL_TOP = 0.95
RAIL_Y = 0.52
RAIL_BOTTOM = 0.605

# hopper
PED_R = 0.28
PED_TOP = 2.35
PED_BOTTOM = 2.00
BOWL_TOP = 2.89
BOWL_R_IN = 0.62
WALL = 0.07
SEG = 32

sc = bpy.context.scene
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()


# ------------------------------------------------------------------- chute ----
def build_chute():
    o = bpy.data.objects.get("Machine_Chute")
    if o is None:
        return None
    mw = o.matrix_world.copy()
    inv = mw.inverted()

    cream = bpy.data.materials.get("MAT_Body")
    amber = bpy.data.materials.get("MAT_Color_Amber")
    dark = bpy.data.materials.get("MAT_Arm_Dark")

    me = o.data
    bm = bmesh.new()
    me.materials.clear()
    for m in (cream, amber, dark):
        if m:
            me.materials.append(m)
    I_CREAM = 0
    I_AMBER = 1
    I_DARK = 2

    def box(x0, x1, y0, y1, z0, z1, top_index=None, mat=I_CREAM):
        """Axis-aligned box in world coords; `top_index` repaints the +Z face."""
        def w(v):
            return inv @ Vector(v)
        v = [bm.verts.new(w((x, y, z)))
             for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        # index order: (x0y0z0),(x0y0z1),(x0y1z0),(x0y1z1),(x1y0z0),(x1y0z1),(x1y1z0),(x1y1z1)
        faces = [
            (0, 1, 3, 2, -1),   # x0
            (4, 6, 7, 5, -1),   # x1
            (0, 4, 5, 1, -1),   # y0
            (2, 3, 7, 6, -1),   # y1
            (0, 2, 6, 4, mat),  # z0
            (1, 5, 7, 3, top_index if top_index is not None else mat),  # z1
        ]
        for f in faces:
            face = bm.faces.new([v[i] for i in f[:4]])
            # f[4] == -1 is the 'use this box's default' sentinel, not an index
            face.material_index = f[4] if f[4] >= 0 else mat
        return v

    # scoop: cream shell, orange channel interior
    box(SCOOP_X[0], SCOOP_X[1], -CH_Y, CH_Y, CH_BOTTOM, CH_FLOOR_TOP, top_index=I_AMBER)
    # side walls, cream, inside faces left cream (the reference's orange is the trough)
    # walls start 5 mm inside the floor: a coplanar seam gets welded, and the bevel
    # modifier then builds self-intersecting geometry on the zero-thickness joint,
    # which makes every overlap test on this object unreliable.
    box(SCOOP_X[0], SCOOP_X[1], -CH_Y, -CH_Y + 0.06, CH_FLOOR_TOP - 0.005, CH_WALL_TOP, mat=I_CREAM)
    box(SCOOP_X[0], SCOOP_X[1], CH_Y - 0.06, CH_Y, CH_FLOOR_TOP - 0.005, CH_WALL_TOP, mat=I_CREAM)
    # rail: low, narrow, dark; its top is the same support plane
    box(RAIL_X[0], RAIL_X[1], -RAIL_Y, RAIL_Y, RAIL_BOTTOM, CH_FLOOR_TOP, mat=I_DARK)

    # deliberately no remove_doubles here: welding the boxes at their shared seams
    # is what created the self-intersecting bevel. Loose parts are fine for a prop.
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return o


# ------------------------------------------------------------------ hopper ----
def build_hopper():
    o = bpy.data.objects.get("Machine_Hopper")
    if o is None:
        return None
    mw = o.matrix_world.copy()
    inv = mw.inverted()
    me = o.data
    me.materials.clear()
    cream = bpy.data.materials.get("MAT_Body")
    if cream:
        me.materials.append(cream)

    bm = bmesh.new()

    def ring(z, r, n=SEG):
        return [bm.verts.new(inv @ Vector((r * math.cos(2 * math.pi * i / n),
                                           r * math.sin(2 * math.pi * i / n), z)))
                for i in range(n)]

    def bridge(inner_a, inner_b, flip=False):
        n = len(inner_a)
        for i in range(n):
            j = (i + 1) % n
            if flip:
                bm.faces.new((inner_a[i], inner_b[i], inner_b[j], inner_a[j]))
            else:
                bm.faces.new((inner_a[i], inner_a[j], inner_b[j], inner_b[i]))

    # pedestal: solid cylinder, top face IS the orb rest plane
    ped_bot = ring(PED_BOTTOM, PED_R)
    ped_top = ring(PED_TOP, PED_R)
    bm.faces.new(list(reversed(ped_bot)))
    bridge(ped_bot, ped_top, flip=True)
    bm.faces.new(ped_top)

    # bowl: inner surface flares from the pedestal to the rim
    inner_lo = ring(PED_TOP, PED_R)
    inner_hi = ring(BOWL_TOP, BOWL_R_IN)
    bridge(inner_lo, inner_hi)
    outer_lo = ring(PED_TOP, PED_R + WALL)
    outer_hi = ring(BOWL_TOP, BOWL_R_IN + WALL)
    bridge(outer_hi, outer_lo)

    # thick rolled rim: outer lip pulled out and down a little
    lip_out = ring(BOWL_TOP + 0.015, BOWL_R_IN + WALL + 0.055)
    bridge(outer_hi, lip_out)
    lip_bot = ring(BOWL_TOP - 0.035, BOWL_R_IN + WALL + 0.030)
    bridge(lip_out, lip_bot)
    bridge(lip_bot, outer_hi, flip=True)

    # underside of the bowl back to the rim, so the shell is closed
    bridge(outer_lo, ring(PED_TOP - 0.001, PED_R + WALL * 0.5), flip=True)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return o


chute = build_chute() if APPLY else None
hopper = build_hopper() if APPLY else None

report = {"applied": APPLY,
          "chute": {"scoop_x": SCOOP_X, "rail_x": RAIL_X, "floor_top": CH_FLOOR_TOP,
                    "rail_y": RAIL_Y, "rail_bottom": RAIL_BOTTOM},
          "hopper": {"pedestal_r": PED_R, "pedestal_top": PED_TOP,
                     "bowl_top": BOWL_TOP, "bowl_r_in": BOWL_R_IN, "wall": WALL}}

if APPLY:
    dgr = bpy.context.evaluated_depsgraph_get()

    def measure(name):
        o = bpy.data.objects.get(name)
        ev = o.evaluated_get(dgr)
        me2 = ev.to_mesh()
        mw2 = ev.matrix_world
        pts = [mw2 @ v.co for v in me2.vertices]
        hi = max(p.z for p in pts)
        lo = min(p.z for p in pts)
        rmax = max(math.hypot(p.x, p.y) for p in pts)
        ev.to_mesh_clear()
        return {"z": [round(lo, 4), round(hi, 4)], "r_max": round(rmax, 4)}

    report["measured"] = {"chute": measure("Machine_Chute"),
                          "hopper": measure("Machine_Hopper")}

    # the orb must still sit on the pedestal: ray straight down the axis
    hits = []
    z = 3.6
    for _ in range(8):
        ok, loc, _n, _i, ob, _m = sc.ray_cast(dgr, Vector((0.0, 0.0, z)),
                                              Vector((0.0, 0.0, -1.0)), distance=z + 2.0)
        if not ok:
            break
        hits.append([round(float(loc.z), 4), str(ob.name)])
        z = float(loc.z) - 0.001
    report["axis_hits"] = hits

print("P3A %s" % ("APPLY" if APPLY else "DRY"))
print("  chute: scoop x %s -> %.3f, rail x %s (top %.3f), rail y +-%.2f" % (
    SCOOP_X, SCOOP_X[1], RAIL_X, CH_FLOOR_TOP, RAIL_Y))
print("  hopper: pedestal r %.2f top %.2f -> bowl top %.2f r %.2f wall %.2f" % (
    PED_R, PED_TOP, BOWL_TOP, BOWL_R_IN, WALL))
if APPLY:
    print("  measured: %s" % json.dumps(report["measured"]))
    print("  axis hits: %s" % report["axis_hits"])

if REPORT:
    os.makedirs(os.path.dirname(os.path.abspath(REPORT)) or ".", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("WROTE %s" % os.path.abspath(REPORT))

if APPLY:
    dest = os.path.abspath(OUT) if OUT else bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(filepath=dest)
    print("SAVED %s" % dest)


