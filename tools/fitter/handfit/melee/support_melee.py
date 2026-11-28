"""Melee hands lane: the SUPPORT (off) hand, an FBX L hand, for the two-handed melee weapons. The FBX L hand is the R hand mirrored
(handmodel.FbxHand('L'): M = diag(1, -1, 1), faces re-wound), so a solved R hand mirrored IS an L hand with the same joint angles.
  sword  <DSweap result>: the gun hand mirrored across the hilt's own plane (through the handle axis, normal = L made orthogonal to the
         axis) and slid down the handle by the hand's own length along it: the off hand below the main hand on the hilt (owner item 10).
  saw    <Chain_saw result> <Chain_saw_top result>: the farm's R hand on the MIRRORED saw's top handle (fit_melee.py, Chain_saw_top),
         mirrored back onto the real saw.
Both are expressed in the weapon's frame, then moved with the weapon by the MAIN fit's shift (the weapon moves to the gun hand).
Writes <out>/support_<Class>.json (X_L_ctrl, metrics, hook rows) and <out>/fbx_melee_<Class>_sup_L.md3 (bake.bake, side L).
usage: python3 support_melee.py sword <DSweap_result> <out>
       python3 support_melee.py saw <Chain_saw_result> <Chain_saw_top_result> <out>"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, json, numpy as np
import os as _fl_os; FITTER_LIB = _fl_os.environ.get('RS_FITTER_LIB', _fl_os.path.join(_fl_os.path.dirname(_fl_os.path.abspath(__file__)), '..', 'fitter_lib'))	# the batch 1-4 fitter modules (were <work>/runs/lane_b_b*run/tools)
FH = os.environ.get('MELEE_FITTER_HOME', _DP.WORK + '/fitter_home/'); sys.path.insert(0, FH)
for p in (_DP.CORE + '/hands_tool', FITTER_LIB): sys.path.insert(0, p)
import scene, exactpen, evaluate, handmodel, revindex, solve, bake
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = _DP.SRC
MIR = np.array([1.0, -1.0, 1.0])
def weapon(g):
    C = json.load(open(os.path.join(HERE, 'melee.json')))[g]; it = dict(C['it']); it['path'] = os.path.join(SRC, 'models/bd', it['path'])
    F, V = scene.merged(it); return np.asarray(F), V
def metrics(X, F, V, other=None):
    ctx = revindex.setup()[0]; L = ctx.L; ex = exactpen.Exact(V, F)
    o = dict(pen=float(ex.depth(X).max()), gap_palm=float(ex.unsigned(X[evaluate.reg(L, 'palm')]).min()), gap_web=float(ex.unsigned(X[evaluate.reg(L, 'web')]).min()))
    for f in 'IMRPT': o['gap_' + f] = float(ex.unsigned(X[evaluate.reg(L, 'pad_' + f)]).min())
    if other is not None:
        from scipy.spatial import cKDTree
        o['hand_to_hand_min'] = float(cKDTree(other).query(X)[0].min())
    return o
def bake_L(name, X_L_ctrl, out):
    ctx, x, to_g, Xf, delta = revindex.setup(); Rg, tg = solve.gun_T(ctx, x); to_c = lambda X: solve.gmove(ctx, Rg, tg, X)
    XL = to_c(X_L_ctrl); cref = to_c(Xf)[ctx.cuff] * MIR		# the L wrist where the approved R pistol wrist is, mirrored (off controller)
    rows, paths, _ = bake.bake([dict(name=name[:15], side='L', X=XL, cuff_ref=cref)], os.path.join(out, 'fbx_melee_%s_sup.md3' % name.split('_sup')[0]))
    return rows, paths['L']
def sword(res, out):
    g = 'DSweap'; J = json.load(open(os.path.join(res, 'curl3_%s.json' % g))); d = np.array(J['shift']); Xg = np.array(J['Xt']) - d   # gun (O) frame
    F, V = weapon(g)
    # the handle: PCA of the mesh, then refit on the handle part only (below the guard, measured: guard from axial t +2)
    c = V.mean(0); a = np.linalg.svd(V - c)[2][0]; a = a if a[2] > 0 else -a
    t = (V - c) @ a; Hd = V[(t < 0.5) & (np.linalg.norm((V - c) - np.outer(t, a), axis=1) < 4.5) & (t > -60)]
    c = Hd.mean(0); a = np.linalg.svd(Hd - c)[2][0]; a = a if a[2] > 0 else -a
    n = np.array([0, 1.0, 0]) - a[1] * a; n /= np.linalg.norm(n)
    Xm = Xg - 2.0 * np.outer((Xg - c) @ n, n)	# mirrored across the handle's plane
    rad = np.linalg.norm((Xg - c) - np.outer((Xg - c) @ a, a), axis=1); grip = Xg[rad < 6.0]; tg_ = (grip - c) @ a
    step = float(tg_.max() - tg_.min()); best = None
    for sl in np.arange(6.0, step + 3.01, 0.25):	# the SMALLEST slide down the handle with the hands apart (>= 0.5 cm) and pen <= 0.6 cm
        XL = Xm - sl * a; m = metrics(XL, F, V, Xg)
        if m['hand_to_hand_min'] >= 0.5 and m['pen'] <= 0.6: best = (sl, XL, m); break
    if best is None: best = (sl, XL, m)
    sl, XL, m = best; hand_t = float(((XL - c) @ a).min()); m.update(slide_cm=float(sl), grip_length_cm=step, handle_axis=a.round(4).tolist(), handle_point=c.round(3).tolist(), lowest_axial_cm=hand_t,
                                                                   handle_end_axial_cm=float(((Hd - c) @ a).min()))
    return finish(g, XL, d, m, out, 'mirror of the gun hand across the handle plane, slid %.2f cm down the handle' % sl)
def saw(res, res_top, out):
    import glob
    J = json.load(open(glob.glob(os.path.join(res, 'curl3_Chain_saw*.json'))[0])); d = np.array(J['shift'])	# Chain_saw or Chain_saw_rear (cropped fit of the same saw)
    T = json.load(open(os.path.join(res_top, 'curl3_Chain_saw_top.json'))); dt = np.array(T['shift'])
    XL = (np.array(T['Xt']) - dt) * MIR			# the farm's R hand on the mirrored saw (its O frame), mirrored back = the L hand on the saw
    F, V = weapon('Chain_saw'); Xg = np.array(J['Xt']) - d
    m = metrics(XL, F, V, Xg); jt = json.load(open(os.path.join(res_top, 'job.json'))); m['farm_minutes'] = jt.get('minutes')
    m['farm_trigger_metrics'] = jt.get('metrics', {}).get('curl', {}).get('trigger')
    return finish('Chain_saw', XL, d, m, out, 'farm R fit on the mirrored top handle (%s), mirrored back' % os.path.basename(res_top.rstrip('/')))
def finish(g, XL_gun, d, m, out, how):
    os.makedirs(out, exist_ok=True); XLc = XL_gun + d
    rows, md3 = bake_L(g + '_sup', XLc, out)
    S = dict(cls=g, how=how, metrics=m, main_shift=d.tolist(), rows=rows, md3=os.path.basename(md3), X_L_ctrl=XLc.round(4).tolist(),
             note='FBX L hand (mirror of the R rig). X_L_ctrl: O frame with the weapon moved by the main fit shift; hook rows from bake.bake (side L, wrist ref = the approved pistol wrist mirrored).')
    p = os.path.join(out, 'support_%s.json' % g); json.dump(S, open(p, 'w'), indent=1, default=float)
    print(g, how, json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in m.items() if not isinstance(v, (list, dict))}), 'bake', rows[0].get('bake_check_max_cm'))
    return S
if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'sword': sword(a[2], a[3])
    elif a[1] == 'saw': saw(a[2], a[3], a[4])
    else: raise SystemExit(__doc__)
