"""Grab gate: pin the contact criterion before the claw changes shape.

Section 6 P3 says the old record's numbers (0.25009 / 0.27014) cannot be reproduced by
any current method, and that P3's first step is to fix a criterion in an executable
script before touching the claw. This is that script. The quantity is the one
qa_v2/v13_baseline_audit.py already reports, so old and new measurements are comparable:

    finger-vertex -> Idea-vertex, nearest pair, world space

Gate frames and what each one means:
    f31, f43   closed grip on the orb     -> contact, and no interpenetration
    f147       open, orb still held       -> contact at the open setting
    f155       released                   -> clearly separated

Critically, the grab target is `Idea`, not `Product` (defect D8: the fingers are 2.9
units away from Product at f31, i.e. not touching it at all). This checks Idea.

Read-only. Exits 3 on FAIL so a shape change cannot be waved through.

Usage:
    blender --background <blend> --python qa_v2/v13_grab_gate.py -- \
        --out <json> [--frames 31,43,147,155]
"""

import json
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUT = arg("--out", "qa_v2/v13_grab_gate.json")
FRAMES = [int(f) for f in arg("--frames", "31,43,147,155").split(",")]

TARGET = "Idea"
FINGERS = {"L": "Arm_Finger_L", "R": "Arm_Finger_R"}

# Bands are set from the P0 baseline measurement, which is the last state accepted as
# correct: f31/f43 = 0.01799 / 0.00614, f147 = 0.02555 / 0.02348, f155 >= 0.415.
LIMITS = {
    31: {"min": 0.002, "max": 0.060, "contact": True},
    43: {"min": 0.002, "max": 0.060, "contact": True},
    147: {"min": 0.005, "max": 0.080, "contact": True},
    155: {"min": 0.300, "max": None, "contact": False},
}

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

idea = bpy.data.objects.get(TARGET)
if idea is None:
    raise SystemExit("GRAB FATAL: no %r" % TARGET)
for name in FINGERS.values():
    if bpy.data.objects.get(name) is None:
        raise SystemExit("GRAB FATAL: no %r" % name)


def world_verts(name, depsgraph):
    ev = bpy.data.objects[name].evaluated_get(depsgraph)
    me = ev.to_mesh()
    mw = ev.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return pts


def world_bvh(name, depsgraph):
    ev = bpy.data.objects[name].evaluated_get(depsgraph)
    me = ev.to_mesh()
    mw = ev.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    tree = BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)
    ev.to_mesh_clear()
    return tree


rows = []
failures = []
for f in FRAMES:
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    iv = world_verts(TARGET, dg)
    row = {"frame": f}
    for side, name in FINGERS.items():
        fv = world_verts(name, dg)
        d = min(min((a - b).length for b in iv) for a in fv)
        row["%s_to_%s" % (side, TARGET)] = round(d, 5)
        # interpenetration: face overlap between the finger and the orb
        pairs = world_bvh(name, dg).overlap(world_bvh(TARGET, dg))
        row["%s_overlap_faces" % side] = len(pairs)
    lv = world_verts(FINGERS["L"], dg)
    rv = world_verts(FINGERS["R"], dg)
    row["tip_gap_LR"] = round(min(min((a - b).length for b in rv) for a in lv), 5)

    lim = LIMITS.get(f)
    ok = True
    if lim:
        for side in FINGERS:
            d = row["%s_to_%s" % (side, TARGET)]
            if d < lim["min"] or (lim["max"] is not None and d > lim["max"]):
                ok = False
            if lim["contact"] and row["%s_overlap_faces" % side] > 0:
                ok = False
    row["pass"] = ok
    if not ok:
        failures.append({"frame": f, "row": row})
    rows.append(row)

out = {
    "blend": os.path.abspath(bpy.data.filepath),
    "target": TARGET,
    "frames": FRAMES,
    "limits": {str(k): v for k, v in LIMITS.items()},
    "rows": rows,
    "verdict": "PASS" if not failures else "FAIL",
    "failures": failures,
}
os.makedirs(os.path.dirname(os.path.abspath(OUT)) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)

print("GRAB GATE  target=%s  frames=%s" % (TARGET, FRAMES))
print("  %-6s %-22s %-22s %-10s %-12s %s" % (
    "frame", "L->Idea (ovl)", "R->Idea (ovl)", "tip_gap_LR", "band", "verdict"))
for r in rows:
    lim = LIMITS.get(r["frame"], {})
    band = "%.3f..%s" % (lim.get("min", 0), lim.get("max", "inf")) if lim else "-"
    print("  %-6d %-9.5f (%d)%-10s %-9.5f (%d)%-10s %-10.5f %-12s %s" % (
        r["frame"], r["L_to_%s" % TARGET], r["L_overlap_faces"], "",
        r["R_to_%s" % TARGET], r["R_overlap_faces"], "",
        r["tip_gap_LR"], band, "ok" if r["pass"] else "FAIL"))
print("VERDICT %s" % out["verdict"])
print("WROTE %s" % os.path.abspath(OUT))
if failures:
    sys.exit(3)
