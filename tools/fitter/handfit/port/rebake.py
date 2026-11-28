"""rebake.py: the solved hand poses as DATA (tools/handfit/poses/<Class>.json), and the MD3 frames rebuilt from them.
  rebake.py export <Class>              fits/curl3_<Class>.json + fits/ported_<Class>.json -> poses/<Class>.json
            [--curl=P --ported=P --fit=P --baked=NAME]   the same from given files (MP40: batch 3's run outputs)
  rebake.py export_lanec <Class> [revindex.json]   BrutalPistol / Flamethrower2 (lane_c r5 results) or BrutalSMG (batch 2 revindex output)
                                         -> poses/<Class>.json, `form: lane_c` (see the lane_c section below)
  rebake.py place <Class>...            the placement numbers (MODELDEF Offset/ZOffset/Angle/Pitch/Roll, gunmoves Pivot + fire rows)
                                         regenerated from poses/<Class>.json with port_gun's functions, compared to src/ and fits/ported_<Class>.json
  rebake.py check [<Class>...]           bake + place for every poses/*.json (bakes go to a temp dir)
  rebake.py bake <poses.json> <out>      the FBX hand (env RSQ_FBX, same skeleton) posed by the JSON's joint vectors -> <out>_R.md3
                                         frames 0 trigger, 1 squeeze, 2 the approved pistol check; prints the difference (bytes, max
                                         md3 units / cm) to the committed bake (`bake_md3`) and the shipped md3 (`baked` / `baked_md3`)
Three pose JSON forms are read: batch 4/5 (q_trigger / q_squeeze, export below), heavies / fit farm (poses.trigger.pose_vector,
heavies/poses_hv.py) and shotguns (joints.trigger / joints.squeeze, shotguns/poses_sg.py).
The pose JSON: `q_trigger` / `q_squeeze` = the full joint-parameter vector of fbx_fitter's hand model (solve.hand_X order: the r5
pistol pose with the solved fingers replaced), `solved_fingers` (those take the pose as solved; the rest keep the approved pistol
hand's per-vertex correction `delta`, exactly as curl3 did), the wrist placement on the gun (R, t: hand -> gun scene frame; `shift`
d), the gun move (MODELDEF Offset/ZOffset/Angle/Pitch/Roll), and the FBX source + take. `support` (batch 5): the FBX support pose
(fbx_b1_L.md3 frame) and the hook / rot / point the handtable row holds, with its measurements.
Needs RSQ_HANDS_TOOL = a full fitter checkout (lane data) and the FBX (fbx_fitter/handmodel.py FBX, or RSQ_FBX). The fit outputs the
poses came from (lane_c round4_final / squeeze_r5 / gun_modeldef_R3, batch 2 / 3 run outputs, mp40chk) are in poses/sources (SHA256SUMS,
checked by `check`; RSQ_POSE_SOURCES overrides)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, re, json, glob, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET; POSES = os.path.join(_DP.POSES)
sys.path.insert(0, os.path.join(HERE, '..', 'fitter_lib')); sys.path.insert(0, _DP.HANDS_TOOL)
import handmodel
if os.environ.get('RSQ_FBX'): handmodel.FBX = os.environ['RSQ_FBX']
import solve, bake, scene, revindex
BONES_PREFIX = None
SOURCES = os.environ.get('RSQ_POSE_SOURCES', os.path.join(POSES, 'sources'))	# the fit outputs the poses were exported from (sha256 in SHA256SUMS)
def _hand_setup():
    """batch2 revindex.setup(), verbatim, with round4_final.json read from poses/sources/lane_c (revindex hard-codes the cloud lane_c path)."""
    R4 = json.load(open(_r4()))['BrutalPistol']
    ctx = solve.Ctx('BrutalPistol', 'R', None, 'gunhand'); x = np.array(R4['x_gun']); Rg, tg = solve.gun_T(ctx, x)
    to_g = lambda X: (X - ctx.c - tg) @ Rg + ctx.c
    Xr = to_g(solve.hand_X(ctx, x)[0]); Xf = np.array(R4['Xg']); delta = Xf - Xr
    return ctx, x, to_g, Xf, delta
def setup():
    from rigid3 import BONES	# finger -> bone prefix (batch 3)
    return _hand_setup(), BONES
def verify_sources():
    import hashlib; bad = []
    for l in open(os.path.join(SOURCES, 'SHA256SUMS')):
        h, f = l.split(None, 1); f = f.strip()
        if hashlib.sha256(open(os.path.join(SOURCES, f), 'rb').read()).hexdigest() != h: bad.append(f)
    assert not bad, 'poses/sources changed (sha256): %s' % bad; print('poses/sources: SHA256SUMS ok')
sys.path.insert(0, os.path.join(HERE, '..', 'fitter_lib'))
def bake_of(g):	# the newest committed bake of this gun's hand (batch 5, then batch 4)
    for b in ('b5', 'b4', 'r9'):	# r9: the Sniper (sniper_fit.py, the Rifle's hold on the Ruger)
        if os.path.exists(os.path.join(_DP.FITS, 'bake', 'fbx_%s_%s_R.md3' % (b, g))): return 'fits/bake/fbx_%s_%s_R.md3' % (b, g)
    return 'fits/bake/fbx_b4_%s_R.md3' % g
SUP_FILE = dict(Rifle='Rifle', Revolver='Revolver', BrutalRevolver='Revolver')	# BrutalRevolver shares the Revolver's row 17 (one cup clears both)
def support_of(g):
    """batch 5: the FBX support hand as data (support_gun.py's solve: fbx_b1_L.md3 frame, the handtable hook / rot / point, measurements)."""
    p = [q for q in (os.path.join(_DP.FITS, d, 'sup_%s.json' % SUP_FILE.get(g, g)) for d in ('b5', 'r9', 'r10', 'r11')) if os.path.exists(q)]	# r9-r11: support_gun.py's json, same form
    if not p: return 'Ermac support pose (no FBX support solved)'
    p = p[0]
    S = json.load(open(p)); S['md3'] = 'models/rsq/fbx/fbx_b1_L.md3'; S['label'] = 'FbxSupF (RQFS B)' if S['pose'] == 'B' else 'FbxSupP (RQFS A)'
    S['how'] = 'support_gun.py %s %s, applied with port_gun.py --support (handtable row %s)' % (S['cls'], S['pose'], {'Rifle': 18, 'Sniper': 22}.get(S['cls'], 17)); return S
def export(g, curl=None, ported=None, fit=None, baked=None):
    """curl / ported / fit / baked: for a gun whose curl3 + ported outputs are not in fits/ (MP40, batch 3): the files given, recorded
    by sha256 in `source`; fit = its port fit.json (the FBX support row in hand.support); baked = the shipped md3 name."""
    curl = curl or os.path.join(_DP.FITS, 'curl3_%s.json' % g); ported = ported or os.path.join(_DP.FITS, 'ported_%s.json' % g)
    C = json.load(open(curl)); P = json.load(open(ported))
    (ctx, x, to_g, Xf, delta), B = setup()
    q = np.array(C['q_MRP']); idx = len(q) == 12; sl = list(range(6 if idx else 9, 18))
    xt = x.copy(); xt[sl] = q; xs = xt.copy(); xs[6:9] = C['q_I_sqz']
    out = dict(cls=g, fbx=os.path.basename(handmodel.FBX), fbx_take='the FBX\'s single 1279-frame take: joint LIMITS only; the pose is the parameter vector below (bind pose + these rotations)',
               model='tools/handfit/fbx_fitter/handmodel.py + solve.hand_X (lane_c r5 parameterisation)', q_pistol_r5=x.tolist(), q_trigger=xt.tolist(), q_squeeze=xs.tolist(),
               solved_fingers='IMRP' if idx else 'MRP', squeeze_fingers='I', wrist_on_gun=dict(R=C['R'], t=C['t'], shift=C['shift']),
               gun_move=dict(zip(['Offset_x', 'Offset_y', 'ZOffset', 'AngleOffset', 'PitchOffset', 'RollOffset'], P['place'])),
               fit=dict(trigger=C['trigger'], squeeze=C['squeeze']), bake_md3=bake_of(g), support=support_of(g))
    if baked:
        out.pop('bake_md3'); out['baked'] = baked
        out['source'] = dict(curl='%s (sha256 %s)' % (os.path.basename(curl), _sha(curl)), ported='%s (sha256 %s)' % (os.path.basename(ported), _sha(ported)))
    if fit:
        F = json.load(open(fit)); out['support'] = dict(F['hand']['support'], pose='fbx_b1_L.md3 frame 1 (RQFS B, FBX palm-under)', note=F['hand'].get('support_note'),
                                                       source='%s (sha256 %s)' % (os.path.basename(fit), _sha(fit)))
    os.makedirs(POSES, exist_ok=True); json.dump(out, open(os.path.join(POSES, '%s.json' % g), 'w'), indent=1); print('poses/%s.json' % g)
def rebuild(J):
    (ctx, x, to_g, Xf, delta), B = setup(); dom = ctx.H.dom
    fm = lambda fs: np.array([any(str(b).startswith(B[f]) for f in fs) for b in dom])
    R = np.array(J['wrist_on_gun']['R']); t = np.array(J['wrist_on_gun']['t']); d = np.array(J['wrist_on_gun']['shift'])
    def X(q, fingers):
        m = fm(fingers); return (to_g(solve.hand_X(ctx, np.array(q))[0]) + np.where(m[:, None], 0, delta)) @ R.T + t + d
    return X(J['q_trigger'], J['solved_fingers']), X(J['q_squeeze'], J['solved_fingers'] + J['squeeze_fingers']), ctx, x, Xf
def rebuild_hv(J):
    """r11: the heavies / fit-farm pose JSON (heavies/poses_hv.py: poses.trigger / poses.squeeze pose_vector + solved_fingers, wrist R, t,
    shift_cm), rebuilt exactly as the farm's curl (fit_hv.curl: solved fingers carry no per-vertex delta; X @ R^T + t + shift)."""
    (ctx, x, to_g, Xf, delta), B = setup(); dom = ctx.H.dom
    fm = lambda fs: np.array([any(str(b).startswith(B[f]) for f in fs) for b in dom])
    W = J['wrist']; R = np.array(W['R']); t = np.array(W['t']); d = np.array(W['shift_cm'])
    def X(P):
        m = fm(P.get('solved_fingers', 'IMRP')); return (to_g(solve.hand_X(ctx, np.array(P['pose_vector']))[0]) + np.where(m[:, None], 0, delta)) @ R.T + t + d
    return X(J['poses']['trigger']), X(J['poses']['squeeze']), ctx, x, Xf
def rebuild_sg(J):
    """the shotguns lane's pose JSON (shotguns/poses_sg.py: joints.trigger / joints.squeeze full vectors, wrist R, t, gun_shift_cm), rebuilt
    exactly as fit_sg.curl: the solved fingers carry no per-vertex delta (IMRP when the index was re-solved, i.e. joints.trigger[6:9] differs
    from joints.pistol[6:9], else MRP; the squeeze adds I), X @ R^T + t + gun_shift."""
    (ctx, x, to_g, Xf, delta), B = setup(); dom = ctx.H.dom
    fm = lambda fs: np.array([any(str(b).startswith(B[f]) for f in fs) for b in dom])
    W = J['wrist']; R = np.array(W['R']); t = np.array(W['t']); d = np.array(W['gun_shift_cm']); j = J['joints']
    sf = J.get('solved_fingers', 'IMRP' if list(j['trigger'][6:9]) != list(j['pistol'][6:9]) else 'MRP')
    def X(q, fs): m = fm(fs); return (to_g(solve.hand_X(ctx, np.array(q))[0]) + np.where(m[:, None], 0, delta)) @ R.T + t + d
    return X(j['trigger'], sf), X(j['squeeze'], sf + 'I'), ctx, x, Xf
SHIPPED = os.path.join(REPO, 'src', 'models', 'rsq', 'fbx')
def refs(J):
    """the md3s this pose must reproduce: the committed bake (fits/, batch 4/5) and the shipped one (src/models/rsq/fbx)."""
    out = []
    if J.get('bake_md3'): out.append(('committed bake', os.path.join(os.path.dirname(_DP.FITS), J['bake_md3'])))	# 'fits/...' is relative to the set's handfit/
    name = J.get('baked') or J.get('baked_md3') or (os.path.basename(J['bake_md3']) if J.get('bake_md3') else None)
    if name: out.append(('shipped', os.path.join(SHIPPED, name)))
    return out
MD3_CM = 1.02	# 1 md3 unit drawn = 1.02 cm (hudrender.to_local ws, the hook chain is a rotation; hook.PL scale +-1)
def compare(new, ref):
    a = scene.md3_full(new)[0]['xyz']; b = scene.md3_full(ref)[0]['xyz']; n = min(len(a), len(b))
    same = open(new, 'rb').read() == open(ref, 'rb').read(); dv = float(np.abs(a[:n] - b[:n]).max()) if a.shape[1] == b.shape[1] else float('nan')
    return dict(bytes_identical=same, frames_new=len(a), frames_ref=len(b), max_md3=dv, max_cm=dv * MD3_CM)
def rebake(path, out):
    J = json.load(open(path))
    if J.get('form') == 'lane_c': return rebake_lanec_cmp(J, out)
    if 'poses' in J and 'trigger' not in J['poses']:	# r12: FlameCannon (owner: no gun hand drawn): nothing to bake, placement only
        print('no gun hand (%s): nothing to bake' % J.get('gun_hand', 'none')); return {}
    Xt, Xs, ctx, x, Xf = (rebuild_hv if 'poses' in J else rebuild_sg if 'joints' in J else rebuild)(J); Rg, tg = solve.gun_T(ctx, x); to_c = lambda X: solve.gmove(ctx, Rg, tg, X)
    ent = [dict(name=J['cls'] + '_trg', side='R', X=to_c(Xt)), dict(name=J['cls'] + '_sqz', side='R', X=to_c(Xs)), dict(name='PISTOL_chk', side='R', X=to_c(Xf))]
    for e in ent: e['cuff_ref'] = e['X'][ctx.cuff]
    rows, paths, _ = bake.bake(ent, out + '.md3'); print(paths['R'])
    res = {}
    for what, ref in refs(J):
        if not os.path.exists(ref): print('vs %s: %s missing' % (what, ref)); continue
        c = compare(paths['R'], ref); res[what] = c
        print('vs %s %s: %s, max %.4f md3 units (%.4f cm) over %d of %d frames' % (what, os.path.relpath(ref, REPO), 'bytes identical' if c['bytes_identical'] else 'bytes differ',
              c['max_md3'], c['max_cm'], min(c['frames_new'], c['frames_ref']), c['frames_ref']))
    return res
def _port():
    sys.path.insert(0, HERE); import port_gun as pg
    pg.SRC = os.environ.get('RSQ_SRC', os.path.join(REPO, 'src'))
    for d, m in (('shotguns', 'port_sg'), ('heavies', 'port_hv'), ('grenade', 'port_nade')):	# hv last of the guns: its SSG entry is the one the r11 port used; port_nade: HandGrenades only
        sys.path.insert(0, os.path.join(HERE, '..', d)); __import__(m)
    __import__('melee_r12')	# r12: the melee registry (BrutalAxe, Chain_saw, DSweap)
    return pg
def place_of(J):
    g = J['gun_move']
    if 'place' in g: return np.array(g['place'])
    if 'modeldef_place' in g: return np.array(g['modeldef_place'])
    return np.array([g[k] for k in ['Offset_x', 'Offset_y', 'ZOffset', 'AngleOffset', 'PitchOffset', 'RollOffset']])
def place(cls):
    if json.load(open(os.path.join(POSES, cls + '.json'))).get('form') == 'lane_c': return place_lanec(json.load(open(os.path.join(POSES, cls + '.json'))))
    """the placement numbers regenerated from poses/<Class>.json with the port tools' own functions (port_gun.rigid_move / pivot /
    fire_rows, port_gun.modeldef's %.3f format; registries of port_gun + shotguns/port_sg + heavies/port_hv), compared to src/ MODELDEF and
    gunmoves.zs and to fits/ported_<Class>.json."""
    pg = _port()
    J = json.load(open(os.path.join(POSES, cls + '.json'))); p = place_of(J); out = dict(cls=cls)
    pp = os.path.join(_DP.FITS, 'ported_%s.json' % cls); P = json.load(open(pp)) if os.path.exists(pp) else None	# MP40: its ported json is not in fits/
    if P: out['pose_vs_ported_place'] = float(np.abs(np.array(P['place']) - p).max())
    G = dict(pg.GUNS[cls], cls=cls); G['md3'] = os.path.join(pg.SRC, G['md3'])
    R, t = pg.rigid_move(G, p)
    if P: out['Rt_vs_ported'] = float(max(np.abs(R - np.array(P['R'])).max(), np.abs(t - np.array(P['t'])).max()))
    if 'R' in J['gun_move']: out['Rt_vs_pose'] = float(max(np.abs(R - np.array(J['gun_move']['R'])).max(), np.abs(t - np.array(J['gun_move']['t'])).max()))
    # MODELDEF: every block drawing this gun's meshes that carries a moved placement (AngleOffset present + the port's tag)
    exp = ['%.3f' % v for v in p]; ok = bad = 0; badl = []
    names = G['names'] + G.get('names_extra', [])
    for f in sorted(glob.glob(os.path.join(pg.SRC, 'MODELDEF*'))):
        tx = open(f, encoding='latin1').read()
        for m in pg.BLK.finditer(tx):
            b = m.group(0)
            if not any('"%s"' % n in b for n in names) or 'gun to the FBX hand' not in b: continue
            o = re.search(r'(?m)^\s*Offset\s+(\S+)\s+(\S+)', b); z = re.search(r'(?m)^\s*ZOffset\s+(\S+)', b)
            a = [re.search(r'(?m)^\s*%sOffset\s+(\S+)' % k, b) for k in ('Angle', 'Pitch', 'Roll')]
            got = [o.group(1), o.group(2), z.group(1)] + [x.group(1) if x else None for x in a]
            if got == exp: ok += 1
            else: bad += 1; badl.append('%s %s %s' % (os.path.basename(f), m.group(1), got))
    nmoved = sum(int(s.rsplit('x', 1)[1]) for s in P['moved'] if s.startswith('MODELDEF ')) if P else (sum(G['blocks'].values()) if G.get('blocks') else None)
    out.update(modeldef_match=ok, modeldef_mismatch=bad, modeldef_ported_count=nmoved, mismatches=badl[:4])
    # gunmoves: Pivot row + fire rows
    if G.get('row') is not None and G.get('bdblock'):
        tx = open(os.path.join(pg.SRC, 'zscript/rsq/gunmoves.zs'), encoding='latin1').read(); row = G['row']
        i0 = tx.index('clearscope static Vector3 Pivot'); i1 = tx.index('};', i0); vals = [float(s.strip()) for s in tx[i0:i1].split('{ ', 1)[1].split(',')]
        if 3 * row + 2 >= len(vals): out['gunmoves'] = 'row %d not in gunmoves.zs (port: nothing moved)' % row; return out
        if cls in sys.modules['port_hv'].NOGUNMOVES and vals[3 * row:3 * row + 3] == [0.0, 0.0, 0.0]:	# r12: row 27 now exists in Pivot as (0, 0, 0) (= what Pivot returned before)
            out['gunmoves'] = 'row %d: Pivot (0, 0, 0), no fire rows (port_hv NOGUNMOVES: nothing moved)' % row; return out
        new = pg.pivot(p[:2], p[2]); out['pivot_diff'] = float(np.abs(np.round(new, 3) - np.array(vals[3 * row:3 * row + 3])).max())
        spr = re.findall(r'"([^"]+)"', re.search(r'static const String spr\[\] = \{([^}]*)\}', tx).group(1))
        key = [int(v) for v in re.search(r'static const int key\[\] = \{([^}]*)\}', tx).group(1).split(',')]
        frows = {}
        for k in range(len(spr)):
            if key[2 * k] == row and key[2 * k + 1] not in frows: frows[key[2 * k + 1]] = spr[k]
        f, c = G['bdblock']; b = [m.group(0) for m in pg.BLK.finditer(open(os.path.join(pg.SRC, f), encoding='latin1').read()) if m.group(1) == c and '"%s"' % G['names'][0] in m.group(0)][0]
        fi = {(a, cc): int(n) for a, cc, n in re.findall(r'FrameIndex\s+(\S+)\s+(\S)\s+\d+\s+(\d+)', b)}
        order = sorted(frows); frames = [fi[(frows[r][:4], frows[r][4])] for r in order]
        r1 = pg.fire_rows(G, p[:3], p[3:], frames) if order else []
        lines = tx[tx.index('static Vector3, Vector3 Frame('):].split('\n'); rx = re.compile(r'^(\s*)(-?\d+\.\d+(?:, -?\d+\.\d+){5}),?(.*)$'); idx = [n for n, l in enumerate(lines) if rx.match(l)]
        dmax = 0.0; txt_ok = 0
        for r, v in zip(order, r1):
            shipped = np.array([float(x) for x in rx.match(lines[idx[r]]).group(2).split(',')]); regen = np.array([float('%.2f' % pg.z0(x, 0.005)) for x in v])
            dmax = max(dmax, float(np.abs(shipped - regen).max())); txt_ok += rx.match(lines[idx[r]]).group(2) == ', '.join('%.2f' % pg.z0(x, 0.005) for x in v)
        out.update(fire_rows=len(order), fire_rows_text_identical=txt_ok, fire_rows_max_diff=dmax)
    else: out['gunmoves'] = 'no handtable row / bd block (port_gun moves no gunmoves rows for this gun)'
    return out
# ---------------------------------------------------------------- lane_c form (BrutalPistol, Flamethrower2: lane_c r5; BrutalSMG: batch 2)
# The hand is lane_c's FbxHand on the gun's own landmark context; every vertex not in the frame's exact joints keeps lane_c's
# contact-projection correction (round4_final[key].Xg minus the FK of its x_gun), exactly as squeeze.py / revindex.py / bake3.py
# built the shipped frames. The frames of one md3 are listed in `md3.frames` ([pose class, trigger|squeeze, frame name]).
INDEX_JOINTS = ['INDEX_BASE_joint', 'INDEX_MID_joint', 'INDEX_TOP_joint', 'INDEX_UP_TOP_joint']	# squeeze.py / revindex.py
LANEC_GUN = {'BrutalPistol': ('BrutalPistol', 'BrutalPistol'), 'Flamethrower2': ('Flamethrower2@nozzle', 'Flamethrower2')}	# landmarks, round4 key
def _r4(): return os.path.join(SOURCES, 'lane_c', 'round4_final.json')
def _sha(p):
    import hashlib; return hashlib.sha256(open(p, 'rb').read()).hexdigest()
def lanec_hand(J):
    """ctx, x_gun, to_g, delta, to_c of the pose's hand (J['hand'])."""
    H = J['hand']; R4 = json.load(open(_r4()))[H['key']]
    ctx = solve.Ctx(H['landmarks'], 'R', None, 'gunhand'); x = np.array(R4['x_gun']); Rg, tg = solve.gun_T(ctx, x)
    to_g = lambda X: (X - ctx.c - tg) @ Rg + ctx.c; delta = np.array(R4['Xg']) - to_g(solve.hand_X(ctx, x)[0])
    return ctx, x, to_g, delta, (lambda X: solve.gmove(ctx, Rg, tg, X))
def lanec_frame(J, which):
    ctx, x, to_g, delta, to_c = lanec_hand(J); m = np.isin(ctx.H.dom, J['exact_joints'][which])
    X = to_c(to_g(solve.hand_X(ctx, np.array(J['q_' + which]))[0]) + np.where(m[:, None], 0, delta)); return X, ctx
def export_lanec(g, revindex_json=None):
    lane = solve.LANE; R4 = json.load(open(_r4()))
    if g in LANEC_GUN:
        lm, key = LANEC_GUN[g]; o = R4[key]; SQ = json.load(open(os.path.join(SOURCES, 'lane_c', 'squeeze_r5.json')))[key]
        x = list(o['x_gun']); assert list(SQ['q_index_trigger']) == x[6:9], 'squeeze_r5 trigger index != round4 x_gun'
        qs = list(x); qs[6:9] = SQ['q_index_squeeze']
        MD = json.load(open(os.path.join(SOURCES, 'lane_c', 'gun_modeldef_R3.json')))[g]
        out = dict(cls=g, form='lane_c', fbx='hand_final.fbx (DXR models/hands, never shipped)',
                   source=dict(trigger='lane_c results/round4_final.json [%s].x_gun (sha256 %s)' % (key, _sha(_r4())),
                               squeeze='lane_c results/squeeze_r5.json [%s].q_index_squeeze (squeeze.py, round 5)' % key,
                               gun_move='lane_c results/gun_modeldef_R3.json [%s] (modeldef3.py: gunplace.fit of gun_T(ctx, x_gun))' % g,
                               md3='lane_c bake3.py LANEC_FINAL=round4_final.json LANEC_SQUEEZE=1 (squeeze_r5.json) -> fbx_b1_R.md3'),
                   hand=dict(landmarks=lm, key=key, vertex_correction='round4_final.json [%s].Xg - FK(x_gun): kept on every vertex outside exact_joints' % key),
                   q_trigger=x, q_squeeze=qs, exact_joints=dict(trigger=[], squeeze=INDEX_JOINTS),
                   gun_move=dict(Offset_x=MD['Offset'][0], Offset_y=MD['Offset'][1], ZOffset=MD['ZOffset'], AngleOffset=MD['AngleOffset'], PitchOffset=MD['PitchOffset'], RollOffset=MD['RollOffset'],
                                 how='the gun move IS the pose wrist: solve.gun_T(ctx, x_gun) as MODELDEF numbers (gunplace.fit)'),
                   md3=dict(baked='fbx_b1_R.md3', frames=[['BrutalPistol', 'trigger', 'Brutal_gun'], ['Flamethrower2', 'trigger', 'Flamet_gun'],
                                                          ['BrutalPistol', 'squeeze', 'Brutal_sqz'], ['Flamethrower2', 'squeeze', 'Flamet_sqz']]),
                   support='lane_c support pose: fbx_b1_L.md3 frame %d (round4_final.json [%s].Xs, %s); its joint vectors are in lane_c results, not re-exported here' % (0 if g == 'BrutalPistol' else 1, key, o.get('support_file')))
    else:	# BrutalSMG: batch 2 revindex.py (the approved pistol hand, index re-solved), gun moved by the shift
        V = json.load(open(revindex_json))[g]; x = list(R4['BrutalPistol']['x_gun']); qt = list(x); qt[6:9] = V['q_trigger']; qs = list(x); qs[6:9] = V['q_squeeze']
        P = port_place_smg(V['shift'])
        out = dict(cls=g, form='lane_c', fbx='hand_final.fbx (DXR models/hands, never shipped)',
                   source=dict(fit='batch 2 revindex.py output revindex_BrutalSMG.json (sha256 %s): q_trigger / q_squeeze (index), shift' % _sha(revindex_json),
                               md3='batch2/bake_b2.py -> fbx_b2_R.md3 (frames SMG_trg, SMG_sqz, PISTOL_chk)',
                               gun_move='batch2/move_b2.py place(shift) = port_gun.place: the pistol r5 aim, translated by shift (original frame)'),
                   hand=dict(landmarks='BrutalPistol', key='BrutalPistol', vertex_correction='round4_final.json [BrutalPistol].Xg - FK(x_gun): kept on every vertex outside exact_joints'),
                   q_trigger=qt, q_squeeze=qs, exact_joints=dict(trigger=INDEX_JOINTS, squeeze=INDEX_JOINTS), shift_cm=V['shift'],
                   fit=dict((k, V[k]) for k in ('pad_err_trigger_cm', 'pad_err_squeeze_cm', 'pen_index_cm', 'pen_hand_cm', 'non_index_moved_cm')),
                   gun_move=dict(zip(['Offset_x', 'Offset_y', 'ZOffset', 'AngleOffset', 'PitchOffset', 'RollOffset'], P)),
                   md3=dict(baked='fbx_b2_R.md3', frames=[['BrutalSMG', 'trigger', 'SMG_trg'], ['BrutalSMG', 'squeeze', 'SMG_sqz'], ['BrutalPistol', 'trigger', 'PISTOL_chk']]),
                   support='batch 2: fbx_b1_L.md3 frame 1 (RQFS B) placed under the SMG forend (bake_b2.py), handtable row 5')
    json.dump(out, open(os.path.join(POSES, '%s.json' % g), 'w'), indent=1); print('poses/%s.json' % g)
SMG = dict(md3='models/bd/BrutalSMG/BrutalSMG.md3', ready=3, scale=[-1, 1, 1], off=[0, 0, -5])	# MODELDEF.bd.txt BrutalSMG base (batch2/revlm.py)
def port_place_smg(shift):
    pg = _port(); G = dict(SMG, md3=os.path.join(pg.SRC, SMG['md3'])); p, res, R0, t0 = pg.place(G, shift); return [float(v) for v in p]
def rebake_lanec(J, out):
    ents = []
    for c, which, name in J['md3']['frames']:
        K = J if c == J['cls'] else json.load(open(os.path.join(POSES, c + '.json')))
        X, ctx = lanec_frame(K, which); ents.append(dict(name=name, side='R', X=X, cuff_ref=X[ctx.cuff]))
    rows, paths, _ = bake.bake(ents, out + '.md3'); print(paths['R']); return paths['R']
LANEC_ROWS = {'BrutalPistol': dict(md3='models/bd/BrutalPistol/BrutalPistol.md3', names=['BrutalPistol.md3'], ready=3, row=4),	# handtable.zs rows, MODELDEF.bd.txt ready frames
              'Flamethrower2': dict(md3='models/bd/Flamethrower2/Flamethrower2.md3', names=['Flamethrower2.md3'], ready=0, row=7),
              'BrutalSMG': dict(md3='models/bd/BrutalSMG/BrutalSMG.md3', names=['BrutalSMG.md3'], ready=3, row=5)}
def _gunmoves(pg, G, p):
    """gunmoves Pivot + fire rows regenerated with port_gun.pivot / fire_rows (rows from key[], md3 frames from the bd block)."""
    tx = open(os.path.join(pg.SRC, 'zscript/rsq/gunmoves.zs'), encoding='latin1').read(); row = G['row']; out = {}
    i0 = tx.index('clearscope static Vector3 Pivot'); i1 = tx.index('};', i0); vals = [float(v.strip()) for v in tx[i0:i1].split('{ ', 1)[1].split(',')]
    out['pivot_diff'] = float(np.abs(np.round(pg.pivot(p[:2], p[2]), 3) - np.array(vals[3 * row:3 * row + 3])).max())
    spr = re.findall(r'"([^"]+)"', re.search(r'static const String spr\[\] = \{([^}]*)\}', tx).group(1))
    key = [int(v) for v in re.search(r'static const int key\[\] = \{([^}]*)\}', tx).group(1).split(',')]
    frows = {}
    for k in range(len(spr)):
        if key[2 * k] == row and key[2 * k + 1] not in frows: frows[key[2 * k + 1]] = spr[k]
    f, c = G['bdblock']; b = [m.group(0) for m in pg.BLK.finditer(open(os.path.join(pg.SRC, f), encoding='latin1').read()) if m.group(1) == c and '"%s"' % G['names'][0] in m.group(0)][0]
    fi = {(a, cc): int(n) for a, cc, n in re.findall(r'FrameIndex\s+(\S+)\s+(\S)\s+\d+\s+(\d+)', b)}
    order = sorted(frows); frames = [fi[(frows[r][:4], frows[r][4])] for r in order]
    r1 = pg.fire_rows(G, p[:3], p[3:], frames) if order else []
    lines = tx[tx.index('static Vector3, Vector3 Frame('):].split('\n'); rx = re.compile(r'^(\s*)(-?\d+\.\d+(?:, -?\d+\.\d+){5}),?(.*)$'); idx = [n for n, l in enumerate(lines) if rx.match(l)]
    dmax = 0.0; txt_ok = 0
    for r, v in zip(order, r1):
        m = rx.match(lines[idx[r]]); shipped = np.array([float(x) for x in m.group(2).split(',')]); txt = ', '.join('%.2f' % pg.z0(x, 0.005) for x in v)
        dmax = max(dmax, float(np.abs(shipped - np.array([float(x) for x in txt.split(',')])).max())); txt_ok += m.group(2) == txt
    out.update(fire_rows=len(order), fire_rows_text_identical=txt_ok, fire_rows_max_diff=round(dmax, 4)); return out
def place_lanec(J):
    """MODELDEF numbers regenerated from the pose: lane_c guns = gunplace.fit of gun_T(ctx, x_gun) (modeldef3.py), BrutalSMG = port_gun.place(shift)."""
    import gunplace, gunview, hudrender, scene as sc
    g = J['cls']
    if g in LANEC_GUN:
        ctx, x, to_g, delta, to_c = lanec_hand(J); it = dict(sc.GUNS[g], path=os.path.join(os.environ.get('RSQ_SRC', os.path.join(REPO, 'src')), 'models', 'bd', g, g + '.md3')); V = np.concatenate([s['xyz'][it['frame']] for s in sc.md3_full(it['path'])])
        r = gunplace.fit(it, to_c(gunview.to_fl(hudrender.to_local(V, it)))); p = r['Offset'] + [r['ZOffset'], r['AngleOffset'], r['PitchOffset'], r['RollOffset']]; names = [os.path.basename(it['path'])]
    else: p = port_place_smg(J['shift_cm']); names = [os.path.basename(SMG['md3'])]
    exp = ['%.3f' % v for v in p]; ok = bad = 0; badl = []; src = os.environ.get('RSQ_SRC', os.path.join(REPO, 'src'))
    pg = _port()
    for f in sorted(glob.glob(os.path.join(src, 'MODELDEF*'))):
        tx = open(f, encoding='latin1').read()
        for m in pg.BLK.finditer(tx):
            b = m.group(0)
            if not any('"%s"' % n in b for n in names) or 'gun to the FBX' not in b: continue
            o = re.search(r'(?m)^\s*Offset\s+(\S+)\s+(\S+)', b); z = re.search(r'(?m)^\s*ZOffset\s+(\S+)', b)
            a = [re.search(r'(?m)^\s*%sOffset\s+(\S+)' % k, b) for k in ('Angle', 'Pitch', 'Roll')]
            got = ['%.3f' % float(v) for v in [o.group(1), o.group(2), z.group(1)] + [x_.group(1) if x_ else 'nan' for x_ in a]]
            if got == exp: ok += 1
            else: bad += 1; badl.append('%s %s %s' % (os.path.basename(f), m.group(1), got))
    gm = J['gun_move']; rec = np.array([gm[k] for k in ['Offset_x', 'Offset_y', 'ZOffset', 'AngleOffset', 'PitchOffset', 'RollOffset']])
    G = dict(LANEC_ROWS[g], cls=g, scale=[-1, 1, 1], off=[0, 0, -5], bdblock=('MODELDEF.bd.txt', g)); G['md3'] = os.path.join(pg.SRC, G['md3'])
    return dict(cls=g, regenerated=exp, pose_vs_regenerated=float(np.abs(rec - np.array(p)).max()), modeldef_match=ok, modeldef_mismatch=bad, mismatches=badl[:4], **_gunmoves(pg, G, np.array(p, float)))
def rebake_lanec_cmp(J, out):
    new = rebake_lanec(J, out); res = {}
    for what, ref in (('shipped', os.path.join(SHIPPED, J['md3']['baked'])),):
        c = compare(new, ref); res[what] = c
        print('vs %s %s: %s, max %.4f md3 units (%.4f cm) over %d of %d frames' % (what, os.path.relpath(ref, REPO), 'bytes identical' if c['bytes_identical'] else 'bytes differ',
              c['max_md3'], c['max_cm'], min(c['frames_new'], c['frames_ref']), c['frames_ref']))
    return res
def check(classes):
    """bake every pose (or the named ones) to a temp dir, compare to the committed + shipped md3, and regenerate its placement."""
    import tempfile, glob
    verify_sources()
    classes = classes or sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(POSES, '*.json'))); tmp = tempfile.mkdtemp(prefix='rebake_')
    for g in classes:
        print('== %s' % g)
        if json.load(open(os.path.join(POSES, g + '.json'))).get('gun_move', 1) is None:	# r12: staged, not ported (HandGrenades: not ready)
            print('not ported (gun_move null): skipped'); continue
        r = rebake(os.path.join(POSES, g + '.json'), os.path.join(tmp, g)); print('placement:', json.dumps(place(g)))
if __name__ == '__main__':
    if sys.argv[1] == 'export':
        a = [v for v in sys.argv[2:] if not v.startswith('--')]; kw = dict(v[2:].split('=', 1) for v in sys.argv[2:] if v.startswith('--'))
        for g in a: export(g, **kw)
    elif sys.argv[1] == 'export_lanec': export_lanec(sys.argv[2], *sys.argv[3:4])
    elif sys.argv[1] == 'place':
        for g in sys.argv[2:]: print(json.dumps(place(g)))
    elif sys.argv[1] == 'check': check(sys.argv[2:])
    else: rebake(sys.argv[2], sys.argv[3])
