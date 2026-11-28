"""Round 4 (hands r4): penetration re-fit for a gun whose fit_hv pick is over the 0.5 cm tolerance.
fit_hv's stage 2 and curl test penetration on a SUBSAMPLE of the hand (stage 2: every 4th non-index vertex; curl: every 3rd
vertex of the curled fingers) with a 0.25 cm hinge, so a finger between the samples can sit 0.6-0.9 cm deep (measured on
the r9/r10 picks: Rocket_Launcher 0.88 in the pinky's middle phalanx, NukeLauncher 0.60 palm/wrist, BFG10k 0.58 palm/fingertips).
Same method, same terms, two changes only: every vertex is tested (step 1) and the hinge is `thr` (default 0.10 cm).
  stage(H, g, R0, t0): rigid re-seat from the CURRENT pick's seat (wrist placement), fit_hv/st2_b4 terms
  curl(H, g, idx):     fit_hv.curl with dense penetration (index solved to the trigger when idx)
  wrap (a gun whose mesh has NO trigger: Unmaker, HellishMissileLauncher): stage(..., wrap=True) drops the index-pad-to-trigger
  term (the start is 1.92's own hold on that gun, m192.T_of); curl(..., wrap=True) closes all four fingers I/M/R/P onto the
  handle (pad contact 0.2 cm, as M/R/P in fit_hv) and there is no squeeze (the squeeze frame = the hold)."""
import json, numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
THR = [0.10]
def stage(H, g, R0, t0, w_rot=0.2, nfev=150, wrap=False):
    ctx, x, to_g, Xf, delta = H.revindex.setup(); L = ctx.L
    F, V = H.scene.merged(H.revlm.GUNS[g]['it']); ex = H.exactpen.Exact(V, F); tf, bore = (None, None) if wrap else H.trigger_face(g)
    cuff = np.array(L['cuff']); c0 = Xf[cuff].mean(0)
    rI = H.evaluate.reg(L, 'pad_I'); rP = H.evaluate.reg(L, 'palm'); rW = H.evaluate.reg(L, 'web')
    idx = np.array([str(b).startswith('INDEX') for b in ctx.H.dom]); nonI = np.where(~idx)[0]	# the index is re-curled after (wrap: onto the handle)
    def place(p):
        R = Rot.from_rotvec(p[:3]).as_matrix() @ R0; return R, (Xf - c0) @ R.T + c0 + p[3:] + (R0 @ c0 + t0 - c0)
    def r_(p):
        R, X = place(p); r = list(4.0 * np.maximum(0, ex.depth(X[nonI]) - THR[0]))
        r.append(2.0 * (ex.unsigned(X[rP]).min() - 0.3)); r.append(1.0 * (ex.unsigned(X[rW]).min() - 0.3))
        if not wrap: r += list(0.5 * (X[rI].mean(0) - tf))
        r += list(w_rot * np.degrees(p[:3]) / 5.0); return np.array(r)
    X0 = place(np.zeros(6))[1]; padd = (lambda X: None) if wrap else (lambda X: float(np.linalg.norm(X[rI].mean(0) - tf)))
    pre = dict(pen=float(ex.depth(X0).max()), pen_nonI=float(ex.depth(X0[nonI]).max()), padI=padd(X0),
               palm=float(ex.unsigned(X0[rP]).min()), web=float(ex.unsigned(X0[rW]).min()))
    s = least_squares(r_, np.zeros(6), max_nfev=nfev)
    R, X = place(s.x); t = X[cuff].mean(0) - R @ c0; d = c0 - X[cuff].mean(0)
    o = dict(gun=g, mode='dense', thr=THR[0], start=pre, rot_vs_start_deg=float(np.degrees(np.linalg.norm(s.x[:3]))), move_vs_start_cm=s.x[3:].round(3).tolist(),
             pad_I_to_trigger=padd(X), pen_max=float(ex.depth(X).max()), pen_nonI=float(ex.depth(X[nonI]).max()),
             gap_palm=float(ex.unsigned(X[rP]).min()), gap_web=float(ex.unsigned(X[rW]).min()), nfev=int(s.nfev))
    return o, R, t, d
def curl(H, g, idx=True, nfev=60, wrap=False):
    ctx, x, to_g, Xf, delta = H.revindex.setup(); L = ctx.L; BONES = H.BONES; evaluate = H.evaluate; handmodel = H.handmodel; solve = H.solve
    a = np.load(H.RUN + '/st2_%s.npy' % g); R = a[:9].reshape(3, 3); t = a[9:12]; d = a[12:15]
    F, V = H.scene.merged(H.revlm.GUNS[g]['it']); ex = H.exactpen.Exact(V, F); tf, bore = (None, None) if wrap else H.trigger_face(g)
    if wrap: idx = True
    dom = ctx.H.dom; fm = lambda fs: np.array([any(str(b).startswith(BONES[f]) for f in fs) for b in dom])
    def X_of(qsl, sl, mask):
        y = x.copy(); y[sl] = qsl; Xn = to_g(solve.hand_X(ctx, y)[0]) + np.where(mask[:, None], 0, delta); return Xn @ R.T + t
    sl = list(range(6 if idx else 9, 18)); mask = fm('IMRP' if idx else 'MRP'); sub = np.where(mask)[0]; lo = handmodel.QLO[sl[0] - 6:12]; hi = handmodel.QHI[sl[0] - 6:12]
    rg = {f: evaluate.reg(L, 'pad_' + f) for f in 'IMRPT'}
    def r1(q):
        X = X_of(q, sl, mask); r = list(4.0 * np.maximum(0, ex.depth(X[sub]) - THR[0]))
        for f in ('IMRP' if wrap else 'MRP'): r.append(2.0 * (ex.unsigned(X[rg[f]]).min() - 0.2))
        r += list(0.05 * (q - x[sl]) / np.array([1, 1, 30] * (len(sl) // 3)))
        if idx and not wrap: r += list(3.0 * (X[rg['I']].mean(0) - tf))
        return np.array(r)
    s = least_squares(r1, np.clip(x[sl], lo + 1e-6, hi - 1e-6), bounds=(lo, hi), max_nfev=nfev)
    x2 = x.copy(); x2[sl] = s.x; Xt = X_of(s.x, sl, mask)
    im = fm('I'); maskI = mask | im
    def XI(qi): y = x2.copy(); y[6:9] = qi; Xn = to_g(solve.hand_X(ctx, y)[0]) + np.where(maskI[:, None], 0, delta); return Xn @ R.T + t
    tgt = None if wrap else Xt[rg['I']].mean(0) - 0.6 * bore; loI = handmodel.QLO[0:3]; hiI = handmodel.QHI[0:3]; iI = np.where(im)[0]
    def r2(qi):
        X = XI(qi); r = list(3.0 * (X[rg['I']].mean(0) - tgt)); r += list(4.0 * np.maximum(0, ex.depth(X[iI]) - THR[0])); r += list(0.05 * (qi - x[6:9]) / np.array([1, 1, 30])); return np.array(r)
    if wrap: s2 = type('S', (), dict(x=s.x[0:3]))(); Xs = Xt
    else: s2 = least_squares(r2, np.clip(x2[6:9], loI + 1e-6, hiI - 1e-6), bounds=(loI, hiI), max_nfev=40); Xs = XI(s2.x)
    m = lambda X: dict(pen=float(ex.depth(X).max()), padI_trig=(None if wrap else float(np.linalg.norm(X[rg['I']].mean(0) - tf))), **{'gap_' + f: float(ex.unsigned(X[rg[f]]).min()) for f in 'IMRPT'},
                       gap_palm=float(ex.unsigned(X[evaluate.reg(L, 'palm')]).min()), gap_web=float(ex.unsigned(X[evaluate.reg(L, 'web')]).min()))
    X0 = Xf @ R.T + t
    o = dict(gun=g, mode='dense', thr=THR[0], rigid_only=m(X0), trigger=m(Xt), squeeze=m(Xs), squeeze_travel=float(np.linalg.norm(Xs[rg['I']].mean(0) - Xt[rg['I']].mean(0))), shift=d.tolist(), wrap=wrap,
             q_curl=s.x.tolist(), q_index_squeeze=s2.x.tolist())
    json.dump(dict(o, Xt=(Xt + d).tolist(), Xs=(Xs + d).tolist(), R=R.tolist(), t=t.tolist()), open(H.RUN + '/curl3_%s.json' % g, 'w'))
    return o
