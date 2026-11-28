"""axe192.py measure | fit [fit192 args...] : the BrutalAxe's two-handed support (FBX L on the haft BELOW the gun hand).

The support shows only in two hands (hands.zs `hold`), when the axe is drawn by its TWO-HANDED block (MODELDEF.bd.txt AXE2, r12 placement,
the same Offset / ZOffset / Angle / Pitch / RollOffset as the AXE2 block: read from the file) and the gun hand regrips by handtable
GunHookTwo / GunRotTwo (row 24). So the scene here is: the axe mesh (ready frame 5) through the AXE2 chain, the FBX gun hand
(fbx_hv_BrutalAxe_R.md3, baked in place) drawn at GunHookTwo / GunRotTwo. The axe has no 1.92 support hold (rows192 has none): the seed
is the Rifle's 1.92 hold (s192.retarget), then the fist put round the measured haft axis (fit192 --vgrip, s192.onto_vgrip).
  measure : the haft (thin part of the mesh: cross-section radius per station along its long axis), the gun hand's extent on it.
  fit ... : fit192.fit for BrutalAxe with that scene (pass --vgrip cx,cy,cz,ax,ay,az from `measure`, --out DIR, --w JSON).
  mirror GAP ... : the seed is the FBX gun hand itself (its drawn md3, two-handed hook) MIRRORED across the plane that holds the haft
            axis and is square to the player's left-right (the left hand from its own side, palm toward the haft), then slid down the haft
            until its grip starts GAP cm below the gun hand's grip; the FBX left hand (vertex-for-vertex the mirror of the right: checked,
            2e-9 cm) solved onto those points; then fit192's solve (kind vgrip: wrap measured round the haft axis) closes it."""
import os, re, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'port'))
import s192
import melee_r12	# registers BrutalAxe in port_gun.GUNS
PG = s192.PG
def axe2_place():
    t = open(os.path.join(PG.SRC, 'MODELDEF.bd.txt'), encoding='latin1').read()
    b = [m.group(0) for m in re.finditer(r'Model BrutalAxe\s*\{[^}]*\}', t) if re.search(r'FrameIndex\s+AXE2\s', m.group(0))]
    assert len(b) == 1, len(b); b = b[0]
    g = lambda k: [float(v) for v in re.search(r'(?m)^\s*%s\s+([-\d. ]+)' % k, b).group(1).split()]
    o = g('Offset'); return [o[0], o[1], g('ZOffset')[0], g('AngleOffset')[0], g('PitchOffset')[0], g('RollOffset')[0]]
def setup():
    G = PG.GUNS['BrutalAxe']; G['place'] = axe2_place(); G['gunhand'] = os.path.join(PG.SRC, 'models/rsq/fbx/fbx_hv_BrutalAxe_R.md3')
    ht0 = s192.ht_row
    def ht(fn, row):	# the gun hand in two hands: GunHookTwo / GunRotTwo
        if row == G['row'] and fn in ('GunHook', 'GunRot'): fn = fn + 'Two'
        return ht0(fn, row)
    s192.ht_row = ht
    jl0 = s192.jl	# retarget reads fits/ported_<g>.json 'place': the two-handed placement instead
    s192.jl = lambda p: dict(jl0(p), place=G['place']) if p.endswith('ported_BrutalAxe.json') else jl0(p)
    return G
def measure():
    G = setup(); S = s192.retarget(s192.Scene('Rifle'), 'BrutalAxe', at=[0, 0])
    V = S.Vg; c = V.mean(0); u, s, vt = np.linalg.svd(V - c); a = vt[0]
    t = (V - c) @ a; print('AXE2 place', np.round(G['place'], 4), '| mesh long axis', np.round(a, 3), 'length %.1f cm' % (t.max() - t.min()))
    th = (S.Xh - c) @ a; print('gun hand along the axis %.1f .. %.1f cm' % (th.min(), th.max()))
    for x in np.arange(np.floor(t.min()), t.max(), 2.0):
        k = (t >= x) & (t < x + 2)
        if k.sum() < 3: continue
        P = V[k] - c - np.outer(t[k], a); r = np.linalg.norm(P - P.mean(0), axis=1)
        print('station %6.1f: n %4d, centre %s, radius max %.2f cm%s' % (x + 1, k.sum(), np.round(c + a * (x + 1) + P.mean(0), 2), r.max(), '  <- gun hand' if th.min() - 1 < x + 1 < th.max() + 1 else ''))
def haft_axis(S):
    V = S.Vg; c = V.mean(0); vt = np.linalg.svd(V - c)[2]; a = vt[0]; return c, a if a[2] > 0 else -a	# toward the head (up)
def near_haft(S, X, c, a, r=3.0):
    t = (X - c) @ a; P = X - c - np.outer(t, a); return t, np.linalg.norm(P, axis=1) < r
def mirror_scene(gap):
    from scipy.optimize import least_squares
    import handmodel
    G = setup(); S = s192.retarget(s192.Scene('Rifle'), 'BrutalAxe', at=[0, 0]); c, a = haft_axis(S)
	# FBX vertex -> md3 vertex (same faces, same order; the md3 splits vertices at UV seams)
    _, Fm = s192.md3_mesh(S.gh_md3, 0); HR = handmodel.FbxHand('R'); mp = np.zeros(len(HR.Vh), int); mp[HR.F.ravel()] = Fm.ravel()
    T = S.Xh[mp]
    m = np.array([0, 1.0, 0]) - a * a[1]; m /= np.linalg.norm(m)	# mirror plane normal: left-right, square to the haft
    T = T - 2 * np.outer((T - c) @ m, m)
    th, kh = near_haft(S, S.Xh, c, a); tt, kt = near_haft(S, T, c, a)
    T = T + a * ((th[kh].min() - gap) - tt[kt].max())	# its grip's top GAP cm below the gun hand's grip's bottom
	# the FBX left hand onto T (vertex for vertex): S.hand(p) with the seed carry dropped (drawn = calib frame)
    S.Rseed = np.eye(3); S.tseed = np.zeros(3)
    Rk, tk = PG.kabsch(S.hand(S.p0), T); p = s192.apply_rigid(S, S.p0, Rk, tk)
    lob = np.r_[[-np.inf] * 6, handmodel.QLO]; hib = np.r_[[np.inf] * 6, handmodel.QHI]
    z0 = np.clip(np.r_[p[:6], p[7:]], lob + 1e-9, hib - 1e-9)
    sol = least_squares(lambda z: (S.hand(np.r_[z[:6], p[6], z[6:]]) - T)[::3].ravel(), z0, bounds=(lob, hib), max_nfev=200)
    S.p0 = np.r_[sol.x[:6], p[6], sol.x[6:]]; S.X0 = S.hand(S.p0); res = float(np.sqrt(((S.X0 - T) ** 2).sum(1).mean()))
    S.r192 = dict(S.r192, vgrip_axis=list(a), seed_from='BrutalAxe gun hand mirrored', mirror_normal=list(np.round(m, 4)), gap_cm=gap, mirror_fit_rms_cm=round(res, 3))
    S.E = S.X0; S.Fe = S.Fl	# the view's "1.92" row shows the mirrored seed (the axe has no 1.92 hold)
    print('mirror seed: haft axis', np.round(a, 3), 'gun-hand grip %.1f..%.1f, seed grip %.1f..%.1f along it; FBX L onto the mirror rms %.3f cm' % (th[kh].min(), th[kh].max(), ((S.X0 - c) @ a)[kt].min(), ((S.X0 - c) @ a)[kt].max(), res), flush=True)
    return S
if __name__ == '__main__':
    if sys.argv[1] == 'measure': measure()
    elif sys.argv[1] == 'mirror':
        S = mirror_scene(float(sys.argv[2])); import fit192
        s192.retarget = lambda *a, **k: S; s192.seed_refit = lambda S_: (S_.p0, S_.X0, dict(seed='the BrutalAxe gun hand mirrored, slid down the haft', **{k: S_.r192[k] for k in ('mirror_normal', 'gap_cm', 'mirror_fit_rms_cm')}))
        sys.argv = ['fit192.py', 'BrutalAxe', '--seed-from', 'Rifle', '--kind', 'vgrip'] + sys.argv[3:]
        exec(compile(open(os.path.join(HERE, 'fit192.py')).read().split("if __name__ == '__main__':")[1].replace('\n    ', '\n'), 'fit192-main', 'exec'), vars(fit192))
    else:
        setup(); import fit192
        sys.argv = ['fit192.py', 'BrutalAxe', '--seed-from', 'Rifle'] + sys.argv[2:]
        exec(compile(open(os.path.join(HERE, 'fit192.py')).read().split("if __name__ == '__main__':")[1].replace('\n    ', '\n'), 'fit192-main', 'exec'), vars(fit192))
