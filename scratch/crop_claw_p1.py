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
def crop(px,r,z,p):
    x0,y0,x1,y1=r; c=px[y0:y1,x0:x1]
    c=np.repeat(np.repeat(c,z,axis=0),z,axis=1); save(c,p); print("saved",p,c.shape)
ref=load('G:/DSHProject/BlenderMcp/reference/style_v13_ref.png')
crop(ref,(865,600,1015,765),6,f'{OUT}/ref_claw_p1b.png')
crop(ref,(760,600,900,770),6,f'{OUT}/ref_claw_p1c.png')
