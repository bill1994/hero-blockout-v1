import bpy, bmesh, json
from mathutils import Vector
dg=bpy.context.evaluated_depsgraph_get()
scn=bpy.context.scene
R={}
# --- base: connected components + volume vs bbox ---
for nm in ('Machine_Base','Machine_Feet','P1_BaseBand'):
    o=bpy.data.objects.get(nm)
    oe=o.evaluated_get(dg); me=oe.to_mesh()
    bm=bmesh.new(); bm.from_mesh(me); bmesh.ops.transform(bm,matrix=oe.matrix_world,verts=bm.verts)
    bm.verts.ensure_lookup_table()
    seen=set(); comps=0
    for v in bm.verts:
        if v.index in seen: continue
        comps+=1; st=[v]; seen.add(v.index)
        while st:
            c=st.pop()
            for e in c.link_edges:
                ov=e.other_vert(c)
                if ov.index not in seen: seen.add(ov.index); st.append(ov)
    bb=[round(min(v.co[i] for v in bm.verts),4) for i in range(3)]
    bx=[round(max(v.co[i] for v in bm.verts),4) for i in range(3)]
    vol=abs(bm.calc_volume(signed=True))
    boxvol=(bx[0]-bb[0])*(bx[1]-bb[1])*(bx[2]-bb[2])
    R[nm]=dict(components=comps, verts=len(bm.verts),
        bbox_min=bb, bbox_max=bx, signed_volume=round(vol,5),
        bbox_volume=round(boxvol,5), fill_ratio=round(vol/boxvol,4))
    bm.free(); oe.to_mesh_clear()

# --- is the body's outlet bore a blind pocket?  shoot a ray +X from inside at the bore ---
def fwd(y,z,x0):
    d=Vector((1,0,0)); cur=Vector((x0,y,z)); seq=[]
    for _ in range(30):
        ok,loc,nor,idx,obj,mw=scn.ray_cast(bpy.context.view_layer.depsgraph,cur,d)
        if not ok: seq.append(('ESCAPE',round(cur.x,3))); break
        seq.append((obj.name,round(loc.x,3))); cur=loc+d*0.0012
    return seq
R['bore_ray_from_inside_x0.3']={f'z={z}':fwd(0.0,z,0.3) for z in (1.05,1.10,1.20,1.30,1.40,1.44)}
# --- mouth look-back, body hidden -> is the channel continuous? ---
body=bpy.data.objects['Machine_Body']
body.hide_render=True
R['mouth_ray_nobody']={f'z={z}':fwd(0.0,z,2.9) for z in (1.10,1.20,1.30,1.40,1.50)}
body.hide_render=False
print("###JSON_START###"); print(json.dumps(R,indent=1,default=str)); print("###JSON_END###")
