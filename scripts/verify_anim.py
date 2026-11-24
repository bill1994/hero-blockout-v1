import bpy, json

P19 = r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend"
V2  = r"G:\DSHProject\BlenderMcp\rebuild_v2.blend"
FRAMES = [1, 60, 120, 156, 200, 240, 280, 327]
NAMES = ["Machine_Root","Machine_Body","Machine_Hopper","Machine_OutputChute",
         "Machine_LightStrip","Machine_Light_01","Machine_Light_02","Machine_Light_03",
         "Arm_Yaw_Pivot","Arm_Shoulder_Pivot","Arm_Elbow_Pivot","Arm_Wrist",
         "Arm_Finger_L","Arm_Finger_R","Arm_Mount","Product","Idea"]

def snap(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    out = {}
    for f in FRAMES:
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        for n in NAMES:
            ob = bpy.data.objects.get(n)
            if ob is None:
                out["%s|%d" % (n, f)] = None
                continue
            m = ob.matrix_world
            out["%s|%d" % (n, f)] = [round(v, 5) for v in
                                     (list(m.translation) + list(m.to_euler()) +
                                      list(m.to_scale()))]
    return out

a = snap(P19)
b = snap(V2)
bad = 0
worst = 0.0
print("VF-BEGIN")
for k in a:
    va, vb = a[k], b[k]
    if va is None or vb is None:
        print("MISSING %s p19=%s v2=%s" % (k, va is not None, vb is not None))
        bad += 1
        continue
    d = max(abs(x - y) for x, y in zip(va, vb))
    worst = max(worst, d)
    if d > 1e-4:
        bad += 1
        print("DIFF %-28s max=%.6f\n   p19=%s\n   v2 =%s" % (k, d, va, vb))
print("VFRAME %d  mismatched=%d  worst_delta=%.8f" % (len(a), bad, worst))
print("VF-END")