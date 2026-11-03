"""Radial equalisation for the claw fingers.

The lumps are axial radius ripple left over from the PCA thickening pass.
This keeps every vertex's axial position (so the bend and length survive) and
replaces only its perpendicular offset with a segment-mean radius that is
itself smoothed across neighbouring segments, so there are no steps between
rings.

Operates in local mesh space, so the object transform / parenting is untouched.
"""
import bpy
import numpy as np


def _pca_axis(co):
    mean = co.mean(axis=0)
    centered = co - mean
    cov = np.cov(centered.T)
    w, v = np.linalg.eigh(cov)
    axis = v[:, int(np.argmax(w))]
    return axis / np.linalg.norm(axis), mean


def _segments(co, axis, segments):
    mean = co.mean(axis=0)
    t = (co - mean) @ axis
    tmin, tmax = float(t.min()), float(t.max())
    span = tmax - tmin
    if span <= 0:
        return None, None
    seg = np.clip(((t - tmin) / span * segments).astype(int), 0, segments - 1)
    return seg, (tmin, tmax)


def _segment_stats(co, axis, seg, segments):
    """Per-segment centroid, mean radius, and the per-vertex perpendicular parts."""
    centroids = []
    radii = []
    for s in range(segments):
        mask = seg == s
        if mask.sum() < 4:
            centroids.append(None)
            radii.append(None)
            continue
        pts = co[mask]
        c = pts.mean(axis=0)
        d = pts - c
        axial = (d @ axis)[:, None] * axis[None, :]
        perp = d - axial
        r = np.linalg.norm(perp, axis=1)
        centroids.append(c)
        radii.append(float(r.mean()))
    return centroids, radii


def _smooth_series(values, window=3):
    idx = [i for i, v in enumerate(values) if v is not None]
    out = list(values)
    half = window // 2
    for k, i in enumerate(idx):
        lo = max(0, k - half)
        hi = min(len(idx), k + half + 1)
        vals = [values[idx[j]] for j in range(lo, hi)]
        out[i] = sum(vals) / len(vals)
    return out


def measure_ripple(obj, segments=26):
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    axis, _ = _pca_axis(co)
    seg, _ = _segments(co, axis, segments)
    if seg is None:
        return {"object": obj.name, "error": "degenerate"}
    _, radii = _segment_stats(co, axis, seg, segments)
    valid = [r for r in radii if r]
    return {
        "object": obj.name,
        "radii": [round(r, 5) if r else None for r in radii],
        "ripple_pct": round((max(valid) - min(valid)) / max(valid) * 100, 2) if valid else None,
        "radius_min": round(min(valid), 5) if valid else None,
        "radius_max": round(max(valid), 5) if valid else None,
    }


def equalise_radius(obj, segments=26, blend=1.0, smooth_window=3, keep_ends=True):
    me = obj.data
    n = len(me.vertices)
    if n == 0:
        return {"error": "no verts"}

    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    original = co.copy()

    axis, _ = _pca_axis(co)
    seg, _ = _segments(co, axis, segments)
    if seg is None:
        return {"error": "degenerate axis"}

    centroids, radii = _segment_stats(co, axis, seg, segments)
    target = _smooth_series(radii, window=smooth_window)

    if keep_ends:
        valid_idx = [i for i, r in enumerate(radii) if r]
        if valid_idx:
            target[valid_idx[0]] = radii[valid_idx[0]]
            target[valid_idx[-1]] = radii[valid_idx[-1]]

    new_co = co.copy()
    for s in range(segments):
        if centroids[s] is None or target[s] is None:
            continue
        mask = seg == s
        c = centroids[s]
        pts = co[mask]
        d = pts - c
        axial = (d @ axis)[:, None] * axis[None, :]
        perp = d - axial
        r = np.linalg.norm(perp, axis=1)
        safe = np.where(r > 1e-9, r, 1.0)
        scaled = perp / safe[:, None] * target[s]
        # keep the axial position - dropping it collapses each ring onto one plane
        new_co[mask] = c + axial + scaled

    final = original + (new_co - original) * blend
    me.vertices.foreach_set("co", final.ravel())
    me.update()

    before_valid = [r for r in radii if r]
    return {
        "object": obj.name,
        "verts": n,
        "segments": segments,
        "blend": blend,
        "smooth_window": smooth_window,
        "ripple_before_pct": round((max(before_valid) - min(before_valid)) / max(before_valid) * 100, 2),
        "radii_before": [round(r, 5) if r else None for r in radii],
        "radii_target": [round(r, 5) if r else None for r in target],
    }
