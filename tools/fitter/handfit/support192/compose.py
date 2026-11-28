"""compose.py <out.png> <title> <Class> [...]: the support-fix sheet. Per gun three rows (near = the player's eye looking down at the off hand, side, eye = the r10/r11 camera): 1.92's hold (Depot
<set>/reference/192_poses <Class>_<view>.jpg) | steadied | the kick | firing | (reload, when shot) from rigsheet.py, then a
row with the fit's own views (fit192: 1.92 Ermac above, the FBX fit below) and its numbers."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, glob, json
from PIL import Image, ImageDraw
RUN = os.environ.get('S192_RUN', _DP.WORK + '/runs/sup192run'); REF = (_DP.SET + '/reference/192_poses')
def main(out, title, guns):
    w = h = 480; lh = 22; top = 30; sts = ['steady', 'kick', 'fire', 'reload']; rows = []
    for g in guns:
        for v in ('near', 'side', 'eye'): rows.append(('rig', g, v))
        rows.append(('fit', g, None))
    def rh(r): return (h + lh) if r[0] == 'rig' else 740
    H = top + sum(rh(r) for r in rows); sheet = Image.new('RGB', (w * 5, H), (24, 24, 24)); dr = ImageDraw.Draw(sheet)
    dr.text((8, 8), title, fill=(235, 235, 235)); y = top
    for kind, g, v in rows:
        if kind == 'rig':
            refs = glob.glob(os.path.join(REF, '%s_%s.*' % (g, {'near': 'eye'}.get(v, v))))
            dr.text((6, y + 4), '%s: 1.92 hold (%s)%s' % (g, v, '' if refs else ': no 1.92 render'), fill=(150, 200, 255))
            if refs:
                im = Image.open(refs[0]).convert('RGB'); im.thumbnail((w, h)); sheet.paste(im, (0, y + lh))
            for c, s in enumerate(sts):
                f = os.path.join(RUN, 'shots', '%s_%s_%s.png' % (g, v, s))
                if os.path.exists(f):
                    dr.text(((c + 1) * w + 6, y + 4), '%s, %s: %s (FBX support, 1.92 seed)' % (g, v, s), fill=(255, 220, 120)); sheet.paste(Image.open(f).convert('RGB'), ((c + 1) * w, y + lh))
        else:
            f = os.path.join(RUN, 'v_%s.png' % g); J = os.path.join(RUN, 'fit192_%s.json' % g)
            if os.path.exists(J):
                m = json.load(open(J))['m']; c = m['contact_cm']
                txt = ('%s fit (top: 1.92 Ermac on the gun; bottom: the FBX support fitted from it). pen into gun %.2f cm, into gun hand %.2f cm; '
                       'touching (<=0.3 cm) %d of 9 finger contacts; wrap %d deg round the part; palm gap %.2f; pads I/M/R/P/T %.2f/%.2f/%.2f/%.2f/%.2f; '
                       'proximal I/M/R/P %.2f/%.2f/%.2f/%.2f cm') % (g, m['pen_gun'], m['pen_gunhand'], m['touch9'], m['wrap_deg'], c['palm'], c['pad_I'], c['pad_M'], c['pad_R'], c['pad_P'], c['pad_T'], c['prox_I'], c['prox_M'], c['prox_R'], c['prox_P'])
                dr.text((6, y + 4), txt, fill=(200, 255, 200))
            if os.path.exists(f):
                im = Image.open(f).convert('RGB'); im.thumbnail((w * 5, 710)); sheet.paste(im, (0, y + 24))
        y += rh((kind, g, v))
    sheet.save(out); print(out, sheet.size)
if __name__ == '__main__': main(sys.argv[1], sys.argv[2], sys.argv[3:])
