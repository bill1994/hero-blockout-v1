"""Pure-stdlib GLB inspector: no bpy, no external deps.

Parses the GLB container, JSON chunk and BIN chunk, and exposes helpers to
read animation sampler data (time + value accessors) for a given node/path.
Used by validate_glb_vis.py as the byte-level ground truth, independent of
Blender's importer.
"""
import json
import struct
import sys

COMPONENT = {
    5120: ("b", 1),
    5121: ("B", 1),
    5122: ("h", 2),
    5123: ("H", 2),
    5125: ("I", 4),
    5126: ("f", 4),
}
NCOMP = {
    "SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
    "MAT2": 4, "MAT3": 9, "MAT4": 16,
}


class Glb:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.raw = f.read()
        magic, version, length = struct.unpack_from("<III", self.raw, 0)
        if magic != 0x46546C67:
            raise ValueError("not a GLB: bad magic 0x%08X" % magic)
        self.version = version
        self.length = length
        off = 12
        self.json = None
        self.bin = b""
        while off < length:
            clen, ctype = struct.unpack_from("<II", self.raw, off)
            body = self.raw[off + 8: off + 8 + clen]
            if ctype == 0x4E4F534A:
                self.json = json.loads(body.decode("utf-8"))
            elif ctype == 0x004E4942:
                self.bin = body
            off += 8 + clen
        if self.json is None:
            raise ValueError("GLB has no JSON chunk")

    # ---- accessors ----------------------------------------------------
    def read_accessor(self, idx):
        acc = self.json["accessors"][idx]
        n = acc["count"]
        ncomp = NCOMP[acc["type"]]
        fmt, size = COMPONENT[acc["componentType"]]
        out = []
        if "bufferView" not in acc:
            return [tuple([0] * ncomp) for _ in range(n)] if ncomp > 1 else [0] * n
        bv = self.json["bufferViews"][acc["bufferView"]]
        base = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        stride = bv.get("byteStride") or (ncomp * size)
        for i in range(n):
            vals = struct.unpack_from("<" + fmt * ncomp, self.bin, base + i * stride)
            out.append(vals[0] if ncomp == 1 else vals)
        return out

    # ---- scene graph --------------------------------------------------
    def nodes(self):
        return self.json.get("nodes", [])

    def node_by_name(self, name):
        for i, nd in enumerate(self.nodes()):
            if nd.get("name") == name:
                return i, nd
        return None, None

    def find_nodes(self, name):
        """Substring / exact-with-suffix match, mirroring glTF importer naming."""
        exact = []
        fuzzy = []
        for i, nd in enumerate(self.nodes()):
            n = nd.get("name", "")
            if n == name:
                exact.append((i, nd))
            elif n.startswith(name):
                fuzzy.append((i, nd))
        return exact or fuzzy

    def node_world_scale(self, idx):
        """Approximate: glTF nodes here are unparented, so local == world basis."""
        nd = self.nodes()[idx]
        return nd.get("scale", [1.0, 1.0, 1.0])

    def parent_map(self):
        p = {}
        for i, nd in enumerate(self.nodes()):
            for c in nd.get("children", []):
                p[c] = i
        return p

    # ---- animations ---------------------------------------------------
    def animations(self):
        return self.json.get("animations", [])

    def channels_for_node(self, node_idx):
        out = []
        for ai, anim in enumerate(self.animations()):
            for ch in anim.get("channels", []):
                t = ch.get("target", {})
                if t.get("node") == node_idx:
                    out.append((ai, anim.get("name", "anim%d" % ai), t.get("path"), ch["sampler"]))
        return out

    def sampler_data(self, ai, sampler_idx):
        anim = self.animations()[ai]
        s = anim["samplers"][sampler_idx]
        times = self.read_accessor(s["input"])
        vals = self.read_accessor(s["output"])
        return times, vals, s.get("interpolation", "LINEAR")

    def sample_at_time(self, ai, sampler_idx, t, eps=1e-6):
        """Nearest-sample lookup (samplers here are baked per frame)."""
        times, vals, _ = self.sampler_data(ai, sampler_idx)
        best = min(range(len(times)), key=lambda i: abs(times[i] - t))
        if abs(times[best] - t) > eps and len(times) > 1:
            # report nearest anyway, flag distance
            return vals[best], times[best]
        return vals[best], times[best]

    def animation_time_range(self):
        lo, hi = None, None
        for anim in self.animations():
            for s in anim.get("samplers", []):
                acc = self.json["accessors"][s["input"]]
                mn = acc.get("min", [None])[0]
                mx = acc.get("max", [None])[0]
                if mn is None:
                    t = self.read_accessor(s["input"])
                    mn, mx = min(t), max(t)
                lo = mn if lo is None else min(lo, mn)
                hi = mx if hi is None else max(hi, mx)
        return lo, hi

    def summary(self):
        js = self.json
        return {
            "glb_bytes": len(self.raw),
            "nodes": len(js.get("nodes", [])),
            "meshes": len(js.get("meshes", [])),
            "materials": len(js.get("materials", [])),
            "animations": len(js.get("animations", [])),
            "animation_names": [a.get("name") for a in js.get("animations", [])],
            "images": len(js.get("images", [])),
        }


def main(path):
    g = Glb(path)
    s = g.summary()
    print("GLB path=%s" % path)
    for k, v in s.items():
        print("GLB %-18s %s" % (k, v))
    lo, hi = g.animation_time_range()
    print("GLB anim_time_range=%s..%s" % (lo, hi))
    for name in ("Product", "Idea"):
        hits = g.find_nodes(name)
        print("GLB node %-10s matches=%s" % (name, [h[1].get("name") for h in hits]))
        for i, nd in hits:
            print("GLB   idx=%d scale=%s translation=%s mesh=%s" % (
                i, nd.get("scale"), nd.get("translation"), nd.get("mesh")))
            for ai, aname, path_, si in g.channels_for_node(i):
                times, vals, interp = g.sampler_data(ai, si)
                print("GLB   ch anim=%-12s path=%-10s keys=%d t=%.4f..%.4f interp=%s" % (
                    aname, path_, len(times), times[0], times[-1], interp))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else r"G:\DSHProject\BlenderMcp\export\hero_v2.glb")
