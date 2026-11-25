"""Pixel diff between two view sheets.

Byte-identical PNGs are too strict (the encoder embeds a timestamp), so compare
the decoded pixels instead: count differing pixels, report the max channel delta
and the bounding box of every difference. A deletion that is truly invisible
must produce zero differing pixels.

Run:
  blender --background --factory-startup --python scripts/ab_diff.py -- \
      renders/ab_v7 v7 renders/ab_s2a s2a
"""

import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = 1.0 / 255.0


def load(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = list(img.pixels)
    bpy.data.images.remove(img)
    return w, h, px


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    dir_a, pre_a, dir_b, pre_b = argv[:4]
    dir_a = os.path.join(ROOT, dir_a)
    dir_b = os.path.join(ROOT, dir_b)

    views = ["front", "right", "top", "iso", "armclose", "back", "ventclose"]
    bad = 0
    for v in views:
        pa = os.path.join(dir_a, "%s_%s.png" % (pre_a, v))
        pb = os.path.join(dir_b, "%s_%s.png" % (pre_b, v))
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print("@@DIFF@@ %-9s MISSING" % v)
            bad += 1
            continue
        wa, ha, a = load(pa)
        wb, hb, b = load(pb)
        assert (wa, ha) == (wb, hb)
        w, h = wa, ha
        n = w * h
        count = 0
        worst = 0.0
        xmin, ymin, xmax, ymax = w, h, -1, -1
        for i in range(n):
            j = i * 4
            d = max(abs(a[j] - b[j]), abs(a[j + 1] - b[j + 1]), abs(a[j + 2] - b[j + 2]))
            if d > TOL:
                count += 1
                if d > worst:
                    worst = d
                x, y = i % w, i // w
                xmin, xmax = min(xmin, x), max(xmax, x)
                ymin, ymax = min(ymin, y), max(ymax, y)
        if count:
            print("@@DIFF@@ %-9s %d px (%.3f%%), max %.4f, box x%d..%d y%d..%d"
                  % (v, count, 100.0 * count / n, worst, xmin, xmax, ymin, ymax))
            bad += 1
        else:
            print("@@SAME@@ %-9s 0 px differ" % v)
    print("@@SUMMARY@@ %d/%d views differ" % (bad, len(views)))


main()
