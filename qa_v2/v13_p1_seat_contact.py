"""Seat the product on whatever the chute surface actually is, per frame.

Ruling: the 5 mm rest sink is interpenetration, not contact registration - the same
class as the 52 mm squash that was already rejected. But a flat +5 mm raise would be
wrong, because the chute floor is not constant: it measures 0.7068 at f234, 0.7137 at
f239 and 0.705 from f244 on (the chute inherits the +-5 mm wobble that Q4 repaired).
A single rest plane would leave f239 interpenetrating by 8 mm in the other direction.

So: per frame, find the surface under the product's footprint, and if the product is
currently touching or sunk into it, reseat it at surface + clearance. Airborne frames
(the f258-f270 bounce, the f289+ flight) are left exactly as they are - they are not
in contact and must not be pinned.

Read-only unless --apply. Saves in place by default (the deliverable evolves), and
prints every frame it touches.

Usage:
    blender --background <blend> --python qa_v2/v13_p1_seat_contact.py -- \
        [--apply] [--out <blend>] [--report <json>] \
        [--clearance 0.001] [--sink-limit 0.06] [--lift-limit 0.010]
"""

import json
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


APPLY = "--apply" in argv
OUT = arg("--out", None)
REPORT = arg("--report", None)
CLEAR = float(arg("--clearance", "0.001"))
SINK_LIMIT = float(arg("--sink-limit", "0.06"))
LIFT_LIMIT = float(arg("--lift-limit", "0.010"))
FIRST = int(arg("--first", "232"))
LAST = int(arg("--last", "305"))
SINK_BAND = 0.080
ALLOW_LOWER = '--allow-lower' in argv
skipped = []
GRID = 3

PRODUCT = "Product"
EXCLUDE = {
    PRODUCT, "Idea",
    "Arm_Finger_L", "Arm_Finger_R", "Arm_Wrist", "Arm_Forearm", "Arm_UpperArm",
    "Arm_Shoulder_Joint", "Arm_Elbow_Joint", "Arm_Base", "Arm_Mount",
    "Arm_Rings_Elbow", "Arm_Rings_Shoulder", "Arm_Seams_Fore", "Arm_Seams_Upper",
    "Product_Proxy_FitCheck", "Product_Proxy_Large",
}

sc = bpy.context.scene
p = bpy.data.objects.get(PRODUCT)
if p is None:
    raise SystemExit("SEAT FATAL: no Product in %s" % bpy.data.filepath)
act = p.animation_data.action


def fcurves_of(action):
    if hasattr(action, "layers") and len(action.layers):
        for lay in action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        yield fc
    else:
        for fc in getattr(action, "fcurves", []):
            yield fc


FC_Z = None
for fc in fcurves_of(act):
    if fc.data_path == "location" and fc.array_index == 2:
        FC_Z = fc
if FC_Z is None:
    raise SystemExit("SEAT FATAL: no location[2] on %s" % act.name)


def surfaces_under(dg, x, y, z_top=6.0, z_bottom=-2.0):
    hits = []
    z = z_top
    for _ in range(32):
        ok, loc, _n, _i, ob, _m = sc.ray_cast(
            dg, Vector((x, y, z)), Vector((0.0, 0.0, -1.0)), distance=z - z_bottom)
        if not ok:
            break
        nm = ob.name if ob else "?"
        if nm not in EXCLUDE and not ob.hide_render and not ob.hide_viewport:
            hits.append((nm, round(float(loc.z), 5)))
        z = loc.z - 1e-4
    return hits


changes = []
for f in range(FIRST, LAST + 1):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = p.evaluated_get(dg)
    wm = ev.matrix_world
    zs = [(wm @ Vector(c)).z for c in ev.bound_box]
    bottom = min(zs)
    half = (max(zs) - min(zs)) / 2.0
    s = wm.to_scale()
    if max(abs(s.x), abs(s.y), abs(s.z)) < 0.01 or p.hide_render or p.hide_viewport:
        continue
    if p.data is None:
        continue

    # sample the footprint, take the highest surface in the sink band
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for c in ev.bound_box:
        w = wm @ Vector(c)
        for i in range(3):
            lo[i] = min(lo[i], w[i])
            hi[i] = max(hi[i], w[i])
    best = None
    # Sample the footprint edges, not just its middle. At f289 the product's centre
    # of mass is already past the chute lip (x 3.35 against a chute ending at 3.40)
    # while its trailing 5 cm is still inside the channel and 4 mm under the floor.
    # Columns at 1/6, 1/2, 5/6 all land beyond the lip and miss that contact, which
    # is exactly the frame the intersection gate flagged.
    FRACS = (0.02, 0.5, 0.98)
    for fx in FRACS:
        for fy in FRACS:
            x = lo.x + (hi.x - lo.x) * fx
            y = lo.y + (hi.y - lo.y) * fy
            cand = [(n, z) for n, z in surfaces_under(dg, x, y) if z <= bottom + SINK_BAND]
            if cand:
                n, z = max(cand, key=lambda t: t[1])
                if best is None or z > best[1]:
                    best = (n, z)
    if best is None:
        continue

    support_obj, support_z = best
    gap = bottom - support_z
    if gap < -SINK_LIMIT or gap > LIFT_LIMIT:
        # airborne or already clear - not ours to move
        continue

    target_bottom = support_z + CLEAR
    delta = target_bottom - bottom
    if abs(delta) < 1e-5:
        continue
    if delta < 0 and not ALLOW_LOWER:
        # Only sinking is a defect. A frame already sitting slightly above the
        # surface is the settle/lift-off read, and pulling it down would flatten
        # the animation to make a number look neat.
        skipped.append({"frame": f, "gap": round(gap, 5),
                        "why": "already clear of the surface"})
        continue
    changes.append({
        "frame": f, "support": support_obj, "support_z": round(support_z, 5),
        "bottom_was": round(bottom, 5), "bottom_to": round(target_bottom, 5),
        "delta": round(delta, 5), "half": round(half, 5),
    })

print("SEAT %s  action=%s  frames %d..%d  clearance=%.4f" % (
    "APPLY" if APPLY else "DRY", act.name, FIRST, LAST, CLEAR))
print("  frames to reseat: %d  (skipped %d already clear)" % (len(changes), len(skipped)))
for c in changes:
    print("    f%-4d %-16s support=%.5f  %.5f -> %.5f  (d=%+.5f)" % (
        c["frame"], c["support"], c["support_z"], c["bottom_was"], c["bottom_to"], c["delta"]))

if APPLY and changes:
    for c in changes:
        # Re-measure here instead of trusting the plan's delta. Inserting a key makes
        # Blender recompute the neighbouring bezier handles, so the curve at the next
        # frame is no longer the curve the plan was computed against; adding the plan's
        # delta accumulates error. Measured: doing that lifted 15 RESTING frames into
        # ARC and left the seat 3-5 cm high. Re-measuring every frame is the fix.
        sc.frame_set(c["frame"])
        dg = bpy.context.evaluated_depsgraph_get()
        ev = p.evaluated_get(dg)
        wm = ev.matrix_world
        cur_bottom = min((wm @ Vector(cc)).z for cc in ev.bound_box)
        target = c["support_z"] + CLEAR
        delta = target - cur_bottom
        if abs(delta) < 1e-6:
            continue
        kp = FC_Z.keyframe_points.insert(c["frame"], wm.translation.z + delta,
                                         options={"FAST"})
        kp.interpolation = "LINEAR"
    FC_Z.update()
    sc.frame_set(1)
    dest = os.path.abspath(OUT) if OUT else bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(filepath=dest)
    print("SAVED %s" % dest)

if REPORT:
    os.makedirs(os.path.dirname(os.path.abspath(REPORT)) or ".", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump({"blend": os.path.abspath(bpy.data.filepath), "applied": APPLY,
                   "clearance": CLEAR, "changes": changes, "skipped": skipped}, fh, indent=2)
    print("WROTE %s" % os.path.abspath(REPORT))

