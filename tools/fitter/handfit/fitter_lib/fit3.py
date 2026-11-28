"""Batch 3 fit: the FBX gun hand on a flagged gun, placed where 1.92's hand sits on that gun.
1. m192.T_of(g): rigid transform taking 1.92's pistol hand to 1.92's hand on g (both in 1.92's controller frame O, where
   every one of these guns is drawn at Offset 0 0 / ZOffset -5, so it is the hand's placement RELATIVE TO THE GUN).
2. The approved FBX pistol hand (lane_c r5 frame 0 = fbx_b1_R frame 0, in O: revindex.setup) is moved by the same T.
3. The gun keeps the pistol's r5 aim (orientation); it is translated by d so the FBX hand's cuff (wrist) stays exactly
   where the approved pistol hand's cuff is on the controller (CHOICE: wrist pinned; the hand turns on the wrist as 1.92's does).
4. Finger curls re-solved (squeeze.py's least-squares on the pose parameters): index pad to the trigger face (lower 35%),
   middle/ring/pinky/thumb: no penetration beyond 0.25 cm, pads pulled to within 0.3 cm of the gun, prior = the pistol curl.
   Then the squeeze: index pad 0.6 cm back along the bore (the pistol's rule)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, numpy as np
import os as _os; _LIB = _os.path.dirname(_os.path.abspath(__file__)); _HOME = _os.environ.get('RS_FITTER_HOME', _DP.WORK + '/fitter_home/').rstrip('/')	# fitter_lib: sibling modules here; data under RS_FITTER_HOME
sys.path.insert(0, _DP.CORE + '/hands_tool'); sys.path.insert(0, _LIB); sys.path.insert(0, _LIB)
from scipy.optimize import least_squares
import solve, scene, exactpen, evaluate, handmodel, revindex, revlm, m192
SRC = _HOME + '/lane_b_b3/src'
revlm.GUNS.update({
 # Rifle.md3, MODELDEF.bd.txt Rifle: Scale -1 1 1, Offset 0 0, ZOffset -5; ready frame 3 (rows192). trigger = surface 2 'trigger'; grip in 'Runko' (4)
 'Rifle': dict(it=dict(path=SRC + '/models/bd/Rifle/Rifle.md3', frame=3, scale=[-1.0, 1.0, 1.0], off=[0.0, 0.0, -5.0]), grip_surf=[4], trig_surf=2, fmax=None, bore_surf=4),
 # MP40.md3: ready frame 2 (rows192). trigger = 'spust_low_Cube' (9); grip in 'korpus_low_Cube' (1)
 'MP40': dict(it=dict(path=SRC + '/models/bd/MP40/MP40.md3', frame=2, scale=[-1.0, 1.0, 1.0], off=[0.0, 0.0, -5.0]), grip_surf=[1], trig_surf=9, fmax=None, bore_surf=1),
})
FING = {'I': (6, 9), 'M': (9, 12), 'R': (12, 15), 'P': (15, 18), 'T': (18, 22)}
BONES = {'I': 'INDEX', 'M': 'MIDDLE_F', 'R': 'RING', 'P': 'PINK', 'T': 'THUMB'}
def trigger_face(g):
    c = revlm.GUNS[g]; S, I = revlm.samples(c['it']); T = S[I == c['trig_surf']]
    if 'trig_box' in c: import gunlm; T = T[gunlm.box(T, **c['trig_box'])]
    u0, u1 = T[:, 2].min(), T[:, 2].max(); band = T[np.abs(T[:, 2] - (u0 + 0.35 * (u1 - u0))) < 0.3]
    B = S[I == c['bore_surf']]
    import gunlm; _, ba, _ = gunlm.pca_axis(B); ba = ba if ba[0] > 0 else -ba
    return band[np.argmax(band[:, 0])], ba
def run(g, free='IMRPT', travel=0.6, Tover=None):
    ctx, x, to_g, Xf, delta = revindex.setup()
    R, t, res, P, G = m192.T_of(g) if Tover is None else Tover
    cuff = np.array(ctx.L['cuff']); c0 = Xf[cuff].mean(0)
    d = c0 - (R @ c0 + t)
    F, V = scene.merged(revlm.GUNS[g]['it']); V = V + d; ex = exactpen.Exact(V, F)
    tf, bore = trigger_face(g); tf = tf + d
    dom = ctx.H.dom; L = ctx.L
    fmask = {f: np.array([str(b).startswith(BONES[f]) for b in dom]) for f in 'IMRPT'}
    moved = np.zeros(len(dom), bool)
    for f in free: moved |= fmask[f]
    sl = [i for f in free for i in range(*FING[f])]
    regs = {f: evaluate.reg(L, 'pad_' + f) for f in 'IMRPT'}
    def X_of(q):
        y = x.copy(); y[sl] = q; Xn = to_g(solve.hand_X(ctx, y)[0]) + np.where(moved[:, None], 0, delta)
        return Xn @ R.T + t + d
    lo = handmodel.QLO[np.array(sl) - 6]; hi = handmodel.QHI[np.array(sl) - 6]; q0 = x[sl]
    scl = np.array([1 if (i - 6) % 3 != 2 or i >= 18 else 30 for i in sl], float); scl[np.array(sl) >= 20] = 30
    def solve_to(target, qs):
        def r_(q):
            Xn = X_of(q); r = list(3.0 * (Xn[regs['I']].mean(0) - target)) if 'I' in free else []
            r += list(4.0 * np.maximum(0, ex.depth(Xn[moved][::5]) - 0.25))
            for f in free.replace('I', ''):
                r.append(1.5 * max(0.0, ex.unsigned(Xn[regs[f]]).min() - 0.3))
            r += list(0.05 * (q - q0) / scl); return np.array(r)
        best = None
        for s0 in qs:
            s = least_squares(r_, np.clip(s0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), max_nfev=80)
            if best is None or s.cost < best.cost: best = s
        return best.x, X_of(best.x)
    starts = [q0, q0 + 0.15 * (hi - q0) * (scl == 1), q0 - 0.15 * (q0 - lo) * (scl == 1)]
    qt, Xt = solve_to(tf, starts)
    qs, Xs = solve_to(Xt[regs['I']].mean(0) - bore * travel, [qt])
    X0 = X_of(q0)
    m = lambda X: dict(pad_I_to_trigger=float(np.linalg.norm(X[regs['I']].mean(0) - tf)), pen_max=float(ex.depth(X).max()),
                       pen_p99=float(np.percentile(ex.depth(X), 99)), **{'gap_' + f: float(ex.unsigned(X[regs[f]]).min()) for f in 'MRPT'})
    from scipy.spatial.transform import Rotation as Rot
    out = dict(gun=g, T_rot_deg=float(np.degrees(np.linalg.norm(Rot.from_matrix(R).as_rotvec()))), T_rotvec=Rot.from_matrix(R).as_rotvec().tolist(),
               T_t=t.tolist(), T_fit_res_cm=res.tolist(), shift=d.tolist(), trigger_face=tf.tolist(),
               before_curl=m(X0), trigger=m(Xt), squeeze=m(Xs), squeeze_travel=float(np.linalg.norm(Xs[regs['I']].mean(0) - Xt[regs['I']].mean(0))),
               q0=q0.tolist(), q_trigger=qt.tolist(), q_squeeze=qs.tolist(), free=free)
    return out, Xt, Xs, R
if __name__ == '__main__':
    R_ = {}
    for g in sys.argv[1:]:
        o, Xt, Xs, R = run(g); R_[g] = dict(o, Xt=Xt.tolist(), Xs=Xs.tolist(), R=R.tolist())
        print(json.dumps({k: (v if not isinstance(v, dict) else {a: round(b, 2) for a, b in v.items()}) for k, v in o.items() if k not in ('q0', 'q_trigger', 'q_squeeze', 'T_rotvec')}, default=float), flush=True)
        json.dump(R_[g], open(_HOME + '/lane_b_b3run/fit3_%s.json' % g, 'w'))
