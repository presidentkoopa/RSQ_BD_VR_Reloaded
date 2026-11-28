"""Batch 3, stage 3: finger curls on the stage-2 placement. Middle/ring/pinky pose parameters re-solved (squeeze.py's method)
so their pads close onto the grip (target gap 0.2 cm) with no penetration beyond 0.25 cm; prior = the pistol curl. Index: the
pistol curl (stage 2 already puts its pad on the trigger), then the squeeze = pad 0.6 cm back along the bore (index 3 params).
Output Xt/Xs in the pistol's original gun frame with the gun SHIFTED by d (the frame bake_b2 / revindex use)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, numpy as np
import os as _os; _LIB = _os.path.dirname(_os.path.abspath(__file__)); _HOME = _os.environ.get('RS_FITTER_HOME', _DP.WORK + '/fitter_home/').rstrip('/')	# fitter_lib: sibling modules here; data under RS_FITTER_HOME
sys.path.insert(0, _LIB)
from rigid3 import *
def run(g, nfev=40, idx=False):
    ctx, x, to_g, Xf, delta = revindex.setup(); L = ctx.L
    a = np.load(_HOME + '/lane_b_b3run/st2_%s.npy' % g); R = a[:9].reshape(3, 3); t = a[9:12]; d = a[12:15]
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
    x2 = x.copy(); x2[sl] = s.x
    Xt = X_of(s.x, sl, mask)
    # squeeze: index 3 params, pad 0.6 cm back along the bore, the rest as Xt
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
    o = dict(gun=g, rigid_only=m(X0), trigger=m(Xt), squeeze=m(Xs), squeeze_travel=float(np.linalg.norm(Xs[rg['I']].mean(0) - Xt[rg['I']].mean(0))),
             nonIMRP_moved=float(np.linalg.norm(Xt - X0, axis=1)[~fm('MRP')].max()), q_MRP=s.x.tolist(), q_I_sqz=s2.x.tolist(), shift=d.tolist())
    json.dump(dict(o, Xt=(Xt + d).tolist(), Xs=(Xs + d).tolist(), R=R.tolist(), t=t.tolist()), open(_HOME + '/lane_b_b3run/curl3_%s.json' % g, 'w'))
    print(json.dumps({k: ({a: round(b, 2) for a, b in v.items()} if isinstance(v, dict) else v) for k, v in o.items() if not k.startswith('q_')}, default=float), flush=True)
if __name__ == '__main__':
    for g in sys.argv[1:]: run(g.lstrip('+'), idx=g.startswith('+'))
