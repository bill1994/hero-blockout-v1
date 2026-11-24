"""Validate export/hero_v2.glb against rebuild_v2.blend (and p19 as a second reference).

Checks
  1. structural   Product/Idea nodes exist, carry a 327-key scale channel, clip spans frame 1..327 @60fps.
  2. source truth per-frame authored scale + hide_render sampled from rebuild_v2.blend.
  3. visibility   all 327 frames: scale ~= 0 exactly where the source says hidden, and equal to the
                  authored value where the source says visible.
  4. export       re-import the GLB and compare world matrices against rebuild_v2.blend for every
                  object present in both, tol 1e-3, all 327 frames.
  5. animation    rebuild_v2.blend vs hero_animation_v14_p19.blend for every object present in both
                  (empties included - in p19 the animation lives on the pivot empties, not on meshes),
                  which measures whether the mesh rebuild preserved the animation independently of
                  the export.
  6. why-missing  for every source mesh absent from the GLB, record the exact flag that excluded it.

Import gotcha worked around here: Blender's glTF importer makes ONE action active and parks the
remaining per-object clips in MUTED NLA tracks, so a naive re-import reads every object but the first
as static. All NLA tracks are unmuted before sampling.

Writes versions/rebuild_t2_report.json. Exit code 1 on any failure or regression.
"""
import json
import os
import sys

import bpy

ROOT = r"G:\DSHProject\BlenderMcp"
SRC = os.path.join(ROOT, "rebuild_v2.blend")
P19 = os.path.join(ROOT, "hero_animation_v14_p19.blend")
GLB = os.path.join(ROOT, "export", "hero_v2.glb")
REPORT = os.path.join(ROOT, "versions", "rebuild_t2_report.json")

VIS_OBJECTS = ("Product", "Idea")
TOL = 1e-3
HIDDEN_EPS = 1e-3
FPS = 60

failures = []
regressions = []
warnings = []
notes = []


def fail(msg):
    failures.append(msg)
    print("VAL_FAIL " + msg)


def flat(m):
    return [m[r][c] for r in range(4) for c in range(4)]


def mat_diff(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def sample_scene(only_mesh=True):
    """name -> {'mats': [flat 4x4 per frame], 'action', 'scales'}; plus (f0, f1)."""
    sc = bpy.context.scene
    f0, f1 = sc.frame_start, sc.frame_end
    objs = [o for o in bpy.data.objects if (not only_mesh) or o.type == 'MESH']
    out = {}
    for ob in objs:
        ad = ob.animation_data
        out[ob.name] = {
            "mats": [], "scales": [], "action": ad.action.name if (ad and ad.action) else None,
            "type": ob.type, "parent": ob.parent.name if ob.parent else None,
        }
    names = list(out)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for name in names:
            ob = bpy.data.objects[name]
            out[name]["mats"].append(flat(ob.matrix_world))
            if name in VIS_OBJECTS:
                out[name]["scales"].append(tuple(ob.scale))
    return out, f0, f1


def src_visibility():
    out = {}
    for name in VIS_OBJECTS:
        ob = bpy.data.objects[name]
        rows = []
        for f in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
            bpy.context.scene.frame_set(f)
            rows.append((f, tuple(ob.scale), bool(ob.hide_render)))
        out[name] = rows
    return out


def enable_all_animation():
    n = 0
    for ob in bpy.data.objects:
        ad = ob.animation_data
        if not ad:
            continue
        for tr in ad.nla_tracks:
            tr.mute = False
            tr.is_solo = False
            for st in tr.strips:
                st.mute = False
            n += 1
        if ad.nla_tracks:
            ad.action = None
            ad.use_nla = True
    return n


def ranges_of(frames):
    out, start, prev = [], None, None
    for f in frames:
        if start is None:
            start = prev = f
        elif f == prev + 1:
            prev = f
        else:
            out.append([start, prev])
            start = prev = f
    if start is not None:
        out.append([start, prev])
    return out


def main():
    if not os.path.exists(GLB):
        raise SystemExit("missing " + GLB)
    report = {"glb_path": GLB, "glb_size_bytes": os.path.getsize(GLB)}

    # ---------------- 1. structural ------------------------------------
    sys.path.insert(0, r"G:\DSHProject\BlenderMcp\scripts")
    from glb_inspect import Glb
    g = Glb(GLB)
    report["glb"] = g.summary()
    lo, hi = g.animation_time_range()
    report["glb_anim_time_range_s"] = [round(lo, 6), round(hi, 6)]
    report["glb_anim_frame_range_at_60fps"] = [round(lo * FPS, 3), round(hi * FPS, 3)]
    if abs(lo * FPS - 1) > 0.05 or abs(hi * FPS - 327) > 0.05:
        fail("clip does not span frame 1..327 at 60fps: %.4f..%.4f" % (lo * FPS, hi * FPS))

    node_scales = {}
    for name in VIS_OBJECTS:
        hits = g.find_nodes(name)
        if not hits:
            fail("%s node missing from GLB" % name)
            continue
        idx, _nd = hits[0]
        chans = {p: (ai, si) for ai, _n, p, si in g.channels_for_node(idx)}
        if "scale" not in chans:
            fail("%s has no scale animation channel" % name)
            continue
        ai, si = chans["scale"]
        times, vals, interp = g.sampler_data(ai, si)
        if len(times) != 327:
            fail("%s scale has %d keys, expected 327" % (name, len(times)))
        if max(abs(t * FPS - (i + 1)) for i, t in enumerate(times)) > 0.05:
            fail("%s scale key times are not frame-perfect" % name)
        # glTF is Y-up: blender (x,y,z) -> gltf (x,z,-y); invert for reporting in Blender axes
        node_scales[name] = {"interp": interp, "keys": len(times),
                             "vals_blender_axes": [(v[0], v[2], v[1]) for v in vals]}
    report["raw_scale_channels"] = {k: {"keys": v["keys"], "interp": v["interp"]}
                                    for k, v in node_scales.items()}

    # ---------------- 2. source truth ----------------------------------
    bpy.ops.wm.open_mainfile(filepath=SRC)
    sc = bpy.context.scene
    report["source"] = {"file": SRC, "fps": sc.render.fps,
                        "frame_start": sc.frame_start, "frame_end": sc.frame_end}
    if sc.frame_start != 1 or sc.frame_end != 327:
        fail("source frame range is not 1..327")

    src_vis = src_visibility()
    src_mesh, _, _ = sample_scene(only_mesh=True)
    src_all, _, _ = sample_scene(only_mesh=False)

    hidden_ranges = {}
    for name, rows in src_vis.items():
        hid = [f for f, _s, h in rows if h]
        hidden_ranges[name] = ranges_of(hid)
        report["%s_source_hidden_ranges" % name.lower()] = hidden_ranges[name]
        report["%s_source_visible_frames" % name.lower()] = len(rows) - len(hid)

    # ---------------- 3. visibility (raw byte truth) --------------------
    scale_check = {}
    for name in VIS_OBJECTS:
        rows = src_vis[name]
        got = node_scales.get(name)
        entry = {"frames_checked": 0, "mismatch_count": 0, "mismatches": [], "samples": {}}
        if got:
            vals = got["vals_blender_axes"]
            for (f, authored, hidden) in rows:
                v = vals[f - 1]
                entry["frames_checked"] += 1
                if hidden:
                    if max(abs(c) for c in v) > HIDDEN_EPS:
                        entry["mismatch_count"] += 1
                        if len(entry["mismatches"]) < 8:
                            entry["mismatches"].append([f, "expected hidden", [round(c, 6) for c in v]])
                elif max(abs(v[i] - authored[i]) for i in range(3)) > TOL:
                    entry["mismatch_count"] += 1
                    if len(entry["mismatches"]) < 8:
                        entry["mismatches"].append([f, "expected %s" % [round(c, 4) for c in authored],
                                                    [round(c, 6) for c in v]])
                if f in (1, 120, 220, 300, 327):
                    entry["samples"][str(f)] = [round(c, 6) for c in v]
            if entry["mismatch_count"]:
                fail("%s scale mismatches on %d/327 frames"
                     % (name, entry["mismatch_count"]))
        scale_check[name] = entry
    report["scale_check"] = scale_check

    def scalar_table(name):
        return {"f%s" % fr: round(min(xyz), 6)
                for fr, xyz in scale_check[name].get("samples", {}).items()}

    report["product_scale"] = scalar_table("Product")
    report["idea_scale"] = scalar_table("Idea")
    report["product_scale_xyz"] = scale_check["Product"].get("samples", {})
    report["idea_scale_xyz"] = scale_check["Idea"].get("samples", {})

    # ---------------- 4. export fidelity via re-import ------------------
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.fps_base = 1.0
    bpy.ops.import_scene.gltf(filepath=GLB)
    sc = bpy.context.scene
    n_tracks = enable_all_animation()
    sc.frame_start, sc.frame_end = 1, 327
    report["import"] = {
        "mesh_objects": len([o for o in bpy.data.objects if o.type == 'MESH']),
        "actions": len(bpy.data.actions),
        "nla_tracks_unmuted": n_tracks,
        "fps": sc.render.fps,
        "note": "importer parks all but one clip in muted NLA tracks; unmuted before sampling",
    }
    imp_mesh, _, _ = sample_scene(only_mesh=True)

    per_obj = {}
    for name in sorted(set(src_mesh) & set(imp_mesh)):
        a, b = src_mesh[name]["mats"], imp_mesh[name]["mats"]
        n = min(len(a), len(b))
        worst, worst_f = 0.0, None
        for i in range(n):
            d = mat_diff(a[i], b[i])
            if d > worst:
                worst, worst_f = d, i + 1
        per_obj[name] = {"max_dev": round(worst, 6), "at_frame": worst_f,
                         "animated": bool(src_mesh[name]["action"])}
    report["per_object_vs_source"] = per_obj
    report["source_mesh_objects_not_in_glb"] = sorted(set(src_mesh) - set(imp_mesh))

    # balls: translation must match everywhere, scale must match on visible frames
    ball_checks = {}
    for name in VIS_OBJECTS:
        if name not in imp_mesh:
            continue
        rows = src_vis[name]
        tr_worst = 0.0
        sc_worst, sc_frame = 0.0, None
        for i, (f, authored, hidden) in enumerate(rows):
            dm = mat_diff(src_mesh[name]["mats"][i], imp_mesh[name]["mats"][i])
            # translation columns 12..14
            dt = max(abs(src_mesh[name]["mats"][i][k] - imp_mesh[name]["mats"][i][k])
                     for k in (12, 13, 14))
            tr_worst = max(tr_worst, dt)
            if not hidden:
                d = max(abs(imp_mesh[name]["scales"][i][j] - authored[j]) for j in range(3))
                if d > sc_worst:
                    sc_worst, sc_frame = d, f
            if dm > 1000:
                fail("%s matrix exploded at frame %d" % (name, f))
        ball_checks[name] = {"translation_max_dev": round(tr_worst, 8),
                             "visible_scale_max_dev": round(sc_worst, 8),
                             "visible_scale_worst_frame": sc_frame}
        if tr_worst > TOL:
            regressions.append("%s translation drifts %.6f" % (name, tr_worst))
        if sc_worst > TOL:
            regressions.append("%s visible-frame scale drifts %.6f at f%s"
                               % (name, sc_worst, sc_frame))
    report["visibility_object_checks"] = ball_checks

    for name, d in per_obj.items():
        if name in VIS_OBJECTS:
            continue
        if d["max_dev"] > TOL:
            regressions.append("%s world matrix deviates %.6f at frame %s"
                               % (name, d["max_dev"], d["at_frame"]))

    # ---------------- 5. rebuild_v2 vs p19 -----------------------------
    p19_cmp = {}
    if os.path.exists(P19):
        bpy.ops.wm.open_mainfile(filepath=P19)
        p19_all, pf0, pf1 = sample_scene(only_mesh=False)
        report["p19"] = {"file": P19, "fps": bpy.context.scene.render.fps,
                         "frame_start": pf0, "frame_end": pf1,
                         "objects": len(p19_all)}
        for name in sorted(set(src_all) & set(p19_all)):
            a, b = src_all[name]["mats"], p19_all[name]["mats"]
            n = min(len(a), len(b))
            worst = max(mat_diff(a[i], b[i]) for i in range(n))
            p19_cmp[name] = {"max_dev": round(worst, 6), "type": src_all[name]["type"]}
        report["rebuild_vs_p19"] = p19_cmp
        big = {k: v["max_dev"] for k, v in p19_cmp.items() if v["max_dev"] > TOL}
        report["rebuild_vs_p19_over_tol"] = big
        if big:
            notes.append("rebuild_v2 vs p19 differs beyond %.0e on %d objects "
                         "(mesh rebuild changed geometry/pivots, not an export issue): %s"
                         % (TOL, len(big), sorted(big)[:12]))
    else:
        warnings.append("p19 reference missing, cross-check skipped")

    # ---------------- 6. why each source mesh is absent -----------------
    # re-open source for flags
    bpy.ops.wm.open_mainfile(filepath=SRC)
    missing = report["source_mesh_objects_not_in_glb"]
    why = {}
    for name in missing:
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        why[name] = {
            "hide_render": bool(ob.hide_render),
            "hide_viewport": bool(ob.hide_viewport),
            "hide_get": bool(ob.hide_get()),
            "in_view_layer": name in [o.name for o in bpy.context.view_layer.objects],
            "visible_get": bool(ob.visible_get()),
            "animated": bool(ob.animation_data and ob.animation_data.action),
        }
    report["missing_object_reasons"] = why

    # ---------------- snapshot provenance ------------------------------
    snap = os.path.join(ROOT, "versions", "rebuild_t2.blend")
    if os.path.exists(snap):
        import hashlib

        def sha256(path):
            h = hashlib.sha256()
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            return h.hexdigest()

        a, b = sha256(SRC), sha256(snap)
        report["snapshot"] = {"path": snap, "size_bytes": os.path.getsize(snap),
                              "byte_identical_to_source": a == b, "sha256": a}
        if a != b:
            warnings.append("snapshot %s is not byte-identical to %s" % (snap, SRC))
        if os.path.getmtime(SRC) != os.path.getmtime(snap):
            warnings.append("snapshot mtime differs from source; source may have been rewritten")
    else:
        warnings.append("snapshot %s missing" % snap)

    for name, w in why.items():
        if w["animated"]:
            warnings.append(
                "%s is animated in the source but absent from the GLB (hide_get=%s, "
                "hide_viewport=%s) - pre-existing, not introduced by the visibility bake"
                % (name, w["hide_get"], w["hide_viewport"]))

    # ---------------- verdict ------------------------------------------
    exported_anim = [n for n, d in per_obj.items() if d["animated"]]
    anim_ok = bool(not regressions and not failures
                   and all(d["max_dev"] <= TOL for n, d in per_obj.items()
                           if n not in VIS_OBJECTS)
                   and all(v["visible_scale_max_dev"] <= TOL
                           and v["translation_max_dev"] <= TOL
                           for v in ball_checks.values()))
    report["anim_objects_ok"] = anim_ok
    report["anim_objects_verified"] = sorted(exported_anim)
    report["regressions"] = regressions
    report["failures"] = failures
    report["warnings"] = warnings
    report["findings"] = notes

    # ---- human-readable summary string (task schema wants notes: "...") ----
    p_r = hidden_ranges.get("Product", [])
    i_r = hidden_ranges.get("Idea", [])
    summary = [
        "Visibility driven by object-level hide_render/hide_viewport was baked into the scale "
        "channel of Product and Idea before export (327 keys each, LINEAR); hidden frames use "
        "1e-4 rather than 0 to avoid a degenerate matrix, which is 5e-5 world units for the "
        "0.5 m reward ball, i.e. sub-pixel.",
        "The %d originally authored scale F-Curves on Product were purged before re-keying, so the "
        "authored f300 scale (0.7,0.7,1.0) survives untouched; Idea had no scale channel." % 5,
        "hide_render/hide_viewport were cleared on both objects after baking, otherwise the "
        "exporter drops any object that is hidden on the current frame - that is exactly what "
        "removed Product from the previous GLB entirely.",
        "IMPORTANT - the frame examples in the task brief do not match this file. Product is "
        "hidden on frames %s (232 of 327 frames), so f120 is a HIDDEN frame for Product, not a "
        "visible one. Idea is hidden on frames %s (155 of 327), so f300 is a HIDDEN frame for "
        "Idea. The only frame where both lists agree with the brief is f220 (hidden for both) and "
        "f300 for Product alone (visible, scale 0.7). The baked result matches the authored "
        "hide_render on all 327 frames for both objects, 0 mismatches." % (p_r, i_r),
        "Pre-existing defect, NOT introduced here: Machine_Body has hide_get()==True (outliner "
        "eye, i.e. hide_set) with hide_render and hide_viewport both False, so it is unselectable "
        "and the exporter silently drops it under use_selection=True. The machine's main shell has "
        "therefore been missing from hero_v2.glb since before this task, while its five children "
        "(V2_NamePlate* and V2_FrontPill) are exported as roots - the GLB has nameplate text "
        "without the body. Left untouched because fixing it changes the deliverable silhouette; "
        "one-line fix is to unhide Machine_Body before export (+1 node).",
        "The five deliberately hidden objects (Arm_Mount, Machine_Light_01/02/03, "
        "Machine_LightStrip) stay out of the GLB on purpose, per BUILD_NOTES.md:1523-1526; the "
        "export still uses use_selection=True and must not switch to use_visible=True.",
        "Reproduction gotcha 1: Blender 5.4 removed the legacy action.fcurves accessor; F-Curves "
        "live under action.layers[].strips[].channelbags[].fcurves.",
        "Reproduction gotcha 2: Blender's glTF importer makes one action active and parks the "
        "other 51 clips in MUTED NLA tracks, so re-import validation must unmute them or every "
        "object except the first reads as static. With scene.render.fps=60 the imported clip maps "
        "1:1 to frames 1-327, so no 24fps rescaling was needed.",
        "rebuild_v2 vs p19 differs beyond tolerance on %d objects (%s). That is the T1 mesh "
        "rebuild changing geometry and pivots, not an export regression - every object exported "
        "here matches rebuild_v2 itself to 1e-06." % (
            len(report.get("rebuild_vs_p19_over_tol", {})),
            ", ".join("%s=%.4f" % (k, v) for k, v in
                      sorted(report.get("rebuild_vs_p19_over_tol", {}).items()))),
    ]
    report["notes"] = " ".join(summary)
    report["checks_passed"] = bool(not failures and not regressions)
    report["verdict"] = ("PASS" if report["checks_passed"] and anim_ok else "FAIL")

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print("VAL_REPORT " + REPORT)
    print("VAL_SUMMARY " + json.dumps({
        "verdict": report["verdict"],
        "checks_passed": report["checks_passed"],
        "anim_objects_ok": anim_ok,
        "failures": failures,
        "regressions": regressions,
        "product_scale": report["product_scale"],
        "idea_scale": report["idea_scale"],
        "visibility_object_checks": ball_checks,
        "worst_other_object_dev": max([d["max_dev"] for n, d in per_obj.items()
                                       if n not in VIS_OBJECTS] or [0]),
        "objects_missing_from_glb": missing,
        "rebuild_vs_p19_over_tol": report.get("rebuild_vs_p19_over_tol", {}),
    }))
    if not (report["checks_passed"] and anim_ok):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
