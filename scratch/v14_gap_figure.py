"""Clean 2x2 comparison figure: reference vs P6, cropped past the machine body."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"G:\DSHProject\hero-blockout\hero-blockout-v1")
OUT = ROOT / "validation" / "v14_gap"
W = 640


def hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    sat = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    hue = np.zeros_like(mx); nz = d > 1e-6
    i = nz & (mx == a[..., 0]); hue[i] = ((a[..., 1][i] - a[..., 2][i]) / d[i]) % 6
    i = nz & (mx == a[..., 1]); hue[i] = (a[..., 2][i] - a[..., 0][i]) / d[i] + 2
    i = nz & (mx == a[..., 2]); hue[i] = (a[..., 0][i] - a[..., 1][i]) / d[i] + 4
    return hue / 6.0, sat, mx


def masks(a, kind):
    if kind == "ref":
        hue, sat, val = hsv(a)
        orange = (sat > 0.32) & (hue > 0.02) & (hue < 0.13) & (val > 0.25)
        obj = sat > 0.065
    else:
        orange = (a[..., 0] > 0.8) & (a[..., 1] > 0.30) & (a[..., 1] < 0.80) & (a[..., 2] < 0.30)
        obj = (a[..., 0] > 0.8) & (((a[..., 1] > 0.85) & (a[..., 2] > 0.70)) | orange)
    return orange, obj & ~orange


def panel(path, kind, cut_from_orange):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255.0
    orange, cream = masks(a, kind)
    ys, xs = np.nonzero(orange)
    x0 = xs.min() if cut_from_orange else np.nonzero(cream)[1].min()
    ys2, xs2 = np.nonzero(cream | orange)
    crop_x0 = min(x0, xs2.min()) if cut_from_orange else xs2.min()
    crop = a[ys2.min():ys2.max() + 1, crop_x0:xs2.max() + 1]
    o = orange[ys2.min():ys2.max() + 1, crop_x0:xs2.max() + 1]
    c = cream[ys2.min():ys2.max() + 1, crop_x0:xs2.max() + 1]
    vis = np.zeros((*crop.shape[:2], 3))
    vis[c] = (0.98, 0.93, 0.80)
    vis[o] = (0.90, 0.42, 0.05)
    img = Image.fromarray((vis * 255).astype(np.uint8))
    return img.resize((W, max(1, int(img.height * W / img.width))), Image.LANCZOS)


panels = [
    ("REFERENCE  side", panel(ROOT / "review/v14/ref_outlet_front.png", "ref", True)),
    ("P6  side", panel(OUT / "flat_side.png", "model", False)),
    ("REFERENCE  top", panel(ROOT / "review/v14/ref_outlet_top.png", "ref", True)),
    ("P6  top", panel(OUT / "flat_top.png", "model", False)),
]

pad, head = 8, 26
rows = [panels[0:2], panels[2:4]]
row_h = [max(p.height for _, p in r) + head for r in rows]
sheet = Image.new("RGB", (W * 2 + pad * 3, sum(row_h) + pad * 3), (250, 250, 250))
dr = ImageDraw.Draw(sheet)
y = pad
for r, hh in zip(rows, row_h):
    x = pad
    for label, img in r:
        dr.text((x + 4, y + 6), label, fill=(20, 20, 20))
        sheet.paste(img, (x, y + head))
        x += W + pad
    y += hh + pad
sheet.save(OUT / "gap_compare_2x2.png")
print("saved", OUT / "gap_compare_2x2.png", sheet.size)
