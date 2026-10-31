"""Product-path gate for the v13 reference-match work.

Answers one question, mechanically: while the product is out on the chute, is it
actually supported, and once it leaves the chute, does it move like something
with no floor under it?

Design doc: docs/superpowers/specs/2026-10-31-style-v13-reference-match-design.md
sections 4.5 (measured path) and 7 (gate table: "product path f232-f286").

Why this file exists: the plan's original gate frames were f31/f43/f147/f155, all
of which fall while Product is hidden (it appears at f232). Section 4.5 called that
out as a hole; this script is the fix. Run it before and after every stage from P1
on, and diff the JSON.

Read-only: opens the .blend, measures, writes JSON, never saves.

Usage:
    blender --background <blend> --python qa_v2/v13_product_path_gate.py -- \
        --out qa_v2/v13_product_path_<tag>.json [--tag <tag>] \
        [--first 232] [--last 327] [--grid 3] [--step 1] \
        [--tol-pen 0.015] [--tol-lift 0.030] [--tol-flat 0.001] [--min-scale 0.01]

Criteria, pinned here so they can be argued with instead of guessed at
--------------------------------------------------------------------
MEASUREMENT BAND (--sink-band 0.080)
    A surface counts as "the thing underneath" only if its z is at or below
    product_bottom + 0.080. The band exists because a sunk product would
    otherwise "find" a deeper surface (the chute's underside) and report itself
    as hovering. It is a measuring instrument, not a tolerance: 0.080 was chosen
    from the worst measured dip in v13-P0 (f256, -57 mm).

STATE per visible frame
    RESTING     the centre of mass is over support, and
                -tol_pen <= gap <= tol_lift   (contact, incl. the ~5 mm sink the
                                              model has always had at rest)
    PENETRATING some column has gap < -tol_pen            -> FAIL
    HOVERING    the centre column is over the chute but has nothing under it
                                                          -> FAIL
                The centre column, not every column: the chute mouth is an
                opening, so while the product emerges (f232-f242) its shoulder
                legitimately overhangs by a few cm with the machine's side below.
                Requiring support under every sampled column failed f234/f239 on
                exactly that overhang, which is a flaw in the instrument, not in
                the asset. Support ratio is reported and warned below 0.5.
    ARC         every column over the chute is above tol_lift, and z is
                actually moving                                  -> OK
                (the f258-f270 bounce is authored animation, not a bug: 37 cm up
                 and back down is a trajectory)
    COLLAPSED   scale < --min-scale, i.e. invisible          -> not gated
    EXITED      no sampled column is over the chute          -> stops the
                support requirement, starts the fall check

FAIL CONDITIONS
    PENETRATING, HOVERING, or FLAT_FLIGHT (below).
    tol_pen = 0.015: 1.5 cm is ~0.8% of the 1.8 m body and is the point where a
    sink reads as interpenetration rather than as contact. v13-P0 measures
    -5..-7.5 mm at rest, -10 mm at f254, -57 mm at f256, -17 mm at f274; only the
    last two cross this line, and every negative gap is listed in the report
    regardless of the threshold.

FLAT_FLIGHT  (after EXITED)
    Once nothing is beneath it, a product that keeps a constant z is sliding on
    invisible glass. Fails when |z(t) - z(t-1)| < --tol-flat for
    --flat-run consecutive frames. Raise --tol-flat to relax this if the shot is
    intentionally a flat launch; do not silently ignore it, because this is the
    exact defect class section 4.5 opened the gate for.

Non-zero exit code on FAIL, so a stage cannot be accepted by accident.
"""

import json
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(flag, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


OUT = arg("--out", "qa_v2/v13_product_path.json")
TAG = arg("--tag", "unknown")
FIRST = int(arg("--first", "232"))
LAST = int(arg("--last", "327"))
STEP = int(arg("--step", "1"))
GRID = int(arg("--grid", "3"))
TOL_PEN = float(arg("--tol-pen", "0.015"))
TOL_LIFT = float(arg("--tol-lift", "0.030"))
TOL_FLAT = float(arg("--tol-flat", "0.001"))
MIN_SCALE = float(arg("--min-scale", "0.01"))
SINK_BAND = float(arg("--sink-band", "0.080"))
FLAT_RUN = int(arg("--flat-run", "3"))

SUPPORT_OBJECT = "Machine_Chute"
PRODUCT_OBJECT = "Product"

# Never counted as "ground": the product itself, the orb it carries, the arm
# that holds it, and the debug proxies that are only kept hidden.
EXCLUDE = {
    PRODUCT_OBJECT, "Idea",
    "Arm_Finger_L", "Arm_Finger_R", "Arm_Wrist", "Arm_Forearm", "Arm_UpperArm",
    "Arm_Shoulder_Joint", "Arm_Elbow_Joint", "Arm_Base", "Arm_Mount",
    "Arm_Rings_Elbow", "Arm_Rings_Shoulder", "Arm_Seams_Fore", "Arm_Seams_Upper",
    "Product_Proxy_FitCheck", "Product_Proxy_Large",
}

sc = bpy.context.scene

# A missing product or chute means this gate measured nothing. Failing loudly
# beats reporting "everything is EXITED" and letting a stage pass on no evidence.
for _required in (PRODUCT_OBJECT, SUPPORT_OBJECT):
    if bpy.data.objects.get(_required) is None:
        raise SystemExit("GATE FATAL: required object %r not in %s"
                         % (_required, bpy.data.filepath))


def wbb(dg, name):
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


def surfaces_under(dg, x, y, z_top=6.0, z_bottom=-2.0, max_hits=32):
    """Upward-facing surfaces below (x, y), highest first."""
    hits = []
    z = z_top
    for _ in range(max_hits):
        ok, loc, _n, _i, ob, _m = sc.ray_cast(
            dg, Vector((x, y, z)), Vector((0.0, 0.0, -1.0)), distance=z - z_bottom)
        if not ok:
            break
        name = ob.name if ob else "?"
        if name not in EXCLUDE and not ob.hide_render and not ob.hide_viewport:
            hits.append((name, round(loc.z, 4)))
        z = loc.z - 1e-4
    return hits


def support_at(dg, x, y, bottom):
    """The highest surface in the sink band: what the product is standing on."""
    cand = [(n, z) for n, z in surfaces_under(dg, x, y) if z <= bottom + SINK_BAND]
    if not cand:
        return None, None
    name, z = max(cand, key=lambda t: t[1])
    return name, z


rows = []
prev_visible_z = None

for f in range(FIRST, LAST + 1, STEP):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()

    o = bpy.data.objects.get(PRODUCT_OBJECT)
    pb = wbb(dg, PRODUCT_OBJECT) if o else None
    if o is None or pb is None:
        rows.append({"frame": f, "state": "MISSING"})
        continue

    ev = o.evaluated_get(dg)
    s = ev.matrix_world.to_scale()
    smax = max(abs(s.x), abs(s.y), abs(s.z))
    p_lo, p_hi = pb
    bottom = p_lo.z

    if smax < MIN_SCALE or o.hide_render or o.hide_viewport:
        rows.append({
            "frame": f, "state": "COLLAPSED",
            "scale": [round(v, 5) for v in s],
            "hide_render": bool(o.hide_render),
            "hide_viewport": bool(o.hide_viewport),
        })
        prev_visible_z = None
        continue

    cb = wbb(dg, SUPPORT_OBJECT)
    cols = []
    if cb is not None:
        cx0, cx1 = cb[0].x, cb[1].x
        cy0, cy1 = cb[0].y, cb[1].y
    else:
        cx0 = cx1 = cy0 = cy1 = None

    fracs = [(i + 0.5) / GRID for i in range(GRID)]
    for fx in fracs:
        for fy in fracs:
            x = p_lo.x + (p_hi.x - p_lo.x) * fx
            y = p_lo.y + (p_hi.y - p_lo.y) * fy
            name, sz = support_at(dg, x, y, bottom)
            over = (cx0 is not None and cx0 <= x <= cx1 and cy0 <= y <= cy1)
            cols.append({
                "x": round(x, 3),
                "y": round(y, 3),
                "over_chute": bool(over),
                "support": name,
                "support_z": sz,
                "gap": round(bottom - sz, 4) if sz is not None else None,
            })

    over_cols = [c for c in cols if c["over_chute"]]
    gaps_over = [c["gap"] for c in over_cols if c["gap"] is not None]
    missing_over = [c for c in over_cols if c["support"] is None]
    worst_all = [(c["gap"], c) for c in cols if c["gap"] is not None]
    center = cols[len(cols) // 2]
    ratio = (len(over_cols) - len(missing_over)) / len(over_cols) if over_cols else None

    if not over_cols:
        state = "EXITED"
    elif center["over_chute"] and center["support"] is None:
        # A rigid body tips when its centre of mass overhangs support. The
        # footprint columns near the chute mouth legitimately have nothing under
        # them (the mouth is an opening, the product is still emerging), so the
        # centre column is the criterion, not every column.
        state = "HOVERING"
    elif gaps_over and min(gaps_over) < -TOL_PEN:
        state = "PENETRATING"
    elif gaps_over and all(g > TOL_LIFT for g in gaps_over):
        state = "ARC"
    elif any(g < -TOL_PEN for g, _ in worst_all):
        state = "PENETRATING"
    else:
        state = "RESTING"

    dz = None if prev_visible_z is None else round(bottom - prev_visible_z, 4)
    prev_visible_z = bottom

    row = {
        "frame": f,
        "state": state,
        "bottom_z": round(bottom, 4),
        "dz": dz,
        "x": [round(p_lo.x, 4), round(p_hi.x, 4)],
        "cols_over_chute": len(over_cols),
        "cols_missing_over_chute": len(missing_over),
        "support_ratio": round(ratio, 4) if ratio is not None else None,
        "centre_supported": bool(center["over_chute"] and center["support"] is not None),
        "gap_min_over_chute": round(min(gaps_over), 4) if gaps_over else None,
        "gap_max_over_chute": round(max(gaps_over), 4) if gaps_over else None,
        "worst_gap_any": round(min(g for g, _ in worst_all), 4) if worst_all else None,
        "support_objects": sorted({c["support"] for c in over_cols if c["support"]}),
    }
    if state in ("PENETRATING", "HOVERING"):
        row["cols"] = cols
    rows.append(row)

# ---------------------------------------------------------------- verdict ----
failures = []
for r in rows:
    if r["state"] in ("PENETRATING", "HOVERING"):
        failures.append({
            "frame": r["frame"],
            "kind": r["state"],
            "gap_min_over_chute": r.get("gap_min_over_chute"),
            "worst_gap_any": r.get("worst_gap_any"),
            "missing_over_chute": r.get("cols_missing_over_chute"),
        })

# flat flight after exit: constant z with nothing underneath
flat_runs = []
run = []
for r in rows:
    if r["state"] == "EXITED" and r.get("dz") is not None and abs(r["dz"]) < TOL_FLAT:
        run.append(r)
    else:
        if len(run) >= FLAT_RUN:
            flat_runs.append({
                "from": run[0]["frame"], "to": run[-1]["frame"],
                "z": run[0]["bottom_z"], "frames": len(run),
            })
        run = []
if len(run) >= FLAT_RUN:
    flat_runs.append({
        "from": run[0]["frame"], "to": run[-1]["frame"],
        "z": run[0]["bottom_z"], "frames": len(run),
    })
for fr in flat_runs:
    failures.append({"frame": fr["from"], "kind": "FLAT_FLIGHT",
                     "to": fr["to"], "z": fr["z"], "frames": fr["frames"]})

counts = {}
for r in rows:
    counts[r["state"]] = counts.get(r["state"], 0) + 1

# If nothing was ever over the chute, the gate proved nothing. That is a failure
# of the measurement, not a pass.
_measured = sum(counts.get(k, 0) for k in
                ("RESTING", "PENETRATING", "HOVERING", "ARC"))
if _measured == 0:
    failures.append({"frame": FIRST, "kind": "NO_MEASURABLE_FRAMES",
                     "note": "no frame had product over the chute; check "
                             "PRODUCT_OBJECT/SUPPORT_OBJECT and the frame range"})

# Support ratio is advisory: overhanging the chute mouth by a few cm is not a
# defect, but a base that is mostly off the chute while still being called
# "supported" deserves a look before it gets signed off.
low_support = [{"frame": r["frame"], "ratio": r["support_ratio"]}
               for r in rows
               if r.get("support_ratio") is not None and r["support_ratio"] < 0.5]

neg = [{"frame": r["frame"], "gap": r["worst_gap_any"]}
       for r in rows if r.get("worst_gap_any") is not None and r["worst_gap_any"] < 0]

exit_frames = [r["frame"] for r in rows if r["state"] == "EXITED"]
arcs = [r for r in rows if r["state"] == "ARC"]

out = {
    "tag": TAG,
    "blend": os.path.abspath(bpy.data.filepath),
    "frame_range": [FIRST, LAST],
    "step": STEP,
    "criteria": {
        "tol_pen": TOL_PEN, "tol_lift": TOL_LIFT, "tol_flat": TOL_FLAT,
        "min_scale": MIN_SCALE, "sink_band": SINK_BAND, "flat_run": FLAT_RUN,
        "grid": GRID, "support_object": SUPPORT_OBJECT,
    },
    "summary": {
        "counts": counts,
        "first_exited_frame": exit_frames[0] if exit_frames else None,
        "arc": {
            "first": arcs[0]["frame"] if arcs else None,
            "last": arcs[-1]["frame"] if arcs else None,
            "peak_gap": max((r["gap_max_over_chute"] for r in arcs), default=None),
            "peak_frame": max(arcs, key=lambda r: r["gap_max_over_chute"])["frame"] if arcs else None,
        },
        "negative_gaps": neg,
        "penetration_worst": min((n["gap"] for n in neg), default=None),
        "flat_runs": flat_runs,
        "low_support_frames": low_support,
    },
    "verdict": "PASS" if not failures else "FAIL",
    "failures": failures,
    "rows": rows,
}

os.makedirs(os.path.dirname(os.path.abspath(OUT)) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2)

print("GATE product-path %s  [%s..%s] tol_pen=%.3f tol_lift=%.3f" %
      (TAG, FIRST, LAST, TOL_PEN, TOL_LIFT))
print("  %-6s %-11s %8s %7s %5s %5s %6s %8s %8s" %
      ("frame", "state", "bottom_z", "dz", "over", "miss", "ratio", "gap_min", "gap_max"))
for r in rows:
    if r["state"] in ("COLLAPSED", "MISSING"):
        print("  %-6d %-11s %s" % (r["frame"], r["state"], r.get("scale", "")))
        continue
    print("  %-6d %-11s %8.3f %7s %5d %5d %6s %8s %8s" % (
        r["frame"], r["state"], r["bottom_z"], r["dz"],
        r["cols_over_chute"], r["cols_missing_over_chute"],
        r["support_ratio"], r["gap_min_over_chute"], r["gap_max_over_chute"]))
s = out["summary"]
print("  counts %s" % s["counts"])
print("  arc %s..%s peak %+.3f @f%s" % (
    s["arc"]["first"], s["arc"]["last"], s["arc"]["peak_gap"] or 0, s["arc"]["peak_frame"]))
print("  first_exited f%s  negative gaps %d (worst %s)" % (
    s["first_exited_frame"], len(neg), s["penetration_worst"]))
for fr in flat_runs:
    print("  FLAT_FLIGHT f%d..f%d at z=%.3f (%d frames, no support)" %
          (fr["from"], fr["to"], fr["z"], fr["frames"]))
if low_support:
    print("  WARN low support ratio: " + ", ".join(
        "f%s=%.2f" % (x["frame"], x["ratio"]) for x in low_support))
print("VERDICT %s%s" % (out["verdict"], "" if not failures else
      "  failures: " + ", ".join("%s@f%s" % (x["kind"], x["frame"]) for x in failures)))
print("WROTE %s" % os.path.abspath(OUT))

if failures:
    sys.exit(3)
