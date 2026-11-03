"""Final outlet gap measurement: exact model masks + reference masks, plus a
normalised side-by-side montage."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(r"G:\DSHProject\hero-blockout\hero-blockout-v1")
OUT = ROOT / "validation" / "v14_gap"
UPX = 0.00128514  # world units per pixel of the 1400px ortho renders


def to_hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn
    sat = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    hue = np.zeros_like(mx); nz = d > 1e-6
    i = nz & (mx == a[..., 0]); hue[i] = ((a[..., 1][i] - a[..., 2][i]) / d[i]) % 6
    i = nz & (mx == a[..., 1]); hue[i] = (a[..., 2][i] - a[..., 0][i]) / d[i] + 2
    i = nz & (mx == a[..., 2]); hue[i] = (a[..., 0][i] - a[..., 1][i]) / d[i] + 4
    return hue / 6.0, sat, mx


def bbox(m):
    ys, xs = np.nonzero(m)
    return None if len(xs) == 0 else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def wh(b):
    return None if b is None else [b[2] - b[0] + 1, b[3] - b[1] + 1]


def ref_masks(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float64) / 255.0
    hue, sat, val = to_hsv(a)
    orange = (sat > 0.32) & (hue > 0.02) & (hue < 0.13) & (val > 0.25)
    obj = sat > 0.065
    return a, {"orange": orange, "cream": obj & ~orange, "obj": obj | orange}


def model_masks(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float64) / 255.0
    # rendered flat colours observed: orange (1,.583,0); cream (1,.958,.875)
    orange = (a[..., 0] > 0.8) & (a[..., 1] > 0.30) & (a[..., 1] < 0.80) & (a[..., 2] < 0.30)
    cream = (a[..., 0] > 0.8) & (a[..., 1] > 0.85) & (a[..., 2] > 0.70)
    return a, {"orange": orange, "cream": cream & ~orange, "obj": orange | cream}


def metrics(name, p, kind):
    a, m = ref_masks(p) if kind == "ref" else model_masks(p)
    ob, rb = bbox(m["obj"]), bbox(m["orange"])
    o_px, c_px = int(m["orange"].sum()), int(m["cream"].sum())
    tot = o_px + c_px
    d = {
        "view": name, "kind": kind,
        "obj_bbox": ob, "obj_wh": wh(ob),
        "orange_bbox": rb, "orange_wh": wh(rb),
        "orange_px": o_px, "cream_px": c_px,
        "orange_share": round(o_px / tot, 4) if tot else None,
    }
    if kind == "model":
        d["obj_world_wh"] = [round(v * UPX, 4) for v in wh(ob)]
        if rb:
            d["orange_world_wh"] = [round(v * UPX, 4) for v in wh(rb)]
    if ob and rb:
        d["far_end_margin_px"] = int(ob[2] - rb[2])
        d["far_end_margin_ratio"] = round((ob[2] - rb[2]) / wh(rb)[0], 4)
    # orange column profile (signature of the U / bowl / leg)
    if rb:
        x0, _, x1, _ = rb
        prof = []
        for x in range(x0, x1 + 1, max(1, (x1 - x0) // 11)):
            ys = np.nonzero(m["orange"][:, x])[0]
            prof.append(int(ys.max() - ys.min() + 1) if len(ys) else 0)
        d["orange_height_profile_px"] = prof
        d["profile_max_to_median"] = round(float(np.max(prof) / max(1, np.median([v for v in prof if v > 0] or [1]))), 3)
    return d, m, a


CASES = [
    ("ref_side", ROOT / "review/v14/ref_outlet_front.png", "ref"),
    ("p6_side", OUT / "flat_side.png", "model"),
    ("ref_top", ROOT / "review/v14/ref_outlet_top.png", "ref"),
    ("p6_top", OUT / "flat_top.png", "model"),
]

res, panels = [], []
for n, p, k in CASES:
    d, m, a = metrics(n, p, k)
    res.append(d)
    rb = bbox(m["orange"])
    ob = bbox(m["obj"])
    ref_x = rb[2] if rb else ob[2]
    # normalise by the outermost extent so both sides compare at one scale
    scale = 620.0 / max(1, (ref_x - ob[0]))
    vis = np.zeros((*m["obj"].shape, 3))
    vis[m["cream"]] = (0.98, 0.93, 0.80)
    vis[m["orange"]] = (0.90, 0.42, 0.05)
    vis[m["obj"] & ~m["cream"] & ~m["orange"]] = (0.3, 0.3, 0.3)
    crop = vis[ob[1]:ob[3] + 1, ob[0]:ref_x + 1]
    img = Image.fromarray((crop * 255).astype(np.uint8))
    img = img.resize((620, max(1, int(img.height * scale))), Image.LANCZOS)
    panels.append((n, img))

H = max(p.height for _, p in panels) + 34
Wd = 620
sheet = Image.new("RGB", (Wd, H * len(panels)), (255, 255, 255))
draw = ImageDraw.Draw(sheet)
for i, (n, img) in enumerate(panels):
    sheet.paste(img, (0, i * H + 30))
    draw.text((6, i * H + 8), n, fill=(0, 0, 0))
sheet.save(OUT / "gap_montage.png")

(OUT / "gap_metrics.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
print(json.dumps(res, indent=2))
