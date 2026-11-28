"""fit_nade.py: the FBX right hand holding BD22's hand grenade (nade.md3, VR blocks MODELDEF.rsq RQNP), solved from the approved
pistol hand with EVERY finger, the thumb and the finger spread free (the melee lane's method curls I/M/R/P on a pistol fist and
leaves the thumb as it is: on a 7.4 cm body it ends at pen 1.83 cm).
usage: python3 fit_nade.py <out_dir> [--nfev N] [--seeds K] [--x0 nade_fit.json] [--thr 0.25] [--move CM W] [--thumb S GAP]
  shipped fit (r4, about 1 min a run on a 2-core box): r1 = all seeds --nfev 150; r2 = --x0 r1 --thr 0 --nfev 300;
  r4 = --x0 r2 --thr 0 --nfev 300 --thumb 4.0 0.15. Then port_nade.py r4/nade_fit.json.
Frames: everything is the DRAWN controller frame (cm, F forward / L left / U up; gunview.to_fl), the frame fbx_b1_R.md3 frame 0 is
baked in (hook 0). The grenade starts at its shipped VR placement (MODELDEF.rsq RQNP: Scale -0.92 0.92 0.92, Offset -4.01 -2.04 -1.45,
ZOffset -5: QZD's MODELDEF parser lets ZOffset overwrite Offset's z (models.cpp), so the drawn z offset is -5, not -6.45).
Unknowns (30): hand rotvec + translation (the r5 parameter layout x[0:6]), the 18 FBX pose parameters x[6:24] (I/M/R/P curls +
spread, thumb curls + spread + twist, wrist flex / deviation), the grenade move: rotvec + translation about its body centre (6).
The drawn hand is exactly what rebake.py rebuilds from a heavies-form pose JSON with wrist R = I, t = 0, shift 0 and solved_fingers
IMRPT: hand_X(pv) + Rg delta on the palm / forearm vertices (the approved pistol hand's per-vertex correction, kept as fit_hv does).
Terms (cm / deg; hinges are 0 inside the band):
  wrist pinned: the cuff ring on the approved pistol hand's cuff (the controller), every cuff vertex (w 4)
  penetration into the grenade (body, spoon, ring, fuse) <= thr on every 2nd vertex (distance grid; reported exactly on every vertex)
  palm on the body (gap 0.3), I/M/R/P pads on the body (<= 0.3), each finger chain palm->base->mid->top->tip wraps >= WRAP deg round
  the body axis, index above the pinky along the axis (>= 4 cm), thumb pad on the spoon (<= --thumb[1]) in its upper part (the lever,
  along the axis >= --thumb[0] from the body centre), fingers below the ring (pads under the ring's lowest point - 0.5)
  priors: pose (0.3, as sup_r4), grenade turn beyond 35 deg and grenade move beyond --move cm (soft, weight), hand turn vs the pistol beyond 30 deg
Outputs nade_fit.json (x, pv, grenade R/t, metrics, X drawn vertices) in out_dir."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, json, time, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET
TOOL = os.environ.get('RSQ_HANDS_TOOL', _DP.HANDS_TOOL); LANE = os.path.dirname(TOOL)
sys.path.insert(0, os.path.join(HERE, '..', 'port')); sys.path.insert(0, TOOL)
import rebake, solve, scene, gunfield, exactpen, evaluate, handmodel
from fit3 import BONES
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
SRC = os.environ.get('RSQ_SRC', os.path.join(REPO, 'src'))
NADE = dict(path='models/bd/Grenade/nade.md3', frame=2, scale=[-0.92, 0.92, 0.92], off=[-4.01, -2.04, -5.0])	# MODELDEF.rsq RQNP C (ready)
SURF = dict(body=0, ring=2, spoon=3, fuse=4)
WRAP = 150.0; THUMB_S = [2.5, 0.4]; THR = [0.25]; MOVE = [3.0, 0.3]	# grenade move hinge (cm) and weight
FT = dict(I='INDEX', M='MIDDLE_F', R='RING', P='PINK')
def nade_mesh():
    it = dict(NADE, path=os.path.join(SRC, NADE['path'])); parts = list(scene.item_verts(it)); T = []; V = []; S = []; n = 0
    for k, (t, v) in enumerate(parts): T.append(np.asarray(t) + n); V.append(v); S.append(np.full(len(t), k)); n += len(v)
    return np.concatenate(T), np.concatenate(V), np.concatenate(S)
class Model:
    def __init__(s):
        (s.ctx, s.x0, s.to_g, s.Xf, s.delta), _ = rebake.setup(); Rg, tg = solve.gun_T(s.ctx, s.x0); s.Rg = Rg
        s.to_c = lambda X: solve.gmove(s.ctx, Rg, tg, X)
        dom = s.ctx.H.dom; m = np.array([any(str(b).startswith(BONES[f]) for f in 'IMRPT') for b in dom])
        s.dc = np.where(m[:, None], 0.0, s.delta @ Rg.T)		# the drawn correction on the unsolved (palm / forearm) vertices
        s.Xp = s.to_c(s.Xf); s.cuff = s.ctx.cuff; s.cuff_ref = s.Xp[s.cuff]
        s.L = s.ctx.L; s.reg = {k: evaluate.reg(s.L, k) for k in ('palm', 'web', 'pad_I', 'pad_M', 'pad_R', 'pad_P', 'pad_T')}
        F, V, Sid = nade_mesh(); s.Fn, s.Vn, s.Sid = F, V, Sid
        body = np.unique(F[Sid == SURF['body']]); Pb = V[body]; s.c = Pb.mean(0)
        U, sv, Vt = np.linalg.svd(Pb - s.c); a = Vt[0]; s.a = a if a[2] > 0 else -a	# body axis, toward the spoon / fuse (up)
        q = Pb - s.c; rr = q - np.outer(q @ s.a, s.a); s.r = float(np.median(np.linalg.norm(rr, axis=1)))
        ring = np.unique(F[Sid == SURF['ring']]); s.ring_lo = float(((V[ring] - s.c) @ s.a).min())
        s.lo = V.min(0) - 4; s.hi = V.max(0) + 4
        s.f_all = gunfield.Field(V, F, s.lo, s.hi, h=0.3, band=1.0)
        sp = F[Sid == SURF['spoon']]; s.f_spoon = gunfield.Field(V, sp, s.lo, s.hi, h=0.3, band=1.0)
        s.ex = exactpen.Exact(V, F); s.ex_spoon = exactpen.Exact(V, sp)
        s.sub = np.arange(0, len(s.Xp), 2); s.pv0 = np.array(s.x0[:24], float)
        s.R_p = Rot.from_rotvec(s.x0[:3]).as_matrix()
    def hand(s, pv):
        X, J = solve.hand_X(s.ctx, pv); return X + s.dc, J
    def gmove(s, y):	# grenade: rotvec y[:3] about the body centre, then y[3:6]
        R = Rot.from_rotvec(y[:3]).as_matrix(); return R, s.c + y[3:6] - R @ s.c
    def local(s, y, P):	# drawn points -> the grenade's shipped frame
        R, t = s.gmove(y); return (np.atleast_2d(P) - t) @ R
    def res(s, z, full=False):
        pv = z[:24]; y = z[24:30]; X, J = s.hand(pv); r = []; m = {}
        Xl = s.local(y, X); Jl = {k: s.local(y, v)[0] for k, v in J.items()}
        r += list(4.0 * (X[s.cuff] - s.cuff_ref).ravel()); m['cuff_max'] = float(np.linalg.norm(X[s.cuff] - s.cuff_ref, axis=1).max())
        d = s.ex.depth(Xl) if full else np.maximum(0, -s.f_all(Xl[s.sub])); r += list(6.0 * np.maximum(0, d - THR[0])); m['pen'] = float(d.max())
        r += list(0.3 * (pv[6:24] - s.pv0[6:24]) / np.array([1, 1, 30] * 4 + [1, 1, 30, 30] + [30, 30]) * 0.3)
        ug = (lambda k: float(s.ex.unsigned(Xl[s.reg[k]]).min())) if full else (lambda k: float(np.abs(s.f_all(Xl[s.reg[k]])).min()))
        m['palm_gap'] = ug('palm'); r.append(2.0 * max(0, m['palm_gap'] - 0.3))
        pc = Xl[s.reg['palm']].mean(0)
        def ang(P):
            q = np.atleast_2d(P) - s.c; rr = q - np.outer(q @ s.a, s.a); e1 = np.cross(s.a, [0, 1.0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(s.a, e1)
            return np.degrees(np.arctan2(rr @ e2, rr @ e1))
        for f in 'IMRP':
            gp = ug('pad_' + f); m['gap_' + f] = gp; r.append(1.5 * max(0, gp - 0.3))
            pts = [pc] + [Jl[FT[f] + k] for k in ('_BASE_joint', '_MID_joint', '_TOP_joint', '_UP_TOP_joint')]
            an = np.unwrap(np.radians(ang(np.array(pts)))); w = float(abs(np.degrees(an[-1] - an[0]))); m['wrap_' + f] = w; r.append(0.05 * max(0, WRAP - w))
            sp_ = float((Xl[s.reg['pad_' + f]].mean(0) - s.c) @ s.a); m['s_' + f] = sp_; r.append(0.5 * max(0, sp_ - (s.ring_lo - 0.5)))
        m['I_to_P'] = m['s_I'] - m['s_P']; r.append(0.5 * max(0, 4.0 - m['I_to_P']))
        pT = Xl[s.reg['pad_T']]
        m['gap_T_spoon'] = float(s.ex_spoon.unsigned(pT).min()) if full else float(np.abs(s.f_spoon(pT)).min()); r.append(2.0 * max(0, m['gap_T_spoon'] - THUMB_S[1]))
        m['s_T'] = float((pT.mean(0) - s.c) @ s.a); r.append(0.5 * max(0, THUMB_S[0] - m['s_T']))
        Rg, tg = s.gmove(y); m['nade_turn_deg'] = float(np.degrees(np.linalg.norm(y[:3]))); m['nade_move_cm'] = float(np.linalg.norm(y[3:6]))
        r.append(0.05 * max(0, m['nade_turn_deg'] - 35)); r.append(MOVE[1] * max(0, m['nade_move_cm'] - MOVE[0]))
        Rh = Rot.from_rotvec(pv[:3]).as_matrix(); m['hand_turn_deg'] = float(np.degrees(Rot.from_matrix(Rh @ s.R_p.T).magnitude())); r.append(0.05 * max(0, m['hand_turn_deg'] - 30))
        return (np.array(r), m) if full else np.array(r)
def seeds(M):
    out = []; q = M.pv0.copy()
    for k, fr in enumerate((0.5, 0.75)):
        z = np.r_[q, np.zeros(6)]
        z[6:18] = np.clip(np.r_[[fr, fr, 0] * 4] * 1.0, handmodel.QLO[:12], handmodel.QHI[:12]); z[6 + 2::3][:4] = M.pv0[8:18:3]
        out.append(z)
    # the body centred where the pistol's grip sits, set back by (r - half the grip depth) away from the palm (gun_landmarks BrutalPistol, drawn)
    G = M.ctx.G; gc = M.to_c(np.array([G['grip_c']]))[0]; ps = M.Rg @ np.array(G['palm_side']); ga = M.Rg @ np.array(G['grip_axis'])
    tgt = gc - ps * (M.r - 0.5 * float(G['grip_d'])) + ga * 3.0
    Ra = rebake_rot(M.a, ga); y = np.r_[Rot.from_matrix(Ra).as_rotvec(), tgt - M.c]
    for fr in (0.5, 0.75):
        z = np.r_[q, y]; z[6:18] = np.clip(np.r_[[fr, fr, 0] * 4], handmodel.QLO[:12], handmodel.QHI[:12]); out.append(z)
    return out
def rebake_rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-12: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]]); return np.eye(3) + K + K @ K * (1 / (1 + c))
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--nfev', type=int, default=120); ap.add_argument('--seeds', type=int, default=99)
    ap.add_argument('--x0'); ap.add_argument('--thr', type=float, default=0.25); ap.add_argument('--only', type=int, default=-1); ap.add_argument('--move', type=float, nargs=2, default=[3.0, 0.3]); ap.add_argument('--thumb', type=float, nargs=2, default=[2.5, 0.4])
    a = ap.parse_args(); THR[0] = a.thr; MOVE[:] = a.move; THUMB_S[:] = a.thumb; os.makedirs(a.out, exist_ok=True); t0 = time.time(); M = Model()
    print('nade axis', M.a.round(3).tolist(), 'centre', M.c.round(2).tolist(), 'r %.2f' % M.r, 'ring lowest s %.2f' % M.ring_lo, 'setup %.1f s' % (time.time() - t0), flush=True)
    lo = np.r_[[-np.inf] * 6, handmodel.QLO, [-np.inf] * 6]; hi = np.r_[[np.inf] * 6, handmodel.QHI, [np.inf] * 6]
    S0 = [np.array(json.load(open(a.x0))['z'])] if a.x0 else seeds(M)[:a.seeds]
    if a.only >= 0: S0 = [S0[a.only]]
    xs = np.r_[[0.05] * 3, [1] * 3, [0.1, 0.1, 5] * 4 + [0.1, 0.1, 5, 5] + [5, 5], [0.05] * 3, [1] * 3]; best = None; log = []
    for k, z0 in enumerate(S0):
        z0 = z0.copy(); z0[6:24] = np.clip(z0[6:24], handmodel.QLO + 1e-6, handmodel.QHI - 1e-6); t1 = time.time()
        s = least_squares(M.res, z0, bounds=(lo, hi), max_nfev=a.nfev, x_scale=xs)
        _, m = M.res(s.x, full=True); c = float(s.cost); log.append(dict(seed=k, cost=c, nfev=int(s.nfev), minutes=round((time.time() - t1) / 60, 2), **m))
        print('seed', k, 'cost %.3f' % c, 'nfev', s.nfev, '%.1f min' % ((time.time() - t1) / 60), json.dumps({kk: round(v, 2) for kk, v in m.items()}), flush=True)
        if best is None or c < best[0]: best = (c, s.x, m, k)
    c, z, m, k = best; X, J = M.hand(z[:24]); Rn, tn = M.gmove(z[24:30])
    o = dict(cost=c, best_seed=k, metrics=m, z=z.tolist(), pv=np.r_[z[:24], M.x0[24:30]].tolist(), nade=dict(R=Rn.tolist(), t=tn.tolist(), centre=M.c.tolist(), axis=M.a.tolist(), r=M.r),
             seeds=log, thr=THR[0], refined_from=a.x0, minutes=round((time.time() - t0) / 60, 2), X=X.round(5).tolist())
    json.dump(o, open(os.path.join(a.out, 'nade_fit.json'), 'w'), indent=1, default=float)
    print('BEST seed', k, 'cost %.3f' % c, json.dumps({kk: round(v, 3) for kk, v in m.items()}), 'minutes', o['minutes'], flush=True)
if __name__ == '__main__': main()
