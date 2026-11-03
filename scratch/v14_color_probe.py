"""Probe colour clusters in reference crops and P6 renders so we can
build a defensible cream/orange/background classifier."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"G:\DSHProject\hero-blockout\hero-blockout-v1")
IMAGES = {
    "ref_front": ROOT / "review/v14/ref_outlet_front.png",
    "ref_top": ROOT / "review/v14/ref_outlet_top.png",
    "ref_34": ROOT / "review/v14/ref_outlet_34.png",
    "p6_front": ROOT / "review/v14/p6_outlet_front.png",
    "p6_top": ROOT / "review/v14/p6_outlet_top.png",
    "p6_34": ROOT / "review/v14/p6_outlet_34.png",
}


def kmeans_simple(data, k, iters=40, seed=0):
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(data), size=k, replace=False)
    cent = data[idx].astype(np.float64)
    for _ in range(iters):
        d = ((data[:, None, :] - cent[None, :, :]) ** 2).sum(axis=2)
        lab = d.argmin(axis=1)
        for j in range(k):
            m = lab == j
            if m.any():
                cent[j] = data[m].mean(axis=0)
    d = ((data[:, None, :] - cent[None, :, :]) ** 2).sum(axis=2)
    lab = d.argmin(axis=1)
    counts = np.bincount(lab, minlength=k)
    return cent, counts, lab


def rgb_to_hsv_arr(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    diff = mx - mn
    sat = np.where(mx > 1e-6, diff / np.maximum(mx, 1e-6), 0.0)
    return mx, sat


out = {}
for name, path in IMAGES.items():
    if not path.exists():
        out[name] = {"error": "missing", "path": str(path)}
        continue
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im).astype(np.float64) / 255.0
    h, w = arr.shape[:2]
    flat = arr.reshape(-1, 3)
    # subsample for speed
    step = max(1, len(flat) // 60000)
    sample = flat[::step]
    cent, counts, _ = kmeans_simple(sample, 6, seed=1)
    order = np.argsort(-counts)
    clusters = []
    for j in order:
        c = cent[j]
        mx, sat = rgb_to_hsv_arr(c[None, :])
        clusters.append({
            "rgb": [round(float(v), 3) for v in c],
            "hex": "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in c),
            "share": round(float(counts[j] / counts.sum()), 4),
            "sat": round(float(sat[0]), 4),
            "val": round(float(mx[0]), 4),
        })
    out[name] = {"size": [w, h], "clusters": clusters}

print(json.dumps(out, indent=2, ensure_ascii=False))
