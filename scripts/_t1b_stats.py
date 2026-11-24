"""T1b measurement: totals + the two fixed regions. Read-only, prints JSON-ish lines."""
import bpy
import os
from mathutils import Vector

ROOT = r"G:\DSHProject\BlenderMcp"
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "rebuild_v2.blend"))
sc = bpy.context.scene
sc.frame_set(1)
bpy.context.view_layer.update()


def bb(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return None
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts),
            min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts))


tv = tt = tf = tq = tn = 0
for ob in bpy.data.objects:
    if ob.type != 'MESH':
        continue
    me = ob.data
    me.calc_loop_triangles()
    tt += len(me.loop_triangles)
    tv += len(me.vertices)
    tf += len(me.polygons)
    for p in me.polygons:
        n = len(p.vertices)
        if n == 4:
            tq += 1
        elif n == 3:
            pass
        else:
            tn += 1

print("TOTAL verts=%d tris=%d faces=%d quads=%d ngons=%d quad_share=%.1f%%"
      % (tv, tt, tf, tq, tn, 100.0 * tq / tf))

for n in ("Machine_Chute", "P1_OutletRailL", "P1_OutletRailR", "P1_ChuteRail",
          "V2_NamePlate", "V2_NamePlate_Mark", "V2_NamePlate_Line1", "V2_NamePlate_Line2",
          "Machine_WindowFrame", "Machine_WindowGlass", "Machine_Body"):
    r = bb(n)
    if r is None:
        print("BB %-20s MISSING" % n)
        continue
    print("BB %-20s x[%7.3f %7.3f] y[%7.3f %7.3f] z[%7.3f %7.3f]  w=%.3f h=%.3f"
          % (n, r[0], r[1], r[2], r[3], r[4], r[5], r[1] - r[0], r[5] - r[4]))

# --- explicit checks -------------------------------------------------------
ch = bb("Machine_Chute")
rail = bb("P1_ChuteRail")
plate = bb("V2_NamePlate")
frame = bb("Machine_WindowFrame")
print("CHECK chute_end=%.4f  (target 2.60 +-0.03)  %s"
      % (ch[1], "OK" if abs(ch[1] - 2.60) <= 0.03 else "FAIL"))
print("CHECK rail_end=%.4f  (target 2.88 +-0.04)  %s"
      % (rail[1], "OK" if abs(rail[1] - 2.88) <= 0.04 else "FAIL"))
print("CHECK plate_w=%.4f plate_h=%.4f  (min 0.36 x 0.17)  %s"
      % (plate[1] - plate[0], plate[5] - plate[4],
         "OK" if (plate[1] - plate[0]) >= 0.36 and (plate[5] - plate[4]) >= 0.17 else "FAIL"))
print("CHECK plate_x=[%.3f %.3f] plate_z=[%.3f %.3f]" % (plate[0], plate[1], plate[4], plate[5]))
print("CHECK screen_z_top=%.4f plate_z_min=%.4f  gap=%.4f  %s"
      % (frame[5], plate[4], plate[4] - frame[5],
         "OK" if plate[4] > frame[5] else "CLASH"))
print("CHECK body_front_y=%.4f plate_front_y=%.4f" % (-0.800, plate[2]))

# nameplate row containment inside the plate (world x/z)
for n in ("V2_NamePlate_Mark", "V2_NamePlate_Line1", "V2_NamePlate_Line2"):
    r = bb(n)
    if r is None:
        continue
    inside = (r[0] > plate[0] + 0.01 and r[1] < plate[1] - 0.01
              and r[4] > plate[4] + 0.005 and r[5] < plate[5] - 0.005)
    print("ROW %-20s x[%.3f %.3f] z[%.3f %.3f] inside=%s"
          % (n, r[0], r[1], r[4], r[5], inside))

# chute body sanity: still meets the shell, still on the 10.8 deg slope
import math
print("CHECK chute_z=[%.3f %.3f]  chute_len_x=%.3f  slope_deg=%.2f  (target 10.83)"
      % (ch[4], ch[5], ch[1] - ch[0], math.degrees(math.atan(0.189))))
print("CHECK objects=%d" % sum(1 for o in bpy.data.objects if o.type == 'MESH'))
print("CHECK V2_objects=%s" % ", ".join(sorted(o.name for o in bpy.data.objects
                                                if o.name.startswith("V2_"))))
