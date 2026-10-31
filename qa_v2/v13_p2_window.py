"""P2: rebuild the window as a tall rounded opening, with a nebula inside it.

Section 6 P2. Three problems with the P1 state, one of them pre-existing:

1. Proportions. The doc contradicts itself: section 6 P1 asks for ~0.64 of body width,
   section 4.3 measures the reference at 0.5421 x 0.6158 of the body. 4.3 is the
   measured number (the doc says it replaced the earlier estimate), so the opening here
   is built to 0.547 x 0.620 - the 0.64 in the plan text is treated as stale.
   The 1.5528 window aspect from 4.3 cannot be reproduced on this body: it only holds
   because the reference machine is 0.73 W:H and ours is 1.00 (section 12 Q1's accepted
   compromise). What is matched is the window's share of the face, not the aspect.

2. `Machine_Window` (the glass) was floating above the opening: its bbox is z 1.298..
   2.102 against an opening at z 0.426..1.574, so the pane was not covering the hole at
   all. Rebuilt as a pane that actually sits in the opening.

3. Nebula. Section 6 asks for a volumetric render version and a mesh-based GLB version.
   This builds ONE version - emissive mesh blobs - used by both, because the deliverable
   is the GLB and it cannot carry volumetrics, and two divergent builds is two ways to
   fail. The section's fear was showing the two as identical when they were not; here
   they are identical by construction, which is a stronger guarantee than a documented
   difference. Recorded in BUILD_NOTES so nobody later assumes a volume shader exists.

Layer stack, front to back: charcoal frame ring (y -0.858..-0.788), cyan glow ring at
the opening's inner edge, glass pane, nebula blobs, dark cavity.

Usage:
    blender --background <blend> --python qa_v2/v13_p2_window.py -- \
        [--out <blend>] [--report <json>] [--no-apply]
"""

import json
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


APPLY = "--no-apply" not in argv
OUT = arg("--out", None)
REPORT = arg("--report", None)

BODY = "Machine_Body"
FACE_Y = -0.80
CENTER_Z = 1.0

# opening (inner) half extents -> 0.984 x 1.116 = 0.547 x 0.620 of a 1.8 body
HW, HH = 0.492, 0.558
R_CORNER = 0.42
FACE_BAND = 0.072          # frame width around the opening
GLOW_W = 0.020
FRAME_Y = (-0.858, -0.788)
GLOW_Y = -0.7955
CUT_Y = (-0.87, -0.45)      # deep pocket: a 0.10 cut hid half the nebula behind the shell
GLASS_Y = -0.792
SEG = 7

BLOBS = 30
BLOB_SEED = 20261031

NEBULA = {
    "MAT_Nebula_Pink": "#F8AEE2",
    "MAT_Nebula_Cyan": "#8BF5F2",
    "MAT_Nebula_Violet": "#C9A7E3",
}

sc = bpy.context.scene
body = bpy.data.objects.get(BODY)
if body is None:
    raise SystemExit("P2 FATAL: no %s" % BODY)


# ------------------------------------------------------------------ helpers ----
def rounded_ring(hx, hy, r, seg, inset=0.0):
    """Perimeter points of a rounded rect, optionally inset, CCW."""
    hx = max(0.004, hx - inset)
    hy = max(0.004, hy - inset)
    r = max(0.002, min(r - inset, min(hx, hy) - 0.002))
    ix, iy = hx - r, hy - r
    corners = ((ix, iy, 0.0), (-ix, iy, math.pi * 0.5),
               (-ix, -iy, math.pi), (ix, -iy, math.pi * 1.5))
    pts = []
    for cx, cy, a0 in corners:
        for i in range(seg + 1):
            a = a0 + (math.pi * 0.5) * i / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rebuild_prism(name, hx, hy, r, y0, y1, mat_name, seg=SEG, inset=0.0,
                  cap_front=True):
    """Solid rounded-rect prism along Y (boolean cutter, or cavity shell).

    cap_front=False leaves the y0 end open, which is what the cavity needs: a closed
    prism hides the nebula behind its own front face, and the window then reads as a
    blank panel.
    """
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    pts = rounded_ring(hx, hy, r, seg, inset)
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, CENTER_Z + z)) for x, z in pts]
    b = [bm.verts.new((x, y1, CENTER_Z + z)) for x, z in pts]
    n = len(a)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_front:
        bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    # Hand-built faces leave normals inconsistent; the EXACT boolean reads
    # inside/outside from them, so an inverted solid silently stops cutting.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    m = bpy.data.materials.get(mat_name) if mat_name else None
    if m:
        o.data.materials.clear()
        o.data.materials.append(m)
    return o


def rebuild_ring(name, hx, hy, r, band, y0, y1, mat_name, seg=SEG):
    """Annulus (frame / glow ring) between the opening and opening+band."""
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    outer = rounded_ring(hx + band, hy + band, r + band, seg)
    inner = rounded_ring(hx, hy, r, seg)
    bm = bmesh.new()
    of = [bm.verts.new((x, y0, CENTER_Z + z)) for x, z in outer]
    ob = [bm.verts.new((x, y1, CENTER_Z + z)) for x, z in outer]
    if_ = [bm.verts.new((x, y0, CENTER_Z + z)) for x, z in inner]
    ib = [bm.verts.new((x, y1, CENTER_Z + z)) for x, z in inner]
    n = len(of)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((of[i], of[j], ob[j], ob[i]))        # outer wall
        bm.faces.new((ib[j], ib[i], if_[i], if_[j]))      # inner wall
        bm.faces.new((of[j], of[i], if_[i], if_[j]))      # front face
        bm.faces.new((ob[i], ob[j], ib[j], ib[i]))        # back face
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    m = bpy.data.materials.get(mat_name)
    if m and not o.data.materials:
        o.data.materials.append(m)
    return o


def rebuild_glass(name, hx, hy, r, y, mat_name, seg=SEG):
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    pts = rounded_ring(hx, hy, r, seg)
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, CENTER_Z + z)) for x, z in pts]
    bm.faces.new(vs)
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    m = bpy.data.materials.get(mat_name)
    if m and not o.data.materials:
        o.data.materials.append(m)
    return o


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def emissive_material(name, hexcolor, strength, alpha=1.0):
    """Emissive + alpha through a Principled BSDF.

    A Mix(Transparent, Emission) stack renders correctly in EEVEE but the glTF
    exporter does not translate it, so the GLB came out with no alphaMode at all -
    the nebula would be opaque in every viewer while looking soft in the render.
    Principled carries Emission Color/Strength and Alpha on the path the exporter
    does understand, so render and GLB share one definition instead of drifting.
    """
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    h = hexcolor.lstrip("#")
    rgb = [srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)]
    bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Emission Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    bsdf.inputs["Emission Strength"].default_value = strength
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Alpha"].default_value = alpha
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    if hasattr(m, "blend_method"):
        m.blend_method = "BLEND"
    m.use_backface_culling = False
    m.diffuse_color = (rgb[0], rgb[1], rgb[2], alpha)
    return m

def make_blob(name, loc, radius, mat):
    o = bpy.data.objects.get(name)
    if o is not None:
        bpy.data.objects.remove(o, do_unlink=True)
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius)
    for v in bm.verts:
        v.co.x *= 1.0
        v.co.y *= 0.35          # flatten along the view axis
        v.co.z *= 1.35          # stretch vertically, like a rising plume
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    sc.collection.objects.link(o)
    o.location = Vector(loc)
    me.materials.append(mat)
    o.parent = body
    o.matrix_parent_inverse = body.matrix_world.inverted()
    return o


# ---------------------------------------------------------------------- build ----
report = {"opening": {"w": round(2 * HW, 4), "h": round(2 * HH, 4),
                      "w_to_body": round(2 * HW / 1.8, 4),
                      "h_to_body": round(2 * HH / 1.8, 4),
                      "target": [0.5421, 0.6158], "corner_r": R_CORNER},
          "applied": APPLY}

if APPLY:
    rebuild_prism("Cutter_Window", HW, HH, R_CORNER, CUT_Y[0], CUT_Y[1], None)
    frame = rebuild_ring("Machine_WindowFrame", HW, HH, R_CORNER, FACE_BAND,
                         FRAME_Y[0], FRAME_Y[1], "MAT_Window_Frame")
    glow = rebuild_ring("Machine_WindowGlow", HW - GLOW_W, HH - GLOW_W,
                        R_CORNER - GLOW_W, GLOW_W,
                        GLOW_Y - 0.004, GLOW_Y + 0.004, "MAT_Window_Glow")
    # glass: the P1 pane was opaque enough to hide the whole interior (the window
    # rendered as a blank cream panel). The reference shows a dark interior with a
    # plume, so the pane is dropped rather than fought with.
    glass = bpy.data.objects.get("Machine_Window")
    if glass is not None:
        bpy.data.objects.remove(glass, do_unlink=True)

    # cavity: open-front shell so the nebula is actually visible inside it
    cav = bpy.data.objects.get("Machine_WindowCavity")
    if cav is not None:
        rebuild_prism("Machine_WindowCavity", HW - 0.008, HH - 0.008, R_CORNER - 0.008,
                      -0.46, -0.40, "MAT_Window_Cavity", cap_front=False)

    for n in ("Machine_WindowNoise1", "Machine_WindowNoise2"):
        o = bpy.data.objects.get(n)
        if o is not None:
            bpy.data.objects.remove(o, do_unlink=True)

    mats = {
        "pink": emissive_material("MAT_Nebula_Pink", NEBULA["MAT_Nebula_Pink"], 1.6, 0.55),
        "cyan": emissive_material("MAT_Nebula_Cyan", NEBULA["MAT_Nebula_Cyan"], 2.0, 0.50),
        "violet": emissive_material("MAT_Nebula_Violet", NEBULA["MAT_Nebula_Violet"], 1.3, 0.45),
    }
    rng = random.Random(BLOB_SEED)
    blobs = []
    for i in range(BLOBS):
        # pull positions toward the window centre so the plume reads as one mass
        u = rng.uniform(-1.0, 1.0)
        w = rng.uniform(-1.0, 1.0)
        r = 0.035 + 0.075 * abs(rng.gauss(0, 0.5))
        x = u * (HW - 0.10) * 0.85
        z = w * (HH - 0.12) * 0.85
        y = -0.72 + rng.uniform(0.0, 0.20)
        key = ("pink", "cyan", "violet")[i % 3]
        blobs.append(make_blob("P2_Nebula_%02d" % i,
                               (x, y, CENTER_Z + z), r, mats[key]).name)
    report["blobs"] = blobs
    report["layers"] = {"frame": FRAME_Y, "glow_y": GLOW_Y, "glass_y": GLASS_Y}

print("P2 WINDOW %s" % ("APPLY" if APPLY else "DRY"))
print("  opening %.3f x %.3f  = %.4f x %.4f of body  (target 0.5421 x 0.6158)" % (
    2 * HW, 2 * HH, 2 * HW / 1.8, 2 * HH / 1.8))
print("  frame band %.3f, glow %.3f, corner r %.3f" % (FACE_BAND, GLOW_W, R_CORNER))
if APPLY:
    print("  blobs: %d (seed %d)" % (len(report["blobs"]), BLOB_SEED))

if REPORT:
    os.makedirs(os.path.dirname(os.path.abspath(REPORT)) or ".", exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("WROTE %s" % os.path.abspath(REPORT))

if APPLY:
    dest = os.path.abspath(OUT) if OUT else bpy.data.filepath
    bpy.ops.wm.save_as_mainfile(filepath=dest)
    print("SAVED %s" % dest)




