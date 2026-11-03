"""P19 final: focused exit proof + reference-matched comparison renders."""
import bpy
import os
import math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

LOG = r"G:\DSHProject\BlenderMcp\scratch\p19_final.txt"
def W(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(str(s) + "\n")

scn = bpy.context.scene
prod = bpy.data.objects["Product"]
OUTLET = ["Machine_Chute", "P1_OutletRailL", "P1_OutletRailR", "P1_OutletCollar", "P1_ChuteRail", "P2_OutletBand"]


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


# ------------------------------------------------------------------ A. real exit test
W("=== A. EXIT PROOF: rays from INSIDE the body bore through the mouth ===")
W("    cast from x=0.50 (inside body, behind the bore) along +X at the product's own")
W("    cross-section, only on frames where the product is still at/inside the mouth.")
fails = []
checked = 0
for f in range(232, 256):
    scn.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = prod.evaluated_get(dg)
    pme = ev.to_mesh()
    pv = [prod.matrix_world @ v.co for v in pme.vertices]
    px1 = max(p.x for p in pv)
    pz0, pz1 = min(p.z for p in pv), max(p.z for p in pv)
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

    for tz in (0.05, 0.5, 0.95):
        z = pz0 + (pz1 - pz0) * tz
        for ty in (-0.90, 0.0, 0.90):
            y = py1 * ty
            checked += 1
            org = Vector((0.50, y, z))
            blocked = None
            for name, b in bvhs.items():
                loc, nor, idx, dist = b.ray_cast(org, Vector((1, 0, 0)), 1.9)
                if loc is not None and dist < (px1 - 0.50) + 0.05:
                    blocked = (name, round(dist, 3))
                    break
            if blocked:
                fails.append((f, round(y, 3), round(z, 3), blocked))

if not fails:
    W(f"  RESULT: {checked} rays, 0 blocked  <-- PASS (product has a clear path out)")
else:
    W(f"  {len(fails)} of {checked} rays blocked:")
    for row in fails[:10]:
        W(f"    f{row[0]} y={row[1]} z={row[2]} hit {row[3]}")

# product cross-section vs collar opening
scn.frame_set(245)
dg = bpy.context.evaluated_depsgraph_get()
ev = prod.evaluated_get(dg)
pme = ev.to_mesh()
pv = [prod.matrix_world @ v.co for v in pme.vertices]
W(f"  product cross-section: y +-{round(max(abs(p.y) for p in pv),3)}  z[{round(min(p.z for p in pv),3)},{round(max(p.z for p in pv),3)}]")
ev.to_mesh_clear()
W("  collar opening:        y +-0.462        z[1.005,1.560]")
W("  trough interior:       y +-0.400        floor 1.074 / rim 1.448")
W(f"  => lateral clearance {round(0.462-max(abs(p.y) for p in pv),3)} ; vertical clearance {round(1.560-1.486,3)}")

# ------------------------------------------------------------------ B. seat gap (downward)
W("")
W("=== B. SEAT GAP measured DOWNWARD onto the supporting surface ===")
for f in (232, 240, 245, 250, 260, 280, 295):
    scn.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = prod.evaluated_get(dg)
    pme = ev.to_mesh()
    pv = [prod.matrix_world @ v.co for v in pme.vertices]
    cx = (min(p.x for p in pv) + max(p.x for p in pv)) / 2
    pz0 = min(p.z for p in pv)
    ev.to_mesh_clear()
    res = scn.ray_cast(dg, Vector((cx, 0.0, pz0 - 0.001)), Vector((0, 0, -1)), distance=0.5)
    surf = round(res[1].z, 4) if (res and res[0]) else None
    who = res[4].name if (res and res[0] and len(res) > 4 and res[4]) else None
    gap = round(pz0 - surf, 4) if surf is not None else None
    W(f"  f{f:3d}: product bottom {round(pz0,4)} -> surface {surf} ({who}) gap={gap}")

# ------------------------------------------------------------------ C. renders
W("")
W("=== C. COMPARISON RENDERS ===")
out = r"G:\DSHProject\BlenderMcp\review\v14\p19"
os.makedirs(out, exist_ok=True)
scn.render.engine = "BLENDER_EEVEE"
scn.render.image_settings.file_format = "PNG"
scn.eevee.taa_render_samples = 48
scn.render.resolution_percentage = 100

hero = bpy.data.objects["Cam_Hero"]
cam_r = bpy.data.objects["Cam_Check_Right"]
cam_t = bpy.data.objects["Cam_Check_Top"]


def render(cam, res, path, frame):
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.frame_set(frame)
    scn.render.filepath = path
    bpy.ops.render.render(write_still=True)


# hero 3/4 at the frame the product is mid-exit
render(hero, (900, 900), os.path.join(out, "p19_hero_f248.png"), 248)
# tight front-of-outlet view matching the reference front panel
scn.render.resolution_x, scn.render.resolution_y = 900, 900
scn.camera = cam_r
scn.frame_set(248)
scn.render.use_border = True
scn.render.use_crop_to_border = True
scn.render.border_min_x, scn.render.border_max_x = 0.30, 0.95
scn.render.border_min_y, scn.render.border_max_y = 0.25, 0.75
scn.render.filepath = os.path.join(out, "p19_outlet_side_f248.png")
bpy.ops.render.render(write_still=True)
scn.render.use_border = False
scn.render.use_crop_to_border = False

# top view of the outlet (matches the reference top panel)
scn.camera = cam_t
scn.frame_set(248)
scn.render.resolution_x, scn.render.resolution_y = 900, 900
scn.render.use_border = True
scn.render.use_crop_to_border = True
scn.render.border_min_x, scn.render.border_max_x = 0.35, 0.95
scn.render.border_min_y, scn.render.border_max_y = 0.30, 0.70
scn.render.filepath = os.path.join(out, "p19_outlet_top_f248.png")
bpy.ops.render.render(write_still=True)
scn.render.use_border = False
scn.render.use_crop_to_border = False

# empty-mouth shots: frame 200 (product hidden) so the outlet shape is unobstructed
for cam, nm in ((cam_r, "side"), (cam_t, "top"), (hero, "hero")):
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = 900, 900
    scn.frame_set(200)
    scn.render.filepath = os.path.join(out, f"p19_empty_{nm}_f200.png")
    bpy.ops.render.render(write_still=True)

W("  rendered 6 images to review/v14/p19")
W("DONE")
