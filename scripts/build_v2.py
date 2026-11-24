"""Rebuild the machine geometry in a copy of p19, keeping every binding intact.

Starts from hero_animation_v14_p19.blend every run, so it is idempotent.
Only mesh datablocks are replaced; objects, parents, actions and constraints
are untouched.

Usage: blender -b --python build_v2.py -- <stage>
  stage 1 : shell, base band, plinth, feet, hopper, hopper collar, screen
  stage 2 : arm
  stage 3 : chute + small details
"""
import bpy
import bmesh
import math
import sys
import os
from mathutils import Vector, Matrix

SRC = r"G:\DSHProject\BlenderMcp\hero_animation_v14_p19.blend"
DST = r"G:\DSHProject\BlenderMcp\rebuild_v2.blend"

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
STAGE = int(args[0]) if args else 1

bpy.ops.wm.open_mainfile(filepath=SRC)
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()


# --------------------------------------------------------------------------
# materials
# --------------------------------------------------------------------------
def _set(bsdf, names, value):
    for n in names:
        if n in bsdf.inputs:
            bsdf.inputs[n].default_value = value
            return True
    return False


def mat(name, base, rough=0.45, metal=0.0, emis=None, emis_str=0.0, spec=0.5):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        return m
    _set(bsdf, ["Base Color"], (*base, 1.0))
    _set(bsdf, ["Roughness"], rough)
    _set(bsdf, ["Metallic"], metal)
    _set(bsdf, ["Specular IOR Level", "Specular"], spec)
    if emis is not None:
        _set(bsdf, ["Emission Color", "Emission"], (*emis, 1.0))
        _set(bsdf, ["Emission Strength"], emis_str)
    return m


M_CREAM = mat("V2_Cream", (0.855, 0.835, 0.775), rough=0.42)
M_MINT = mat("V2_Mint", (0.330, 0.600, 0.510), rough=0.46)
M_MINT_D = mat("V2_MintDeep", (0.180, 0.410, 0.345), rough=0.50)
M_SLATE = mat("V2_Slate", (0.048, 0.062, 0.078), rough=0.22, spec=0.7)
M_SCREEN = mat("V2_Screen", (0.020, 0.028, 0.036), rough=0.26, spec=0.45,
               emis=(0.11, 0.19, 0.23), emis_str=0.30)
M_CORAL = mat("V2_Coral", (0.780, 0.330, 0.230), rough=0.45)
M_METAL = mat("V2_Metal", (0.480, 0.500, 0.520), rough=0.32, metal=1.0)
M_RUBBER = mat("V2_Rubber", (0.045, 0.048, 0.052), rough=0.82)
M_IDEA = mat("V2_Idea", (0.86, 0.44, 0.13), rough=0.30,
             emis=(1.00, 0.56, 0.20), emis_str=0.90)
M_GLOW = mat("V2_Glow", (0.26, 0.74, 0.62), rough=0.38,
             emis=(0.20, 0.62, 0.50), emis_str=0.85)


# --------------------------------------------------------------------------
# mesh helpers
# --------------------------------------------------------------------------
def finish(bm, me_name, material, smooth=True, uv_scale=1.0):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(me_name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.validate(verbose=False)
    me.materials.append(material)
    box_uv(me, uv_scale)
    return me


def box_uv(me, scale=1.0):
    if me.uv_layers:
        while me.uv_layers:
            me.uv_layers.remove(me.uv_layers[0])
    layer = me.uv_layers.new(name="UVMap")
    uv = layer.data
    for poly in me.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.y, co.z
            elif ax == 1:
                u, v = co.x, co.z
            else:
                u, v = co.x, co.y
            uv[li].uv = (u * scale, v * scale)


# --- global LOD knobs: keep the asset low-poly without touching call sites ---
DENS = 0.40
DENS_BEVEL = 0.45


def bm_box(size, bevel=0.0, segs=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts),
                        offset=bevel,
                        segments=max(1, int(round(segs * DENS_BEVEL))),
                        profile=0.5,
                        affect='EDGES', clamp_overlap=True)
    return bm


def bm_lathe(profile, segs=48, close=True):
    """profile: list of (radius, z) forming a closed outline."""
    segs = max(12, int(round(segs * DENS)))
    bm = bmesh.new()
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    n = len(rings)
    for j in range(n - 1):
        for i in range(segs):
            i2 = (i + 1) % segs
            bm.faces.new((rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i]))
    if close:
        for i in range(segs):
            i2 = (i + 1) % segs
            bm.faces.new((rings[-1][i], rings[-1][i2], rings[0][i2], rings[0][i]))
    return bm


def rr_points(w, h, r, nc=7):
    """Closed rounded-rectangle outline in the XZ plane, Y=0."""
    hw, hh = w * 0.5, h * 0.5
    r = min(r, hw * 0.999, hh * 0.999)
    cx, cy = hw - r, hh - r
    corners = [(cx, cy, 0.0), (-cx, cy, math.pi * 0.5),
               (-cx, -cy, math.pi), (cx, -cy, 1.5 * math.pi)]
    pts = []
    for k, (ox, oy, a0) in enumerate(corners):
        for i in range(nc + 1):
            if k > 0 and i == 0:
                continue
            a = a0 + (math.pi * 0.5) * i / nc
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def bm_ring(w_out, h_out, r_out, w_in, h_in, r_in, depth, nc=7):
    """Rounded-rect ring extruded along Y, centred on origin."""
    po = rr_points(w_out, h_out, r_out, nc)
    pi = rr_points(w_in, h_in, r_in, nc)
    assert len(po) == len(pi)
    bm = bmesh.new()
    yf, yb = -depth * 0.5, depth * 0.5
    of = [bm.verts.new((x, yf, z)) for (x, z) in po]
    ob = [bm.verts.new((x, yb, z)) for (x, z) in po]
    inf = [bm.verts.new((x, yf, z)) for (x, z) in pi]
    ib = [bm.verts.new((x, yb, z)) for (x, z) in pi]
    n = len(po)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((of[i], of[j], inf[j], inf[i]))
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
        bm.faces.new((of[j], of[i], ob[i], ob[j]))
        bm.faces.new((inf[i], inf[j], ib[j], ib[i]))
    return bm


def bm_plate(w, h, r, depth, nc=7):
    """Filled rounded-rect slab extruded along Y."""
    p = rr_points(w, h, r, nc)
    bm = bmesh.new()
    yf, yb = -depth * 0.5, depth * 0.5
    front = [bm.verts.new((x, yf, z)) for (x, z) in p]
    back = [bm.verts.new((x, yb, z)) for (x, z) in p]
    n = len(p)
    cf = bm.verts.new((0, yf, 0))
    cb = bm.verts.new((0, yb, 0))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((cf, front[j], front[i]))
        bm.faces.new((cb, back[i], back[j]))
        bm.faces.new((front[i], front[j], back[j], back[i]))
    return bm


def bm_cyl(r, h, segs=32, bevel=0.0):
    segs = max(10, int(round(segs * DENS)))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r, depth=h)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts),
                        offset=bevel, segments=2, profile=0.5,
                        affect='EDGES', clamp_overlap=True)
    return bm


def bm_sphere(r, segs=32, rings=16):
    segs = max(10, int(round(segs * DENS)))
    rings = max(6, int(round(rings * DENS)))
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    return bm


def swap(ob, me):
    old = ob.data
    ob.data = me
    if old is not None and old.users == 0:
        bpy.data.meshes.remove(old)


def world_of(ob):
    return ob.matrix_world.translation.copy()


def translate(bm, offset):
    for v in bm.verts:
        v.co += offset


def rebuild(name, bm, material, smooth=True, uv_scale=1.0, local_offset=None,
            reset_scale=False):
    ob = bpy.data.objects.get(name)
    if ob is None:
        print("SKIP missing object: %s" % name)
        return None
    if reset_scale:
        ob.scale = (1.0, 1.0, 1.0)
        bpy.context.view_layer.update()
    if local_offset is not None:
        translate(bm, Vector(local_offset))
    me = finish(bm, name + "_V2", material, smooth, uv_scale)
    swap(ob, me)
    print("REBUILT %-22s verts=%d polys=%d" % (name, len(me.vertices), len(me.polygons)))
    return ob


# --------------------------------------------------------------------------
# stage 1 - shell, base, hopper, screen
# --------------------------------------------------------------------------
def delete_objects(names):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)


if STAGE >= 1:
    # Cube: not part of the asset. In the p19 working file it was a raw
    # untextured cube (144 verts, 1.861 x 1.598 x 2.285) dropped in at the main
    # shell's position while Machine_Body itself was hidden in the outliner -
    # an abandoned body-swap experiment. The committed p19 has no Cube; this
    # keeps the script idempotent against either state.
    delete_objects(["Cube"])
    delete_objects(["P1_Bolt_%s%d" % (s, i) for s in "BFLR" for i in range(4)])
    # Superseded by the rebuilt shell: the side mint strips are replaced by
    # V2_SidePanel and the thin top skin by the beveled body top. Present in
    # committed p19, absent from the aborted edit - delete either way so both
    # inputs produce the same model.
    delete_objects(["P1_MintStrip_L", "P1_MintStrip_R", "P3f_TopSkin"])

    # --- main shell -------------------------------------------------------
    # object origin sits at world (0,0,1.49); local frame == world frame
    ob = bpy.data.objects["Machine_Body"]
    body_me = finish(bm_box((1.80, 1.60, 2.46), bevel=0.105, segs=4),
                     "Machine_Body_V2", M_CREAM, uv_scale=0.5)
    swap(ob, body_me)
    print("REBUILT Machine_Body verts=%d" % len(body_me.vertices))

    # --- mint skirt band --------------------------------------------------
    # world z 0.26 .. 0.74, wrapper slightly proud of the shell
    band_ob = bpy.data.objects["P1_BaseBand"]
    base = world_of(band_ob)
    bm = bm_box((1.845, 1.645, 0.48), bevel=0.075, segs=3)
    translate(bm, Vector((0, 0, 0.50)) - base)
    swap(band_ob, finish(bm, "P1_BaseBand_V2", M_MINT, uv_scale=0.5))
    print("REBUILT P1_BaseBand")

    # --- plinth -----------------------------------------------------------
    base_ob = bpy.data.objects["Machine_Base"]
    base_ob.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    b = world_of(base_ob)
    bm = bm_box((1.79, 1.59, 0.27), bevel=0.070, segs=3)
    translate(bm, Vector((0, 0, 0.135)) - b)
    swap(base_ob, finish(bm, "Machine_Base_V2", M_CREAM, uv_scale=0.5))
    print("REBUILT Machine_Base")

    # --- feet -------------------------------------------------------------
    feet_ob = bpy.data.objects["Machine_Feet"]
    f = world_of(feet_ob)
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            sub = bm_cyl(0.082, 0.12, segs=20, bevel=0.0)
            translate(sub, Vector((sx * 0.72, sy * 0.545, -0.02)) - f)
            tmp = bpy.data.meshes.new("_tmp")
            sub.to_mesh(tmp)
            sub.free()
            bm.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
    swap(feet_ob, finish(bm, "Machine_Feet_V2", M_RUBBER, uv_scale=0.5))
    print("REBUILT Machine_Feet")

    # --- hopper collar (pedestal ring on the shell top) -------------------
    col = bpy.data.objects["P3d_HopperCollar"]
    col.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    c = world_of(col)
    bm = bm_cyl(0.395, 0.09, segs=64, bevel=0.025)
    translate(bm, Vector((0, 0, 2.745)) - c)
    swap(col, finish(bm, "P3d_HopperCollar_V2", M_CREAM, uv_scale=0.5))
    print("REBUILT P3d_HopperCollar")

    # --- hopper bowl ------------------------------------------------------
    hop = bpy.data.objects["Machine_Hopper"]
    hop.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    h = world_of(hop)
    # wide shallow bowl sitting on a short neck (Tripo reads as a bowl, not a cone)
    N = 12
    z0, z1 = -0.620, 0.205
    neck_top = -0.320

    def rad(z):
        if z <= neck_top:
            t = (z - z0) / (neck_top - z0)
            return 0.398 + 0.028 * (t ** 1.4)
        t = (z - neck_top) / (z1 - neck_top)
        return 0.426 + (0.700 - 0.426) * (t ** 1.45)

    wall = []
    for i in range(N + 1):
        z = z0 + (z1 - z0) * (i / N)
        wall.append((rad(z), z))
    lip = [(0.713, z1 + 0.019),
           (0.706, z1 + 0.033),
           (0.674, z1 + 0.034),
           (0.659, z1 + 0.014)]
    inner = []
    for i in range(N, -1, -1):
        z = z0 + (z1 - z0) * (i / N)
        inner.append((max(0.300, rad(z) - 0.042), z))
    profile = wall + lip + inner
    bm = bm_lathe(profile, segs=48, close=True)
    translate(bm, Vector((0, 0, 3.245)) - h)
    swap(hop, finish(bm, "Machine_Hopper_V2", M_MINT, uv_scale=0.5))
    print("REBUILT Machine_Hopper verts=%d" % len(hop.data.vertices))

    # --- screen -----------------------------------------------------------
    # window centre world (0, -0.80, 1.645); opening 0.98 x 1.52
    win_c = Vector((0.0, -0.80, 1.645))

    frame = bpy.data.objects["Machine_WindowFrame"]
    frame.scale = (1.0, 1.0, 1.0)
    frame.location = (0, 0, 0)
    bpy.context.view_layer.update()
    fw = world_of(frame)
    bm = bm_ring(1.10, 1.62, 0.185, 0.955, 1.475, 0.135, depth=0.105, nc=8)
    translate(bm, win_c + Vector((0, -0.03, 0)) - fw)
    swap(frame, finish(bm, "Machine_WindowFrame_V2", M_CREAM, uv_scale=0.5))
    print("REBUILT Machine_WindowFrame")

    cavity = bpy.data.objects["Machine_WindowCavity"]
    cavity.scale = (1.0, 1.0, 1.0)
    cavity.location = (0, 0, 0)
    bpy.context.view_layer.update()
    cw = world_of(cavity)
    bm = bm_plate(1.02, 1.56, 0.155, depth=0.06, nc=8)
    translate(bm, win_c + Vector((0, 0.045, 0)) - cw)
    swap(cavity, finish(bm, "Machine_WindowCavity_V2", M_SLATE, uv_scale=0.5))
    print("REBUILT Machine_WindowCavity")

    glass = bpy.data.objects["Machine_WindowGlass"]
    bm = bm_plate(0.955, 1.475, 0.135, depth=0.022, nc=8)
    translate(bm, win_c + Vector((0, -0.012, 0)) - glass.matrix_world.translation)
    swap(glass, finish(bm, "Machine_WindowGlass_V2", M_SCREEN, smooth=False, uv_scale=0.5))
    print("REBUILT Machine_WindowGlass")

    # thin mint indicator strip tucked under the screen
    glow = bpy.data.objects["Machine_WindowGlow"]
    bm = bm_box((0.62, 0.03, 0.035), bevel=0.012, segs=2)
    translate(bm, Vector((0.0, -0.822, 0.795)) - glow.matrix_world.translation)
    swap(glow, finish(bm, "Machine_WindowGlow_V2", M_MINT_D, uv_scale=0.5))
    print("REBUILT Machine_WindowGlow")

    # --- indicator dots: keep object transforms, shift mesh in local space -
    dots = [("Machine_Light_01", -0.30), ("Machine_Light_02", 0.0), ("Machine_Light_03", 0.30)]
    for name, target_x in dots:
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        w = ob.matrix_world.translation.copy()
        bm = bm_cyl(0.048, 0.026, segs=24, bevel=0.008)
        bmesh.ops.rotate(bm, verts=bm.verts,
                         cent=(0, 0, 0),
                         matrix=__import__("mathutils").Matrix.Rotation(math.pi * 0.5, 3, 'X'))
        # target world position: below the screen, on the front face
        target = Vector((target_x, -0.815, 0.60))
        translate(bm, target - w)
        swap(ob, finish(bm, name + "_V2", M_GLOW if name.endswith("03") else M_MINT_D,
                        uv_scale=1.0))
        print("REBUILT %s" % name)

    # --- product + idea props --------------------------------------------
    prod = bpy.data.objects.get("Product")
    if prod is not None:
        bm = bm_sphere(0.5, segs=32, rings=20)
        swap(prod, finish(bm, "Product_V2", M_CORAL, uv_scale=1.0))
        print("REBUILT Product")

    idea = bpy.data.objects.get("Idea")
    if idea is not None:
        bm = bm_sphere(0.25, segs=24, rings=14)
        swap(idea, finish(bm, "Idea_V2", M_IDEA, uv_scale=1.0))
        print("REBUILT Idea")

# --------------------------------------------------------------------------
# stage 2 - articulated arm
# --------------------------------------------------------------------------
def rebuild_world(name, bm, material, smooth=True, uv_scale=0.5):
    """Mesh is authored in world space at the current frame, then baked into
    the object's local space so it keeps riding the existing animation."""
    ob = bpy.data.objects.get(name)
    if ob is None:
        print("SKIP missing object: %s" % name)
        return None
    bm.transform(ob.matrix_world.inverted())
    return rebuild(name, bm, material, smooth, uv_scale)


def bm_capsule(r, length, segs=28, rings=16):
    segs = max(10, int(round(segs * DENS)))
    rings = max(6, int(round(rings * DENS)))
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    for v in bm.verts:
        if v.co.z > 1e-5:
            v.co.z += length * 0.5
        elif v.co.z < -1e-5:
            v.co.z -= length * 0.5
    return bm


def bm_frustum(r0, r1, h, segs=24, bevel=0.018):
    segs = max(10, int(round(segs * DENS)))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r0, radius2=r1, depth=h)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts),
                        offset=bevel, segments=2, profile=0.5,
                        affect='EDGES', clamp_overlap=True)
    return bm


def aim(bm, direction, origin=(0, 0, 0)):
    q = Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized())
    bm.transform(q.to_matrix().to_4x4())
    bm.transform(Matrix.Translation(Vector(origin)))
    return bm


def seg_mid(p0, p1, t):
    return Vector(p0) + (Vector(p1) - Vector(p0)) * t


if STAGE >= 2:


    bpy.context.view_layer.update()
    sh_piv = bpy.data.objects["Arm_Shoulder_Pivot"]
    el_piv = bpy.data.objects["Arm_Elbow_Pivot"]
    wr_ob = bpy.data.objects["Arm_Wrist"]
    yaw_piv = bpy.data.objects["Arm_Yaw_Pivot"]

    P_yaw = yaw_piv.matrix_world.translation.copy()
    P_sh = sh_piv.matrix_world.translation.copy()
    P_el = el_piv.matrix_world.translation.copy()
    P_wr = wr_ob.matrix_world.translation.copy()
    # hinge axes come straight from the pivot frames (rotation is about local Y)
    AX_SH = sh_piv.matrix_world.to_3x3().col[1].normalized()
    AX_EL = el_piv.matrix_world.to_3x3().col[1].normalized()

    print("ARM yaw=%s sh=%s el=%s wr=%s" % (tuple(round(v, 3) for v in P_yaw),
                                            tuple(round(v, 3) for v in P_sh),
                                            tuple(round(v, 3) for v in P_el),
                                            tuple(round(v, 3) for v in P_wr)))

    # --- turret base bolted to the shell ---------------------------------
    bm = bm_cyl(0.196, 0.335, segs=48, bevel=0.030)
    aim(bm, (0, 0, 1), (P_yaw.x, P_yaw.y, P_sh.z - 0.315))
    rebuild_world("Arm_Base", bm, M_CREAM)

    bm = bm_cyl(0.214, 0.076, segs=48, bevel=0.020)
    aim(bm, (0, 0, 1), (P_yaw.x, P_yaw.y, P_sh.z - 0.150))
    rebuild_world("Arm_Yaw_Housing", bm, M_MINT)

    bm = bm_cyl(0.201, 0.058, segs=48, bevel=0.016)
    aim(bm, (0, 0, 1), (P_yaw.x, P_yaw.y, P_sh.z - 0.075))
    rebuild_world("Arm_ShoulderRiser", bm, M_CREAM)

    # --- shoulder knuckle --------------------------------------------------
    bm = bm_sphere(0.206, segs=32, rings=18)
    translate(bm, P_sh)
    rebuild_world("Arm_Shoulder_Joint", bm, M_CREAM)

    for side in (-1.0, 1.0):
        nm = "Arm_Shoulder_Cap_%s" % ("L" if side < 0 else "R")
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        bm = bm_cyl(0.138, 0.044, segs=40, bevel=0.012)
        aim(bm, AX_SH, P_sh + AX_SH * (0.150 * side))
        bm2 = bm_cyl(0.042, 0.020, segs=24, bevel=0.006)
        aim(bm2, AX_SH, P_sh + AX_SH * (0.178 * side))
        rebuild_world(nm, bm, M_MINT)
        n2 = nm.replace("_Cap_", "_Dot_")
        if bpy.data.objects.get(n2) is not None:
            rebuild_world(n2, bm2, M_SLATE)

    # --- upper arm ---------------------------------------------------------
    bm = bm_capsule(0.170, (P_el - P_sh).length - 0.16)
    aim(bm, P_el - P_sh, seg_mid(P_sh, P_el, 0.5))
    rebuild_world("Arm_UpperArm", bm, M_CREAM)

    for tag, t in (("A", 0.42), ("B", 0.78)):
        nm = "Arm_UpperArm_Seam_%s" % tag
        if bpy.data.objects.get(nm) is None:
            continue
        bm = bm_cyl(0.180, 0.034, segs=40, bevel=0.008)
        aim(bm, P_el - P_sh, seg_mid(P_sh, P_el, t))
        rebuild_world(nm, bm, M_MINT)

    # --- elbow knuckle -----------------------------------------------------
    bm = bm_sphere(0.186, segs=30, rings=16)
    translate(bm, P_el)
    rebuild_world("Arm_Elbow_Joint", bm, M_CREAM)

    for side in (-1.0, 1.0):
        nm = "Arm_Elbow_Cap_%s" % ("L" if side < 0 else "R")
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        bm = bm_cyl(0.126, 0.040, segs=40, bevel=0.010)
        aim(bm, AX_EL, P_el + AX_EL * (0.134 * side))
        bm2 = bm_cyl(0.038, 0.018, segs=24, bevel=0.005)
        aim(bm2, AX_EL, P_el + AX_EL * (0.160 * side))
        rebuild_world(nm, bm, M_MINT)
        n2 = nm.replace("_Cap_", "_Dot_")
        if bpy.data.objects.get(n2) is not None:
            rebuild_world(n2, bm2, M_SLATE)

    # --- forearm -----------------------------------------------------------
    bm = bm_capsule(0.158, (P_wr - P_el).length - 0.15)
    aim(bm, P_wr - P_el, seg_mid(P_el, P_wr, 0.5))
    rebuild_world("Arm_Forearm", bm, M_CREAM)

    for tag, t in (("A", 0.38), ("B", 0.74)):
        nm = "Arm_Forearm_Seam_%s" % tag
        if bpy.data.objects.get(nm) is None:
            continue
        bm = bm_cyl(0.168, 0.030, segs=40, bevel=0.007)
        aim(bm, P_wr - P_el, seg_mid(P_el, P_wr, t))
        rebuild_world(nm, bm, M_MINT)

    # --- wrist collar + cuff ----------------------------------------------
    fdir = (P_wr - P_el).normalized()
    bm = bm_cyl(0.140, 0.090, segs=40, bevel=0.018)
    aim(bm, fdir, P_wr - fdir * 0.055)
    rebuild_world("Arm_WristCollar", bm, M_MINT)

    bm = bm_cyl(0.152, 0.028, segs=40, bevel=0.008)
    aim(bm, fdir, P_wr + fdir * 0.012)
    rebuild_world("P3d_WristCuff", bm, M_SLATE)

    # --- gripper palm ------------------------------------------------------
    bm = bm_box((0.268, 0.268, 0.235), bevel=0.085, segs=4)
    aim(bm, fdir, P_wr + fdir * 0.150)
    rebuild_world("Arm_Gripper", bm, M_CREAM)

    # --- three claw prongs -------------------------------------------------
    grip_c = P_wr + fdir * 0.215
    for nm in ("Arm_Finger_L", "Arm_Finger_R", "Arm_Finger_C"):
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        base = ob.matrix_world.translation.copy()
        d = base - P_wr
        perp = d - fdir * d.dot(fdir)
        if perp.length > 0.06:
            prong = (perp.normalized() * 0.85 + fdir * 0.62).normalized()
        else:
            prong = fdir.copy()
        bm = bm_frustum(0.072, 0.026, 0.580, segs=20, bevel=0.018)
        aim(bm, prong, base + prong * 0.290)
        rebuild_world(nm, bm, M_CORAL)
        bm = bm_sphere(0.062, segs=20, rings=12)
        aim(bm, prong, base)
        n2 = nm + "_Knuckle"
        ob2 = bpy.data.objects.get(n2)
        if ob2 is not None:
            rebuild_world(n2, bm, M_CORAL)

    # --- shoulder fairing bridging the shell flank to the turret ----------
    bay = bpy.data.objects.get("P1_ShoulderBay")
    if bay is not None:
        bm = bm_box((0.520, 0.640, 0.470), bevel=0.145, segs=4)
        translate(bm, Vector((-1.100, 0.0, 2.090)))
        rebuild_world("P1_ShoulderBay", bm, M_CREAM)

# --------------------------------------------------------------------------
# stage 3 - output chute
# --------------------------------------------------------------------------
def merge_bms(parts):
    out = bmesh.new()
    for bm in parts:
        tmp = bpy.data.meshes.new("_tmpmerge")
        bm.to_mesh(tmp)
        bm.free()
        out.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    return out


CH_SLOPE = 0.189          # ~10.8 deg downhill toward +X
# T1b: the outlet read as a spear (tray ran to x 3.36). The tray now stops at
# x 2.60 and the coral end stop closes the run at x 2.88. Length is derived,
# so the side walls, rails and floor all follow CH_X1.
CH_X0, CH_X1 = 0.88, 2.536
CH_RAIL_END_X = 2.893     # outer face of the coral end stop, before its bevel
CH_YH = 0.400
CH_Z0, CH_Z1 = 1.400, 1.400 - math.tan(CH_SLOPE) * (CH_X1 - CH_X0)


def chute_place(bm, along=0.0, lift=0.0):
    """along / lift are measured in the chute's own rotated frame."""
    bm.transform(Matrix.Translation((along, 0.0, lift)))
    bm.transform(Matrix.Rotation(CH_SLOPE, 4, 'Y'))
    cx = (CH_X0 + CH_X1) * 0.5
    cz = (CH_Z0 + CH_Z1) * 0.5
    bm.transform(Matrix.Translation((cx, 0.0, cz)))
    return bm


def chute_along_for_x(x_world, length, lift, height):
    """along offset that puts a length x height block's downhill face on x_world."""
    cx = (CH_X0 + CH_X1) * 0.5
    return ((x_world - cx - (lift + height * 0.5) * math.sin(CH_SLOPE))
            / math.cos(CH_SLOPE) - length * 0.5)


if STAGE >= 3:
    L = CH_X1 - CH_X0
    ang = math.atan2(CH_Z0 - CH_Z1, L)

    # --- tray: floor plate + two side walls, one merged shell --------------
    plate = bm_box((L + 0.10, CH_YH * 2.0 + 0.04, 0.085), bevel=0.032, segs=3)
    plate_w = bm_box((L + 0.10, 0.085, 0.230), bevel=0.030, segs=3)
    translate(plate_w, Vector((0.0, CH_YH + 0.020, 0.070)))
    plate_w2 = bm_box((L + 0.10, 0.085, 0.230), bevel=0.030, segs=3)
    translate(plate_w2, Vector((0.0, -CH_YH - 0.020, 0.070)))
    tray = merge_bms([plate, plate_w, plate_w2])
    chute_place(tray)
    rebuild_world("Machine_Chute", tray, M_CREAM)

    bm = bm_box((L + 0.10, 0.115, 0.070), bevel=0.026, segs=3)
    translate(bm, Vector((0.0, CH_YH + 0.020, 0.170)))
    chute_place(bm)
    rebuild_world("P1_OutletRailL", bm, M_MINT)

    bm = bm_box((L + 0.10, 0.115, 0.070), bevel=0.026, segs=3)
    translate(bm, Vector((0.0, -CH_YH - 0.020, 0.170)))
    chute_place(bm)
    rebuild_world("P1_OutletRailR", bm, M_MINT)

    # --- coral end stop: rounded bumper that closes the outlet ------------
    # 0.34 long, so it caps the last stretch of the tray and its outer face
    # lands on CH_RAIL_END_X. Width is a touch proud of the side walls.
    CHAR_LEN, CHAR_W, CHAR_H = 0.340, 0.930, 0.245
    CHAR_LIFT = 0.080
    bm = bm_box((CHAR_LEN, CHAR_W, CHAR_H), bevel=0.038, segs=3)
    chute_place(bm, along=chute_along_for_x(CH_RAIL_END_X, CHAR_LEN, CHAR_LIFT, CHAR_H),
                lift=CHAR_LIFT)
    rebuild_world("P1_ChuteRail", bm, M_CORAL)

    # --- support bracket under the inner end ------------------------------
    bm = bm_box((0.420, CH_YH * 2.0 - 0.10, 0.320), bevel=0.055, segs=3)
    translate(bm, Vector((CH_X0 + 0.16, 0.0, CH_Z0 - 0.230)))
    rebuild_world("P1_ChuteSeat", bm, M_SLATE)

# --------------------------------------------------------------------------
# stage 4 - style pass: joint discs, side panel
# --------------------------------------------------------------------------
def new_child(parent_name, name, bm_world, material, smooth=True, uv_scale=0.5):
    piv = bpy.data.objects.get(parent_name)
    if piv is None:
        print("SKIP missing parent: %s" % parent_name)
        return None
    me = finish(bm_world, name, material, smooth, uv_scale)
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, me)
        piv.users_collection[0].objects.link(ob)
    else:
        swap(ob, me)
    ob.parent = piv
    ob.matrix_parent_inverse = piv.matrix_world.inverted()
    ob.location = (0.0, 0.0, 0.0)
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.scale = (1.0, 1.0, 1.0)
    print("NEWCHILD %-24s parent=%s verts=%d" % (name, parent_name, len(me.vertices)))
    return ob


if STAGE >= 4:
    bpy.context.view_layer.update()
    sh_piv = bpy.data.objects["Arm_Shoulder_Pivot"]
    el_piv = bpy.data.objects["Arm_Elbow_Pivot"]
    P_sh = sh_piv.matrix_world.translation.copy()
    P_el = el_piv.matrix_world.translation.copy()
    AX_SH = sh_piv.matrix_world.to_3x3().col[1].normalized()
    AX_EL = el_piv.matrix_world.to_3x3().col[1].normalized()

    for side in (-1.0, 1.0):
        tag = "L" if side < 0 else "R"
        bm = bm_cyl(0.150, 0.060, segs=44, bevel=0.014)
        aim(bm, AX_SH, P_sh + AX_SH * (0.172 * side))
        new_child("Arm_Yaw_Pivot", "V2_ShoulderDisc_" + tag, bm, M_MINT)
        bm = bm_cyl(0.050, 0.026, segs=24, bevel=0.007)
        aim(bm, AX_SH, P_sh + AX_SH * (0.208 * side))
        new_child("Arm_Yaw_Pivot", "V2_ShoulderDot_" + tag, bm, M_SLATE)

        bm = bm_cyl(0.136, 0.052, segs=44, bevel=0.012)
        aim(bm, AX_EL, P_el + AX_EL * (0.152 * side))
        new_child("Arm_Elbow_Pivot", "V2_ElbowDisc_" + tag, bm, M_MINT)
        bm = bm_cyl(0.044, 0.022, segs=24, bevel=0.006)
        aim(bm, AX_EL, P_el + AX_EL * (0.184 * side))
        new_child("Arm_Elbow_Pivot", "V2_ElbowDot_" + tag, bm, M_SLATE)

    # --- mint side panel on the +X flank ----------------------------------
    bm = bm_box((0.070, 1.060, 1.260), bevel=0.085, segs=4)
    translate(bm, Vector((0.918, 0.0, 1.640)))
    new_child("Machine_Body", "V2_SidePanel", bm, M_MINT)

    bm = bm_box((0.040, 0.760, 0.130), bevel=0.045, segs=3)
    translate(bm, Vector((0.958, 0.0, 1.120)))
    new_child("Machine_Body", "V2_SidePanelSlot", bm, M_MINT_D)

    # --- coral pill button on the front skirt -----------------------------
    # the skirt's flat front face sits at y=-0.8225 for z 0.335..0.665
    PILL_X, PILL_Z, PILL_R = -0.350, 0.465, 0.070
    bm = bm_capsule(PILL_R, 0.480, segs=30, rings=18)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.pi * 0.5, 3, 'Y'))
    for v in bm.verts:
        v.co.y *= 0.5
    translate(bm, Vector((PILL_X, -0.828, PILL_Z)))
    new_child("Machine_Body", "V2_FrontPill", bm, M_CORAL)

    # --- name badge: white band above the screen --------------------------
    # The strip left of the screen is only 0.34 wide, so the badge lives in the
    # white band between the screen frame top (z 2.462) and the shell bevel
    # (z 2.615). 0.600 x 0.175, left edge on x -0.72. The back face is buried
    # 0.020 into the shell so the bevel above cannot open a gap.
    NP_W, NP_H, NP_D = 0.600, 0.175, 0.050
    NP_X, NP_Z, NP_Y = -0.420, 2.564, -0.803
    NP_FRONT = NP_Y - NP_D * 0.5           # -0.828, the raised face
    NP_LEFT = NP_X - NP_W * 0.5 + 0.048    # -0.672, first glyph column
    bm = bm_plate(NP_W, NP_H, 0.030, NP_D, nc=4)
    translate(bm, Vector((NP_X, NP_Y, NP_Z)))
    new_child("Machine_Body", "V2_NamePlate", bm, M_CREAM)

    def np_row(name, z, h, row):
        """row = ((width, offset_from_NP_LEFT), ...); strips sit 0.008 proud."""
        parts = []
        for w, dx in row:
            p = bm_plate(w, h, min(w, h) * 0.30, 0.020, nc=2)
            translate(p, Vector((NP_LEFT + dx + w * 0.5, NP_FRONT + 0.002, z)))
            parts.append(p)
        new_child("Machine_Body", "V2_NamePlate_" + name, merge_bms(parts), M_MINT_D)

    # four fat blocks read as a wordmark, then two text lines split at a word gap
    np_row("Mark", NP_Z + 0.045, 0.034, ((0.050, 0.000), (0.050, 0.068),
                                         (0.050, 0.136), (0.050, 0.204)))
    np_row("Line1", NP_Z - 0.005, 0.015, ((0.280, 0.000), (0.160, 0.310)))
    np_row("Line2", NP_Z - 0.040, 0.015, ((0.205, 0.000), (0.125, 0.233)))

bpy.context.view_layer.update()

# frame the scene settings
sc = bpy.context.scene
sc.frame_start = 1
sc.frame_end = 327
sc.render.fps = 60

bpy.ops.wm.save_as_mainfile(filepath=DST)
print("SAVED " + DST)
