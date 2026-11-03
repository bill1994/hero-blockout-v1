"""Crop + upscale regions from reference and current renders using Blender's numpy."""
import bpy, numpy as np, os

OUT = 'G:/DSHProject/BlenderMcp/scratch/crops'
os.makedirs(OUT, exist_ok=True)

def load(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w*h*img.channels, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, img.channels)[::-1]   # top-down
    bpy.data.images.remove(img)
    return px

def save(arr, path):
    h, w, c = arr.shape
    if c == 3:
        arr = np.dstack([arr, np.ones((h,w,1), np.float32)])
    img = bpy.data.images.new(os.path.basename(path), width=w, height=h, alpha=True)
    img.pixels.foreach_set(arr[::-1].ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)

def crop(px, rect, zoom, path, gain=1.0):
    x0,y0,x1,y1 = rect
    c = px[y0:y1, x0:x1]
    c = np.repeat(np.repeat(c, zoom, axis=0), zoom, axis=1)
    if gain != 1.0:
        rgb = np.clip(c[...,:3]*gain, 0, 1)
        c = np.dstack([rgb, c[...,3:4]]) if c.shape[2]==4 else rgb
    save(c, path)
    print("saved", path, c.shape)

REF = 'G:/DSHProject/BlenderMcp/reference/style_v13_ref.png'
HERO = 'G:/DSHProject/BlenderMcp/review/v14/p19/p19_empty_hero_f200.png'
TOP  = 'G:/DSHProject/BlenderMcp/review/v14/p19/p19_empty_top_f200.png'
SIDE = 'G:/DSHProject/BlenderMcp/review/v14/p19/p19_empty_side_f200.png'

r = load(REF)
print("REF size", r.shape)
crop(r, (150, 700, 520, 820), 3, f'{OUT}/ref_base.png')
crop(r, (170, 380, 500, 470), 3, f'{OUT}/ref_top_screws.png')
crop(r, (110, 520, 250, 680), 4, f'{OUT}/ref_claw.png')
crop(r, (500, 460, 690, 620), 4, f'{OUT}/ref_outlet_front.png')
crop(r, (1680, 440, 1860, 620), 4, f'{OUT}/ref_outlet_top.png')

for path, tag in ((HERO,'hero'), (TOP,'top'), (SIDE,'side')):
    try:
        p = load(path)
        print(tag, p.shape)
        if tag=='hero':
            crop(p, (300, 540, 660, 700), 3, f'{OUT}/cur_base.png')
            crop(p, (120, 440, 260, 560), 4, f'{OUT}/cur_claw.png')
            crop(p, (520, 400, 860, 600), 3, f'{OUT}/cur_outlet.png')
        elif tag=='top':
            crop(p, (380, 380, 780, 700), 3, f'{OUT}/cur_outlet_top.png')
            crop(p, (300, 500, 800, 900), 2, f'{OUT}/cur_base_top.png')
        else:
            crop(p, (380, 380, 900, 700), 3, f'{OUT}/cur_outlet_side.png')
    except Exception as e:
        print("ERR", tag, e)
print("DONE")
