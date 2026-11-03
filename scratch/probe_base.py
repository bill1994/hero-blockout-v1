"""What is actually at the base? Raycast a grid; find all meshes intersecting the base zone."""
import bpy, json
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
bpy.context.view_layer.update()
scn = bpy.context.scene
R = {}

def down(x,y,z0=0.9):
    d=Vector((0,0,-1)); cur=Vector((x,y,z0)); seq=[]
    for _ in range(10):
        ok,loc,nor,idx,obj,mw = scn.ray_cast(bpy.context.view_layer.depsgraph, cur, d)
        if not ok: seq.append(('ESCAPE',round(cur.z,3))); break
        seq.append((obj.name, round(loc.z,3))); cur = loc + d*0.0012
    return seq

grid = {}
for x in (-0.85,-0.70,-0.55,-0.39,-0.20,0.0,0.20,0.45,0.65,0.80,0.90):
    for y in (-0.70,-0.52,0.0,0.52,0.70):
        grid[f'x={x},y={y}'] = down(x,y)
R['BASE_DOWN_GRID'] = grid

# every mesh whose world bbox intersects z in [-0.15, 0.55]
near=[]
for o in bpy.data.objects:
    if o.type!='MESH': continue
    oe=o.evaluated_get(dg); mw=oe.matrix_world
    pts=[mw @ Vector((c[0],c[1],c[2])) for c in oe.bound_box]
    zmin=min(p.z for p in pts); zmax=max(p.z for p in pts)
    if zmax < -0.16 or zmin > 0.56: continue
    near.append(dict(name=o.name, hide_render=o.hide_render, visible=o.visible_get(),
        bbox_min=[round(min(p[i] for p in pts),4) for i in range(3)],
        bbox_max=[round(max(p[i] for p in pts),4) for i in range(3)],
        mat=[s.material.name if s.material else None for s in o.material_slots],
        parent=o.parent.name if o.parent else None))
R['NEAR_BASE_MESHES']=near

# proxy / pedestal objects
for n in ('Product_Proxy_FitCheck','Product_Proxy_Large','Prop_IdeaPedestal','Idea','Product'):
    o=bpy.data.objects.get(n)
    if o:
        oe=o.evaluated_get(dg); mw=oe.matrix_world
        pts=[mw @ Vector((c[0],c[1],c[2])) for c in oe.bound_box]
        R[n]=dict(hide_render=o.hide_render, visible=o.visible_get(),
            bbox_min=[round(min(p[i] for p in pts),4) for i in range(3)],
            bbox_max=[round(max(p[i] for p in pts),4) for i in range(3)])

print("###JSON_START###")
print(json.dumps(R,indent=1,default=str))
print("###JSON_END###")
