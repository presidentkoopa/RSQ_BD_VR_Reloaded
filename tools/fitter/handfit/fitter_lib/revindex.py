"""BD 2.0 b2: the revolvers keep the pistol's APPROVED gun hand (lane_c r5: round-4 trigger pose = fbx_b1_R frame 0) and
re-solve ONLY the index finger's three pose parameters (squeeze.py's method) so the pad reaches each revolver's trigger.
Gun placement (named choice): the revolver keeps the pistol's r5 orientation (same aim as the approved pistol) and is
translated so its web point (top of the backstrap under the hammer, revlm.py) sits on the pistol's web point.
Frame: the pistol's ORIGINAL gun frame (scene.GUNS, Offset 0 0 -5), where round4_final.json's Xg lives."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, numpy as np
import os as _os; _LIB = _os.path.dirname(_os.path.abspath(__file__)); _HOME = _os.environ.get('RS_FITTER_HOME', _DP.WORK + '/fitter_home/').rstrip('/')	# fitter_lib: sibling modules here; data under RS_FITTER_HOME
sys.path.insert(0, _DP.CORE + '/hands_tool'); sys.path.insert(0, _LIB)
from scipy.optimize import least_squares
import solve, scene, exactpen, evaluate, handmodel, revlm
WEB_U = {'Revolver': -1.25, 'BrutalRevolver': -1.0, 'BrutalSMG': -3.7}	# BrutalSMG: the grip's top, where it meets the receiver (rear profile)	# CHOICE: read from the rear profile (backstrap meets the frame under the hammer)
def web(g, S, I):
    c = revlm.GUNS[g]; G = np.isin(I, c['grip_surf'])
    q = S[(np.abs(S[:, 2] - WEB_U[g]) < 0.13) & (np.abs(S[:, 1]) < 1.0) & G & (S[:, 0] < 0) & (S[:, 0] > -8)]	# behind the trigger, in front of any stock
    return q[np.argmin(q[:, 0])]
def setup():
    R4 = json.load(open(_DP.CORE + '/results/round4_final.json'))['BrutalPistol']
    ctx = solve.Ctx('BrutalPistol', 'R', None, 'gunhand'); x = np.array(R4['x_gun']); Rg, tg = solve.gun_T(ctx, x)
    to_g = lambda X: (X - ctx.c - tg) @ Rg + ctx.c
    Xr = to_g(solve.hand_X(ctx, x)[0]); Xf = np.array(R4['Xg']); delta = Xf - Xr
    return ctx, x, to_g, Xf, delta
def run(g, travel=0.6):
    ctx, x, to_g, Xf, delta = setup()
    P = revlm.pistol(); o, S, I = revlm.measure(g)
    w = web(g, S, I); d = P['backstrap_top'] - w		# translation in the pistol's original frame
    tf = o['trigger_face'] + d
    F, V = scene.merged(revlm.GUNS[g]['it']); V = V + d
    ex = exactpen.Exact(V, F)
    L = ctx.L; regI = evaluate.reg(L, 'pad_I'); dom = ctx.H.dom
    idx = np.isin(dom, ['INDEX_BASE_joint', 'INDEX_MID_joint', 'INDEX_TOP_joint', 'INDEX_UP_TOP_joint'])
    def X_of(qi):
        y = x.copy(); y[6:9] = qi; Xn = to_g(solve.hand_X(ctx, y)[0]); return Xn + np.where(idx[:, None], 0, delta)
    lo = handmodel.QLO[0:3]; hi = handmodel.QHI[0:3]
    def solve_to(target):
        def res(qi):
            Xn = X_of(qi); r = list(3.0 * (Xn[regI].mean(0) - target))
            r += list(4.0 * np.maximum(0, ex.depth(Xn[idx][::7]) - 0.25)); r += list(0.05 * (qi - x[6:9]) / np.array([1, 1, 30])); return np.array(r)
        best = None
        for s0 in (x[6:9], x[6:9] + [0.2, 0.2, 0], x[6:9] + [-0.3, -0.2, 0], x[6:9] + [0.4, 0.1, 0]):
            s = least_squares(res, np.clip(s0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), max_nfev=60)
            if best is None or s.cost < best.cost: best = s
        Xs = X_of(best.x); return best.x, Xs, float(np.linalg.norm(Xs[regI].mean(0) - target))
    qt, Xt, et = solve_to(tf)
    pull = -o['bore_axis'] * travel		# CHOICE (as the pistol): 0.6 cm straight back along the bore
    qs, Xs, es = solve_to(Xt[regI].mean(0) + pull)
    out = dict(gun=g, web=w.tolist(), shift=d.tolist(), trigger_face=tf.tolist(), pistol_trigger_face=P['trigger_face'].tolist(),
               pad_pistol_pose_to_trigger_cm=float(np.linalg.norm(Xf[regI].mean(0) - tf)),
               q_trigger=qt.tolist(), pad_err_trigger_cm=et, q_squeeze=qs.tolist(), pad_err_squeeze_cm=es,
               pen_index_cm=float(ex.depth(Xt[idx]).max()), pen_hand_cm=float(ex.depth(Xt).max()), pen_hand_pistol_pose_cm=float(ex.depth(Xf).max()),
               non_index_moved_cm=float(np.linalg.norm(Xt - Xf, axis=1)[~idx].max()), qlo=lo.tolist(), qhi=hi.tolist())
    return out, Xt, Xs
if __name__ == '__main__':
    R = {}
    for g in sys.argv[1:]:
        o, Xt, Xs = run(g); R[g] = dict(o, Xt=Xt.tolist(), Xs=Xs.tolist())
        print(json.dumps(o, indent=None, default=float), flush=True)
    json.dump(R, open(_HOME + '/lane_b_b2run/revindex_%s.json' % '_'.join(sys.argv[1:]), 'w'))
