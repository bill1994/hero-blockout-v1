"""rebuild_v2.blend -> export/hero_v2.glb

glTF has no visibility channel, so the two objects whose visibility is driven by
object-level `hide_render` / `hide_viewport` keyframes (Product, Idea) are baked
into SCALE before export:

  * sample, per frame, the *authored* local scale and the hide_render state
  * drop the existing scale + hide_* F-Curves (otherwise two curves fight)
  * re-key scale on EVERY frame: authored value when visible, HIDDEN_SCALE when
    hidden. glTF baking samples every frame anyway, so per-frame keys reproduce
    the original hard visibility switch exactly - no fade is introduced.
  * clear hide_render / hide_viewport on those two objects only

The last point is load-bearing: the exporter drops any object that fails
select_get() (io_scene_gltf2/blender/exp/tree.py, node_filter_inheritable), and an
object with hide_viewport=True cannot be selected. That is why Product was
entirely absent from the previous GLB.

HIDDEN_SCALE is 1e-4 rather than 0: a zero scale produces a degenerate/NaN normal
matrix in several glTF runtimes. At radius 0.5 that is 5e-5 units - sub-pixel.

Everything else is untouched. In particular we do NOT pass use_visible=True:
Arm_Mount and Machine_Light_01/02/03/LightStrip are intentionally hidden and must
stay out of the GLB (BUILD_NOTES "any future GLB export must use use_visible=True
or these five come back" - so we deliberately keep the selection-based filter).

Nothing is saved back: all baking happens in this process's memory copy.
"""
import json
import sys
import traceback

import bpy

SRC = r"G:\DSHProject\BlenderMcp\rebuild_v2.blend"
DST = r"G:\DSHProject\BlenderMcp\export\hero_v2.glb"
VIS_OBJECTS = ("Product", "Idea")
HIDDEN_SCALE = 1e-4
ACTIVE_OBJECT = "Machine_Body"
FALLBACK_FPS = 60


def action_channelbags(act):
    """Blender 5.x slotted actions: `action.fcurves` no longer exists."""
    bags = []
    for layer in getattr(act, "layers", []) or []:
        for strip in getattr(layer, "strips", []):
            for cb in getattr(strip, "channelbags", None) or []:
                bags.append(cb)
    return bags


def purge_channels(ob, data_paths):
    """Remove F-Curves for exact data_paths; returns count removed."""
    ad = ob.animation_data
    if not (ad and ad.action):
        return 0
    removed = 0
    for cb in action_channelbags(ad.action):
        doomed = [fc for fc in cb.fcurves if fc.data_path in data_paths]
        for fc in doomed:
            cb.fcurves.remove(fc)
            removed += 1
    return removed


def scale_fcurves(ob):
    ad = ob.animation_data
    if not (ad and ad.action):
        return []
    return [fc for cb in action_channelbags(ad.action)
            for fc in cb.fcurves if fc.data_path == "scale"]


def sample_authored(ob, f0, f1):
    """Per-frame (scale, hide_render) as authored, BEFORE we touch any F-Curve."""
    rows = []
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        rows.append((f, tuple(ob.scale), bool(ob.hide_render), bool(ob.hide_viewport)))
    return rows


def bake_visibility_to_scale(ob, f0, f1):
    rows = sample_authored(ob, f0, f1)

    src_hidden = [f for f, _s, h, _hv in rows if h]
    disagree = [f for f, _s, h, hv in rows if h != hv]
    if disagree:
        print("BAKE_WARN %s hide_render/hide_viewport disagree on %d frames: %s"
              % (ob.name, len(disagree), disagree[:8]))

    removed = purge_channels(ob, {"scale", "hide_render", "hide_viewport"})

    for f, s, hidden, _hv in rows:
        if hidden:
            ob.scale = (HIDDEN_SCALE, HIDDEN_SCALE, HIDDEN_SCALE)
        else:
            ob.scale = s
        ob.keyframe_insert(data_path="scale", frame=f, group=ob.name)

    for fc in scale_fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()

    # visibility flags must be OFF, otherwise the exporter skips the object whole
    ob.hide_render = False
    ob.hide_viewport = False
    ob.hide_set(False)
    bpy.context.view_layer.update()

    visible = [f for f, _s, h, _hv in rows if not h]
    return {
        "object": ob.name,
        "purged_fcurves": removed,
        "keyed_frames": f1 - f0 + 1,
        "hidden_frames": len(src_hidden),
        "visible_frames": len(visible),
        "hidden_ranges": _ranges(src_hidden),
        "sample": {str(f): [round(v, 6) for v in s] for f, s, h, _ in rows
                   if f in (f0, 120, 220, 300, f1)},
        "hidden_at_sample": {str(f): h for f, _s, h, _ in rows
                             if f in (f0, 120, 220, 300, f1)},
    }


def _ranges(frames):
    out = []
    start = prev = None
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
    bpy.ops.wm.open_mainfile(filepath=SRC)
    sc = bpy.context.scene
    f0, f1 = sc.frame_start, sc.frame_end
    if sc.render.fps != FALLBACK_FPS:
        print("EXPORT_WARN scene fps=%s (expected %s); times will rescale"
              % (sc.render.fps, FALLBACK_FPS))
    print("EXPORT scene fps=%s range=%s..%s engine=%s"
          % (sc.render.fps, f0, f1, sc.render.engine))

    manifests = []
    for name in VIS_OBJECTS:
        ob = bpy.data.objects.get(name)
        if ob is None:
            raise RuntimeError("missing object %r" % name)
        manifests.append(bake_visibility_to_scale(ob, f0, f1))
        print("BAKE " + json.dumps(manifests[-1]))

    # --- clear stale outliner hides -------------------------------------
    # A stale hide_get() (the outliner eye) makes an object unselectable, and the
    # glTF exporter silently drops unselectable objects under use_selection=True.
    # The source file has Machine_Body with hide_get()==True while hide_render
    # and hide_viewport are both False, so the entire shell was missing from the
    # GLB while its children were exported as scene roots ("text without body").
    # Only objects whose render flags already say "visible" are touched, so the
    # intentionally hidden parts and the boolean cutters stay out.
    restored = []
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if ob.hide_render or ob.hide_viewport:
            continue
        if ob.hide_get():
            ob.hide_set(False)
            restored.append(ob.name)
    print("EXPORT outliner_unhide=" + json.dumps(restored))

    # --- selection: meshes only, same filter as before -------------------
    bpy.ops.object.select_all(action='DESELECT')
    selected, failed = [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        try:
            ob.select_set(True)
        except Exception as ex:
            failed.append([ob.name, "exception: %s" % ex])
            continue
        if ob.select_get():
            selected.append(ob.name)
        else:
            failed.append([ob.name, "select_get() False"])

    for name in VIS_OBJECTS:
        if name not in selected:
            raise RuntimeError("%s still not selectable after unhide - exporter would drop it"
                               % name)

    act = bpy.data.objects.get(ACTIVE_OBJECT)
    if act is not None and act.select_get():
        bpy.context.view_layer.objects.active = act
    else:
        bpy.context.view_layer.objects.active = bpy.data.objects[selected[0]]

    print("EXPORT meshes_selected=%d skipped=%d" % (len(selected), len(failed)))
    for n, why in failed:
        print("EXPORT skip %-26s %s" % (n, why))

    bpy.ops.export_scene.gltf(
        filepath=DST,
        export_format='GLB',
        use_selection=True,
        export_animations=True,
        export_animation_mode='SCENE',
        export_bake_animation=True,
        export_apply=False,
        export_yup=True,
    )

    import os
    size = os.path.getsize(DST)
    print("EXPORT wrote %s (%d bytes)" % (DST, size))
    print("EXPORT_DONE " + json.dumps({
        "glb_path": DST,
        "glb_size_bytes": size,
        "meshes_selected": len(selected),
        "meshes_skipped": [n for n, _ in failed],
        "outliner_unhide": restored,
        "active_object": bpy.context.view_layer.objects.active.name,
        "bakes": manifests,
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
