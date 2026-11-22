"""empty_skin.py (2.0.5e) -> src/models/rsq/ammobox/ammoa_empty.png

The chaingun's dropped, spent ammo box (owner 2026-11-22: "a resized, recoloured copy of the ammo box: smaller, dark or
grey-tinted, so it reads as EMPTY"). The box's skin is the 16 x 16 Doom palette (ammoa.png, BD22 VR's rsqvox/ammoa.png);
every entry becomes a dark grey of its own brightness, a touch cool, so the box keeps its shading and reads as an
empty, dead box. Run from the repo root: python tools/ammobox/empty_skin.py"""
import os
from PIL import Image
D = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'models', 'rsq', 'ammobox')
im = Image.open(os.path.join(D, 'ammoa.png')).convert('RGB')
out = Image.new('RGB', im.size)
for y in range(im.size[1]):
    for x in range(im.size[0]):
        r, g, b = im.getpixel((x, y))
        l = 0.30 * r + 0.59 * g + 0.11 * b
        out.putpixel((x, y), (int(l * 0.45), int(l * 0.46), int(l * 0.52)))
out.save(os.path.join(D, 'ammoa_empty.png'))
print('ammoa_empty.png: %d x %d' % im.size)
