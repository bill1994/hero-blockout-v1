"""Stage 1b probe - sample the rig pose across the animation.

Temporarily binds each action to its owner, steps the timeline, and records
world positions of every pivot. Nothing is saved.
"""
import bpy

REBUILD = r"G:\DSHProject\BlenderMcp\rebuild_v1.blend"
bpy.ops.wm.open_mainfile(filepath=REBUILD)

BIND = {
    "Machine_Root": "Machine_RootAction_V2",
    "Machine_OutputChute": "Machine_OutputChuteAction_V2",
    "Arm_Yaw_Pivot": "Arm_Yaw_PivotAction_V2",
    "Arm_Shoulder_Pivot": "Arm_Shoulder_PivotAction_V2",
    "Arm_Elbow_Pivot": "Arm_Elbow_PivotAction_V2",
    "Arm_Wrist": "Arm_WristAction_V2",
}

bound, missing = [], []
for name, actname in BIND.items():
    o = bpy.data.objects.get(name)
    a = bpy.data.actions.get(actname)
    if o is None or a is None:
        missing.append(name)
        continue
    if o.animation_data is None:
        o.animation_data_create()
    o.animation_data.action = a
    try:
        if hasattr(o.animation_data, "action_slot") and o.animation_data.action_slot is None and len(a.slots):
            o.animation_data.action_slot = a.slots[0]
    except Exception:
        pass
    bound.append((name, actname))

FRAMES = [1, 60, 120, 156, 180, 220, 240, 270, 300, 327]
samples = {}
for f in FRAMES:
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    for name, _ in bound:
        o = bpy.data.objects.get(name)
        if o is None:
            continue
        samples.setdefault(name, {})[f] = [round(v, 4) for v in o.matrix_world.translation]

print("BOUND " + repr([b[0] for b in bound]))
print("MISSING " + repr(missing))
for name in samples:
    row = samples[name]
    print("PIVOT %-22s " % name + "  ".join("f%d=%s" % (f, row.get(f)) for f in FRAMES))

# how much does the machine body actually travel?
for name in ("Machine_Root", "Machine_OutputChute"):
    o = bpy.data.objects.get(name)
    if o and o.animation_data and o.animation_data.action:
        print("DETAIL %-22s action=%s" % (name, o.animation_data.action.name))
        for fc in o.animation_data.action.fcurves:
            print("   fc %-16s idx=%d  f1=%.4f  f180=%.4f  f327=%.4f" % (
                fc.data_path, fc.array_index, fc.evaluate(1), fc.evaluate(180), fc.evaluate(327)))
