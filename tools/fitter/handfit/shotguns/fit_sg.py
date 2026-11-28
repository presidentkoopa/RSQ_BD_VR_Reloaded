"""Shotguns lane (batch 3 method, unchanged): m192 measures 1.92's hold on the gun, rigid3.stage2 re-seats the approved FBX
pistol hand there (wrist pinned, gun shifted by d), then curl3's M/R/P close + index squeeze (curl4.py's body, output dir
parametrised). Usage: fit_sg.py <Gun> [+]   ('+' = also re-solve the index with M/R/P, curl3's idx=True).
Surfaces (read from the md3 surface boxes at the ready frame, tools/surf.py):
  Shot_Gun  Shotgun.md3 ready frame 4 (MODELDEF.bd.txt SHTN A): trigger = surf 3 (F 3.9..4.8, U -6.5..-3.8), grip/bore = 6 'Runko'
  AssaultShotgun AssaultShotgun.md3 frame 4 (1.92 rows192): trigger = surf 5 (F 3.4..4.4, U -6.6..-4.1), grip/bore = 3 'Frame'
  SSG       SSG.md3 frame 1 (rows192): trigger = surf 5 (F 2.7..5.0, U -7.0..-3.3), grip = 1 'Runko' (stock), bore = 0 'Cube' (barrels)"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, numpy as np
import os as _fl_os; FITTER_LIB = _fl_os.environ.get('RS_FITTER_LIB', _fl_os.path.join(_fl_os.path.dirname(_fl_os.path.abspath(__file__)), '..', 'fitter_lib'))	# the batch 1-4 fitter modules (were <work>/runs/lane_b_b*run/tools)
RUN = _DP.WORK + '/runs/lane_b_sgrun'; SRC = _DP.SRC
sys.path.insert(0, FITTER_LIB)
from rigid3 import *
import rigid3
M = SRC + '/models/bd/'
# Memory (2026-10-27): Shotgun.md3's 'Runko' is 18.9k vertices; exactpen on the whole gun was OOM-killed twice (1 GB rss in a
# shared 8 GB cgroup). The gun hand only touches the gun behind F = crop cm (the support hand is not in this fit), so the
# collision mesh keeps only faces with every vertex at F < crop (it['crop']). Drawing and baking still use the whole gun.
_merged = scene.merged
def _merged_crop(it, *a, **k):
    it2 = {kk: v for kk, v in it.items() if kk != 'crop'}; F, V = _merged(it2, *a, **k)
    if 'crop' not in it: return F, V
    keep = (V[np.asarray(F)][:, :, 0] < it['crop']).all(1); return np.asarray(F)[keep], V
scene.merged = _merged_crop
revlm.GUNS.update({
 'Shot_Gun': dict(it=dict(path=M + 'ShotGun/Shotgun.md3', frame=4, crop=25.0, scale=[-1.0, 1.0, 1.0], off=[0.0, 0.0, -5.0]), grip_surf=[6], trig_surf=3, fmax=None, bore_surf=6),
 'AssaultShotgun': dict(it=dict(path=M + 'AssaultShotgun/AssaultShotgun.md3', frame=4, scale=[-1.0, 1.0, 1.0], off=[0.0, 0.0, -5.0]), grip_surf=[3], trig_surf=5, fmax=None, bore_surf=3),
 'SSG': dict(it=dict(path=M + 'SSG/SSG.md3', frame=1, crop=20.0, scale=[-1.0, 1.0, 1.0], off=[0.0, 0.0, -5.0]), grip_surf=[1], trig_surf=5, fmax=None, bore_surf=0),
})
def curl(g, R, t, d, nfev=40, idx=False):
    ctx, x, to_g, Xf, delta = revindex.setup(); L = ctx.L
    F, V = scene.merged(revlm.GUNS[g]['it']); ex = exactpen.Exact(V, F); tf, bore = trigger_face(g)
    dom = ctx.H.dom; fm = lambda fs: np.array([any(str(b).startswith(BONES[f]) for f in fs) for b in dom])
    def X_of(qsl, sl, mask):
        y = x.copy(); y[sl] = qsl; Xn = to_g(solve.hand_X(ctx, y)[0]) + np.where(mask[:, None], 0, delta); return Xn @ R.T + t
    sl = list(range(6 if idx else 9, 18)); mask = fm('IMRP' if idx else 'MRP'); sub = np.where(mask)[0][::3]; lo = handmodel.QLO[sl[0] - 6:12]; hi = handmodel.QHI[sl[0] - 6:12]
    rg = {f: evaluate.reg(L, 'pad_' + f) for f in 'IMRPT'}
    def r1(q):
        X = X_of(q, sl, mask); r = list(4.0 * np.maximum(0, ex.depth(X[sub]) - 0.25))
        for f in 'MRP': r.append(2.0 * (ex.unsigned(X[rg[f]]).min() - 0.2))
        r += list(0.05 * (q - x[sl]) / np.array([1, 1, 30] * (len(sl) // 3)))
        if idx: r += list(3.0 * (X[rg['I']].mean(0) - tf))
        return np.array(r)
    s = least_squares(r1, np.clip(x[sl], lo + 1e-6, hi - 1e-6), bounds=(lo, hi), max_nfev=nfev)
    x2 = x.copy(); x2[sl] = s.x; Xt = X_of(s.x, sl, mask)
    im = fm('I'); maskI = mask | im
    def XI(qi): y = x2.copy(); y[6:9] = qi; Xn = to_g(solve.hand_X(ctx, y)[0]) + np.where(maskI[:, None], 0, delta); return Xn @ R.T + t
    tgt = Xt[rg['I']].mean(0) - 0.6 * bore; loI = handmodel.QLO[0:3]; hiI = handmodel.QHI[0:3]
    def r2(qi):
        X = XI(qi); r = list(3.0 * (X[rg['I']].mean(0) - tgt)); r += list(4.0 * np.maximum(0, ex.depth(X[im][::5]) - 0.25)); r += list(0.05 * (qi - x[6:9]) / np.array([1, 1, 30])); return np.array(r)
    s2 = least_squares(r2, np.clip(x[6:9], loI + 1e-6, hiI - 1e-6), bounds=(loI, hiI), max_nfev=40)
    Xs = XI(s2.x)
    m = lambda X: dict(pen=float(ex.depth(X).max()), padI_trig=float(np.linalg.norm(X[rg['I']].mean(0) - tf)), **{'gap_' + f: float(ex.unsigned(X[rg[f]]).min()) for f in 'MRPT'},
                       gap_palm=float(ex.unsigned(X[evaluate.reg(L, 'palm')]).min()), gap_web=float(ex.unsigned(X[evaluate.reg(L, 'web')]).min()))
    X0 = Xf @ R.T + t
    o = dict(q_trigger=x2.tolist(), q_squeeze_index=s2.x.tolist(), q_pistol=x.tolist(), gun=g, rigid_only=m(X0), trigger=m(Xt), squeeze=m(Xs), squeeze_travel=float(np.linalg.norm(Xs[rg['I']].mean(0) - Xt[rg['I']].mean(0))), shift=d.tolist())
    json.dump(dict(o, Xt=(Xt + d).tolist(), Xs=(Xs + d).tolist(), R=R.tolist(), t=t.tolist()), open(RUN + '/curl3_%s.json' % g, 'w'))
    return o
if __name__ == '__main__':
    g = sys.argv[1]; idx = len(sys.argv) > 2 and sys.argv[2] == '+'
    R, t, res, P, G = m192.T_of(g); print('m192 fit residual per landmark (cm)', res.round(2), flush=True)
    import os
    if idx and os.path.exists(RUN + '/st2_%s.npy' % g):	# index re-solve on the saved stage-2 placement
        a = np.load(RUN + '/st2_%s.npy' % g); R = a[:9].reshape(3, 3); t = a[9:12]; d = a[12:15]
    else:
        o, R, t, d = rigid3.stage2(g); print('stage2', json.dumps(o, default=float), flush=True)
        np.save(RUN + '/st2_%s.npy' % g, np.r_[R.ravel(), t, d])
    o = curl(g, R, t, d, idx=idx)
    print('curl', json.dumps({k: ({a: round(b, 2) for a, b in v.items()} if isinstance(v, dict) else v) for k, v in o.items() if not k.startswith('q_')}, default=float), flush=True)
