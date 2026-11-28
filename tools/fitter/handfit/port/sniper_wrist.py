"""sniper_wrist.py: batch 5, the Sniper (Ruger mesh XM21.md3) held by its STOCK WRIST, not a pistol grip.
Measured (this file's `measure`): the wrist behind the trigger is ~3.3 cm wide and its underside drops from z -1.7 (x -1.8)
to -5.5 (x -5.8); the Rifle's pistol grip runs to z -16. The Rifle's hold re-seated rigidly (batch 4) wraps air below it.
Start: the Rifle's solved hold (fits/st2_Rifle.npy) with the index pad on the Ruger trigger, then the hand is PITCHED about
the gun's lateral axis through the trigger (fingers forward-up round the wrist underside, web over the wrist top) by the
angle that scores best on rigid metrics (scan), then reseat_from.stage2b (rigid) and curl_gun (+: index, M/R/P curls).
Writes fits/st2_Sniper.npy and fits/curl3_Sniper.json (the batch 3/4 formats)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'fitter_lib'))
import reseat_from, curl_gun
from rigid3 import *
from scipy.spatial.transform import Rotation as Rot
revlm.GUNS['Sniper'] = dict(it=dict(path=os.path.join(_DP.SRC, 'models/bd/XM21/XM21.md3'), frame=0, scale=[-10.485, 10.485, 10.485], off=[-0.2816, -44.5467, -6.3157]),
                            grip_surf=[9], trig_surf=8, fmax=None, bore_surf=0)
def score(g, R, t, ex, L, tf, Xf):
    X = Xf @ R.T + t; sub = np.arange(0, len(X), 6)
    o = dict(pen=float(ex.depth(X[sub]).max()), padI=float(np.linalg.norm(X[evaluate.reg(L, 'pad_I')].mean(0) - tf)), palm=float(ex.unsigned(X[evaluate.reg(L, 'palm')]).min()),
             web=float(ex.unsigned(X[evaluate.reg(L, 'web')]).min()), **{'gap_' + f: float(ex.unsigned(X[evaluate.reg(L, 'pad_' + f)]).min()) for f in 'MRPT'})
    o['cost'] = 3 * max(0, o['pen'] - 0.25) + o['palm'] + 0.5 * o['web'] + sum(o['gap_' + f] for f in 'MRP') / 3; return o
if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'curl':	# the curl stage alone, on the saved fits/st2_Sniper.npy
    curl_gun.run('Sniper', nfev=int(os.environ.get('NFEV', '40')), idx=True); sys.exit(0)
if __name__ == '__main__':
    ctx, x, to_g, Xf, delta = revindex.setup(); L = ctx.L
    F, V = scene.merged(revlm.GUNS['Sniper']['it']); ex = exactpen.Exact(V, F)
    a = np.load(os.path.join(_DP.FITS, 'st2_Rifle.npy')); R0 = a[:9].reshape(3, 3); t0 = a[9:12]
    tr, _ = trigger_face('Rifle'); tg, _ = trigger_face('Sniper'); t0 = t0 + (tg - tr)
    rI = evaluate.reg(L, 'pad_I'); best = None
    for ang in [float(v) for v in os.environ.get('ANGS', '0,15,30,45,60,-15').split(',')]:
        Ry = Rot.from_euler('y', ang, degrees=True).as_matrix(); R = Ry @ R0
        p0 = Xf[rI].mean(0) @ R0.T + t0; t = p0 - R @ Xf[rI].mean(0)	# pivot: the index pad stays on the trigger
        o = score('Sniper', R, t, ex, L, tg, Xf); o.update(ang=ang)
        print(json.dumps({k: round(v, 2) for k, v in o.items()}), flush=True)
        if best is None or o['cost'] < best[0]['cost']: best = (o, R, t)
    o, Rb, tb = best; print('start: pitch %.0f deg' % o['ang'], flush=True)
    o2, R, t, d = reseat_from.stage2b('Sniper', Rb, tb, w_rot=float(os.environ.get('W_ROT', '0.05'))); print(json.dumps(o2, default=float), flush=True)
    np.save(os.path.join(_DP.FITS, 'st2_Sniper.npy'), np.r_[R.ravel(), t, d])
    curl_gun.run('Sniper', nfev=int(os.environ.get('NFEV', '40')), idx=True)
