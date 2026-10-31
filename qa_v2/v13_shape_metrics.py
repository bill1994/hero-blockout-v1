"""Shape metrics for the v13 reference-match gates.

Measures the front-elevation shape ratios of the machine the same way
qa_v2/v13_ref_contract.py measures the reference sheet, so the two files can be
compared key-by-key (body_w_to_h, window_w_to_body_w, ...).

Read-only: opens the .blend, measures, writes JSON, never saves.

Usage:
    blender --background <blend> --python qa_v2/v13_shape_metrics.py -- \
        --out qa_v2/v13_shape_metrics_<tag>.json [--tag <tag>] [--frame 1]
"""

import json
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUT = arg("--out", "qa_v2/v13_shape_metrics.json")
TAG = arg("--tag", "unknown")
FRAME = int(arg("--frame", "1"))

sc = bpy.context.scene
sc.frame_set(FRAME)
dg = bpy.context.evaluated_depsgraph_get()


def wbb(name):
    """World-space bounding box of the evaluated object."""
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    ev = o.evaluated_get(dg)
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for c in ev.bound_box:
        w = ev.matrix_world @ Vector(c)
        for i in range(3):
            lo[i] = min(lo[i], w[i])
            hi[i] = max(hi[i], w[i])
    return lo, hi


def dim(name):
    bb = wbb(name)
    if bb is None:
        return None
    lo, hi = bb
    return {
        "min": [round(v, 4) for v in lo],
        "max": [round(v, 4) for v in hi],
        "w": round(hi.x - lo.x, 4),
        "h": round(hi.z - lo.z, 4),
        "d": round(hi.y - lo.y, 4),
    }


parts = {n: dim(n) for n in (
    "Machine_Body",
    "Machine_WindowGlow",
    "Machine_WindowFrame",
    "Machine_Hopper",
    "Machine_Chute",
    "Machine_Base",
    "Arm_Base",
    "Arm_Finger_L",
    "Arm_Finger_R",
)}

body = parts["Machine_Body"]
ratios = {}
if body and body["w"] and body["h"]:
    bw, bh = body["w"], body["h"]
    ratios["body_w_to_h"] = round(bw / bh, 4)
    for key, part in (
        ("window_w_to_body_w", ("Machine_WindowGlow", "w")),
        ("window_h_to_body_h", ("Machine_WindowGlow", "h")),
        ("hopper_dia_to_body_w", ("Machine_Hopper", "w")),
        ("chute_len_to_body_w", ("Machine_Chute", "w")),
        ("base_h_to_body_h", ("Machine_Base", "h")),
    ):
        p = parts[part[0]]
        if p:
            ratios[key] = round(p[part[1]] / (bw if "body_w" in key else bh), 4)
    wg = parts["Machine_WindowGlow"]
    if wg and wg["w"]:
        ratios["window_h_to_w"] = round(wg["h"] / wg["w"], 4)
    # how far the window centre sits from the body centre, as a fraction of body h
    if wg:
        ratios["window_centre_dz_to_body_h"] = round(
            ((wg["min"][2] + wg["max"][2]) / 2 - (body["min"][2] + body["max"][2]) / 2) / bh, 4)
    # arm reach: leftmost point of the claw relative to the body's left face
    fl = parts["Arm_Finger_L"]
    if fl:
        ratios["claw_reach_beyond_body_w"] = round((body["min"][0] - fl["min"][0]) / bw, 4)

out = {
    "tag": TAG,
    "blend": os.path.abspath(bpy.data.filepath),
    "frame": FRAME,
    "parts": parts,
    "ratios": ratios,
}

os.makedirs(os.path.dirname(os.path.abspath(OUT)) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)

print("SHAPE %s" % TAG)
for k, v in ratios.items():
    print("   %-28s %s" % (k, v))
print("WROTE %s" % os.path.abspath(OUT))
