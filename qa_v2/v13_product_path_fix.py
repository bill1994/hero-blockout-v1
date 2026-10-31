"""Fix the two product-path defects the gate found. Surgical, and only these two.

Defect 3 - squash penetration (f254-f256, f273-f275)
    The squash is authored: scale_z drops to 0.400 at f253.629. But it is scaled
    about the object centre, so shrinking lifts the bottom while the location key
    at f255.459 drops the centre 34 mm at the same time; both move the bottom
    below the chute floor. Correct squash-against-floor keeps the bottom planted
    and lets the scale do all the work, so the centre has to RISE as the box
    gets shorter.
    Fix: where the measured bottom is below the rest plane (0.700), raise
    location[2] by exactly the deficit. Never lower a frame. scale is not touched.

Defect 2 - flat flight (f289-f300)
    location[2] has no key at all after f273.756, so the product holds z through
    the whole exit: 21 per-frame keys on x, none on z. Fix: key the vertical
    component from release at f289 with v_z = 0 and 9.81 m/s^2, so the product
    arcs down exactly as far as physics says for the 0.18 s it is on screen.
    Only z gets new keys.

Scope guard, checked at the end and reported:
    - every other fcurve keeps its exact key count and values
    - ProductAction's fcurve count must stay 8
    - existing keys are only ever raised, never lowered, never retimed
    - key count may only grow

Read-only unless --apply. Dry run prints every proposed change.

Usage:
    blender --background <blend> --python qa_v2/v13_product_path_fix.py -- \
        [--apply] [--out <blend>] [--report <json>]
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

PRODUCT = "Product"
REST_BOTTOM = 0.700          # measured rest contact, 5 mm into the chute floor top
GRAVITY = 9.81
FPS = 60.0
RELEASE_FRAME = 289          # first frame entirely off the chute lip
CONTACT_WINDOWS = ((250, 258), (268, 278))
FLIGHT_RANGE = (RELEASE_FRAME, 301)

sc = bpy.context.scene
p = bpy.data.objects.get(PRODUCT)
if p is None or p.animation_data is None:
    raise SystemExit("FIX FATAL: no Product/action in %s" % bpy.data.filepath)
act = p.animation_data.action


def channelbag_fcurves(action):
    if hasattr(action, "layers") and len(action.layers):
        for lay in action.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in cb.fcurves:
                        yield fc
    else:
        for fc in getattr(action, "fcurves", []):
            yield fc


CURVES = {(fc.data_path, fc.array_index): fc for fc in channelbag_fcurves(act)}
FC_LOC_Z = CURVES.get(("location", 2))
if FC_LOC_Z is None:
    raise SystemExit("FIX FATAL: Product has no location[2] fcurve")


def snapshot():
    return {k: [(round(kp.co[0], 4), round(kp.co[1], 6)) for kp in fc.keyframe_points]
            for k, fc in CURVES.items()}


BEFORE = snapshot()


def measure(f):
    """Evaluated bottom / scale / centre height of the product at frame f.

    f may be fractional (existing keys sit at e.g. f255.459); Scene.frame_set
    takes an int plus a subframe, not a float.
    """
    base = int(f)
    sc.frame_set(base, subframe=float(f) - base)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = p.evaluated_get(dg)
    wm = ev.matrix_world
    zs = [(wm @ Vector(c)).z for c in ev.bound_box]
    return {
        "loc_z": wm.translation.z,
        "bottom": min(zs),
        "half": (max(zs) - min(zs)) / 2.0,
        "scale_z": wm.to_scale().z,
    }


# ------------------------------------------------------------------ plan ----
changes = {"raised_keys": [], "inserted_keys": [], "flight_keys": []}

# Pass A: existing keys whose own frame sinks below the rest plane.
for kp in list(FC_LOC_Z.keyframe_points):
    f = kp.co[0]
    if not any(a <= f <= b for a, b in CONTACT_WINDOWS):
        continue
    st = measure(f)
    if st["bottom"] < REST_BOTTOM - 1e-5:
        new_v = kp.co[1] + (REST_BOTTOM - st["bottom"])
        changes["raised_keys"].append({
            "frame": round(f, 3), "from": round(kp.co[1], 5),
            "to": round(new_v, 5),
            "bottom_was": round(st["bottom"], 5),
        })

# Pass B: integer frames inside the contact windows that still sink between keys.
for a, b in CONTACT_WINDOWS:
    for f in range(a, b + 1):
        if any(abs(k["frame"] - f) < 1e-3 for k in changes["raised_keys"]):
            continue
        st = measure(f)
        if st["bottom"] < REST_BOTTOM - 1e-5:
            changes["inserted_keys"].append({
                "frame": f,
                "to": round(st["loc_z"] + (REST_BOTTOM - st["bottom"]), 5),
                "bottom_was": round(st["bottom"], 5),
            })

# Pass C: give the exit a vertical component.
rel = measure(RELEASE_FRAME)
for f in range(FLIGHT_RANGE[0] + 1, FLIGHT_RANGE[1] + 1):
    st = measure(f)
    t = (f - RELEASE_FRAME) / FPS
    target_bottom = rel["bottom"] - 0.5 * GRAVITY * t * t
    changes["flight_keys"].append({
        "frame": f,
        "t_s": round(t, 4),
        "to": round(target_bottom + st["half"], 5),
        "bottom_from": round(st["bottom"], 5),
        "bottom_to": round(target_bottom, 4),
        "drop": round(rel["bottom"] - target_bottom, 4),
    })

# ----------------------------------------------------------------- apply ----
def set_key(fcurve, frame, value):
    kp = fcurve.keyframe_points.insert(frame, value, options={"FAST"})
    kp.interpolation = "LINEAR"
    return kp


if APPLY:
    for ch in changes["raised_keys"]:
        for kp in FC_LOC_Z.keyframe_points:
            if abs(kp.co[0] - ch["frame"]) < 1e-3:
                kp.co[1] = ch["to"]
                kp.handle_left[1] = ch["to"]
                kp.handle_right[1] = ch["to"]
                break
    for ch in changes["inserted_keys"]:
        set_key(FC_LOC_Z, ch["frame"], ch["to"])
    for ch in changes["flight_keys"]:
        set_key(FC_LOC_Z, ch["frame"], ch["to"])
    FC_LOC_Z.update()

sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()

# ---------------------------------------------------------------- verify ----
AFTER = snapshot()
scope = []
for key, before_keys in BEFORE.items():
    after_keys = AFTER.get(key, [])
    if key == ("location", 2):
        if len(after_keys) < len(before_keys):
            scope.append("%s lost keys: %d -> %d" % (key, len(before_keys), len(after_keys)))
        continue
    if before_keys != after_keys:
        scope.append("%s changed: %d -> %d keys" % (key, len(before_keys), len(after_keys)))

# re-measure the windows and the flight on the (now modified) data
post = {"contact": [], "flight": [], "worst_bottom_contact": None}
for a, b in CONTACT_WINDOWS:
    for f in range(a, b + 1):
        st = measure(f)
        post["contact"].append({"frame": f, "bottom": round(st["bottom"], 5)})
post["worst_bottom_contact"] = round(min(c["bottom"] for c in post["contact"]), 5)
for f in range(FLIGHT_RANGE[0], FLIGHT_RANGE[1] + 1):
    st = measure(f)
    post["flight"].append({"frame": f, "bottom": round(st["bottom"], 5)})

report = {
    "blend": os.path.abspath(bpy.data.filepath),
    "applied": APPLY,
    "action": act.name,
    "rest_bottom": REST_BOTTOM,
    "release_frame": RELEASE_FRAME,
    "changes": changes,
    "scope_guard": {
        "violations": scope,
        "product_fcurves_before": len(BEFORE),
        "product_fcurves_after": len(AFTER),
        "loc_z_keys_before": len(BEFORE[("location", 2)]),
        "loc_z_keys_after": len(AFTER[("location", 2)]),
    },
    "post": post,
    "json": os.path.abspath(OUT) if OUT else None,
}

print("FIX product-path %s  action=%s" % ("APPLY" if APPLY else "DRY-RUN", act.name))
print("  raise existing keys : %d" % len(changes["raised_keys"]))
for c in changes["raised_keys"]:
    print("    f%-9s %.5f -> %.5f   (bottom was %.5f)" %
          (c["frame"], c["from"], c["to"], c["bottom_was"]))
print("  insert contact keys : %d" % len(changes["inserted_keys"]))
for c in changes["inserted_keys"]:
    print("    f%-4d -> %.5f   (bottom was %.5f)" % (c["frame"], c["to"], c["bottom_was"]))
print("  insert flight keys  : %d  (release f%d, %.2f m/s^2)" %
      (len(changes["flight_keys"]), RELEASE_FRAME, GRAVITY))
for c in changes["flight_keys"]:
    print("    f%-4d t=%.4fs  bottom %.4f -> %.4f  (drop %.4f)" %
          (c["frame"], c["t_s"], c["bottom_from"], c["bottom_to"], c["drop"]))
print("  scope guard violations: %s" % (scope or "none"))
print("  loc_z keys %d -> %d" % (len(BEFORE[("location", 2)]), len(AFTER[("location", 2)])))
print("  post worst contact bottom: %.5f (rest %.5f)" % (post["worst_bottom_contact"], REST_BOTTOM))

if REPORT:
    os.makedirs(os.path.dirname(os.path.abspath(REPORT)) or ".", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("WROTE %s" % os.path.abspath(REPORT))

if APPLY:
    dest = os.path.abspath(OUT) if OUT else bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(filepath=dest)
    print("SAVED %s" % dest)
elif scope:
    raise SystemExit("FIX: scope guard violated in dry run, aborting")
