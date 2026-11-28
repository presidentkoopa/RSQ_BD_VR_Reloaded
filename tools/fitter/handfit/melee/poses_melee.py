"""Melee hands lane: a picked farm fit as DATA, tools/handfit/poses/<Class>.json (heavies/poses_hv.py's layout and FK recovery, verbatim
method). Differences: no gun_move (this lane fits and stages; the port lane moves the weapon and writes it), and the support is an FBX L
hand solved here (support_melee.py), recorded with its own pose vector (the L rig = the R rig mirrored, same parameters).
usage: python3 poses_melee.py <Class> <result_dir> [--support <support.json> [--support-res <Chain_saw_top result_dir>]] [--pick-note TEXT]"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, json, argparse, numpy as np
import os as _fl_os; FITTER_LIB = _fl_os.environ.get('RS_FITTER_LIB', _fl_os.path.join(_fl_os.path.dirname(_fl_os.path.abspath(__file__)), '..', 'fitter_lib'))	# the batch 1-4 fitter modules (were <work>/runs/lane_b_b*run/tools)
FH = os.environ.get('MELEE_FITTER_HOME', _DP.WORK + '/fitter_home/'); sys.path.insert(0, FH)
for p in (_DP.CORE + '/hands_tool', FITTER_LIB, FITTER_LIB): sys.path.insert(0, p)
from scipy.optimize import least_squares
import solve, revindex, handmodel
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(_DP.POSES)
BON = {'I': 'INDEX', 'M': 'MIDDLE_F', 'R': 'RING', 'P': 'PINK'}
def fk(res, g, keys=(('trigger', 'Xt'), ('squeeze', 'Xs'))):
    ctx, x, to_g, Xf, delta = revindex.setup(); J = json.load(open(os.path.join(res, 'curl3_%s.json' % g)))
    a = np.load(os.path.join(res, 'st2_%s.npy' % g)); R = a[:9].reshape(3, 3); t = a[9:12]; d = a[12:15]
    sl = list(range(6, 18)); lo = handmodel.QLO[0:12]; hi = handmodel.QHI[0:12]
    fm = lambda fs: np.array([any(str(b).startswith(BON[f]) for f in fs) for b in ctx.H.dom])
    def X_of(q, mask):
        y = x.copy(); y[sl] = q; Xn = to_g(solve.hand_X(ctx, y)[0]); return (Xn + np.where(mask[:, None], 0, delta)) @ R.T + t + d
    poses = {}
    for name, key in keys:
        T = np.array(J[key]); best = None
        for mask in (fm('IMRP'), fm('MRP')):
            s = least_squares(lambda q: (X_of(q, mask) - T)[::7].ravel(), np.clip(x[sl], lo + 1e-6, hi - 1e-6), bounds=(lo, hi), max_nfev=60)
            r = np.abs(X_of(s.x, mask) - T).max()
            if best is None or r < best[1]: best = (s.x, r)
        y = x.copy(); y[sl] = best[0]
        poses[name] = dict(pose_vector=y.tolist(), solved_params='x[6:18] (index, middle, ring, pinky; 3 each)', fk_fit_max_cm=float(best[1]))
    return poses, R, t, d
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('g'); ap.add_argument('res'); ap.add_argument('--support'); ap.add_argument('--support-res'); ap.add_argument('--pick-note', default=''); ap.add_argument('--fit-class', help='class name in the fit files (curl3_<it>.json), e.g. Chain_saw_rear')
    a = ap.parse_args(); g = a.g
    poses, R, t, d = fk(a.res, a.fit_class or g); job = json.load(open(os.path.join(a.res, 'job.json')))
    if a.support:
        S = json.load(open(a.support)); sup = dict(side='L', source=S['how'], md3=S['md3'], rows=S['rows'], metrics=S['metrics'],
                                                   rig='FBX L hand = the R rig mirrored (handmodel.FbxHand L, M diag(1,-1,1)); joint parameters as the R pose vector below')
        if a.support_res:	# Chain_saw: the farm's R fit on the mirrored top handle
            sp, sR, st, sd = fk(a.support_res, 'Chain_saw_top', (('grip', 'Xt'),)); sup['pose_vector'] = sp['grip']['pose_vector']; sup['fk_fit_max_cm'] = sp['grip']['fk_fit_max_cm']
            sup['mirrored_fit'] = dict(R=sR.tolist(), t=st.tolist(), note='R hand placement on the MIRRORED weapon (O frame); mirror L->-L for the L hand')
        else:			# DSweap: the gun hand's own trigger pose, mirrored + slid down the hilt
            sup['pose_vector'] = poses['trigger']['pose_vector']; sup['fk_fit_max_cm'] = poses['trigger']['fk_fit_max_cm']
        poses['support'] = sup
    else: poses['support'] = None
    o = dict(cls=g, fbx_source='hand_final.fbx (DXR models/hands, never shipped); approved pistol hand = lane_c results/round4_final.json BrutalPistol x_gun (= fbx_b1_R frame 0)',
             pose_params='handmodel.FbxHand pose vector (revindex.setup x layout: 0-5 wrist/gun, 6-17 I/M/R/P, 18-21 thumb); bounds handmodel.QLO/QHI',
             poses=poses, wrist=dict(R=R.tolist(), t=t.tolist(), shift_cm=d.tolist(), note='hand placed X = X_pistol R^T + t in the pistol gun frame; the wrist stays pinned, the WEAPON moves by shift'),
             gun_move=None, gun_move_note='not ported: the melee lane fits and stages only; the port lane writes MODELDEF place / R / t and moves the melee points (melee.zs BladeIn/BladeOut/AxeHead/Place)',
             farm=dict(result=os.path.basename(a.res.rstrip('/')), job=job.get('job'), minutes=job.get('minutes'), pick=a.pick_note),
             baked='fbx_hv_%s_R.md3' % (a.fit_class or g), metrics=job.get('metrics', {}).get('curl'))
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, '%s.json' % g); json.dump(o, open(p, 'w'), indent=1)
    print(g, 'wrote', p, {k: (v or {}).get('fk_fit_max_cm') for k, v in poses.items()})
if __name__ == '__main__': main()
