"""Reference measurement + parent-chain drift check. Read-only.

1) tripo front render: pixel scale from the body width, chute overhang in world units.
2) p19/rebuild_v2: do Machine_Body and Machine_OutputChute share the same world
   transform over the animation? (rail rides Machine_Body, chute rides the empty)
"""
import bpy
import os
import numpy as np
from mathutils import Vector

ROOT = r"G:\DSHProject\BlenderMcp"


def load(p):
    img = bpy.data.images.load(p)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(img)
    a = np.clip(a, 0.0, None)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055)


a = load(os.path.join(ROOT, "renders", "tripo_f001_front.png"))
r, g, b = a[..., 0], a[..., 1], a[..., 2]
lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
model = lum > 0.16
coral = (r > 0.45) & (r - b > 0.10) & (r - g > 0.06) & (lum > 0.25)

ys, xs = np.where(model)
print("REF model bbox x %d..%d  y %d..%d" % (xs.min(), xs.max(), ys.min(), ys.max()))

# body width: widest row in the machine area (rows 420..700)
best = None
for row in range(420, 700):
    xs_r = np.where(model[row])[0]
    if len(xs_r) == 0:
        continue
    x0, x1 = xs_r.min(), xs_r.max()
    if best is None or (x1 - x0) > best[0]:
        best = (x1 - x0, row, x0, x1)
print("REF widest row %d: x %d..%d (w=%d)" % (best[1], best[2], best[3], best[0]))

# rows through the conveyor only (right half) to find the chute end
for row in (640, 660, 680, 700, 720, 740, 760):
    xs_r = np.where(model[row])[0]
    if len(xs_r):
        print("REF row %3d model x %d..%d n=%d" % (row, xs_r.min(), xs_r.max(), len(xs_r)))
    cs = np.where(coral[row])[0]
    if len(cs):
        print("REF row %3d coral x %d..%d" % (row, cs.min(), cs.max()))

# body left/right edges measured at mid height (rows 450..620) restricted to x<520
for row in (470, 520, 570, 620, 660):
    xs_r = np.where(model[row])[0]
    xs_r = xs_r[xs_r < 520]
    if len(xs_r):
        print("REF row %3d body-left x=%d" % (row, xs_r.min()))

print("=== parent chain drift ===")
for tag, path in (("p19", "hero_animation_v14_p19.blend"), ("v2", "rebuild_v2.blend")):
    bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, path))
    for f in (1, 60, 120, 220, 327):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        out = []
        for n in ("Machine_Root", "Machine_Body", "Machine_OutputChute", "Machine_Chute",
                  "P1_ChuteRail", "P1_OutletRailL"):
            ob = bpy.data.objects.get(n)
            if ob is None:
                out.append("%s=None" % n)
                continue
            m = ob.matrix_world
            out.append("%s=(%.4f,%.4f,%.4f)" % (n, *m.translation))
        print("DRIFT %s f%-3d %s" % (tag, f, "  ".join(out)))
