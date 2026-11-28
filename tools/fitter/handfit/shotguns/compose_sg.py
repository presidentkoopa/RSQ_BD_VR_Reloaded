"""b4_hands.png: each fitted gun at rest / steadied / firing, from the eye and from the side (QZD 17.3 rig frames), next to its
1.92 render (<set>/reference/192_poses/<Class>_eye.jpg / _side.jpg)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os
from PIL import Image, ImageDraw
D = (_DP.WORK + '/runs/lane_b_sgrun' + '/shots'); REF = (_DP.SET + '/reference/192_poses/')
guns = sys.argv[1].split(','); pick = dict(a.split('=') for a in sys.argv[2:])
sts = ['rest', 'steady', 'fire']; lab = {'rest': 'at rest', 'steady': 'steadied (off hand on, grip)', 'fire': 'firing (squeeze)'}
rows = [(g, v) for g in guns for v in ('eye', 'side')]
w, h = Image.open(os.path.join(D, 'sgeye_%s_rest_5.png' % guns[0])).size; top = 34; lh = 22
sheet = Image.new('RGB', (w * 4, top + (h + lh) * len(rows)), (24, 24, 24)); dr = ImageDraw.Draw(sheet)
dr.text((8, 8), 'shotguns lane: FBX gun hand fitted from 1.92, gun moved to the hand (port_sg.py). QZD 17.3 rig, doom2 > brutal22test6 > BD_VoxelPack > pack. Rig only, not headset-confirmed', fill=(230, 230, 230))
for r, (g, v) in enumerate(rows):
    y = top + r * (h + lh)
    ref = Image.open(REF + '%s_%s.jpg' % (g, v)).convert('RGB'); ref = ref.resize((w, int(ref.size[1] * w / ref.size[0])))
    dr.text((6, y + 4), '%s: 1.92 (%s)' % (g, v), fill=(150, 200, 255)); sheet.paste(ref.crop((0, 0, w, h)), (0, y + lh))
    for c, s in enumerate(sts):
        f = os.path.join(D, 'sg%s_%s_%s_%s.png' % (v, g, s, pick.get('%s_%s_%s' % (g, v, s), '5')))
        dr.text(((c + 1) * w + 6, y + 4), '%s, %s: %s' % (g, v, lab[s]), fill=(255, 220, 120))
        if os.path.exists(f): sheet.paste(Image.open(f).convert('RGB'), ((c + 1) * w, y + lh))
sheet.save((_DP.WORK + '/out' + '/hands_shotguns.png')); print(sheet.size)
