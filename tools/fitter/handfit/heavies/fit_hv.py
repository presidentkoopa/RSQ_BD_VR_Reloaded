"""Heavies lane (MG42, Machinegun, Minigun, Plasma_Gun, RailGun, Rocket_Launcher, GrenadeLauncher, IncendiaryLauncher):
batch 3's method, one gun per call, no new rules:
  1. 1.92's hand placement on the gun (m192.T_of, the rows192 hold) carried onto the approved FBX pistol hand, then
     re-seated rigidly on the grip (st2_b4.stage2b = rigid3.stage2 from a given start).
     Machinegun: no 1.92 hold (not in rows192) -> starts from the MG42's 1.92 hold, moved by the trigger-face difference.
  2. M/R/P curls closed + index squeeze 0.6 cm along the bore (curl3/curl4's code, paths parametrised).
  3. Bake the gun-hand md3 (frames 0 trigger, 1 squeeze, 2 pistol re-bake check) and the FBX palm-under (RQFS B) under the
     gun at its handtable SupportPoint (bake_b3.py's support half), then write fits/<Gun>_hv.json for port_gun.py.
usage: python3 fit_hv.py <Gun> [<Gun> ...]   (outputs under RUN; the md3 + fit json are copied into tools/handfit/port/fits)
Mesh surfaces (trigger / bore) were named from surf_hv.py's listing at each gun's 1.99 ready frame."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, json, shutil, numpy as np
import os as _fl_os; FITTER_LIB = _fl_os.environ.get('RS_FITTER_LIB', _fl_os.path.join(_fl_os.path.dirname(_fl_os.path.abspath(__file__)), '..', 'fitter_lib'))	# the batch 1-4 fitter modules (were <work>/runs/lane_b_b*run/tools)
for p in (_DP.HANDS_TOOL, FITTER_LIB, FITTER_LIB, FITTER_LIB, FITTER_LIB):
    sys.path.insert(0, p)
from rigid3 import *          # fit3 (revlm.GUNS, trigger_face, BONES), m192, revindex, scene, exactpen, evaluate, handmodel, solve, least_squares
import st2_b4
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET
SRC = os.path.join(REPO, 'src'); RUN = os.environ.get('HV_RUN', _DP.WORK + '/runs/lane_b_hvrun'); os.makedirs(RUN + '/bake', exist_ok=True)
FITS = os.path.join(REPO, 'tools/handfit/port/fits')
M = lambda p: os.path.join(SRC, 'models/bd', p)
U = [-1.0, 1.0, 1.0]; O = [0.0, 0.0, -5.0]
# key: rows192 key (m192) / revlm.GUNS key. cls: weapon class. row: handtable row. ready: 1.99 ready md3 frame (MODELDEF.bd.txt FrameIndex of the Ready sprite)
HV = {
 'MG42': dict(cls='MG42', row=11, it=dict(path=M('HitlersBuzzsaw/HitlersBuzzsaw.md3'), frame=0, scale=U, off=O), trig_surf=1, bore_surf=0, src192='MG42'),
 'Machinegun': dict(cls='Machinegun', row=27, it=dict(path=M('Machinegun/Machinegun.md3'), frame=4, scale=U, off=O), trig_surf=4, bore_surf=5, src192='MG42'),
 'Minigun': dict(cls='Minigun', row=13, it=dict(path=M('Minigun/Minigun.md3'), frame=4, scale=U, off=O), trig_surf=4, bore_surf=2, src192='Minigun'),
 'Plasma_Gun': dict(cls='Plasma_Gun', row=15, it=dict(path=M('Plasma_Gun/Plasma.md3'), frame=4, scale=U, off=O), trig_surf=2, bore_surf=3, src192='Plasma_Gun'),
 'RailGun': dict(cls='RailGun', row=16, it=dict(path=M('RailGun/RailGun.md3'), frame=3, scale=U, off=O), trig_surf=3, bore_surf=2, src192='RailGun'),
 'Rocket_Launcher': dict(cls='Rocket_Launcher', row=19, it=dict(path=M('RPG/RPG.md3'), frame=5, scale=U, off=O), trig_surf=4, bore_surf=0, src192='Rocket_Launcher'),
 'GrenadeLauncher': dict(cls='GrenadeLauncher', row=8, it=dict(path=M('M79/M79.md3'), frame=3, scale=U, off=O), trig_surf=2, bore_surf=4, src192='GrenadeLauncher'),
 'IncendiaryLauncher': dict(cls='IncendiaryLauncher', row=10, it=dict(path=M('M32/m32.md3'), frame=0, scale=[-0.62, 0.62, 0.62], off=[0.0, -30.0, -8.0]), trig_surf=8, bore_surf=3, src192='IncendiaryLauncher'),
}
for k, v in HV.items(): revlm.GUNS[k] = dict(it=v['it'], grip_surf=[v['bore_surf']], trig_surf=v['trig_surf'], fmax=None, bore_surf=v['bore_surf'])

def support_point(row):
    import re
    tx = open(os.path.join(SRC, 'zscript/rsq/handtable.zs'), encoding='latin1').read()
    i0 = tx.index('static Vector3 SupportPoint(int i)'); i1 = tx.index('}', tx.index('return', i0))
    return [100 * float([s.strip() for s in a.split(',')][row]) for a in re.findall(r'static const double [xyz]\[\] = \{ ([^}]*) \};', tx[i0:i1])]

# START: a gun whose 1.92 hold re-seats badly starts from a finished gun's SOLVED placement (st2 npy), moved by the trigger-face
# difference (st2_b4's Moonlight-from-Shotvolver rule). RailGun: its 1.92 hold re-seated 41 deg off with the index pad 6.2 cm from the
# trigger (log fit_RailGun.log), so it starts from batch 3's MP40 placement (approved, rig).
START = {'RailGun': ('MP40', (_DP.WORK + '/runs/lane_b_b3run' + '/st2_MP40.npy'))}
def stage(g):
    c = HV[g]
    if g in START:
        src, npy = START[g]; a = np.load(npy); R0 = a[:9].reshape(3, 3); t0 = a[9:12]
        tr, _ = trigger_face(src); tg, _ = trigger_face(g); t0 = t0 + (tg - tr)
        o, R, t, d = st2_b4.stage2b(g, R0, t0); np.save(RUN + '/st2_%s.npy' % g, np.r_[R.ravel(), t, d]); o['start_from'] = src; return o
    R0, t0, res, P, G = m192.T_of(c['src192'])
    if c['src192'] != g:
        tr, _ = trigger_face(c['src192']) if c['src192'] in revlm.GUNS else (None, None); tg, _ = trigger_face(g); t0 = t0 + (tg - tr)
    o, R, t, d = st2_b4.stage2b(g, R0, t0); np.save(RUN + '/st2_%s.npy' % g, np.r_[R.ravel(), t, d]); return o

def curl(g, nfev=40, idx=False):		# curl4.run, paths parametrised (verbatim otherwise); idx=True = curl4's '+' mode (index solved to the trigger too)
    ctx, x, to_g, Xf, delta = revindex.setup(); L = ctx.L
    a = np.load(RUN + '/st2_%s.npy' % g); R = a[:9].reshape(3, 3); t = a[9:12]; d = a[12:15]
    F, V = scene.merged(revlm.GUNS[g]['it']); ex = exactpen.Exact(V, F); tf, bore = trigger_face(g)
    dom = ctx.H.dom; fm = lambda fs: np.array([any(str(b).startswith(BONES[f]) for f in fs) for b in dom])
    def X_of(qsl, sl, mask):
        y = x.copy(); y[sl] = qsl; Xn = to_g(solve.hand_X(ctx, y)[0]) + np.where(mask[:, None], 0, delta); return Xn @ R.T + t
    sl = list(range(6 if idx else 9, 18)); mask = fm('IMRP' if idx else 'MRP'); sub = np.where(mask)[0][::3]; lo = handmodel.QLO[sl[0] - 6:12]; hi = handmodel.QHI[sl[0] - 6:12]
    rg = {f: evaluate.reg(L, 'pad_' + f) for f in 'IMRPT'}
    def r1(q):
        X = X_of(q, sl, mask); r = list(4.0 * np.maximum(0, ex.depth(X[sub]) - 0.25))
        for f in 'MRP': r.append(2.0 * (ex.unsigned(X[rg[f]]).min() - 0.2))
        r += list(0.05 * (q - x[sl]) / np.array([1, 1, 30] * (len(sl) // 3)))
        if idx: r += list(3.0 * (X[rg['I']].mean(0) - tf))
        return np.array(r)
    s = least_squares(r1, np.clip(x[sl], lo + 1e-6, hi - 1e-6), bounds=(lo, hi), max_nfev=nfev)
    x2 = x.copy(); x2[sl] = s.x; Xt = X_of(s.x, sl, mask)
    im = fm('I'); maskI = mask | im
    def XI(qi): y = x2.copy(); y[6:9] = qi; Xn = to_g(solve.hand_X(ctx, y)[0]) + np.where(maskI[:, None], 0, delta); return Xn @ R.T + t
    tgt = Xt[rg['I']].mean(0) - 0.6 * bore; loI = handmodel.QLO[0:3]; hiI = handmodel.QHI[0:3]
    def r2(qi):
        X = XI(qi); r = list(3.0 * (X[rg['I']].mean(0) - tgt)); r += list(4.0 * np.maximum(0, ex.depth(X[im][::5]) - 0.25)); r += list(0.05 * (qi - x[6:9]) / np.array([1, 1, 30])); return np.array(r)
    s2 = least_squares(r2, np.clip(x[6:9], loI + 1e-6, hiI - 1e-6), bounds=(loI, hiI), max_nfev=40); Xs = XI(s2.x)
    m = lambda X: dict(pen=float(ex.depth(X).max()), padI_trig=float(np.linalg.norm(X[rg['I']].mean(0) - tf)), **{'gap_' + f: float(ex.unsigned(X[rg[f]]).min()) for f in 'MRPT'},
                       gap_palm=float(ex.unsigned(X[evaluate.reg(L, 'palm')]).min()), gap_web=float(ex.unsigned(X[evaluate.reg(L, 'web')]).min()))
    X0 = Xf @ R.T + t
    o = dict(gun=g, rigid_only=m(X0), trigger=m(Xt), squeeze=m(Xs), squeeze_travel=float(np.linalg.norm(Xs[rg['I']].mean(0) - Xt[rg['I']].mean(0))), shift=d.tolist())
    json.dump(dict(o, Xt=(Xt + d).tolist(), Xs=(Xs + d).tolist(), R=R.tolist(), t=t.tolist()), open(RUN + '/curl3_%s.json' % g, 'w'))
    return o

def bake_it(g):		# bake_b3.py, parametrised
    import bake, hook, hudrender, md3write, gunmove
    ctx, x, to_g, Xf, delta = revindex.setup(); Rg, tg = solve.gun_T(ctx, x); to_c = lambda X: solve.gmove(ctx, Rg, tg, X)
    J = json.load(open(RUN + '/curl3_%s.json' % g)); B1 = os.path.join(SRC, 'models/rsq/fbx/')
    ent = [dict(name=g + '_trg', side='R', X=to_c(np.array(J['Xt']))), dict(name=g + '_sqz', side='R', X=to_c(np.array(J['Xs']))), dict(name='PISTOL_chk', side='R', X=to_c(Xf))]
    for e in ent: e['cuff_ref'] = e['X'][ctx.cuff]
    rows, paths, _ = bake.bake(ent, RUN + '/bake/fbx_hv_%s.md3' % g)
    chk = float(np.abs(scene.md3_full(paths['R'])[0]['xyz'][2] - scene.md3_full(B1 + 'fbx_b1_R.md3')[0]['xyz'][0]).max())
    Lm = scene.md3_full(B1 + 'fbx_b1_L.md3')[0]
    Y = 100 * (hudrender.to_local(Lm['xyz'][1], dict(hook=[0, 0, 0], rot=[0, 0, 0], **hook.PL)) @ hook.P.T)
    H = handmodel.FbxHand('L'); _, src, _ = md3write.split_uv(H.h.F, H.h.Fc, H.h.uv_corner)
    Lj = json.load(open((_DP.CORE + '/landmarks_fbx.json')))['L']
    pk = np.where(np.isin(src, Lj['palm']))[0] if isinstance(Lj['palm'], list) else np.where(src == Lj['palm'])[0]
    palm = Y[pk].mean(0)
    Rm, tm = gunmove.move('BrutalPistol'); Rf, _ = gunmove.move('Flamethrower2'); Rs = Rm @ Rf.T
    dd = np.array(J['shift']); F_, V_ = scene.merged(revlm.GUNS[g]['it']); Vm = (V_ + dd) @ Rm.T + tm
    SPm = Rm @ (np.array(support_point(HV[g]['row'])) + dd) + tm
    rad = 1.5
    while True:
        near = Vm[(np.abs(Vm[:, 0] - SPm[0]) < rad) & (np.abs(Vm[:, 1] - SPm[1]) < rad)]
        if len(near): break
        rad += 1.0
    under = near[np.argmin(near[:, 2])]; Yr = (Y - palm) @ Rs.T; ex = exactpen.Exact(Vm, F_); best = None
    for dz in np.arange(0.0, -4.01, -0.1):
        Ys = Yr + under + np.array([0, 0, dz]); pen = float(ex.depth(Ys).max())
        if pen <= 0.5: best = (dz, pen, Ys); break
    if best is None: best = (dz, pen, Ys)
    dz, pen, Ys = best; ts = under + np.array([0, 0, dz]) - Rs @ palm
    h, r = hook.hook_from_rigid(Rs, ts); gap = float(ex.unsigned(Ys[pk]).min())
    sup = dict(sup_hook=list(map(float, h)), sup_rot=list(map(float, r)), sup_point_m=list(map(float, SPm / 100)))
    return dict(rows=[str(r_) for r_ in rows], pistol_rebake_max=chk, sup_pen=pen, sup_gap=gap, sup_dz=float(dz), sup_search_cm=rad), sup, paths['R']

def fit(g, squeeze='false', squeeze_note='fullbright (firing) frames', sprite=None, label=None, skip_stage=False, bake_only=False):
    if skip_stage: o1 = dict(reused=RUN + '/st2_%s.npy' % g)
    else: o1 = stage(g); print(g, 'stage2', json.dumps(o1, default=float), flush=True)
    if bake_only:	# '==Gun': the saved curl (curl3_<g>.json) as it is
        J = json.load(open(RUN + '/curl3_%s.json' % g)); o2 = {k: v for k, v in J.items() if k not in ('Xt', 'Xs', 'R', 't')}
    else: o2 = curl(g)
    if not bake_only and o2['trigger']['padI_trig'] > 1.0:	# the re-seat left the index pad off the trigger: curl4's '+' mode (index solved too)
        print(g, 'curl (M/R/P only)', json.dumps(o2['trigger'], default=float), '-> index solved too', flush=True); o2 = curl(g, idx=True)
    print(g, 'curl', json.dumps({k: ({a: round(b, 2) for a, b in v.items()} if isinstance(v, dict) else v) for k, v in o2.items()}, default=float), flush=True)
    o3, sup, md3 = bake_it(g); print(g, 'bake', json.dumps(o3, default=float), flush=True)
    os.makedirs(FITS, exist_ok=True); name = 'fbx_hv_%s_R.md3' % g; shutil.copyfile(md3, os.path.join(FITS, name))
    F = dict(shift=o2['shift'], hand=dict(md3=name, md3_name=name, sprite=sprite, label=label, squeeze=squeeze, squeeze_note=squeeze_note, support=sup,
             support_note="the FBX palm-under (RQFS B) under the gun at its SupportPoint, moved with the gun (fit_hv.py)"),
             metrics=dict(stage2=o1, curl={k: v for k, v in o2.items() if k != 'shift'}, bake=o3))
    json.dump(F, open(os.path.join(FITS, '%s_hv.json' % g), 'w'), indent=1, default=float); return F
if __name__ == '__main__':
    for g in sys.argv[1:]: fit(g.lstrip('='), skip_stage=g.startswith('='), bake_only=g.startswith('=='))	# '=Gun': reuse the saved stage-2 placement
