"""sheet.py <out.png> <title> <png[:caption]>...: the rig frames side by side, 4 a row, each with its caption (TEST ONLY evidence sheet)."""
import os, sys
from PIL import Image, ImageDraw
out, title, items = sys.argv[1], sys.argv[2], sys.argv[3:]
cells = []
for it in items:
    p, _, cap = it.partition(':'); cells.append((Image.open(p).convert('RGB'), cap or os.path.basename(p)))
w, h = 360, 360; lh = 30; cols = 4; rows = (len(cells) + cols - 1) // cols
sh = Image.new('RGB', (cols * w, 30 + rows * (h + lh)), (22, 22, 28)); d = ImageDraw.Draw(sh); d.text((8, 8), title, fill=(240, 240, 240))
for k, (im, cap) in enumerate(cells):
    x = (k % cols) * w; y = 30 + (k // cols) * (h + lh); sh.paste(im.resize((w, h)), (x, y + lh))
    for n, line in enumerate([cap[i:i + 58] for i in range(0, len(cap), 58)][:2]): d.text((x + 4, y + 2 + 13 * n), line, fill=(255, 220, 120))
sh.save(out); print(out, sh.size)
