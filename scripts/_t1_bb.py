import bpy, os
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=r"G:\DSHProject\BlenderMcp\versions\rebuild_t1.blend")
sc = bpy.context.scene; sc.frame_set(1); bpy.context.view_layer.update()
for n in ("V2_FrontPill","V2_NamePlate","V2_NamePlate_Mark","V2_NamePlate_Line1","V2_NamePlate_Line2",
          "Machine_Chute","P1_OutletRailL","P1_OutletRailR","P1_ChuteRail"):
    ob = bpy.data.objects.get(n)
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    xs=[p.x for p in bb]; ys=[p.y for p in bb]; zs=[p.z for p in bb]
    print("BB %-20s x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f] par=%s"
          % (n, min(xs),max(xs), min(ys),max(ys), min(zs),max(zs), ob.parent.name if ob.parent else "-"))
