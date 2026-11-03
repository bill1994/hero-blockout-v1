"""Render matched comparison views: front / 3q / top + 4 detail closeups."""
import bpy, os, math
from mathutils import Vector

OUT = 'G:/DSHProject/BlenderMcp/review/v14/audit'
os.makedirs(OUT, exist_ok=True)
scn = bpy.context.scene
scn.render.engine = 'BLENDER_EEVEE'
scn.render.resolution_x = 1100
scn.render.resolution_y = 1100
scn.render.image_settings.file_format = 'PNG'
scn.view_settings.view_transform = 'Standard'

# frame 200 = product out of the way (empty machine), frame 248 = product in mouth
scn.frame_set(200)

cam_data = bpy.data.cameras.new('AuditCam')
cam = bpy.data.objects.new('AuditCam', cam_data)
scn.collection.objects.link(cam)
scn.camera = cam
cam_data.lens = 50

def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def shot(name, loc, target, lens=50, res=(1100,1100), ortho=None):
    cam.location = Vector(loc)
    cam_data.lens = lens
    if ortho:
        cam_data.type = 'ORTHO'; cam_data.ortho_scale = ortho
    else:
        cam_data.type = 'PERSP'
    look_at(cam, target)
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.filepath = f'{OUT}/{name}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name)

TGT = (0.0, 0.0, 1.35)

# three matched views
shot('cur_front', (0.0, -9.0, 1.35), TGT, lens=50)
shot('cur_3q',    (-5.2, -7.6, 3.4), TGT, lens=50)
shot('cur_top',   (0.0, -0.35, 9.0), TGT, lens=50, ortho=2.6)

# 1) BASE detail  (base z 0..0.444, feet to -0.1)
shot('det_base',      (1.6, -3.0, 0.75), (0.0, 0.0, 0.18), lens=70, res=(1000,1000))

# 2) SCREW detail (bolts on front face y=-0.9, x=+-0.78, z=0.533 and 2.447)
shot('det_screw_up',  (-0.78, -3.2, 2.6), (-0.78, -0.9, 2.447), lens=90, res=(1000,1000))
shot('det_screw_lo',  (-0.78, -3.2, 0.9), (-0.78, -0.9, 0.533), lens=90, res=(1000,1000))

# 3) CLAW detail  (gripper at f31 closed pose)
scn.frame_set(31)
shot('det_claw_closed', (-3.0, -2.6, 2.55), (-3.09, -0.54, 2.63), lens=95, res=(1000,1000))
scn.frame_set(147)
shot('det_claw_open',   (-0.35, -1.9, 4.1), (-0.34, 0.0, 4.09), lens=95, res=(1000,1000))
scn.frame_set(200)

# 4) OUTLET detail
shot('det_outlet_3q',  (2.6, -2.2, 2.2), (1.5, 0.0, 1.30), lens=70, res=(1100,1100))
shot('det_outlet_side',(1.7, -4.2, 1.55), (1.55, 0.0, 1.30), lens=75, res=(1100,1100))
shot('det_outlet_top', (1.55, -0.05, 4.2), (1.55, 0.0, 1.30), lens=60, res=(1100,1100), ortho=1.6)

# 5) outlet mouth look-back: camera outside looking into the mouth
shot('det_outlet_mouth', (3.6, 0.0, 1.30), (0.5, 0.0, 1.30), lens=85, res=(1100,700))

print("DONE")
