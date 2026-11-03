"""Ring-based radius equalisation for the claw fingers.

The fingers are regular tubes: 8 vertices per ring, ~62 rings, plus 2 cap
verts. Earlier attempts segmented along a global PCA axis, which is wrong on a
bent tube and produced as much ripple as it removed.

Here the real topology defines the rings. Each ring's centroid is its centre
(rings are perpendicular to the local tangent, so the centroid lies on the
centreline), and each ring's mean radius is smoothed across neighbouring rings.
Vertices keep their direction from the ring centre and only their distance is
replaced - so the bend, the length and the topology all survive.
"""
import bpy
import numpy as np


def ring_radii(obj, per_ring=8):
    me = obj.data
    n = len(me.vertices)
    co = np.empty(n * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(n, 3)
    rings = n // per_ring
    centers = np.zeros((rings, 3))
    radii = np.zeros(rings)
    for i in range(rings):
        pts = co[i * per_ring:(i + 1) * per_ring]
        c = pts.mean(axis=0)
        centers[i] = c
        radii[i] = float(np.linalg.norm(pts - c, axis=1).mean())
    return co, centers, radii, rings


def measure_ring_ripple(obj, per_ring=8):
    co, centers, radii, rings = ring_radii(obj, per_ring)
    d2 = np.abs(np.diff(radii, n=2))
    return {
        "object": obj.name,
        "rings": rings,
        "radius_min": round(float(radii.min()), 5),
        "radius_max": round(float(radii.max()), 5),
        "max_second_diff": round(float(d2.max()), 5),
        "mean_second_diff": round(float(d2.mean()), 5),
        "radii_head": [round(float(x), 5) for x in radii[:6]],
        "radii_tail": [round(float(x), 5) for x in radii[-6:]],
    }


def equalise_rings(obj, per_ring=8, window=7, blend=1.0):
    me = obj.data
    co, centers, radii, rings = ring_radii(obj, per_ring)

    k = max(3, window | 1)  # odd kernel
    kernel = np.ones(k) / k
    smoothed = np.convolve(radii, kernel, mode="same")
    head = k // 2 + 1
    # keep the true end radii so the tip taper and root seat are not fattened
    smoothed[:head] = radii[:head]
    smoothed[-head:] = radii[-head:]

    new = co.copy()
    for i in range(rings):
        pts = co[i * per_ring:(i + 1) * per_ring]
        c = centers[i]
        d = pts - c
        dn = np.linalg.norm(d, axis=1)
        safe = np.where(dn > 1e-9, dn, 1.0)
        new[i * per_ring:(i + 1) * per_ring] = c + d / safe[:, None] * smoothed[i]

    final = co + (new - co) * blend
    me.vertices.foreach_set("co", final.ravel())
    me.update()

    before = np.abs(np.diff(radii, n=2))
    return {
        "object": obj.name,
        "rings": rings,
        "window": k,
        "blend": blend,
        "max_second_diff_before": round(float(before.max()), 5),
        "radii_before": [round(float(x), 5) for x in radii],
        "radii_target": [round(float(x), 5) for x in smoothed],
    }
