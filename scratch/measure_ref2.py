"""Refined reference measurement: recessed screw dimples, base profile, claw fingers."""
import bpy, numpy as np, json

def load(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w*h*img.channels, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, img.channels)[::-1]
    bpy.data.images.remove(img)
    return px

def tosrgb(c):
    return np.where(c <= 0.0031308, c*12.92, 1.055*np.power(np.clip(c,0,None), 1/2.4)-0.055)

ref = load('G:/DSHProject/BlenderMcp/reference/style_v13_ref.png')
s = tosrgb(np.clip(ref[..., :3], 0, 1))
R,G,B = s[...,0], s[...,1], s[...,2]
lum = 0.299*R + 0.587*G + 0.114*B
sat = np.where(s.max(axis=2)>1e-6, (s.max(axis=2)-s.min(axis=2))/np.maximum(s.max(axis=2),1e-6), 0)
out = {}

# ---- RECESSED SCREW DIMPLES: locally darker than surrounding cream ----
# search the cream body of P0 and P2 for small round depressions
def find_dimples(x0,x1,y0,y1, thr=0.055, r=9):
    """local minima of luminance on cream, circular"""
    reg = lum[y0:y1, x0:x1]
    hits = []
    # box blur
    from numpy.lib.stride_tricks import sliding_window_view
    k = r
    pad = np.pad(reg, k, mode='edge')
    win = sliding_window_view(pad, (2*k+1, 2*k+1))
    blur = win.mean(axis=(2,3))
    diff = blur - reg                      # >0 means this pixel is darker than surroundings
    ys, xs = np.nonzero(diff > thr)
    # cluster
    used = set(); clusters = []
    for i,j in zip(ys,xs):
        if (i,j) in used: continue
        stack=[(i,j)]; used.add((i,j)); pts=[]
        while stack:
            a,b = stack.pop(); pts.append((a,b))
            for da in range(-2,3):
                for db in range(-2,3):
                    na,nb = a+da, b+db
                    if (na,nb) in used: continue
                    if 0<=na<diff.shape[0] and 0<=nb<diff.shape[1] and diff[na,nb]>thr*0.6:
                        used.add((na,nb)); stack.append((na,nb))
        if len(pts)>=6:
            ays=[p[0] for p in pts]; axs=[p[1] for p in pts]
            w_=max(axs)-min(axs)+1; h_=max(ays)-min(ays)+1
            if 5<=w_<=20 and 5<=h_<=20:
                hits.append(dict(cx=int(min(axs)+x0+(max(axs)-min(axs))//2),
                                 cy=int(min(ays)+y0+(max(ays)-min(ays))//2),
                                 w=int(w_), h=int(h_),
                                 depth=round(float(diff[min(ays),min(axs)]),4),
                                 n=len(pts)))
    return hits

# P0 front view body region (exclude window core x 205..375, y 505..770)
out['P0_dimples_all'] = find_dimples(95, 682, 380, 800, thr=0.05, r=9)
# P2 top view
out['P2_dimples_all'] = find_dimples(1270, 1852, 400, 860, thr=0.05, r=9)

# ---- BASE profile in P0: cream body bottom edge and the dark plinth ----
# Find, for each column in P0, the lowest cream pixel (body bottom) and the dark band below it
rows = []
for x in range(100, 400, 20):
    col_cream = np.nonzero((lum[y0:y1, x] > 0.6) & (sat[y0:y1, x] < 0.30))[0] if (y0:=0) is None else None
# simpler: for P0 columns, find runs of 'dark charcoal' (low sat, low-ish lum) in y 700..870
darkband = (lum < 0.5) & (sat < 0.30)
prof = []
for x in range(110, 400, 15):
    col = np.nonzero(darkband[740:880, x])[0]
    if len(col):
        prof.append((x, int(col.min()+740), int(col.max()+740), int(len(col))))
out['P0_base_dark_profile'] = prof

# reference cream body bottom edge: lowest cream in each column
prof2 = []
for x in range(110, 400, 15):
    col = np.nonzero((lum[700:880, x] > 0.62) & (sat[700:880, x] < 0.25))[0]
    if len(col):
        prof2.append((x, int(col.min()+700), int(col.max()+700)))
out['P0_body_bottom_edge'] = prof2

# ---- CLAW in P0: orange blob structure ----
orange = (R > 0.35) & (R > B*1.7) & (R > G*1.7) & (sat > 0.45)
out['CLAW'] = {}
ys,xs = np.nonzero(orange[440:700, 60:280])
if len(xs):
    out['CLAW']['bbox'] = dict(x0=int(xs.min()+60), x1=int(xs.max()+60),
                               y0=int(ys.min()+440), y1=int(ys.max()+440),
                               w=int(xs.max()-xs.min()+1), h=int(ys.max()-ys.min()+1))
# horizontal runs of orange across the claw -> count finger lobes
for y in range(520, 660, 6):
    row = orange[y, 60:280]
    xs2 = np.nonzero(row)[0]
    if len(xs2)==0: continue
    runs=[]; st=xs2[0]; prev=xs2[0]
    for v in xs2[1:]:
        if v>prev+1: runs.append((int(st+60), int(prev+60))); st=v
        prev=v
    runs.append((int(st+60), int(prev+60)))
    out['CLAW'][f'y{y}'] = runs

# ---- OUTLET P0: orange region on the right, and the cream "spoon" ----
out['OUTLET_P0'] = {}
for y in range(470, 680, 10):
    row = orange[y, 400:682]
    xs3 = np.nonzero(row)[0]
    if len(xs3)==0: continue
    runs=[]; st=xs3[0]; prev=xs3[0]
    for v in xs3[1:]:
        if v>prev+1: runs.append((int(st+400), int(prev+400))); st=v
        prev=v
    runs.append((int(st+400), int(prev+400)))
    out['OUTLET_P0'][f'y{y}'] = runs
# vertical extent of the P0 orange at each x
for x in (420,450,480,510,540,570,600,630,660):
    col = np.nonzero(orange[440:700, x])[0]
    if len(col):
        out['OUTLET_P0'][f'x{x}'] = [int(col.min()+440), int(col.max()+440)]

# ---- OUTLET P2 (top): orange mouth ----
out['OUTLET_P2'] = {}
ys,xs = np.nonzero(orange[400:860, 1268:1852])
if len(xs):
    out['OUTLET_P2']['bbox'] = dict(x0=int(xs.min()+1268), x1=int(xs.max()+1268),
                                    y0=int(ys.min()+400), y1=int(ys.max()+400))
for y in (520,550,580,610):
    row = orange[y, 1268:1852]
    xs4 = np.nonzero(row)[0]
    if len(xs4):
        runs=[]; st=xs4[0]; prev=xs4[0]
        for v in xs4[1:]:
            if v>prev+1: runs.append((int(st+1268), int(prev+1268))); st=v
            prev=v
        runs.append((int(st+1268), int(prev+1268)))
        out['OUTLET_P2'][f'y{y}'] = runs

print("###JSON_START###")
print(json.dumps(out, indent=1, default=str))
print("###JSON_END###")
