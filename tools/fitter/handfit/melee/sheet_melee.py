"""Melee hands lane: the FIT sheet of one farm result (offline: the weapon mesh moved by the fit's shift and the solved FBX hand(s),
both in the controller frame, flat-shaded painter's render; no engine). It shows the fit, not the game: the engine check is the
port lane's (rig) and then the owner's headset.
usage: python3 sheet_melee.py <Class> <result_dir> <out.png> [--support <support.json>] [--title TEXT]
  result_dir: a farm job folder (curl3_<C>.json, job.json); the hand drawn is the trigger pose (Xt).
  --support: support_melee.py's json (L hand vertices X_L in the same frame) drawn in a second colour."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, json, argparse, numpy as np
import os as _fl_os; FITTER_LIB = _fl_os.environ.get('RS_FITTER_LIB', _fl_os.path.join(_fl_os.path.dirname(_fl_os.path.abspath(__file__)), '..', 'fitter_lib'))	# the batch 1-4 fitter modules (were <work>/runs/lane_b_b*run/tools)
from PIL import Image, ImageDraw, ImageFont
FH = os.environ.get('MELEE_FITTER_HOME', _DP.WORK + '/fitter_home/'); sys.path.insert(0, FH)
for p in (_DP.CORE + '/hands_tool', FITTER_LIB): sys.path.insert(0, p)
import scene, handmodel
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = _DP.SRC
def weapon(g):
    C = json.load(open(os.path.join(HERE, 'melee.json')))[g]; it = dict(C['it']); it['path'] = os.path.join(SRC, 'models/bd', it['path'])
    F, V = scene.merged(it); return np.asarray(F), V
VIEWS = {'side (from right)': (np.array([0, -1, 0.]), np.array([0, 0, 1.])), 'side (from left)': (np.array([0, 1, 0.]), np.array([0, 0, 1.])),
         'top': (np.array([0, 0, 1.]), np.array([1, 0, 0.])), 'front': (np.array([1, 0, 0.]), np.array([0, 0, 1.])),
         'eye (behind, above)': (np.array([-0.75, -0.25, 0.6]), np.array([0, 0, 1.]))}
def panel(meshes, view, W, Hh, box, title):
    d, up = VIEWS[view]; d = d / np.linalg.norm(d); r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    lo, hi = box; c = (lo + hi) / 2; span = max(np.linalg.norm(hi - lo), 1.0); s = 0.9 * min(W, Hh) / span
    img = Image.new('RGB', (W, Hh), (38, 40, 52)); dr = ImageDraw.Draw(img); polys = []
    Lt = np.array([0.3, -0.5, 0.8]); Lt /= np.linalg.norm(Lt)
    for F, V, col in meshes:
        A, B, Cc = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]; n = np.cross(B - A, Cc - A); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
        sh = 0.3 + 0.7 * np.abs(n @ Lt); dep = ((A + B + Cc) / 3 - c) @ d
        P = [np.stack([W / 2 + ((X - c) @ r) * s, Hh / 2 - ((X - c) @ u) * s], 1) for X in (A, B, Cc)]
        keep = np.linalg.norm(np.cross(B - A, Cc - A), axis=1) > 1e-9
        for i in np.where(keep)[0]: polys.append((dep[i], (tuple(P[0][i]), tuple(P[1][i]), tuple(P[2][i])), tuple(int(v * sh[i]) for v in col)))
    polys.sort(key=lambda t: t[0])
    for _, pts, cl in polys: dr.polygon(pts, fill=cl)
    o = -c; dr.ellipse((W / 2 + (o @ r) * s - 4, Hh / 2 - (o @ u) * s - 4, W / 2 + (o @ r) * s + 4, Hh / 2 - (o @ u) * s + 4), outline=(255, 230, 0))
    dr.text((6, 4), title, fill=(235, 235, 235)); return img
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('g'); ap.add_argument('res'); ap.add_argument('out'); ap.add_argument('--support'); ap.add_argument('--title', default='')
    ap.add_argument('--zoom', type=float, default=14.0); a = ap.parse_args()
    import glob
    J = json.load(open(glob.glob(os.path.join(a.res, 'curl3_%s*.json' % a.g))[0])); job = json.load(open(os.path.join(a.res, 'job.json')))
    d = np.array(J['shift']); F, V = weapon(a.g); Vm = V + d          # the weapon moved by the fit (wrist pinned)
    HR = handmodel.FbxHand('R'); Xt = np.array(J['Xt'])               # stored in the controller frame (gun moved by d)
    meshes = [(F, Vm, (150, 150, 165)), (np.asarray(HR.F), Xt, (225, 175, 140))]
    pts = [Xt]
    if a.support:
        S = json.load(open(a.support)); HL = handmodel.FbxHand('L'); XL = np.array(S['X_L_ctrl']); meshes.append((np.asarray(HL.F), XL, (140, 200, 225))); pts.append(XL)
    P = np.concatenate(pts); full = (np.minimum(Vm.min(0), P.min(0)), np.maximum(Vm.max(0), P.max(0)))
    zc = Xt.mean(0); zoom = (zc - a.zoom, zc + a.zoom)
    W = 460; tiles = [panel(meshes, 'side (from right)', W, W, full, 'whole, side (right)'), panel(meshes, 'eye (behind, above)', W, W, full, 'whole, eye')]
    for v in ('side (from right)', 'side (from left)', 'top', 'front'): tiles.append(panel(meshes, v, W, W, zoom, 'grip, ' + v))
    if a.support:
        zs = XL.mean(0); tiles.append(panel(meshes, 'side (from left)', W, W, (zs - a.zoom, zs + a.zoom), 'support, side (left)'))
        tiles.append(panel(meshes, 'eye (behind, above)', W, W, (zs - a.zoom, zs + a.zoom), 'support, eye'))
    cols = 4; rows = (len(tiles) + cols - 1) // cols; sheet = Image.new('RGB', (cols * W, rows * W + 70), (20, 20, 26)); dr = ImageDraw.Draw(sheet)
    for k, t in enumerate(tiles): sheet.paste(t, ((k % cols) * W, 70 + (k // cols) * W))
    m = job.get('metrics', {}).get('curl', {}).get('trigger', {})
    txt = '%s  %s  (%s)  trigger pose: pad->target %.2f cm, pen %.2f cm, palm gap %.2f cm, web %.2f cm; shift d %s cm; %.1f min' % (
        a.g, os.path.basename(a.res.rstrip('/')), a.title, m.get('padI_trig', -1), m.get('pen', -1), m.get('gap_palm', -1), m.get('gap_web', -1), np.round(d, 2).tolist(), job.get('minutes', -1))
    dr.text((8, 8), txt, fill=(240, 240, 240)); dr.text((8, 30), 'OFFLINE FIT SHEET (mesh + solved FBX hand in the fitter O frame = 1.92 controller frame; yellow ring = its origin). Not an engine frame: not shown working in game.', fill=(255, 200, 120))
    if a.support: dr.text((8, 50), 'blue = support (FBX L hand): ' + json.dumps({k: round(v, 2) for k, v in S.get('metrics', {}).items() if isinstance(v, (int, float))}), fill=(160, 210, 240))
    sheet.save(a.out); print('wrote', a.out)
if __name__ == '__main__': main()
