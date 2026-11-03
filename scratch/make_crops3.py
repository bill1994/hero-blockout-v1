import bpy, numpy as np, os
OUT='G:/DSHProject/BlenderMcp/scratch/crops'
def load(p):
    img=bpy.data.images.load(p, check_existing=False); w,h=img.size
    px=np.empty(w*h*img.channels,dtype=np.float32); img.pixels.foreach_get(px)
    px=px.reshape(h,w,img.channels)[::-1]; bpy.data.images.remove(img); return px
def save(a,p):
    h,w,c=a.shape
    if c==3: a=np.dstack([a,np.ones((h,w,1),np.float32)])
    i=bpy.data.images.new(os.path.basename(p),width=w,height=h,alpha=True)
    i.pixels.foreach_set(a[::-1].ravel()); i.filepath_raw=p; i.file_format='PNG'; i.save()
    bpy.data.images.remove(i)
def crop(px,r,z,p,gain=1.0):
    x0,y0,x1,y1=r; c=px[y0:y1,x0:x1]
    c=np.repeat(np.repeat(c,z,axis=0),z,axis=1)
    if gain!=1.0:
        rgb=np.clip(c[...,:3]*gain,0,1); c=np.dstack([rgb,c[...,3:4]]) if c.shape[2]==4 else rgb
    save(c,p); print("saved",p,c.shape)

ref=load('G:/DSHProject/BlenderMcp/reference/style_v13_ref.png')
crop(ref,(700,300,800,400),8,f'{OUT}/ref_claw_p1.png')
crop(ref,(690,600,900,760),4,f'{OUT}/ref_base_p1.png')
crop(ref,(60,280,180,400),7,f'{OUT}/ref_claw_p0.png')
print("DONE")
