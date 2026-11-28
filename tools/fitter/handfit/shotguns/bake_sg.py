"""Shotguns lane: bake_b3.py with the lane's paths (run dir <work>/runs/lane_b_sgrun, GUNS from fit_sg.py). Usage: bake_sg.py <Gun> <SupportPoint F L U cm, original frame>"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
"""Batch 3 bake (copy of bake_b2.py, parametrised): gun hand frames from curl3_<gun>.json (0 trigger, 1 squeeze, 2 pistol re-bake check); support = RQFS B palm-under at the gun SupportPoint (args, cm), moved with the gun."""
"""Batch 2 bake: BrutalSMG gun hand (the pistol's approved hand, index re-solved: trigger + squeeze) into
models/rsq/fbx/fbx_b2_R.md3 (frames 0 trigger, 1 squeeze), and the support row for the existing palm-under pose
(fbx_b1_L.md3 frame 1, RQFS B) placed under the SMG forend.  Validation: the same bake of the pistol's own trigger
pose must reproduce fbx_b1_R.md3 frame 0 (r5, approved) and give hook 0."""
import sys, json, os, numpy as np
import os as _fl_os; FITTER_LIB = _fl_os.environ.get('RS_FITTER_LIB', _fl_os.path.join(_fl_os.path.dirname(_fl_os.path.abspath(__file__)), '..', 'fitter_lib'))	# the batch 1-4 fitter modules (were <work>/runs/lane_b_b*run/tools)
sys.path.insert(0, _DP.HANDS_TOOL); sys.path.insert(0, FITTER_LIB); sys.path.insert(0, FITTER_LIB)
import solve, bake, hook, scene, hudrender, exactpen, md3write, handmodel, gunmove, revlm, revindex
from scipy.spatial.transform import Rotation as Rot
OUT = (_DP.WORK + '/runs/lane_b_sgrun' + '/bake'); os.makedirs(OUT, exist_ok=True)
B1 = (_DP.SRC + '/models/rsq/fbx/')
ctx, x, to_g, Xf, delta = revindex.setup(); Rg, tg = solve.gun_T(ctx, x)
to_c = lambda X: solve.gmove(ctx, Rg, tg, X)
G = sys.argv[1]; SPX = [float(v) for v in sys.argv[2:5]]; sys.path.insert(0, FITTER_LIB); import fit3; sys.path.insert(0, (_DP.WORK + '/runs/lane_b_sg' + '/tools/handfit/shotguns')); import fit_sg; scene.merged = fit_sg._merged	# the support bake collides with the whole gun (no crop)
J = json.load(open((_DP.WORK + '/runs/lane_b_sgrun' + '/curl3_%s.json') % G))
ent = [dict(name=G + '_trg', side='R', X=to_c(np.array(J['Xt'])), cuff_ref=None),
       dict(name=G + '_sqz', side='R', X=to_c(np.array(J['Xs'])), cuff_ref=None),
       dict(name='PISTOL_chk', side='R', X=to_c(Xf), cuff_ref=None)]
for e in ent: e['cuff_ref'] = e['X'][ctx.cuff]	# as lane_c bake3.py: the frame IS where the hand is drawn (hook 0)
rows, paths, _ = bake.bake(ent, OUT + '/fbx_sg_%s.md3' % G)
for r in rows: print(r)
# validation against the shipped r5/b1 frame 0
s_new = scene.md3_full(paths['R'])[0]['xyz'][2]; s_b1 = scene.md3_full(B1 + 'fbx_b1_R.md3')[0]['xyz'][0]
print('pistol re-bake vs fbx_b1_R frame 0: max %.4f md3 units' % np.abs(s_new - s_b1).max())
# gun move: pistol move check (gunmove vs the solver's gmove) on the SMG grip
Rm, tm = gunmove.move('BrutalPistol'); P0 = np.array([[0, 0, 0], [10, 0, 0], [0, 0, -10.0]])
print('gunmove vs solver gmove (cm):', np.abs((P0 @ Rm.T + tm) - to_c(P0)).max().round(4))
# ---- support: RQFS B (fbx_b1_L frame 1) re-placed under the SMG forend
L = scene.md3_full(B1 + 'fbx_b1_L.md3')[0]
Y = 100 * (hudrender.to_local(L['xyz'][1], dict(hook=[0, 0, 0], rot=[0, 0, 0], **hook.PL)) @ hook.P.T)	# drawn, cm, controller frame
H = handmodel.FbxHand('L'); _, src, _ = md3write.split_uv(H.h.F, H.h.Fc, H.h.uv_corner)
Lm = json.load(open((_DP.CORE + '/landmarks_fbx.json')))['L']
pk = np.where(np.isin(src, Lm['palm']))[0] if isinstance(Lm['palm'], list) else np.where(src == Lm['palm'])[0]
palm = Y[pk].mean(0)
# flamer's own move rotation: the palm-under keeps its relation to the gun's bore (flamer -> SMG)
Rf, tf_ = gunmove.move('Flamethrower2'); Rs = Rm @ Rf.T
dsmg = np.array(J['shift']); it = revlm.GUNS[G]['it']
F_, V_ = scene.merged(it); Vm = (V_ + dsmg) @ Rm.T + (Rm @ np.zeros(3) + tm)		# SMG as drawn after the move
SP0 = np.array(SPX)	# handtable SupportPoint row 5 (m x100), the forend underside BD22Q's support uses
SPm = Rm @ (SP0 + dsmg) + tm
# contact: the forend underside below SPm (min U of the gun near it)
near = Vm[(np.abs(Vm[:, 0] - SPm[0]) < 1.5) & (np.abs(Vm[:, 1] - SPm[1]) < 1.5)]
under = near[np.argmin(near[:, 2])]
Yr = (Y - palm) @ Rs.T
ex = exactpen.Exact(Vm, F_)
best = None; alt = None
for dz in np.arange(-0.0, -4.01, -0.1):	# shotguns lane: to -4 cm (the pump is 4 cm deep)		# lower the palm until the hand is clear of the gun (pen <= 0.5 cm, lane_c TOL)
    Ys = Yr + under + np.array([0, 0, dz]); pen = float(ex.depth(Ys).max())
    if pen <= 0.5: best = (dz, pen, Ys); break
    if alt is None or pen < alt[1]: alt = (dz, pen, Ys)
dz, pen, Ys = best if best else alt	# shotguns lane: no clear drop within 4 cm -> the least-penetrating one, reported (flag)
ts = under + np.array([0, 0, dz]) - Rs @ palm		# Ys = Rs Y + ts
h, r = hook.hook_from_rigid(Rs, ts)
chk = hook.check(L['xyz'][1], h, r, Ys)
gap = float(ex.unsigned(Ys[pk]).min())
print('support: palm at', palm.round(2), '-> under', under.round(2), 'dz', round(dz, 2), 'pen %.2f' % pen, 'palm gap %.2f' % gap,
      'hook', h.round(3), 'rot', r.round(3), 'check %.4f' % chk, 'SupportPoint moved (m)', (SPm / 100).round(3))
json.dump(dict(rows=rows, sup_hook=h.tolist(), sup_rot=r.tolist(), sup_point_m=(SPm / 100).tolist(), sup_pen=pen, sup_gap=gap, sup_dz=dz), open(OUT + '/bake_sg_%s.json' % G, 'w'), indent=1)
