"""Decisive probe: is the outlet a real through-channel? Plus base plan geometry."""
import bpy, json, math, bmesh
from mathutils import Vector

dg = bpy.context.evaluated_depsgraph_get()
bpy.context.view_layer.update()
scene = bpy.context.scene
R = {}

def ev(o): return o.evaluated_get(dg)

# ---------- 1. raw section points of the chute ----------
def raw_section(objname, axis, val):
    o = bpy.data.objects.get(objname)
    oe = ev(o); me = oe.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.transform(bm, matrix=oe.matrix_world, verts=bm.verts)
    normal = {'x':Vector((1,0,0)),'y':Vector((0,1,0)),'z':Vector((0,0,1))}[axis]
    geom = list(bm.verts)+list(bm.edges)+list(bm.faces)
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5,
                                 plane_co=normal*val, plane_no=normal,
                                 clear_inner=False, clear_outer=False)
    pts = set()
    for e in res['geom_cut']:
        if isinstance(e, bmesh.types.BMEdge):
            for v in e.verts:
                pts.add((round(v.co.x,3), round(v.co.y,3), round(v.co.z,3)))
    bm.free(); oe.to_mesh_clear()
    return sorted(pts)

R['chute_section_x1.0'] = raw_section('Machine_Chute','x',1.0)
R['chute_section_x2.0'] = raw_section('Machine_Chute','x',2.0)
R['collar_section_x1.55'] = raw_section('P1_OutletCollar','x',1.55)

# ---------- 2. down rays across the full trough width ----------
def down(x,y,z0=2.4):
    d=Vector((0,0,-1)); cur=Vector((x,y,z0)); seq=[]
    for _ in range(12):
        ok,loc,nor,idx,obj,mw = scene.ray_cast(bpy.context.view_layer.depsgraph, cur, d)
        if not ok: seq.append(('ESCAPE',round(cur.z,3))); break
        seq.append((obj.name, round(loc.z,3))); cur = loc + d*0.0012
    return seq
R['down_width_scan_x1.0'] = {f'y={y}': down(1.0,y) for y in
    (-0.42,-0.40,-0.38,-0.36,-0.34,-0.30,-0.20,0.0,0.20,0.30,0.34,0.36,0.38,0.40,0.42)}

# ---------- 3. can a ray ENTER the mouth from outside and reach the bore? ----------
def back_ray(y,z, x0=3.4):
    d=Vector((-1,0,0)); cur=Vector((x0,y,z)); seq=[]
    for _ in range(24):
        ok,loc,nor,idx,obj,mw = scene.ray_cast(bpy.context.view_layer.depsgraph, cur, d)
        if not ok: seq.append(('ESCAPE',round(cur.x,3))); break
        seq.append((obj.name, round(loc.x,3))); cur = loc + d*0.0012
    return seq
R['mouth_entry_x2.29'] = {f'z={z}': back_ray(0.0,z) for z in (1.08,1.15,1.25,1.35,1.45,1.52)}
R['mouth_entry_x1.20'] = {f'z={z}': back_ray(0.0,z,1.20) for z in (1.08,1.20,1.35,1.50)}

# ---------- 4. body bbox + base plan outline ----------
for nm in ('Machine_Body','Machine_Base','P1_BaseBand','Machine_Feet'):
    o = bpy.data.objects.get(nm)
    if not o: continue
    oe=ev(o); me=oe.to_mesh(); bm=bmesh.new(); bm.from_mesh(me)
    bmesh.ops.transform(bm, matrix=oe.matrix_world, verts=bm.verts)
    R[nm]=dict(
        min=[round(min(v.co[i] for v in bm.verts),4) for i in range(3)],
        max=[round(max(v.co[i] for v in bm.verts),4) for i in range(3)],
        vol=round(bm.calc_volume(signed=True),4), nv=len(bm.verts))
    bm.free(); oe.to_mesh_clear()

# base plan outline: horizontal sections of Machine_Base
def plan_section(objname, z):
    o=bpy.data.objects.get(objname); oe=ev(o); me=oe.to_mesh()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.transform(bm, matrix=oe.matrix_world, verts=bm.verts)
    geom=list(bm.verts)+list(bm.edges)+list(bm.faces)
    res=bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-5,plane_co=Vector((0,0,z)),
                               plane_no=Vector((0,0,1)),clear_inner=False,clear_outer=False)
    pts=set()
    for e in res['geom_cut']:
        if isinstance(e,bmesh.types.BMEdge):
            for v in e.verts: pts.add((round(v.co.x,3),round(v.co.y,3)))
    bm.free(); oe.to_mesh_clear(); return sorted(pts)
R['base_plan_z'] = {f'z={z}': plan_section('Machine_Base', z) for z in (0.02,0.10,0.20,0.28)}
R['band_plan_z'] = {f'z={z}': plan_section('P1_BaseBand', z) for z in (0.30,0.40,0.44)}

# body plan at a mid height for silhouette comparison
R['body_plan_z'] = {f'z={z}': plan_section('Machine_Body', z) for z in (0.30,0.50,1.0,2.4)}

print("###JSON_START###")
print(json.dumps(R, indent=1, default=str))
print("###JSON_END###")
