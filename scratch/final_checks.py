import bpy, numpy as np, json
def load(p):
    img=bpy.data.images.load(p, check_existing=False); w,h=img.size
    px=np.empty(w*h*img.channels,dtype=np.float32); img.pixels.foreach_get(px)
    px=px.reshape(h,w,img.channels)[::-1]; bpy.data.images.remove(img); return px
def tosrgb(c):
    return np.where(c<=0.0031308,c*12.92,1.055*np.power(np.clip(c,0,None),1/2.4)-0.055)
ref=load('G:/DSHProject/BlenderMcp/reference/style_v13_ref.png')
s=tosrgb(np.clip(ref[...,:3],0,1))
R={}
def samp(name,x0,y0,x1,y1):
    p=s[y0:y1,x0:x1].reshape(-1,3)
    med=np.median(p,axis=0)
    R[name]=dict(srgb=[round(float(v),3) for v in med],
                 linear=[round(float(v),4) for v in tosrgb(med)],
                 n=len(p))
# reference claw jaw (p1 panel, upper jaw) and the ball
samp('ref_claw_jaw',  880,615, 920,632)
samp('ref_claw_ball', 925,640, 955,672)
samp('ref_spout_orange',1745,545,1780,600)
samp('ref_body_cream',300,300,340,360)
samp('ref_plinth_dark',300,832,440,842)
samp('ref_mint_panel',1420,470,1500,520)
# current render equivalents
cur=load('G:/DSHProject/BlenderMcp/review/v14/audit/claw_only_closed.png')
cs=tosrgb(np.clip(cur[...,:3],0,1))
R['cur_claw_orange']=dict(srgb=[round(float(v),3) for v in np.median(cs[560:620,60:200].reshape(-1,3),axis=0)])
cur2=load('G:/DSHProject/BlenderMcp/review/v14/audit/cur_front.png')
c2=tosrgb(np.clip(cur2[...,:3],0,1))
R['cur_body_cream']=dict(srgb=[round(float(v),3) for v in np.median(c2[560:600,480:560].reshape(-1,3),axis=0)])
print("###JSON_START###"); print(json.dumps(R,indent=1,default=str)); print("###JSON_END###")
