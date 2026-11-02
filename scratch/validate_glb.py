import json
import struct
import sys


def load(path):
    with open(path, "rb") as fh:
        data = fh.read()
    magic, version, length = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF", magic
    assert length == len(data), (length, len(data))
    off = 12
    js = None
    bin_len = 0
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bin_len = clen
        off += 8 + clen + ((4 - clen % 4) % 4 if clen % 4 else 0)
    return version, len(data), js, bin_len


def main(path):
    version, size, js, bin_len = load(path)
    tris = 0
    prims = 0
    for mesh in js.get("meshes", []):
        for prim in mesh.get("primitives", []):
            prims += 1
            if "indices" in prim:
                tris += js["accessors"][prim["indices"]]["count"] // 3
    mats = [m.get("name") for m in js.get("materials", [])]
    anims = [a.get("name") for a in js.get("animations", [])]
    out = {
        "gltf_version": version,
        "file_bytes": size,
        "bin_bytes": bin_len,
        "nodes": len(js.get("nodes", [])),
        "meshes": len(js.get("meshes", [])),
        "primitives": prims,
        "triangles": tris,
        "materials": len(mats),
        "material_names": mats,
        "animations": len(anims),
        "animation_names": anims,
        "images": len(js.get("images", [])),
        "has_skins": len(js.get("skins", [])) > 0,
        "generator": js.get("asset", {}).get("generator"),
    }
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
