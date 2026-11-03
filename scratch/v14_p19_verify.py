"""P19 verification: product clearance, exit pass-through, triangle budget."""
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_verify.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

scn = bpy.context.scene
prod = bpy.data.objects["Product"]

OUTLET = ["Machine_Chute", "P1_ChuteSeat", "P1_OutletCollar", "P1_ChuteRail", "P2_OutletBand"]


def world_tris(obj, dg):
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    if me is None:
        return [], []
    mw = obj.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [list(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return verts, polys


# ---------------------------------------------------------------- 1. penetration
W("=== 1. PRODUCT vs OUTLET penetration (f232..f301, every frame) ===")
worst = {}
total_hits = 0
for f in range(232, 302):
    scn.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = prod.evaluated_get(dg)
    pme = ev.to_mesh()
    if pme is None:
        continue
    pverts = [prod.matrix_world @ v.co for v in pme.vertices]
    pfaces = [list(p.vertices) for p in pme.polygons]
    p_bvh = BVHTree.FromPolygons(pverts, pfaces)
    ev.to_mesh_clear()

    for name in OUTLET:
        o = bpy.data.objects.get(name)
        if not o:
            continue
        ov, op = world_tris(o, dg)
        if not ov:
            continue
        o_bvh = BVHTree.FromPolygons(ov, op)
        hits = p_bvh.overlap(o_bvh)
        if hits:
            total_hits += len(hits)
            rec = worst.setdefault(name, {"frames": [], "max_pairs": 0})
            rec["frames"].append(f)
            rec["max_pairs"] = max(rec["max_pairs"], len(hits))

if not worst:
    W("  RESULT: 0 penetration frames  <-- PASS")
else:
    for name, rec in worst.items():
        fr = rec["frames"]
        W(f"  {name}: {len(fr)} frames, max {rec['max_pairs']} pairs; f{fr[0]}..f{fr[-1]}")
        W(f"     sample frames: {fr[:12]}")
W(f"  total overlap pairs: {total_hits}")

# ---------------------------------------------------------------- 2. exit pass-through
W("")
W("=== 2. EXIT PASS-THROUGH: cast +X rays through the mouth each frame ===")
W("    origin x=0.95 (just outside body face 0.90), marching through the outlet")
blocked_frames = []
for f in range(232, 302):
    scn.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    # sample the product's own cross-section at this frame
    ev = prod.evaluated_get(dg)
    pme = ev.to_mesh()
    pverts = [prod.matrix_world @ v.co for v in pme.vertices]
    pz0 = min(p.z for p in pverts); pz1 = max(p.z for p in pverts)
    py1 = max(abs(p.y) for p in pverts)
    ev.to_mesh_clear()

    zs = [pz0 + (pz1 - pz0) * t for t in (0.06, 0.5, 0.94)]
    ys = [-py1 * 0.92, 0.0, py1 * 0.92]
    blocked = 0
    for z in zs:
        for y in ys:
            hit = scn.ray_cast(dg, Vector((0.95, y, z)), Vector((1, 0, 0)), distance=2.0)
            if hit and hit[0]:
                blocked += 1
    if blocked:
        blocked_frames.append((f, blocked, round(pz0, 3), round(pz1, 3), round(py1, 3)))

if not blocked_frames:
    W("  RESULT: every sampled ray clears the outlet  <-- PASS")
else:
    W(f"  BLOCKED on {len(blocked_frames)} frames:")
    for row in blocked_frames[:20]:
        W(f"    f{row[0]}: {row[1]}/9 rays blocked  (prod z[{row[2]},{row[3]}] y+-{row[4]})")

# ---------------------------------------------------------------- 3. seat gap
W("")
W("=== 3. SEAT GAP: product bottom vs trough floor ===")
gaps = []
for f in (232, 236, 240, 245, 250, 255, 260):
    scn.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = prod.evaluated_get(dg)
    pme = ev.to_mesh()
    pverts = [prod.matrix_world @ v.co for v in pme.vertices]
    px0 = min(p.x for p in pverts); px1 = max(p.x for p in pverts)
    pz0 = min(p.z for p in pverts)
    pym = max(abs(p.y) for p in pverts)
    ev.to_mesh_clear()
    cx = (px0 + px1) / 2.0
    hit = scn.ray_cast(dg, Vector((cx, 0.0, pz0 - 0.4)), Vector((0, 0, 1)), distance=1.0)
    floor = round(hit[1].z, 4) if (hit and hit[0]) else None
    who = hit[4].name if (hit and hit[0] and len(hit) > 4 and hit[4]) else None
    gap = round(pz0 - floor, 4) if floor is not None else None
    gaps.append((f, round(pz0, 4), floor, gap, who, round(pym, 3)))
    W(f"  f{f}: prod_bottom={round(pz0,4)} floor={floor} gap={gap} on={who} prod_y=+-{round(pym,3)}")

# ---------------------------------------------------------------- 4. triangle budget
W("")
W("=== 4. TRIANGLE BUDGET ===")
dg = bpy.context.evaluated_depsgraph_get()
tris = 0
per = {}
for o in scn.objects:
    if o.type != "MESH" or o.hide_render:
        continue
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    if me is None:
        continue
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    per[o.name] = n
    tris += n
    ev.to_mesh_clear()
W(f"  visible triangles = {tris} / 60000  ({tris/60000*100:.1f}%)")
top = sorted(per.items(), key=lambda x: -x[1])[:8]
for k, v in top:
    W(f"    {k}: {v}")

# ---------------------------------------------------------------- 5. animation untouched
W("")
W("=== 5. ANIMATION INTEGRITY (must be unchanged) ===")
decided = bpy.data.actions.get("IdeaAction_V2")
W(f"  actions total = {len(bpy.data.actions)}")
used = set()
for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action:
        used.add(o.animation_data.action.name)
W(f"  animated objects = {len(used)}")
scn.frame_set(31)
idea = bpy.data.objects["Idea"]
tips = []
for fn in ("Arm_Finger_L", "Arm_Finger_R"):
    o = bpy.data.objects[fn]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    tp = min(vs, key=lambda p: (p - idea.matrix_world.translation).length)
    tips.append(round((tp - idea.matrix_world.translation).length, 4))
W(f"  grab distance f31 = {tips}")
scn.frame_set(1)
a1 = {o.name: [round(v, 4) for v in o.matrix_world.translation] for o in scn.objects if o.type in ("MESH", "EMPTY")}
scn.frame_set(327)
a2 = {o.name: [round(v, 4) for v in o.matrix_world.translation] for o in scn.objects if o.type in ("MESH", "EMPTY")}
diffs = [k for k in a1 if k in a2 and sum((a1[k][i] - a2[k][i]) ** 2 for i in range(3)) ** 0.5 > 1e-4]
W(f"  loop closure diffs = {diffs if diffs else 'none (0.000)'}")

W("DONE")
