"""look.py: check views (lane_c render.py): Ermac's frame dark, the FBX hand orange, the object grey. Columns: from the left,
from above, from the right, and from the player's eye (behind-above, toward the body's centre; a right hand in the drawn frame)."""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ohfit, render
from PIL import Image, ImageDraw
EYE = np.array([-30.0, -12.0, 22.0])	# drawn cm from the hand's centre: behind, toward the head (-L for this right-hand frame), above
def views(rows, out, title='', box=13):
    """rows: list of (label, [mesh dicts])"""
    ims_all = []
    for lab, ms in rows:
        allV = np.concatenate([m['V'] for m in ms if m.get('centre', True)]); c = (allV.min(0) + allV.max(0)) / 2; ims = []
        for kind in ('left', 'top', 'side'):
            R, U, T = render.VIEWS[kind]; h = c @ R; v = c @ U
            ims.append(render.render(ms, kind=kind, rng=(h - box, h + box, v - box, v + box), px=11))
        ims.append(render.render(ms, eye=c + EYE, look=c, W=ims[0].width, H=ims[0].height, fov=50))
        ims_all.append((lab, ims))
    W = sum(i.width for i in ims_all[0][1]) + 8; H = sum(r[1][0].height + 16 for r in ims_all) + 26
    sh = Image.new('RGB', (W, H), (20, 20, 28)); d = ImageDraw.Draw(sh); d.text((6, 6), title, fill=(240, 240, 240)); y = 24
    for lab, r in ims_all:
        d.text((6, y), lab, fill=(255, 220, 120)); y += 14; x = 4
        for im in r: sh.paste(im, (x, y)); x += im.width
        y += r[0].height + 2
    sh.save(out); return out
def m(V, F, col): return dict(V=np.asarray(V), F=np.asarray(F), col=col)
