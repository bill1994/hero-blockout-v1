"""Read-only audit of hero_animation_v14_p19.blend.

Captures: per-object animation binding (action + slot), world transforms,
parent chain, constraints; per-action fcurve paths and frame ranges.
Writes audit/p19_bind.json. Never modifies the scene.
"""
import bpy
import json
import os

OUT = r"G:\DSHProject\BlenderMcp\audit"
os.makedirs(OUT, exist_ok=True)


def fcurves_of(act):
    """Collect fcurves across Blender 4.4+ layered actions and legacy layout."""
    fcs = []
    try:
        for layer in act.layers:
            for strip in layer.strips:
                try:
                    for cb in strip.channelbags:
                        fcs.extend(list(cb.fcurves))
                except Exception:
                    pass
    except Exception:
        pass
    if not fcs:
        try:
            fcs = list(act.fcurves)
        except Exception:
            fcs = []
    return fcs


rows = []
for o in bpy.data.objects:
    ad = o.animation_data
    act = ad.action if ad else None
    slot_name = None
    slot_handle = None
    try:
        if ad and ad.action_slot:
            slot_name = ad.action_slot.name
            slot_handle = ad.action_slot.handle
    except Exception:
        pass
    entry = {
        "name": o.name,
        "type": o.type,
        "parent": o.parent.name if o.parent else None,
        "parent_type": o.parent_type,
        "loc": [round(v, 6) for v in o.location],
        "rot_mode": o.rotation_mode,
        "world_loc": [round(v, 6) for v in o.matrix_world.translation],
        "world_scale": [round(v, 6) for v in o.matrix_world.to_scale()],
        "dimensions": [round(v, 6) for v in o.dimensions],
        "action": act.name if act else None,
        "action_slot": slot_name,
        "action_slot_handle": slot_handle,
        "nla_tracks": len(ad.nla_tracks) if ad else 0,
        "constraints": [{"type": c.type, "name": c.name, "target": (
            c.target.name if hasattr(c, "target") and c.target else None)} for c in o.constraints],
        "visible_render": not o.hide_render,
        "visible_viewport": not o.hide_viewport,
    }
    if o.type == 'MESH' and o.data:
        me = o.data
        entry["verts"] = len(me.vertices)
        entry["polys"] = len(me.polygons)
        entry["mats"] = [s.material.name if s.material else None for s in o.material_slots]
    rows.append(entry)

acts = []
for a in bpy.data.actions:
    fcs = fcurves_of(a)
    paths = sorted({fc.data_path for fc in fcs})
    fr = a.frame_range
    slot_names = []
    try:
        slot_names = [s.name_display or s.name for s in a.slots]
    except Exception:
        pass
    acts.append({
        "name": a.name,
        "users": a.users,
        "use_fake_user": a.use_fake_user,
        "frame_range": [round(fr[0], 3), round(fr[1], 3)],
        "n_fcurves": len(fcs),
        "paths": paths,
        "slots": slot_names,
    })

sc = bpy.context.scene
result = {
    "file": bpy.data.filepath,
    "blender": bpy.app.version_string,
    "scene_frame_range": [sc.frame_start, sc.frame_end],
    "fps": sc.render.fps,
    "active_camera": sc.camera.name if sc.camera else None,
    "n_objects": len(bpy.data.objects),
    "n_actions": len(bpy.data.actions),
    "objects": rows,
    "actions": acts,
}

dest = os.path.join(OUT, "p19_bind.json")
with open(dest, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("WROTE " + dest)
