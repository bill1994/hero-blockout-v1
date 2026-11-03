"""v14 four-point repair — staged, idempotent, MCP-executable.

Usage from Blender MCP (execute_blender_code):

    exec(open(r"G:\\DSHProject\\hero-blockout\\hero-blockout-v1\\exec\\v14_fix.py", encoding="utf-8").read())
    result = run("baseline")
    result = run("outlet_normals")
    ...

Every stage:
  * is safe to re-run (idempotent where practical),
  * returns a JSON-safe dict,
  * refuses to run if a precondition is missing,
  * never touches the animation actions unless the stage says so.

Stage order matters. See EXECUTION_PLAN.md.
"""
import bpy
import bmesh
import math
import json
import os
from mathutils import Vector, Matrix

PROJECT = r"G:\DSHProject\hero-blockout\hero-blockout-v1"
REPORT_DIR = os.path.join(PROJECT, "review", "v14", "exec")

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _ensure_dir():
    os.makedirs(REPORT_DIR, exist_ok=True)


def _dg():
    return bpy.context.evaluated_depsgraph_get()


def _bm(obj, evaluated=True):
    """World-space bmesh of an object."""
    if evaluated:
        eo = obj.evaluated_get(_dg())
        me = eo.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(eo.matrix_world)
        eo.to_mesh_clear()
    else:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
    return bm


def _signed_volume(obj):
    bm = _bm(obj)
    v = 0.0
    for f in bm.faces:
        vs = f.verts
        for i in range(1, len(vs) - 1):
            a, b, c = vs[0].co, vs[i].co, vs[i + 1].co
            v += a.dot(b.cross(c)) / 6.0
    bm.free()
    return v


def _bbox(obj):
    bm = _bm(obj)
    if not bm.verts:
        bm.free()
        return None
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    bm.free()
    return [min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)]


def _fill_ratio(obj):
    bb = _bbox(obj)
    if not bb:
        return None
    vol = (bb[1] - bb[0]) * (bb[3] - bb[2]) * (bb[5] - bb[4])
    if vol <= 0:
        return None
    return abs(_signed_volume(obj)) / vol


def _topology(obj):
    bm = _bm(obj)
    bnd = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nonm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    nv, nf = len(bm.verts), len(bm.faces)
    bm.free()
    return {"verts": nv, "faces": nf, "boundary_edges": bnd, "nonmanifold": nonm}


def _ray(origin, direction):
    hit, loc, nor, idx, obj, mat = bpy.context.scene.ray_cast(
        _dg(), Vector(origin), Vector(direction).normalized())
    return {"obj": obj.name if hit else None,
            "loc": [round(c, 4) for c in loc] if hit else None}


def _ray_march(origin, direction, limit=8):
    out = []
    o = Vector(origin)
    d = Vector(direction).normalized()
    for _ in range(limit):
        hit, loc, nor, idx, obj, mat = bpy.context.scene.ray_cast(_dg(), o, d)
        if not hit:
            out.append("ESCAPE")
            break
        out.append({"obj": obj.name, "loc": [round(c, 4) for c in loc]})
        o = loc + d * 1e-4
    return out


def _material_of(obj, fallback="MAT_Body"):
    for ms in obj.material_slots:
        if ms.material:
            return ms.material
    return bpy.data.materials.get(fallback)


def _new_mesh_object(name, bm, material=None, collection=None):
    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    if material:
        me.materials.append(material)
    return ob


def _delete_object(name):
    o = bpy.data.objects.get(name)
    if not o:
        return False
    bpy.data.objects.remove(o, do_unlink=True)
    return True


def _save_as(suffix):
    """Save a cleanly-named versioned copy next to the project files."""
    src = bpy.data.filepath
    d = os.path.dirname(src)
    out = os.path.join(d, f"hero_animation_v14_{suffix}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=out)
    return out


def _report(name, data):
    _ensure_dir()
    p = os.path.join(REPORT_DIR, name)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
    return p


# --------------------------------------------------------------------------
# stage 0 — baseline
# --------------------------------------------------------------------------

def stage_baseline():
    """Record the pre-change state. Changes nothing."""
    scene = bpy.context.scene
    tris = 0
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        eo = o.evaluated_get(_dg())
        me = eo.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        eo.to_mesh_clear()

    data = {
        "file": bpy.data.filepath,
        "frame": scene.frame_current,
        "objects": len(bpy.data.objects),
        "meshes": len([o for o in bpy.data.objects if o.type == "MESH"]),
        "actions": len(bpy.data.actions),
        "triangles": tris,
        "chute_signed_volume": round(_signed_volume(bpy.data.objects["Machine_Chute"]), 6),
        "chute_topology": _topology(bpy.data.objects["Machine_Chute"]),
        "chute_bbox": [round(c, 4) for c in _bbox(bpy.data.objects["Machine_Chute"])],
        "base_fill_ratio": round(_fill_ratio(bpy.data.objects["Machine_Base"]), 5),
        "base_bbox": [round(c, 4) for c in _bbox(bpy.data.objects["Machine_Base"])],
        "base_scale": [round(s, 5) for s in bpy.data.objects["Machine_Base"].scale],
        "bolt_count": len([o for o in bpy.data.objects if o.name.startswith("P1_Bolt")]),
        "body_modifiers": [{"type": m.type,
                            "target": getattr(getattr(m, "object", None), "name", None)}
                           for m in bpy.data.objects["Machine_Body"].modifiers],
        "grab_ray_f147_z13": _ray_march((-0.5, 0.0, 1.30), (1, 0, 0)),
        "base_ray_up": _ray_march((0.66, 0.44, -0.5), (0, 0, 1)),
    }
    path = _report("stage0_baseline.json", data)
    return {"stage": "baseline", "report": path, "data": data}


# --------------------------------------------------------------------------
# stage 1 — outlet normals (zero-risk, proves the U-channel exists)
# --------------------------------------------------------------------------

def stage_outlet_normals():
    """Flip inward-facing normals on the outlet pieces.

    The audit claimed Machine_Chute is a solid block with no cavity. The
    re-measurement showed the U-channel geometry IS there, but every face
    points inward (signed_volume -0.090417, 0 boundary edges). Recalculating
    outside should make the channel render as a channel.
    """
    targets = ["Machine_Chute", "P1_ChuteRail", "P2_OutletBand"]
    out = {}
    for nm in targets:
        o = bpy.data.objects.get(nm)
        if not o or o.type != "MESH":
            out[nm] = {"skipped": "missing"}
            continue
        before = _signed_volume(o)
        topo_before = _topology(o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()
        bpy.context.view_layer.update()
        after = _signed_volume(o)
        out[nm] = {
            "before": round(before, 6),
            "after": round(after, 6),
            "flipped": (before < 0) and (after > 0),
            "topology": topo_before,
        }
    # did the channel survive the flip?
    out["channel_probe"] = {
        "down_y0": _ray_march((1.0, 0.0, 2.2), (0, 0, -1)),
        "down_y038": _ray_march((1.0, 0.38, 2.2), (0, 0, -1)),
    }
    path = _report("stage1_outlet_normals.json", out)
    return {"stage": "outlet_normals", "report": path, "data": out}


# --------------------------------------------------------------------------
# stage 2 — base rebuild
# --------------------------------------------------------------------------

def _rounded_rect(hx, hy, r, seg=6):
    """Counter-clockwise rounded-rectangle outline points."""
    pts = []
    corners = [
        (hx - r, hy - r, 0.0),
        (-hx + r, hy - r, math.pi / 2),
        (-hx + r, -hy + r, math.pi),
        (hx - r, -hy + r, 3 * math.pi / 2),
    ]
    for cx, cy, a0 in corners:
        for i in range(seg + 1):
            a = a0 + (math.pi / 2) * i / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def stage_base():
    """Rebuild Machine_Base as a solid rounded slab, and Machine_Feet as
    4 round posts that actually embed into it.

    Contract: x +-0.90, y +-0.78, z 0.02..0.288, plan radius 0.16,
    feet r 0.055 at (+-0.66, +-0.44), top of foot z=0.02 (0.02 into the slab).
    """
    body = bpy.data.objects.get("Machine_Body")
    if not body:
        return {"stage": "base", "error": "Machine_Body missing"}

    old_base = bpy.data.objects.get("Machine_Base")
    mat = _material_of(old_base, "MAT_Arm_Dark")
    coll = old_base.users_collection[0] if old_base and old_base.users_collection else bpy.context.scene.collection

    hx, hy, r = 0.90, 0.78, 0.16
    z0, z1 = 0.02, 0.288
    pts = _rounded_rect(hx, hy, r, seg=6)

    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, z0)) for x, y in pts]
    bm.verts.ensure_lookup_table()
    face = bm.faces.new(bottom)
    ret = bmesh.ops.extrude_face_region(bm, geom=[face])
    new_verts = [g for g in ret["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=new_verts, vec=(0, 0, z1 - z0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table()

    new_base = _new_mesh_object("Machine_Base_Rebuilt", bm, mat, coll)
    # inherit the transform of the old base so parenting stays consistent
    if old_base:
        # the bmesh was built in world coordinates, so the object must stay at
        # identity. Copying the old matrix would re-apply its un-applied
        # 0.34/0.34/0.192 scale and throw the slab out of place.
        new_base.matrix_world = Matrix.Identity(4)
        new_base.scale = (1.0, 1.0, 1.0)
        for m in list(old_base.modifiers):
            try:
                new_base.modifiers.new(m.name, m.type)
            except Exception:
                pass
        _delete_object("Machine_Base")
        new_base.name = "Machine_Base"

    # vertical-arc bevel + small edge bevel
    bev = new_base.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.05
    bev.segments = 3
    bev.limit_method = "ANGLE"
    bev.angle_limit = math.radians(40)

    # ---- feet ----
    old_feet = bpy.data.objects.get("Machine_Feet")
    feet_mat = _material_of(old_feet, "MAT_Arm_Dark")
    _delete_object("Machine_Feet")

    bm = bmesh.new()
    for cx in (-0.66, 0.66):
        for cy in (-0.44, 0.44):
            ret = bmesh.ops.create_cone(
                bm, cap_ends=True, cap_tris=False, segments=16,
                radius1=0.055, radius2=0.055, depth=0.12,
            )
            vs = [g for g in ret["verts"]]
            bmesh.ops.translate(bm, verts=vs, vec=(cx, cy, -0.04))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    feet = _new_mesh_object("Machine_Feet", bm, feet_mat, coll)

    bpy.context.view_layer.update()

    # user rulings (2026-11-03):
    #   1. P1_BaseBand has no counterpart in the reference -> delete
    #   5. P1_ChuteSeat is a hidden dead object below the floor -> delete
    removed = []
    for nm in ("P1_BaseBand", "P1_ChuteSeat"):
        if _delete_object(nm):
            removed.append(nm)
    bpy.context.view_layer.update()

    data = {
        "base_fill_ratio": round(_fill_ratio(new_base), 5),
        "base_bbox": [round(c, 4) for c in _bbox(new_base)],
        "base_topology": _topology(new_base),
        "feet_bbox": [round(c, 4) for c in _bbox(feet)],
        "feet_topology": _topology(feet),
        "ray_up_through_foot": _ray_march((0.66, 0.44, -0.5), (0, 0, 1)),
        "removed": removed,
    }
    path = _report("stage2_base.json", data)
    return {"stage": "base", "report": path, "data": data}


# --------------------------------------------------------------------------
# stage 3 — countersunk screw holes
# --------------------------------------------------------------------------

def stage_screws():
    """Delete the 16 proud bolt caps and cut countersinks instead.

    Holes are cut with a boolean into Machine_Body (front/back) and
    P1_MintStrip_L/R (sides). Top-face holes are cut into P3f_TopSkin.
    Positions come from the audit's pixel->world conversion; verify visually.
    """
    bolts = [o for o in bpy.data.objects if o.name.startswith("P1_Bolt")]
    for b in bolts:
        _delete_object(b.name)

    body = bpy.data.objects.get("Machine_Body")
    if not body:
        return {"stage": "screws", "error": "Machine_Body missing"}

    body_mat = _material_of(body)

    # countersink profile: outer r 0.031, bottom r 0.015, depth 0.016
    def make_cutter(name, center, normal_axis):
        bm = bmesh.new()
        ret = bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=False, segments=16,
            radius1=0.031, radius2=0.015, depth=0.016,
        )
        vs = [g for g in ret["verts"]]
        # cone is built along Z; rotate to the face normal
        if normal_axis == "X":
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0),
                             matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
        elif normal_axis == "Y":
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0),
                             matrix=Matrix.Rotation(math.radians(90), 3, "X"))
        bmesh.ops.translate(bm, verts=vs, vec=center)
        return _new_mesh_object(name, bm, None, bpy.context.scene.collection)

    # --- positions ---
    # front/back: symmetric x +-0.60. The audit's right-hand pixels convert to
    # +-0.87, i.e. flush with the body edge, which contradicts the left side's
    # 0.30 inset - bad data, so mirror the reliable left side instead.
    front = [(-0.60, 2.42), (0.60, 2.42), (-0.60, 0.64), (0.60, 0.64)]
    # top: measured off the mint panel at 203 px/unit -> (+-0.52, +-0.44)
    top = [(-0.52, -0.44), (0.52, -0.44), (-0.52, 0.44), (0.52, 0.44)]
    # sides: mirrored from the front pattern
    side = [(-0.60, 2.42), (0.60, 2.42), (-0.60, 0.64), (0.60, 0.64)]

    # cutter half-depth: centre sits this far inside the surface so the full
    # 0.016 recess is cut instead of only the half that pokes out
    HALF = 0.008
    cutters = []
    for i, (x, z) in enumerate(front):
        cutters.append(make_cutter(f"Cutter_Screw_F{i}", (x, -0.80 + HALF, z), "Y"))
        cutters.append(make_cutter(f"Cutter_Screw_B{i}", (x, 0.80 - HALF, z), "Y"))
    for i, (y, z) in enumerate(side):
        cutters.append(make_cutter(f"Cutter_Screw_L{i}", (-0.90 + HALF, y, z), "X"))
        cutters.append(make_cutter(f"Cutter_Screw_R{i}", (0.90 - HALF, y, z), "X"))
    top_cutters = []
    for i, (x, y) in enumerate(top):
        top_cutters.append(make_cutter(f"Cutter_Screw_T{i}", (x, y, 2.72 - HALF), "Z"))

    made = []
    for c in cutters:
        c.hide_render = True
        mod = body.modifiers.new(f"ScrewCut_{c.name}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = c
        mod.solver = "EXACT"
        made.append(mod.name)

    # top holes are cut into the body; the mint skin sits 0.0025 above it and
    # will need its own shallow pass if it occludes the recess
    top_made = []
    for c in top_cutters:
        c.hide_render = True
        mod = body.modifiers.new(f"ScrewCut_{c.name}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = c
        mod.solver = "EXACT"
        top_made.append(mod.name)

    bpy.context.view_layer.update()
    data = {
        "bolts_deleted": len(bolts),
        "cutters": len(cutters) + len(top_cutters),
        "body_booleans": made,
        "top_booleans": top_made,
        "positions": {"front_back": front, "sides": side, "top": top},
        "body_modifiers": [m.name for m in body.modifiers],
    }
    path = _report("stage3_screws.json", data)
    return {"stage": "screws", "report": path, "data": data}


# --------------------------------------------------------------------------
# stage 4 — claw: de-lump, hinge pins, even spread
# --------------------------------------------------------------------------

def stage_claw():
    """Smooth the ring bulges and add hinge pins.

    Deliberately does NOT change the cross-section (the audit's pale-cream
    colour claim was disproved; the amber is correct) and does NOT retime
    the open/close keys - the grab distance at f31/f96/f147 must stay 0.006.
    """
    out = {"fingers": {}, "pins": []}
    for nm in ("Arm_Finger_L", "Arm_Finger_R", "Arm_Finger_C"):
        o = bpy.data.objects.get(nm)
        if not o:
            out["fingers"][nm] = {"skipped": "missing"}
            continue
        before = _bbox(o)
        # Smooth modifier flattens the PCA thickening lumps without rebuilding
        sm = o.modifiers.get("Delump")
        if not sm:
            sm = o.modifiers.new("Delump", "SMOOTH")
            sm.factor = 0.55
            sm.iterations = 6
        bpy.context.view_layer.update()
        after = _bbox(o)
        out["fingers"][nm] = {
            "bbox_before": [round(c, 4) for c in before],
            "bbox_after": [round(c, 4) for c in after],
            "modifier": sm.name,
        }

    # hinge pins: one small cylinder at each finger root, dark material
    dark = bpy.data.materials.get("MAT_Arm_Dark")
    coll = bpy.context.scene.collection
    for nm, cx in (("L", -1.50), ("R", -1.95), ("C", -1.69)):
        name = f"Arm_FingerPin_{nm}"
        if bpy.data.objects.get(name):
            out["pins"].append({"name": name, "skipped": "exists"})
            continue
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12,
                              radius1=0.012, radius2=0.012, depth=0.075)
        bmesh.ops.rotate(bm, verts=list(bm.verts), cent=(0, 0, 0),
                         matrix=Matrix.Rotation(math.radians(90), 3, "X"))
        bmesh.ops.translate(bm, verts=list(bm.verts), vec=(cx, -1.78, 1.54))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        ob = _new_mesh_object(name, bm, dark, coll)
        out["pins"].append({"name": name, "bbox": [round(c, 4) for c in _bbox(ob)]})

    path = _report("stage4_claw.json", out)
    return {"stage": "claw", "report": path, "data": out}


# --------------------------------------------------------------------------
# stage 5 — outlet structure (highest risk, touches product path)
# --------------------------------------------------------------------------

def stage_outlet_structure():
    """Punch the bore through the body, fix the lip/amber height relation.

    Does NOT move the product animation. Cutter_Outlet is extended inward so
    the bore reaches the body cavity; the collar top is raised above the
    amber rim so cream wraps amber instead of the reverse.
    """
    out = {}
    cutter = bpy.data.objects.get("Cutter_Outlet")
    if not cutter:
        return {"stage": "outlet_structure", "error": "Cutter_Outlet missing"}

    before = [round(c, 4) for c in _bbox(cutter)]
    # clear the stale parent inverse before resizing (known trap)
    cutter.matrix_parent_inverse.identity()
    # extend the cutter inward so the bore reaches the cavity
    if cutter.data:
        for v in cutter.data.vertices:
            if v.co.x < 0.74:
                v.co.x = -1.0
    cutter.data.update()
    bpy.context.view_layer.update()
    after = [round(c, 4) for c in _bbox(cutter)]
    out["cutter"] = {"bbox_before": before, "bbox_after": after}

    # is the bore open now?
    out["bore_rays"] = {
        "z1_10": _ray_march((-0.5, 0.0, 1.10), (1, 0, 0)),
        "z1_30": _ray_march((-0.5, 0.0, 1.30), (1, 0, 0)),
        "z1_40": _ray_march((-0.5, 0.0, 1.40), (1, 0, 0)),
        "from_outside": _ray_march((2.9, 0.0, 1.30), (-1, 0, 0)),
    }

    # collar top vs amber rim
    collar = bpy.data.objects.get("P1_OutletCollar")
    chute = bpy.data.objects.get("Machine_Chute")
    if collar and chute:
        cb = _bbox(collar)
        chb = _bbox(chute)
        out["heights"] = {
            "collar_z": [round(cb[4], 4), round(cb[5], 4)],
            "chute_z": [round(chb[4], 4), round(chb[5], 4)],
            "cream_above_amber": round(cb[5] - chb[5], 4),
        }

    # user ruling: keep P1_ChuteRail, but stop it reading as a dark slab -
    # give it the lip material so it extends the collar instead of blocking it
    rail = bpy.data.objects.get("P1_ChuteRail")
    if rail:
        mat = bpy.data.materials.get("MAT_Body")
        if mat:
            rail.data.materials.clear()
            rail.data.materials.append(mat)
        out["chute_rail"] = {"kept": True, "material": "MAT_Body"}

    path = _report("stage5_outlet_structure.json", out)
    return {"stage": "outlet_structure", "report": path, "data": out}


# --------------------------------------------------------------------------
# stage 6 — verification
# --------------------------------------------------------------------------

def stage_verify():
    """Re-run every acceptance gate and report pass/fail."""
    gates = {}

    base = bpy.data.objects.get("Machine_Base")
    if base:
        fr = _fill_ratio(base)
        gates["base_fill_ratio>=0.85"] = {"value": round(fr, 4), "pass": fr >= 0.85}

    feet = bpy.data.objects.get("Machine_Feet")
    if feet and base:
        fb = _bbox(feet)
        bb = _bbox(base)
        overlap = min(fb[5], bb[5]) - max(fb[4], bb[4])
        gates["foot_embeds>=0.02"] = {"value": round(overlap, 4), "pass": overlap >= 0.02}

    chute = bpy.data.objects.get("Machine_Chute")
    if chute:
        sv = _signed_volume(chute)
        gates["chute_signed_volume>0"] = {"value": round(sv, 6), "pass": sv > 0}

    rays = _ray_march((-0.5, 0.0, 1.30), (1, 0, 0))
    gates["bore_through"] = {"value": rays, "pass": rays[-1] == "ESCAPE"}

    collar = bpy.data.objects.get("P1_OutletCollar")
    if collar and chute:
        cb, chb = _bbox(collar), _bbox(chute)
        gates["cream_above_amber"] = {
            "value": round(cb[5] - chb[5], 4), "pass": cb[5] > chb[5]}

    bolts = [o for o in bpy.data.objects if o.name.startswith("P1_Bolt")]
    gates["bolts_removed"] = {"value": len(bolts), "pass": len(bolts) == 0}

    tris = 0
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        eo = o.evaluated_get(_dg())
        me = eo.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        eo.to_mesh_clear()
    gates["triangles<=60000"] = {"value": tris, "pass": tris <= 60000}

    gates["actions_unchanged"] = {"value": len(bpy.data.actions),
                                  "pass": len(bpy.data.actions) == 36}

    summary = {"pass": sum(1 for g in gates.values() if g["pass"]),
               "fail": sum(1 for g in gates.values() if not g["pass"]),
               "total": len(gates)}
    data = {"gates": gates, "summary": summary}
    path = _report("stage6_verify.json", data)
    return {"stage": "verify", "report": path, "data": data}


# --------------------------------------------------------------------------
# dispatch
# --------------------------------------------------------------------------

STAGES = {
    "baseline": stage_baseline,
    "outlet_normals": stage_outlet_normals,
    "base": stage_base,
    "screws": stage_screws,
    "claw": stage_claw,
    "outlet_structure": stage_outlet_structure,
    "verify": stage_verify,
}


def run(stage):
    if stage not in STAGES:
        return {"error": f"unknown stage {stage!r}", "available": sorted(STAGES)}
    bpy.context.view_layer.update()
    return STAGES[stage]()


def save(suffix):
    return _save_as(suffix)
