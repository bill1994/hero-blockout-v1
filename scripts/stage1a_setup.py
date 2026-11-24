"""Stage 1a - build the skeleton of rebuild_v1.blend. (v2)

Fixes over v1:
  * the RIG layer imports the complete parent chain so world matrices survive
  * imports rig objects first, wipes their inherited animation, then imports the
    action list cleanly (avoids .001 name collisions)
"""
import bpy

TRIPO = r"G:\DSHProject\BlenderMcp\ReferenceModel.blend"
P19 = r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend"
OUT = r"G:\DSHProject\BlenderMcp\rebuild_v1.blend"

bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.render.fps = 60
scene.frame_start = 1
scene.frame_end = 327
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.name = "REBUILD"

ref_col = bpy.data.collections.new("REF_Tripo")
rig_col = bpy.data.collections.new("RIG")
build_col = bpy.data.collections.new("BUILD")
for c in (ref_col, rig_col, build_col):
    scene.collection.children.link(c)

# ------------------------------------------------ 1. RIG parent chain (p19)
RIG_NAMES = [
    "Machine_Root",
    "Machine_OutputChute",
    "Arm_Base",
    "Arm_Yaw_Pivot",
    "Arm_Shoulder_Pivot",
    "Arm_Elbow_Pivot",
    "Arm_Wrist",
]
with bpy.data.libraries.load(P19, link=False) as (src, dst):
    have = set(src.objects)
    dst.objects = [n for n in RIG_NAMES if n in have]

rig_objs = [o for o in dst.objects if o is not None]
for o in rig_objs:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    rig_col.objects.link(o)
    o.hide_render = True
    if o.type == 'MESH':
        o.data.materials.clear()

bpy.context.view_layer.update()

rig_report = {}
for o in rig_objs:
    rig_report[o.name] = {
        "type": o.type,
        "parent": o.parent.name if o.parent else None,
        "world_loc": [round(v, 6) for v in o.matrix_world.translation],
        "world_euler": [round(v, 6) for v in o.matrix_world.to_euler()],
        "local_loc": [round(v, 6) for v in o.location],
        "rot_mode": o.rotation_mode,
        "rot_euler": [round(v, 6) for v in o.rotation_euler],
        "dimensions": [round(v, 6) for v in o.dimensions],
        "parent_inverse_translation": [round(v, 6) for v in o.matrix_parent_inverse.translation],
    }

# also capture the world bbox of the mesh rig pieces so geometry can be matched
for o in rig_objs:
    if o.type == 'MESH':
        from mathutils import Vector
        mn = Vector((1e18,) * 3)
        mx = Vector((-1e18,) * 3)
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
        rig_report[o.name]["world_bbox_min"] = [round(v, 5) for v in mn]
        rig_report[o.name]["world_bbox_max"] = [round(v, 5) for v in mx]

# wipe inherited animation from the appended rig objects
for o in rig_objs:
    if o.animation_data:
        o.animation_data_clear()
for a in list(bpy.data.actions):
    bpy.data.actions.remove(a)

# ------------------------------------------------ 2. actions (clean slate now)
action_names = [
    "Machine_RootAction_V2", "Machine_BodyAction_V2", "Machine_HopperAction_V2",
    "Machine_OutputChuteAction_V2", "Machine_LightStripAction_V2",
    "Machine_Light_01Action_V2", "Machine_Light_02Action_V2", "Machine_Light_03Action_V2",
    "Arm_Yaw_PivotAction_V2", "Arm_Shoulder_PivotAction_V2",
    "Arm_Elbow_PivotAction_V2", "Arm_WristAction_V2",
    "Arm_Finger_LAction_V2", "Arm_Finger_RAction_V2", "Arm_MountAction_V2",
    "ProductAction.001_V2", "IdeaAction_V2",
]
with bpy.data.libraries.load(P19, link=False) as (src, dst):
    have = set(src.actions)
    dst.actions = [n for n in action_names if n in have]

got = [a.name for a in dst.actions if a is not None]
for a in dst.actions:
    if a is not None:
        a.use_fake_user = True


def fcurves_of(act):
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


def sample_frame(act, f):
    out = {}
    for fc in fcurves_of(act):
        key = fc.data_path if fc.array_index < 0 else "%s[%d]" % (fc.data_path, fc.array_index)
        try:
            out[key] = round(fc.evaluate(f), 4)
        except Exception:
            pass
    return out


act_report = {}
for a in dst.actions:
    if a is None:
        continue
    act_report[a.name] = {
        "paths": sorted({fc.data_path for fc in fcurves_of(a)}),
        "frame_range": [round(v, 3) for v in a.frame_range],
        "n_fcurves": len(fcurves_of(a)),
        "at_frame_1": sample_frame(a, 1.0),
    }

# ------------------------------------------------ 3. Tripo reference
with bpy.data.libraries.load(TRIPO, link=False) as (src, dst):
    dst.objects = list(src.objects)

tripo_objs = [o for o in dst.objects if o is not None]
for o in tripo_objs:
    for c in list(o.users_collection):
        c.objects.unlink(o)
    ref_col.objects.link(o)
    o.hide_render = True
    o.display_type = 'WIRE'
    o.show_name = False
    if o.type == 'MESH':
        o.data.materials.clear()

print("RIG " + repr(rig_report))
print("ACTS " + repr(sorted(act_report.keys())))
print("PATHS " + repr(act_report))
print("TRIPO " + str(len(tripo_objs)))

bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("SAVED " + OUT)
