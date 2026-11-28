"""view.py: shaded check views of a support fit (lane_c render.py rasteriser): gun grey (cropped round the hand), the gun hand
blue, the support hand orange (FBX) or dark (1.92 Ermac). Row 1 = 1.92's hold, row 2 = the FBX fit; columns = from the left,
from below, from behind-above (near the player's eye)."""
import numpy as np, render
from PIL import Image, ImageDraw
def _crop(V, F, c, r):
    k = (np.abs(V[F].mean(1) - c) < r).all(1); return F[k]
def views(S, X, out, title='', box=14):
    c = X.mean(0); Fg = _crop(S.Vg, S.Fg, c, box + 6)
    gun = dict(V=S.Vg, F=Fg, col=(165, 165, 170)); gh = dict(V=S.Xh, F=S.Fh, col=(90, 130, 200))
    rows = []
    for hand in (dict(V=S.E, F=S.Fe, col=(60, 45, 40)), dict(V=X, F=S.Fl, col=(235, 150, 90))):
        ims = []
        for kind in ('left', 'bottom'):
            R, U, T = render.VIEWS[kind]; h = c @ R; v = c @ U
            ims.append(render.render([gun, gh, hand], kind=kind, rng=(h - box, h + box, v - box, v + box), px=12))
        eye = c + np.array([-38.0, 10.0, 22.0]); ims.append(render.render([gun, gh, hand], eye=eye, look=c, W=336, H=336, fov=45))
        rows.append(ims)
    W = sum(i.width for i in rows[0]) + 8; H = sum(r[0].height for r in rows) + 30
    sh = Image.new('RGB', (W, H), (20, 20, 28)); d = ImageDraw.Draw(sh); d.text((6, 8), title, fill=(240, 240, 240)); y = 26
    for r in rows:
        x = 4
        for im in r: sh.paste(im, (x, y)); x += im.width
        y += r[0].height
    sh.save(out)
