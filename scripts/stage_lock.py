"""Stage chain lock: each stage may only consume the exact blend it was built on.

`qa_v3/topo_freeze.json` locks the original sources (reference + v7_s1). Every
stage after that produces a new blend, and a stage script must consume the
previous stage's output byte for byte. The chain lives in
`qa_v3/stage_chain.json`: first use records the hash, later uses verify it and
abort on mismatch.

So the failure mode "someone edited the intermediate blend by hand and the next
stage silently built on top of it" cannot happen quietly.
"""

import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAIN = os.path.join(ROOT, "qa_v3", "stage_chain.json")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rel(path):
    return os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")


def _load():
    if not os.path.exists(CHAIN):
        return {"schema": 1, "stages": {}}
    with open(CHAIN, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _save(rec):
    with open(CHAIN, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
        fh.write("\n")


def verify(path, label="input"):
    """Abort if the file does not match its recorded hash."""
    rec = _load()
    rel = _rel(path)
    got = sha256_file(path)
    want = rec["stages"].get(rel)
    if want is None:
        rec["stages"][rel] = got
        _save(rec)
        print("[lock] %s %s recorded %s" % (label, rel, got[:16]))
        return got
    if got != want:
        sys.exit("[lock] %s %s hash mismatch: %s != %s" % (label, rel, got, want))
    print("[lock] %s %s ok %s" % (label, rel, got[:16]))
    return got


def record(path):
    rec = _load()
    rel = _rel(path)
    got = sha256_file(path)
    rec["stages"][rel] = got
    _save(rec)
    print("[lock] output %s recorded %s" % (rel, got[:16]))
    return got
