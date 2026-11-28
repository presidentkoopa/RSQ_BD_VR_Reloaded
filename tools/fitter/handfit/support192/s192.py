"""support192/s192.py: the scene for a support-hand fit that STARTS FROM THE 1.92 HOLD (owner rule).

For a ported gun <Class>:
  - the gun as drawn now (fits/ported_<Class>.json place, the gun's ready frame, port_gun.chain), cm FLU;
  - the shipped FBX gun hand (its trigger frame, handtable GunHook / GunRot row), an obstacle;
  - 1.92's support: Ermac's hand2.md3 frame (lane_c rows192.json sframe / shook / srot) drawn the 1.92 way, then carried
    onto the moved gun by the rigid that takes the 1.92 gun (rows192 gun: path / frame / scale / off) onto the gun as drawn now
    (Kabsch over the same mesh's vertices; the residual is reported);
  - the FBX LEFT hand fitted to that very Ermac frame (lane_c landmarks_ermac_frames.json 'hand2:<k>': rigid + 18 pose
    parameters, scale fixed at the controller calibration), carried the same way = the SEED of the support fit.
Paths: RSQ_HANDS_TOOL (the lane_c fitter, default <depot>/tools/handfit/core/hands_tool), LANE data one level up."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET
TOOL = os.environ.get('RSQ_HANDS_TOOL', _DP.HANDS_TOOL); LANE = os.path.dirname(TOOL.rstrip('/'))
for p in (os.path.join(HERE, '..', 'shotguns'), os.path.join(HERE, '..', 'heavies'), os.path.join(HERE, '..', 'port'), TOOL):
    sys.path.insert(0, p)
import scene, calib, handmodel, hook, hudrender, md3write, exactpen	# the lane_c fitter first (its scene.P192 = the 1.92 pack)
import port_gun as PG
import port_sg, port_hv	# registries (hv last: its SSG entry is the one r11 used)
sys.path.insert(0, TOOL)	# port_gun puts the repo's fbx_fitter snapshot first: the lane_c fitter (with its LANE data) wins
from scipy.spatial.transform import Rotation as Rot
FITS = os.path.join(_DP.FITS)
HT = lambda: os.path.join(PG.SRC, 'zscript/rsq/handtable.zs')
def jl(p): return json.load(open(p))
def md3_mesh(path, frame):
    import struct
    d = open(path, 'rb').read(); nsurf = struct.unpack_from('<i', d, 84)[0]; off = struct.unpack_from('<i', d, 100)[0]; V = []; F = []; n = 0
    for s in range(nsurf):
        flags, snfr, nsh, nv, nt, otri, osh, ost, oxyz, oend = struct.unpack_from('<10i', d, off + 68)
        xyz = np.frombuffer(d, '<i2', snfr * nv * 4, off + oxyz).reshape(snfr, nv, 4)[:, :, :3].astype(float) / 64.0
        tri = np.frombuffer(d, '<i4', nt * 3, off + otri).reshape(nt, 3)
        V.append(xyz[min(frame, snfr - 1)]); F.append(tri + n); n += nv; off += oend
    return np.concatenate(V), np.concatenate(F)
def draw(xyz, h, r): return 100 * (hudrender.to_local(xyz, dict(hook=list(h), rot=list(r), **hook.PL)) @ hook.P.T)
def ht_row(fn, row): return PG.getrow(open(HT()).read(), fn, row)
def gunhand_md3(g):
    for f in ('%s_hv.json' % g, '%s_sg.json' % g, '%s.json' % g):
        p = os.path.join(FITS, f)
        if os.path.exists(p):
            h = jl(p).get('hand') or {}
            if h.get('md3_name') or h.get('md3'): return os.path.join(PG.SRC, 'models/rsq/fbx', h.get('md3_name') or h.get('md3'))
    p = os.path.join(PG.SRC, 'models/rsq/fbx', 'fbx_hv_%s_R.md3' % g)	# r12 port: the gun hand baked in place (hook 0), no fit JSON in fits/
    if os.path.exists(p): return p
    raise SystemExit('no gun-hand md3 for %s' % g)
class Scene:
    def __init__(s, g, names=None, gun192=None):
        s.g = g; G = s.G = PG.GUNS[g]; s.row = G['row']
        s.place = np.array(G['place']) if 'place' in G else np.array(jl(os.path.join(FITS, 'ported_%s.json' % g))['place'])
        names = names or G['names'][:1]; d = os.path.dirname(os.path.join(PG.SRC, G['md3'])); VV = []; FF = []; n = 0
        for nm in names:
            X, F = md3_mesh(os.path.join(d, nm), G['ready']); VV.append(PG.chain(G['scale'], s.place[:3], s.place[3:])(X)); FF.append(F + n); n += len(X)
        s.Vg = np.concatenate(VV); s.Fg = np.concatenate(FF); s.names = names
        # the gun hand (trigger frame) where it is drawn
        gh = G.get('gunhand') or gunhand_md3(g); s.gh_md3 = gh
        Xh, Fh = md3_mesh(gh, 0); s.Xh = draw(PG.md3_frames(gh)[0][0], *((ht_row('GunHook', s.row), ht_row('GunRot', s.row)) if s.row else ((0, 0, 0), (0, 0, 0)))); s.Fh = Fh
        # 1.92: the gun and Ermac's support
        R192 = jl(os.path.join(LANE, 'rows192.json'))[gun192 or g]; R192 = dict(R192, gun=dict(R192['gun'], path=_DP.gp192(R192['gun']['path']))); s.r192 = R192
        _, V192 = scene.merged(R192['gun']); V1, _ = md3_mesh(os.path.join(d, names[0]), G['ready'])
        V1 = PG.chain(G['scale'], s.place[:3], s.place[3:])(V1)
        assert len(V192) == len(V1), '1.92 gun mesh != 1.99 gun mesh (%d vs %d vertices)' % (len(V192), len(V1))
        s.Rm, s.tm = PG.kabsch(V192, V1); s.move_res = float(np.abs(V192 @ s.Rm.T + s.tm - V1).max())
        mv = lambda X: np.asarray(X) @ s.Rm.T + s.tm
        it = dict(path=scene.HAND2_192, frame=R192['sframe'], **scene.ERMAC_PL)
        Fe, E0 = scene.merged(dict(it, hook=(0, 0, 0), rot=(0, 0, 0))); _, E1 = scene.merged(dict(it, hook=R192['shook'], rot=R192['srot']))
        Rh, th = PG.kabsch(E0, E1); s.E = mv(E1); s.Fe = Fe
        # the FBX left hand fitted to that Ermac frame (controller frame, hook 0), carried the same way
        s.HL = handmodel.FbxHand('L'); s.lm_e = jl(os.path.join(LANE, 'landmarks_ermac_frames.json'))['hand2:%d' % R192['sframe']]
        s.p0 = np.array(s.lm_e['p']); X0 = calib.place(s.HL, s.p0); s.X0 = mv(X0 @ Rh.T + th)
        s.Rseed = s.Rm @ Rh; s.tseed = s.Rm @ th + s.tm	# hand frame (calib.place output) -> drawn
        s.L = jl(os.path.join(LANE, 'landmarks_fbx.json'))['L']; s.Fl = s.HL.F
        s.exg = exactpen.Exact(s.Vg, s.Fg); s.exh = exactpen.Exact(s.Xh, s.Fh)
    def hand(s, p):
        """p = [rotvec(3), t(3), logscale, q(18)] in the calib frame, then the seed carry -> drawn cm"""
        return calib.place(s.HL, p) @ s.Rseed.T + s.tseed

LMK = ['web', 'palm', 'pad_I', 'prox_I', 'pad_M', 'prox_M', 'pad_R', 'prox_R', 'pad_P', 'prox_P', 'pad_T', 'prox_T']
def seed_refit(S, w_lm=1.0, w_ch=0.3, nfev=80):
    """The lane_c FBX-to-Ermac frame fit (landmarks_ermac_frames) is a trimmed chamfer and can land in a fist where Ermac's
    fingers are straight (SSG: rms 1.7 cm, curled). Re-fit the FBX left hand to the SAME 1.92 Ermac frame (as drawn on the gun)
    with landmark correspondences: Ermac's landmark REGIONS (lane_c landmarks_ermac.json, hand2 has hand.md3's topology) <->
    the FBX landmark vertices (landmarks_fbx.json L), plus a trimmed two-way chamfer. Starts: lane_c's fit and the open hand
    (q = 0) placed by the landmark Kabsch; the lower cost wins. Scale stays at the controller calibration (p[6])."""
    from scipy.optimize import least_squares
    from scipy.spatial import cKDTree
    e = jl(os.path.join(LANE, 'landmarks_ermac.json')); R = e['_reg']
    T = np.array([S.E[R[k]].mean(0) for k in LMK]); Lv = np.array([S.L[k] for k in LMK]); tE = cKDTree(S.E); subE = S.E[::2]
    nolf = np.setdiff1d(np.arange(len(S.HL.Vh)), S.L['cuff'])	# the FBX forearm/cuff band has no Ermac counterpart: out of the chamfer
    nolf = nolf[::3]
    def res(z, p6):
        X = S.hand(np.r_[z[:6], p6, z[6:]]); r = [w_lm * (X[Lv] - T).ravel()]
        d1, _ = tE.query(X[nolf]); d1 = np.minimum(d1, np.quantile(d1, 0.9)); r.append(w_ch * d1)
        d2, _ = cKDTree(X).query(subE); d2 = np.minimum(d2, np.quantile(d2, 0.9)); r.append(w_ch * d2)
        return np.concatenate(r)
    lob = np.r_[[-np.inf] * 6, handmodel.QLO]; hib = np.r_[[np.inf] * 6, handmodel.QHI]; best = None
    for q in (S.p0[7:], np.zeros(18), np.r_[[0.3, 0.3, 0] * 4, [0.2, 0.2, 0, 0], [0, 0]]):
        p = np.r_[S.p0[:7], q]; X = S.hand(p); Rk, tk = PG.kabsch(X[Lv], T)	# rigid start: landmarks onto Ermac's
        Rp = Rot.from_rotvec(p[:3]).as_matrix(); Rs = S.Rseed
        # X = (s V Rp^T + t) Rs^T + ts ; apply Rk: new Rp' = Rs^T Rk Rs Rp, t' = Rs^T (Rk (Rs t + ts) + tk - ts)
        Rp2 = Rs.T @ Rk @ Rs @ Rp; t2 = Rs.T @ (Rk @ (Rs @ p[3:6] + S.tseed) + tk - S.tseed)
        z0 = np.clip(np.r_[Rot.from_matrix(Rp2).as_rotvec(), t2, q], lob + 1e-9, hib - 1e-9)
        sol = least_squares(lambda z: res(z, S.p0[6]), z0, bounds=(lob, hib), max_nfev=nfev, x_scale=np.r_[[0.02] * 3, [0.5] * 3, [0.1, 0.1, 5] * 4 + [0.1, 0.1, 5, 5] + [5, 5]])
        X = S.hand(np.r_[sol.x[:6], S.p0[6], sol.x[6:]]); lm = float(np.sqrt(((X[Lv] - T) ** 2).sum(1).mean()))
        if best is None or sol.cost < best[0]: best = (sol.cost, sol.x, lm)
    z = best[1]; p = np.r_[z[:6], S.p0[6], z[6:]]; X = S.hand(p)
    d1, _ = tE.query(X[nolf]); return p, X, dict(landmark_rms_cm=round(best[2], 2), chamfer_med_cm=round(float(np.median(d1)), 2))

def apply_rigid(S, p, Rk, tk):
    """p (calib frame) such that its drawn hand = Rk @ (drawn hand of p) + tk"""
    Rp = Rot.from_rotvec(p[:3]).as_matrix(); Rs = S.Rseed
    Rp2 = Rs.T @ Rk @ Rs @ Rp; t2 = Rs.T @ (Rk @ (Rs @ p[3:6] + S.tseed) + tk - S.tseed)
    return np.r_[Rot.from_matrix(Rp2).as_rotvec(), t2, p[6:]]
def onto_vgrip(S, p, c, a):
    """a vertical foregrip (centre c, axis a pointing up, measured on the mesh): the 1.92 fist moved so the grip runs THROUGH it:
    the fist's curl centre (mean of palm + the 4 proximal + the 4 pad landmarks) onto the grip axis at c, and its knuckle line
    (pinky -> index proximal) turned onto the axis (index on top), the smallest turn about the curl centre."""
    X = S.hand(p); L = S.L; k = [L['palm']] + [L['prox_' + f] for f in 'IMRP'] + [L['pad_' + f] for f in 'IMRP']
    cc = X[k].mean(0); u = X[L['prox_I']] - X[L['prox_P']]; u /= np.linalg.norm(u); a = np.asarray(a, float) / np.linalg.norm(a)
    v = np.cross(u, a); sn = np.linalg.norm(v); Rk = Rot.from_rotvec(v / sn * np.arcsin(min(1.0, sn))).as_matrix() if sn > 1e-9 else np.eye(3)
    if u @ a < 0: Rk = Rot.from_rotvec(v / sn * (np.pi - np.arcsin(min(1.0, sn)))).as_matrix()
    tk = np.asarray(c, float) - Rk @ cc
    return apply_rigid(S, p, Rk, tk)

def retarget(S, g, names=None, at=None):
    """a gun with NO 1.92 hold (Sniper, Machinegun): the seed is another gun's 1.92 hold (S, built for that gun), moved by the
    difference of the two guns' handtable SupportPoints (both guns keep the approved pistol aim after the port, so only a
    translation). S is changed in place to hold gun g (mesh, gun hand) with that moved seed."""
    T = Scene.__new__(Scene); T.g = g; G = T.G = PG.GUNS[g]; T.row = G['row']
    P = jl(os.path.join(FITS, 'ported_%s.json' % g)); T.place = np.array(P['place'])
    names = names or G['names'][:1]; d = os.path.dirname(os.path.join(PG.SRC, G['md3'])); VV = []; FF = []; n = 0
    for nm in names:
        X, F = md3_mesh(os.path.join(d, nm), G['ready']); VV.append(PG.chain(G['scale'], T.place[:3], T.place[3:])(X)); FF.append(F + n); n += len(X)
    T.Vg = np.concatenate(VV); T.Fg = np.concatenate(FF); T.names = names
    gh = gunhand_md3(g); T.gh_md3 = gh; T.Xh = draw(PG.md3_frames(gh)[0][0], ht_row('GunHook', T.row), ht_row('GunRot', T.row)); T.Fh = md3_mesh(gh, 0)[1]
    dsp = 100 * (ht_row('SupportPoint', T.row) - ht_row('SupportPoint', S.row))
    for k in ('HL', 'lm_e', 'L', 'Fl', 'Fe', 'Rseed', 'Rm', 'tm', 'move_res'): setattr(T, k, getattr(S, k))
    # then onto THIS gun's underside: the palm landmark 0.5 cm under the lowest surface point within 1.5 cm (F, L) of the
    # target SupportPoint (the surface sampled every 2 mm: long polygons have no vertex there), as support_gun.py does
    sp = 100 * ht_row('SupportPoint', T.row)
    if at is not None:	# a measured support part (F, L of a point on the mesh's grippable underside, cm drawn) instead of the SupportPoint
        dsp = dsp + np.r_[at[0] - sp[0], at[1] - sp[1], 0.0]; sp = np.r_[at[0], at[1], sp[2]]
    Tr = T.Vg[T.Fg]; k = np.where((Tr.min(1)[:, 0] < sp[0] + 1.5) & (Tr.max(1)[:, 0] > sp[0] - 1.5) & (Tr.min(1)[:, 1] < sp[1] + 1.5) & (Tr.max(1)[:, 1] > sp[1] - 1.5))[0]
    import sdf as _sdf
    Ps = _sdf.samples(Tr[k][:, 0], Tr[k][:, 1], Tr[k][:, 2], 0.2); Ps = Ps[(np.abs(Ps[:, 0] - sp[0]) < 1.5) & (np.abs(Ps[:, 1] - sp[1]) < 1.5)]
    under = Ps[np.argmin(Ps[:, 2])]; pal = (S.X0 + dsp)[S.L['palm']]; dsp = dsp + (under - np.array([0, 0, 0.5]) - pal)
    T.p0 = S.p0.copy(); T.tseed = S.tseed + dsp; T.E = S.E + dsp; T.X0 = S.X0 + dsp
    T.r192 = dict(S.r192, seed_from=S.g, at_cm=None if at is None else list(at), support_point_shift_cm=list(np.round(dsp, 2)), underside_cm=list(np.round(under, 2)))
    T.exg = exactpen.Exact(T.Vg, T.Fg); T.exh = exactpen.Exact(T.Xh, T.Fh); return T

def register_staged(g, poses_json, gunhand_md3_path):
    """a gun whose gun hand is NOT in this branch yet (staged, owner's call): its placement from the other lane's pose JSON
    (gun_move.modeldef_place), its mesh / ready frame / Scale / Offset from 1.92's rows192 (the same MODELDEF block), the gun hand
    baked in place (hook 0) from the given md3. No handtable row is read or written."""
    r = jl(os.path.join(LANE, 'rows192.json'))[g]['gun']; rel = r['path'].split('bd22q_192/')[1]
    PG.GUNS[g] = dict(md3=rel, names=[os.path.basename(rel)], ready=r['frame'], scale=r['scale'], off=r['off'], row=None,
                      place=jl(poses_json)['gun_move']['modeldef_place'], gunhand=gunhand_md3_path)
