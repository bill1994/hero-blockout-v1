"""v13 baseline audit: animation integrity, loop endpoints, grab contact, poly budget.

Read-only. Run with:
    blender --background hero_animation_v12_style.blend --python qa_v2/v13_baseline_audit.py

Writes JSON to the path given by --out (default qa_v2/v13_baseline.json).
"""
import sys
import os
import json
import bpy

argv = sys.argv
out_path = None
if "--out" in argv:
    out_path = argv[argv.index("--out") + 1]
if not out_path:
    out_path = os.path.join(os.path.dirname(bpy.data.filepath), "qa_v2", "v13_baseline.json")

sc = bpy.context.scene
out = {
    "blend": bpy.data.filepath,
    "frame_start": sc.frame_start,
    "frame_end": sc.frame_end,
    "fps": sc.render.fps,
}

# ---------------- action integrity ----------------


def iter_fcurves(action):
    """Blender 4.4+ slotted actions dropped Action.fcurves; walk layers/strips/bags."""
    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        try:
            return list(legacy)
        except (AttributeError, TypeError, RuntimeError):
            pass
    found = []
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            bags = getattr(strip, "channelbags", None)
            if bags is not None:
                for bag in bags:
                    found.extend(bag.fcurves)
    return found


acts = []
for a in bpy.data.actions:
    fcs = iter_fcurves(a)
    nk = sum(len(fc.keyframe_points) for fc in fcs)
    fr = a.frame_range
    acts.append(
        {
            "name": a.name,
            "fcurves": len(fcs),
            "keys": nk,
            "range": [round(fr[0], 3), round(fr[1], 3)],
            "users": a.users,
        }
    )
out["actions"] = sorted(acts, key=lambda d: d["name"])
out["action_count"] = len(acts)
out["total_fcurves"] = sum(d["fcurves"] for d in acts)
out["total_keys"] = sum(d["keys"] for d in acts)

# ---------------- NLA / object animation assignment ----------------
anim = {}
for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action:
        anim[o.name] = o.animation_data.action.name
out["object_action_map"] = anim


# ---------------- loop endpoint delta ----------------
def wloc(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    return o.matrix_world.translation.copy()


probe = [
    "Idea",
    "Product",
    "Arm_Finger_L",
    "Arm_Finger_R",
    "Arm_Wrist",
    "Machine_Hopper",
    "Outlet_Flap",
    "Machine_Root",
]
loop = {}
for f in (sc.frame_start, sc.frame_end):
    sc.frame_set(int(f))
    bpy.context.view_layer.update()
    for n in probe:
        v = wloc(n)
        if v is not None:
            loop.setdefault(n, {})[int(f)] = [round(c, 6) for c in v]

delta = {}
for n, d in loop.items():
    a = d.get(sc.frame_start)
    b = d.get(sc.frame_end)
    if a and b:
        delta[n] = round(max(abs(a[i] - b[i]) for i in range(3)), 6)
out["loop_endpoint_max_abs_delta"] = delta


# ---------------- grab contact ----------------
def world_verts(name):
    o = bpy.data.objects.get(name)
    if o is None or o.type != "MESH":
        return None
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    return vs


prod_names = [n for n in ("Product", "Idea") if bpy.data.objects.get(n)]
contact = {}
for fr in (31, 43, 147, 155):
    sc.frame_set(fr)
    bpy.context.view_layer.update()
    row = {}
    targets = {}
    for pn in prod_names:
        pv = world_verts(pn)
        if pv:
            targets[pn] = pv
            row[pn + "_bbox"] = [
                [round(min(v[i] for v in pv), 4) for i in range(3)],
                [round(max(v[i] for v in pv), 4) for i in range(3)],
            ]
    for fn in ("Arm_Finger_L", "Arm_Finger_R"):
        fv = world_verts(fn)
        if not fv:
            continue
        for pn, pv in targets.items():
            best = min(min((a - b).length for b in pv) for a in fv)
            row["%s->%s_min" % (fn, pn)] = round(best, 5)
    lv = world_verts("Arm_Finger_L")
    rv = world_verts("Arm_Finger_R")
    if lv and rv:
        row["tip_gap_LR"] = round(min(min((a - b).length for b in rv) for a in lv), 5)
    contact[str(fr)] = row
out["grab_contact"] = contact

# ---------------- poly budget ----------------
dg = bpy.context.evaluated_depsgraph_get()
tris = 0
mesh_objs = 0
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    mesh_objs += 1
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    tris += len(me.loop_triangles)
    ev.to_mesh_clear()
out["evaluated_triangles"] = tris
out["mesh_objects"] = mesh_objs

# ---------------- materials ----------------
out["materials"] = sorted(m.name for m in bpy.data.materials)
out["body_material_slots"] = [
    s.material.name if s.material else None
    for s in bpy.data.objects["Machine_Body"].material_slots
] if bpy.data.objects.get("Machine_Body") else None

os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, ensure_ascii=False)
print("WROTE", out_path)
print(json.dumps({k: out[k] for k in ("action_count", "total_fcurves", "total_keys",
                                      "evaluated_triangles", "mesh_objects")}, indent=2))
