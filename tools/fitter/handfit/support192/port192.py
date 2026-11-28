"""port192.py: the support hands fitted from the 1.92 holds (fit192.py) into the pack.
  port192.py port <Class>[,<Class>...] [--run DIR] [--tag TEXT]   bake + write, for the listed guns (plus every gun already ported this way)
  port192.py check                                                 re-bake every poses/<Class>.json `support` (form support192) and compare
                                                                   to the shipped md3 frame (max md3 units)
What `port` writes (src/):
  - models/rsq/fbx/fbx_s192_L.md3: one frame per gun, baked IN PLACE (the frame's wrist where the solved hand is: hook 0, as the gun
    hands), lane_c bake.bake (side L, the FBX's left rig, same UV split as every FBX md3). Frame letter per gun = ORDER below (fixed).
  - MODELDEF.rsq: the RSQ_GunSide + RSQ_Hands blocks for it (sprite RQWS; free in the pack, brutal22test6 and BD_VoxelPack, checked
    2026-10-27), between the `support192` markers (regenerated each run).
  - zscript/rsq/hands.zs: one state label per gun (FbxWrap<Class>: RQWS <letter>), between the markers; the gun row's support label
    line (`if (i == row) spl = ...`) now selects it. Rifle: the purist rifle takes the same hand (owner: PuristRifle copies Rifle):
    its Ermac handguard label and hook override are removed.
  - zscript/rsq/handtable.zs: SupportHook / SupportRot of the row = the bake's row (hook 0 when baked in place). SupportPoint unchanged.
  - tools/handfit/poses/<Class>.json: `support` = the pose as data (form support192: the FBX pose vector p, the 1.92 seed carry
    Rseed / tseed, the md3 / frame / label, the measurements of the fit and the 1.92 seed)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, re, json, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import s192
from s192 import PG
import bake, scene, handmodel, calib
sys.path.insert(0, os.path.join(HERE, '..', 'port')); import melee_r12	# BrutalAxe (row 24) in port_gun.GUNS: its support is fitted by axe192.py
ORDER = ['SSG', 'Shot_Gun', 'AssaultShotgun', 'Rifle', 'Devastator', 'IncendiaryLauncher', 'GrenadeLauncher', 'Rocket_Launcher', 'Plasma_Gun',
         'RailGun', 'Sniper', 'MG42', 'Machinegun', 'NukeLauncher', 'BFG10k', 'BIG_FUCKING_GUN', 'Unmaker', 'HellishMissileLauncher', 'BrutalAxe']
VARIANT = {}	# owner rule (report item 23): variants are never fitted; they copy the Brutal gun's rows (PuristRifle takes the Rifle's frame)
def GUN(g): return PG.GUNS[g]
SPR = 'RQWS'; MD3 = 'fbx_s192_L.md3'
POSES = os.path.join(_DP.POSES)
def letter(g): return chr(ord('A') + ORDER.index(g))
def label(g): return 'FbxWrap' + {'BIG_FUCKING_GUN': 'BFG9', 'IncendiaryLauncher': 'Inc', 'Rocket_Launcher': 'RL', 'GrenadeLauncher': 'GL', 'AssaultShotgun': 'AS', 'HellishMissileLauncher': 'HML'}.get(g, g.replace('_', ''))
def rd(p): return open(os.path.join(PG.SRC, p), encoding='latin1').read()
def wr(p, t): open(os.path.join(PG.SRC, p), 'w', encoding='latin1', newline='').write(t)
def X_of(S):
    Rs = np.array(S['Rseed']); ts = np.array(S['tseed']); return calib.place(handmodel.FbxHand('L'), np.array(S['p'])) @ Rs.T + ts
def ported():
    out = []
    for g in ORDER:
        p = os.path.join(POSES, '%s.json' % g)
        if os.path.exists(p) and isinstance(json.load(open(p)).get('support'), dict) and json.load(open(p))['support'].get('form') == 'support192': out.append(g)
    return out
def block(cls, guns):
    fi = ''.join('\tFrameIndex %s %s 0 %d\t// %s\n' % (SPR, letter(g), k, g) for k, g in enumerate(guns))
    return 'Model %s\n{\n\tPath "models/rsq/fbx"\n\tModel 0 "%s"\n\tSkin 0 "fbx_hand.png"\n\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n%s}\n' % (cls, MD3, fi)
def mark(tx, begin, end, body, anchor_after):
    if begin in tx: i = tx.index(begin); j = tx.index(end, i) + len(end); return tx[:i] + begin + body + end + tx[j:]
    if anchor_after is None: return tx + ('' if tx.endswith('\n') else '\n') + begin + body + end
    k = tx.index(anchor_after) + len(anchor_after); return tx[:k] + begin + body + end + tx[k:]
def port(new, run, tag):
    import json as _j
    have = ported(); fits = {}
    for g in ORDER:
        f = os.path.join(run, 'fit192_%s.json' % g)
        if g in new: fits[g] = _j.load(open(f))
    guns = [g for g in ORDER if g in have or g in new]
	# 1. bake every gun's frame (the old ones from their pose data, the new ones from the fit)
    ents = []; data = {}
    for g in guns:
        if g in new:
            F = fits[g]; S = dict(p=F['p'], Rseed=F['Rseed'], tseed=F['tseed'])
        else:
            S = json.load(open(os.path.join(POSES, '%s.json' % g)))['support']
        X = X_of(S); data[g] = S; ents.append(dict(name=g[:15], side='L', X=X))
    H = handmodel.FbxHand('R'); Lc = json.load(open(os.path.join(s192.LANE, 'landmarks_fbx.json')))['R']['cuff']
    for e in ents: e['cuff_ref'] = e['X'][Lc]	# baked in place: hook 0
    tmp = os.path.join(run, 'fbx_s192.md3'); rows, paths, _ = bake.bake(ents, tmp)
    dst = os.path.join(PG.SRC, 'models/rsq/fbx', MD3); open(dst, 'wb').write(open(paths['L'], 'rb').read())
    for r in rows: assert r['bake_check_max_cm'] < 0.05, r
	# 2. MODELDEF.rsq
    tx = rd('MODELDEF.rsq'); body = '\n// support192 (%s): the FBX support hands fitted from the 1.92 holds (tools/handfit/support192), baked in place\n' % tag + block('RSQ_GunSide', guns) + block('RSQ_Hands', guns)
    tx = mark(tx, '// support192 BEGIN\n', '// support192 END\n', body, None)
    wr('MODELDEF.rsq', tx)
	# 3. hands.zs: labels + the row's support label
    tx = rd('zscript/rsq/hands.zs')
    labs = ''.join('\t%s: %s %s -1; Stop;\t// %s (row %d)\n' % (label(g), SPR, letter(g), g, GUN(g)['row']) for g in guns)
    tx = mark(tx, '\t// support192 BEGIN: the FBX support hands fitted from the 1.92 holds (tools/handfit/support192)\n', '\t// support192 END\n', labs, '\tFbxSupF: RQFS B -1; Stop;\n')
    for g in new:
        row = GUN(g)['row']
        pat = r'\t\tif \(i == %d( && !\(p\.ReadyWeapon is \'PuristRifle\'\))?\)\n\t\t\tspl = "[A-Za-z0-9]+";[^\n]*\n' % row
        m = re.search(pat, tx)
        if not m:	# a row with no FBX support line yet (r12 guns: Ermac RQSP by RSQ_HandTable.Support): one is added before the SUPPORT layer call
            k = tx.index('\t\tinvoker.SetLayer(p, RSQ_Layers.SUPPORT'); m = re.match('', tx[k:]); tx = tx[:k] + '\t\tif (i == %d)\n\t\t\tspl = "x";\n' % row + tx[k:]
            m = re.search(pat, tx); assert m, 'support label line of row %d' % row
        tx = tx[:m.start()] + '\t\tif (i == %d)\n\t\t\tspl = "%s";\t// %s: %s, the FBX support hand fitted from the 1.92 hold (handtable SupportHook / SupportRot row %d = 0: baked in place)\n' % (row, label(g), tag, g, row) + tx[m.end():]
        if g == 'Rifle':	# owner: PuristRifle copies Rifle
            tx, n1 = re.subn(r'\t\tif \(i == 18 && p\.ReadyWeapon is \'PuristRifle\'\)\n\t\t\tsp = "B";[^\n]*\n\t\telse if', '\t\tif', tx)
            tx, n2 = re.subn(r'\t\tif \(!gunHand && i == 18 && o\.ReadyWeapon is \'PuristRifle\'\)\n\t\t\{\n[^}]*\}\n', '', tx)
            tx = tx.replace("if (!gunHand && i == 18 && !(o.ReadyWeapon is 'PuristRifle') && RSK_M203Handler.TriggerGrip(Owner))", "if (!gunHand && i == 18 && RSK_M203Handler.TriggerGrip(Owner))")
            assert n1 == 1 and n2 == 1, ('purist rifle edits', n1, n2)
    wr('zscript/rsq/hands.zs', tx)
	# 4. handtable rows
    tx = rd('zscript/rsq/handtable.zs')
    for g, r in zip(guns, rows):
        if g in new and g not in VARIANT: tx = PG.setrow(tx, 'SupportHook', r['hook'], GUN(g)['row']); tx = PG.setrow(tx, 'SupportRot', r['rot'], GUN(g)['row'])
        if g in VARIANT: assert max(abs(v) for v in r['hook'] + r['rot']) < 1e-3, 'a variant shares the row: its frame must be baked in place (hook 0)'
    wr('zscript/rsq/handtable.zs', tx)
	# 5. poses
    for g, r in zip(guns, rows):
        if g not in new:	# an earlier gun keeps its pose; only its frame number moves when a gun earlier in ORDER is added
            pp = os.path.join(POSES, '%s.json' % g); J = json.load(open(pp))
            if J['support'].get('frame') != guns.index(g): J['support']['frame'] = guns.index(g); json.dump(J, open(pp, 'w'), indent=1)
            continue
        F = fits[g]; pp = os.path.join(POSES, '%s.json' % g)
        J = json.load(open(pp)) if os.path.exists(pp) else dict(cls=g, note='variant of %s: the gun hand, gun move and placement are %s\'s (poses/%s.json); only the support is its own' % (VARIANT[g], VARIANT[g], VARIANT[g]))
        J['support'] = dict(form='support192', md3='models/rsq/fbx/' + MD3, sprite=SPR, frame=guns.index(g), letter=letter(g), label=label(g),
                            handtable_row=GUN(g)['row'], sup_hook=r['hook'], sup_rot=r['rot'], bake_check_max_cm=r['bake_check_max_cm'],
                            p=F['p'], Rseed=F['Rseed'], tseed=F['tseed'], seed_1_92=dict(hand2_frame=F['m']['sframe'], seed_refit=F['m'].get('seed_refit'), measured=F['seed']),
                            measured=F['m'], names=F['names'], weights=F['w'],
                            how='tools/handfit/support192/fit192.py %s (seed = 1.92 Ermac hand2 frame %d on the gun, FBX left hand re-fitted to it, then closed onto the gun), port192.py port' % (g, F['m']['sframe']))
        json.dump(J, open(pp, 'w'), indent=1)
    return guns, rows
def check():
    guns = ported(); fr = PG.md3_frames(os.path.join(PG.SRC, 'models/rsq/fbx', MD3)); bad = 0
    import tempfile
    ents = [dict(name=g[:15], side='L', X=X_of(json.load(open(os.path.join(POSES, '%s.json' % g)))['support'])) for g in guns]
    Lc = json.load(open(os.path.join(s192.LANE, 'landmarks_fbx.json')))['R']['cuff']
    for e in ents: e['cuff_ref'] = e['X'][Lc]
    d = tempfile.mkdtemp(); rows, paths, _ = bake.bake(ents, os.path.join(d, 'chk.md3')); new = PG.md3_frames(paths['L'])
    for k, g in enumerate(guns):
        S = json.load(open(os.path.join(POSES, '%s.json' % g)))['support']
        dv = max(float(np.abs(a[S['frame']] - b[k]).max()) for a, b in zip(fr, new)); bad += dv > 0.02
        print('%-18s frame %s (%d): max %.4f md3 units vs shipped' % (g, S['letter'], S['frame'], dv))
    print('support192 check:', 'OK' if not bad else '%d DIFFER' % bad); return bad
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('guns', nargs='?'); ap.add_argument('--run', default=_DP.WORK + '/runs/sup192run'); ap.add_argument('--tag', default='support192')
    a = ap.parse_args()
    if a.cmd == 'port':
        guns, rows = port(a.guns.split(','), a.run, a.tag); print('ported', guns); [print(r) for r in rows]
    else: sys.exit(1 if check() else 0)
