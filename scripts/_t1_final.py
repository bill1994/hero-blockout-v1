"""T1 final checks: prop placement vs extended chute, temp-rig contamination, stats."""
import bpy
import os
from mathutils import Vector

ROOT = r"G:\DSHProject\BlenderMcp"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "rebuild_v2.blend"))
sc = bpy.context.scene
D = bpy.data

print("TMP objects:", [o.name for o in D.objects if o.name.startswith("TMP_")])
print("CAMERAS:", [o.name for o in D.objects if o.type == 'CAMERA'])
print("LIGHTS:", [o.name for o in D.objects if o.type == 'LIGHT'])

for f in (1, 60, 120, 180, 220, 280, 327):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    out = []
    for n in ("Product", "Idea", "Machine_Chute", "P1_ChuteRail"):
        ob = D.objects.get(n)
        if ob:
            w = ob.matrix_world.translation
            out.append("%s=(%.2f,%.2f,%.2f)" % (n, w.x, w.y, w.z))
    print("F%-4d %s" % (f, "  ".join(out)))

sc.frame_set(1)
bpy.context.view_layer.update()
tv = tt = tq = tn = tf = 0
for me_ob in [o for o in D.objects if o.type == 'MESH']:
    me = me_ob.data
    me.calc_loop_triangles()
    tt += len(me.loop_triangles)
    tv += len(me.vertices)
    tf += len(me.polygons)
    for p in me.polygons:
        n = len(p.vertices)
        if n == 4:
            tq += 1
        elif n != 3:
            tn += 1
print("FINAL verts=%d faces=%d tris=%d quads=%d ngons=%d quad_face_share=%.2f%% tri_share_of_tris=%.2f%%"
      % (tv, tf, tt, tq, tn, 100.0 * tq / tf, 100.0 * 2 * tq / tt))
print("BUDGET headroom=%d (cap 18000)" % (18000 - tt))
