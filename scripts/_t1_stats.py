"""T1 stats: global topology, new-object bounds, legacy front props. Read-only."""
import bpy
import os
from mathutils import Vector

ROOT = r"G:\DSHProject\BlenderMcp"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "rebuild_v2.blend"))
sc = bpy.context.scene
sc.frame_set(1)
bpy.context.view_layer.update()

tv = tt = tq = tn = tf = 0
rows = []
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    me = ob.data
    me.calc_loop_triangles()
    t = len(me.loop_triangles)
    q = sum(1 for p in me.polygons if len(p.vertices) == 4)
    tri = sum(1 for p in me.polygons if len(p.vertices) == 3)
    ng = len(me.polygons) - q - tri
    tv += len(me.vertices); tt += t; tq += q; tn += ng; tf += len(me.polygons)
    rows.append((ob.name, len(me.vertices), len(me.polygons), t, q, tri, ng))

print("STAT objects=%d verts=%d faces=%d tris=%d quads=%d ngons=%d"
      % (sum(1 for o in bpy.data.objects if o.type == 'MESH'), tv, tf, tt, tq, tn))
print("STAT quad_share=%.2f%%  tri_share=%.2f%%"
      % (100.0 * 2 * tq / tt, 100.0 * (tt - 2 * tq) / tt))

print("--- new / changed parts ---")
for n in ("V2_FrontPill", "V2_NamePlate", "V2_NamePlate_Mark", "V2_NamePlate_Line1",
          "V2_NamePlate_Line2", "Machine_Chute", "P1_OutletRailL", "P1_OutletRailR",
          "P1_ChuteRail"):
    for r in rows:
        if r[0] == n:
            print("OBJ %-18s v=%4d f=%4d tri=%4d q=%4d" % (r[0], r[1], r[2], r[3], r[4]))

print("--- world bounds ---")
for n in ("V2_FrontPill", "V2_NamePlate", "Machine_Chute", "P1_OutletRailL",
          "P1_OutletRailR", "P1_ChuteRail", "P1_OutletCollar", "P2_OutletBand",
          "P3c_Button_Mode", "P3c_Button_Power", "P3d_Label", "P3d_RingSeat_Power",
          "P2_Plasma", "Cutter_Outlet", "Machine_Light_01", "Machine_WindowFrame"):
    ob = bpy.data.objects.get(n)
    if ob is None:
        print("BB %-18s MISSING" % n)
        continue
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs = [p.x for p in bb]; ys = [p.y for p in bb]; zs = [p.z for p in bb]
    print("BB %-18s x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f]"
          % (n, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

print("--- cameras / lights ---")
for ob in bpy.data.objects:
    if ob.type in {'CAMERA', 'LIGHT'}:
        print("RIG %-8s %s" % (ob.type, ob.name))

print("--- new objects' parents / animation ---")
for ob in bpy.data.objects:
    if ob.name.startswith("V2_"):
        print("CHK %-22s par=%-16s anim=%s loc=%s"
              % (ob.name, ob.parent.name if ob.parent else "-",
                 bool(ob.animation_data and ob.animation_data.action),
                 tuple(round(v, 4) for v in ob.matrix_world.translation)))
