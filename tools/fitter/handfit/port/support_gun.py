"""support_gun.py <Class> <A|B> <out.json> [--names m1.md3,m2.md3] [--ref MP40|BrutalPistol]

Batch 5: the FBX support hand (fbx_b1_L.md3: frame 0 = RQFS A the pistol cup, frame 1 = RQFS B the open palm under)
placed on a PORTED gun at 1.92's SupportPoint, moved with the gun (the gun already sits where port_gun.py put it; the
wrist of the gun hand stays pinned, nothing here moves the gun or the gun hand).
  - B (palm under): the MP40's solved palm-under (handtable row 12, batch 3) keeps its relation to the bore: its rotation
    is carried by R_gun R_mp40^T. Its palm goes under the gun's lowest point within 1.5 cm of the moved 1.92 SupportPoint
    and is lowered in 1 mm steps until the hand is clear of the gun (pen <= 0.5 cm, lane_c TOL), as bake_b3.py.
  - A (cup): the BrutalPistol's cup (row 4, hook 0) keeps its relation to the pistol's 1.92 SupportPoint (moved with the
    pistol's r5 move) and is carried to this gun's moved 1.92 SupportPoint (rotation R_gun R_pistol^T), then lowered the
    same way until clear of the gun AND the gun hand (its baked trigger frame, hook 0).
Writes sup_hook / sup_rot / sup_point_m (what port_gun.py --support writes into handtable) and the measurements.
Needs RSQ_HANDS_TOOL (a full fitter checkout: landmarks_fbx.json one level up, the FBX for the palm vertices)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, re, sys, json, struct, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
TOOL = os.environ.get('RSQ_HANDS_TOOL'); assert TOOL, 'set RSQ_HANDS_TOOL'
sys.path.insert(0, TOOL)
import port_gun as PG
import hook, hudrender, exactpen, handmodel, md3write

def md3_mesh(path, frame):
    d = open(path, 'rb').read(); nsurf = struct.unpack_from('<i', d, 84)[0]; off = struct.unpack_from('<i', d, 100)[0]; V = []; F = []; n = 0
    for s in range(nsurf):
        flags, snfr, nsh, nv, nt, otri, osh, ost, oxyz, oend = struct.unpack_from('<10i', d, off + 68)
        xyz = np.frombuffer(d, '<i2', snfr * nv * 4, off + oxyz).reshape(snfr, nv, 4)[:, :, :3].astype(float) / 64.0
        tri = np.frombuffer(d, '<i4', nt * 3, off + otri).reshape(nt, 3)
        V.append(xyz[min(frame, snfr - 1)]); F.append(tri + n); n += nv; off += oend
    return np.concatenate(V), np.concatenate(F)
def table_row(path, fn, row):
    tx = open(path).read(); return PG.getrow(tx, fn, row)
def draw(xyz, h, r):
    return 100 * (hudrender.to_local(xyz, dict(hook=list(h), rot=list(r), **hook.PL)) @ hook.P.T)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cls'); ap.add_argument('pose'); ap.add_argument('out')
    ap.add_argument('--names'); ap.add_argument('--src'); ap.add_argument('--sp192', help='1.92 handtable.zs (default lane_c bd22q_192)')
    ap.add_argument('--also', help='another ported class sharing this handtable row: its gun and gun hand are obstacles too'); ap.add_argument('--near', type=float, default=1.5, help='cm: x/y window round the SupportPoint for the contact'); ap.add_argument('--sprow', type=int, help='1.92 SupportPoint row (default the gun row)')
    a = ap.parse_args()
    SRC = os.path.abspath(a.src) if a.src else PG.SRC; PG.SRC = SRC
    G = PG.GUNS[a.cls]; FIT = os.path.join(_DP.FITS)
    P = json.load(open(os.path.join(FIT, 'ported_%s.json' % a.cls))); p = np.array(P['place']); R = np.array(P['R']); t = np.array(P['t'])
    R2, t2 = PG.rigid_move(G, p); assert np.abs(R2 - R).max() < 1e-9 and np.abs(t2 - t).max() < 1e-6, 'ported json != chain'
    # the gun as drawn after the port
    names = a.names.split(',') if a.names else G['names'][:1]
    d = os.path.dirname(os.path.join(SRC, G['md3'])); VV = []; FF = []; n = 0
    for nm in names:
        X, F = md3_mesh(os.path.join(d, nm), G['ready']); VV.append(PG.chain(G['scale'], p[:3], p[3:])(X)); FF.append(F + n); n += len(X)
    Vg = np.concatenate(VV); Fg = np.concatenate(FF); exg = exactpen.Exact(Vg, Fg)
    T192 = a.sp192 or (_DP.GUNPACK192 + '/zscript/rsq/handtable.zs')
    row = G['row']; sp192 = table_row(T192, 'SupportPoint', a.sprow or row) * 100; SPd = R @ sp192 + t
    # the FBX support hand
    L = os.path.join(SRC, 'models/rsq/fbx/fbx_b1_L.md3'); fr = 0 if a.pose == 'A' else 1
    xyz = PG.md3_frames(L)[0][fr]; Y0 = draw(xyz, (0, 0, 0), (0, 0, 0))
    H = handmodel.FbxHand('L'); _, src, _ = md3write.split_uv(H.h.F, H.h.Fc, H.h.uv_corner)
    Lm = json.load(open(os.path.join(os.path.dirname(TOOL.rstrip('/')), 'landmarks_fbx.json')))['L']
    pk = np.where(np.isin(src, np.atleast_1d(Lm['palm'])))[0]; assert len(pk), 'palm vertices'
    obst = [exg]; extra = {}
    HT = os.path.join(SRC, 'zscript/rsq/handtable.zs')
    if a.pose == 'B':
        Gm = PG.GUNS['MP40']; pm = json.load(open(os.path.join(FIT, 'MP40_b3.json')))['place']; Rm, _ = PG.rigid_move(Gm, np.array(pm))
        Ym = draw(xyz, table_row(HT, 'SupportHook', 12), table_row(HT, 'SupportRot', 12)); Rsm, _ = PG.kabsch(Y0, Ym)
        Rs = R @ Rm.T @ Rsm; Yr = (Y0 - Y0[pk].mean(0)) @ Rs.T
        T = Vg[Fg]; lo = T.min(1); hi = T.max(1); w = a.near	# the surface sampled every ~2 mm on the triangles that reach the window (long polys have no vertex there)
        k = np.where((lo[:, 0] < SPd[0] + w) & (hi[:, 0] > SPd[0] - w) & (lo[:, 1] < SPd[1] + w) & (hi[:, 1] > SPd[1] - w))[0]; pts = []
        for tri in T[k]:
            n = int(np.ceil(np.linalg.norm(tri - np.roll(tri, 1, 0), axis=1).max() / 0.2)) + 1
            u, v = np.meshgrid(np.linspace(0, 1, n + 1), np.linspace(0, 1, n + 1)); m = u + v <= 1; u, v = u[m], v[m]
            pts.append(tri[0] + u[:, None] * (tri[1] - tri[0]) + v[:, None] * (tri[2] - tri[0]))
        S_ = np.concatenate(pts); near = S_[(np.abs(S_[:, 0] - SPd[0]) < w) & (np.abs(S_[:, 1] - SPd[1]) < w)]; under = near[np.argmin(near[:, 2])]
        base = under; extra['under'] = under.round(3).tolist()
    else:
        R0, t0 = PG.pistol_move(); spp = R0 @ (table_row(T192, 'SupportPoint', 4) * 100) + t0
        assert np.abs(table_row(HT, 'SupportHook', 4)).max() == 0, 'pistol cup is at hook 0'
        Rs = R @ R0.T; Yr = (Y0 - spp) @ Rs.T; base = SPd
        gh = json.load(open(os.path.join(FIT, '%s.json' % a.cls)))['hand']; ghx = PG.md3_frames(os.path.join(FIT, gh['md3']))
        Xh = draw(ghx[0][0], (0, 0, 0), (0, 0, 0)); Fh = md3_mesh(os.path.join(FIT, gh['md3']), 0)[1]; obst.append(exactpen.Exact(Xh, Fh))
        extra['pistol_sp_drawn'] = spp.round(3).tolist()
    if a.also:	# a class sharing the row (BrutalRevolver shares row 17): the same support must clear its gun and gun hand too
        Ga = PG.GUNS[a.also]; pa = np.array(json.load(open(os.path.join(FIT, 'ported_%s.json' % a.also)))['place'])
        Xa, Fa = md3_mesh(os.path.join(SRC, Ga['md3']), Ga['ready']); obst.append(exactpen.Exact(PG.chain(Ga['scale'], pa[:3], pa[3:])(Xa), Fa))
        gha = json.load(open(os.path.join(FIT, '%s.json' % a.also)))['hand']['md3']
        obst.append(exactpen.Exact(draw(PG.md3_frames(os.path.join(FIT, gha))[0][0], (0, 0, 0), (0, 0, 0)), md3_mesh(os.path.join(FIT, gha), 0)[1])); extra['also'] = a.also
    pen0 = None
    for dz in np.arange(0.0, -3.01, -0.1):
        Ys = Yr + base + np.array([0, 0, dz]); pen = max(float(o.depth(Ys[::4]).max()) for o in obst)	# every 4th vertex while lowering; full check below
        if pen0 is None: pen0 = pen
        if pen <= 0.5 and max(float(o.depth(Ys).max()) for o in obst) <= 0.5: break
    else: raise SystemExit('support: not clear of the gun within 3 cm (pen %.2f): flag' % pen)
    ts = Ys.mean(0) - (Y0 @ Rs.T).mean(0)	# Ys = Rs Y0 + ts
    h, r = hook.hook_from_rigid(Rs, ts); chk = hook.check(xyz, h, r, Ys)
    gap = float(exg.unsigned(Ys[pk]).min())
    pens = [float(o.depth(Ys).max()) for o in obst]
    out = dict(cls=a.cls, pose=a.pose, frame=fr, sup_hook=np.round(h, 3).tolist(), sup_rot=np.round(r, 3).tolist(), sup_point_m=(SPd / 100).round(3).tolist(),
               sp192_cm=sp192.round(3).tolist(), dz=round(float(dz), 2), pen_at_contact=round(pen0, 2), pen_gun=round(pens[0], 2),
               pen_gunhand=round(pens[1], 2) if len(pens) > 1 else None, pen_also_gun_hand=[round(v, 2) for v in pens[2:]], palm_gap_to_gun=round(gap, 2), check=round(chk, 4), names=names, **extra)
    print(json.dumps(out)); json.dump(out, open(a.out, 'w'), indent=1)
