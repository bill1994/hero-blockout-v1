"""Hard-surface intersection gate: does the product clip the machine?

The product-path gate answers "is it supported and does it fall". It cannot answer
"does it cut through the shell", because it only ever casts rays downward. The
product is a 1.0 m cube emerging through an outlet opening that is 0.91 m tall, so
this question is not academic: during the emergence frames the box is taller than
the hole it comes out of.

Method: BVHTree.FromObject on the evaluated meshes, then BVHTree.overlap. That
reports overlapping face pairs without touching the scene - no booleans, no
modifiers, nothing saved.

Runs per frame, reports every frame with overlap and which object it overlaps.

Read-only.

Usage:
    blender --background <blend> --python qa_v2/v13_penetration_check.py -- \
        --out <json> [--first 232] [--last 327] \
        [--target Product] [--against Machine_Body,Machine_Chute]
"""

import json
import os
import sys

import bpy
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUT = arg("--out", "qa_v2/v13_penetration.json")
FIRST = int(arg("--first", "232"))
LAST = int(arg("--last", "327"))
TARGET = arg("--target", "Product")
AGAINST = [s for s in arg(
    "--against", "Machine_Body,Machine_Chute,P1_ChuteSeat,P1_ShoulderBay").split(",") if s]

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()

missing = [n for n in AGAINST if bpy.data.objects.get(n) is None]
if bpy.data.objects.get(TARGET) is None:
    raise SystemExit("PEN FATAL: target %r missing" % TARGET)

def world_bvh(obj, depsgraph):
    """BVH in world space, explicitly.

    BVHTree.FromObject ignores the parent chain, so a piece parented to the body
    (as the P1 junction pieces are) gets compared at the wrong place and reports
    overlap on every frame. Building from world-space polygons removes the
    ambiguity: what is tested is what renders.
    """
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    mw = ev.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    tree = BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)
    ev.to_mesh_clear()
    return tree


rows = []
per_object = {}
for f in range(FIRST, LAST + 1):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    tob = bpy.data.objects[TARGET]
    tv = world_bvh(tob, dg)
    hits = {}
    for name in AGAINST:
        o = bpy.data.objects.get(name)
        if o is None:
            continue
        ov = world_bvh(o, dg)
        pairs = tv.overlap(ov)
        if pairs:
            hits[name] = len(pairs)
            per_object[name] = per_object.get(name, 0) + 1
    if hits:
        rows.append({"frame": f, "hits": hits})

summary = {
    "frames_checked": LAST - FIRST + 1,
    "frames_with_overlap": len(rows),
    "per_object_frames": per_object,
    "first": rows[0] if rows else None,
    "last": rows[-1] if rows else None,
    "missing_objects": missing,
    "verdict": "FAIL" if rows else "PASS",
}

os.makedirs(os.path.dirname(os.path.abspath(OUT)) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"blend": os.path.abspath(bpy.data.filepath),
               "target": TARGET, "against": AGAINST,
               "range": [FIRST, LAST], "summary": summary, "rows": rows}, fh, indent=2)

print("PEN CHECK %s vs %s  [%d..%d]" % (TARGET, ",".join(AGAINST), FIRST, LAST))
if missing:
    print("  missing: %s" % missing)
print("  frames with overlap: %d / %d" % (len(rows), LAST - FIRST + 1))
for k, v in sorted(per_object.items()):
    print("    %-22s %d frames" % (k, v))
if rows:
    frames = [r["frame"] for r in rows]
    print("  frame list: %s" % frames)
print("VERDICT %s" % summary["verdict"])
print("WROTE %s" % os.path.abspath(OUT))
if rows:
    sys.exit(3)
