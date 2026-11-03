"""Final reference measurements: screws on front panel, base band, spout extent, claw crop."""
import bpy, numpy as np, json, os
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
crop(ref,(55,520,215,650),6,f'{OUT}/ref_claw_p0b.png')

def tosrgb(c):
    return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.clip(c,0,None),1/2.4)-0.055)
s=tosrgb(np.clip(ref[...,:3],0,1))
mx=s.max(axis=2); mn=s.min(axis=2)
sat=np.where(mx>1e-6,(mx-mn)/np.maximum(mx,1e-6),0)
R,G,B=s[...,0],s[...,1],s[...,2]
cream=(mx>0.60)&(sat<0.32)
orange=(R>0.35)&(R>B*1.7)&(R>G*1.7)&(sat>0.45)
dark=(mx<0.45)&(sat<0.32)

O={}

# ---- P0 front panel silhouette (machine body only, exclude spout & arm) ----
# body vertical extent: look at column x=300 (window centre) for cream
def rowspan(m,x,y0,y1,x0=0):
    col=m[y0:y1,x]; ys=np.nonzero(col)[0]
    return (int(ys.min()+y0),int(ys.max()+y0),int(len(ys))) if len(ys) else None
O['P0_cream_col_x300']=rowspan(cream,300,340,900)
O['P0_cream_col_x200']=rowspan(cream,200,340,900)
O['P0_dark_col_x300']=rowspan(dark,300,700,900)
O['P0_dark_col_x200']=rowspan(dark,200,700,900)

# horizontal extent of the dark plinth band (exclude shadow: use rows 780-820)
for y in (782,790,798,806,814,822,830,838):
    row=dark[y,150:520]; xs=np.nonzero(row)[0]
    O[f'P0_plinth_y{y}']=(int(xs.min()+150),int(xs.max()+150),int(len(xs))) if len(xs) else None

# ---- P2 top view: body + spout extent ----
def rowspan2(m,x,y0,y1):
    col=m[y0:y1,x]; ys=np.nonzero(col)[0]
    return (int(ys.min()+y0),int(ys.max()+y0),int(len(ys))) if len(ys) else None
O['P2_cream_col_x1400']=rowspan2(cream,1400,380,900)
O['P2_cream_col_x1700']=rowspan2(cream,1700,380,900)
O['P2_orange_col_x1780']=rowspan2(orange,1780,380,900)
O['P2_orange_col_x1820']=rowspan2(orange,1820,380,900)
# P2 body right edge / spout: for each row, orange x range
O['P2_rows']={}
for y in range(500,660,10):
    row=orange[y,1268:1860]; xs=np.nonzero(row)[0]
    if len(xs): O['P2_rows'][str(y)]=(int(xs.min()+1268),int(xs.max()+1268))
# P2 cream right edge (outer shell of spout)
O['P2_cream_edge']={}
for y in range(500,660,10):
    row=cream[y,1268:1860]; xs=np.nonzero(row)[0]
    if len(xs): O['P2_cream_edge'][str(y)]=(int(xs.min()+1268),int(xs.max()+1268))

# ---- P0 spout: orange vertical leg + horizontal run ----
O['P0_orange_cols']={}
for x in range(400,690,10):
    col=orange[400:760,x]; ys=np.nonzero(col)[0]
    if len(ys): O['P0_orange_cols'][str(x)]=(int(ys.min()+400),int(ys.max()+400),int(len(ys)))
O['P0_orange_bbox']=None
ys,xs=np.nonzero(orange[400:760,390:690])
if len(xs):
    O['P0_orange_bbox']=(int(xs.min()+390),int(xs.max()+390),int(ys.min()+400),int(ys.max()+400))
# cream shell around P0 spout
O['P0_spool_cream_bbox']=None
ys,xs=np.nonzero(cream[400:760,390:690])
if len(xs):
    O['P0_spool_cream_bbox']=(int(xs.min()+390),int(xs.max()+390),int(ys.min()+400),int(ys.max()+400))

# ---- P0 claw: orange finger structure ----
O['P0_claw_orange_cols']={}
for x in range(60,230,8):
    col=orange[500:660,x]; ys=np.nonzero(col)[0]
    if len(ys): O['P0_claw_orange_cols'][str(x)]=(int(ys.min()+500),int(ys.max()+500),int(len(ys)))
O['P0_claw_orange_bbox']=None
ys,xs=np.nonzero(orange[490:670,50:240])
if len(xs):
    O['P0_claw_orange_bbox']=(int(xs.min()+50),int(xs.max()+50),int(ys.min()+490),int(ys.max()+490))

print("###JSON_START###")
print(json.dumps(O,indent=1,default=str))
print("###JSON_END###")
