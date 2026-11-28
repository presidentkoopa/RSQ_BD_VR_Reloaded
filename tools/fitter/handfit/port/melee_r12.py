"""melee_r12.py <Class> <fit.json> [--support sup.json --sprite RQXC --label FbxSupSaw] [--tag TEXT] [--dry]   (r12 port lane)

The melee hands (PICKS_melee.md; owner item 28: Chain_saw, DSweap approved; BrutalAxe staged) by the ONE method: the wrist is pinned and
the WEAPON moves to the fitted hand (fit `shift`, port_gun.place: the approved pistol's aim, translated), and everything that hangs off
the weapon moves with it:
  - the one-handed gun-controller MODELDEF block (port_gun.modeldef) and gunmoves Pivot + fire (swing) rows (port_gun.gunmoves)
  - the TWO-HANDED blocks, re-placed by least squares on every vertex through the QZD chain (port_gun.chain):
      BrutalAxe AXE2 (the head grip):  drawn = M . AXE2_old          (M = this move)
      DSweap DSL2:                     drawn = K . M . DSL1_old      (K = the 110 deg turn DSL2 applies, measured: rigid DSL1_old -> DSL2_old,
                                                                       about the controller; hands.zs turns the hands by the same K)
  - handtable row: GunHook / GunRot = 0 (the FBX hand is baked in place); GunHookTwo / GunRotTwo = M (H2 H1^-1) M^-1 (the old two-hand
    regrip, conjugated by the move: the hand still slides the same way along the haft); the support either moved with the weapon
    (old Ermac pose) or the FBX L support (its own md3, support_md3.wire); SupportPoint moved with the weapon
  - src/zscript/rsvr/melee.zs: the hit points (BladeIn / BladeOut / AxeHead, through Place) take the same rigid move: Place() applies
    RSVR_MeleeMove.Apply(k, poseFrame, flu) = the per-weapon (R, t) written here (in the controller's F/L/U cm, the chain's frame)
The fitted hand: port_gun.hand (md3, MODELDEF hand blocks, hands.zs label; no dual blocks: melee keeps its dual behaviour).
Writes fits/ported_<Class>.json."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, re, sys, json, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'heavies'))
import port_gun as pg
import port_hv
import support_md3
from scipy.optimize import least_squares
MELEE = {
 'BrutalAxe': dict(md3='models/bd/BrutalAxe/BrutalAxe.md3', names=['BrutalAxe.md3'], ready=5, scale=[-1, 1, 1], off=[0, 0, -5], row=24, k='AXE',
    two=dict(sprite='AXE2', off=[0, 8.9584, -22.2631], ao=[0, 0, 0], rule='M'), sup_frame=4,
    blocks=None, skip=[], skipcls=[], bdblock=('MODELDEF.bd.txt', 'BrutalAxe'), dual=[]),
 'Chain_saw': dict(md3='models/bd/Chain_saw/Chain_saw.md3', names=['Chain_saw.md3'], ready=11, scale=[-1.5, 1.5, 1.5], off=[0, 10, -5], row=25, k='SAW',
    two=None, sup_frame=4, blocks=None, skip=[], skipcls=[], bdblock=('MODELDEF.bd.txt', 'Chain_saw'), dual=[]),
 'DSweap': dict(md3='models/bd/DSweap/DSweap.md3', names=['DSweap.md3'], ready=0, scale=[-1, 1, 1], off=[0, 0, -5], row=26, k='SWORD',
    two=dict(sprite='DSL2', off=[0, -40.26, -33.19], ao=[0, 110, 0], rule='KM'), sup_frame=4,
    blocks=None, skip=[], skipcls=[], bdblock=('MODELDEF.bd.txt', 'DSweap'), dual=[]),
}
pg.GUNS.update(MELEE)
port_hv.HANDSPR.update({'BrutalAxe': ('RQVI', 'Axe'), 'Chain_saw': ('RQVG', 'Saw'), 'DSweap': ('RQVH', 'DS')})	# free in the pack, brutal22test6, BD_VoxelPack, doom2 (checked)

def rig(A, b):
    return np.r_[np.c_[A, b], [[0, 0, 0, 1]]]
def chainM(G, off, ao):
    A, b = pg.affine(pg.chain(G['scale'], off, ao)); return rig(A, b)
def hookM(h, r):
    """the hand-layer rigid motion (FLU cm) that hook h / rot r draw (port_gun.support_move's draw, any point set)"""
    import hook, hudrender
    xyz = pg.md3_frames(os.path.join(pg.SRC, 'models/rsq/hand2.md3'))[0][0]
    draw = lambda h, r: 100 * (hudrender.to_local(xyz, dict(hook=list(h), rot=list(r), **hook.PL)) @ hook.P.T)
    R, t = pg.kabsch(draw((0, 0, 0), (0, 0, 0)), draw(h, r)); return rig(R, t)
def replace_block(G, f, sprite, Mtgt, tag, what):
    """re-place the block of G's mesh keyed on `sprite` so it draws Mtgt (4x4 affine of md3 -> FLU)"""
    tx = pg.rd(f); hit = [m for m in pg.BLK.finditer(tx) if '"%s"' % G['names'][0] in m.group(0) and re.search(r'FrameIndex\s+%s\s' % sprite, m.group(0))]
    assert len(hit) == 1, (sprite, len(hit)); b = hit[0].group(0)
    X = pg.raw(G['md3'], G['ready']); tgt = X @ Mtgt[:3, :3].T + Mtgt[:3, 3]
    o = pg.num(r'(?m)^\s*Offset\s+([-\d. ]+)', b); z = pg.num(r'(?m)^\s*ZOffset\s+([-\d.]+)', b); po = pg.num(r'(?m)^\s*PitchOffset\s+([-\d.]+)', b)
    q0 = np.r_[o[0], o[1], z[0], 0, po[0] if po else 0, 0]
    fn = lambda q: (pg.chain(G['scale'], q[:3], q[3:])(X) - tgt).ravel(); s = least_squares(fn, q0); q = s.x; res = float(np.abs(fn(q)).max()); assert res < 0.01, (sprite, res)
    nb = re.sub(r'(?m)^[ \t]*(Offset|ZOffset|AngleOffset|PitchOffset|RollOffset)[ \t][^\n]*\n', '', b)
    nb = nb.replace('\n{\n', '\n{\n', 1)
    i = nb.index('\n', nb.index('Scale')) + 1
    nb = nb[:i] + '   Offset %.4f %.4f 0.0\n   ZOffset %.4f\n   AngleOffset %.4f\n   PitchOffset %.4f\n   RollOffset %.4f\t// %s (lane B): %s (was Offset %s %s, ZOffset %s%s)\n' % (
        tuple(q) + (tag, what, o[0], o[1], z[0], ', PitchOffset %s' % po[0] if po else '')) + nb[i:]
    pg.wr(f, tx.replace(b, nb, 1)); pg.note('TWO-HANDED block %s %s re-placed' % (f, sprite), np.round(q0, 4), '->', np.round(q, 4), 'residual %.4f cm' % res); return q

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cls'); ap.add_argument('fit'); ap.add_argument('--support'); ap.add_argument('--sprite'); ap.add_argument('--label'); ap.add_argument('--note', default='')
    ap.add_argument('--tag', default='r12 port'); ap.add_argument('--dry', action='store_true')
    pg.ARGS = A = ap.parse_args()
    G = dict(pg.GUNS[A.cls], cls=A.cls); G['md3'] = os.path.join(pg.SRC, G['md3']); pg.CUR = G
    F = json.load(open(A.fit)); fitdir = os.path.dirname(os.path.abspath(A.fit)); row = G['row']
    p, res, _, _ = pg.place(G, F['shift']); R, t = pg.rigid_move(G, p); M = rig(R, t)
    print('%s: MODELDEF Offset %.3f %.3f  ZOffset %.3f  Angle/Pitch/Roll %.3f/%.3f/%.3f (chain residual %.4f cm)' % ((A.cls,) + tuple(p) + (res,)))
    pg.gun_blocks_cache = {A.cls: pg.gun_blocks(G)}
    pg.modeldef(G, p, A.tag)
    pg.gunmoves(G, p, A.tag)
    moves = {2 if A.cls == 'Chain_saw' else 0: M}	# poseFrame -> the rigid move the hit points take (melee.zs Place; the saw is always poseFrame 2)
    T = G['two']
    if T:
        C1 = chainM(G, G['off'], (0, 0, 0)); C2 = chainM(G, T['off'], T['ao'])
        if T['rule'] == 'M':
            tgt = M @ C2; moves[1] = M; what = 'the two-handed placement moved with the weapon to the FBX hand'
        else:
            K = C2 @ np.linalg.inv(C1); assert np.abs(K[:3, :3] @ K[:3, :3].T - np.eye(3)).max() < 1e-9
            tgt = K @ M @ C1; moves[3] = K @ M @ np.linalg.inv(K); what = 'the two-handed block = its 110 deg turn K (about the controller) of the one-handed block moved to the FBX hand'
            pg.note('DSL2 turn K (rigid DSL1 -> DSL2, FLU)', np.round(K[:3, :3], 4).tolist(), np.round(K[:3, 3], 4))
        replace_block(G, 'MODELDEF.bd.txt', T['sprite'], tgt, A.tag, what)
    # the FBX gun hand (no dual blocks, no squeeze except the saw's trigger)
    H = F['hand']
    if A.cls != 'Chain_saw': H['squeeze'] = 'false && false'; H['squeeze_note'] = 'never (melee: frame 1 is the saw trigger only); fullbright frames only'
    H['sprite'], H['label'] = port_hv.HANDSPR[A.cls]
    if H.get('squeeze', 'false') == 'false': H['squeeze'], H['squeeze_note'] = port_hv.squeeze_expr(G)
    H['support'] = None
    pg.hand(G, H, R, t, A.tag, fitdir)
    tx = pg.rd('zscript/rsq/handtable.zs')
    h1 = pg.getrow(tx, 'GunHook', row); r1 = pg.getrow(tx, 'GunRot', row); h2 = pg.getrow(tx, 'GunHookTwo', row); r2 = pg.getrow(tx, 'GunRotTwo', row)
    tx0 = open(os.path.join(pg.SRC, 'zscript/rsq/handtable.zs'), encoding='latin1').read(); h1 = pg.getrow(tx0, 'GunHook', row); h2 = pg.getrow(tx0, 'GunHookTwo', row)
    D = M @ hookM(h2, r2) @ np.linalg.inv(hookM(h1, r1)) @ np.linalg.inv(M)
    import hook
    hh, rr = hook.hook_from_rigid(D[:3, :3], D[:3, 3]); hh = np.where(np.abs(hh) < 5e-4, 0, hh); rr = np.where(np.abs(rr) < 5e-4, 0, rr)
    tx = pg.setrow(tx, 'GunRot', (0, 0, 0), row); tx = pg.setrow(tx, 'GunHookTwo', hh, row); tx = pg.setrow(tx, 'GunRotTwo', rr, row)
    pg.note('handtable row %d GunRot 0 (was %s); GunHookTwo / GunRotTwo = M (H2 H1^-1) M^-1:' % (row, r1), np.round(hh, 3), np.round(rr, 3), '(was hook %s / %s, two %s / %s)' % (h1, r1, h2, r2))
    sp = pg.getrow(tx, 'SupportPoint', row); sp1 = (R @ (sp * 100) + t) / 100
    if A.support:
        S = json.load(open(A.support)); r0 = S['rows'][0]; S2 = dict(sup_hook=r0['hook'], sup_rot=r0['rot'], sup_point_m=list(np.round(sp1, 4)))
        pg.wr('zscript/rsq/handtable.zs', tx)
        support_md3.wire(A.cls, S2, A.sprite, A.label, row, A.tag, A.note, os.path.join(os.path.dirname(os.path.abspath(A.support)), S['md3']), r0.get('frame', 0))
        tx = pg.rd('zscript/rsq/handtable.zs')
    else:
        h0 = pg.getrow(tx, 'SupportHook', row); s0 = pg.getrow(tx, 'SupportRot', row)
        hs, rs = pg.support_move(G, h0, s0, R, t, None, G['sup_frame'])
        tx = pg.setrow(tx, 'SupportHook', hs, row); tx = pg.setrow(tx, 'SupportRot', rs, row); tx = pg.setrow(tx, 'SupportPoint', sp1, row)
        pg.note('handtable Support row %d (Ermac pose %s) moved with the weapon' % (row, 'E'), h0, s0, '->', np.round(hs, 3), np.round(rs, 3), 'point', sp, '->', np.round(sp1, 3))
    pg.wr('zscript/rsq/handtable.zs', tx)
    # melee.zs hit points
    tx = pg.rd('zscript/rsvr/melee.zs'); k = G['k']
    body = []
    for pf, Mm in sorted(moves.items()):
        Rm = Mm[:3, :3]; tm = Mm[:3, 3]
        body.append('\t\tif (k == RSVR_Hand.%s && pf == %d)\t// %s %s\n\t\t\treturn (%.6f * p.x + %.6f * p.y + %.6f * p.z + %.4f, %.6f * p.x + %.6f * p.y + %.6f * p.z + %.4f, %.6f * p.x + %.6f * p.y + %.6f * p.z + %.4f);' % (
            (k, pf, A.cls, {0: 'one-handed', 1: 'AXE2 (two hands)', 2: 'saw', 3: 'DSL2 (two hands): K M K^-1 on the old DSL2 point'}[pf]) + tuple(np.r_[Rm[0], tm[0], Rm[1], tm[1], Rm[2], tm[2]])))
    mark = '\t\t// %s: %s\n' % (A.tag, A.cls)
    if 'class RSVR_MeleeMove' not in tx:
        tx = tx.rstrip('\n') + ('\n\n// r12 port (lane B): the melee weapons are drawn moved to the fitted FBX hand (MODELDEF Offset / Angle, tools/handfit/port/melee_r12.py),\n'
            '// so their hit points move with them: the point Place() computed in the ORIGINAL placement (controller frame, F / L / U cm, the\n'
            '// QZD chain at vr_weaponScale 1.02) -> R p + t, the weapon\'s own rigid move. One block per weapon and placement (poseFrame).\n'
            'class RSVR_MeleeMove abstract\n{\n\tstatic Vector3 Apply(int k, int pf, Vector3 p)\n\t{\n\t\treturn p;\n\t}\n}\n')
        old = '\t\tdouble f = 0.01 * (ws * m.x - 30 - oz - sf);\n\t\tdouble r = 0.01 * (-ws * m.y + ox);\n\t\tdouble u = 0.01 * (ws * m.z + oy + su);\n'
        new = old + ('\t\t// r12 port: the weapon is drawn moved to the FBX hand: its points move the same way (RSVR_MeleeMove, F / L / U cm)\n'
            '\t\tVector3 mv = RSVR_MeleeMove.Apply(placeK, poseFrame, (100 * f, -100 * r, 100 * u));\n\t\tf = 0.01 * mv.x;\n\t\tr = -0.01 * mv.y;\n\t\tu = 0.01 * mv.z;\n')
        tx = pg.sub1(tx, old, new, 'Place body')
        tx = pg.sub1(tx, '\tint poseFrame;', '\tint poseFrame;\n\tint placeK;\t\t// r12 port: which weapon Place() is placing (RSVR_MeleeMove)', 'poseFrame decl')
        tx = pg.sub1(tx, '\t\tSpriteID s = psp.Sprite;\n\t\tposeFrame = 0;\n', '\t\tSpriteID s = psp.Sprite;\n\t\tposeFrame = 0;\n\t\tplaceK = k;\t// r12 port\n', 'ReadyPose placeK')
        tx = pg.sub1(tx, '\t\tVector3 t1 = Place(BladeOut(AXE));\n', '\t\tplaceK = AXE;\t// r12 port: the axe\'s own move (RSVR_MeleeMove)\n\t\tVector3 t1 = Place(BladeOut(AXE));\n', 'Throw placeK')
    a = '\tstatic Vector3 Apply(int k, int pf, Vector3 p)\n\t{\n'
    tx = pg.sub1(tx, a, a + mark + '\n'.join(body) + '\n', 'Apply')
    pg.wr('zscript/rsvr/melee.zs', tx); pg.note('melee.zs RSVR_MeleeMove %s: poseFrames %s' % (k, sorted(moves)))
    pg.flush(); print('moved %d items%s' % (len(pg.MOVED), ' (dry run: nothing written)' if A.dry else ''))
    if not A.dry: json.dump(dict(cls=A.cls, place=list(p), R=R.tolist(), t=t.tolist(), moves={str(k_): v.tolist() for k_, v in moves.items()}, moved=pg.MOVED), open(os.path.join(_DP.FITS, 'ported_%s.json' % A.cls), 'w'), indent=1)
