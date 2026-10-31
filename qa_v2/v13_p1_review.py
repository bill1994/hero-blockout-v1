"""P1 review: sample rendered colours against section 5.1, and build the comparison sheet.

Two jobs, both about not trusting the eye:

1. Palette sampling. Quantise a render to its dominant colours, ignore the studio
   backdrop, and report each cluster next to the nearest section 5.1 target with its
   distance. This is how "the front looks washed out" gets answered with a number
   instead of an opinion.

2. Contact sheet. The reference sheet's three panels (front / three-quarter / top) side
   by side with the matching renders, so P1 can be judged the way section 6 asks.

Runs on the workspace Python (Pillow), not inside Blender.

Usage:
    python qa_v2/v13_p1_review.py --palette review/v13/p1c_front.png [...] \
        --sheet review/v13/p1_contact.png \
        --panels review/v13/p1c_front.png,review/v13/p1c_right.png,review/v13/p1c_top.png
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# section 5.1, sRGB
TARGETS = {
    "cream": "#DDD5C8",
    "mint": "#A6BAB2",
    "orange": "#C5793E",
    "charcoal": "#424847",
    "cyan_glow": "#8BF5F2",
}


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def sample(path, n_colors=8, bg_tol=26):
    im = Image.open(path).convert("RGB")
    small = im.resize((max(1, im.width // 2), max(1, im.height // 2)))

    # The backdrop is the dominant flat colour at the corners. Quantising first and
    # filtering afterwards lets the backdrop's gradient eat most of the palette slots
    # (measured: 8 clusters produced 1 usable colour), so the subject pixels are
    # collected first and only then quantised.
    corners = [small.getpixel(p) for p in ((2, 2), (small.width - 3, 2),
                                           (2, small.height - 3),
                                           (small.width - 3, small.height - 3))]
    bg = min(corners, key=lambda c: sum(c))

    px = list(small.getdata())
    subject = [c for c in px if dist(c, bg) > bg_tol]
    if not subject:
        return {"file": path, "background": "#%02X%02X%02X" % bg, "clusters": []}

    strip = Image.new("RGB", (len(subject), 1))
    strip.putdata(subject)
    q = strip.quantize(colors=min(n_colors, max(2, len(set(subject)))), method=Image.MEDIANCUT)
    pal = q.getpalette()
    counts = sorted(q.getcolors(), reverse=True)
    total = sum(c for c, _ in counts)

    rows = []
    for cnt, idx in counts:
        rgb = tuple(pal[idx * 3: idx * 3 + 3])
        best = min(TARGETS.items(), key=lambda kv: dist(rgb, hex_rgb(kv[1])))
        rows.append({
            "hex": "#%02X%02X%02X" % rgb,
            "share_of_subject": round(cnt / total, 4),
            "nearest": best[0],
            "target": best[1],
            "dist": round(dist(rgb, hex_rgb(best[1])), 1),
        })
    rows.sort(key=lambda r: -r["share_of_subject"])
    return {"file": path, "background": "#%02X%02X%02X" % bg,
            "subject_pixels": len(subject), "clusters": rows}


def fit(im, size):
    im = im.copy()
    im.thumbnail(size, Image.LANCZOS)
    canvas = Image.new("RGB", size, (24, 24, 26))
    canvas.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
    return canvas


def build_sheet(ref_path, panels, out_path, cell=(430, 430)):
    ref = Image.open(ref_path).convert("RGB")
    # document 5.2: the sheet splits at x [85,682] [776,1198] [1268,1852]
    boxes = [(85, 200, 682, 900), (776, 200, 1198, 900), (1268, 200, 1852, 900)]
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    rows = 2
    sheet = Image.new("RGB", (cell[0] * len(boxes), cell[1] * rows + 30 * rows),
                      (24, 24, 26))
    d = ImageDraw.Draw(sheet)

    for i, box in enumerate(boxes[:len(panels)]):
        crop = ref.crop(box)
        sheet.paste(fit(crop, cell), (i * cell[0], 0))
        d.text((i * cell[0] + 8, cell[1] + 4), "reference %d" % (i + 1), fill=(230, 230, 230), font=font)

    for i, p in enumerate(panels):
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGB")
        sheet.paste(fit(im, cell), (i * cell[0], cell[1] + 30))
        d.text((i * cell[0] + 8, cell[1] * 2 + 34),
               os.path.basename(p), fill=(230, 230, 230), font=font)

    sheet.save(out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--palette", nargs="*", default=[])
    ap.add_argument("--sheet")
    ap.add_argument("--panels", default="")
    ap.add_argument("--reference", default="reference/style_v13_ref.png")
    args = ap.parse_args()

    if args.palette:
        import json
        results = [sample(p) for p in args.palette]
        for r in results:
            print("PALETTE %s  (bg %s)" % (os.path.basename(r["file"]), r["background"]))
            for c in r["clusters"][:6]:
                print("   %s  %5.1f%%  nearest %-9s %s  d=%.1f" % (
                    c["hex"], c["share_of_subject"] * 100, c["nearest"], c["target"], c["dist"]))
        out = os.path.splitext(args.palette[0])[0] + "_palette.json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        print("WROTE %s" % out)

    if args.sheet and args.panels:
        panels = [p for p in args.panels.split(",") if p]
        p = build_sheet(args.reference, panels, args.sheet)
        print("SHEET %s" % p)


if __name__ == "__main__":
    main()
