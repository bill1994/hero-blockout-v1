"""Rebuild a claw finger as a clean swept tube.

Extracts the finger's centreline from its own vertices (per-segment centroids),
smooths the radius profile along that line, then sweeps a round cross-section
with a Curve + bevel and converts it back to a mesh. The object, its transform,
parenting and animation are untouched - only obj.data is replaced.

This kills the ring lumps at the source: they are 8-sided topology + bevel
artefacts that no smoothing modifier could remove.
"""
import bpy
import numpy as np
from mathutils import Vector


def _centreline_and_radius(co, segments, axis):
    t = co @ axis
    tmin, tmax = float(t.min()), float(t.max())
    span = tmax - tmin
    seg = np.clip(((t - tmin) / span * segments).astype(int), 0, segments - 1)
    centres, radii = [], []
    for s in range(segments):
        mask = seg == s
        if mask.sum() < 3:
            continue
        pts = co[mask]
        c = pts.mean(axis=0)
        d = pts - c
        axial = (d @ axis)[:, None] * axis[None, :]
        perp = d - axial
        centres.append(c)
        radii.append(float(np.linalg.norm(perp, axis=1).mean()))
    return centres, radii


def rebuild_finger(obj, segments=30, bevel_res=5, smooth_window=5, verbose=False):
    me = obj.data
    n = len(me.vertices)
    if n == 0:
        return {"error": "no verts"}

    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)

    mean = co.mean(axis=0)
    centered = co - mean
    cov = np.cov(centered.T)
    w, v = np.linalg.eigh(cov)
    axis = v[:, int(np.argmax(w))]
    axis = axis / np.linalg.norm(axis)

    centres, radii = _centreline_and_radius(centered, segments, axis)
    if len(centres) < 3:
        return {"error": "too few segments"}

    radii = np.array(radii)
    k = max(1, smooth_window)
    kernel = np.ones(k) / k
    smoothed = np.convolve(radii, kernel, mode="same")
    # keep the true end radii so the tip and root do not get fattened
    head = k // 2 + 1
    smoothed[:head] = radii[:head]
    smoothed[-head:] = radii[-head:]

    cu = bpy.data.curves.new("tmp_finger", "CURVE")
    cu.dimensions = "3D"
    # NURBS, not POLY: a polyline puts a hard corner at every sampled segment,
    # which reads as a bamboo joint on a bent finger
    sp = cu.splines.new("NURBS")
    sp.order_u = 4
    sp.use_endpoint_u = True
    sp.points.add(len(centres) - 1)
    for i, (c, r) in enumerate(zip(centres, smoothed)):
        sp.points[i].co = (float(c[0]), float(c[1]), float(c[2]), 1.0)
        sp.points[i].radius = float(r)
    cu.bevel_depth = 1.0
    cu.bevel_resolution = bevel_res
    cu.use_fill_caps = True
    cu.resolution_u = 8

    tmp = bpy.data.objects.new("tmp_finger", cu)
    bpy.context.scene.collection.objects.link(tmp)
    bpy.context.view_layer.update()

    dg = bpy.context.evaluated_depsgraph_get()
    eo = tmp.evaluated_get(dg)
    new_me = bpy.data.meshes.new_from_object(eo)
    new_me.name = me.name + "_rebuilt"

    old_mats = [ms.material for ms in obj.material_slots if ms.material]
    obj.data = new_me
    new_me.materials.clear()
    for m in old_mats:
        new_me.materials.append(m)
    for p in new_me.polygons:
        p.material_index = 0
        p.use_smooth = True

    bpy.data.objects.remove(tmp, do_unlink=True)
    if cu.users == 0:
        bpy.data.curves.remove(cu)

    # ripple check on the new mesh
    nco = np.empty(len(new_me.vertices) * 3, dtype=np.float64)
    new_me.vertices.foreach_get("co", nco)
    nco = nco.reshape(-1, 3)
    ncent = nco.mean(axis=0)
    nc = nco - ncent
    ncov = np.cov(nc.T)
    nw, nv = np.linalg.eigh(ncov)
    naxis = nv[:, int(np.argmax(nw))]
    naxis = naxis / np.linalg.norm(naxis)
    ncentres, nradii = _centreline_and_radius(nc, segments, naxis)
    nr = np.array(nradii)
    diffs = np.abs(np.diff(nr))
    return {
        "object": obj.name,
        "verts_before": n,
        "verts_after": len(new_me.vertices),
        "faces_after": len(new_me.polygons),
        "radius_min": round(float(nr.min()), 5),
        "radius_max": round(float(nr.max()), 5),
        "radius_span_pct": round(float((nr.max() - nr.min()) / nr.max() * 100), 2),
        "max_step_between_rings": round(float(diffs.max()), 5),
        "mean_step_between_rings": round(float(diffs.mean()), 5),
        "materials": [m.name for m in old_mats],
    }
