"""sniper_pistol.py: the Sniper (Ruger, XM21.md3) held PISTOL-STYLE (owner, 2026-10-27): the stock wrist is ignored.
The hand keeps the Rifle's solved placement relative to the controller (fits/st2_Rifle.npy, no rotation, no rigid re-seat
against the stock), translated by the trigger-face difference so the index sits on the Ruger's trigger; the gun keeps the
approved pistol's aim (port_gun.py), so the hand matches the controller and the barrel is on the aim. Then curl_gun.py
(index + M/R/P) closes the fingers onto whatever is under them. sniper_fit.py's start, without its stage-2 re-seat.
Writes fits/st2_Sniper.npy and fits/curl3_Sniper.json (NFEV env: curl iterations, default 40)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'fitter_lib'))
import curl_gun
from rigid3 import *
revlm.GUNS['Sniper'] = dict(it=dict(path=os.path.join(_DP.SRC, 'models/bd/XM21/XM21.md3'), frame=0, scale=[-10.485, 10.485, 10.485], off=[-0.2816, -44.5467, -6.3157]),
                            grip_surf=[9], trig_surf=8, fmax=None, bore_surf=0)
a = np.load(os.path.join(_DP.FITS, 'st2_Rifle.npy')); R0 = a[:9].reshape(3, 3); t0 = a[9:12]
tr, _ = trigger_face('Rifle'); tg, _ = trigger_face('Sniper'); print('trigger rifle', tr.round(2), 'sniper', tg.round(2), 'move', (tg - tr).round(2))
ctx, x, to_g, Xf, delta = revindex.setup(); c0 = Xf[np.array(ctx.L['cuff'])].mean(0)
t = t0 + (tg - tr); X = Xf @ R0.T + t; d = c0 - X[np.array(ctx.L['cuff'])].mean(0)
F, V = scene.merged(revlm.GUNS['Sniper']['it']); ex = exactpen.Exact(V, F); L = ctx.L
print(json.dumps(dict(rigid=dict(pen=float(ex.depth(X).max()), padI=float(np.linalg.norm(X[evaluate.reg(L, 'pad_I')].mean(0) - tg)),
      palm=float(ex.unsigned(X[evaluate.reg(L, 'palm')]).min()), web=float(ex.unsigned(X[evaluate.reg(L, 'web')]).min())), shift=d.round(3).tolist())), flush=True)
np.save(os.path.join(_DP.FITS, 'st2_Sniper.npy'), np.r_[R0.ravel(), t, d])
curl_gun.run('Sniper', nfev=int(os.environ.get('NFEV', '40')), idx=True)
