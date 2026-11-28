"""sniper_fit.py: the Sniper (Ruger mesh XM21.md3, MODELDEF.rsr Sniper: Scale -10.485, Offset -0.2816 -44.5467, ZOffset -6.3157, one frame).
Start = the Rifle's solved hold (fits/st2_Rifle.npy) moved by the trigger-face difference (the stock wrist sits behind the trigger as the
rifle's grip does), then reseat_from.stage2b (rigid), then curl_gun (index + M/R/P). Registers the mesh for the batch 3 tools."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'fitter_lib'))
import reseat_from, curl_gun
from rigid3 import *
revlm.GUNS['Sniper'] = dict(it=dict(path=os.path.join(_DP.SRC, 'models/bd/XM21/XM21.md3'), frame=0, scale=[-10.485, 10.485, 10.485], off=[-0.2816, -44.5467, -6.3157]),
                            grip_surf=[9], trig_surf=8, fmax=None, bore_surf=0)
a = np.load(os.path.join(_DP.FITS, 'st2_Rifle.npy')); R0 = a[:9].reshape(3, 3); t0 = a[9:12]
tr, _ = trigger_face('Rifle'); tg, bg = trigger_face('Sniper'); print('trigger rifle', tr.round(2), 'sniper', tg.round(2))
o, R, t, d = reseat_from.stage2b('Sniper', R0, t0 + (tg - tr), w_rot=float(os.environ.get('W_ROT', '0.2'))); print(json.dumps(o, default=float), flush=True)
np.save(os.path.join(_DP.FITS, 'st2_Sniper.npy'), np.r_[R.ravel(), t, d])
curl_gun.run('Sniper', nfev=int(os.environ.get('NFEV', '40')), idx=True)
