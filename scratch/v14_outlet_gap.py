"""Measure outlet geometry: reference crops (heuristic masks) vs P6 flat masks (exact).

Outputs JSON metrics + debug PNGs so every number can be eyeballed.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"G:\DSHProject\hero-blockout\hero-blockout-v1")
OUT = ROOT / "validation" / "v14_gap"
OUT.mkdir(parents=True, exist_ok=True)


def to_hsv(arr):
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mx = arr.max(axis=-1)
    mn = arr.min(axis=-1)
    d = mx - mn
    sat = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    # hue in turns
    hue = np.zeros_like(mx)
    nz = d > 1e-6
    idx = nz & (mx == r)
    hue[idx] = ((g[idx] - b[idx]) / d[idx]) % 6
    idx = nz & (mx == g)
    hue[idx] = (b[idx] - r[idx]) / d[idx] + 2
    idx = nz & (mx == b)
    hue[idx] = (r[idx] - g[idx]) / d[idx] + 4
    hue = hue / 6.0
    return hue, sat, mx


def bbox(mask):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def wh(b):
    return None if b is None else [b[2] - b[0] + 1, b[3] - b[1] + 1]


def frame_thickness(obj_mask, hole_mask, b):
    """Thickness of obj border around hole, measured on 4 sides, in px."""
    x0, y0, x1, y1 = b
    hb = bbox(hole_mask)
    if hb is None:
        return None
    left = hb[0] - x0
    right = x1 - hb[2]
    top = hb[1] - y0
    bottom = y1 - hb[3]
    return {"left": int(left), "right": int(right), "top": int(top), "bottom": int(bottom)}


def ref_masks(path):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im).astype(np.float64) / 255.0
    hue, sat, val = to_hsv(arr)
    orange = (sat > 0.32) & (hue > 0.02) & (hue < 0.13) & (val > 0.25)
    # object = anything warm/coloured enough to not be the flat studio backdrop
    obj = sat > 0.065
    obj = obj | orange
    cream = obj & ~orange
    return arr, {"orange": orange, "cream": cream, "obj": obj}


def model_masks(path):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im).astype(np.float64) / 255.0
    # exact: cream (1,.92,.72) ; orange (1,.30,0)
    cream = (arr[..., 0] > 0.5) & (arr[..., 2] > 0.4) & (arr[..., 2] < 0.9)
    orange = (arr[..., 0] > 0.5) & (arr[..., 2] < 0.25) & (arr[..., 1] > 0.1) & (arr[..., 1] < 0.5)
    return arr, {"orange": orange, "cream": cream, "obj": cream | orange}


def debug_png(arr, masks, path, scale=1.0):
    h, w = masks["obj"].shape
    panel = np.zeros((h, w, 3), dtype=np.float64)
    panel[masks["cream"]] = (1.0, 0.92, 0.72)
    panel[masks["orange"]] = (1.0, 0.30, 0.0)
    combo = np.concatenate([arr, panel], axis=1)
    img = Image.fromarray((np.clip(combo, 0, 1) * 255).astype(np.uint8))
    if scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.NEAREST)
    img.save(path)


def analyse(name, path, kind):
    arr, m = ref_masks(path) if kind == "ref" else model_masks(path)
    ob = bbox(m["obj"])
    rb = bbox(m["orange"])
    res = {
        "source": str(path.name),
        "kind": kind,
        "size": [int(m["obj"].shape[1]), int(m["obj"].shape[0])],
        "obj_bbox": ob,
        "obj_wh": wh(ob),
        "orange_bbox": rb,
        "orange_wh": wh(rb),
        "orange_px": int(m["orange"].sum()),
        "cream_px": int(m["cream"].sum()),
    }
    tot = res["orange_px"] + res["cream_px"]
    res["orange_share_of_outlet"] = round(res["orange_px"] / tot, 4) if tot else None
    if ob and rb:
        res["frame_px"] = frame_thickness(m["obj"], m["orange"], ob)
        ow = res["obj_wh"][0]
        res["frame_ratio_of_width"] = {
            k: round(v / ow, 4) for k, v in res["frame_px"].items()
        }
    # column profile of orange: reveals a vertical leg / open side
    if rb:
        prof = []
        x0, y0, x1, y1 = rb
        for x in range(x0, x1 + 1, max(1, (x1 - x0) // 12)):
            col = m["orange"][:, x]
            ys = np.nonzero(col)[0]
            prof.append({"x": int(x), "top": int(ys.min()), "bot": int(ys.max()), "h": int(ys.max() - ys.min() + 1)})
        res["orange_column_profile"] = prof
    debug_png(arr, m, OUT / f"mask_{name}.png")
    return res


CASES = [
    ("ref_front", ROOT / "review/v14/ref_outlet_front.png", "ref"),
    ("ref_top", ROOT / "review/v14/ref_outlet_top.png", "ref"),
    ("ref_34", ROOT / "review/v14/ref_outlet_34.png", "ref"),
    ("p6_side", OUT / "flat_side.png", "model"),
    ("p6_top", OUT / "flat_top.png", "model"),
    ("p6_front", OUT / "flat_front.png", "model"),
]

report = [analyse(n, p, k) for n, p, k in CASES]
(OUT / "mask_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
