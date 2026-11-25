"""Shared occlusion test for cap ngons.

One place decides whether a polygon is hidden, so the triage report and the
deletion pass can never disagree.

The test: sample the face at its centroid plus a ring of interior points, and
from every sample point cast the face normal plus a cone of rays (70 deg half
angle). The face counts as enclosed only if EVERY sample point hits some other
object on ALL rays. A single centroid ray is not enough: it calls an annulus
enclosed whenever a small part sits over its middle, which is exactly how
Arm_Base's visible ring was once freed for deletion by mistake.
"""

import math

from mathutils import Vector
from mathutils.bvhtree import BVHTree

RAY_LEN = 3.0
CONE_DEG = 70.0
CONE_RAYS = 8
RING_FRAC = 0.75
ENCLOSED_AT = 0.99


def build_trees(objects):
    trees = {}
    for ob in objects:
        mw = ob.matrix_world
        verts = [mw @ v.co for v in ob.data.vertices]
        polys = [tuple(p.vertices) for p in ob.data.polygons]
        trees[ob.name] = BVHTree.FromPolygons(verts, polys, all_triangles=False)
    return trees


def _dirs(normal):
    up = Vector((0.0, 0.0, 1.0)) if abs(normal.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    t = normal.cross(up).normalized()
    b = normal.cross(t).normalized()
    cone = math.radians(CONE_DEG)
    out = [normal]
    for k in range(CONE_RAYS):
        a = 2.0 * math.pi * k / CONE_RAYS
        out.append((normal * math.cos(cone)
                    + (t * math.cos(a) + b * math.sin(a)) * math.sin(cone)).normalized())
    return out


def _enclosure(center, normal, trees, self_name, cache_dirs):
    if cache_dirs is None:
        cache_dirs = _dirs(normal)
    hits = 0
    for d in cache_dirs:
        origin = center + normal * 1e-4
        for name, tree in trees.items():
            if name == self_name:
                continue
            if tree.ray_cast(origin, d, RAY_LEN)[0] is not None:
                hits += 1
                break
    return hits / float(len(cache_dirs))


def _samples(mesh, poly, mw):
    vs = [mw @ mesh.vertices[i].co for i in poly.vertices]
    centroid = sum(vs, Vector()) / len(vs)
    pts = [centroid]
    for v in vs:
        pts.append(centroid + (v - centroid) * RING_FRAC)
    return centroid, pts


def cap_rows(objects, min_verts=5, trees=None):
    """One row per polygon with more than four sides."""
    if trees is None:
        trees = build_trees(objects)
    rows = []
    for ob in objects:
        mw = ob.matrix_world
        me = ob.data
        for poly in me.polygons:
            n = len(poly.vertices)
            if n < min_verts:
                continue
            normal = (mw.to_3x3() @ poly.normal).normalized()
            dirs = _dirs(normal)
            centroid, pts = _samples(me, poly, mw)
            worst = min(_enclosure(p, normal, trees, ob.name, dirs) for p in pts)
            rows.append({
                "object": ob.name,
                "face_index": poly.index,
                "n": n,
                "tris_if_deleted": n - 2,
                "tris_if_fan": n,
                "enclosure": round(worst, 3),
                "center": [round(c, 4) for c in centroid],
                "normal": [round(c, 3) for c in normal],
            })
    return rows


def tally(rows):
    hidden = [r for r in rows if r["enclosure"] >= ENCLOSED_AT]
    visible = [r for r in rows if r["enclosure"] < ENCLOSED_AT]
    return {
        "total": len(rows),
        "hidden": hidden,
        "visible": visible,
        "delete_tris": sum(r["tris_if_deleted"] for r in hidden),
        "fan_tris": sum(r["tris_if_fan"] for r in visible),
    }
