"""Batch 4, stage 2 from a GIVEN start (no 1.92 hold): the approved FBX pistol hand placed by (R0, t0) (X = Xf R0^T + t0, gun scene frame),
re-solved rigidly exactly as rigid3.stage2 (no penetration > 0.25 cm, palm and web onto the grip, index pad to the trigger, turn prior
1 per 5 deg vs R0). Moonlight: R0 = the Shotvolver's solved placement (st2_Revolver), t0 moved by the trigger-face difference."""
import sys, json, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fitter_lib'))	# rigid3 (its deps keep the batch 3 snapshot's paths)
from rigid3 import *
def stage2b(g, R0, t0, w_rot=0.2):
    ctx, x, to_g, Xf, delta = revindex.setup(); L = ctx.L
    F, V = scene.merged(revlm.GUNS[g]['it']); ex = exactpen.Exact(V, F); tf, bore = trigger_face(g)
    cuff = np.array(L['cuff']); c0 = Xf[cuff].mean(0)
    rI = evaluate.reg(L, 'pad_I'); rP = evaluate.reg(L, 'palm'); rW = evaluate.reg(L, 'web')
    sub = np.arange(0, len(Xf), 4); idx = np.array([str(b).startswith('INDEX') for b in ctx.H.dom]); nonI = sub[~idx[sub]]
    def place(p):
        R = Rot.from_rotvec(p[:3]).as_matrix() @ R0; return R, (Xf - c0) @ R.T + c0 + p[3:] + (R0 @ c0 + t0 - c0)
    def r_(p):
        R, X = place(p); r = list(4.0 * np.maximum(0, ex.depth(X[nonI]) - 0.25))
        r.append(2.0 * (ex.unsigned(X[rP]).min() - 0.3)); r.append(1.0 * (ex.unsigned(X[rW]).min() - 0.3))
        r += list(0.5 * (X[rI].mean(0) - tf)); r += list(w_rot * np.degrees(p[:3]) / 5.0); return np.array(r)
    X0 = place(np.zeros(6))[1]
    pre = dict(pen=float(ex.depth(X0).max()), padI=float(np.linalg.norm(X0[rI].mean(0) - tf)), palm=float(ex.unsigned(X0[rP]).min()), web=float(ex.unsigned(X0[rW]).min()))
    s = least_squares(r_, np.zeros(6), max_nfev=int(os.environ.get('NFEV2', '150')))
    R, X = place(s.x); t = X[cuff].mean(0) - R @ c0; d = c0 - X[cuff].mean(0)
    o = dict(gun=g, start=pre, rot_vs_start_deg=float(np.degrees(np.linalg.norm(s.x[:3]))), rot_vs_pistol_deg=float(np.degrees(np.linalg.norm(Rot.from_matrix(R).as_rotvec()))),
             move_vs_start_cm=s.x[3:].round(2).tolist(), pad_I_to_trigger=float(np.linalg.norm(X[rI].mean(0) - tf)), pen_max=float(ex.depth(X).max()),
             gap_palm=float(ex.unsigned(X[rP]).min()), gap_web=float(ex.unsigned(X[rW]).min()))
    for f in 'MRPT': o['gap_' + f] = float(ex.unsigned(X[evaluate.reg(L, 'pad_' + f)]).min())
    return o, R, t, d
if __name__ == '__main__':
    g = sys.argv[1]; a = np.load(os.environ.get('RSQ_ST2_FROM', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fits', 'st2_Revolver.npy'))); R0 = a[:9].reshape(3, 3); t0 = a[9:12]
    tr, _ = trigger_face('Revolver'); tg, _ = trigger_face(g); t0 = t0 + (tg - tr); print('trigger shift', (tg - tr).round(2))
    o, R, t, d = stage2b(g, R0, t0); print(json.dumps(o, default=float))
    np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fits', 'st2_%s.npy' % g), np.r_[R.ravel(), t, d])
