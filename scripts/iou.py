"""Silhouette IoU against the reference views.

The orthographic contract is shared (720 px, ortho_scale 1.15, centre
(-0.0005, 0, 0.377) -> 627 px/m), so the silhouette masks are directly
comparable. The mask is "everything that is not the background colour", taken
from the corner pixel, so no material knowledge is needed.

Run:
  blender --background --factory-startup --python scripts/iou.py -- \
      renders/ab_s2c s2c reference/views_20261124 ref
"""

import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = 6.0 / 255.0
VIEWS = ["front", "right", "top"]


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


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    dir_a, pre_a, dir_b, pre_b = argv[:4]
    dir_a = os.path.join(ROOT, dir_a)
    dir_b = os.path.join(ROOT, dir_b)
    for v in VIEWS:
        pa = os.path.join(dir_a, "%s_%s.png" % (pre_a, v))
        pb = os.path.join(dir_b, "%s_%s.png" % (pre_b, v))
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print("@@IOU@@ %-6s MISSING" % v)
            continue
        wa, ha, ma = mask(pa)
        wb, hb, mb = mask(pb)
        assert (wa, ha) == (wb, hb)
        inter = sum(1 for i in range(wa * ha) if ma[i] and mb[i])
        only_a = sum(1 for i in range(wa * ha) if ma[i] and not mb[i])
        only_b = sum(1 for i in range(wa * ha) if mb[i] and not ma[i])
        union = inter + only_a + only_b
        print("@@IOU@@ %-6s %.4f  A %d  B %d  inter %d  onlyA %d  onlyB %d"
              % (v, inter / union if union else 0.0, inter + only_a, inter + only_b,
                 inter, only_a, only_b))


main()
