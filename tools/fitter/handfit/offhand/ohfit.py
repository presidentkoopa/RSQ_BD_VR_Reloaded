"""ohfit.py (off-hand FBX lane, 2026-10-28): the FBX hand fitted IN PLACE of an Ermac free-hand frame (hand.md3 / ammo_hand.md3,
drawn by RSQ_Hands / RSQ_GunSide: Scale -1 1 1, Offset 0 -24 -10, no hook), and then round the object that frame holds.

Frame: the DRAWN controller frame, cm F / L / U (scene.merged, hudrender.to_local = models.cpp RenderHUDModel). In that frame
Ermac's free-hand mesh is a RIGHT hand on both controllers: the engine mirrors the OFF controller (hw_vrmodes GetWeaponTransform;
lane_c calib.py), so one right-hand frame draws the right fist on the main controller and the left fist on the off controller,
exactly as Ermac's single hand.md3 frame 1 did. So every frame here is the FBX RIGHT rig (handmodel.FbxHand('R'),
calib.place: rotvec, t, log-scale fixed at the controller calibration, 18 pose parameters), baked as side R in place (hook 0).
(r12's offhand_r12.py mirrored the right hand to L and baked side L: on the off controller the engine mirrored it back, so the
off hand drew as a RIGHT hand: rig frame lane_b_out/offhand_gate/shots/hand0_left.png vs Ermac's hand0_left_r11.png.)

  seed(E)           the FBX hand fitted to an Ermac frame E (drawn cm): landmark regions (lane_c landmarks_ermac.json, the same
                    1021-vertex topology for hand / hand2 / ammo_hand) <-> FBX landmark vertices, + a trimmed two-way chamfer
                    (support192 s192.seed_refit's method), started from lane_c calib '0' (open) and '1' (fist), q prior optional
  grip(...)         the hold: from the seed, the hand closes round the object (V, F drawn cm): penetration into it <= tol, palm and
                    pads I M R P T onto its surface, cuff (wrist) near the seed's, joints near the seed's; optional object move
                    (translation only, soft) -- returned so every row that reads the object's position moves with it
  measure(...)      exact pen (exactpen), contact gaps, fingers touching, cuff move, visible share of the object from the eye
Needs RSQ_HANDS_TOOL (lane_c hands_tool, default <depot>/tools/handfit/core/hands_tool) and the FBX (handmodel.FBX / RSQ_FBX)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, json, numpy as np
TOOL = os.environ.get('RSQ_HANDS_TOOL', _DP.HANDS_TOOL); LANE = os.path.dirname(TOOL.rstrip('/'))
sys.path.insert(0, TOOL)
import handmodel
if os.environ.get('RSQ_FBX'): handmodel.FBX = os.environ['RSQ_FBX']
import calib, scene, exactpen, gunfield
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET
SRC = os.environ.get('RSQ_SRC', os.path.join(REPO, 'src'))
def jl(p): return json.load(open(p))
CAL = jl(os.path.join(LANE, 'calib.json'))
H = handmodel.FbxHand('R'); LOGS = CAL['1']['p'][6]
LM = jl(os.path.join(LANE, 'landmarks_fbx.json'))['R']; LM['_reg'] = jl(os.path.join(LANE, 'regions.json'))['fbx']
EREG = jl(os.path.join(LANE, 'landmarks_ermac.json'))['_reg']
LMK = ['web', 'palm', 'pad_I', 'prox_I', 'pad_M', 'prox_M', 'pad_R', 'prox_R', 'pad_P', 'prox_P', 'pad_T', 'prox_T']
def reg(k): return np.array(LM['_reg'][k] if k in LM['_reg'] else [LM[k]])
CUFF = np.array(LM['cuff']) if isinstance(LM['cuff'], list) else None
def ermac(md3, frame):
    """Ermac's frame as RSQ_Hands draws it (drawn cm); md3 = 'hand.md3' / 'ammo_hand.md3' / 'hand2.md3' (src/models/rsq)"""
    F, V = scene.merged(dict(path=os.path.join(SRC, 'models', 'rsq', md3), frame=frame, **scene.ERMAC_PL)); return V, F
def hand(p): return calib.place(H, p)
def zp(z): return np.r_[z[:6], LOGS, z[6:]]
LO = np.r_[[-np.inf] * 6, handmodel.QLO]; HI = np.r_[[np.inf] * 6, handmodel.QHI]
XS = np.r_[[0.02] * 3, [0.5] * 3, [0.1, 0.1, 5] * 4 + [0.1, 0.1, 5, 5] + [5, 5]]
def cuff_idx():
    c = LM['cuff']; return np.array(c if isinstance(c, list) else jl(os.path.join(LANE, 'landmarks_fbx.json'))['R']['cuff'])
def seed(E, starts=('0', '1'), q_prior=None, w_q=0.0, nfev=120, w_ch=0.3):
    """FBX right hand onto Ermac's frame E (drawn cm). q_prior (18) with weight w_q pulls the pose (e.g. q_fist for a tight fist)."""
    T = np.array([E[EREG[k]].mean(0) for k in LMK]); Lv = np.array([LM[k] for k in LMK]); tE = cKDTree(E); subE = E[::2]
    V0 = hand(np.array(CAL['1']['p'])); nolf = np.arange(len(V0))[::3]
    def res(z):
        X = hand(zp(z)); r = [(X[Lv] - T).ravel()]
        d1, _ = tE.query(X[nolf]); d1 = np.minimum(d1, np.quantile(d1, 0.9)); r.append(w_ch * d1)
        d2, _ = cKDTree(X).query(subE); d2 = np.minimum(d2, np.quantile(d2, 0.9)); r.append(w_ch * d2)
        if q_prior is not None and w_q > 0: r.append(w_q * (z[6:] - q_prior) / np.r_[[1, 1, 30] * 4 + [1, 1, 30, 30] + [30, 30]])
        return np.concatenate(r)
    best = None
    for k in starts:
        p = np.array(CAL[k]['p']); z0 = np.clip(np.r_[p[:6], p[7:]], LO + 1e-9, HI - 1e-9)
        if q_prior is not None: z0[6:] = np.clip(q_prior, handmodel.QLO + 1e-9, handmodel.QHI - 1e-9)
        s = least_squares(res, z0, bounds=(LO, HI), max_nfev=nfev, x_scale=XS)
        X = hand(zp(s.x)); lm = float(np.sqrt(((X[Lv] - T) ** 2).sum(1).mean())); d1, _ = tE.query(X)
        if best is None or s.cost < best[0]: best = (s.cost, s.x, dict(start=k, landmark_rms_cm=round(lm, 2), chamfer_med_cm=round(float(np.median(d1)), 2)))
    return best[1], best[2]

class Obj:
    """the held object: drawn cm mesh, fields for the solve, exact distances for the report"""
    def __init__(s, V, F, pad=8.0, h=0.3):
        s.V = np.asarray(V, float); s.F = np.asarray(F); lo = s.V.min(0) - pad; hi = s.V.max(0) + pad
        s.f = gunfield.Field(s.V, s.F, lo, hi, h=h, band=1.0); s.ex = exactpen.Exact(s.V, s.F); s.lo, s.hi = lo, hi
def grip(z0, O, cuff_ref=None, W=None, nfev=150, move=False, fingers='IMRPT', palm=True, y_init=None):
    """the hand round object O, from z0 (seed). Unknowns: rotvec, t, q (+ object translation y if move). Returns z, y, metrics."""
    w = dict(pen=6.0, tol_pen=0.15, con=1.5, tol_con=0.25, palm=1.0, cuff=1.0, cuff_free=1.0, q=0.3, move=0.6, move_free=0.5); w.update(W or {})
    X0 = hand(zp(z0)); C = cuff_idx(); cref = X0[C] if cuff_ref is None else cuff_ref; sub = np.arange(0, len(X0), 2)
    R = {k: reg('pad_' + k) for k in fingers}
    if palm: R['palm'] = reg('palm')
    qs = np.r_[[1, 1, 30] * 4 + [1, 1, 30, 30] + [30, 30]]
    def unpack(v): return (v[:24], v[24:27]) if move else (v, np.zeros(3))
    def res(v):
        z, y = unpack(v); X = hand(zp(z)) - y; r = []	# the object moved by y == the hand moved by -y in the object's frame
        r.append(w['pen'] * np.maximum(0, -s_(O, X[sub]) - w['tol_pen']))
        for k, ix in R.items():
            r.append([(w['palm'] if k == 'palm' else w['con']) * max(0.0, float(np.abs(s_(O, X[ix])).min()) - w['tol_con'])])
        dc = np.linalg.norm(X[C] + y - cref, axis=1); r.append(w['cuff'] * np.maximum(0, dc - w['cuff_free']))
        r.append(w['q'] * (z[6:] - z0[6:]) / qs)
        if move: r.append([w['move'] * max(0.0, float(np.linalg.norm(y)) - w['move_free'])])
        return np.concatenate([np.atleast_1d(np.asarray(a, float)).ravel() for a in r])
    y0 = np.zeros(3)
    if move:	# a seed deep in the object traps the solve (its field is flat more than 1 cm in): first slide the object straight out,
        # away from the palm, 2.5 mm steps, until the hand is <= 0.5 cm into it (exact), at most 6 cm (fit192's 'lower the seed first')
        yi = np.zeros(3) if y_init is None else np.asarray(y_init, float)
        pc = X0[reg('palm')].mean(0); dv = (O.V.min(0) + O.V.max(0)) / 2 + yi - pc; dv /= np.linalg.norm(dv)
        for dd in np.arange(0.0, 6.01, 0.25):
            if O.ex.depth(X0[::3] - yi - dd * dv).max() <= 0.5: break
        y0 = yi + dd * dv; w['move_free'] = max(w['move_free'], float(np.linalg.norm(y0)))
    v0 = np.r_[z0, y0] if move else z0.copy()
    lo = np.r_[LO, [-np.inf] * 3] if move else LO; hi = np.r_[HI, [np.inf] * 3] if move else HI
    xs = np.r_[XS, [1, 1, 1]] if move else XS
    sol = least_squares(res, np.clip(v0, lo + 1e-9, hi - 1e-9), bounds=(lo, hi), max_nfev=nfev, x_scale=xs)
    z, y = unpack(sol.x); return z, y, float(sol.cost)
def s_(O, P): return O.f(P)
def measure(z, O, y=np.zeros(3), cuff_ref=None, eyes=None):
    X = hand(zp(z)); Xo = X - y; C = cuff_idx()
    d = O.ex.unsigned(Xo); pen = O.ex.depth(Xo)
    m = dict(pen_cm=round(float(pen.max()), 2), n_in=int((pen > 0.15).sum()))
    for k in 'IMRPT': m['gap_' + k] = round(float(d[reg('pad_' + k)].min()), 2)
    m['gap_palm'] = round(float(d[reg('palm')].min()), 2); m['touch'] = int(sum(m['gap_' + k] <= 0.3 for k in 'IMRPT'))
    if cuff_ref is not None: m['cuff_move_cm'] = round(float(np.linalg.norm(X[C] - cuff_ref, axis=1).max()), 2)
    m['object_move_cm'] = round(float(np.linalg.norm(y)), 2)
    if eyes is not None: m['visible'] = [round(v, 2) for v in visible(X, H.F, O.V + y, O.F, eyes)]
    return m
def visible(Xh, Fh, Vo, Fo, eyes, n=400):
    """share of the object's surface samples (area-weighted, front-facing to the eye) not hidden by the hand, per eye (drawn cm)"""
    a, b, c = Vo[Fo[:, 0]], Vo[Fo[:, 1]], Vo[Fo[:, 2]]; ar = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    rng = np.random.default_rng(1); k = rng.choice(len(Fo), n, p=ar / ar.sum()); u = rng.random((n, 2)); m = u.sum(1) > 1; u[m] = 1 - u[m]
    P = a[k] + (b[k] - a[k]) * u[:, :1] + (c[k] - a[k]) * u[:, 1:]
    out = []
    for e in eyes:
        e = np.asarray(e, float); ok = ~hit(e, P, Vo, Fo, 0.02)	# samples the object itself does not hide
        if ok.sum() == 0: out.append(0.0); continue
        out.append(float((~hit(e, P[ok], Xh, Fh, 0.0)).mean()))
    return out
def hit(e, P, V, F, eps):
    """segment eye -> P blocked by a triangle of (V, F) (before P - eps)"""
    A, B, Cc = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]; e1 = B - A; e2 = Cc - A; res = np.zeros(len(P), bool)
    for i in range(0, len(P), 64):
        d = P[i:i + 64] - e; L = np.linalg.norm(d, axis=1); dn = d / L[:, None]
        h = np.cross(dn[:, None, :], e2[None]); det = (e1[None] * h).sum(2); ok = np.abs(det) > 1e-9; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        s = e - A; uu = (s[None] * h).sum(2) * inv; q = np.cross(s[None], e1[None]); vv = (dn[:, None, :] * q).sum(2) * inv; t = (e2[None] * q).sum(2) * inv
        res[i:i + 64] = (ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (t > 1e-3) & (t < L[:, None] - eps)).any(1)
    return res
