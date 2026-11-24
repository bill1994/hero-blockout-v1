"""Dump the exact binding state of every animated mesh in p19.

Nothing is saved. Output is JSON so the build script can consume it.
"""
import bpy
import json
import os

P19 = r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend"
OUT = r"G:\DSHProject\BlenderMcp\audit\p19_binding.json"
bpy.ops.wm.open_mainfile(filepath=P19)

TARGETS = [
    "Machine_Body", "Machine_Hopper", "Machine_LightStrip",
    "Machine_Light_01", "Machine_Light_02", "Machine_Light_03",
    "Arm_Finger_L", "Arm_Finger_R", "Arm_Mount",
    "Product", "Idea",
    "Arm_UpperArm", "Arm_Forearm", "Arm_Gripper", "Arm_WristCollar",
    "Arm_Base", "Arm_Shoulder_Joint", "Arm_Elbow_Joint",
    "Arm_ShoulderRiser", "Arm_Yaw_Housing", "Arm_UpperArm_Seam_A",
    "Arm_UpperArm_Seam_B", "Arm_Forearm_Seam_A", "Arm_Forearm_Seam_B",
    "P3d_WristCuff", "Machine_Chute", "P1_OutletCollar",
    "P1_OutletRailL", "P1_OutletRailR", "P1_ChuteSeat", "P1_ChuteRail",
    "P1_BaseBand", "P1_ShoulderBay", "P3d_HopperCollar",
    "Machine_WindowFrame", "Machine_WindowCavity", "Machine_WindowGlass", "Machine_WindowGlow",
    "Machine_Feet", "Machine_Base", "P3c_Button_Power", "P3c_Button_Mode",
    "P3d_RingSeat_Power", "P3d_RingSeat_Mode", "P3d_Label",
]

# bind every live action so frame 1 is the authored rest pose
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action is None:
        pass
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

report = {}
for name in TARGETS:
    ob = bpy.data.objects.get(name)
    if ob is None:
        report[name] = {"MISSING": True}
        continue
    entry = {
        "type": ob.type,
        "parent": ob.parent.name if ob.parent else None,
        "parent_type": ob.parent_type,
        "location": [round(v, 6) for v in ob.location],
        "rotation_mode": ob.rotation_mode,
        "rotation_euler": [round(v, 6) for v in ob.rotation_euler],
        "scale": [round(v, 6) for v in ob.scale],
        "matrix_parent_inverse": [[round(v, 6) for v in row] for row in ob.matrix_parent_inverse],
        "matrix_world_f1": [[round(v, 6) for v in row] for row in ob.matrix_world],
        "material_slots": [s.material.name if s.material else None for s in ob.material_slots],
        "constraints": [
            {"name": c.name, "type": c.type,
             "target": getattr(getattr(c, "target", None), "name", None),
             "influence": round(c.influence, 4)}
            for c in ob.constraints
        ],
    }
    if ob.type == 'MESH' and ob.data:
        me = ob.data
        vs = [v.co for v in me.vertices]
        if vs:
            entry["local_bbox_min"] = [round(min(v[i] for v in vs), 6) for i in range(3)]
            entry["local_bbox_max"] = [round(max(v[i] for v in vs), 6) for i in range(3)]
        entry["n_verts"] = len(me.vertices)
        entry["n_polys"] = len(me.polygons)
    report[name] = entry

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("WROTE " + OUT)
for name, e in report.items():
    if e.get("MISSING"):
        print("MISSING %s" % name)
        continue
    print("%-22s p=%-20s loc=%-30s lb=%-34s" % (
        name, str(e["parent"]), str(e["location"]),
        str(e.get("local_bbox_min")) + ">" + str(e.get("local_bbox_max"))))
