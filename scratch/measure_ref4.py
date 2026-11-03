"""Final: P0 body silhouette + screw positions; P1 spout orientation."""
import bpy, numpy as np, json, os
def load(p):
    img=bpy.data.images.load(p, check_existing=False); w,h=img.size
    px=np.empty(w*h*img.channels,dtype=np.float32); img.pixels.foreach_get(px)
    px=px.reshape(h,w,img.channels)[::-1]; bpy.data.images.remove(img); return px
def tosrgb(c):
    return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.clip(c,0,None),1/2.4)-0.055)
ref=load('G:/DSHProject/BlenderMcp/reference/style_v13_ref.png')
s=tosrgb(np.clip(ref[...,:3],0,1))
mx=s.max(axis=2); mn=s.min(axis=2)
sat=np.where(mx>1e-6,(mx-mn)/np.maximum(mx,1e-6),0)
R,G,B=s[...,0],s[...,1],s[...,2]
cream=(mx>0.58)&(sat<0.30)
orange=(R>0.30)&(R>B*1.6)&(R>G*1.6)&(sat>0.40)
O={}

# --- P0: vertical scan lines that avoid the window (window x 208..368) ---
# use x = 190 (left of window) and x = 400 (right of window, left of spout)
for x in (192, 200, 400, 410, 470):
    col=cream[300:900,x]; ys=np.nonzero(col)[0]
    O[f'cream_x{x}']=(int(ys.min()+300),int(ys.max()+300),int(len(ys))) if len(ys) else None
# dark plinth: scan x=200..470 at rows 780..860, find contiguous dark
dp=[]
for y in range(775,865,3):
    row=(mx[y,180:470]<0.52)&(sat[y,180:470]<0.30)
    xs=np.nonzero(row)[0]
    if len(xs): dp.append((y,int(xs.min()+180),int(xs.max()+180),int(len(xs))))
O['P0_plinth']=dp

# --- P1 spout: where is orange in panel 1 (776..1198)? ---
ys,xs=np.nonzero(orange[300:760,776:1198])
O['P1_orange_bbox']=(int(xs.min()+776),int(xs.max()+776),int(ys.min()+300),int(ys.max()+300)) if len(xs) else None
O['P1_orange_cols']={}
for x in range(1000,1200,8):
    col=orange[300:760,x]; yy=np.nonzero(col)[0]
    if len(yy): O['P1_orange_cols'][str(x)]=(int(yy.min()+300),int(yy.max()+300),int(len(yy)))
O['P1_orange_rows']={}
for y in range(300,760,8):
    row=orange[y,776:1198]; xx=np.nonzero(row)[0]
    if len(xx): O['P1_orange_rows'][str(y)]=(int(xx.min()+776),int(xx.max()+776),int(len(xx)))

# --- P2 spout (top view) ---
ys,xs=np.nonzero(orange[380:880,1268:1860])
O['P2_orange_bbox']=(int(xs.min()+1268),int(xs.max()+1268),int(ys.min()+380),int(ys.max()+380)) if len(xs) else None
# cream shell right of the orange in P2 (the spout's outer frame)
O['P2_shell_right']={}
for y in range(500,650,8):
    row=cream[y,1268:1860]; xx=np.nonzero(row)[0]
    if len(xx): O['P2_shell_right'][str(y)]=int(xx.max()+1268)
# body right edge in P2 (mint panel right edge is where orange begins)
O['P2_rows_orange']={}
for y in range(490,650,8):
    row=orange[y,1268:1860]; xx=np.nonzero(row)[0]
    if len(xx): O['P2_rows_orange'][str(y)]=(int(xx.min()+1268),int(xx.max()+1268))

print("###JSON_START###")
print(json.dumps(O,indent=1,default=str))
print("###JSON_END###")
