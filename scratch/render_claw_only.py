import bpy
from mathutils import Vector
OUT='G:/DSHProject/BlenderMcp/review/v14/audit'
scn=bpy.context.scene
scn.render.engine='BLENDER_EEVEE'
scn.render.resolution_x=1100; scn.render.resolution_y=1100
scn.view_settings.view_transform='Standard'
KEEP={'Arm_Finger_L','Arm_Finger_R','Arm_Finger_C','Arm_Gripper','Arm_WristCollar',
      'P3d_WristCuff','Arm_Wrist','Idea','Product','Machine_Body','Machine_Root','Arm_Base'}
hidden=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name not in KEEP:
        hidden.append(o); o.hide_render=True
cam_d=bpy.data.cameras.new('C'); cam=bpy.data.objects.new('C',cam_d)
scn.collection.objects.link(cam); scn.camera=cam; cam_d.lens=60
def look(o,t):
    d=Vector(t)-o.location; o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
def shot(n,loc,tgt,lens=60,f=31):
    scn.frame_set(f)
    cam.location=Vector(loc); cam_d.lens=lens; look(cam,tgt)
    scn.render.filepath=f'{OUT}/{n}.png'; bpy.ops.render.render(write_still=True); print('R',n,f)
import math
for f,tag in ((31,'closed'),(147,'open')):
    scn.frame_set(f)
    dg=bpy.context.evaluated_depsgraph_get()
    gp=bpy.data.objects['Arm_Gripper'].evaluated_get(dg).matrix_world.translation
    shot(f'claw_only_{tag}', (gp.x+0.45, gp.y-1.15, gp.z+0.35), tuple(gp), 70, f)
for o in hidden: o.hide_render=False
print('DONE')
