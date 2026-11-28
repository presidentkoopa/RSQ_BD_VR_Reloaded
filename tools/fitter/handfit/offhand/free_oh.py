"""free_oh.py <outdir>: the FBX free hand (RQHN A open, RQHN H fist, RQGF fist: Fists weapon + dual DFist + BD22 punches; RQHR A
ring pinch) fitted IN PLACE of Ermac's frames (ohfit.seed): hand.md3 frame 0 (open), frame 1 (the fist: the same frame Ermac drew
for the gun-hand fists and the free fist, knuckles forward), ammo_hand.md3 frame 1 (his one-shell pinch, the grenade ring).
The fist is pulled to the tight FBX fist (handmodel.q_fist, w_q); the pinch then closes index and thumb pads on each other.
Writes <outdir>/free_oh.json (pose vectors, measurements) and free_oh.png (Ermac dark / FBX orange)."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ohfit as O, look, handmodel
from scipy.optimize import least_squares
out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
E0, Fe = O.ermac('hand.md3', 0); E1, _ = O.ermac('hand.md3', 1); E3, _ = O.ermac('ammo_hand.md3', 1)
z_open, m_open = O.seed(E0, starts=('0',))
qf = handmodel.q_fist(); qf[16:18] = O.CAL['1']['p'][7 + 16:7 + 18]
z_fist, m_fist = O.seed(E1, starts=('1',), q_prior=qf, w_q=2.0)
z_p0, m_p0 = O.seed(E3, starts=('1', '0'))
pI, pT = O.reg('pad_I'), O.reg('pad_T')
def res(v):	# pinch: index + thumb free, pads together; everything else stays the seed's
    z = z_p0.copy(); z[6:9] = v[:3]; z[18:22] = v[3:7]; X = O.hand(O.zp(z))
    return np.r_[X[pI].mean(0) - X[pT].mean(0), 0.1 * (v - np.r_[z_p0[6:9], z_p0[18:22]]) / np.r_[1, 1, 30, 1, 1, 30, 30]]
lo = np.r_[handmodel.QLO[0:3], handmodel.QLO[12:16]]; hi = np.r_[handmodel.QHI[0:3], handmodel.QHI[12:16]]
s = least_squares(res, np.clip(np.r_[z_p0[6:9], z_p0[18:22]], lo + 1e-9, hi - 1e-9), bounds=(lo, hi))
z_pinch = z_p0.copy(); z_pinch[6:9] = s.x[:3]; z_pinch[18:22] = s.x[3:7]; Xp = O.hand(O.zp(z_pinch))
gap = float(np.linalg.norm(Xp[pI].mean(0) - Xp[pT].mean(0))); pinch_pt = (Xp[pI].mean(0) + Xp[pT].mean(0)) / 2
C = O.cuff_idx(); cm = lambda z, E: None
J = dict(open=dict(z=z_open.tolist(), seed=m_open, ermac='hand.md3 frame 0'), fist=dict(z=z_fist.tolist(), seed=m_fist, ermac='hand.md3 frame 1', q_prior='handmodel.q_fist (wrist from calib 1), w_q 2'),
         pinch=dict(z=z_pinch.tolist(), seed=m_p0, ermac='ammo_hand.md3 frame 1', pad_gap_cm=gap, pinch_point_cm=pinch_pt.tolist()), logscale=O.LOGS)
# knuckles forward: the fist's knuckle line (proximal I..P) and the direction palm -> middle knuckle, drawn frame
Xf = O.hand(O.zp(z_fist)); kd = Xf[O.LM['prox_M']] - Xf[O.reg('palm')].mean(0); J['fist']['palm_to_knuckle_dir'] = (kd / np.linalg.norm(kd)).round(3).tolist()
json.dump(J, open(os.path.join(out, 'free_oh.json'), 'w'), indent=1)
print(json.dumps({k: (v.get('seed'), v.get('pad_gap_cm')) for k, v in J.items() if isinstance(v, dict)}), J['fist']['palm_to_knuckle_dir'])
rows = []
for lab, z, E in (('open (hand.md3 0)', z_open, E0), ('fist (hand.md3 1)', z_fist, E1), ('pinch (ammo_hand.md3 1)', z_pinch, E3)):
    rows.append((lab + ': Ermac', [look.m(E, Fe, (60, 45, 40))])); rows.append((lab + ': FBX over Ermac (same view)', [dict(look.m(E, Fe, (60, 45, 40)), centre=True), dict(look.m(O.hand(O.zp(z)), O.H.F, (235, 150, 90)), centre=False)]))
print(look.views(rows, os.path.join(out, 'free_oh.png'), 'FBX free hand in place of Ermac frames (drawn frame; right hand = both controllers)'))
