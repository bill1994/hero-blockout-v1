"""Deep audit: base, bolts, claw, outlet geometry of the current asset."""
import bpy, json, math
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
bpy.context.view_layer.update()
scene = bpy.context.scene

def ev(o):
    return o.evaluated_get(dg)

def wbb(o):
    oe = ev(o); mw = oe.matrix_world
    pts = [mw @ Vector(c) for c in oe.bound_box]
    return ([round(min(p[i] for p in pts),4) for i in range(3)],
            [round(max(p[i] for p in pts),4) for i in range(3)])

def meshstats(o):
    oe = ev(o)
    me = oe.to_mesh()
    me.calc_loop_triangles()
    nm = len(me.vertices); np_ = len(me.polygons)
    ne = len(me.edges)
    # manifold / closed check on evaluated mesh
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    nonmanifold = sum(1 for e in bm.edges if not e.is_manifold)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    wire = sum(1 for e in bm.edges if e.is_wire)
    vol = bm.calc_volume(signed=True) if nonmanifold == 0 else None
    bm.free()
    res = dict(verts=nm, polys=np_, edges=ne, tris=len(me.loop_triangles),
               nonmanifold_edges=nonmanifold, boundary_edges=boundary, wire_edges=wire,
               signed_volume=round(vol,5) if vol is not None else None,
               ngons=sum(1 for p in me.polygons if len(p.vertices)>4),
               smooth_polys=sum(1 for p in me.polygons if p.use_smooth))
    oe.to_mesh_clear()
    return res

def mods(o):
    out = []
    for m in o.modifiers:
        d = dict(name=m.name, type=m.type)
        for k in ('width','segments','limit_method','angle_limit','use_clamp_overlap',
                  'operation','solver','object','use_hole_tolerant','offset_type',
                  'levels','render_levels','show_viewport','show_render','mode'):
            if hasattr(m, k):
                v = getattr(m, k)
                if isinstance(v, float): v = round(v,5)
                d[k] = v
        out.append(d)
    return out

def mats(o):
    return [s.material.name if s.material else None for s in o.material_slots]

def dump(n):
    o = bpy.data.objects.get(n)
    if not o: return {'name': n, 'missing': True}
    mn, mx = wbb(o)
    d = dict(name=n, type=o.type,
             parent=o.parent.name if o.parent else None,
             hide_render=o.hide_render, hide_viewport=o.hide_viewport,
             visible=o.visible_get(),
             bbox_min=mn, bbox_max=mx,
             dim=[round(mx[i]-mn[i],4) for i in range(3)],
             loc=[round(v,4) for v in o.location],
             scale=[round(v,4) for v in o.scale],
             rot_deg=[round(math.degrees(v),2) for v in o.rotation_euler],
             modifiers=mods(o), materials=mats(o))
    if o.type=='MESH':
        d['mesh'] = meshstats(o)
        # world-space vertex cloud for spatial analysis
        oe = ev(o); mw = oe.matrix_world
        vs = [mw @ v.co for v in oe.data.vertices]
        if vs:
            d['n_world_verts'] = len(vs)
    return d

R = {}

# ================= 1. BASE =================
base_names = [n for n in bpy.data.objects.keys() if any(k in n for k in
               ('Base','Feet','Foot','Plinth','Leg'))]
R['BASE'] = {n: dump(n) for n in base_names}

# base profile: cross-section of Machine_Base at several y
ob = bpy.data.objects.get('Machine_Base')
if ob:
    prof = []
    for zz in [0.05,0.1,0.15,0.2,0.25,0.28,0.3,0.35]:
        # find vertices near this z
        oe = ev(ob); mw = oe.matrix_world
        vs = [mw @ v.co for v in oe.data.vertices]
        sel = [v for v in vs if abs(v.z-zz) < 0.012]
        if sel:
            prof.append(dict(z=zz, x=[round(min(p.x for p in sel),3), round(max(p.x for p in sel),3)],
                             y=[round(min(p.y for p in sel),3), round(max(p.y for p in sel),3)], n=len(sel)))
    R['BASE_profile'] = prof

# ================= 2. BOLTS / SCREWS =================
bolt_names = sorted([n for n in bpy.data.objects.keys() if 'Bolt' in n or 'Screw' in n])
R['BOLTS'] = {n: dump(n) for n in bolt_names}
R['BOLTS_positions'] = {}
for n in bolt_names:
    o = bpy.data.objects[n]
    oe = ev(o); mw = oe.matrix_world
    c = mw @ (sum((Vector(v) for v in oe.bound_box), Vector())/8.0)
    R['BOLTS_positions'][n] = dict(
        world=[round(c.x,4), round(c.y,4), round(c.z,4)],
        rot_deg=[round(math.degrees(v),2) for v in o.rotation_euler],
        verts=len(oe.data.vertices), polys=len(oe.data.polygons),
        mat=mats(o))

# any boolean cutters referencing bolts? any screw holes cut into body?
for bo in bpy.data.objects:
    if bo.type=='MESH':
        for m in bo.modifiers:
            if m.type=='BOOLEAN':
                R.setdefault('BOOLEANS',[]).append(
                    dict(host=bo.name, mod=m.name, op=getattr(m,'operand_type','?'),
                         target=getattr(m,'object',None).name if getattr(m,'object',None) else None))

# ================= 3. CLAW =================
claw_names = [n for n in bpy.data.objects.keys() if any(k in n for k in
              ('Finger','Gripper','Palm','Wrist','Cuff','GrabPoint'))]
R['CLAW'] = {n: dump(n) for n in claw_names}

# finger shape analysis at the closed pose frame
for fr in (31, 147):
    scene.frame_set(fr)
    dg2 = bpy.context.evaluated_depsgraph_get()
    fg = {}
    for n in claw_names:
        o = bpy.data.objects.get(n)
        if not o or o.type!='MESH': continue
        oe = o.evaluated_get(dg2); mw = oe.matrix_world
        vs = [mw @ v.co for v in oe.data.vertices]
        if not vs: continue
        fg[n] = dict(
            bbox_min=[round(min(p[i] for p in vs),4) for i in range(3)],
            bbox_max=[round(max(p[i] for p in vs),4) for i in range(3)],
            dim=[round(max(p[i] for p in vs)-min(p[i] for p in vs),4) for i in range(3)],
            world_centre=[round(sum(p[i] for p in vs)/len(vs),4) for i in range(3)],
            rot_deg=[round(math.degrees(v),2) for v in o.rotation_euler],
            scale=[round(v,4) for v in o.scale])
    R.setdefault('CLAW_by_frame',{})[f'f{fr}'] = fg
    # relative angle of each finger about the gripper axis
    gp = bpy.data.objects.get('Arm_Gripper')
    if gp:
        axis = ev(gp).matrix_world.to_3x3() @ Vector((0,0,1))
        base = []
        for n in claw_names:
            if 'Finger' not in n: continue
            o = bpy.data.objects[n]
            c = ev(o).matrix_world.translation
            r = c - ev(gp).matrix_world.translation
            r = r - axis * r.dot(axis)
            if r.length > 1e-6:
                a = math.atan2(r.y, r.x)
                base.append(dict(finger=n, angle_deg=round(math.degrees(a),2),
                                 radius=round(r.length,4)))
        R.setdefault('CLAW_radial',{})[f'f{fr}'] = sorted(base, key=lambda d:d['angle_deg'])
scene.frame_set(1)

# ================= 4. OUTLET =================
out_names = [n for n in bpy.data.objects.keys() if any(k in n for k in
              ('Chute','Outlet','Cutter_Outlet','Seat'))]
R['OUTLET'] = {n: dump(n) for n in out_names}

# is the chute an open trough or a closed solid? -> count boundary edges & check cross-section
oe = ev(bpy.data.objects['Machine_Chute'])
me = oe.to_mesh()
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
R['CHUTE_openness'] = dict(
    boundary_edges=sum(1 for e in bm.edges if e.is_boundary),
    nonmanifold=sum(1 for e in bm.edges if not e.is_manifold),
    verts=len(bm.verts), faces=len(bm.faces))
bm.free(); oe.to_mesh_clear()

# cross-section of the chute at several x: slice the mesh
def slice_x(o, x):
    """Return the set of (y,z) points of the mesh at plane x (evaluated)."""
    oe = ev(o); mw = oe.matrix_world
    pts = []
    for p in oe.data.polygons:
        for vi in p.vertices:
            v = mw @ oe.data.vertices[vi].co
            if abs(v.x - x) < 0.004:
                pts.append((round(v.y,3), round(v.z,3)))
    return sorted(set(pts))

R['CHUTE_slices'] = {str(x): slice_x(bpy.data.objects['Machine_Chute'], x)
                     for x in (0.9, 1.1, 1.3, 1.5, 1.58, 1.9, 2.2, 2.29)}

# ray test straight down the outlet axis from inside the body
def ray_axis(zc, ys):
    hits = []
    org = Vector((0.2, ys, zc))
    d = Vector((1,0,0))
    res = []
    cur = org.copy()
    for _ in range(24):
        ok, loc, nor, idx, obj, mw = scene.ray_cast(bpy.context.view_layer.depsgraph, cur, d)
        if not ok:
            res.append(('ESCAPE', round(cur.x,3)))
            break
        res.append((obj.name, round(loc.x,3)))
        cur = loc + d*0.0015
    return res

R['AXIS_RAYS'] = {}
for zc in (1.10, 1.20, 1.30, 1.40, 1.50):
    R['AXIS_RAYS'][f'z{zc}'] = ray_axis(zc, 0.0)

# ================= global =================
R['total_tris'] = 0
for o in bpy.data.objects:
    if o.type=='MESH' and not o.hide_render:
        oe = ev(o); me = oe.to_mesh(); me.calc_loop_triangles()
        R['total_tris'] += len(me.loop_triangles); oe.to_mesh_clear()

print("###JSON_START###")
print(json.dumps(R, indent=1, default=str))
print("###JSON_END###")
