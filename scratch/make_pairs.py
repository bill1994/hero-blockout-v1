"""Build ref|current side-by-side comparison plates for the four focus areas."""
import bpy, numpy as np, os
OUT='G:/DSHProject/BlenderMcp/review/v14/audit'
os.makedirs(OUT, exist_ok=True)
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

def fit(a, W, H):
    """cover-fit to WxH"""
    h,w = a.shape[:2]
    s = max(W/w, H/h)
    nh, nw = int(round(h*s)), int(round(w*s))
    yi = np.clip((np.arange(nh)/s).astype(int), 0, h-1)
    xi = np.clip((np.arange(nw)/s).astype(int), 0, w-1)
    r = a[yi][:, xi]
    y0 = (nh-H)//2; x0 = (nw-W)//2
    return r[y0:y0+H, x0:x0+W]

def bar(w,h,rgb=(0.10,0.11,0.12)):
    return np.dstack([np.ones((h,w,3),np.float32)*np.array(rgb,np.float32),
                      np.ones((h,w,1),np.float32)])

def label_bar(W, text, rgb=(0.10,0.11,0.12)):
    b = bar(W,34,rgb)
    return b

def pair(name, ref_path, cur_path, W=980, H=760, crop_ref=None, crop_cur=None,
         zoom_ref=1.0, zoom_cur=1.0):
    def prep(p, cz, z):
        a = load(p)
        if cz:
            x0,y0,x1,y1 = cz
            a = a[y0:y1, x0:x1]
        if z!=1.0:
            a = np.repeat(np.repeat(a, int(z), axis=0), int(z), axis=1)
        return a
    A = prep(ref_path, crop_ref, zoom_ref)
    B = prep(cur_path, crop_cur, zoom_cur)
    A = fit(A, W, H); B = fit(B, W, H)
    gap = 10
    canvas = bar(W*2+gap, H)
    canvas[:, :W] = A
    canvas[:, W+gap:] = B
    save(canvas, f'{OUT}/{name}.png')
    print('PAIR', name, canvas.shape)

REF='G:/DSHProject/BlenderMcp/reference/style_v13_ref.png'
C='G:/DSHProject/BlenderMcp/scratch/crops'
A='G:/DSHProject/BlenderMcp/review/v14/audit'

# 1 BASE
pair('cmp1_base', REF, f'{A}/det_base.png',
     crop_ref=(150,700,540,880), crop_cur=(0,0,1000,1000),
     W=940, H=560)
# 2 SCREWS
pair('cmp2_screws', REF, f'{A}/det_screw_up.png',
     crop_ref=(200,390,540,470), crop_cur=(0,0,1000,1000),
     W=940, H=420)
# 3 CLAW
pair('cmp3_claw', REF, f'{A}/det_claw_closed.png',
     crop_ref=(60,520,220,650), crop_cur=(0,0,1000,1000),
     W=940, H=520)
# 4 OUTLET  (reference top-view of spout vs current 3/4)
pair('cmp4_outlet', REF, f'{A}/det_outlet_3q.png',
     crop_ref=(1690,450,1860,640), crop_cur=(0,0,1100,1100),
     W=940, H=560)
# 4b OUTLET side
pair('cmp4b_outlet_side', REF, f'{A}/det_outlet_side.png',
     crop_ref=(500,450,690,620), crop_cur=(0,0,1100,1100),
     W=940, H=520)
# 5 full machine
pair('cmp5_full', REF, f'{A}/cur_front.png',
     crop_ref=(85,240,682,880), crop_cur=(0,0,1100,1100),
     W=940, H=940)
print("DONE")
