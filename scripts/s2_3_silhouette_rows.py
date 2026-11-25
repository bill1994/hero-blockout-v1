"""Row-by-row and column-by-column silhouette extents, ours vs the reference,
in metres. Turns an IoU number into a place on the model.

  blender -b --factory-startup --python scripts/s2_3_silhouette_rows.py -- \
      ab_s2d front 0.05,0.2,0.35

arguments: <render dir under renders/> [view] [comma separated world z list]

Pixel conventions: row 0 is the bottom of the image; the orthographic contract
is 720 px over ortho_scale 1.15 centred on world (x -0.0005, z 0.377), so
  px_x = 360 + (x + 0.0005) * 720 / 1.15
  px_y = 360 + (z - 0.377) * 720 / 1.15
"""

import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL = 6.0 / 255.0
PPM = 720.0 / 1.15                  # px per metre
ORIGIN_X = 360.0 + 0.0005 * PPM     # px of world x = 0
ORIGIN_Z = 360.0 - 0.377 * PPM      # px of world z = 0


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


def row_extent(w, h, m, world_z):
    row = int(round(ORIGIN_Z + world_z * PPM))
    if not (0 <= row < h):
        return None
    xs = [x for x in range(w) if m[row * w + x]]
    return None if not xs else ((min(xs) - ORIGIN_X) / PPM, (max(xs) - ORIGIN_X) / PPM)


def col_extent(w, h, m, world_x):
    col = int(round(ORIGIN_X + world_x * PPM))
    if not (0 <= col < w):
        return None
    ys = [y for y in range(h) if m[y * w + col]]
    return None if not ys else ((min(ys) - ORIGIN_Z) / PPM, (max(ys) - ORIGIN_Z) / PPM)


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = argv[0] if argv else "ab_s2d"
view = argv[1] if len(argv) > 1 else "front"
zs = ([float(s) for s in argv[2].split(",")] if len(argv) > 2
      else [0.02, 0.10, 0.20, 0.30, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70])

pa = os.path.join(ROOT, "renders", out_dir, "view_%s.png" % view)
pb = os.path.join(ROOT, "reference", "views_20261124", "ref_%s.png" % view)
wa, ha, ma = mask(pa)
wb, hb, mb = mask(pb)

print("@@ROWS@@ view %s (world x extents per row)" % view)
for z in zs:
    ea = row_extent(wa, ha, ma, z)
    eb = row_extent(wb, hb, mb, z)
    if ea is None or eb is None:
        print("@@ROWS@@ z %.2f  ours %s  ref %s" % (z, ea, eb))
        continue
    print("@@ROWS@@ z %.2f  ours %.4f..%.4f (w %.4f)   ref %.4f..%.4f (w %.4f)   dx %+.4f %+.4f"
          % (z, ea[0], ea[1], ea[1] - ea[0], eb[0], eb[1], eb[1] - eb[0],
             ea[0] - eb[0], ea[1] - eb[1]))

print("@@COLS@@ view %s (world z extents per column)" % view)
for x in [-0.45, -0.35, -0.25, -0.12, 0.0, 0.10, 0.25, 0.40, 0.49]:
    ca = col_extent(wa, ha, ma, x)
    cb = col_extent(wb, hb, mb, x)
    if ca is None or cb is None:
        print("@@COLS@@ x %.2f  ours %s  ref %s" % (x, ca, cb))
        continue
    print("@@COLS@@ x %.2f  ours z %.4f..%.4f   ref z %.4f..%.4f   d %+.4f %+.4f"
          % (x, ca[0], ca[1], cb[0], cb[1], ca[0] - cb[0], ca[1] - cb[1]))
