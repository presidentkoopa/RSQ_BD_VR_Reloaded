"""Batch 3, stage 1 (cheap): metrics of the FBX pistol hand placed by 1.92's relative hand transform (fit3 steps 1-3), no curl change."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, time, numpy as np
import os as _os; _LIB = _os.path.dirname(_os.path.abspath(__file__)); _HOME = _os.environ.get('RS_FITTER_HOME', _DP.WORK + '/fitter_home/').rstrip('/')	# fitter_lib: sibling modules here; data under RS_FITTER_HOME
sys.path.insert(0, _LIB)
import fit3
from fit3 import *
def stage1(g):
    t0 = time.time()
    ctx, x, to_g, Xf, delta = revindex.setup(); R, t, res, P, G = m192.T_of(g)
    cuff = np.array(ctx.L['cuff']); c0 = Xf[cuff].mean(0); d = c0 - (R @ c0 + t)
    F, V = scene.merged(revlm.GUNS[g]['it']); V = V + d; ex = exactpen.Exact(V, F)
    tf, bore = trigger_face(g); tf = tf + d
    X = Xf @ R.T + t + d; L = ctx.L
    dep = ex.depth(X); dom = ctx.H.dom
    o = dict(gun=g, rot=float(np.degrees(np.linalg.norm(__import__('scipy.spatial.transform', fromlist=['Rotation']).Rotation.from_matrix(R).as_rotvec()))),
             shift=d.round(2).tolist(), pad_I_to_trigger=float(np.linalg.norm(X[evaluate.reg(L, 'pad_I')].mean(0) - tf)),
             pen_max=float(dep.max()), secs=time.time() - t0)
    for f in 'IMRPT':
        m = np.array([str(b).startswith(BONES[f]) for b in dom]); o['pen_' + f] = float(dep[m].max()); o['gap_' + f] = float(ex.unsigned(X[evaluate.reg(L, 'pad_' + f)]).min())
    m = np.array([str(b) in ('HANDPALM_joint', 'Root_joint') for b in dom]); o['pen_palm'] = float(dep[m].max())
    o['gap_palm'] = float(ex.unsigned(X[evaluate.reg(L, 'palm')]).min())
    return o
if __name__ == '__main__':
    for g in sys.argv[1:]: print(json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in stage1(g).items()}), flush=True)

# ---- stage 2: the hand's placement ON THE GUN re-solved rigidly (curl = the approved pistol curl), starting from 1.92's
# transported placement; terms: no penetration (>0.25 cm), palm and web onto the grip (0.3 cm), index pad to the trigger,
# rotation kept near 1.92's relative rotation (prior 1 per 5 deg). The gun then moves (shift d) so the cuff stays pinned.
from scipy.spatial.transform import Rotation as Rot
def stage2(g, w_rot=0.2, pin_cuff=True):
    ctx, x, to_g, Xf, delta = revindex.setup(); R0, t0, res, P, G = m192.T_of(g); L = ctx.L
    F, V = scene.merged(revlm.GUNS[g]['it']); ex = exactpen.Exact(V, F); tf, bore = trigger_face(g)
    cuff = np.array(L['cuff']); c0 = Xf[cuff].mean(0)
    rI = evaluate.reg(L, 'pad_I'); rP = evaluate.reg(L, 'palm'); rW = evaluate.reg(L, 'web')
    sub = np.arange(0, len(Xf), 4); idx = np.array([str(b).startswith('INDEX') for b in ctx.H.dom])
    nonI = sub[~idx[sub]]
    def place(p):
        R = Rot.from_rotvec(p[:3]).as_matrix() @ R0; return R, (Xf - c0) @ R.T + c0 + p[3:] + (R0 @ c0 + t0 - c0)
    def r_(p):
        R, X = place(p); r = list(4.0 * np.maximum(0, ex.depth(X[nonI]) - 0.25))
        r.append(2.0 * (ex.unsigned(X[rP]).min() - 0.3)); r.append(1.0 * (ex.unsigned(X[rW]).min() - 0.3))
        r += list(0.5 * (X[rI].mean(0) - tf))
        r += list(w_rot * np.degrees(p[:3]) / 5.0); return np.array(r)
    s = least_squares(r_, np.zeros(6), max_nfev=150)
    R, X = place(s.x); t = X[cuff].mean(0) - R @ c0	# X = Xf R^T + t
    d = c0 - X[cuff].mean(0)
    o = dict(gun=g, rot_vs_192_deg=float(np.degrees(np.linalg.norm(s.x[:3]))), rot_vs_pistol_deg=float(np.degrees(np.linalg.norm(Rot.from_matrix(R).as_rotvec()))),
             euler_ZYX_vs_pistol=Rot.from_matrix(R).as_euler('ZYX', degrees=True).round(1).tolist(), move_vs_192_cm=s.x[3:].round(2).tolist(),
             pad_I_to_trigger=float(np.linalg.norm(X[rI].mean(0) - tf)), pen_max=float(ex.depth(X).max()), pen_nonI=float(ex.depth(X[~idx]).max()),
             gap_palm=float(ex.unsigned(X[rP]).min()), gap_web=float(ex.unsigned(X[rW]).min()))
    for f in 'MRPT': o['gap_' + f] = float(ex.unsigned(X[evaluate.reg(L, 'pad_' + f)]).min())
    return o, R, t, d
if __name__ == '__main__' and False: pass
