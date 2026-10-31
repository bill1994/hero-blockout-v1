"""P1b: mint accents as narrow strips, and palette values against section 5.1.

Ruling: mint becomes one vertical band per side plus the existing top band, cream
everywhere else. The four full-face mint plates (Machine_Panel_L, Machine_Panel_R_Top,
Machine_Panel_R_SideF, _SideB) are what make the machine read as a green box; they are
removed and replaced by two narrow bands sitting 10 mm proud of the flat part of each
side face. The top plate stays as the section 5.2 "arc band".

Palette: section 5.1 gives p50 midtones. Albedo is set from p50 (sRGB -> linear), which
is the documented approximation; verification is a render sample afterwards, not a claim
made here.

Run after v13_p1a_shell.py, on the p1a scratch. Read-only unless --apply.

Usage:
    blender --background <p1a scratch.blend> --python qa_v2/v13_p1b_dress.py -- \
        [--out <blend>] [--report <json>] [--no-apply]
"""

import json
import math
import os
import sys

import bmesh
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


APPLY = "--no-apply" not in argv
OUT = arg("--out", None)
REPORT = arg("--report", None)

BODY = "Machine_Body"
OLD_PANELS = ["Machine_Panel_L", "Machine_Panel_R_Top",
              "Machine_Panel_R_SideF", "Machine_Panel_R_SideB"]
HALF_X = 0.90          # current shell half width
STRIP_Y = 0.34         # half width of the mint band
STRIP_Z = (0.28, 1.72)  # inside the body's flat z range (0.20 .. 1.80)
STRIP_T = 0.010        # proud of the face
CORNER_SEG = 4

sc = bpy.context.scene
body = bpy.data.objects.get(BODY)
if body is None:
    raise SystemExit("P1B FATAL: no %s in %s" % (BODY, bpy.data.filepath))

mint = bpy.data.materials.get("MAT_Color_Mint")


# ---------------------------------------------------------- geometry helper ----
def rounded_rect(hx, hy, r, seg):
    r = max(0.002, min(r, min(hx, hy) - 0.002))
    ix, iy = hx - r, hy - r
    corners = ((ix, iy, 0.0), (-ix, iy, math.pi * 0.5),
               (-ix, -iy, math.pi), (ix, -iy, math.pi * 1.5))
    pts = []
    for cx, cy, a0 in corners:
        for i in range(seg + 1):
            a = a0 + (math.pi * 0.5) * i / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def build_slab(bm, hx, hy, hz, r, seg):
    """Thin rounded slab centred on the origin, flat faces normal to X."""
    lo = rounded_rect(hy, hz, r, seg)
    hi = list(lo)
    vlo = [bm.verts.new((-hx, y, z)) for y, z in lo]
    vhi = [bm.verts.new((hx, y, z)) for y, z in hi]
    n = len(vlo)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vlo[i], vlo[j], vhi[j], vhi[i]))
    bm.faces.new(list(reversed(vlo)))
    bm.faces.new(vhi)


def make_strip(name, sign):
    o = bpy.data.objects.get(name)
    if o is not None:
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    build_slab(bm, STRIP_T / 2.0, STRIP_Y, (STRIP_Z[1] - STRIP_Z[0]) / 2.0, 0.05, CORNER_SEG)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.location = (sign * (HALF_X + STRIP_T / 2.0 - 0.002), 0.0,
                  (STRIP_Z[0] + STRIP_Z[1]) / 2.0)
    if mint:
        o.data.materials.append(mint)
    o.parent = body
    o.matrix_parent_inverse = body.matrix_world.inverted()
    return o


# ------------------------------------------------------------------ palette ----
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_linear(h):
    h = h.lstrip("#")
    return [round(srgb_to_linear(int(h[i:i + 2], 16) / 255.0), 4) for i in (0, 2, 4)]


TARGETS = {
    "MAT_Color_Mint": "#8DA69D",    # section 5.1 p50 grey-mint
    "MAT_Color_Amber": "#AB642E",   # section 5.1 p50 orange
    "MAT_Arm_Dark": "#424847",      # section 5.1 charcoal
}


def set_base_color(mat, rgb):
    before = None
    if not mat.use_nodes:
        mat.use_nodes = True
    bsdf = None
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            bsdf = n
            break
    if bsdf is not None:
        inp = bsdf.inputs["Base Color"]
        before = [round(v, 4) for v in inp.default_value]
        inp.default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    mat.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
    return before


palette = {}
for name, hx in TARGETS.items():
    m = bpy.data.materials.get(name)
    if m is None:
        palette[name] = "missing"
        continue
    target = hex_to_linear(hx)
    before = set_base_color(m, target) if APPLY else None
    palette[name] = {"hex": hx, "linear": target, "before": before}

# ------------------------------------------------------------------- strips ----
strips = []
if APPLY:
    for name in OLD_PANELS:
        o = bpy.data.objects.get(name)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)
    strips = [make_strip("P1_MintStrip_L", -1.0).name,
              make_strip("P1_MintStrip_R", +1.0).name]

out = {
    "blend": os.path.abspath(bpy.data.filepath),
    "applied": APPLY,
    "removed": OLD_PANELS,
    "strips": strips,
    "strip_spec": {"y_half": STRIP_Y, "z": list(STRIP_Z), "thickness": STRIP_T,
                   "proud_of_face": round(STRIP_T - 0.002, 4)},
    "palette": palette,
    "kept_top_band": "Machine_Panel_Top",
}

print("P1B DRESS %s" % ("APPLY" if APPLY else "DRY"))
print("  removed: %s" % ", ".join(OLD_PANELS))
print("  strips : %s  (y +-%.2f, z %.2f..%.2f, %.0f mm proud)" % (
    strips, STRIP_Y, STRIP_Z[0], STRIP_Z[1], STRIP_T * 1000))
for k, v in palette.items():
    print("  %-18s -> %s  linear %s  (was %s)" % (
        k, v["hex"] if isinstance(v, dict) else v,
        v["linear"] if isinstance(v, dict) else "", v["before"] if isinstance(v, dict) else ""))

if REPORT:
    os.makedirs(os.path.dirname(os.path.abspath(REPORT)) or ".", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("WROTE %s" % os.path.abspath(REPORT))

if APPLY:
    dest = os.path.abspath(OUT) if OUT else bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(filepath=dest)
    print("SAVED %s" % dest)
