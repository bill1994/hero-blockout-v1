import bpy, numpy as np, os, json
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
# verify the 4 candidate screws on the front panel
for i,(cx,cy) in enumerate([(252,432),(492,432),(248,762),(496,763)]):
    crop(ref,(cx-28,cy-28,cx+28,cy+28),10,f'{OUT}/ref_screw_{i}.png')
# body silhouette of P0 front panel: cream, excluding the spout region x>470
def tosrgb(c):
    return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.clip(c,0,None),1/2.4)-0.055)
s=tosrgb(np.clip(ref[...,:3],0,1))
mx=s.max(axis=2); mn=s.min(axis=2)
sat=np.where(mx>1e-6,(mx-mn)/np.maximum(mx,1e-6),0)
cream=(mx>0.60)&(sat<0.32)
dark=(mx<0.45)
R={}
# body left/right per row (exclude spout by limiting x<480)
prof=[]
for y in range(380, 800, 10):
    row=cream[y,150:480]; xs=np.nonzero(row)[0]
    if len(xs): prof.append((y,int(xs.min()+150),int(xs.max()+150),int(len(xs))))
R['cream_prof']=prof
# dark band (plinth) rows
dp=[]
for y in range(780, 860, 4):
    row=dark[y,150:480]; xs=np.nonzero(row)[0]
    if len(xs): dp.append((y,int(xs.min()+150),int(xs.max()+150),int(len(xs))))
R['dark_prof']=dp
print(json.dumps(R,indent=1))
print("DONE")
