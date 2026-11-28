"""wire_holds.py <fitdir>: the reload holds' FBX frames into the pack.
  - poses/offhand/holds.json (each frame's z, the fit's measurements, the object, the Ermac hold it replaces), and the bake
    src/models/rsq/fbx/fbx_oh_hold_R.md3 (one frame per held object, side R in place: the engine mirrors the off controller);
  - MODELDEF.rsq: RSQ_Hands RQHF <letter> -> that frame; hands.zs RSQ_Hands labels OhHold<letter>;
  - vreload.zs RSR_ReloadHandler.HoldState(i) and rsb_guns.zs RSB_Guns.HoldState(i): each gun's own hold (OhHold<letter>);
  - every Ermac hold block left (RQHN I / J / L / M, RQUN A, RQ2H A / B) repointed to the FBX frame of its object, so no path draws
    Ermac's glove: RQUN A = the pump shell, RQ2H A / B = the M203 round (model 1, the round, unchanged), RQHN L = the Moonlight loader,
    RQHN I / J / M = the Rifle magazine / SSG shell / Nuker block holds (no longer reached by a shipped gun: HoldState names its own).
Objects keep their place (no fit moved one: asserted), so no HandHook / TopInHand / Hand rows change."""
import os, sys, re, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ohfit as O, ohbake
FD = os.path.abspath(sys.argv[1])
ORDER = [('rsr%d' % i, chr(64 + i)) for i in range(1, 19)] + [('rsb1', 'S'), ('rsb2', 'T'), ('rsb3', 'U'), ('rsb10', 'V'), ('rsb11', 'W'), ('rsp1', 'X'), ('rsm', 'Y')]
fits = {}
for f in os.listdir(FD):
    if f.endswith('.json'):
        J = json.load(open(os.path.join(FD, f))); fits[J['job']] = J
missing = [j for j, _ in ORDER if j not in fits]; assert not missing, 'no fit for %s' % missing
moved = {j: np.array(fits[j]['y']) for j, _ in ORDER if np.linalg.norm(fits[j]['y']) > 1e-9}
assert all(j.startswith('rsr') or j.startswith('rsb') for j in moved), 'only magazine / break-open rows can move their part here: %s' % list(moved)
frames = []
for k, (j, L) in enumerate(ORDER):
    J = fits[j]; frames.append(dict(name=J['name'][:15], z=J['z'], job=j, object=J['name'], letter=L, md3_frame=k, ermac='%s frame %d' % tuple(J['ermac']),
                                     m=J['m'], ermac_m=J['ermac_m'], seed=J['seed'] | dict(z=None), W=J['W']))
P = dict(md3='models/rsq/fbx/fbx_oh_hold_R.md3', logscale=O.LOGS, fbx=os.path.basename(O.handmodel.FBX), sprite='RQHF',
         how='tools/handfit/offhand/hold_fit.py (ohfit.seed on the Ermac hold, ohfit.grip round the object as drawn: objects.py), wire_holds.py', frames=frames)
rows = ohbake.bake(P, os.path.join(O.SRC, P['md3'])); P['bake_check_max_cm'] = max(r['bake_check_max_cm'] for r in rows)
for f in P['frames']: f['seed'].pop('z', None)
json.dump(P, open(os.path.join(ohbake.POSES, 'holds.json'), 'w'), indent=1)
S = O.SRC
def rd(p): return open(os.path.join(S, p), encoding='latin1').read()
def wr(p, t): open(os.path.join(S, p), 'w', encoding='latin1').write(t)
def sub1(t, a, b):
    assert t.count(a) == 1, (a[:80], t.count(a)); return t.replace(a, b)
letter = dict(ORDER)
# MODELDEF.rsq: the hold frames
fi = ''.join('\tFrameIndex RQHF %s 0 %d\t// %s (was Ermac %s)\n' % (f['letter'], f['md3_frame'], f['object'], f['ermac']) for f in frames)
blk = ('\n// off-hand FBX lane (owner 2026-10-28: every off-hand reload hold becomes FBX for 2.0): the FBX hand round each held object as the\n'
       '// engine draws it (tools/handfit/offhand/hold_fit.py from the Ermac hold, wire_holds.py; poses/offhand/holds.json). One frame per object,\n'
       '// baked in place (hook 0); the objects keep their place, so no reload row moved.\nModel RSQ_Hands\n{\n\tPath "models/rsq/fbx"\n\tModel 0 "fbx_oh_hold_R.md3"\n'
       '\tSkin 0 "fbx_hand.png"\n\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n' + fi + '}\n')
t = rd('MODELDEF.rsq')
if 'fbx_oh_hold_R.md3' not in t: wr('MODELDEF.rsq', t.rstrip('\n') + '\n' + blk)
# the Ermac blocks repointed
def repoint(fname, old, new):
    t = rd(fname)
    if old in t or new not in t: wr(fname, sub1(t, old, new))	# idempotent: a second run finds the block already repointed
H = lambda: '\tPath "models/rsq/fbx"\n\tModel 0 "fbx_oh_hold_R.md3"\n\tSkin 0 "fbx_hand.png"\n'
E = '\tPath "models/rsq"\n\tModel 0 "ammo_hand.md3"\n\tSkin 0 "hand.png"\n'
ix = {f['letter']: f['md3_frame'] for f in frames}
repoint('MODELDEF.rsr', E + '\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQHN I 0 3\n\tFrameIndex RQHN M 0 6\t// 1.99x: the pod hold (Nuker, Hellish)\n',
        H() + '\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQHN I 0 %d\t// off-hand FBX lane: was Ermac ammo_hand 3; = the FBX Rifle magazine hold (RQHF A). No shipped gun reaches it now (HoldState: OhHold<letter>)\n'
        '\tFrameIndex RQHN M 0 %d\t// was Ermac ammo_hand 6 (pod hold); = the FBX Nuker block hold (RQHF O)\n' % (ix['A'], ix['O']))
repoint('MODELDEF.rsb', E + '\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQHN J 0 1\n\tFrameIndex RQHN L 0 5\n',
        H() + '\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQHN J 0 %d\t// off-hand FBX lane: was Ermac ammo_hand 1; = the FBX SSG shell hold (RQHF S)\n'
        '\tFrameIndex RQHN L 0 %d\t// was Ermac ammo_hand 5; = the FBX Moonlight speedloader hold (RQHF V)\n' % (ix['S'], ix['V']))
repoint('MODELDEF.rsrpump', E + '\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQUN A 0 1\n',
        H() + '\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQUN A 0 %d\t// off-hand FBX lane: the FBX hand round the shell (RQHF X); was Ermac ammo_hand 1\n' % ix['X'])
t = rd('MODELDEF.rsm')
if 'fbx/fbx_oh_hold_R.md3' not in t:
  t = sub1(t, E + '\tModel 1 "m203_round_hand.md3"\n', '\tPath "models/rsq"\t// one Path for both models: the round stays in models/rsq\n\tModel 0 "fbx/fbx_oh_hold_R.md3"\n\tSkin 0 "fbx/fbx_hand.png"\n\tModel 1 "m203_round_hand.md3"\n')
  t = sub1(t, '\tFrameIndex RQ2H A 0 5\n', '\tFrameIndex RQ2H A 0 %d\t// off-hand FBX lane: the FBX hand round the 40 mm round (RQHF Y); was Ermac ammo_hand 5\n' % ix['Y'])
  t = sub1(t, E + '\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQ2H B 0 5\n', H() + '\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex RQ2H B 0 %d\t// the same FBX grip, the round on the gun\n' % ix['Y'])
wr('MODELDEF.rsm', t)
# hands.zs labels
t = rd('zscript/rsq/hands.zs')
if 'OhHoldA:' not in t:
    lab = '\t// off-hand FBX lane (2026-10-28): each reload hold\'s own FBX frame (MODELDEF.rsq RQHF; vreload / rsb HoldState)\n' + \
          ''.join('\tOhHold%s: RQHF %s -1; Stop;\t// %s\n' % (f['letter'], f['letter'], f['object']) for f in frames)
    t = sub1(t, '\tRsgRing: RQHR A -1; Stop;\n', '\tRsgRing: RQHR A -1; Stop;\n' + lab)
    for a, b in (('Ermac\'s one-shell hold (ammo_hand frame 1), round the gun\'s own shell', 'the FBX hand round the gun\'s own shell (RQUN A = RQHF X; was Ermac\'s ammo_hand 1)'),
                 ('real reload: Ermac\'s hold, round the gun\'s own magazine (rsr)', 'real reload: was Ermac\'s hold (ammo_hand 3); now RQHF A, no shipped gun uses it (vreload HoldState: OhHold<letter>)'),
                 ('1.99x: Ermac\'s BFG pod hold (ammo_hand 6), round the Nuker block / Hellish drum', 'was Ermac\'s BFG pod hold (ammo_hand 6); now RQHF O, unused (OhHold<letter>)'),
                 ('RSR-BREAK: Ermac\'s hold of one shell (ammo_hand 1), round the gun\'s own round', 'RSR-BREAK: was Ermac\'s one-shell hold; now RQHF S, unused (rsb HoldState: OhHold<letter>)'),
                 ('RSR-BREAK: Ermac\'s hold of a cell (ammo_hand 5), round the gun\'s own speedloader', 'RSR-BREAK: was Ermac\'s cell hold; now RQHF V, unused (OhHold<letter>)'),
                 ('1.30 RSR-M203: Ermac\'s open grip (ammo_hand 3) round a 40 mm round', '1.30 RSR-M203: the FBX hand round a 40 mm round (RQ2H A = RQHF Y + the round; was Ermac\'s ammo_hand 5)')):
        t = sub1(t, a, b)
    wr('zscript/rsq/hands.zs', t)
# a magazine part the fit moved (translation y, drawn cm): HandHook(i) by the hook change that moves the drawn part by y (the
# RenderHUDModel chain is affine in the hook: solved from the part's own block, objects.mesh), TopInHand(i) by y (both in the off-hand frame)
if moved:
    import objects as B
    t = rd('zscript/rsr/rsr_guns.bd.zs')
    for j, y in [(j, y) for j, y in moved.items() if j.startswith('rsr')]:
        i = int(j[3:]); o = B.rsr(i); spr = B.str_rows(t, 'SprPart')[i]; b = B.find('MODELDEF.rsr', 'RSQ_Hands', spr); hh = np.array(o['rows']['HandHook']); hr = B.handrot(i)
        f = lambda h: B.mesh(b, (spr, 'A'), h, hr)[0][0]; A = np.stack([f(hh + np.eye(3)[k]) - f(hh) for k in range(3)], 1); dh = np.linalg.solve(A, y)
        assert np.abs(f(hh + dh) - (f(hh) + y)).max() < 1e-6
        for fn, old, new in (('HandHook', hh, hh + dh), ('TopInHand', np.array(o['rows']['TopInHand']), np.array(o['rows']['TopInHand']) + y)):
            i0 = t.index('static Vector3 %s(int i)' % fn); i1 = t.index('\n\t}', i0); seg = t[i0:i1]
            m = re.search(r'case %d:\s*return \([^)]*\);[^\n]*' % i, seg); w_ = re.search(r'off-hand FBX lane.*\(was \(([^)]*)\)\)', m.group(0))
            if w_: old = np.array([float(x) for x in w_.group(1).split(',')]); new = old + (dh if fn == 'HandHook' else y)	# a second run: from the row before this lane
            line = 'case %d:\treturn (%.3f, %.3f, %.3f);\t// off-hand FBX lane: the part moved %.2f cm (%.2f %.2f %.2f F L U) so the FBX hand grips it (wire_holds.py) (was (%.3f, %.3f, %.3f))' % ((i,) + tuple(new) + (np.linalg.norm(y),) + tuple(y) + tuple(old))
            t = t[:i0] + seg[:m.start()] + line + seg[m.end():] + t[i1:]
        print('moved', j, np.round(y, 2), 'HandHook +', np.round(dh, 3))
    wr('zscript/rsr/rsr_guns.bd.zs', t)
# a break-open round the fit moved by y (drawn cm = the off-hand frame): the round in the hand is G (K P + RestT) + HandT, so HandT += y,
# and HandBase / HandTip (the round's base and tip in the hand, which the insert check reads) += y
if any(j.startswith('rsb') for j in moved):
    t = rd('zscript/rsr/rsb_guns.zs')
    for j, y in [(j, y) for j, y in moved.items() if j.startswith('rsb')]:
        i = int(j[3:])
        for fn in ('HandT', 'HandBase', 'HandTip'):
            i0 = t.index('static Vector3 %s(int i)' % fn); i1 = t.index('\n\t}', i0); seg = t[i0:i1]
            m = re.search(r'case %d:\s*return \(([^)]*)\);[^\n]*' % i, seg); w_ = re.search(r'off-hand FBX lane.*\(was \(([^)]*)\)\)', m.group(0))
            old = np.array([float(x) for x in (w_ or m).group(1).split(',')]); new = old + y
            line = 'case %d:\treturn (%.4f, %.4f, %.4f);\t// off-hand FBX lane: the round moved %.2f cm (%.2f %.2f %.2f F L U) into the FBX pinch, where it shows (wire_holds.py) (was (%.4f, %.4f, %.4f))' % ((i,) + tuple(new) + (np.linalg.norm(y),) + tuple(y) + tuple(old))
            t = t[:i0] + seg[:m.start()] + line + seg[m.end():] + t[i1:]
        print('moved', j, np.round(y, 2))
    wr('zscript/rsr/rsb_guns.zs', t)
# vreload HoldState: each magazine gun its own frame
t = rd('zscript/rsr/vreload.zs'); i0 = t.index('	clearscope static String HoldState(int i)'); i1 = t.index('\n\t}\n', i0) + 4
new = ('\tclearscope static String HoldState(int i)\n\t{\n\t\t// off-hand FBX lane (owner 2026-10-28: the reload holds become FBX): each gun\'s own FBX frame round its own part\n'
       '\t\t// (MODELDEF.rsq RQHF <letter> = OhHold<letter>, tools/handfit/offhand). Was Ermac\'s ammo_hand 3 (RsrHold) / 6 (RsrHoldPod: 13, 15, 16).\n'
       '\t\tstatic const String h[] = { "RsrHold"' + ''.join(', "OhHold%s"' % chr(64 + i) for i in range(1, 19)) + ' };\n'
       '\t\treturn i >= 1 && i < h.Size() ? h[i] : "RsrHold";\n\t}\n')
t = t[:i0] + new + t[i1:]
if 'holds are FBX since' not in t: t = sub1(t, '	// 1.99x item 10: which of Ermac\'s ammo_hand holds takes the part.', '	// 1.99x item 10 (history; the holds are FBX since 2026-10-28): which of Ermac\'s ammo_hand holds took the part.')
wr('zscript/rsr/vreload.zs', t)
# rsb HoldState
t = rd('zscript/rsr/rsb_guns.zs'); i0 = t.index('	clearscope static String HoldState(int i)'); i1 = t.index('\n\t}\n', i0) + 4
m = {1: 'S', 2: 'T', 3: 'U', 7: 'U', 8: 'U', 9: 'U', 10: 'V', 11: 'W'}
new = ('\tclearscope static String HoldState(int i)\n\t{\n\t\t// off-hand FBX lane (2026-10-28): the FBX hand round each gun\'s own round / loader (RQHF, tools/handfit/offhand).\n'
       '\t\t// Rows 3, 7, 8, 9 draw the same part (RBRP H): one frame. Rows 4-6 have no class in the pack (Ermac-era names kept, now FBX frames).\n\t\tswitch (i)\n\t\t{\n' +
       ''.join('\t\tcase %d:\treturn "%s";\n' % (i, 'OhHold' + m[i] if i in m else {4: 'RsbShell', 5: 'RsbCell', 6: 'RsbCell'}[i]) for i in range(1, 12)) + '\t\t}\n\t\treturn "";\n\t}\n')
t = t[:i0] + new + t[i1:]; wr('zscript/rsr/rsb_guns.zs', t)
print(json.dumps(dict(frames=len(frames), bake=P['bake_check_max_cm'])))
