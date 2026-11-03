"""P19 v2 verification - product clearance + true exit pass-through (product excluded)."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_verify2.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

scn = bpy.context.scene
prod = bpy.data.objects["Product"]
OUTLET = ["Machine_Chute", "P1_OutletRailL", "P1_OutletRailR", "P1_OutletCollar", "P1_ChuteRail", "P2_OutletBand"]
FLOOR = 1.074


def tris_of(obj, dg):
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    if me is None:
        return [], []
    mw = obj.matrix_world
    vs = [mw @ v.co for v in me.vertices]
    ps = [list(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return vs, ps


# ---------------------------------------------------------------- 1 penetration
W("=== 1. PRODUCT vs OUTLET penetration (f232..f301) ===")
bad = {}
for f in range(232, 302):
    scn.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = prod.evaluated_get(dg)
    pme = ev.to_mesh()
    if pme is None:
        continue
    pv = [prod.matrix_world @ v.co for v in pme.vertices]
    pf = [list(p.vertices) for p in pme.polygons]
    pb = BVHTree.FromPolygons(pv, pf)
    ev.to_mesh_clear()
    for name in OUTLET:
        o = bpy.data.objects.get(name)
        if not o:
            continue
        ov, op = tris_of(o, dg)
        if not ov:
            continue
        ob = BVHTree.FromPolygons(ov, op)
        h = pb.overlap(ob)
        if h:
            r = bad.setdefault(name, [0, 0, []])
            r[0] += 1
            r[1] = max(r[1], len(h))
            r[2].append(f)
if not bad:
    W("  RESULT: 0 penetration frames  <-- PASS")
else:
    for n, (cnt, mx, fr) in bad.items():
        W(f"  {n}: {cnt} frames, max {mx} pairs, frames {fr[:15]}")

# ---------------------------------------------------------------- 2 exit pass-through
W("")
W("=== 2. EXIT PASS-THROUGH (rays cast against OUTLET ONLY, product excluded) ===")
W("    origin x=0.94, +X, distance 3.0 - does anything in the outlet block the lane?")
blocked = {}
for f in range(232, 302):
    scn.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = prod.evaluated_get(dg)
    pme = ev.to_mesh()
    pv = [prod.matrix_world @ v.co for v in pme.vertices]
    pz0 = min(p.z for p in pv)
    pz1 = max(p.z for p in pv)
    py1 = max(abs(p.y) for p in pv)
    ev.to_mesh_clear()

    bvhs = {}
    for name in OUTLET:
        o = bpy.data.objects.get(name)
        if not o:
            continue
        ov, op = tris_of(o, dg)
        if ov:
            bvhs[name] = BVHTree.FromPolygons(ov, op)

    hits = []
    for tz in (0.05, 0.5, 0.95):
        z = pz0 + (pz1 - pz0) * tz
        for ty in (-0.92, 0.0, 0.92):
            y = py1 * ty
            org = Vector((0.94, y, z))
            d = Vector((1, 0, 0))
            for name, b in bvhs.items():
                loc, nor, idx, dist = b.ray_cast(org, d, 3.0)
                if loc is not None:
                    hits.append((name, round(dist, 3), round(y, 3), round(z, 3)))
                    break
    if hits:
        blocked[f] = hits

if not blocked:
    W("  RESULT: every sampled lane is clear through the whole exit  <-- PASS")
else:
    W(f"  blocked on {len(blocked)} frames")
    for f, h in list(blocked.items())[:12]:
        W(f"    f{f}: {h[:3]}")

# ---------------------------------------------------------------- 3 seat gap
W("")
W("=== 3. SEAT GAP: product bottom vs whatever carries it ===")
W(f"    outlet floor = {FLOOR}")
rows = []
for f in (232, 236, 240, 245, 250, 255, 265, 280, 295, 300):
    scn.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = prod.evaluated_get(dg)
    pme = ev.to_mesh()
    pv = [prod.matrix_world @ v.co for v in pme.vertices]
    px0, px1 = min(p.x for p in pv), max(p.x for p in pv)
    pz0 = min(p.z for p in pv)
    ev.to_mesh_clear()
    cx = (px0 + px1) / 2
    hit = scn.ray_cast(dg, Vector((cx, 0.0, pz0 - 0.30)), Vector((0, 0, 1)), distance=0.60)
    floor = round(hit[1].z, 4) if (hit and hit[0]) else None
    who = hit[4].name if (hit and hit[0] and len(hit) > 4 and hit[4]) else None
    gap = round(pz0 - floor, 4) if floor is not None else None
    rows.append((f, round(px0, 3), round(px1, 3), round(pz0, 4), floor, gap, who))
    W(f"  f{f:3d}: prod x[{round(px0,3)},{round(px1,3)}] bottom={round(pz0,4)} "
      f"floor={floor} gap={gap} on={who}")

# ---------------------------------------------------------------- 4 budget
W("")
W("=== 4. TRIANGLE BUDGET ===")
dg = bpy.context.evaluated_depsgraph_get()
tot = 0
per = {}
for o in scn.objects:
    if o.type != "MESH" or o.hide_render:
        continue
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    if me is None:
        continue
    me.calc_loop_triangles()
    per[o.name] = len(me.loop_triangles)
    tot += per[o.name]
    ev.to_mesh_clear()
W(f"  visible = {tot} / 60000 ({tot/60000*100:.1f}%)")
for k, v in sorted(per.items(), key=lambda x: -x[1])[:6]:
    W(f"    {k}: {v}")

# ---------------------------------------------------------------- 5 anim
W("")
W("=== 5. ANIMATION INTEGRITY ===")
W(f"  actions = {len(bpy.data.actions)}")
idea = bpy.data.objects["Idea"]
scn.frame_set(31)
tips = []
for fn in ("Arm_Finger_L", "Arm_Finger_R"):
    o = bpy.data.objects[fn]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    tp = min(vs, key=lambda p: (p - idea.matrix_world.translation).length)
    tips.append(round((tp - idea.matrix_world.translation).length, 4))
W(f"  grab distance f31 = {tips}  (expect 0.2531 / 0.2560)")
scn.frame_set(1)
a1 = {o.name: list(o.matrix_world.translation) for o in scn.objects if o.type in ("MESH", "EMPTY")}
scn.frame_set(327)
a2 = {o.name: list(o.matrix_world.translation) for o in scn.objects if o.type in ("MESH", "EMPTY")}
d = [k for k in a1 if k in a2 and sum((a1[k][i] - a2[k][i]) ** 2 for i in range(3)) ** 0.5 > 1e-4]
W(f"  loop closure = {d if d else 'none (0.000)'}")
W("DONE")
