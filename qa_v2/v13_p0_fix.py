"""v13 P0: audit fixes on hero_animation_v12_style.blend -> hero_animation_v13_soft.blend

Fixes, in order:
  Q4  Machine_Hopper location[2] last key 2.455005 -> 2.450000 (closes the 5 mm loop pop)
  D1  Machine_Body had zero material slots; assign a measured cream
  D2  Four arm decorations were parented but left ~3 units off their parent mesh; snap them
  D3  Hide tool-only meshes (boolean cutters, fit-check proxies) from render

Run:
    blender-5.4.0-alpha --background hero_animation_v12_style.blend \
        --python qa_v2/v13_p0_fix.py -- --out hero_animation_v13_soft.blend

Every mutation prints a line so the run log is the change record.
"""
import sys
import json
import bpy
from mathutils import Vector

argv = sys.argv
out_path = argv[argv.index("--out") + 1] if "--out" in argv else "hero_animation_v13_soft.blend"
report = {"out": out_path, "fixes": []}


def log(stage, msg):
    print("[P0:%s] %s" % (stage, msg))
    report["fixes"].append("%s: %s" % (stage, msg))


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def iter_fcurves(action):
    """Blender 4.4+ slotted actions dropped Action.fcurves."""
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


def world_bbox(obj, depsgraph):
    """World-space (min, max) of the evaluated mesh, or None."""
    if obj is None or obj.type != "MESH":
        return None
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    mw = ev.matrix_world
    if not me.vertices:
        ev.to_mesh_clear()
        return None
    pts = [mw @ v.co for v in me.vertices]
    mn = Vector((min(p[i] for p in pts) for i in range(3)))
    mx = Vector((max(p[i] for p in pts) for i in range(3)))
    ev.to_mesh_clear()
    return mn, mx


# --------------------------------------------------------------------------
# Q4 - close the loop. Scan every animated fcurve for first/last mismatch,
#      report all of them, and repair only the allow-listed ones.
# --------------------------------------------------------------------------
LOOP_ALLOWLIST = {
    ("Arm_Mount", "location", 2),
    ("Machine_Body", "location", 2),
    ("Machine_Hopper", "location", 2),
    ("Machine_Light_01", "location", 2),
    ("Machine_Light_02", "location", 2),
    ("Machine_Light_03", "location", 2),
    ("Machine_LightStrip", "location", 2),
    ("Machine_OutputChute", "location", 2),
}
# Deliberately NOT closed: ("Product", "location", 0) and ("Product", "location", 2).
# Product is hidden at f1 and scaled to 0.001 (invisible) at f327, so both loop
# endpoints are off-screen; rewriting them would interfere with the product path.

loop_breaks = []
for obj in bpy.data.objects:
    ad = obj.animation_data
    if not ad or not ad.action:
        continue
    for fc in iter_fcurves(ad.action):
        kps = fc.keyframe_points
        if len(kps) < 2:
            continue
        v_first = fc.evaluate(bpy.context.scene.frame_start)
        v_last = fc.evaluate(bpy.context.scene.frame_end)
        if abs(v_last - v_first) <= 1e-6:
            continue
        key = (obj.name, fc.data_path, fc.array_index)
        loop_breaks.append((key, v_first, v_last, len(kps)))
        if key not in LOOP_ALLOWLIST:
            continue
        last = kps[-1]
        delta = v_first - v_last
        last.co[1] += delta
        last.handle_left[1] += delta
        last.handle_right[1] += delta
        log(
            "Q4",
            "%s %s[%d]: last key f%.2f %.6f -> %.6f (delta %+.6f, keys %d unchanged) CLOSED"
            % (obj.name, fc.data_path, fc.array_index, last.co[0], v_last, last.co[1], delta, len(kps)),
        )

report["loop_breaks_found"] = [
    {"object": k[0], "path": k[1], "index": k[2], "first": round(a, 6), "last": round(b, 6), "keys": n}
    for k, a, b, n in loop_breaks
]
not_fixed = [
    "%s.%s[%d]" % (k[0], k[1], k[2]) for k, _, _, _ in loop_breaks if k not in LOOP_ALLOWLIST
]
log("Q4", "loop breaks found: %d, repaired: %d, left alone: %s"
    % (len(loop_breaks), len(loop_breaks) - len(not_fixed), not_fixed or "none"))

# --------------------------------------------------------------------------
# D1 - Machine_Body had no material at all
# --------------------------------------------------------------------------
body = bpy.data.objects["Machine_Body"]
if body.material_slots and body.material_slots[0].material:
    log("D1", "already has material %s, skipped" % body.material_slots[0].material.name)
else:
    mat = bpy.data.materials.get("MAT_Body")
    if mat is None:
        # sRGB #DDD5C8 (reference cream, lit p70) -> linear
        mat = bpy.data.materials.new("MAT_Body")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (0.723, 0.665, 0.578, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.45
        bsdf.inputs["Metallic"].default_value = 0.0
    if not body.data.materials:
        body.data.materials.append(mat)
    else:
        body.data.materials[0] = mat
    for poly in body.data.polygons:
        poly.material_index = 0
    log("D1", "Machine_Body(0 slots) <- %s  albedo linear (0.723, 0.665, 0.578) rough 0.45" % mat.name)

# --------------------------------------------------------------------------
# D2 - snap the four arm decorations back onto their parent mesh
# --------------------------------------------------------------------------
FLOATERS = ["Arm_Rings_Elbow", "Arm_Rings_Shoulder", "Arm_Seams_Fore", "Arm_Seams_Upper"]
depsgraph = bpy.context.evaluated_depsgraph_get()

for name in FLOATERS:
    obj = bpy.data.objects.get(name)
    if obj is None:
        log("D2", "FAIL %s missing" % name)
        continue
    parent = obj.parent
    if parent is None:
        log("D2", "FAIL %s has no parent" % name)
        continue
    pbb = world_bbox(parent, depsgraph)
    cbb = world_bbox(obj, depsgraph)
    if pbb is None or cbb is None:
        log("D2", "FAIL %s no bbox (obj mesh=%s parent mesh=%s)" % (name, cbb is not None, pbb is not None))
        continue
    p_center = (pbb[0] + pbb[1]) / 2.0
    c_center = (cbb[0] + cbb[1]) / 2.0
    shift = p_center - c_center
    obj.matrix_world.translation = obj.matrix_world.translation + shift
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    new_bb = world_bbox(obj, depsgraph)
    new_center = (new_bb[0] + new_bb[1]) / 2.0
    residual = (new_center - p_center).length
    log(
        "D2",
        "%s <- %s  moved (%+.3f, %+.3f, %+.3f)  residual %.6f"
        % (name, parent.name, shift.x, shift.y, shift.z, residual),
    )

# --------------------------------------------------------------------------
# D3 - tool-only meshes must not render
# --------------------------------------------------------------------------
TOOLS = ["Cutter_Outlet", "Cutter_Window", "Product_Proxy_FitCheck", "Product_Proxy_Large"]
for name in TOOLS:
    obj = bpy.data.objects.get(name)
    if obj is None:
        continue
    was = (obj.hide_render, obj.hide_viewport)
    obj.hide_render = True
    obj.hide_viewport = True
    log("D3", "%s hide_render/hide_viewport %s -> (True, True)" % (name, was))

# report anything else that renders without a material
bare = []
for obj in bpy.data.objects:
    if obj.type != "MESH" or obj.hide_render:
        continue
    if not obj.material_slots or all(s.material is None for s in obj.material_slots):
        bare.append(obj.name)
report["rendering_without_material"] = bare
log("D3", "meshes still rendering with no material: %s" % (bare or "none"))

# --------------------------------------------------------------------------
# save
# --------------------------------------------------------------------------
report["scene"] = {
    "frame_start": bpy.context.scene.frame_start,
    "frame_end": bpy.context.scene.frame_end,
    "fps": bpy.context.scene.render.fps,
    "objects": len(bpy.data.objects),
    "actions": len(bpy.data.actions),
}

with open(out_path.replace(".blend", "_p0_report.json"), "w", encoding="utf-8") as fh:
    json.dump(report, fh, indent=2, ensure_ascii=False)

bpy.ops.wm.save_as_mainfile(filepath=out_path if out_path.endswith(".blend") else out_path + ".blend")
print("SAVED", bpy.data.filepath)
