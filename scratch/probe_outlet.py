"""Precise probe of the outlet region: true cross-sections, solidity, ray reachability."""
import bpy, json, math, bmesh
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
bpy.context.view_layer.update()
scene = bpy.context.scene

def ev(o): return o.evaluated_get(dg)

R = {}

# ---------- 1. TRUE cross-sections via bmesh bisect ----------
def section(objname, axis, val, filt=None):
    o = bpy.data.objects.get(objname)
    if not o: return None
    oe = ev(o); me = oe.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me)
    mw = oe.matrix_world
    # work in world space
    bmesh.ops.transform(bm, matrix=mw, verts=bm.verts)
    geom = list(bm.verts)+list(bm.edges)+list(bm.faces)
    normal = {'x':Vector((1,0,0)),'y':Vector((0,1,0)),'z':Vector((0,0,1))}[axis]
    try:
        res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=normal*val,
                                    plane_no=normal, clear_inner=False, clear_outer=False)
        edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        pts = []
        for e in edges:
            for v in e.verts:
                p = v.co
                if filt is None or filt(p):
                    pts.append((round(p.x,3), round(p.y,3), round(p.z,3)))
        pts = sorted(set(pts))
        return {'n': len(pts), 'pts': pts}
    finally:
        bm.free(); oe.to_mesh_clear()

def summarise(objname, axis, val, filt=None):
    s = section(objname, axis, val, filt)
    if not s or not s['pts']: return {'n':0}
    ps = s['pts']
    d = {'n': s['n']}
    for i,ax in enumerate('xyz'):
        d[ax] = [min(p[i] for p in ps), max(p[i] for p in ps)]
    return d

R['SECTIONS_chute_X'] = {}
for x in (0.90, 1.10, 1.30, 1.50, 1.58, 1.80, 2.10, 2.28):
    R['SECTIONS_chute_X'][f'x={x}'] = summarise('Machine_Chute','x',x)
R['SECTIONS_collar_X'] = {}
for x in (1.51, 1.55, 1.59):
    R['SECTIONS_collar_X'][f'x={x}'] = summarise('P1_OutletCollar','x',x)

# ---------- 2. is the chute a closed solid? vertical reachability ----------
# ray straight DOWN from above the chute at a grid of (x,y)
def down_ray(x, y, z0=2.2):
    d = Vector((0,0,-1)); cur = Vector((x,y,z0)); seq=[]
    for _ in range(12):
        ok, loc, nor, idx, obj, mw = scene.ray_cast(bpy.context.view_layer.depsgraph, cur, d)
        if not ok: seq.append(('ESCAPE', round(cur.z,3))); break
        seq.append((obj.name, round(loc.z,3)))
        cur = loc + d*0.0012
    return seq

grid = {}
for x in (1.0, 1.2, 1.4, 1.55, 1.75, 2.0, 2.25):
    for y in (-0.30, -0.15, 0.0, 0.15, 0.30):
        grid[f'x={x},y={y}'] = down_ray(x,y)
R['DOWN_RAYS'] = grid

# ---------- 3. horizontal axis rays (from body bore outward) at many z ----------
def fwd_ray(y, z, x0=0.3):
    d = Vector((1,0,0)); cur = Vector((x0,y,z)); seq=[]
    for _ in range(20):
        ok, loc, nor, idx, obj, mw = scene.ray_cast(bpy.context.view_layer.depsgraph, cur, d)
        if not ok: seq.append(('ESCAPE', round(cur.x,3))); break
        seq.append((obj.name, round(loc.x,3)))
        cur = loc + d*0.0012
    return seq

fwd = {}
for z in (1.06, 1.12, 1.20, 1.28, 1.36, 1.44, 1.52):
    fwd[f'z={z}'] = fwd_ray(0.0, z)
R['FWD_RAYS'] = fwd

# ---------- 4. solid-body test: is the trough interior enclosed? ----------
# for each x station, sample the vertical column at y=0 and see if there is a
# gap (air) between the rim and the floor
def column_profile(x):
    seq = down_ray(x, 0.0, z0=1.75)
    return seq
R['COLUMNS'] = {f'x={x}': column_profile(x) for x in (1.0,1.2,1.4,1.55,1.7,2.0,2.25)}

# ---------- 5. body bore: does Machine_Body actually have a hole? ----------
o = bpy.data.objects.get('Machine_Body')
oe = ev(o); me = oe.to_mesh()
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table()
bmesh.ops.transform(bm, matrix=oe.matrix_world, verts=bm.verts)
R['BODY'] = dict(verts=len(bm.verts), faces=len(bm.faces),
                 volume=round(bm.calc_volume(signed=True),5),
                 boundary=sum(1 for e in bm.edges if e.is_boundary),
                 nonmanifold=sum(1 for e in bm.edges if not e.is_manifold))
bm.free(); oe.to_mesh_clear()

# cutter
o = bpy.data.objects.get('Cutter_Outlet')
oe = ev(o); me = oe.to_mesh()
_cpts = [oe.matrix_world @ Vector((c[0], c[1], c[2])) for c in oe.bound_box]
R['CUTTER_outlet'] = dict(verts=len(me.vertices), faces=len(me.polygons),
    bbox_min=[round(min(p[i] for p in _cpts),4) for i in range(3)],
    bbox_max=[round(max(p[i] for p in _cpts),4) for i in range(3)],
    hide_render=o.hide_render, visible=o.visible_get(),
    parent=o.parent.name if o.parent else None)
oe.to_mesh_clear()

# ---------- 6. base detail: feet geometry, groove search ----------
for nm in ('Machine_Base','Machine_Feet','P1_BaseBand','Machine_Body'):
    o = bpy.data.objects.get(nm)
    if not o: continue
    oe = ev(o); me = oe.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.transform(bm, matrix=oe.matrix_world, verts=bm.verts)
    zs = sorted(set(round(v.co.z,3) for v in bm.verts))
    ys = sorted(set(round(v.co.y,3) for v in bm.verts))
    xs = sorted(set(round(v.co.x,3) for v in bm.verts))
    R.setdefault('BASEGEO',{})[nm] = dict(
        verts=len(bm.verts), faces=len(bm.faces), volume=round(bm.calc_volume(signed=True),5),
        distinct_z=zs, distinct_y=ys[:24], distinct_x=xs[:24],
        n_z=len(zs), n_y=len(ys), n_x=len(xs))
    bm.free(); oe.to_mesh_clear()

# Machine_Feet: how many separate lumps?
o = bpy.data.objects.get('Machine_Feet')
oe = ev(o); me = oe.to_mesh()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.transform(bm, matrix=oe.matrix_world, verts=bm.verts)
# cluster by connected components
seen=set(); comps=[]
for v in bm.verts:
    if v.index in seen: continue
    stack=[v]; comp=[]
    seen.add(v.index)
    while stack:
        c=stack.pop(); comp.append(c)
        for e in c.link_edges:
            oth=e.other_vert(c)
            if oth.index not in seen:
                seen.add(oth.index); stack.append(oth)
    comps.append(comp)
R['FEET'] = []
for comp in comps:
    ps=[c.co for c in comp]
    R['FEET'].append(dict(nv=len(comp),
        min=[round(min(p[i] for p in ps),4) for i in range(3)],
        max=[round(max(p[i] for p in ps),4) for i in range(3)]))
bm.free(); oe.to_mesh_clear()

print("###JSON_START###")
print(json.dumps(R, indent=1, default=str))
print("###JSON_END###")
