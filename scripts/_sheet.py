import bpy, os, numpy as np
base = r"G:\DSHProject\BlenderMcp\renders"

def sheet(out_name, names):
    tiles = []
    for fn in names:
        p = os.path.join(base, fn)
        if not os.path.exists(p):
            print("MISSING " + p); return
        img = bpy.data.images.load(p)
        w, h = img.size
        a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
        tiles.append(a)
        bpy.data.images.remove(img)
    h, w = tiles[0].shape[0], tiles[0].shape[1]
    out = np.zeros((h, w * len(tiles), 4), dtype=np.float32)
    out[..., 3] = 1.0
    for i, a in enumerate(tiles):
        out[:, i * w:(i + 1) * w, :] = a
    res = bpy.data.images.new(out_name, width=out.shape[1], height=h, alpha=True)
    res.pixels = out[::-1].ravel().tolist()
    res.file_format = 'PNG'
    dst = os.path.join(base, out_name)
    res.filepath_raw = dst
    res.save()
    print("WROTE " + dst)

sheet("cmp_f001.png", ["tripo_f001_34.png", "p19_f001_34.png", "v2_f001_34.png"])
sheet("cmp_f120.png", ["p19_f120_34.png", "v2_f120_34.png"])
sheet("cmp_f220.png", ["p19_f220_34.png", "v2_f220_34.png"])