from PIL import Image, ImageDraw
import os
views = ["front", "right", "back", "top"]
rows = [("v12", "pin_v12"), ("v13 P0", "pin_p0")]
cell_w, cell_h, pad, label_h = 440, 440, 8, 26
W = len(views) * (cell_w + pad) + pad
H = len(rows) * (cell_h + label_h + pad) + pad
sheet = Image.new("RGB", (W, H), (26, 26, 28))
d = ImageDraw.Draw(sheet)
for r, (label, prefix) in enumerate(rows):
    y = pad + r * (cell_h + label_h + pad)
    for c, v in enumerate(views):
        p = f"review/v13/{prefix}_{v}.png"
        x = pad + c * (cell_w + pad)
        d.text((x + 4, y + 6), f"{label}  {v.upper()}", fill=(235, 235, 235))
        im = Image.open(p).convert("RGB")
        im.thumbnail((cell_w, cell_h))
        sheet.paste(im, (x + (cell_w - im.width) // 2, y + label_h))
sheet.save("review/v13/contact_v12_vs_p0.png")
print("ok", sheet.size)

# apples-to-apples shell colour: same camera now, so same pixels
for tag in ("pin_v12", "pin_p0"):
    for view in ("front", "back"):
        im = Image.open(f"review/v13/{tag}_{view}.png").convert("RGB")
        w, h = im.size
        px = list(im.crop((int(w*0.44), int(h*0.42), int(w*0.50), int(h*0.52))).getdata())
        n = len(px)
        avg = tuple(sum(c[i] for c in px)//n for i in range(3))
        print(tag, view, "shell patch #%02X%02X%02X" % avg)
