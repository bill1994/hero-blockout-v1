"""Reference front-view pixel measurement with a threshold that drops the backdrop."""
import bpy
import os
import numpy as np

ROOT = r"G:\DSHProject\BlenderMcp"


def load(p):
    img = bpy.data.images.load(p)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(img)
    a = np.clip(a, 0.0, None)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055)


for fn in ("tripo_f001_front.png", "v2_f001_front.png"):
    a = load(os.path.join(ROOT, "renders", fn))
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    m = lum > 0.42
    ys, xs = np.where(m)
    print("### %s  bbox x %d..%d y %d..%d" % (fn, xs.min(), xs.max(), ys.min(), ys.max()))
    for row in (400, 450, 500, 550, 600, 640, 680, 700, 720, 740):
        xr = np.where(m[row])[0]
        if len(xr):
            # segment gaps
            d = np.diff(xr)
            gaps = np.where(d > 6)[0]
            starts = [0] + list(gaps + 1)
            ends = list(gaps) + [len(xr) - 1]
            segs = ["%d..%d" % (xr[s], xr[e]) for s, e in zip(starts, ends)]
            print("  row %3d  %s" % (row, " | ".join(segs)))
