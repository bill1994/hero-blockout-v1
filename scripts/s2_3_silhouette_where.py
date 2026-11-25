"""Where do the extra / missing silhouette pixels sit? Prints the bounding box
and the worst rows and columns of the ours-only and reference-only regions, so
an IoU number points at a part instead of a number.

  blender -b --factory-startup --python scripts/s2_3_silhouette_where.py -- ab_s2d front
"""

import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = 6.0 / 255.0


def mask(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = list(img.pixels)
    bpy.data.images.remove(img)
    bg = (px[0], px[1], px[2])
    m = bytearray(w * h)
    for i in range(w * h):
        j = i * 4
        if (abs(px[j] - bg[0]) > TOL or abs(px[j + 1] - bg[1]) > TOL
                or abs(px[j + 2] - bg[2]) > TOL):
            m[i] = 1
    return w, h, m


def bbox(w, h, m):
    xs, ys, n = [], [], 0
    for y in range(h):
        row = y * w
        for x in range(w):
            if m[row + x]:
                xs.append(x)
                ys.append(y)
                n += 1
    if not n:
        return None
    return dict(n=n, x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys))


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = argv[0] if argv else "ab_s2d"
view = argv[1] if len(argv) > 1 else "front"
pa = os.path.join(ROOT, "renders", out_dir, "view_%s.png" % view)
pb = os.path.join(ROOT, "reference", "views_20261124", "ref_%s.png" % view)
wa, ha, ma = mask(pa)
wb, hb, mb = mask(pb)

only_a = bytearray(wa * ha)
only_b = bytearray(wa * ha)
for i in range(wa * ha):
    if ma[i] and not mb[i]:
        only_a[i] = 1
    elif mb[i] and not ma[i]:
        only_b[i] = 1

print("@@WHERE@@ %s ours-only %s" % (view, bbox(wa, ha, only_a)))
print("@@WHERE@@ %s ref-only  %s" % (view, bbox(wa, ha, only_b)))
cols = sorted(((sum(only_a[y * wa + x] for y in range(ha)), x) for x in range(wa)), reverse=True)[:6]
rows = sorted(((sum(only_a[y * wa + x] for x in range(wa)), y) for y in range(ha)), reverse=True)[:6]
print("@@WHERE@@ worst cols (count, x): %s" % cols)
print("@@WHERE@@ worst rows (count, y_from_bottom): %s" % rows)
