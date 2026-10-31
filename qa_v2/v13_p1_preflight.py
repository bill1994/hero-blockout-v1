"""P1 preflight: what P1 must not move, and the hopper bowl question, measured.

Section 12 Q1 of the design doc says the first P1 action is not modelling: narrowing
the shell from 2.32 to 1.80 turns the existing 1.37 hopper rim into 0.76 of body
width, so the hopper has to be re-checked against the Idea orb before anything is
shrunk. That pre-check as written asks whether the ball "still passes the hopper
mouth", which assumes a through-hole. It does not have one (measured: the hopper is a
closed shell, zero boundary edges, and the funnel runs to the axis). So this file
measures the real constraint instead:

  - the funnel's inner radius as a function of z (horizontal rays from the axis, so
    the double-walled shell cannot confuse inner with outer),
  - where a ball of radius R first touches that funnel,
  - where the orb actually is during the animation, and whether it ever sits in the
    bowl at all. The doc pins "hopper floor holds Idea at (0,0,2.600)"; if the orb
    never visits that point, that constraint is not load-bearing and should not be
    used to block a shrink.

Section 4.3 and section 12 also quote two different reference ratios (0.7778 rim vs
0.45 throat). Both are computed here against the current body and against the 1.80
target so they can stop being confused.

Read-only: opens the .blend, measures, writes JSON, never saves.

Usage:
    blender --background <blend> --python qa_v2/v13_p1_preflight.py -- \
        --out qa_v2/v13_p1_preflight.json [--tag v13p0.1] [--step 0.04]
"""

import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUT = arg("--out", "qa_v2/v13_p1_preflight.json")
TAG = arg("--tag", "unknown")
STEP = float(arg("--step", "0.04"))
TARGET_W = float(arg("--target-width", "1.80"))
BALL_CLEAR = float(arg("--ball-clearance", "0.02"))
AXIS_TOL = float(arg("--axis-tol", "0.06"))

sc = bpy.context.scene
sc.frame_set(1)
dg = bpy.context.evaluated_depsgraph_get()


def wbb(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    ev = o.evaluated_get(dg)
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for c in ev.bound_box:
        w = ev.matrix_world @ Vector(c)
        for i in range(3):
            lo[i] = min(lo[i], w[i])
            hi[i] = max(hi[i], w[i])
    return lo, hi


def box(name):
    bb = wbb(name)
    if bb is None:
        return None
    lo, hi = bb
    return {"min": [round(v, 4) for v in lo], "max": [round(v, 4) for v in hi],
            "dim": [round(hi[i] - lo[i], 4) for i in range(3)]}


# ------------------------------------------------------------ body + anchors ----
body = box("Machine_Body")
anchors = {n: box(n) for n in (
    "Machine_Body", "Arm_Base", "Arm_Mount", "Machine_Chute", "Machine_Hopper",
    "Machine_Base", "Machine_WindowGlow", "Idea", "Machine_Screws")}

frozen = {}
if anchors["Arm_Base"]:
    frozen["arm_root_min_x"] = anchors["Arm_Base"]["min"][0]
if anchors["Machine_Chute"]:
    frozen["chute_mouth_min_x"] = anchors["Machine_Chute"]["min"][0]
if body:
    frozen.update({"body_min_x": body["min"][0], "body_max_x": body["max"][0],
                   "body_width": body["dim"][0], "body_height": body["dim"][2]})

# ------------------------------------------------------- hopper funnel profile ----
o = bpy.data.objects.get("Machine_Hopper")
hopper = {"present": o is not None}
if o is not None:
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    zs = [(mw @ v.co).z for v in me.vertices]
    z0, z1 = min(zs), max(zs)
    ev.to_mesh_clear()

    def ray(origin, direction, dist=4.0):
        ok, loc, _n, _i, ob, _m = sc.ray_cast(dg, Vector(origin), Vector(direction),
                                              distance=dist)
        if not ok:
            return None, None
        return round(float(loc.x), 4), (ob.name if ob else "")

    prof = []
    z = z0 + 0.01
    while z < z1:
        rin, oin = ray((0.0, 0.0, z), (1.0, 0.0, 0.0))
        rout, oout = ray((2.5, 0.0, z), (-1.0, 0.0, 0.0))
        prof.append({"z": round(z, 3), "inner_r": rin, "inner_obj": oin,
                     "outer_r": rout, "outer_obj": oout})
        z += STEP

    # closed? count boundary edges of the evaluated mesh
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    open_edges = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    bm.free()
    ev.to_mesh_clear()

    inner_hits = [p for p in prof if p["inner_r"] is not None]
    hopper.update({
        "z_range": [round(z0, 4), round(z1, 4)],
        "open_boundary_edges": open_edges,
        "is_closed_shell": open_edges == 0,
        "funnel_plugged": bool(inner_hits and inner_hits[0]["inner_r"] >= 0.0
                               and inner_hits[0]["inner_r"] < 0.02),
        "profile": prof,
    })

# ------------------------------------------------------------ orb + its path ----
idea_r = round(max(anchors["Idea"]["dim"]) / 2.0, 4) if anchors["Idea"] else None

orb = {"radius": idea_r, "near_axis": [], "min_r_xy": None, "min_r_frame": None,
       "z_range": None}
if idea_r is not None:
    zmin, zmax = 1e9, -1e9
    for f in range(1, sc.frame_end + 1):
        sc.frame_set(f)
        d2 = bpy.context.evaluated_depsgraph_get()
        c = bpy.data.objects["Idea"].evaluated_get(d2).matrix_world.translation
        rxy = math.hypot(c.x, c.y)
        zmin, zmax = min(zmin, c.z), max(zmax, c.z)
        if orb["min_r_xy"] is None or rxy < orb["min_r_xy"]:
            orb["min_r_xy"] = round(rxy, 4)
            orb["min_r_frame"] = f
            orb["min_r_centre"] = [round(c.x, 4), round(c.y, 4), round(c.z, 4)]
        if rxy < AXIS_TOL:
            orb["near_axis"].append({"f": f, "c": [round(c.x, 4), round(c.y, 4),
                                                   round(c.z, 4)]})
    orb["z_range"] = [round(zmin, 4), round(zmax, 4)]

# ------------------------------------------------------------ bowl containment ----
bowl = {"ball_r": idea_r}
if idea_r is not None and hopper.get("profile"):
    need = idea_r
    # where a ball of radius R first touches the funnel going up from the axis
    contact = None
    for p in hopper["profile"]:
        if p["inner_r"] is not None and p["inner_r"] >= need:
            contact = p
            break
    bowl.update({
        "contact_z": contact["z"] if contact else None,
        "contact_inner_r": contact["inner_r"] if contact else None,
        "ball_bottom_at_contact": round(contact["z"] - idea_r, 4) if contact else None,
        "needs_inner_r_at_rest": round(need + BALL_CLEAR, 4),
    })
if orb.get("min_r_centre") and idea_r is not None:
    cz = orb["min_r_centre"][2]
    at = None
    for p in hopper["profile"]:
        if p["inner_r"] is not None and abs(p["z"] - (cz - idea_r)) < STEP:
            at = p
            break
    bowl.update({
        "orb_min_axis_z": cz,
        "orb_bottom_there": round(cz - idea_r, 4),
        "funnel_inner_r_near_orb_bottom": at["inner_r"] if at else None,
        "orb_seated_in_bowl": bool(at and at["inner_r"] is not None
                                   and at["inner_r"] <= idea_r + 0.05),
    })

# -------------------------------------------------------------- ratios ----
ratios = {}
if body and anchors["Machine_Hopper"]:
    rim_outer_r = None
    if hopper.get("profile"):
        outers = [p["outer_r"] for p in hopper["profile"] if p["outer_r"] is not None]
        rim_outer_r = max(outers) if outers else None
    if rim_outer_r:
        ratios = {
            "rim_dia": round(2 * rim_outer_r, 4),
            "rim_to_body_now": round(2 * rim_outer_r / body["dim"][0], 4),
            "rim_to_body_at_1_80": round(2 * rim_outer_r / TARGET_W, 4),
            "ref_rim_ratio_4_3": 0.7778,
            "ref_throat_ratio_12": 0.45,
            "rim_dia_implied_by_4_3_at_1_80": round(0.7778 * TARGET_W, 4),
        }

# -------------------------------------------------------------- window ----
window = {}
if anchors["Machine_WindowGlow"] and body:
    ww = anchors["Machine_WindowGlow"]["dim"][0]
    wh = anchors["Machine_WindowGlow"]["dim"][2]
    window = {
        "window_w": ww, "window_h": wh,
        "w_to_body_w_now": round(ww / body["dim"][0], 4),
        "w_to_body_w_at_1_80": round(ww / TARGET_W, 4),
        "p1_target_ratio": 0.64,
        "needed_window_w_at_1_80": round(0.64 * TARGET_W, 4),
        "stretch_factor_needed": round((0.64 * TARGET_W) / ww, 4),
    }

out = {
    "tag": TAG,
    "blend": os.path.abspath(bpy.data.filepath),
    "target_body_width": TARGET_W,
    "anchors": anchors,
    "frozen": frozen,
    "hopper": hopper,
    "orb": orb,
    "bowl": bowl,
    "ratios": ratios,
    "window": window,
    "body_material_slots": [
        s.material.name if s.material else None
        for s in bpy.data.objects["Machine_Body"].material_slots
    ] if bpy.data.objects.get("Machine_Body") else None,
}

os.makedirs(os.path.dirname(os.path.abspath(OUT)) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)

print("P1 PREFLIGHT %s" % TAG)
print("  body w=%.4f h=%.4f  x[%.4f %.4f]" % (
    body["dim"][0], body["dim"][2], body["min"][0], body["max"][0]))
print("  frozen arm_root_min_x=%s chute_mouth_min_x=%s" % (
    frozen.get("arm_root_min_x"), frozen.get("chute_mouth_min_x")))
h = hopper
print("  hopper z=%.3f..%.3f closed=%s plugged=%s open_edges=%s" % (
    h["z_range"][0], h["z_range"][1], h["is_closed_shell"], h["funnel_plugged"],
    h["open_boundary_edges"]))
print("  %-7s %-10s %-22s %-10s" % ("z", "inner_r", "hit", "outer_r"))
for p in h["profile"]:
    print("  %-7.3f %-10s %-22s %-10s" % (
        p["z"], p["inner_r"], p["inner_obj"], p["outer_r"]))
print("  orb r=%s  min r_xy=%s @f%s centre=%s" % (
    orb["radius"], orb["min_r_xy"], orb["min_r_frame"], orb.get("min_r_centre")))
print("  orb near axis (<%.3f): %d frames %s" % (
    AXIS_TOL, len(orb["near_axis"]),
    [x["f"] for x in orb["near_axis"]][:10]))
print("  bowl: contact_z=%s contact_inner_r=%s ball_bottom=%s seated=%s" % (
    bowl.get("contact_z"), bowl.get("contact_inner_r"),
    bowl.get("ball_bottom_at_contact"), bowl.get("orb_seated_in_bowl")))
print("  ratios: rim_dia=%s  rim/body_now=%s  rim/body@1.80=%s  (ref 0.7778)" % (
    ratios.get("rim_dia"), ratios.get("rim_to_body_now"), ratios.get("rim_to_body_at_1_80")))
print("  window: w=%.4f h=%.4f  now=%.4f  at1.80=%.4f  need_w=%.4f stretch=%.3f" % (
    window["window_w"], window["window_h"], window["w_to_body_w_now"],
    window["w_to_body_w_at_1_80"], window["needed_window_w_at_1_80"],
    window["stretch_factor_needed"]))
print("WROTE %s" % os.path.abspath(OUT))
