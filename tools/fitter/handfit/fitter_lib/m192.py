"""Batch 3: where 1.92's displayed gun hand (Ermac hand.md3, handtable row + trigger frame, lane_c rows192.json) sits on each
gun, in the controller frame of 1.92 (every gun at Offset 0 0 / ZOffset -5, same as 1.99 for these meshes; md5-equal).
Landmarks (lane_c ermaclm): web, palm, cuff (forearm stub), prox_I/M/R/P (knuckles), pad_I. Palm normal = palm - mean(prox) x
knuckle line. T(G) = rigid Kabsch pistol-hand -> G-hand over web, palm, cuff, prox I/M/R/P (the curl-independent skin)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, numpy as np
import os as _os; _LIB = _os.path.dirname(_os.path.abspath(__file__)); _HOME = _os.environ.get('RS_FITTER_HOME', _DP.WORK + '/fitter_home/').rstrip('/')	# fitter_lib: sibling modules here; data under RS_FITTER_HOME
sys.path.insert(0, _DP.CORE + '/hands_tool')
import scene, ermaclm, evaluate
ROWS = json.load(open(_DP.CORE + '/rows192.json'))
KEYS = ['web', 'palm', 'cuff', 'prox_I', 'prox_M', 'prox_R', 'prox_P']
def hand(g, frame=None):
    r = ROWS[g]; _, V = scene.merged(dict(path=scene.HAND192, frame=r['gframe'] if frame is None else frame, hook=r['ghook'], rot=r['grot'], **scene.ERMAC_PL))
    L = ermaclm.get(); return V, L
def lm(V, L):
    o = {k: V[np.array(evaluate.reg(L, k)).ravel()].mean(0) for k in KEYS + ['pad_I', 'pad_T']}
    return o
def kabsch(A, B):
    ca, cb = A.mean(0), B.mean(0); H = (A - ca).T @ (B - cb); U, S, Vt = np.linalg.svd(H)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]); R = Vt.T @ D @ U.T; return R, cb - R @ ca
def T_of(g):
    P = lm(*hand('BrutalPistol')); G = lm(*hand(g))
    A = np.array([P[k] for k in KEYS]); B = np.array([G[k] for k in KEYS]); R, t = kabsch(A, B)
    res = np.linalg.norm(A @ R.T + t - B, axis=1)
    return R, t, res, P, G
if __name__ == '__main__':
    from scipy.spatial.transform import Rotation as Rot
    for g in sys.argv[1:]:
        R, t, res, P, G = T_of(g)
        e = Rot.from_matrix(R).as_euler('ZYX', degrees=True)
        print(g, 'T rot (yaw,pitch,roll about Z,Y,X) %s deg, angle %.1f, t %s; fit residual per landmark %s cm' % (e.round(1), np.degrees(np.linalg.norm(Rot.from_matrix(R).as_rotvec())), t.round(2), res.round(2)))
        print('   web', G['web'].round(2), 'cuff', G['cuff'].round(2), 'pad_I', G['pad_I'].round(2), '| pistol web', P['web'].round(2), 'cuff', P['cuff'].round(2))
