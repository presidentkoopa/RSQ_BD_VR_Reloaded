"""objects.py: what each Ermac reload hold holds, as the engine draws it on the OFF controller (drawn cm F / L / U, the frame ohfit
fits in), parsed from the pack (never typed in):
  rsr(i)   RSR magazine guns (rsr_guns.bd.zs Index 1-18): the RSQ_Hands MODELDEF.rsr block of SprPart(i) frame A (the HANDMAG layer,
           layer 2201), its visible surfaces (SurfaceSkin not rsr_clear.png), placed by vreload Place(HANDMAG): hook HandHook(i),
           hook rotation RSR.HandRot(i) (row 13 only). Ermac hold: HoldState(i) (RsrHold = ammo_hand 3, RsrHoldPod = ammo_hand 6).
Returns dict(V, F, ermac=(md3, frame), name, rows) ; rows = the table rows that read the object's place (moved together if it moves)."""
import os, re, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
import ohfit as O, scene, hudrender, gunview
def rd(p): return open(os.path.join(O.SRC, p), encoding='latin1').read()
def vec_rows(txt, fn):
    i0 = txt.index('static Vector3 %s(int i)' % fn); i1 = txt.index('\n\t}', i0)
    return {int(a): np.array([float(x) for x in b.split(',')]) for a, b in re.findall(r'case (\d+):\s*return \(([^)]*)\)', txt[i0:i1])}
def str_rows(txt, fn, typ='Name'):
    i0 = txt.index('static %s %s(int i)' % (typ, fn)); i1 = txt.index('\n\t}', i0)
    return {int(a): b for a, b in re.findall(r"case (\d+):\s*return ['\"]([^'\"]*)['\"]", txt[i0:i1])}
def blocks(fname, cls):
    out = []
    for m in re.finditer(r'Model\s+%s\s*\{(.*?)\n\}' % cls, rd(fname), re.S):
        b = m.group(1); g = lambda k: [float(x) for x in re.search(k + r'\s+([-\d\. ]+)', b).group(1).split()] if re.search(k + r'\s+([-\d\. ]+)', b) else None
        off = g(r'\n\s*Offset') or [0, 0, 0]; z = g('ZOffset')
        if z: off = [off[0], off[1], z[0]]
        out.append(dict(path=re.search(r'Path\s+"([^"]+)"', b).group(1), model=re.search(r'Model\s+0\s+"([^"]+)"', b).group(1),
                        skins={int(a): s for a, s in re.findall(r'SurfaceSkin\s+0\s+(\d+)\s+"([^"]+)"', b)}, scale=g('Scale'), off=off,
                        ao=[(g(k) or [0])[0] for k in ('AngleOffset', 'PitchOffset', 'RollOffset')],
                        frames={(s, l): int(f) for s, l, f in re.findall(r'FrameIndex\s+(\S+)\s+(\S)\s+0\s+(\d+)', b)}, text=b))
    return out
def find(fname, cls, spr, letter='A'):
    b = [x for x in blocks(fname, cls) if (spr, letter) in x['frames']]; assert len(b) == 1, (fname, cls, spr, letter, len(b)); return b[0]
def mesh(b, letter_spr, hook=(0, 0, 0), rot=(0, 0, 0)):
    fr = b['frames'][letter_spr]; path = os.path.join(O.SRC, b['path'], b['model']); S = scene.md3_full(path); V = []; F = []; n = 0; used = []
	# a surface is drawn unless its SurfaceSkin is the clear texture
    for k, s in enumerate(S):
        if 'rsr_clear' in b['skins'].get(k, ''): continue
        assert not any(b['ao']), 'angle offsets: use port_gun.chain'
        v = gunview.to_fl(hudrender.to_local(s['xyz'][min(fr, len(s['xyz']) - 1)], dict(scale=b['scale'], off=b['off'], hook=list(hook), rot=list(rot))))
        V.append(v); F.append(s['tris'] + n); n += len(v); used.append(k)
    return np.concatenate(V), np.concatenate(F), used
RSR_CLS = {1: 'Rifle', 2: 'BrutalPistol', 3: 'BrutalSMG', 4: 'MP40', 5: 'AssaultShotgun', 6: 'RailGun', 7: 'Plasma_Gun', 8: 'Sniper', 9: 'Rocket_Launcher',
           10: 'MG42', 11: 'Flamethrower2', 12: 'IncendiaryLauncher', 13: 'Unmaker', 14: 'Devastator', 15: 'NukeLauncher', 16: 'HellishMissileLauncher',
           17: 'Minigun', 18: 'Machinegun'}
POD = (13, 15, 16)	# vreload HoldState before the FBX holds (lb-r8 / 1.99x item 10): RsrHoldPod = ammo_hand 6 for these, RsrHold = ammo_hand 3 for the rest
def hold_rsr(i): return ('ammo_hand.md3', 6) if i in POD else ('ammo_hand.md3', 3)
def handrot(i):
    t = rd('zscript/rsr/vreload.zs'); m = re.search(r'static Vector3 HandRot\(int i\)\s*\{\s*return i == (\d+) \? \(([^)]*)\)', t)
    return np.array([float(x) for x in m.group(2).split(',')]) if m and int(m.group(1)) == i else np.zeros(3)
def rsr(i):
    t = rd('zscript/rsr/rsr_guns.bd.zs'); spr = str_rows(t, 'SprPart')[i]; hh = vec_rows(t, 'HandHook')[i]; top = vec_rows(t, 'TopInHand')[i]
    b = find('MODELDEF.rsr', 'RSQ_Hands', spr); V, F, used = mesh(b, (spr, 'A'), hh, handrot(i))
    return dict(name='rsr%02d_%s' % (i, RSR_CLS[i]), V=V, F=F, ermac=hold_rsr(i), surfaces=used, block=dict(path=b['path'], model=b['model'], scale=b['scale'], off=b['off']),
                rows=dict(HandHook=hh.tolist(), TopInHand=top.tolist(), HandRot=handrot(i).tolist()), top_in_hand=top)

# RSR-BREAK (rsb_guns.zs, rsr_break.zs Place(HANDROUND)): the round (or speedloader) in the off hand =
#   G (K P + RestT(i, 0)) + HandT(i),  G = rows Hand0-2(i), K = rows Rest0-2(i, 0), P = the part block drawn at hook 0 (its own Scale /
#   Offset / ZOffset / Angle-Pitch-RollOffset: port_gun.chain), frame 7 ('H', CARRY) of the RSQ_Hands block of SprPart(i).
# The pair (SSG, nch 2): the second shell rides on chamber 1's rest (HANDROUND2). Rows 4-6 (VR_SuperShotgun, VR_Revolver, VR_Revolver2)
# have no class in the pack (never reached).
RSB_CLS = {1: 'SSG', 2: 'GrenadeLauncher', 3: 'Revolver', 7: 'Revolver (a round at a time)', 8: 'Revolver2', 9: 'Revolver2 (a round at a time)',
           10: 'BrutalRevolver', 11: 'BrutalRevolver (a round at a time)'}
def _rows_k(txt, fn):
    i0 = txt.index('static Vector3 %s(int i' % fn); i1 = txt.index('\n\t}', i0)
    return {int(a): np.array([float(x) for x in b.split(',')]) for a, b in re.findall(r'case (\d+):\s*return \(([^)]*)\)', txt[i0:i1])}
RSB_HOLD = {1: 'RsbShell', 2: 'RsrHold', 3: 'RsbShell', 4: 'RsbShell', 5: 'RsbCell', 6: 'RsbCell', 7: 'RsbShell', 8: 'RsbShell', 9: 'RsbShell',
            10: 'RsbCell', 11: 'RsbShell'}	# rsb_guns HoldState before the FBX holds (the Ermac hold each part was seated in)
def rsb(i, pair=None):
    sys_path_port()
    import port_gun as PG
    t = rd('zscript/rsr/rsb_guns.zs'); spr = str_rows(t, 'SprPart')[i]; hold = RSB_HOLD[i]
    G = np.array([_rows_k(t, 'Hand%d' % k)[i] for k in range(3)]); HT = _rows_k(t, 'HandT')[i]
    files = [f for f in os.listdir(O.SRC) if f.startswith('MODELDEF')]
    bl = [(f, b) for f in files for b in blocks(f, 'RSQ_Hands') if (spr, 'H') in b['frames']]
    assert len(bl) == 1, (spr, [x[0] for x in bl]); f, b = bl[0]
    S = scene.md3_full(os.path.join(O.SRC, b['path'], b['model'])); fr = b['frames'][(spr, 'H')]
    ch = PG.chain(b['scale'], b['off'], b['ao']); V = []; F = []; n = 0; used = []
    nch = 2 if (pair if pair is not None else i == 1) else 1
    for k in range(nch):
        K = np.array([_rows_k(t, 'Rest%d' % a)[i * 8 + k] for a in range(3)]); RT = _rows_k(t, 'RestT')[i * 8 + k]
        for si, s in enumerate(S):
            if 'rsr_clear' in b['skins'].get(si, ''): continue
            P = ch(s['xyz'][min(fr, len(s['xyz']) - 1)]); v = (P @ K.T + RT) @ G.T + HT
            V.append(v); F.append(s['tris'] + n); n += len(v); used.append(si)
    base = _rows_k(t, 'HandBase')[i]; tip = _rows_k(t, 'HandTip')[i]
    ermac = {'RsbShell': ('ammo_hand.md3', 1), 'RsbCell': ('ammo_hand.md3', 5), 'RsrHold': ('ammo_hand.md3', 3)}[hold]
    return dict(name='rsb%02d_%s' % (i, RSB_CLS[i].split(' (')[0] + ('_round' if 'a round' in RSB_CLS[i] else '')), V=np.concatenate(V), F=np.concatenate(F), ermac=ermac, hold=hold,
                surfaces=used, block=dict(file=f, path=b['path'], model=b['model']), rows=dict(HandT=HT.tolist(), HandBase=base.tolist(), HandTip=tip.tolist()), base=base, tip=tip)
def sys_path_port():
    import sys
    p = os.path.join(HERE, '..', 'port')
    if p not in sys.path: sys.path.insert(0, p)

# RSR-PUMP (rsr_pump.zs Place(HANDSHELL), layer 2210, frame 2 'C' of SprPart(i)): hook HandHook(i), hook rotation HandRot(i).
# Only Shot_Gun (row 1) is in the pack (VR_Shotgun, row 2, has no class). Ermac hold: RspShell = ammo_hand 1.
def pump(i=1):
    t = rd('zscript/rsr/rsr_pump_guns.zs'); spr = str_rows(t, 'SprPart')[i]; hh = vec_rows(t, 'HandHook')[i]; hr = vec_rows(t, 'HandRot')[i]
    b = find('MODELDEF.rsrpump', 'RSQ_Hands', spr, 'C'); V, F, used = mesh(b, (spr, 'C'), hh, hr)
    return dict(name='rsp%02d_Shot_Gun' % i, V=V, F=F, ermac=('ammo_hand.md3', 1), hold='RspShell', surfaces=used, block=dict(path=b['path'], model=b['model']),
                rows=dict(HandHook=hh.tolist(), HandRot=hr.tolist()))
# RSR-M203 (rsr_m203.zs): RsmRound = ammo_hand 5 + m203_round_hand.md3 (model 1, frame 0) in ONE block (MODELDEF.rsm RQ2H A), drawn
# with the hand's own placement; RsmGrip (RQ2H B) = the same grip with the round on the gun: the same FBX frame serves both.
def m203():
    b = find('MODELDEF.rsm', 'RSQ_Hands', 'RQ2H', 'A'); S = scene.md3_full(os.path.join(O.SRC, b['path'], 'm203_round_hand.md3')); V = []; F = []; n = 0
    for s in S:
        v = gunview.to_fl(hudrender.to_local(s['xyz'][0], dict(scale=b['scale'], off=b['off']))); V.append(v); F.append(s['tris'] + n); n += len(v)
    return dict(name='rsm_M203_round', V=np.concatenate(V), F=np.concatenate(F), ermac=('ammo_hand.md3', 5), hold='RsmRound / RsmGrip', surfaces=[0],
                block=dict(path=b['path'], model='m203_round_hand.md3'), rows={})
