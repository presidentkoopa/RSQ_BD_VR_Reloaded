"""port_hv.py <Class> <fit.json> [--src DIR] [--tag TEXT] [--dry]
The heavies lane's entry to tools/handfit/port/port_gun.py (unchanged, imported): it registers the heavies' guns (GUNS_HV,
parsed from the tree: MODELDEF names/scale/offset, handtable row, rsr_guns.bd.zs / rsb_guns.zs case, casings.zs row, scope
row) and adds the one move port_gun.py does not have: break-open (rsb_guns.zs) rows written as switch cases (the M79).
Then it runs port_gun.py's own main sequence."""
import os, re, sys, json, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'port'))
import port_gun as pg
D = lambda cls, extra=(): [('MODELDEF.rsqdual', cls)] + list(extra)
# r10: MG42 / Machinegun + their reload drawings (*_rsr.md3, MODELDEF.rsr: were not moved, as the MiniGun's in r9); the Machinegun's
# muzzle on the M249 barrel (surface 5), not the launcher tube, and its launcher (gun 2) tables move (m203mg); NukeLauncher, BFG10k added.
GUNS_HV = {
 'MG42': dict(md3='models/bd/HitlersBuzzsaw/HitlersBuzzsaw.md3', names=['HitlersBuzzsaw.md3'], names_extra=['HitlersBuzzsaw_rsr.md3'], ready=0, scale=[-1, 1, 1], off=[0, 0, -5], row=11, rsr=10,
    casing='MG42', blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'MG42'), dual=D('MG42', [('MODELDEF.purist', 'PuristMG42')])),
 'Machinegun': dict(md3='models/bd/Machinegun/Machinegun.md3', names=['Machinegun.md3'], names_extra=['Machinegun_rsr.md3'], ready=4, muzzle_surf=[5], m203mg=True, scale=[-1, 1, 1], off=[0, 0, -5], row=27, rsr=18,
    casing='Machinegun', blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'Machinegun'), dual=[]),
 'Minigun': dict(md3='models/bd/Minigun/Minigun.md3', names=['Minigun.md3'], names_extra=['Minigun_rsr.md3'],	# r9: the reload drawing (MODELDEF.rsr Minigun / RSR_GunParts) moves too
    ready=4, scale=[-1, 1, 1], off=[0, 0, -5], row=13, rsr=17,
    kick_surf=[0, 1, 3, 4, 5],	# the recoil fit leaves out surface 2 'Pipe' (the spinning barrels: shipped rows are 0 for spin-only frames)
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'Minigun'), dual=D('Minigun', [('MODELDEF.purist', 'PuristMinigun')])),
 'Plasma_Gun': dict(md3='models/bd/Plasma_Gun/Plasma.md3', names=['Plasma.md3'], ready=4, scale=[-1, 1, 1], off=[0, 0, -5], row=15, rsr=7,
    blocks=None, skip=['RQZW'], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'Plasma_Gun'),
    dual=D('Plasma_Gun', [('MODELDEF.rsqoff', 'RSQ_Off_Plasma_Gun'), ('MODELDEF.purist', 'PuristPlasma_Gun')])),
 'RailGun': dict(md3='models/bd/RailGun/RailGun.md3', names=['RailGun.md3'], ready=3, scale=[-1, 1, 1], off=[0, 0, -5], row=16, rsr=6, scope=1,
    blocks=None, skip=['RQLW'], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'RailGun'),
    dual=D('RailGun', [('MODELDEF.rsqoff', 'RSQ_Off_RailGun'), ('MODELDEF.purist', 'PuristRailGun')])),
 'Rocket_Launcher': dict(md3='models/bd/RPG/RPG.md3', names=['RPG.md3'], ready=5, scale=[-1, 1, 1], off=[0, 0, -5], row=19, rsr=9,
    blocks=None, skip=['RQDW'], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'Rocket_Launcher'),
    dual=D('Rocket_Launcher', [('MODELDEF.purist', 'PuristRocket_Launcher')])),
 'GrenadeLauncher': dict(md3='models/bd/M79/M79.md3', names=['M79.md3'], ready=3, scale=[-1, 1, 1], off=[0, 0, -5], row=8, rsbcase=2,
    blocks=None, skip=['RBGW'], skipcls=['RSB_Round'], bdblock=('MODELDEF.bd.txt', 'GrenadeLauncher'),	# r9: RSQ_Hands RBGP H (the round in the off hand) moves too: RSB.Place hooks it with Offset(i) (batch 4 rule)
   
    dual=D('GrenadeLauncher', [('MODELDEF.purist', 'PuristGrenadeLauncher')])),
 'IncendiaryLauncher': dict(md3='models/bd/M32/m32.md3', names=['m32.md3'], names_extra=['m32_rsr.md3'],	# r9: the reload drawing (MODELDEF.rsr IncendiaryLauncher / RSR_GunParts) moves too
    ready=0, scale=[-0.62, 0.62, 0.62], off=[0, -30, -8], row=10, rsr=12,
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'IncendiaryLauncher'),
    dual=D('IncendiaryLauncher', [('MODELDEF.purist', 'PuristIncendiaryLauncher')])),
 'BFG10k': dict(md3='models/bd/BFG/BFG_10k.md3', names=['BFG_10k.md3'], ready=4, scale=[-1, 1, 1], off=[0, 0, -5], row=2,	# r10 (farm guns.json; no rsr / rsb case, no casing)
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'BFG10k'),
    dual=D('BFG10k', [('MODELDEF.purist', 'PuristBFG10k')])),
 'NukeLauncher': dict(md3='models/bd/Nuker/Nuker.md3', names=['Nuker.md3'], names_extra=['Nuker_rsr.md3'], ready=0, scale=[-1.1, 1.1, 1.1], off=[0, 0, -5], row=14, rsr=15,	# r10 (farm guns.json: frame 0, MODELDEF.bd.txt)
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'NukeLauncher'),
    dual=D('NukeLauncher', [('MODELDEF.purist', 'PuristNukeLauncher')])),
 # r11 (farm guns.json: BFG.md3 frame 4 / sidewinder.md3 frame 0, handtable rows 3 / 6; MODELDEF.bd.txt + purist blocks parsed;
 # BFG9000: no rsr / rsb case, no casing; Devastator: rsr case 14 (+ its reload drawing sidewinder_rsr.md3), Offset 0 -13 0 (no ZOffset: rd_norm))
 'BIG_FUCKING_GUN': dict(md3='models/bd/BFG/BFG.md3', names=['BFG.md3'], ready=4, scale=[-1, 1, 1], off=[0, 0, -5], row=3,
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'BIG_FUCKING_GUN'),
    dual=D('BIG_FUCKING_GUN', [('MODELDEF.purist', 'PuristBIG_FUCKING_GUN')])),
 'Devastator': dict(md3='models/bd/Sidewinder/sidewinder.md3', names=['sidewinder.md3'], names_extra=['sidewinder_rsr.md3'], ready=0, scale=[-1, 1, 1], off=[0, -13, 0], row=6, rsr=14,
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'Devastator'),
    dual=D('Devastator', [('MODELDEF.purist', 'PuristDevastator')])),
 # r11: SSG through this entry (not shotguns/port_sg.py): its break-open is rsb case 1 and its off-hand shell block (MODELDEF.rsb
 # RSQ_Hands RBSP H) is drawn with Offset(1), so batch 4's rule applies as for the M79: that block moves and the hold rows are
 # re-expressed (rsb_cases); port_sg.py's rsbc keeps RSQ_Hands out and the hold rows unchanged. Registry numbers as port_sg.py's.
 'SSG': dict(md3='models/bd/SSG/SSG.md3', names=['SSG.md3'], ready=1, scale=[-1, 1, 1], off=[0, 0, -5], row=20, rsbcase=1, casing='SSG',
    blocks=None, skip=['RBSW'], skipcls=['RSB_Round'], bdblock=('MODELDEF.bd.txt', 'SSG'),
    dual=[('MODELDEF.rsqdual', 'SSG'), ('MODELDEF.rsqoff', 'RSQ_Off_SSG'), ('MODELDEF.purist', 'PuristSSG')]),
 # r12 (farm/guns.json _note_r4: ready frame 0, Scale -1 1 1, Offset 0 0, ZOffset -5; handtable rows 23 / 9; rsr cases 13 / 16 and their reload
 # drawings Unmaker_rsr.md3 / HellishMissile_rsr.md3 (MODELDEF.rsr: the gun without its magazine + RSR_GunParts at the gun move; RSQ_Hands = the
 # skull / drum in the off hand and RSR_DroppedMag stay). FlameCannon: no handtable row in the tree (r12 adds row 28 for its support), no rsr case.
 'Unmaker': dict(md3='models/bd/Unmaker/Unmaker.md3', names=['Unmaker.md3'], names_extra=['Unmaker_rsr.md3'], ready=0, scale=[-1, 1, 1], off=[0, 0, -5], row=23, rsr=13,
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'Unmaker'),
    dual=D('Unmaker', [('MODELDEF.purist', 'PuristUnmaker')])),
 'HellishMissileLauncher': dict(md3='models/bd/HellishMissile/HellishMissile.md3', names=['HellishMissile.md3'], names_extra=['HellishMissile_rsr.md3'], ready=0, scale=[-1, 1, 1], off=[0, 0, -5], row=9, rsr=16,
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'HellishMissileLauncher'),
    dual=D('HellishMissileLauncher', [('MODELDEF.purist', 'PuristHellishMissileLauncher')])),
 'FlameCannon': dict(md3='models/bd/FlameCannon/FlameCannon.md3', names=['FlameCannon.md3'], ready=0, scale=[-1, 1, 1], off=[0, 0, -5], row=28,
    blocks=None, skip=[], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'FlameCannon'), dual=[]),
}
pg.GUNS.update(GUNS_HV)
# hand sprites (new; free in the pack, brutal22test6 and BD_VoxelPack: checked by name) and state-label suffixes
HANDSPR = {'MG42': ('RQV1', 'MG42'), 'Machinegun': ('RQV2', 'MGun'), 'Minigun': ('RQV3', 'Mini'), 'Plasma_Gun': ('RQV4', 'Plas'), 'RailGun': ('RQV5', 'Rail'),
           'Rocket_Launcher': ('RQV6', 'RL'), 'GrenadeLauncher': ('RQV7', 'GL'), 'IncendiaryLauncher': ('RQV8', 'Inc'),
           'NukeLauncher': ('RQV9', 'Nuke'), 'BFG10k': ('RQVA', 'BFGk'),
           'BIG_FUCKING_GUN': ('RQVB', 'BFG9'), 'Devastator': ('RQVC', 'Deva'), 'SSG': ('RQVD', 'SSG'),
           'Unmaker': ('RQVE', 'Unm'), 'HellishMissileLauncher': ('RQVF', 'HML')}	# r12: RQVE / RQVF free in the pack, brutal22test6, BD_VoxelPack and doom2 (checked)	# r11: RQV8 / RQVB / RQVC / RQVD free in the pack, brutal22test6 and BD_VoxelPack (checked)	# r10: RQV9 free in the pack, brutal22test6 and BD_VoxelPack (checked)
EXTRA_SQZ = {'Machinegun': [('MGN1', 'BCDEFK')]}	# no gunmoves rows: its Fire frames (Machinegun.dec Fire: MGN1 B-F, K)
def squeeze_expr(G):
    """the gun hand squeezes on the gun's fire frames: the sprites/frames gunmoves.zs keys to its handtable row (+ EXTRA_SQZ)"""
    tx = pg.rd('zscript/rsq/gunmoves.zs')
    spr = re.findall(r'"([^"]+)"', re.search(r'static const String spr\[\] = \{([^}]*)\}', tx).group(1))
    key = [int(v) for v in re.search(r'static const int key\[\] = \{([^}]*)\}', tx).group(1).split(',')]
    fr = {}
    for k, sname in enumerate(spr):
        if key[2 * k] == G['row']: fr.setdefault(sname[:4], set()).update(ord(c) - 65 for c in sname[4:])
    for sp, ls in EXTRA_SQZ.get(G['cls'], []): fr.setdefault(sp, set()).update(ord(c) - 65 for c in ls)
    parts = ["(mgp.Sprite == Actor.GetSpriteIndex('%s') && (%s))" % (sp, ' || '.join('mf == %d' % f for f in sorted(fs))) for sp, fs in sorted(fr.items())]
    return ' || '.join(parts) if parts else 'false', 'fire frames: ' + ', '.join('%s %s' % (sp, ''.join(chr(65 + f) for f in sorted(fs))) for sp, fs in sorted(fr.items()))
NOGUNMOVES = {'Machinegun'}	# gunmoves.zs has no Pivot row 27 and no fire rows for the Machinegun: nothing to move (reported)

_rd = pg.rd
def rd_norm(p):
    """MODELDEF blocks of the M32 carry the z in Offset (Offset 0.0 -30.0 -8.0, no ZOffset). Same placement written as
    Offset x y 0.0 + ZOffset z (the form port_gun.py edits); only blocks drawing the current gun's meshes."""
    tx = _rd(p)
    if not p.startswith('MODELDEF') or not getattr(pg, 'CUR', None): return tx
    def fix(m):
        b = m.group(0)
        if not any('"%s"' % n in b for n in pg.CUR['names'] + pg.CUR.get('names_extra', [])) or re.search(r'(?m)^[ \t]*ZOffset', b): return b
        return re.sub(r'(?m)^([ \t]*)Offset[ \t]+([-\d.]+)[ \t]+([-\d.]+)[ \t]+([-\d.]+)[ \t]*\n', lambda o: '%sOffset %s %s 0.0\n%sZOffset %s\n' % (o.group(1), o.group(2), o.group(3), o.group(1), o.group(4)), b, count=1)
    return pg.BLK.sub(fix, tx)
pg.rd = rd_norm

def rsb_cases(G, p, R, t, tag):
    """rsb_guns.zs rows written as switch cases: Hinge (point) moves, Axis turns, Offset = the new placement. Hand-frame rows
    (Hand0-2, HandT/Base/Tip) are kept (b1-b3 rule); Casing (0,0,0 = none) kept; PushRef (a gun-frame direction) turns; PushZ/PushR
    (along / around the hinge axis, from the hinge) are rigid-invariant."""
    tx = pg.rd('zscript/rsr/rsb_guns.zs'); c = G['rsbcase']
    v, s = pg.getcase(tx, 'Hinge', c); tx = pg.setcase(tx, 'Hinge', c, s, '(%.4f, %.4f, %.4f)' % tuple(R @ v + t), tag)
    v, s = pg.getcase(tx, 'Axis', c); tx = pg.setcase(tx, 'Axis', c, s, '(%.4f, %.4f, %.4f)' % tuple(R @ v), tag)
    v, s = pg.getcase(tx, 'Offset', c); assert np.abs(v - np.array(G['off'])).max() < 1e-3, ('rsb Offset not base', v)
    tx = pg.setcase(tx, 'Offset', c, s, '(%.4f, %.4f, %.4f)' % tuple(p[:3]), tag)
    v, s = pg.getcase(tx, 'PushRef', c)
    if v is not None: tx = pg.setcase(tx, 'PushRef', c, s, '(%.4f, %.4f, %.4f)' % tuple(R @ v), tag)
    # r9 (batch 4's rule, pg.rsb): the chamber bores turn with the gun; the round in the off hand is drawn with Offset(i) through the
    # moved RSQ_Hands block, so its hold rows are re-expressed (Hand0-2 = g R^T, HandT = HandT - g R^T t): the hold is unchanged
    i0 = tx.index(' Bore(int i, int k)'); i1 = tx.index('\n\t}', i0); seg = tx[i0:i1]
    for k in range(8):
        m = re.search(r'\t\tcase %d:\treturn \(([^)]*)\);' % (c * 8 + k), seg)
        if not m: continue
        v = np.array([float(x) for x in m.group(1).split(',')]); nv = R @ v
        seg = seg.replace(m.group(0), '\t\tcase %d:\treturn (%.4f, %.4f, %.4f);\t// %s: turned with the gun (was %s)' % ((c * 8 + k,) + tuple(pg.z0(x, 5e-5) for x in nv) + (tag, m.group(1))), 1)
        pg.note('reload rsb Bore gun %d chamber %d' % (c, k), m.group(1), '->', '%.4f, %.4f, %.4f' % tuple(nv))
    tx = tx[:i0] + seg + tx[i1:]
    g = np.array([pg.getcase(tx, 'Hand%d' % r, c)[0] for r in range(3)]); g1 = g @ R.T; hT = pg.getcase(tx, 'HandT', c)[0]; hT1 = hT - g1 @ t
    for fn, nv in (('Hand0', g1[0]), ('Hand1', g1[1]), ('Hand2', g1[2]), ('HandT', hT1)):
        v, s_ = pg.getcase(tx, fn, c); tx = pg.setcase(tx, fn, c, s_, '(%.4f, %.4f, %.4f)' % tuple(pg.z0(x, 5e-5) for x in nv), tag)
    pg.wr('zscript/rsr/rsb_guns.zs', tx)	# PushZ0/1, PushR0/1, PushEdge: measured along / around the hinge axis from the hinge: unchanged by a rigid move

def m203mg(G, p, R, t, tag):
    """r10: the Machinegun's under-barrel launcher (RSM gun 2). Its tables (rsr_m203_geo.zs AxisL/U, TubeRear/Front, ...) stay in the
    gun's ORIGINAL controller frame, as the rifle's (gun 1, batch 4): ToGun / DirToGun / FromGun get a gun-2 branch with this move's
    R, t, FwdHook(2) turns with the gun, and the 40 mm round drawn on the gun (MODELDEF.rsm RSR_GunParts RQ3P B, m203_round.md3 at its
    own seat offset) is re-placed so it is drawn moved by the same R, t (the tube RQ3P A and the no-tube twins QU0x draw Machinegun.md3:
    moved by modeldef())."""
    tx = pg.rd('zscript/rsr/rsr_m203_geo.zs'); fw = R @ np.array([1.0, 0, 0]); fh = [fw[1], fw[2], -fw[0]]
    m = re.search(r'clearscope static Vector3 FwdHook\(int gun\) \{ return gun == 2 \? \(0\.0000, 0\.0000, -1\.0000\) : ', tx); assert m, 'FwdHook gun 2'
    tx = tx[:m.start()] + 'clearscope static Vector3 FwdHook(int gun) { return gun == 2 ? (%.4f, %.4f, %.4f) : ' % tuple(fh) + tx[m.end():]
    Ri = R.T; ti = -R.T @ t
    aff = lambda M, b, s: '(' + ', '.join(' + '.join('%.6f * %s.%s' % (M[r_, c], s, 'xyz'[c]) for c in range(3)) + ('' if b is None else ' + %.6f' % b[r_]) for r_ in range(3)) + ')'
    for fn, M, b, v in (('ToGun', Ri, ti, 'p'), ('DirToGun', Ri, None, 'v'), ('FromGun', R, t, 'p')):
        a = '\tclearscope static Vector3 %s(int gun, Vector3 %s)\n\t{\n\t\tif (gun != 1) return %s;' % (fn, v, v)
        tx = pg.sub1(tx, a, '\tclearscope static Vector3 %s(int gun, Vector3 %s)\n\t{\n\t\tif (gun == 2) return %s;\t// %s: the Machinegun (gun 2) moved to the FBX hand\n\t\tif (gun != 1) return %s;' % (fn, v, aff(M, b, v), tag, v), fn)
    tx = tx.replace('\tclearscope static Vector3 RoundInHand()', '\t// %s (lane B): the Machinegun (gun 2) is drawn moved to the FBX hand (MODELDEF Offset %.3f %.3f, ZOffset %.3f, Angle/Pitch/Roll %.3f/%.3f/%.3f);\n\t// its numbers above stay in its ORIGINAL frame, FwdHook(2) is its forward axis after the move (was 0 0 -1).\n\tclearscope static Vector3 RoundInHand()' % ((tag,) + tuple(p)), 1)
    pg.wr('zscript/rsr/rsr_m203_geo.zs', tx); pg.note('M203 gun 2 FwdHook', np.round(fh, 4), '+ ToGun / DirToGun / FromGun gun-2 branch (R, t of this move)')
    # the round seated on the gun
    tx = pg.rd('MODELDEF.rsm'); hit = [mm for mm in pg.BLK.finditer(tx) if mm.group(1) == 'RSR_GunParts' and re.search(r'FrameIndex RQ3P B ', mm.group(0)) and 'm203_round.md3' in mm.group(0)]
    assert len(hit) == 1, 'RQ3P B round block'; b = hit[0].group(0)
    o = pg.num(r'(?m)^\s*Offset\s+([-\d. ]+)', b); z = pg.num(r'(?m)^\s*ZOffset\s+([-\d.]+)', b); assert not re.search(r'(Angle|Pitch|Roll)Offset', b)
    off0 = [o[0], o[1], z[0]]; X = pg.raw(os.path.join(pg.SRC, 'models/bd/Rifle/m203_round.md3'), 0); V0 = pg.chain([-1, 1, 1], off0, (0, 0, 0))(X); tgt = V0 @ R.T + t
    from scipy.optimize import least_squares
    f = lambda q: (pg.chain([-1, 1, 1], q[:3], q[3:])(X) - tgt).ravel(); s_ = least_squares(f, np.r_[off0, p[3:]]); q = s_.x; res = float(np.abs(f(q)).max()); assert res < 0.01, ('round re-place', res)
    nb = re.sub(r'(?m)^([ \t]*)Offset[^\n]*\n[ \t]*ZOffset[^\n]*\n', lambda mm: '%sOffset %.3f %.3f 0.0\n%sZOffset %.3f\n%sAngleOffset %.3f\n%sPitchOffset %.3f\n%sRollOffset %.3f\t// %s (lane B): the Machinegun\'s seated 40 mm round, moved with the gun (was Offset %s %s, ZOffset %s)\n' % (
        mm.group(1), q[0], q[1], mm.group(1), q[2], mm.group(1), q[3], mm.group(1), q[4], mm.group(1), q[5], tag, o[0], o[1], z[0]), b, count=1)
    assert nb != b; pg.wr('MODELDEF.rsm', tx.replace(b, nb, 1)); pg.note('MODELDEF.rsm RSR_GunParts RQ3P B (m203_round) re-placed', np.round(off0, 3), '->', np.round(q, 3), 'residual %.4f cm' % res)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cls'); ap.add_argument('fit'); ap.add_argument('--src'); ap.add_argument('--tag', default='heavies'); ap.add_argument('--dry', action='store_true')
    pg.ARGS = ARGS = ap.parse_args()
    if ARGS.src: pg.SRC = os.path.abspath(ARGS.src)
    G = dict(pg.GUNS[ARGS.cls], cls=ARGS.cls); G['md3'] = os.path.join(pg.SRC, G['md3']); pg.CUR = G
    F = json.load(open(ARGS.fit)); fitdir = os.path.dirname(os.path.abspath(ARGS.fit))
    if 'place' in F: p = np.array(F['place'], float); res = None
    else: p, res, R0, t0 = pg.place(G, F['shift'])
    R, t = pg.rigid_move(G, p)
    print('%s: MODELDEF Offset %.3f %.3f  ZOffset %.3f  Angle/Pitch/Roll %.3f/%.3f/%.3f' % ((ARGS.cls,) + tuple(p)), '' if res is None else '(chain residual %.4f cm)' % res)
    pg.gun_blocks_cache = {ARGS.cls: pg.gun_blocks(G)}
    pg.modeldef(G, p, ARGS.tag)
    if G.get('row') is not None and G.get('bdblock') and ARGS.cls not in NOGUNMOVES: pg.gunmoves(G, p, ARGS.tag)
    else: pg.note('gunmoves: no Pivot / fire rows for %s in gunmoves.zs: nothing moved' % ARGS.cls)
    if G.get('rsr'): pg.rsr(G, p, R, t, ARGS.tag)
    if G.get('rsbcase'): rsb_cases(G, p, R, t, ARGS.tag)
    if G.get('casing'): pg.casing(G, R, t, ARGS.tag)
    if not F.get('no_muzzle'): pg.muzzle(G, R, t, ARGS.tag)
    if G.get('scope'): pg.scope(G, R, t, ARGS.tag)
    if G.get('m203mg'): m203mg(G, p, R, t, ARGS.tag)
    if F.get('hand'):
        H = F['hand']; H['sprite'], H['label'] = HANDSPR[ARGS.cls]
        if H.get('squeeze', 'false') == 'false': H['squeeze'], H['squeeze_note'] = squeeze_expr(G)
        pg.note('hand squeeze:', H['squeeze_note'])
    if F.get('hand'): pg.hand(G, F['hand'], R, t, ARGS.tag, fitdir)
    pg.flush()
    print('moved %d items%s' % (len(pg.MOVED), ' (dry run: nothing written)' if ARGS.dry else ''))
    if not ARGS.dry: json.dump(dict(cls=ARGS.cls, place=list(p), R=R.tolist(), t=t.tolist(), moved=pg.MOVED), open(os.path.join(fitdir, 'ported_%s.json' % ARGS.cls), 'w'), indent=1)
