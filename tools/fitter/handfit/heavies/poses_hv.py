"""Save a finished gun's solved hand as DATA: tools/handfit/poses/<Class>.json (owner: a future hand mesh with the same skeleton
re-bakes from it in one run).
  - joint angles per pose: trigger and squeeze = the FBX hand's pose vector (handmodel parameters, revindex.setup's x with the
    index/middle/ring/pinky parameters re-solved). curl json keeps the vertex positions, so the parameters are recovered by a
    forward-kinematics fit to them (residual reported, cm). Support = the shipped FBX support frame (fbx_b1_L frame 1, RQFS B,
    palm-under) and its placement (hook/rot/point); its joint angles are those of that source pose (not re-solved here).
  - wrist placement: R, t (gun frame, stage 2) and the gun shift d; the wrist is pinned to the controller.
  - gun move: MODELDEF place (6 numbers) and the controller-frame R, t (ported_<Class>.json).
  - FBX source: hand_final.fbx (DXR, never shipped), approved pistol hand = lane_c r5 round 4 (fbx_b1_R frame 0).
usage: python3 poses_hv.py <Gun> [...]"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, json, numpy as np
import os as _fl_os; FITTER_LIB = _fl_os.environ.get('RS_FITTER_LIB', _fl_os.path.join(_fl_os.path.dirname(_fl_os.path.abspath(__file__)), '..', 'fitter_lib'))	# the batch 1-4 fitter modules (were <work>/runs/lane_b_b*run/tools)
for p in (_DP.HANDS_TOOL, FITTER_LIB, FITTER_LIB): sys.path.insert(0, p)
from scipy.optimize import least_squares
import solve, revindex, handmodel
HERE = os.path.dirname(os.path.abspath(__file__)); FITS = os.path.join(_DP.FITS); OUT = os.path.join(_DP.POSES)
RUN = os.environ.get('HV_RUN', _DP.WORK + '/runs/lane_b_hvrun')
def run(g):
    ctx, x, to_g, Xf, delta = revindex.setup(); J = json.load(open(RUN + '/curl3_%s.json' % g))
    a = np.load(RUN + '/st2_%s.npy' % g); R = a[:9].reshape(3, 3); t = a[9:12]; d = a[12:15]
    sl = list(range(6, 18)); lo = handmodel.QLO[0:12]; hi = handmodel.QHI[0:12]
    BON = {'I': 'INDEX', 'M': 'MIDDLE_F', 'R': 'RING', 'P': 'PINK'}
    fm = lambda fs: np.array([any(str(b).startswith(BON[f]) for f in fs) for b in ctx.H.dom])
    def X_of(q, mask):		# curl3's frame: the curled fingers' vertices carry no delta
        y = x.copy(); y[sl] = q; Xn = to_g(solve.hand_X(ctx, y)[0]); return (Xn + np.where(mask[:, None], 0, delta)) @ R.T + t + d
    poses = {}
    for name, key in (('trigger', 'Xt'), ('squeeze', 'Xs')):
        T = np.array(J[key]); best = None
        for fs in ('IMRP', 'MRP' if name == 'trigger' else 'IMRP'):
            mask = fm(fs)
            s = least_squares(lambda q: (X_of(q, mask) - T)[::7].ravel(), np.clip(x[sl], lo + 1e-6, hi - 1e-6), bounds=(lo, hi), max_nfev=60)
            res = np.abs(X_of(s.x, mask) - T).max()
            if best is None or res < best[1]: best = (s.x, res, fs)
        y = x.copy(); y[sl] = best[0]; res = best[1]
        # r11: solved_fingers = the fingers drawn from the pose (no per-vertex delta): rebake.py needs it to rebuild the frames
        poses[name] = dict(pose_vector=y.tolist(), solved_params='x[6:18] (index, middle, ring, pinky; 3 each)', solved_fingers=best[2], fk_fit_max_cm=float(res))
    F = json.load(open(os.path.join(FITS, '%s_hv.json' % g))); P = json.load(open(os.path.join(FITS, 'ported_%s.json' % g)))
    S = F['hand']['support']
    if S == 'move':	# r9: no FBX pose fits (MiniGun side handle): Ermac's support pose moved with the gun, read from the ported handtable row
        sys.path.insert(0, os.path.join(HERE, '..', 'port')); import port_hv, port_gun as PG
        tx = open(os.path.join(PG.SRC, 'zscript/rsq/handtable.zs')).read(); row = PG.GUNS[g]['row']
        S = dict(sup_hook=PG.getrow(tx, 'SupportHook', row).tolist(), sup_rot=PG.getrow(tx, 'SupportRot', row).tolist(), sup_point_m=PG.getrow(tx, 'SupportPoint', row).tolist())
        poses['support'] = dict(source='FLAG: Ermac hand2.md3 frame %d moved with the gun (no FBX handle-grip pose exists)' % F['hand'].get('support_frame', 0), hook=S['sup_hook'], rot=S['sup_rot'], point_m=S['sup_point_m'])
    else: poses['support'] = dict(source='fbx_b1_L.md3 frame 1 (RQFS B, FBX open palm-under; lane_c pose, shipped)', hook=S['sup_hook'], rot=S['sup_rot'], point_m=S['sup_point_m'],
                            joint_angles='those of the source pose (not re-solved for this gun)')
    o = dict(cls=g, fbx_source='hand_final.fbx (DXR models/hands, never shipped); approved pistol hand = lane_c results/round4_final.json BrutalPistol x_gun (= fbx_b1_R frame 0)',
             pose_params='handmodel.FbxHand pose vector (revindex.setup x layout: 0-5 wrist/gun, 6-17 I/M/R/P, 18-21 thumb); bounds handmodel.QLO/QHI',
             poses=poses, wrist=dict(R=R.tolist(), t=t.tolist(), shift_cm=d.tolist(), note='hand placed X = X_pistol R^T + t in the pistol gun frame; the wrist stays pinned, the gun moves by shift'),
             gun_move=dict(modeldef_place=P['place'], R=P['R'], t=P['t'], note='controller-frame point -> drawn point after the move'),
             baked=F['hand']['md3_name'], bake_md3='fits/' + F['hand']['md3'], metrics=F.get('metrics', {}).get('curl'))	# r11: bake_md3 (port/-relative) for rebake.py
    os.makedirs(OUT, exist_ok=True); json.dump(o, open(os.path.join(OUT, '%s.json' % g), 'w'), indent=1)
    print(g, {k: v.get('fk_fit_max_cm') for k, v in poses.items()})
if __name__ == '__main__':
    for g in sys.argv[1:]: run(g)
