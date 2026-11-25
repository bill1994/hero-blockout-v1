"""S2.5a triage report: which cap ngons are truly enclosed.

Report-only; writes nothing to the blend. Kept as the human-readable gate in
front of s2_5a_clear_caps.py, which uses the same test from cap_occlusion.

Run:
  blender --background --factory-startup --python scripts/s2_5a_triage.py -- \
      versions/rebuild_v7_s1.blend [--json qa_v3/s2_5a_triage.json]
"""

import json
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import cap_occlusion as occ


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    blend = argv[0] if argv else os.path.join("versions", "rebuild_v7_s1.blend")
    out = None
    if "--json" in argv:
        out = argv[argv.index("--json") + 1]
    return blend, out


def main():
    blend, out_path = args()
    if not os.path.isabs(blend):
        blend = os.path.join(ROOT, blend)
    bpy.ops.wm.open_mainfile(filepath=blend)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    rows = occ.cap_rows(meshes)
    t = occ.tally(rows)

    print("@@TRIAGE@@ ngons=%d hidden=%d visible=%d"
          % (t["total"], len(t["hidden"]), len(t["visible"])))
    print("@@DELETE_HIDDEN@@ -%d tris" % t["delete_tris"])
    print("@@FAN_VISIBLE@@ +%d tris" % t["fan_tris"])
    print("@@KEEP_VISIBLE@@ net if only hidden are deleted: -%d" % t["delete_tris"])
    for tag, group in (("H", t["hidden"]), ("X", t["visible"])):
        for r in sorted(group, key=lambda q: (q["object"], -q["n"], q["center"])):
            print("   %s %-22s n=%2d del=%2d fan=%2d encl=%.2f"
                  % (tag, r["object"], r["n"], r["tris_if_deleted"],
                     r["tris_if_fan"], r["enclosure"]))

    if out_path:
        if not os.path.isabs(out_path):
            out_path = os.path.join(ROOT, out_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump({"blend": os.path.basename(blend),
                       "hidden": len(t["hidden"]),
                       "visible": len(t["visible"]),
                       "rows": rows}, fh, indent=1)
            fh.write("\n")
        print("@@WROTE@@ %s" % out_path)


main()
