"""Read-only audit of ReferenceModel.blend (Tripo-generated reference).

Captures per-part world bbox / center / size so parts can be clustered into
semantic groups, plus material and UV inventory.
Writes audit/tripo_parts.json. Never modifies the scene.
"""
import bpy
import json
import os
from mathutils import Vector

OUT = r"G:\DSHProject\BlenderMcp\audit"
os.makedirs(OUT, exist_ok=True)

parts = []
for o in [ob for ob in bpy.data.objects if ob.type == 'MESH']:
    me = o.data
    try:
        me.calc_loop_triangles()
        tris = len(me.loop_triangles)
    except Exception:
        tris = 0
    mn = Vector((1e18, 1e18, 1e18))
    mx = Vector((-1e18, -1e18, -1e18))
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i])
            mx[i] = max(mx[i], w[i])
    ctr = (mn + mx) / 2.0
    size = mx - mn
    parts.append({
        "name": o.name,
        "verts": len(me.vertices),
        "tris": tris,
        "bbox_min": [round(v, 5) for v in mn],
        "bbox_max": [round(v, 5) for v in mx],
        "center": [round(v, 5) for v in ctr],
        "size": [round(v, 5) for v in size],
        "max_dim": round(max(size), 5),
        "mats": [s.material.name if s.material else None for s in o.material_slots],
        "uv_layers": len(me.uv_layers),
    })

parts.sort(key=lambda p: -p["max_dim"])

sc = bpy.context.scene
result = {
    "file": bpy.data.filepath,
    "blender": bpy.app.version_string,
    "n_parts": len(parts),
    "total_tris": sum(p["tris"] for p in parts),
    "total_verts": sum(p["verts"] for p in parts),
    "parts": parts,
    "materials": [{"name": m.name, "users": m.users} for m in bpy.data.materials],
    "unit_settings": [sc.unit_settings.system, round(sc.unit_settings.scale_length, 5)],
    "frame_range": [sc.frame_start, sc.frame_end],
    "images": [{"name": i.name, "size": list(i.size), "packed": bool(i.packed_file)}
               for i in bpy.data.images],
}

dest = os.path.join(OUT, "tripo_parts.json")
with open(dest, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("WROTE " + dest)
