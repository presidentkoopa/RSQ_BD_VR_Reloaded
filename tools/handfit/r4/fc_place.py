"""Hands r4, job 1: FlameCannon placement (owner 2026-10-27 18:46-18:48, OWNER_REPORT_2026-10-27_r3.md item 21).
No gun hand is drawn. The wrist stays pinned (the approved FBX pistol hand, fbx_b1_R.md3 frame 0, hook 0); the CANNON moves:
  - the rear flesh slit's centre goes to the wrist (the hand slides into the slit; the hand is inside the housing)
  - the housing axis is turned onto the forearm axis (the barrel runs along the forearm), the smallest turn that does it (no extra roll)
Everything is measured here, nothing typed in:
  slit  = area-weighted centre of the red-textured faces on the rear cap (F < -14 cm at the shipped placement)
  axis  = least-squares cylinder through the housing vertices (F -16..48)
  forearm axis / wrist = least-squares cylinder through the FBX hand's forearm stub (Root_joint vertices = landmarks 'cuff');
          wrist = the stub axis point at the stub's front end (95th percentile of the projections)
  muzzle = centre of the black (bore) faces at the front (F > 40)
Writes fc_place.json: rigid R, t (shipped controller-frame point -> drawn point), the MODELDEF 'place' (Offset x, y, ZOffset,
AngleOffset, PitchOffset, RollOffset; port_gun.chain) and its residual, and the measurements.
usage: python3 fc_place.py <out.json>"""
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'port'))
import common_r4 as C
from scipy.optimize import least_squares
from PIL import Image
import port_gun as PG
MD3 = 'FlameCannon/FlameCannon.md3'; SKIN = 'FlameCannon/FlameCannon.png'; BASE = dict(scale=[-1.0, 1.0, 1.0], off=[0.0, 0.0, -5.0], ready=0)
def face_colours(F, it):
    s = C.scene.md3_full(it['path'])[0]; im = np.asarray(Image.open(os.path.join(C.SRC, 'models/bd', SKIN)).convert('RGB')); h, w, _ = im.shape
    st = s['st'][F].mean(1); return im[((st[:, 1] % 1) * (h - 1)).astype(int), ((st[:, 0] % 1) * (w - 1)).astype(int)].astype(float)
def cyl(P, d0, c0, r0, f0):
    def r(p):
        d = np.array([1, p[0], p[1]]); d /= np.linalg.norm(d); c = np.array([f0, p[2], p[3]]); q = P - c; q = q - np.outer(q @ d, d); return np.linalg.norm(q, axis=1) - p[4]
    s = least_squares(r, [d0[1] / d0[0], d0[2] / d0[0], c0[1], c0[2], r0], loss='soft_l1', f_scale=0.5)
    d = np.array([1, s.x[0], s.x[1]]); d /= np.linalg.norm(d); return d, np.array([f0, s.x[2], s.x[3]]), float(s.x[4]), float(np.median(np.abs(s.fun)))
def measure():
    F, V, it = C.gun(MD3, BASE['ready'], BASE['scale'], BASE['off']); fc = face_colours(F, it); cen = V[F].mean(1)
    A = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
    red = (fc[:, 0] > fc[:, 1] + 35) & (fc[:, 0] > fc[:, 2] + 35); rear = red & (cen[:, 0] < -14)
    slit = (cen[rear] * A[rear, None]).sum(0) / A[rear].sum()
    blk = (fc.sum(1) < 60) & (cen[:, 0] > 40); muzzle = (cen[blk] * A[blk, None]).sum(0) / A[blk].sum()
    ax, ac, ar, ares = cyl(V[(V[:, 0] > -16) & (V[:, 0] < 48)], [1, 0, 0], [0, 0, -3], 12, 0.0)
    Y, T = C.pinned_hand(); I = C.fbx_index('R'); cuff = C.md3_sel(I['L']['cuff']); Q = Y[cuff]
    fa, fcen, fr, fres = cyl(Q, [1, 0, 0], [0, -0.6, -7], 3.5, -9.0)
    pr = (Q - fcen) @ fa; wrist = fcen + np.percentile(pr, 95) * fa
    return dict(F=F, V=V, it=it, slit=slit, muzzle=muzzle, n_slit_faces=int(rear.sum()), n_bore_faces=int(blk.sum()), housing_axis=ax, housing_c=ac, housing_r=ar, housing_res=ares,
                forearm_axis=fa, forearm_c=fcen, forearm_r=fr, forearm_res=fres, wrist=wrist, Y=Y, T=T)
def solve(m):
    R = C.rot_a_to_b(m['housing_axis'], m['forearm_axis']); t = m['wrist'] - R @ m['slit']; return R, t
def modeldef(R, t):
    G = dict(md3=m_path(), ready=BASE['ready'], scale=BASE['scale'], off=BASE['off'])
    X = PG.raw(G['md3'], G['ready']); V0 = PG.chain(G['scale'], G['off'], (0, 0, 0))(X); tgt = V0 @ R.T + t
    res = lambda p: (PG.chain(G['scale'], p[:3], p[3:])(X) - tgt).ravel()
    s = least_squares(res, np.r_[G['off'], 0, 0, 0]); Rm, tm = PG.rigid_move(G, s.x)
    return s.x, float(np.abs(res(s.x)).max()), float(np.abs(Rm - R).max()), float(np.abs(tm - t).max())
def m_path(): return os.path.join(C.SRC, 'models/bd', MD3)
def containment(Vm, F, Y):
    """the (undrawn) hand vs the moved housing: palm + fingers + thumb (not the forearm stub, which stays behind the slit)"""
    ex = C.exactpen.Exact(Vm, F); dep = ex.depth(Y, band=15.0); inside = dep > 0; I = C.fbx_index('R')
    stub = np.zeros(len(Y), bool); stub[C.md3_sel(I['L']['cuff'])] = True; o = {}
    for k, sel in (('hand_no_stub', ~stub), ('forearm_stub', stub)):
        out = sel & ~inside; dout = ex.unsigned(Y[out]) if out.any() else np.zeros(0)
        o[k] = dict(verts=int(sel.sum()), inside=int((sel & inside).sum()), outside=int(out.sum()), outside_max_cm=round(float(dout.max()), 3) if len(dout) else 0.0)
    return o
if __name__ == '__main__':
    m = measure(); R, t = solve(m); Vm = m['V'] @ R.T + t
    p, res, dR, dt = modeldef(R, t)
    ang = float(np.degrees(np.arccos(np.clip(m['housing_axis'] @ m['forearm_axis'], -1, 1))))
    o = dict(gun='FlameCannon', method='wrist pinned (fbx_b1_R frame 0); the cannon moves: rear slit centre -> wrist, housing axis -> forearm axis (smallest turn)',
             measured=dict(slit_centre=m['slit'].round(3).tolist(), slit_faces=m['n_slit_faces'], muzzle_centre=m['muzzle'].round(3).tolist(), bore_faces=m['n_bore_faces'],
                           housing_axis=m['housing_axis'].round(5).tolist(), housing_axis_point_F0=m['housing_c'].round(3).tolist(), housing_radius_cm=round(m['housing_r'], 2), housing_fit_median_res_cm=round(m['housing_res'], 2),
                           forearm_axis=m['forearm_axis'].round(5).tolist(), forearm_radius_cm=round(m['forearm_r'], 2), forearm_fit_median_res_cm=round(m['forearm_res'], 2), wrist=m['wrist'].round(3).tolist(),
                           turn_deg=round(ang, 3)),
             R=R.tolist(), t=t.tolist(), place=[float(x) for x in p], place_note='Offset x, Offset y, ZOffset, AngleOffset, PitchOffset, RollOffset (port_gun.chain)',
             place_residual_cm=res, place_vs_rigid=dict(R=dR, t=dt), slit_after=(R @ m['slit'] + t).round(3).tolist(), muzzle_after=(R @ m['muzzle'] + t).round(3).tolist(),
             hand_in_housing=containment(Vm, m['F'], m['Y']), gun_hand='none drawn (owner)')
    json.dump(o, open(sys.argv[1], 'w'), indent=1); print(json.dumps({k: v for k, v in o.items() if k not in ('R',)}, indent=1))
