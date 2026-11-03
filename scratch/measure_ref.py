"""Quantitative pixel measurement of the reference image for the four focus areas."""
import bpy, numpy as np, json

def load(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w*h*img.channels, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, img.channels)[::-1]
    bpy.data.images.remove(img)
    return px

ref = load('G:/DSHProject/BlenderMcp/reference/style_v13_ref.png')
H, W = ref.shape[:2]
rgb = ref[..., :3]
# sRGB-ish classification on display values (pixels are linear; convert)
def tosrgb(c):
    return np.where(c <= 0.0031308, c*12.92, 1.055*np.power(np.clip(c,0,None), 1/2.4)-0.055)
s = tosrgb(np.clip(rgb, 0, 1))
R, G, B = s[...,0], s[...,1], s[...,2]
mx = s.max(axis=2); mn = s.min(axis=2)
sat = np.where(mx > 1e-6, (mx-mn)/np.maximum(mx,1e-6), 0)

cream = (mx > 0.62) & (sat < 0.30)
orange = (R > 0.35) & (R > B*1.7) & (R > G*1.7) & (sat > 0.45)
dark   = (mx < 0.42)
mint   = (G > R*1.02) & (G > B*1.02) & (sat > 0.06) & (mx > 0.45)

out = {}

PANELS = {'P0': (85, 682), 'P1': (776, 1198), 'P2': (1268, 1852)}

def bbox(m, x0, x1, y0, y1):
    sub = m[y0:y1, x0:x1]
    ys, xs = np.nonzero(sub)
    if len(xs) == 0: return None
    return dict(x0=int(xs.min()+x0), x1=int(xs.max()+x0),
                y0=int(ys.min()+y0), y1=int(ys.max()+y0),
                w=int(xs.max()-xs.min()+1), h=int(ys.max()-ys.min()+1),
                n=int(sub.sum()))

# ---------- 1. BASE (P0 front view) ----------
out['BASE_P0'] = {}
out['BASE_P0']['dark_bbox'] = bbox(dark, 85, 682, 600, 900)
out['BASE_P0']['body_bbox'] = bbox(cream, 85, 682, 300, 700)
# the plinth = dark region under the body in P0
# scan rows: find dark run widths
prof = []
for y in range(700, 900, 6):
    row = dark[y, 85:682]
    xs = np.nonzero(row)[0]
    if len(xs): prof.append((y, int(xs.min()+85), int(xs.max()+85), int(len(xs))))
out['BASE_P0']['dark_rows'] = prof

# ---------- 2. SCREWS ----------
# screws appear as small dark rings on the cream body. Find small dark blobs
# inside the body region, excluding the window.
def small_dark_blobs(mask, x0, x1, y0, y1, maxsize=22):
    sub = mask[y0:y1, x0:x1].astype(np.uint8)
    H2, W2 = sub.shape
    lab = np.zeros((H2, W2), np.int32); cur = 0; out_ = []
    for i in range(H2):
        for j in range(W2):
            if sub[i,j] and lab[i,j]==0:
                cur += 1; stack=[(i,j)]; lab[i,j]=cur; pts=[]
                while stack:
                    a,b = stack.pop(); pts.append((a,b))
                    for da,db in ((1,0),(-1,0),(0,1),(0,-1)):
                        na,nb = a+da, b+db
                        if 0<=na<H2 and 0<=nb<W2 and sub[na,nb] and lab[na,nb]==0:
                            lab[na,nb]=cur; stack.append((na,nb))
                ys=[p[0] for p in pts]; xs=[p[1] for p in pts]
                w=max(xs)-min(xs)+1; h=max(ys)-min(ys)+1
                if 3<=w<=maxsize and 3<=h<=maxsize and len(pts)>=8:
                    out_.append(dict(cx=int(min(xs)+x0+ (max(xs)-min(xs))//2),
                                     cy=int(min(ys)+y0+ (max(ys)-min(ys))//2),
                                     w=w, h=h, n=len(pts)))
    return out_

# P0 front: cream body region excluding window. Window approx x 200-380, y 500-780 per contract
out['SCREWS_P0'] = small_dark_blobs(dark, 95, 682, 380, 800, maxsize=20)
# P2 top view
out['SCREWS_P2'] = small_dark_blobs(dark, 1268, 1852, 400, 860, maxsize=20)

# ---------- 3. CLAW (P0 left side) ----------
out['CLAW_P0'] = {}
out['CLAW_P0']['orange_bbox'] = bbox(orange, 60, 260, 480, 700)
out['CLAW_P0']['cream_bbox'] = bbox(cream, 60, 260, 480, 700)
# finger structure: horizontal runs of orange in the claw band
for y in range(540, 660, 8):
    row = orange[y, 60:260]
    xs = np.nonzero(row)[0]
    if len(xs):
        # find runs
        runs=[]; st=xs[0]; prev=xs[0]
        for v in xs[1:]:
            if v>prev+2: runs.append((int(st+60), int(prev+60))); st=v
            prev=v
        runs.append((int(st+60), int(prev+60)))
        out['CLAW_P0'][f'y{y}'] = runs

# ---------- 4. OUTLET ----------
out['OUTLET'] = {}
# P0 front: orange = the spout on the right side of the machine
out['OUTLET']['P0_orange_bbox'] = bbox(orange, 380, 682, 400, 720)
# row scans through P0 spout
for y in (480, 520, 560, 600, 640):
    row = orange[y, 380:682]
    xs = np.nonzero(row)[0]
    if len(xs):
        runs=[]; st=xs[0]; prev=xs[0]
        for v in xs[1:]:
            if v>prev+2: runs.append((int(st+380), int(prev+380))); st=v
            prev=v
        runs.append((int(st+380), int(prev+380)))
        out['OUTLET'][f'P0_y{y}'] = runs
# column scans of P0 spout (vertical profile at the mouth)
for x in (420, 460, 500, 540, 580, 620, 650):
    col = orange[400:720, x]
    ys = np.nonzero(col)[0]
    if len(ys):
        out['OUTLET'][f'P0_x{x}'] = [int(ys.min()+400), int(ys.max()+400), int(len(ys))]

# P2 top view outlet
out['OUTLET']['P2_orange_bbox'] = bbox(orange, 1268, 1852, 400, 860)
for y in (520, 540, 560, 580, 600, 620):
    row = orange[y, 1268:1852]
    xs = np.nonzero(row)[0]
    if len(xs):
        runs=[]; st=xs[0]; prev=xs[0]
        for v in xs[1:]:
            if v>prev+2: runs.append((int(st+1268), int(prev+1268))); st=v
            prev=v
        runs.append((int(st+1268), int(prev+1268)))
        out['OUTLET'][f'P2_y{y}'] = runs

# body silhouette in P0 for proportion reference
out['P0_body_px'] = bbox(cream, 85, 682, 350, 820)

print("###JSON_START###")
print(json.dumps(out, indent=1, default=str))
print("###JSON_END###")
