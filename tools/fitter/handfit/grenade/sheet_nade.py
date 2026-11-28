"""sheet_nade.py: OFFLINE fit sheet of fit_nade.py's result (the grenade moved by the fit and the solved FBX hand, drawn controller
frame, flat-shaded painter's render; sheet_melee.py's panel). Not an engine frame.
usage: python3 sheet_nade.py <nade_fit.json> <out.png> [--title TEXT]"""
import os, sys, json, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
import fit_nade as N, handmodel
VIEWS = {'side (from right)': ([0, -1, 0.], [0, 0, 1.]), 'side (from left)': ([0, 1, 0.], [0, 0, 1.]), 'top': ([0, 0, 1.], [1, 0, 0.]),
         'front': ([1, 0, 0.], [0, 0, 1.]), 'back': ([-1, 0, 0.], [0, 0, 1.]), 'eye (behind, above)': ([-0.75, -0.25, 0.6], [0, 0, 1.]), 'below': ([0, 0, -1.], [1, 0, 0.])}
def panel(meshes, view, W, box, title):
    d, up = (np.array(v, float) for v in VIEWS[view]); d /= np.linalg.norm(d); r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    lo, hi = box; c = (lo + hi) / 2; s = 0.9 * W / max(np.linalg.norm(hi - lo), 1.0)
    img = Image.new('RGB', (W, W), (38, 40, 52)); dr = ImageDraw.Draw(img); polys = []; Lt = np.array([0.3, -0.5, 0.8]); Lt /= np.linalg.norm(Lt)
    for F, V, col in meshes:
        A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]; n = np.cross(B - A, C - A); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
        sh = 0.3 + 0.7 * np.abs(n @ Lt); dep = ((A + B + C) / 3 - c) @ d
        P = [np.stack([W / 2 + ((X - c) @ r) * s, W / 2 - ((X - c) @ u) * s], 1) for X in (A, B, C)]
        for i in range(len(F)): polys.append((dep[i], (tuple(P[0][i]), tuple(P[1][i]), tuple(P[2][i])), tuple(int(v * sh[i]) for v in col)))
    polys.sort(key=lambda t: t[0])
    for _, pts, cl in polys: dr.polygon(pts, fill=cl)
    dr.text((6, 4), title, fill=(235, 235, 235)); return img
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('fit'); ap.add_argument('out'); ap.add_argument('--title', default=''); a = ap.parse_args()
    J = json.load(open(a.fit)); F, V, S = N.nade_mesh(); R = np.array(J['nade']['R']); t = np.array(J['nade']['t']); Vm = V @ R.T + t
    X = np.array(J['X']); H = handmodel.FbxHand('R'); cols = {0: (150, 150, 165), 1: (150, 150, 165), 2: (200, 190, 90), 3: (120, 170, 120), 4: (150, 150, 165)}
    meshes = [(F[S == k], Vm, cols[k]) for k in range(int(S.max()) + 1)] + [(np.asarray(H.F), X, (225, 175, 140))]
    P = np.concatenate([Vm, X]); full = (P.min(0), P.max(0)); zc = Vm.mean(0); zoom = (zc - 11, zc + 11)
    W = 420; tiles = [panel(meshes, 'eye (behind, above)', W, full, 'whole, eye (behind, above)'), panel(meshes, 'side (from right)', W, full, 'whole, side (right)')]
    for v in ('side (from left)', 'front', 'back', 'top', 'below'): tiles.append(panel(meshes, v, W, zoom, 'grenade, ' + v))
    tiles.append(panel([(F[S == k], Vm, cols[k]) for k in range(int(S.max()) + 1)], 'side (from left)', W, zoom, 'grenade alone, from left (yellow ring, green spoon)'))
    cols_ = 4; rows = 2; sheet = Image.new('RGB', (cols_ * W, rows * W + 60), (20, 20, 26)); dr = ImageDraw.Draw(sheet)
    for k, tl in enumerate(tiles): sheet.paste(tl, ((k % cols_) * W, 60 + (k // cols_) * W))
    m = J['metrics']
    dr.text((8, 6), 'HandGrenades FBX hand (fit_nade.py) %s: pen %.2f cm, palm gap %.2f, pads I/M/R/P %.2f/%.2f/%.2f/%.2f, wrap %.0f/%.0f/%.0f/%.0f deg, thumb-spoon %.2f, cuff %.2f, grenade turn %.1f deg move %.2f cm' % (
        a.title, m['pen'], m['palm_gap'], m['gap_I'], m['gap_M'], m['gap_R'], m['gap_P'], m['wrap_I'], m['wrap_M'], m['wrap_R'], m['wrap_P'], m['gap_T_spoon'], m['cuff_max'], m['nade_turn_deg'], m['nade_move_cm']), fill=(240, 240, 240))
    dr.text((8, 30), 'OFFLINE FIT SHEET (drawn controller frame, cm). Not an engine frame.', fill=(255, 200, 120))
    sheet.save(a.out); print('wrote', a.out)
if __name__ == '__main__': main()
