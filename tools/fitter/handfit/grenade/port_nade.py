"""port_nade.py: the grenade hand fit (fit_nade.py) into the pack, and its pose as data.
usage: python3 port_nade.py <nade_fit.json> [--dry]
  1. tools/handfit/poses/HandGrenades.json (heavies form, read by port/rebake.py: pose_vector = the solved r5-layout vector, every
     finger + thumb solved (solved_fingers IMRPT), wrist R = I, t = 0, shift 0, so rebake rebuilds exactly the fitted drawn hand),
     gun_move = the grenade's MODELDEF numbers + R, t (port_gun.rigid_move of them)
  2. the md3: rebake.py bake of that JSON -> src/models/rsq/fbx/fbx_nade_R.md3 (frames: grip, grip (squeeze = same pose), pistol check)
  3. MODELDEF.rsq: the three VR grenade blocks (RQNP C / A / B) moved; the RQGN hand block (RSQ_GunSide, Ermac's ammo_hand.md3 frame 3)
     and MODELDEF.rsqdual's HandGrenades RQGN block draw fbx_nade_R.md3 frame 0 (Ermac's placement, hook 0: Scale -1 1 1, Offset 0 -24 -10)
  4. rsg/grenade.zs: the ring point (RING_F/L/U) = the drawn ring's centre after the move; the throw and the in-hand blast spawn from the
     drawn grenade's body centre (NADE_F/L/U) when the grenade moved more than 3 cm (it is printed)
Every text edit asserts the exact text it replaces. GUNS_NADE registers the grenade for rebake.py place()."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, re, json, shutil, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET
sys.path.insert(0, os.path.join(HERE, '..', 'port'))
import port_gun as pg
from scipy.optimize import least_squares
GUNS_NADE = {'HandGrenades': dict(md3='models/bd/Grenade/nade.md3', names=['nade.md3'], ready=2, scale=[-0.92, 0.92, 0.92], off=[-4.01, -2.04, -5.0], row=None,
                                  bdblock=None, blocks={('MODELDEF.rsq', 'HandGrenades'): 3}, skip=[], skipcls=[], dual=[],
                                  note='VR blocks only (MODELDEF.rsq RQNP C/A/B). Shipped: Offset -4.01 -2.04 -1.45 then ZOffset -5; QZD reads ZOffset last, so z = -5. '
                                       'MODELDEF.bd.txt\'s flat HandGrenades block (BD22\'s own throw animation, no RSQ hand) is not moved.')}
pg.GUNS.update(GUNS_NADE)
TAG = 'grenade hand (lane B): gun to the FBX hand, fit_nade.py'
MD3 = 'fbx_nade_R.md3'
def place_of(R, t):
    G = dict(GUNS_NADE['HandGrenades']); X = pg.raw(os.path.join(pg.SRC, G['md3']), G['ready']); V0 = pg.chain(G['scale'], G['off'], (0, 0, 0))(X)
    tgt = V0 @ R.T + t; res = lambda p: (pg.chain(G['scale'], p[:3], p[3:])(X) - tgt).ravel()
    s = least_squares(res, np.r_[G['off'], 0, 0, 0]); p = np.round(s.x, 3)
    Rm, tm = pg.rigid_move(dict(G, md3=os.path.join(pg.SRC, G['md3'])), p)
    return p, float(np.abs(res(p)).reshape(-1, 3).max()), Rm, tm, V0
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('fit'); ap.add_argument('--dry', action='store_true'); a = ap.parse_args()
    J = json.load(open(a.fit)); R = np.array(J['nade']['R']); t = np.array(J['nade']['t']); c0 = np.array(J['nade']['centre'])
    p, fit_err, Rm, tm, V0 = place_of(R, t)
    sys.path.insert(0, HERE); import fit_nade as N
    F, V, S = N.nade_mesh(); assert np.abs(V - V0).max() < 1e-6, 'fit_nade mesh != port_gun chain'
    c1 = Rm @ c0 + tm; move = float(np.linalg.norm(c1 - c0)); ring = V[np.unique(F[S == N.SURF['ring']])].mean(0) @ Rm.T + tm
    print('place', p.tolist(), 'fit err %.4f cm' % fit_err, 'body centre', c0.round(3).tolist(), '->', c1.round(3).tolist(), 'moved %.2f cm' % move, 'ring', ring.round(2).tolist())
    m = J['metrics']
    pose = dict(cls='HandGrenades', fbx_source='hand_final.fbx (DXR models/hands, never shipped); start = the approved pistol hand (lane_c round4_final BrutalPistol x_gun)',
                pose_params='handmodel.FbxHand pose vector (r5 layout: 0-5 hand rotvec + cm, 6-17 I/M/R/P curl/curl/spread, 18-21 thumb curl/curl/spread/twist, 22-23 wrist flex/deviation, 24-29 the pistol gun_T, unused by the hand)',
                poses=dict(trigger=dict(pose_vector=J['pv'], solved_fingers='IMRPT', solved_params='x[0:24]: hand placement, every finger, the thumb, spread and wrist (fit_nade.py)'),
                           squeeze=dict(pose_vector=J['pv'], solved_fingers='IMRPT', note='no trigger: the squeeze frame is the grip pose'), support=None),
                wrist=dict(R=np.eye(3).tolist(), t=[0.0, 0.0, 0.0], shift_cm=[0.0, 0.0, 0.0], note='the pose vector places the hand in the drawn controller frame itself; the cuff sits on the approved pistol cuff (max %.3f cm)' % m['cuff_max']),
                gun_move=dict(place=p.tolist(), R=Rm.tolist(), t=tm.tolist(), body_centre_from=c0.tolist(), body_centre_to=c1.tolist(), moved_cm=move, fit_err_cm=fit_err,
                              how='fit_nade.py grenade rigid move (drawn frame) -> MODELDEF Offset x y 0 / ZOffset / Angle / Pitch / Roll (port_gun.chain least squares); R, t = port_gun.rigid_move of the written numbers'),
                baked=MD3, metrics=m, fit=dict(source=os.path.basename(os.path.dirname(os.path.abspath(a.fit))), cost=J['cost'], minutes=J['minutes'], thr=J['thr'], refined_from=J.get('refined_from')))
    if a.dry: return
    pp = os.path.join(_DP.POSES, 'HandGrenades.json'); json.dump(pose, open(pp, 'w'), indent=1); print('wrote', os.path.relpath(pp, REPO))
    import rebake, tempfile
    tmp = tempfile.mkdtemp(prefix='nade_'); dst = os.path.join(pg.SRC, 'models/rsq/fbx', MD3)
    if os.path.exists(dst): os.remove(dst)
    rebake.rebake(pp, os.path.join(tmp, 'nade')); shutil.copyfile(os.path.join(tmp, 'nade_R.md3'), dst); print('baked', os.path.relpath(dst, REPO))
    # MODELDEF.rsq: the three RQNP blocks
    f = os.path.join(pg.SRC, 'MODELDEF.rsq'); tx = open(f, encoding='latin1').read()
    old = '   Offset -4.01 -2.04 -1.45\n   NoInterpolation\n   ZOffset -5\n'
    new = ('   Offset %.3f %.3f 0.0\n   NoInterpolation\n   ZOffset %.3f\n   AngleOffset %.3f\n   PitchOffset %.3f\n   RollOffset %.3f\t// ' + TAG + '\n') % tuple(p)
    assert tx.count(old) == 3, tx.count(old); tx = tx.replace(old, new)
    oh = '\tPath "models/rsq"\n\tModel 0 "ammo_hand.md3"\n\tSkin 0 "hand.png"\n\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQGN A 0 3\n'
    nh = '\tPath "models/rsq/fbx"\n\tModel 0 "%s"\n\tSkin 0 "fbx_hand.png"\n\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQGN A 0 0\t// %s (frame baked in place, hook 0)\n' % (MD3, TAG.replace('gun to the FBX hand', 'the FBX hand'))
    assert tx.count(oh) == 1, tx.count(oh); tx = tx.replace(oh, nh)
    tx = pg.sub1(tx, '// ammo hand round a chaingun box (ammo_hand.md3 frame 3) round BD22\'s grenade (below)', '// the VR grenade\'s hand: the FBX hand (fbx/%s, fit_nade.py), was Ermac\'s ammo hand (ammo_hand.md3 frame 3)' % MD3, 'rsq hand comment')
    open(f, 'w', encoding='latin1').write(tx)
    f = os.path.join(pg.SRC, 'MODELDEF.rsqdual'); tx = open(f, encoding='latin1').read(); assert tx.count(oh) == 1, 'rsqdual'; tx = tx.replace(oh, nh); open(f, 'w', encoding='latin1').write(tx)
    # grenade.zs: the ring point, and the spawn point
    f = os.path.join(pg.SRC, 'zscript/rsg/grenade.zs'); tx = open(f, encoding='latin1').read()
    tx = pg.sub1(tx, '\tconst RING_F = -3.04;\t\t// the ring: nade.md3 in Ermac\'s hand (MODELDEF.rsq RQNP), gun hand cm (F, L, U)\n\tconst RING_L = 5.45;\n\tconst RING_U = 4.18;\n',
                 '\tconst RING_F = %.2f;\t\t// the ring\'s centre: nade.md3 as drawn in the FBX hand (MODELDEF.rsq RQNP, fit_nade.py), gun hand cm (F, L, U)\n\tconst RING_L = %.2f;\n\tconst RING_U = %.2f;\n' % tuple(ring)
                 + ('\tconst NADE_F = %.2f;\t\t// the grenade body\'s centre as drawn (moved %.1f cm by the FBX hand fit): the throw and the in-hand blast start here\n\tconst NADE_L = %.2f;\n\tconst NADE_U = %.2f;\n' % (c1[0], move, c1[1], c1[2]) if move > 3.0 else ''), 'ring')
    if move > 3.0:
        tx = pg.sub1(tx, '\t\tlet g = Actor.Spawn(gc, RSVR_VRHand.HandPos(mo), ALLOW_REPLACE);\n', '\t\tlet g = Actor.Spawn(gc, DrawnNade(mo), ALLOW_REPLACE);\n', 'throw spawn')
        tx = pg.sub1(tx, '\t\t\tlet e = Actor.Spawn(ec, RSVR_VRHand.HandPos(mo));\n', '\t\t\tlet e = Actor.Spawn(ec, DrawnNade(mo));\n', 'boom spawn')
        tx = pg.sub1(tx, '\tvoid Boom(PlayerPawn mo)\n', '\t// the drawn grenade (its body centre) in the world: the controller plus the gun-hand offset (geo: this tic\'s frames)\n'
                     '\tVector3 DrawnNade(PlayerPawn mo)\n\t{\n\t\tVector3 h = RSVR_VRHand.HandPos(mo);\n\t\tif (!geo)\n\t\t\treturn h;\n'
                     '\t\treturn h + geo.FromGun((NADE_F, NADE_L, NADE_U));\n\t}\n\n\tvoid Boom(PlayerPawn mo)\n', 'DrawnNade')
    open(f, 'w', encoding='latin1').write(tx)
    f = os.path.join(pg.SRC, 'zscript/rsq/hands.zs'); tx = open(f, encoding='latin1').read()
    tx = pg.sub1(tx, "\tNade: RQGN A -1; Stop;\t// Ermac's ammo hand round the VR grenade", "\tNade: RQGN A -1; Stop;\t// the FBX hand round the VR grenade (fbx_nade_R.md3, fit_nade.py)", 'hands.zs Nade')
    open(f, 'w', encoding='latin1').write(tx); print('ported: MODELDEF.rsq x3 RQNP + RQGN hand, MODELDEF.rsqdual RQGN hand, grenade.zs ring' + (' + spawn' if move > 3 else ''))
if __name__ == '__main__': main()
