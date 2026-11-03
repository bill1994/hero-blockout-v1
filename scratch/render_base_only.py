import bpy, os
from mathutils import Vector
OUT='G:/DSHProject/BlenderMcp/review/v14/audit'
scn=bpy.context.scene
scn.render.engine='BLENDER_EEVEE'
scn.render.resolution_x=1100; scn.render.resolution_y=1100
scn.view_settings.view_transform='Standard'
scn.frame_set(200)
KEEP={'Machine_Base','Machine_Feet','P1_BaseBand','Machine_Root'}
hidden=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name not in KEEP:
        hidden.append(o); o.hide_render=True
cam_d=bpy.data.cameras.new('C'); cam=bpy.data.objects.new('C',cam_d)
scn.collection.objects.link(cam); scn.camera=cam; cam_d.lens=52
def look(o,t):
    d=Vector(t)-o.location; o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
def shot(n,loc,tgt,lens=52):
    cam.location=Vector(loc); cam_d.lens=lens; look(cam,tgt)
    scn.render.filepath=f'{OUT}/{n}.png'; bpy.ops.render.render(write_still=True); print('R',n)
shot('base_only_3q',(1.9,-2.6,0.95),(0,0,0.15))
shot('base_only_low',(2.2,-1.9,0.18),(0,0,0.12),lens=45)
shot('base_only_below',(1.4,-1.6,-0.55),(0,0,0.05),lens=45)
for o in hidden: o.hide_render=False
print('DONE')
