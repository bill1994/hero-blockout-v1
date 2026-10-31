"""P1 shell inventory: what is mounted on each face of Machine_Body.

Narrowing the shell from 2.32 to 1.80 moves both x faces inward by 0.26 m. Anything
sitting on those faces detaches unless it is either remapped onto the new surface or
bridged by one of the three junction pieces section 12 Q1 asks for (shoulder bay,
chute seat, hopper seat). This records the current attachment set so the same file
can be run after the rebuild and diffed - a part that stops touching the body is a
part that fell off.

The body also gains a superellipse profile in P1, so "touching the face plane" is
measured with a tolerance band rather than exact contact.

Read-only: opens the .blend, measures, writes JSON, never saves.

Usage:
    blender --background <blend> --python qa_v2/v13_p1_shell_inventory.py -- \
        --out qa_v2/v13_p1_shell_inventory.json [--band 0.03]
"""

import json
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUT = arg("--out", "qa_v2/v13_p1_shell_inventory.json")
BAND = float(arg("--band", "0.03"))
BODY = "Machine_Body"

sc = bpy.context.scene
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()

bo = bpy.data.objects[BODY]
bev = bo.evaluated_get(dg)
bme = bev.to_mesh()
body_local = [list(v.co) for v in bme.vertices]
bev.to_mesh_clear()

blo = Vector((1e9, 1e9, 1e9))
bhi = Vector((-1e9, -1e9, -1e9))
for c in bev.bound_box:
    w = bev.matrix_world @ Vector(c)
    for i in range(3):
        blo[i] = min(blo[i], w[i])
        bhi[i] = max(bhi[i], w[i])

body_info = {
    "verts": len(body_local),
    "local_min": [round(min(v[i] for v in body_local), 4) for i in range(3)],
    "local_max": [round(max(v[i] for v in body_local), 4) for i in range(3)],
    "world_min": [round(v, 4) for v in blo],
    "world_max": [round(v, 4) for v in bhi],
    "modifiers": [{"type": m.type, "name": m.name} for m in bo.modifiers],
    "material_slots": [s.material.name if s.material else None for s in bo.material_slots],
}

faces = {"left": [], "right": [], "top": [], "bottom": [], "front": [], "back": []}
for o in bpy.data.objects:
    if o.type != "MESH" or o.name == BODY:
        continue
    ev = o.evaluated_get(dg)
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for c in ev.bound_box:
        w = ev.matrix_world @ Vector(c)
        for i in range(3):
            lo[i] = min(lo[i], w[i])
            hi[i] = max(hi[i], w[i])
    rec = {"name": o.name,
           "bbox": [[round(v, 3) for v in lo], [round(v, 3) for v in hi]]}
    # a part is "mounted" on a face when its bbox reaches into that face's band
    if lo.x <= blo.x + BAND and hi.x >= blo.x - BAND:
        faces["left"].append(rec)
    if hi.x >= bhi.x - BAND and lo.x <= bhi.x + BAND:
        faces["right"].append(rec)
    if hi.z >= bhi.z - BAND and lo.z <= bhi.z + BAND:
        faces["top"].append(rec)
    if lo.z <= blo.z + BAND and hi.z >= blo.z - BAND:
        faces["bottom"].append(rec)
    if lo.y <= blo.y + BAND and hi.y >= blo.y - BAND:
        faces["front"].append(rec)
    if hi.y >= bhi.y - BAND and lo.y <= bhi.y + BAND:
        faces["back"].append(rec)

# how far the arm and chute reach past the body faces (the gaps the junctions bridge)
arm = bpy.data.objects.get("Arm_Base")
chute = bpy.data.objects.get("Machine_Chute")
gaps = {}
if arm:
    ev = arm.evaluated_get(dg)
    amin = min((ev.matrix_world @ Vector(c)).x for c in ev.bound_box)
    gaps["left_gap_after_narrow"] = round(blo.x - (-0.90), 4) if True else None
    gaps["arm_outer_min_x"] = round(amin, 4)
    gaps["arm_reaches_past_body_left_face"] = round(blo.x - amin, 4)
if chute:
    ev = chute.evaluated_get(dg)
    cmax = max((ev.matrix_world @ Vector(c)).x for c in ev.bound_box)
    cmin = min((ev.matrix_world @ Vector(c)).x for c in ev.bound_box)
    gaps["chute_x"] = [round(cmin, 4), round(cmax, 4)]
    gaps["chute_mouth_inside_body_by"] = round(bhi.x - cmin, 4)

out = {
    "blend": os.path.abspath(bpy.data.filepath),
    "band": BAND,
    "body": body_info,
    "mounted": {k: [r["name"] for r in v] for k, v in faces.items()},
    "mounted_detail": faces,
    "gaps": gaps,
}
os.makedirs(os.path.dirname(os.path.abspath(OUT)) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)

print("SHELL INVENTORY")
print("  body verts=%d local=%s..%s world=%s..%s" % (
    body_info["verts"], body_info["local_min"], body_info["local_max"],
    body_info["world_min"], body_info["world_max"]))
print("  modifiers: %s" % body_info["modifiers"])
print("  material slots: %s" % body_info["material_slots"])
for k in ("left", "right", "top", "bottom", "front", "back"):
    print("  %-7s (%2d): %s" % (k, len(faces[k]), ", ".join(faces[k][:10])))
print("  gaps: %s" % json.dumps(gaps))
print("WROTE %s" % os.path.abspath(OUT))
