import glob, os
from PIL import Image, ImageDraw, ImageChops, ImageStat

SRC = r"G:\DSHProject\BlenderMcp\qa_v2\p0"
OUT = r"G:\DSHProject\BlenderMcp\qa_v2\p0_contact.png"
files = sorted(glob.glob(os.path.join(SRC, "p0_f*.png")))
assert files, "no frames"
COLS = 5
LABEL_H = 26
imgs = [Image.open(f).convert("RGB") for f in files]
W, H = imgs[0].size
rows = (len(imgs) + COLS - 1) // COLS
sheet = Image.new("RGB", (W * COLS, (H + LABEL_H) * rows), (24, 24, 24))
d = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(files, imgs)):
    r, c = divmod(i, COLS)
    x, y = c * W, r * (H + LABEL_H)
    tag = os.path.splitext(os.path.basename(f))[0].replace("p0_f", "f")
    d.text((x + 8, y + 5), tag, fill=(255, 220, 90))
    sheet.paste(im, (x, y + LABEL_H))
sheet.save(OUT)

diffs = []
for a, b in zip(files[:-1], files[1:]):
    ia = Image.open(a).convert("L")
    ib = Image.open(b).convert("L")
    diff = ImageChops.difference(ia, ib)
    st = ImageStat.Stat(diff)
    diffs.append("%s->%s mean=%.2f" % (
        os.path.basename(a)[3:7], os.path.basename(b)[3:7], st.mean[0]))
print("sheet=" + OUT + " size=%dB" % os.path.getsize(OUT))
print("\n".join(diffs))
