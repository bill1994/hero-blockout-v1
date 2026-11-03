"""Audit the four focus areas of the current asset: base, screw holes, claw, outlet."""
import bpy, json, math
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
bpy.context.view_layer.update()

def wbb(o):
    try:
        oe = o.evaluated_get(dg)
        mw = oe.matrix_world
        pts = [mw @ Vector(c) for c in oe.bound_box]
        mn = [min(p[i] for p in pts) for i in range(3)]
        mx = [max(p[i] for p in pts) for i in range(3)]
        return [round(v, 4) for v in mn], [round(v, 4) for v in mx]
    except Exception as e:
        return None, str(e)

def mods(o):
    return [(m.name, m.type, round(getattr(m, 'width', 0) or 0, 4),
             getattr(m, 'segments', None), getattr(m, 'limit_method', None),
             getattr(m, 'angle_limit', None)) for m in o.modifiers]

def tris(o):
    try:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        n = sum(len(p.vertices) - 2 for p in me.polygons)
        oe.to_mesh_clear()
        return n
    except Exception:
        return None

def slotinfo(o):
    out = []
    for i, s in enumerate(o.material_slots):
        m = s.material
        out.append((i, m.name if m else None))
    return out

def polyinfo(o, limit=40):
    """Sample polygons: normal spread tells us flat vs curved."""
    try:
        oe = o.evaluated_get(dg)
        me = oe.to_mesh()
        res = {
            'verts': len(me.vertices), 'polys': len(me.polygons),
            'ngons': sum(1 for p in me.polygons if len(p.vertices) > 4),
            'tris': sum(1 for p in me.polygons if len(p.vertices) == 3),
            'quads': sum(1 for p in me.polygons if len(p.vertices) == 4),
            'loose_verts': sum(1 for v in me.vertices if not any(v.index in e.vertices for e in me.edges)),
            'smooth': sum(1 for p in me.polygons if p.use_smooth),
        }
        oe.to_mesh_clear()
        return res
    except Exception as e:
        return {'error': str(e)}

names = sorted([o.name for o in bpy.data.objects])
report = {'file': bpy.data.filepath, 'frame': bpy.context.scene.frame_current,
          'all_objects': names}

# ---- classify --------------------------------------------------------
KEY = {
 'base': ['Machine_Base','Machine_BaseBand','Machine_Feet','Machine_Plinth','Base','Plinth',
          'Machine_Base_Foot','Machine_BaseFoot','Machine_Leg'],
 'bolts': ['P1_Bolt','Bolt','Screw','Machine_Screw'],
 'claw': ['Arm_Finger','Arm_Gripper','Arm_Palm','Arm_Wrist','Arm_Cuff'],
 'outlet': ['Machine_Chute','P1_ChuteSeat','P1_Outlet','P2_OutletBand','P1_ChuteRail',
            'Cutter_Outlet','Machine_Detail','Outlet_Flap'],
}

def match(pat):
    return [n for n in names if pat in n]

buckets = {}
for k, pats in KEY.items():
    buckets[k] = match(k)
report['buckets'] = buckets

def dump(n):
    o = bpy.data.objects.get(n)
    if not o:
        return {'name': n, 'missing': True}
    mn, mx = wbb(o)
    d = {
        'name': n, 'type': o.type,
        'parent': o.parent.name if o.parent else None,
        'hide_render': o.hide_render, 'hide_viewport': o.hide_viewport,
        'visible': o.visible_get() if o.name in bpy.context.view_layer.objects else None,
        'dim_world': [round(mx[i]-mn[i], 4) for i in range(3)] if isinstance(mx, list) else None,
        'bbox_min': mn, 'bbox_max': mx,
        'loc': [round(v,4) for v in o.location],
        'scale': [round(v,4) for v in o.scale],
        'rot_euler': [round(math.degrees(v),2) for v in o.rotation_euler],
        'modifiers': mods(o),
        'materials': slotinfo(o),
        'tris': tris(o),
    }
    if o.type == 'MESH':
        d['mesh'] = polyinfo(o)
    return d

report['detail'] = {n: dump(n) for grp in buckets.values() for n in grp}

# ---- scene wide bbox of visible mesh ---------------------------------
allpts = []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.hide_render:
        continue
    oe = o.evaluated_get(dg)
    mw = oe.matrix_world
    for c in oe.bound_box:
        allpts.append(mw @ Vector(c))
if allpts:
    report['scene_bbox'] = {
        'min': [round(min(p[i] for p in allpts), 4) for i in range(3)],
        'max': [round(max(p[i] for p in allpts), 4) for i in range(3)]}

report['total_tris'] = sum(t or 0 for t in [dump(n)['tris'] for n in names
                                           if bpy.data.objects.get(n) and bpy.data.objects[n].type=='MESH'])

print("###JSON_START###")
print(json.dumps(report, indent=1))
print("###JSON_END###")
