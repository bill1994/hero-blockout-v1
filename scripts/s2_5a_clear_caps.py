"""S2.5a: delete the cap ngons that are provably enclosed.

Deletes only faces whose enclosure >= ENCLOSED_AT under the multi-sample test in
cap_occlusion. Visible caps are kept as planar ngons on purpose: triangulating
them costs more tris than it saves (see REFERENCE_REBUILD_PLAN.md S4.2), and the
glTF export triangulates anyway.

Guarded by the S2.0 input hash: refuses to run against a source blend that does
not match qa_v3/topo_freeze.json.

Run:
  blender --background --factory-startup --python scripts/s2_5a_clear_caps.py -- \
      versions/rebuild_v7_s1.blend versions/rebuild_v7_s2a.blend
"""

import hashlib
import json
import os
import sys

import bmesh
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import cap_occlusion as occ

RECORD = os.path.join(ROOT, "qa_v3", "topo_freeze.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_input(path):
    with open(RECORD, "r", encoding="utf-8") as fh:
        rec = json.load(fh)
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    want = rec["inputs"].get(rel)
    if not want:
        raise SystemExit("[s2_5a] %s is not a frozen input in topo_freeze.json" % rel)
    got = sha256_file(path)
    if got != want["sha256"]:
        raise SystemExit("[s2_5a] input hash mismatch for %s: %s != %s"
                         % (rel, got, want["sha256"]))
    print("[s2_5a] input ok %s %s" % (rel, got[:16]))


def totals():
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    tris = quads = ngons = polys = 0
    for ob in meshes:
        me = ob.data
        polys += len(me.polygons)
        for p in me.polygons:
            n = len(p.vertices)
            tris += n - 2
            if n == 4:
                quads += 1
            elif n > 4:
                ngons += 1
    return {"objects": len(meshes), "polys": polys, "tris": tris,
            "quads": quads, "ngons": ngons}


def delete_caps(by_object):
    removed = 0
    for name, indices in sorted(by_object.items()):
        ob = bpy.data.objects[name]
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.ensure_lookup_table()
        victims = [bm.faces[i] for i in indices]
        bmesh.ops.delete(bm, geom=victims, context="FACES")
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        removed += len(indices)
        print("[s2_5a] %-22s -%d caps" % (name, len(indices)))
    return removed


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    src = argv[0] if argv else os.path.join("versions", "rebuild_v7_s1.blend")
    dst = argv[1] if len(argv) > 1 else os.path.join("versions", "rebuild_v7_s2a.blend")
    if not os.path.isabs(src):
        src = os.path.join(ROOT, src)
    if not os.path.isabs(dst):
        dst = os.path.join(ROOT, dst)

    verify_input(src)
    bpy.ops.wm.open_mainfile(filepath=src)
    before = totals()

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    rows = occ.cap_rows(meshes)
    t = occ.tally(rows)
    print("[s2_5a] triage: %d caps -> %d enclosed / %d visible"
          % (t["total"], len(t["hidden"]), len(t["visible"])))

    by_object = {}
    for r in t["hidden"]:
        by_object.setdefault(r["object"], []).append(r["face_index"])
    removed = delete_caps(by_object)

    after = totals()
    print("[s2_5a] caps deleted: %d" % removed)
    print("[s2_5a] tris %d -> %d (%+d)" % (before["tris"], after["tris"],
                                           after["tris"] - before["tris"]))
    print("[s2_5a] quads %d -> %d, ngons %d -> %d, polys %d -> %d"
          % (before["quads"], after["quads"], before["ngons"], after["ngons"],
             before["polys"], after["polys"]))
    if after["tris"] != before["tris"] - t["delete_tris"]:
        raise SystemExit("[s2_5a] triangle delta does not match the triage prediction")

    bpy.ops.wm.save_as_mainfile(filepath=dst)
    print("[s2_5a] saved %s (%d B)" % (dst, os.path.getsize(dst)))

    report = {
        "source": os.path.relpath(src, ROOT).replace("\\", "/"),
        "output": os.path.relpath(dst, ROOT).replace("\\", "/"),
        "before": before,
        "after": after,
        "deleted": by_object,
        "kept_visible": [{"object": r["object"], "n": r["n"],
                          "enclosure": r["enclosure"]} for r in t["visible"]],
    }
    out = os.path.join(ROOT, "qa_v3", "s2_5a_result.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print("[s2_5a] wrote %s" % out)


main()
