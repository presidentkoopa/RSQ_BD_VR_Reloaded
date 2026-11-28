"""fit192.py <Class> [--out DIR] [--names a.md3,b.md3] [--w JSON] : the FBX support hand fitted FROM THE 1.92 HOLD.

Seed = the FBX left hand already fitted to 1.92's Ermac support frame (s192.Scene: lane_c landmarks_ermac_frames 'hand2:<k>'),
carried onto the ported gun with the 1.92 gun -> gun-now rigid. Then ONE solve (scipy least_squares) moves it as little as it can:
  - the hand out of the gun (pen > 0.2 cm) and out of the gun hand (pen > 0.3 cm);
  - the palm, the four finger pads, the four proximal finger segments and the thumb pad onto the gun's surface (gap > 0.15 cm);
  - the wrist (cuff) stays where 1.92's was (0.3 / cm), the palm near 1.92's (0.1 / cm), the joints near the seed's (0.2 / unit).
Measured after (exact, no grid: exactpen): pen into the gun / gun hand, each contact gap, WRAP = how many of the 9 finger
contacts (pads + proximal, I M R P + thumb pad) touch (<= 0.3 cm) and the angle round the support part covered by touching hand
vertices (in the plane across the part's axis: the bore F for a forend / tube, the grip axis for a vertical grip).
Writes <out>/fit192_<Class>.json (p, X, measurements) and <out>/fit192_<Class>.png (views)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, json, argparse, time, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import s192, sdf as SDFm, view
from scipy.optimize import least_squares
import evaluate, handmodel
FING = 'IMRP'
def regions(S):
    L = dict(S.L); L['_reg'] = s192.jl(os.path.join(s192.LANE, 'regions.json'))['fbx']
    R = {k: np.array(evaluate.reg(L, k)) for k in ['palm'] + ['pad_' + f for f in FING + 'T']}
    for f in FING + 'T': R['prox_' + f] = np.array([L['prox_' + f]])
    return R, L
def axis_of(S, kind):
    if kind == 'vgrip': return np.array(S.r192.get('vgrip_axis', [0.0, 0.0, 1.0]))
    return S.Rm @ np.array([1.0, 0, 0]) / np.linalg.norm(S.Rm @ np.array([1.0, 0, 0]))	# the bore (1.92 F) carried with the gun
def wrap(S, X, ex, kind, R, tol=0.3):
    d = ex.unsigned(X); a = axis_of(S, kind)
    inner = np.concatenate([R[k] for k in R]); touch = inner[d[inner] <= tol]
    cont = {k: round(float(d[R[k]].min()), 2) for k in R}
    n9 = sum(cont[k] <= tol for k in ['pad_' + f for f in FING + 'T'] + ['prox_' + f for f in FING])
    if len(touch) < 3: return cont, n9, 0.0
	# angle round the part: centre = the gun's surface points near the touching hand vertices, projected across the axis
    P = X[touch]; c = S.Vg[np.linalg.norm(S.Vg - P.mean(0), axis=1) < 6]; c = c.mean(0) if len(c) else P.mean(0)
    u = np.cross(a, [0, 0, 1.0] if abs(a[2]) < 0.9 else [1.0, 0, 0]); u /= np.linalg.norm(u); v = np.cross(a, u)
    ang = np.sort(np.degrees(np.arctan2((P - c) @ v, (P - c) @ u)) % 360); gaps = np.diff(np.r_[ang, ang[0] + 360])
    return cont, n9, float(360 - gaps.max())
def fit(g, out, names=None, W=None, kind='wrap', nfev=60, gun192=None, as_=None, vgrip=None, seed_from=None, seed_fit=None, at=None):
    t0 = time.time(); src = g; g = as_ or g
    if seed_fit:	# the 1.92 hold is too weak to copy (owner review): another gun's FINISHED fit (fit192_<src>.json), moved onto this gun's underside
        Ss = s192.Scene(seed_fit); F0 = json.load(open(os.path.join(out, 'fit192_%s.json' % seed_fit))); Ss.p0 = np.array(F0['p']); Ss.X0 = Ss.hand(Ss.p0)
        S = s192.retarget(Ss, g, names, at); seed_from = 'fit:' + seed_fit
    elif seed_from: S = s192.retarget(s192.Scene(seed_from), g, names)	# no 1.92 hold: another gun's 1.92 hold, moved by the SupportPoint difference
    else: S = s192.Scene(g, names=names, gun192=gun192)
    R, L = regions(S)	# as_: fit under another name (not for variants: they copy the Brutal gun's rows)
    if seed_fit: seedfit = dict(seed='the finished fit of %s, moved onto this gun' % seed_fit, at_cm=at)
    else: S.p0, S.X0, seedfit = s192.seed_refit(S); print(g, 'seed refit to 1.92 Ermac', seedfit, flush=True)
    if vgrip is not None:	# a measured vertical foregrip: the 1.92 fist moved onto it first (s192.onto_vgrip)
        c, a = np.array(vgrip[:3]), np.array(vgrip[3:]); S.r192 = dict(S.r192, vgrip_axis=list(a / np.linalg.norm(a))); kind = 'vgrip'
        S.p0 = s192.onto_vgrip(S, S.p0, c, a); S.X0 = S.hand(S.p0); seedfit = dict(seedfit, onto_vgrip=dict(centre=list(c), axis=list(np.round(a / np.linalg.norm(a), 3))))
    w = dict(pen=8.0, penh=6.0, con=1.0, palmc=1.0, across=0.0, across_cos=0.5, thumb=0.7, cuff=0.5, palm=0.1, q=0.2, tol_pen=0.1, tol_penh=0.2, tol_con=0.15); w.update(W or {})
    lo = S.X0.min(0) - 6; hi = S.X0.max(0) + 6
    G = SDFm.SDF(S.Vg, S.Fg, lo, hi); H = SDFm.SDF(S.Xh, S.Fh, lo, hi); print(g, 'sdf ready (%d / %d tris) %.0fs' % (G.ntri, H.ntri, time.time() - t0), flush=True)
    if w.get('lower', 1) and kind != 'vgrip':	# a seed deep in the gun (big guns: 1.92's hold 2-3 cm into the body) traps the solve: lower it first,
        X = S.hand(S.p0)	# 1 mm steps (support_gun.py's rule), until the hand is <= 0.3 cm into the gun (grid), at most 5 cm
        for dz in np.arange(0.0, 5.01, 0.1):
            if -G.signed(X[::2] - np.array([0, 0, dz])).min() <= 0.3: break
        if dz > 0: S.p0 = s192.apply_rigid(S, S.p0, np.eye(3), np.array([0, 0, -dz])); S.X0 = S.hand(S.p0); seedfit = dict(seedfit, lowered_cm=round(float(dz), 1)); print(g, 'seed lowered %.1f cm out of the gun' % dz, flush=True)
    ax_ = axis_of(S, kind); p0 = S.p0.copy(); X0 = S.X0; cuff0 = X0[L['cuff']].mean(0); palm0 = X0[R['palm']].mean(0); sub = np.arange(len(X0))
    def X_of(z): return S.hand(np.r_[z[:6], p0[6], z[6:]])
    allr = np.concatenate(list(R.values())); q = np.unique(np.r_[sub, allr]); pos = {v: i for i, v in enumerate(q)}
    rix = {k: np.array([pos[v] for v in ix]) for k, ix in R.items()}; sx = np.array([pos[v] for v in sub])
    def res(z):
        X = X_of(z); r = []; dg = G.signed(X[q])
        r.append(w['pen'] * np.maximum(0, -dg[sx] - w['tol_pen'])); r.append(w['penh'] * np.maximum(0, -H.signed(X[sub]) - w['tol_penh']))
        for k, ix in rix.items():
            r.append([(w['thumb'] if k.endswith('T') else w['palmc'] if k == 'palm' else w['con']) * max(0.0, float(dg[ix].min()) - w['tol_con'])])
        if w['across'] > 0:	# the hand ACROSS the part (fingers round it, not along it): knuckle direction (palm -> middle proximal) >= 60 deg off the axis
            kd = X[L['prox_M']] - X[R['palm']].mean(0); kd = kd / np.linalg.norm(kd); r.append([w['across'] * max(0.0, abs(float(kd @ ax_)) - w['across_cos'])])
        r.append(w['cuff'] * (X[L['cuff']].mean(0) - cuff0)); r.append(w['palm'] * (X[R['palm']].mean(0) - palm0)); r.append(w['q'] * (z[6:] - p0[7:]))
        return np.concatenate([np.atleast_1d(np.asarray(a, float)).ravel() for a in r])
    z0 = np.r_[p0[:6], p0[7:]]; lob = np.r_[[-np.inf] * 6, handmodel.QLO]; hib = np.r_[[np.inf] * 6, handmodel.QHI]
    z0 = np.clip(z0, lob + 1e-9, hib - 1e-9)
    xs = np.r_[[0.02] * 3, [0.5] * 3, [0.1, 0.1, 5] * 4 + [0.1, 0.1, 5, 5] + [5, 5]]
    sol = least_squares(res, z0, bounds=(lob, hib), max_nfev=nfev, x_scale=xs)
    z = sol.x; X = X_of(z); p = np.r_[z[:6], p0[6], z[6:]]
    m = measure(S, X, kind, R, L); m0 = measure(S, X0, kind, R, L)
    m.update(cost=float(sol.cost), nfev=int(sol.nfev), secs=round(time.time() - t0), cuff_move_cm=round(float(np.linalg.norm(X[L['cuff']].mean(0) - cuff0)), 2), seed_refit=seedfit,
             palm_move_cm=round(float(np.linalg.norm(X[R['palm']].mean(0) - palm0)), 2), move192_res=S.move_res, sframe=S.r192['sframe'], seed_fit_rms_cm=S.lm_e['fit_rms_cm'])
    os.makedirs(out, exist_ok=True)
    json.dump(dict(cls=g, fitted_on=src, seed_from=seed_from, kind=kind, names=S.names, p=p.tolist(), p_seed=p0.tolist(), Rseed=S.Rseed.tolist(), tseed=S.tseed.tolist(), m=m, seed=m0, w=w),
              open(os.path.join(out, 'fit192_%s.json' % g), 'w'), indent=1)
    np.save(os.path.join(out, 'fit192_%s_X.npy' % g), X)
    view.views(S, X, os.path.join(out, 'fit192_%s.png' % g), '%s: 1.92 Ermac (black), FBX fit (orange); pen %.2f / %.2f, touching %d of 9, wrap %.0f deg' % (g, m['pen_gun'], m['pen_gunhand'], m['touch9'], m['wrap_deg']))
    print(g, 'seed', json.dumps(m0), '\n', g, 'fit ', json.dumps(m), flush=True); return S, X, p, m
def measure(S, X, kind, R, L):
    cont, n9, wd = wrap(S, X, S.exg, kind, R)
    return dict(pen_gun=round(float(S.exg.depth(X).max()), 2), pen_gunhand=round(float(S.exh.depth(X).max()), 2), touch9=int(n9), wrap_deg=round(wd), contact_cm=cont)
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cls'); ap.add_argument('--out', default=_DP.WORK + '/runs/sup192run'); ap.add_argument('--names'); ap.add_argument('--w')
    ap.add_argument('--kind', default='wrap'); ap.add_argument('--nfev', type=int, default=80); ap.add_argument('--gun192'); ap.add_argument('--as', dest='as_'); ap.add_argument('--seed-from', dest='seed_from'); ap.add_argument('--seed-fit', dest='seed_fit'); ap.add_argument('--vgrip', help='cx,cy,cz,ax,ay,az: the measured vertical foregrip (centre, axis up), cm drawn')
    ap.add_argument('--at', help='x,y: the measured support part (cm drawn, F / L) the seed is moved under, in place of the SupportPoint')
    ap.add_argument('--staged', help='poses.json,gunhand.md3: a gun not ported in this branch (s192.register_staged)')
    a = ap.parse_args()
    if a.staged: s192.register_staged(a.cls, *a.staged.split(','))
    fit(a.cls, a.out, a.names.split(',') if a.names else None, json.loads(a.w) if a.w else None, a.kind, a.nfev, a.gun192, a.as_, [float(v) for v in a.vgrip.split(',')] if a.vgrip else None, a.seed_from, a.seed_fit, [float(v) for v in a.at.split(',')] if a.at else None)
