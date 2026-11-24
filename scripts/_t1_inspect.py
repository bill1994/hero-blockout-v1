"""T1 inspection: scene stats + reference crops/bboxes. Read-only."""
import bpy
import os
import numpy as np

ROOT = r"G:\DSHProject\BlenderMcp"
OUT = os.path.join(ROOT, "renders", "insp")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "rebuild_v2.blend"))
sc = bpy.context.scene
sc.frame_set(1)
bpy.context.view_layer.update()

print("=== OBJECTS ===")
tot_v = tot_t = tot_p = 0
for ob in bpy.data.objects:
    if ob.type == 'MESH':
        me = ob.data
        me.calc_loop_triangles()
        t = len(me.loop_triangles)
        tris = sum(1 for p in me.polygons if len(p.vertices) == 3)
        quads = sum(1 for p in me.polygons if len(p.vertices) == 4)
        ng = len(me.polygons) - tris - quads
        tot_v += len(me.vertices); tot_t += t; tot_p += len(me.polygons)
        ad = "anim" if (ob.animation_data and ob.animation_data.action) else "-"
        par = ob.parent.name if ob.parent else "-"
        w = ob.matrix_world.translation
        print("MESH %-26s v=%5d f=%5d tri=%5d q=%4d n=%3d par=%-22s %s loc=(%.3f,%.3f,%.3f)"
              % (ob.name, len(me.vertices), len(me.polygons), t, quads, ng, par, ad, w.x, w.y, w.z))
    elif ob.type in {'CAMERA', 'LIGHT', 'EMPTY', 'ARMATURE'}:
        print("%-8s %-26s par=%s" % (ob.type, ob.name, ob.parent.name if ob.parent else "-"))

print("=== TOTAL verts=%d faces=%d tris=%d ===" % (tot_v, tot_p, tot_t))
print("=== COLLECTIONS ===")
for c in bpy.data.collections:
    print("COLL", c.name, len(c.objects))

print("=== MATRICES ===")
for f in (1, 120, 220):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    for n in ("Machine_Body", "Machine_Chute", "P1_ChuteRail", "P1_OutletRailL",
              "Machine_Hopper", "Machine_WindowFrame"):
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        m = ob.matrix_world
        print("M f%-3d %-18s loc=(%.4f,%.4f,%.4f) rot=(%.4f,%.4f,%.4f) scl=(%.3f,%.3f,%.3f)"
              % (f, n, *m.translation, *m.to_euler(), *m.to_scale()))

print("=== DIMS ===")
for n in ("Machine_Body", "Machine_Chute", "P1_ChuteRail", "P1_BaseBand",
          "Machine_WindowFrame", "V2_SidePanel", "P1_OutletRailL"):
    ob = bpy.data.objects.get(n)
    if ob is None:
        continue
    bb = [ob.matrix_world @ __import__("mathutils").Vector(c) for c in ob.bound_box]
    xs = [p.x for p in bb]; ys = [p.y for p in bb]; zs = [p.z for p in bb]
    print("BB %-18s x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f]"
          % (n, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

sc.frame_set(1)
bpy.context.view_layer.update()


# ---------------------------------------------------------------- images
def load(p):
    img = bpy.data.images.load(p)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(img)
    # linear -> sRGB
    a = np.clip(a, 0.0, None)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055)


def save(a, name):
    h, w = a.shape[:2]
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[..., :3] = a
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    img.pixels = rgba[::-1].ravel().tolist()
    img.file_format = 'PNG'
    p = os.path.join(OUT, name)
    img.filepath_raw = p
    img.save()
    bpy.data.images.remove(img)
    print("WROTE", p)


def up(a, f):
    return np.repeat(np.repeat(a, f, axis=0), f, axis=1)


def crop(a, name, x0, y0, x1, y1, f=3):
    save(up(a[y0:y1, x0:x1], f), name)


def bbox(mask, win=None):
    m = mask.copy()
    if win:
        x0, y0, x1, y1 = win
        k = np.zeros_like(m)
        k[y0:y1, x0:x1] = True
        m = m & k
    ys, xs = np.where(m)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), int(len(xs)))


def masks(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mx = a.max(axis=2); mn = a.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1e-5)
    coral = (r > 0.45) & (r - b > 0.10) & (r - g > 0.06) & (lum > 0.25) & (sat > 0.18)
    mint = (g > b + 0.015) & (g > r + 0.02) & (sat > 0.05) & (lum > 0.45)
    cream = (lum > 0.60) & (sat < 0.12)
    dark = (lum < 0.42) & (b >= r - 0.02)
    light = lum > 0.16
    return dict(coral=coral, mint=mint, cream=cream, dark=dark, model=light, lum=lum, sat=sat)


for tag, fn in (("tripo", "tripo_f001_front.png"), ("v2", "v2_f001_front.png")):
    a = load(os.path.join(ROOT, "renders", fn))
    M = masks(a)
    print("### %s" % tag)
    for k in ("model", "coral", "mint", "cream", "dark"):
        print("  mask %-6s bbox=%s" % (k, bbox(M[k])))
    # column profile of the model mask at some rows
    for row in (400, 450, 500, 560, 620, 660, 690, 705, 715):
        xs = np.where(M["model"][row])[0]
        xs = xs[(xs > 60) & (xs < 620)] if tag == "tripo" else xs
        if len(xs):
            print("  row %3d  x %d..%d  (n=%d)" % (row, xs.min(), xs.max(), len(xs)))
    # coral components (crude flood fill on masked coords)
    ys, xs = np.where(M["coral"])
    if len(xs):
        print("  coral pixel rows: %d..%d" % (ys.min(), ys.max()))

a = load(os.path.join(ROOT, "renders", "tripo_f001_front.png"))
crop(a, "tripo_front_lowerleft.png", 90, 585, 545, 760, 3)
crop(a, "tripo_front_upperleft.png", 90, 375, 425, 530, 4)
crop(a, "tripo_front_right.png", 480, 560, 850, 780, 3)

a = load(os.path.join(ROOT, "renders", "tripo_f001_34.png"))
crop(a, "tripo_34_conveyor.png", 380, 450, 830, 820, 2)

a = load(os.path.join(ROOT, "renders", "v2_f001_front.png"))
crop(a, "v2_front_lower.png", 330, 560, 700, 760, 3)
crop(a, "v2_front_upper.png", 330, 350, 700, 560, 3)

a = load(os.path.join(ROOT, "renders", "v2_f001_34.png"))
crop(a, "v2_34_conveyor.png", 520, 470, 830, 700, 3)
print("DONE")
