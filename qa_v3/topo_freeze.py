"""Topology freeze contract for the reference rebuild (plan S2.0 / S2.6 gate).

Two jobs, one file:

  inputs   Hash the frozen source assets so no later run can silently rebuild
           them differently. This is the S2.0 gate.

  objects  Fingerprint every mesh object's topology so any edit after the UV
           pass is detected. This is the S2.6 gate.

Run under Blender's python:

  blender --background --factory-startup --python qa_v3/topo_freeze.py -- init
  blender --background --factory-startup --python qa_v3/topo_freeze.py -- check
  blender --background --factory-startup --python qa_v3/topo_freeze.py -- objects <blend>
  blender --background --factory-startup --python qa_v3/topo_freeze.py -- diff <blend>

`init` refuses to overwrite an existing record unless --force is given; the
whole point is that the baseline stops moving.
"""

import hashlib
import json
import os
import sys
import datetime

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RECORD = os.path.join(HERE, "topo_freeze.json")

# Source assets that later stages must not silently re-derive.
INPUTS = [
    "ReferenceModel.blend",
    os.path.join("versions", "rebuild_v7_s1.blend"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load():
    if not os.path.exists(RECORD):
        return None
    with open(RECORD, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(rec):
    with open(RECORD, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
        fh.write("\n")


def cmd_init(force):
    rec = load()
    if rec and not force:
        print("[topo_freeze] record exists: %s (use --force to rewrite)" % RECORD)
        return 1
    rec = {
        "schema": 1,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "inputs": {},
        "objects": {},
        "frozen_at": None,
    }
    missing = []
    for rel in INPUTS:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            missing.append(rel)
            continue
        rec["inputs"][rel.replace("\\", "/")] = {
            "sha256": sha256_file(path),
            "bytes": os.path.getsize(path),
        }
    if missing:
        print("[topo_freeze] MISSING inputs: %s" % ", ".join(missing))
    save(rec)
    for rel, meta in sorted(rec["inputs"].items()):
        print("[topo_freeze] in  %-34s %s (%d B)" % (rel, meta["sha256"][:16], meta["bytes"]))
    print("[topo_freeze] wrote %s" % RECORD)
    return 0 if not missing else 2


def cmd_check():
    rec = load()
    if not rec:
        print("[topo_freeze] no record; run `init` first")
        return 2
    bad = 0
    for rel, meta in sorted(rec["inputs"].items()):
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("[topo_freeze] FAIL  %-34s deleted" % rel)
            bad += 1
            continue
        got = sha256_file(path)
        if got != meta["sha256"]:
            print("[topo_freeze] FAIL  %-34s %s != %s" % (rel, got[:16], meta["sha256"][:16]))
            bad += 1
        else:
            print("[topo_freeze] ok    %-34s %s" % (rel, got[:16]))
    return 1 if bad else 0


def fingerprint(objs):
    out = {}
    for ob in sorted(objs, key=lambda o: o.name):
        me = ob.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        quads = sum(1 for p in me.polygons if len(p.vertices) == 4)
        ngons = sum(1 for p in me.polygons if len(p.vertices) > 4)
        h = hashlib.sha1()
        for v in me.vertices:
            h.update(("%.6f,%.6f,%.6f;" % (v.co.x, v.co.y, v.co.z)).encode())
        out[ob.name] = {
            "verts": len(me.vertices),
            "polys": len(me.polygons),
            "tris": tris,
            "quads": quads,
            "ngons": ngons,
            "coord_hash": h.hexdigest(),
        }
    return out


def open_blend(path):
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    bpy.ops.wm.open_mainfile(filepath=path)
    return path


def cmd_objects(blend, force):
    rec = load()
    if not rec:
        print("[topo_freeze] no record; run `init` first")
        return 2
    if rec.get("objects") and not force:
        print("[topo_freeze] objects already frozen (frozen_at=%s); use --force" % rec.get("frozen_at"))
        return 1
    open_blend(blend)
    rec["objects"] = fingerprint([o for o in bpy.data.objects if o.type == "MESH"])
    rec["frozen_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    rec["frozen_blend"] = os.path.basename(blend)
    save(rec)
    tot = sum(v["tris"] for v in rec["objects"].values())
    print("[topo_freeze] froze %d objects / %d tris at %s"
          % (len(rec["objects"]), tot, rec["frozen_at"]))
    return 0


def cmd_diff(blend):
    rec = load()
    if not rec or not rec.get("objects"):
        print("[topo_freeze] nothing frozen yet")
        return 2
    open_blend(blend)
    now = fingerprint([o for o in bpy.data.objects if o.type == "MESH"])
    old = rec["objects"]
    drift = 0
    for name in sorted(set(old) | set(now)):
        a, b = old.get(name), now.get(name)
        if a is None:
            print("[topo_freeze] NEW     %-26s %s tris" % (name, b["tris"]))
            drift += 1
        elif b is None:
            print("[topo_freeze] GONE    %-26s was %s tris" % (name, a["tris"]))
            drift += 1
        else:
            delta = {k: b[k] - a[k] for k in ("verts", "polys", "tris", "ngons") if a[k] != b[k]}
            if delta or a["coord_hash"] != b["coord_hash"]:
                moved = "" if a["coord_hash"] == b["coord_hash"] else " coords"
                print("[topo_freeze] DRIFT   %-26s %s%s" % (name, delta or "", moved))
                drift += 1
    if drift:
        print("[topo_freeze] FAIL: %d object(s) drifted since %s" % (drift, rec.get("frozen_at")))
        return 1
    print("[topo_freeze] ok: %d objects identical to %s" % (len(now), rec.get("frozen_at")))
    return 0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    force = "--force" in argv
    argv = [a for a in argv if not a.startswith("--")]
    cmd = argv[0] if argv else "check"
    if cmd == "init":
        return cmd_init(force)
    if cmd == "check":
        return cmd_check()
    if cmd == "objects":
        return cmd_objects(argv[1] if len(argv) > 1 else "versions/rebuild_v7_s1.blend", force)
    if cmd == "diff":
        return cmd_diff(argv[1] if len(argv) > 1 else "versions/rebuild_v7_s1.blend")
    print("[topo_freeze] unknown command %r" % cmd)
    return 2


sys.exit(main())
