"""T1b probe: full object table (visibility + world bbox at f1) and totals. Read-only."""
import bpy
import os
from mathutils import Vector

ROOT = r"G:\DSHProject\BlenderMcp"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "rebuild_v2.blend"))
sc = bpy.context.scene
sc.frame_set(1)
bpy.context.view_layer.update()

tv = tt = tf = tq = 0
rows = []
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        print("OBJ %-8s %-28s par=%s" % (ob.type, ob.name,
                                         ob.parent.name if ob.parent else "-"))
        continue
    me = ob.data
    me.calc_loop_triangles()
    t = len(me.loop_triangles)
    q = sum(1 for p in me.polygons if len(p.vertices) == 4)
    tv += len(me.vertices)
    tt += t
    tf += len(me.polygons)
    tq += q
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs = [p.x for p in bb]
    ys = [p.y for p in bb]
    zs = [p.z for p in bb]
    rows.append((ob.name, len(me.vertices), len(me.polygons), t, q,
                 ob.hide_render, ob.hide_viewport,
                 (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)),
                 ob.parent.name if ob.parent else "-"))

print("STAT objects=%d verts=%d faces=%d tris=%d quads=%d" % (len(rows), tv, tf, tt, tq))

for r in sorted(rows, key=lambda r: r[0]):
    print("MESH %-24s v=%5d f=%5d tri=%5d q=%4d hr=%d hv=%d "
          "x[%7.3f %7.3f] y[%7.3f %7.3f] z[%7.3f %7.3f] par=%s"
          % (r[0], r[1], r[2], r[3], r[4], r[5], r[6],
             r[7][0], r[7][1], r[8][0], r[8][1], r[9][0], r[9][1], r[10]))

print("=== collections ===")
for c in bpy.data.collections:
    print("COLL %-28s objs=%d" % (c.name, len(c.objects)))
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        print("INCOL %-24s %s" % (ob.name, [c.name for c in ob.users_collection]))
