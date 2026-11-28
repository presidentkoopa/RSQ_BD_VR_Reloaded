"""hands_heavies.png: per gun, from the eye and from the side: 1.92 render (<set>/reference/192_poses/<Class>_<view>.jpg),
then rest / steadied / firing (sheet_hv.py picks). usage: python3 compose_hv.py <out.png> <Gun,...> [title]"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os
from PIL import Image, ImageDraw
RUN = os.environ.get('HV_RUN', _DP.WORK + '/runs/lane_b_hvrun'); D = RUN + '/shots'; REF = (_DP.SET + '/reference/192_poses/')
out = sys.argv[1]; guns = sys.argv[2].split(','); title = sys.argv[3] if len(sys.argv) > 3 else ''
REFNAME = {'Machinegun': None}
sts = ['rest', 'steady', 'fire']; lab = {'rest': 'at rest', 'steady': 'steadied (off hand on, grip)', 'fire': 'firing (squeeze)'}
rows = [(g, v) for g in guns for v in ('eye', 'side')]
w, h = 480, 480
for g in guns:
    f = os.path.join(D, 'hv_eye_%s_rest.png' % g)
    if os.path.exists(f): w, h = Image.open(f).size; break
top = 34; lh = 22
sheet = Image.new('RGB', (w * 4, top + (h + lh) * len(rows)), (24, 24, 24)); dr = ImageDraw.Draw(sheet)
dr.text((8, 8), (title + '  ' if title else '') + 'QZD 17.3 rig, doom2 > brutal22test6 > BD_VoxelPack > pack. RIG ONLY, NOT HEADSET-CONFIRMED', fill=(230, 230, 230))
for r, (g, v) in enumerate(rows):
    y = top + r * (h + lh); rn = REFNAME.get(g, g)
    if rn and os.path.exists(REF + '%s_%s.jpg' % (rn, v)):
        ref = Image.open(REF + '%s_%s.jpg' % (rn, v)).convert('RGB'); ref = ref.resize((w, int(ref.size[1] * w / ref.size[0])))
        dr.text((6, y + 4), '%s: 1.92 (%s)' % (g, v), fill=(150, 200, 255)); sheet.paste(ref.crop((0, 0, w, h)), (0, y + lh))
    else:
        dr.text((6, y + 4), '%s: no 1.92 render (no 1.92 hold)' % g, fill=(150, 200, 255))
    for c, s in enumerate(sts):
        f = os.path.join(D, 'hv_%s_%s_%s.png' % (v, g, s))
        dr.text(((c + 1) * w + 6, y + 4), '%s, %s: %s' % (g, v, lab[s]), fill=(255, 220, 120))
        if os.path.exists(f): sheet.paste(Image.open(f).convert('RGB'), ((c + 1) * w, y + lh))
sheet.save(out); print(out, sheet.size)
