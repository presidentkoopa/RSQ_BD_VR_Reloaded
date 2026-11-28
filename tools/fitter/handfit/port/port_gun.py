"""port_gun.py <Class> <fit.json> [--src DIR] [--tag TEXT] [--dry]

ONE command for the owner's one method (batches 1-3 consolidated): the drawn wrist stays pinned to the controller and
the GUN moves to the fitted hand. It applies the gun move and moves EVERY table that hangs off the gun, then lists what
it moved:
  - every gun-controller MODELDEF block that draws the gun's meshes (count asserted per (file, class); off-hand,
    dropped and world blocks excluded by sprite)
  - gunmoves.zs: Pivot row and every fire-frame row keyed to the gun (rigid fit through the full QZD 17.3 MODELDEF chain,
    the Depot generator's conventions; the original placement must reproduce the shipped rows, asserted)
  - reload tables: rsr_guns.bd.zs (Well, Axis, MagCentre, WellHook, Grab, Pull, HandleHook, Offset), rsb_guns.zs
    (break-open: Hinge, Axis, Offset, Casing; the hand-frame rows are kept)
  - casing port (casings.zs), muzzle row (RSQ_Muzzle; added at the drawn muzzle if the gun has none), RSQ_ScopeTable
    (Lens, Axis), the Rifle's M203 tables (rsr_m203_geo ToGun/FromGun/FwdHook + the purist handguard hook)
  - optional, if fit.json has "hand": the FBX gun-hand wiring (md3, MODELDEF hand blocks, hands.zs / dualhands.zs labels,
    handtable rows) and "support" (palm-under hook/rot/point; "move" = the existing support pose moved with the gun)
fit.json: "shift" (cm, the gun's ORIGINAL controller frame: curl3's shift) or "place" (6 MODELDEF numbers).
The gun keeps the approved pistol's r5 aim (batch 3's method) and is translated so its grip meets the hand.
Paths: the repo is found from this file; the fitter modules from ../fbx_fitter. No absolute paths.
Every text edit asserts the exact text it replaces (port_b2/b3's rule)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, re, sys, json, math, shutil, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET
sys.path.insert(0, _DP.HANDS_TOOL)
import gunplace, gunview, hudrender
from scipy.optimize import least_squares
SRC = os.environ.get('RSQ_SRC', os.path.join(REPO, 'src'))

# ---------------------------------------------------------------- geometry (gunmove.py / move_b2 / follow_b2, generalised)
def md3_frames(path):
    import struct
    d = open(path, 'rb').read(); nfr, ntag, nsurf = struct.unpack_from('<3i', d, 76); osurf = struct.unpack_from('<i', d, 100)[0]
    out = []; off = osurf
    for s in range(nsurf):
        flags, snfr, nsh, nv, nt, otri, osh, ost, oxyz, oend = struct.unpack_from('<10i', d, off + 68)
        out.append(np.frombuffer(d, '<i2', snfr * nv * 4, off + oxyz).reshape(snfr, nv, 4)[:, :, :3].astype(float) / 64.0); off += oend
    return out
def raw(path, fr, surf=None): return np.concatenate([s[fr] for k, s in enumerate(md3_frames(path)) if surf is None or k in surf])
def chain(scale, off, ao):
    it = dict(scale=list(scale), off=list(off), ao=tuple(ao))
    return lambda V: gunview.to_fl(gunplace.to_local_ao(np.atleast_2d(np.asarray(V, float)), it))
def affine(f):
    b = f(np.zeros(3))[0]; return np.stack([f(np.eye(3)[i])[0] - b for i in range(3)], 1), b
PISTOL_R5 = dict(off=[0.820, -8.333, -1.408], ao=(3.854, 3.363, 10.974))	# lane_c r5, the approved pistol (owner)
def pistol_move():
    A0, b0 = affine(chain([-1, 1, 1], [0, 0, -5], (0, 0, 0))); A1, b1 = affine(chain([-1, 1, 1], PISTOL_R5['off'], PISTOL_R5['ao']))
    R = A1 @ np.linalg.inv(A0); return R, b1 - R @ b0
def place(G, d):
    """MODELDEF numbers that draw the gun at R0 (p + d) + t0: the pistol's aim, translated by d (original frame)."""
    R0, t0 = pistol_move(); X = raw(G['md3'], G['ready']); V0 = chain(G['scale'], G['off'], (0, 0, 0))(X)
    tgt = V0 @ R0.T + (R0 @ np.asarray(d) + t0)
    res = lambda p: (chain(G['scale'], p[:3], p[3:])(X) - tgt).ravel()
    s = least_squares(res, np.r_[G['off'], PISTOL_R5['ao']]); return s.x, float(np.abs(res(s.x)).max()), R0, R0 @ np.asarray(d) + t0
def rigid_move(G, p):
    """R, t: original controller-frame point -> drawn point after the move (exact, from the chain)."""
    A0, b0 = affine(chain(G['scale'], G['off'], (0, 0, 0))); A1, b1 = affine(chain(G['scale'], p[:3], p[3:]))
    R = A1 @ np.linalg.inv(A0); return R, b1 - R @ b0
def kabsch(a, b):
    ca, cb = a.mean(0), b.mean(0); U, s, Vt = np.linalg.svd((a - ca).T @ (b - cb)); dd = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, dd]) @ U.T; return R, cb - R @ ca
def rigid(a, b, keep=0.6, rounds=5):	# Depot kick_measure.rigid (trimmed), verbatim logic
    idx = np.arange(len(a))
    for _ in range(rounds):
        R, t = kabsch(a[idx], b[idx]); res = np.linalg.norm(a @ R.T + t - b, axis=1); idx = np.argsort(res)[:max(10, int(len(a) * keep))]
    return kabsch(a[idx], b[idx])
D_ = np.diag([-1.0, 1.0, 1.0]); O_H = np.array([0.0, -10.0, -24.0]); P_ = np.array([[0, 0, -1], [-1, 0, 0], [0, 1, 0.]]); SH = np.array([0, 5, 30.])
def kick_angles(R): return np.array([math.degrees(math.atan2(R[0, 2], R[2, 2])), math.degrees(math.asin(max(-1, min(1, -R[1, 2])))), math.degrees(math.atan2(R[1, 0], R[1, 1]))])
def fire_rows(G, off, ao, frames):
    f = lambda fr: chain(G['scale'], off, ao)(raw(G['md3'], fr, G.get('kick_surf'))) @ P_ - SH
    a = f(G['ready']); out = []
    for fr in frames:
        Rw, tw = rigid(a, f(fr)); Rk = D_ @ Rw @ D_; u = Rk.T @ (Rk @ O_H - O_H + D_ @ tw); out.append(np.r_[kick_angles(Rk), u])
    return np.array(out)
def pivot(off, zoff): return D_ @ np.array([off[0], zoff, off[1]]) - O_H

# ---------------------------------------------------------------- text helpers
PENDING = {}	# all edits are held here and written only when every step has passed (no half-moved tree on an assert)
def rd(p): return PENDING[p] if p in PENDING else open(os.path.join(SRC, p), encoding='latin1').read()
def wr(p, t): PENDING[p] = t
def flush():
    if ARGS.dry: return
    for p, t in PENDING.items(): open(os.path.join(SRC, p), 'w', encoding='latin1').write(t)
    for a, b in COPIES: shutil.copyfile(a, b)
COPIES = []
def sub1(t, a, b, what):
    n = t.count(a); assert n == 1, '%s: %d matches' % (what, n); return t.replace(a, b)
def first(rx, t, what):
    m = re.search(rx, t); assert m, what; return m
z0 = lambda x, e=5e-4: 0.0 if abs(x) < e else x
v3 = lambda q: '(%.3f, %.3f, %.3f)' % tuple(z0(x) for x in q)
MOVED = []
def note(*a): MOVED.append(' '.join(str(x) for x in a)); print(' ', *a)

# ---------------------------------------------------------------- per-gun registry (parsed from the tree; numbers in it are the base placements as shipped)
# blocks: (MODELDEF file, class) -> expected count of gun-controller blocks; skip: sprites of off-hand / dropped / world blocks
GUNS = {
 'MP40': dict(md3='models/bd/MP40/MP40.md3', names=['MP40.md3'], ready=2, scale=[-1, 1, 1], off=[0, 0, -5], row=12, rsr=4,
    casing='MP40', blocks={('MODELDEF.bd.txt', 'MP40'): 1, ('MODELDEF.purist', 'PuristMP40'): 3, ('MODELDEF.rsqoff', 'RSQ_Off_MP40'): 3,
    ('MODELDEF.rsr', 'MP40'): 2, ('MODELDEF.rsr', 'RSR_GunParts'): 2}, skip=['RQMW'], skipcls=['RSQ_Hands'], bdblock=('MODELDEF.bd.txt', 'MP40'),
    dual=[('MODELDEF.rsqdual', 'MP40'), ('MODELDEF.rsqoff', 'RSQ_Off_MP40'), ('MODELDEF.purist', 'PuristMP40')]),
 'Rifle': dict(md3='models/bd/Rifle/Rifle.md3', names=['Rifle.md3', 'M203.md3'], ready=3, scale=[-1, 1, 1], off=[0, 0, -5], row=18, rsr=1,
    names_extra=['m203_round.md3'], classes=['Rifle', 'PuristRifle', 'RSR_GunParts', 'RSQ_Off_Rifle'],
    casing='Rifle', muzzle_surf=[4], skip=['RQRW', 'RQ2H', 'RQ2S'], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'Rifle'),
    blocks={('MODELDEF.bd.txt', 'Rifle'): 1, ('MODELDEF.purist', 'PuristRifle'): 3, ('MODELDEF.rsm', 'Rifle'): 5, ('MODELDEF.rsm', 'RSR_GunParts'): 2,
            ('MODELDEF.rsqoff', 'RSQ_Off_Rifle'): 9, ('MODELDEF.rsr', 'Rifle'): 3, ('MODELDEF.rsr', 'RSR_GunParts'): 3},
    m203=True, dual=[('MODELDEF.rsqdual', 'Rifle'), ('MODELDEF.rsqoff', 'RSQ_Off_Rifle'), ('MODELDEF.purist', 'PuristRifle')]),
 'Revolver': dict(md3='models/bd/Revolver/Revolver.md3', names=['Revolver.md3'], ready=0, scale=[-1, 1, 1], off=[0, 0, -5], row=17, rsb=[3, 7],
    casing='Revolver', skip=['RBRW'], skipcls=['RSB_Round'],	# RSQ_Hands RBRP (the round in the off hand) moves too: RSB.Hook places it with Offset(i)
    blocks={('MODELDEF.bd.txt', 'Revolver'): 1, ('MODELDEF.purist', 'PuristRevolver'): 2, ('MODELDEF.rsb', 'RSB_GunParts'): 7, ('MODELDEF.rsb', 'Revolver'): 1,
            ('MODELDEF.rsb', 'RSQ_Hands'): 1, ('MODELDEF.rsqoff', 'RSQ_Off_Revolver'): 2}, bdblock=('MODELDEF.bd.txt', 'Revolver'),
    dual=[('MODELDEF.rsqdual', 'Revolver'), ('MODELDEF.rsqoff', 'RSQ_Off_Revolver'), ('MODELDEF.purist', 'PuristRevolver')]),
 'BrutalRevolver': dict(md3='models/bd/Moonlight/rev.md3', names=['rev.md3', 'rev_rsb.md3'], ready=0, scale=[1.35, 1.35, 1.35], off=[0.0262, 0.9224, 0.5878], row=17, rsb=[10, 11],
    skip=[], skipcls=['RSB_Round', 'RSB_Casing'], bdblock=None, dual=[],	# row 17 is shared with the Revolver; no gunmoves rows of its own (RVMA is not in gunmoves' spr list)
    blocks={('MODELDEF.rsqmoon', 'BrutalRevolver'): 2, ('MODELDEF.rsqmoon', 'RSB_GunParts'): 10, ('MODELDEF.rsqmoon', 'RSQ_Hands'): 3}),
 'Sniper': dict(md3='models/bd/XM21/XM21.md3', names=['XM21.md3'], ready=0, scale=[-10.485, 10.485, 10.485], off=[-0.2816, -44.5467, -6.3157], row=22, rsr=8,
    scope=2, skip=['RQKW'], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.rsr', 'Sniper'), dual=[],	# one-frame mesh: no gunmoves fire rows (keyed 99), Pivot row 22 only
    blocks={('MODELDEF.rsr', 'Sniper'): 3, ('MODELDEF.rsr', 'RSR_GunParts'): 3}),
}

# ---------------------------------------------------------------- 1. MODELDEF
BLK = re.compile(r'(?m)^Model[ \t]+(\S+)[ \t]*\n\{.*?\n\}', re.S)
def num(rx, body):
    m = re.search(rx, body); return [float(v) for v in m.group(1).split()] if m else None
def gun_blocks(G):
    """(file, class, match) of every block drawing the gun's meshes at its base placement, not skipped."""
    import glob
    out = []
    for f in sorted(glob.glob(os.path.join(SRC, 'MODELDEF*'))):
        f = os.path.basename(f); tx = rd(f)
        for m in BLK.finditer(tx):
            b = m.group(0); cls = m.group(1)
            if not any('"%s"' % n in b for n in G['names'] + G.get('names_extra', [])): continue
            if G.get('classes') and cls not in G['classes']: continue
            if cls in G['skipcls'] or any(re.search(r'Frame(Index)?\s+%s\s' % s, b) for s in G['skip']): continue
            sc = num(r'(?m)^\s*Scale\s+([-\d. ]+)', b)
            if sc is None or np.abs(np.array(sc[:3]) - np.array(G['scale'])).max() > 1e-3: continue	# a different drawing (world / dropped)
            o = num(r'(?m)^\s*Offset\s+([-\d. ]+)', b); zz = num(r'(?m)^\s*ZOffset\s+([-\d.]+)', b)
            if o is None or zz is None or np.abs(np.array(o[:2] + zz[:1]) - np.array(G['off'])).max() > 1e-3:
                print('  (not moved: %s %s at Offset %s ZOffset %s, not this gun\'s base placement)' % (f, cls, o, zz)); continue
            out.append((f, cls, m))
    return out
def modeldef(G, p, tag):
    PL = 'Offset %.3f %.3f 0.0\n{i}ZOffset %.3f\n{i}AngleOffset %.3f\n{i}PitchOffset %.3f\n{i}RollOffset %.3f\t// ' + tag + ' (lane B): gun to the FBX hand fitted from 1.92'
    PL = PL % tuple(p); count = {}
    files = sorted(set(b[0] for b in gun_blocks(G)))
    for f in files:
        tx = rd(f); out = []; last = 0
        for m in BLK.finditer(tx):
            body = m.group(0); cls = m.group(1)
            if any(fb == f and cb == cls and mb.start() == m.start() for fb, cb, mb in gun_blocks_cache[G['cls']]):
                mm = re.search(r'(?m)^([ \t]*)Offset[ \t]+([-\d.]+)[ \t]+([-\d.]+)[ \t]+([-\d.]+)[^\n]*\n', body); assert mm, (f, cls)
                z = re.search(r'(?m)^[ \t]*ZOffset[ \t]+([-\d.]+)[ \t]*\n', body); assert z, (f, cls)
                base = [float(mm.group(2)), float(mm.group(3)), float(z.group(1))]
                assert np.abs(np.array(base) - np.array(G['off'])).max() < 1e-3, (f, cls, 'not at the base placement', base)
                assert not re.search(r'(Angle|Pitch|Roll)Offset', body), (f, cls)
                nb = body[:z.start()] + body[z.end():]; ind = mm.group(1)
                body = nb.replace(mm.group(0), ind + PL.format(i=ind) + '\n', 1); count[(f, cls)] = count.get((f, cls), 0) + 1
            out.append(tx[last:m.start()]); out.append(body); last = m.end()
        out.append(tx[last:]); wr(f, ''.join(out))
    if G.get('blocks'): assert count == G['blocks'], count
    for k, n in sorted(count.items()): note('MODELDEF', k[0], k[1], 'x%d' % n)
    return count

# ---------------------------------------------------------------- 2. gunmoves (Pivot + fire rows of the gun's handtable row)
def gunmoves(G, p, tag):
    tx = rd('zscript/rsq/gunmoves.zs'); row = G['row']
    spr = re.findall(r'"([^"]+)"', first(r'static const String spr\[\] = \{([^}]*)\}', tx, 'spr').group(1))
    key = [int(v) for v in first(r'static const int key\[\] = \{([^}]*)\}', tx, 'key').group(1).split(',')]
    frows = {}
    for k in range(len(spr)):
        if key[2 * k] == row and key[2 * k + 1] not in frows: frows[key[2 * k + 1]] = spr[k]
    # md3 frame of each row: the gun's bd block FrameIndex for the sprite's first frame letter
    f, cls = G['bdblock']; b = [m.group(0) for m in BLK.finditer(rd(f)) if m.group(1) == cls and '"%s"' % G['names'][0] in m.group(0)][0]
    fi = {(a, c): int(n) for a, c, n in re.findall(r'FrameIndex\s+(\S+)\s+(\S)\s+\d+\s+(\d+)', b)}
    order = sorted(frows); frames = [fi[(frows[r][:4], frows[r][4])] for r in order]
    i0 = tx.index('clearscope static Vector3 Pivot'); i1 = tx.index('};', i0); seg = tx[i0:i1]
    pre, body = seg.split('{ ', 1); vals = [s.strip() for s in body.split(',')]
    old = pivot(G['off'][:2], G['off'][2]); assert np.abs(np.array([float(v) for v in vals[3 * row:3 * row + 3]]) - old).max() < 2e-3, ('pivot', vals[3 * row:3 * row + 3], old)
    new = pivot(p[:2], p[2]); vals[3 * row:3 * row + 3] = ['%.3f' % v for v in new]; tx = tx[:i0] + pre + '{ ' + ', '.join(vals) + ' ' + tx[i1:]
    note('gunmoves Pivot row %d' % row, np.round(old, 3), '->', np.round(new, 3))
    r0 = fire_rows(G, G['off'], (0, 0, 0), frames); r1 = fire_rows(G, p[:3], p[3:], frames)
    i0 = tx.index('static Vector3, Vector3 Frame('); head = tx[:i0]; rest = tx[i0:]
    lines = rest.split('\n'); rx = re.compile(r'^(\s*)(-?\d+\.\d+(?:, -?\d+\.\d+){5}),?(.*)$'); idx = [n for n, l in enumerate(lines) if rx.match(l)]
    for r, a, b in zip(order, r0, r1):
        n = idx[r]; m = rx.match(lines[n]); shipped = np.array([float(v) for v in m.group(2).split(',')])
        assert np.abs(shipped - a).max() < 0.011, ('row %d: the original placement does not reproduce the shipped row' % r, shipped, a.round(2))
        cm = ',' if lines[n][m.end(2):m.end(2) + 1] == ',' else ''	# r12: the table's LAST row has no comma (Chain_saw row 182: a trailing comma is a ZScript error)
        lines[n] = '%s%s%s\t// %s: row %d %s, refitted for the moved gun' % (m.group(1), ', '.join('%.2f' % z0(v, 0.005) for v in b), cm, tag, r, G['cls'])
        note('gunmoves row %d (%s, md3 frame %d)' % (r, frows[r], frames[order.index(r)]), m.group(2), '->', ', '.join('%.2f' % z0(v, 0.005) for v in b))
    wr('zscript/rsq/gunmoves.zs', head + '\n'.join(lines))

# ---------------------------------------------------------------- 3. reload tables
def case_rx(fn, case): return r'( %s\(int i\)\s*\{.*?\t\tcase %d:\treturn )\(([^)]*)\);' % (fn, case)
def getcase(tx, fn, case):
    m = re.search(case_rx(fn, case), tx, re.S); return (np.array([float(s) for s in m.group(2).split(',')]), '(%s)' % m.group(2)) if m else (None, None)
def setcase(tx, fn, case, old, new, tag):
    a = '\t\tcase %d:\treturn %s;' % (case, old); b = '\t\tcase %d:\treturn %s;\t// %s: moved with the gun to the FBX hand (was %s)' % (case, new, tag, old)
    i0 = tx.index(' %s(int i)' % fn); i1 = tx.index('\n\t}', i0); seg = tx[i0:i1]; assert seg.count(a) == 1, (fn, case, a)
    note('reload %s case %d' % (fn, case), old, '->', new); return tx[:i0] + seg.replace(a, b) + tx[i1:]
def rsr(G, p, R, t, tag):
    tx = rd('zscript/rsr/rsr_guns.bd.zs'); c = G['rsr']; pt = lambda q: R @ q + t
    for fn in ('Well', 'MagCentre', 'Grab'):
        v, s = getcase(tx, fn, c)
        if v is not None: tx = setcase(tx, fn, c, s, v3(pt(v)), tag)
    ax, s = getcase(tx, 'Axis', c); ax1 = R @ ax; tx = setcase(tx, 'Axis', c, s, v3(ax1), tag)
    v, s = getcase(tx, 'WellHook', c); tx = setcase(tx, 'WellHook', c, s, v3(np.linalg.norm(v) * np.array([-ax1[1], -ax1[2], ax1[0]])), tag)	# r9: keep the row's length (1 / mesh scale on scaled meshes: Sniper 0.0954, M32 1.613)
    pu, s = getcase(tx, 'Pull', c)
    if pu is not None:
        pu1 = R @ pu; tx = setcase(tx, 'Pull', c, s, v3(pu1), tag)
        v, s = getcase(tx, 'HandleHook', c); tx = setcase(tx, 'HandleHook', c, s, v3(np.linalg.norm(v) * np.array([pu1[1], pu1[2], -pu1[0]])), tag)	# r9: keep the row's length
    v, s = getcase(tx, 'Offset', c); assert np.abs(v - np.array(G['off'])).max() < 1e-3, ('reload Offset is not the base', v)
    tx = setcase(tx, 'Offset', c, s, '(%.3f, %.3f, %.3f)' % tuple(p[:3]), tag)
    wr('zscript/rsr/rsr_guns.bd.zs', tx)
def rsb(G, p, R, t, tag):
    """break-open table rows (rsb_guns.zs, switch/case): gun-frame points (Hinge, Casing) move, the hinge Axis turns, Offset = the
    new placement. The Hand0..HandTip rows are the off-hand's hold of the round (hand frame): kept, as rsr's TopInHand / HandHook."""
    tx = rd('zscript/rsr/rsb_guns.zs')
    for fn, kind in (('Hinge', 'p'), ('Axis', 'd'), ('Casing', 'p'), ('Offset', 'o')):
        i0 = tx.index(' %s(int i)' % fn); i1 = tx.index('\n\t}', i0); seg = tx[i0:i1]
        for c in G['rsb']:
            m = re.search(r'\t\tcase %d:\treturn \(([^)]*)\);' % c, seg); assert m, (fn, c)
            v = np.array([float(x) for x in m.group(1).split(',')])
            if kind == 'o': assert np.abs(v - np.array(G['off'])).max() < 1e-3, ('rsb Offset not the base', c, v)
            nv = R @ v + t if kind == 'p' else R @ v if kind == 'd' else np.array(p[:3])
            new = '\t\tcase %d:\treturn (%.4f, %.4f, %.4f);\t// %s: moved with the gun to the FBX hand (was %s)' % ((c,) + tuple(z0(x, 5e-5) for x in nv) + (tag, m.group(1)))
            seg = seg.replace(m.group(0), new, 1); note('reload rsb %s case %d' % (fn, c), m.group(1), '->', '%.4f, %.4f, %.4f' % tuple(nv))
        tx = tx[:i0] + seg + tx[i1:]
    # chamber bores turn with the gun (Rest0-2 / RestT are the identity motion of parts drawn in place: unchanged under the conjugation)
    i0 = tx.index(' Bore(int i, int k)'); i1 = tx.index('\n\t}', i0); seg = tx[i0:i1]
    for c in G['rsb']:
        for k in range(8):
            m = re.search(r'\t\tcase %d:\treturn \(([^)]*)\);' % (c * 8 + k), seg)
            if not m: continue
            v = np.array([float(x) for x in m.group(1).split(',')]); nv = R @ v
            seg = seg.replace(m.group(0), '\t\tcase %d:\treturn (%.4f, %.4f, %.4f);\t// %s: turned with the gun (was %s)' % ((c * 8 + k,) + tuple(z0(x, 5e-5) for x in nv) + (tag, m.group(1))), 1)
            note('reload rsb Bore gun %d chamber %d' % (c, k), m.group(1), '->', '%.4f, %.4f, %.4f' % tuple(nv))
    tx = tx[:i0] + seg + tx[i1:]
    # the round in the off hand: seated point (now drawn moved, M x) -> hold. g' = g R^T, HandT' = HandT - g' t keeps the hold unchanged
    def getc(fn, c):
        i0 = tx.index(' %s(int i)' % fn); i1 = tx.index('\n\t}', i0); m = re.search(r'\t\tcase %d:\treturn \(([^)]*)\);' % c, tx[i0:i1])
        return np.array([float(x) for x in m.group(1).split(',')]), m.group(0), m.group(1)
    for c in G['rsb']:
        g = np.array([getc('Hand%d' % r, c)[0] for r in range(3)]); g1 = g @ R.T; hT = getc('HandT', c)[0]; hT1 = hT - g1 @ t
        for fn, nv in (('Hand0', g1[0]), ('Hand1', g1[1]), ('Hand2', g1[2]), ('HandT', hT1)):
            v, line, old = getc(fn, c); i0 = tx.index(' %s(int i)' % fn)
            new = '\t\tcase %d:\treturn (%.4f, %.4f, %.4f);\t// %s: the hold of the round re-expressed for the moved gun (was %s)' % ((c,) + tuple(z0(x, 5e-5) for x in nv) + (tag, old))
            tx = tx[:i0] + tx[i0:].replace(line, new, 1); note('reload rsb %s case %d' % (fn, c), old, '->', '%.4f, %.4f, %.4f' % tuple(nv))
    wr('zscript/rsr/rsb_guns.zs', tx)

# ---------------------------------------------------------------- 4. casing port, muzzle, scope
def casing(G, R, t, tag):
    tx = rd('zscript/rsq/casings.zs')
    for k in ('casing', 'casing2'):
        if not G.get(k): continue
        m = first(r"\t\tif \(w is '%s'\)(\t+)return \(([^)]*)\);([^\n]*)" % G[k], tx, 'casing ' + G[k])
        v = np.array([float(s) for s in m.group(2).split(',')]); nv = R @ v + t
        new = "\t\tif (w is '%s')%sreturn (%.1f, %.1f, %.1f);\t// %s: moved with the gun to the FBX hand (was %s)%s" % (G[k], m.group(1), nv[0], nv[1], nv[2], tag, m.group(2), m.group(3))
        tx = tx.replace(m.group(0), new, 1); note('casing port', G[k], m.group(2), '->', '%.1f, %.1f, %.1f' % tuple(nv))
    wr('zscript/rsq/casings.zs', tx)
def muzzle(G, R, t, tag):
    tx = rd('zscript/rsq/muzzle.zs'); c = G['cls']
    m = re.search(r"\t\tif \((?:w is|n ==) '%s'\)\treturn \(([^)]*)\);[^\n]*" % c, tx)
    if m:
        v = np.array([float(s) for s in m.group(1).split(',')]); nv = R @ v + t
        tx = tx.replace(m.group(0), m.group(0).split('\treturn')[0] + '\treturn (%.2f, %.2f, %.2f);\t// %s: moved with the gun to the FBX hand (was %s)' % (tuple(nv) + (tag, m.group(1))), 1)
        note('muzzle row', c, m.group(1), '->', '%.2f, %.2f, %.2f' % tuple(nv))
    else:
        V = chain(G['scale'], G['off'], (0, 0, 0))(raw(G['md3'], G['ready'], G.get('muzzle_surf'))); f = V[:, 0].max(); S = V[V[:, 0] > f - 0.3]
        v = np.array([f, (S[:, 1].min() + S[:, 1].max()) / 2, (S[:, 2].min() + S[:, 2].max()) / 2]); nv = R @ v + t
        a = "\t\treturn (0, 0, 0);\n\t}"; assert tx.count(a) == 1, 'muzzle anchor'
        tx = tx.replace(a, "\t\t// %s: %s's drawn muzzle (front-most face centre of the ready frame, %.2f %.2f %.2f before the move), moved with the gun\n\t\tif (w is '%s')\treturn (%.2f, %.2f, %.2f);\n" % ((tag, c) + tuple(v) + (c,) + tuple(nv)) + a, 1)
        note('muzzle row ADDED', c, 'drawn tip', v.round(2), '->', nv.round(2))
    wr('zscript/rsq/muzzle.zs', tx)
def scope(G, R, t, tag):
    tx = rd('zscript/rsq/scope.zs'); i = G['scope']
    for fn, kind in (('Lens', 'p'), ('Axis', 'd')):
        i0 = tx.index('static Vector3 %s(int i)' % fn); i1 = tx.index('return', i0); seg = tx[i0:i1]
        cols = [[s.strip() for s in re.search(r'static const double %s\[\] = \{([^}]*)\};' % n, seg).group(1).split(',')] for n in 'flu']
        v = np.array([float(cols[k][i]) for k in range(3)]); nv = R @ v + t if kind == 'p' else R @ v
        fmt = '%.3f' if kind == 'p' else '%.4f'
        for k in range(3): cols[k][i] = fmt % z0(nv[k])
        s2 = seg
        for k, n in enumerate('flu'):
            s2 = re.sub(r'(static const double %s\[\] = \{ )([^}]*)( \};)' % n, lambda mm: mm.group(1) + ', '.join(cols[k]) + mm.group(3), s2, count=1)
        tx = tx[:i0] + s2 + '\t\t// %s: %s %d moved with the gun to the FBX hand (was %s)\n\t\t' % (tag, fn, i, ' '.join('%.4f' % x for x in v)) + tx[i1:]
        note('scope %s %d' % (fn, i), v.round(4), '->', nv.round(4))
    wr('zscript/rsq/scope.zs', tx)

# ---------------------------------------------------------------- 5. the Rifle's M203 (its tables stay in the ORIGINAL frame; ToGun/FromGun carry points across)
def m203(G, p, R, t, tag):
    tx = rd('zscript/rsr/rsr_m203_geo.zs'); fw = R @ np.array([1.0, 0, 0]); fh = [-fw[1], -fw[2], -fw[0]] if False else [fw[1], fw[2], -fw[0]]
    old = 'clearscope static Vector3 FwdHook(int gun) { return gun == 2 ? (0.0000, 0.0000, -1.0000) : (0.0000, 0.0000, -1.0000); }'
    Ri = R.T; ti = -R.T @ t
    aff = lambda M, b, s: '(' + ', '.join(' + '.join('%.6f * %s.%s' % (M[r, c], s, 'xyz'[c]) for c in range(3)).replace('+ -', '+ -') + ('' if b is None else ' + %.6f' % b[r]) for r in range(3)) + ')'
    new = ('clearscope static Vector3 FwdHook(int gun) { return gun == 2 ? (0.0000, 0.0000, -1.0000) : (%.4f, %.4f, %.4f); }\t// %s: the rifle\'s forward axis after its move to the FBX hand (was 0 0 -1)\n'
           '\t// %s (lane B): the rifle (gun 1) is drawn moved to the FBX hand (MODELDEF Offset %.3f %.3f, ZOffset %.3f, Angle/Pitch/Roll %.3f/%.3f/%.3f).\n'
           '\t// The numbers above stay in its ORIGINAL controller frame: ToGun takes a moved-frame point there, FromGun brings one back.\n'
           '\tclearscope static Vector3 ToGun(int gun, Vector3 p)\n\t{\n\t\tif (gun != 1) return p;\n\t\treturn %s;\n\t}\n'
           '\tclearscope static Vector3 DirToGun(int gun, Vector3 v)\n\t{\n\t\tif (gun != 1) return v;\n\t\treturn %s;\n\t}\n'
           '\tclearscope static Vector3 FromGun(int gun, Vector3 p)\n\t{\n\t\tif (gun != 1) return p;\n\t\treturn %s;\n\t}') % (
           tuple(fh) + (tag, tag) + tuple(p) + (aff(Ri, ti, 'p'), aff(Ri, None, 'v'), aff(R, t, 'p')))
    tx = sub1(tx, old, new, 'FwdHook'); wr('zscript/rsr/rsr_m203_geo.zs', tx); note('M203 FwdHook', np.round(fh, 4), '+ ToGun / DirToGun / FromGun (R, t of this move)')
    tx = rd('zscript/rsr/rsr_m203.zs')
    for a, b in (('palm = geo.OffPoint(RSR.PalmGrab());', 'palm = RSM_Geo.ToGun(gun, geo.OffPoint(RSR.PalmGrab()));\t// %s: in the rifle\'s original frame' % tag),
                 ('Vector3 mid = geo.OffPoint(RSM_Geo.RoundInHand());', 'Vector3 mid = RSM_Geo.ToGun(gun, geo.OffPoint(RSM_Geo.RoundInHand()));\t// %s: in the rifle\'s original frame' % tag),
                 ('Vector3 nose = geo.OffDirInGun(RSM_Geo.RoundAxisInHand());', 'Vector3 nose = RSM_Geo.DirToGun(gun, geo.OffDirInGun(RSM_Geo.RoundAxisInHand()));'),
                 ('Vector3 pos = RSVR_VRHand.HandPos(mo) + geo.FromGun(at);', 'Vector3 pos = RSVR_VRHand.HandPos(mo) + geo.FromGun(RSM_Geo.FromGun(gun, at));\t// %s: the moved breech' % tag)):
        tx = sub1(tx, a, b, a); note('M203 rsr_m203.zs:', a.split('=')[0].strip(), 'via ToGun/FromGun')
    wr('zscript/rsr/rsr_m203.zs', tx)
    # the purist rifle (no launcher): its handguard support hook moves with the gun
    tx = rd('zscript/rsq/hands.zs'); a = '\t\t\thook = (-0.090, -1.390, 11.380);\t// 1.30: purist\'s rifle (no launcher): the handguard grip as before\n\t\t\thookTurn = (0, 0, 0);'
    h, r = support_move(G, (-0.090, -1.390, 11.380), (0, 0, 0), R, t, None, 1)	# Ermac hand2 pose B
    tx = sub1(tx, a, '\t\t\thook = (%.3f, %.3f, %.3f);\t// %s: purist\'s rifle (no launcher): the handguard grip, moved with the gun (was -0.090, -1.390, 11.380 / 0 0 0)\n\t\t\thookTurn = (%.3f, %.3f, %.3f);' % (tuple(h) + (tag,) + tuple(r)), 'purist hook')
    wr('zscript/rsq/hands.zs', tx); note('purist rifle support hook', '(-0.090, -1.390, 11.380)/0 ->', np.round(h, 3), np.round(r, 3))

# ---------------------------------------------------------------- 6. support pose moved rigidly with the gun (supmove_b4 / hook.py)
def support_move(G, h0, r0, R, t, md3=None, frame=None):
    import hook
    hand2 = os.path.join(SRC, 'models/rsq/hand2.md3'); xyz = md3_frames(hand2)[0][frame]
    draw = lambda h, r: 100 * (hudrender.to_local(xyz, dict(hook=list(h), rot=list(r), **hook.PL)) @ hook.P.T)
    Y0 = draw((0, 0, 0), (0, 0, 0)); Y1 = draw(h0, r0); R0, t0 = kabsch(Y0, Y1)
    h, r = hook.hook_from_rigid(R @ R0, R @ t0 + t); return np.array(h), np.array(r)

# ---------------------------------------------------------------- 7. FBX gun-hand wiring (optional "hand" in fit.json)
def setrow(tx, fn, vals, row, fmt='%.3f'):
    i0 = tx.index('static Vector3 %s(int i)' % fn); i1 = tx.index('}', tx.index('return', i0)); seg = tx[i0:i1]; k = [0]
    def z(m):
        v = [s.strip() for s in m.group(2).split(',')]; v[row] = fmt % vals[k[0]]; k[0] += 1; return m.group(1) + ', '.join(v) + m.group(3)
    seg2, n = re.subn(r'(static const double [xyz]\[\] = \{ )([^}]*)( \};)', z, seg); assert n == 3, fn
    return tx[:i0] + seg2 + tx[i1:]
def getrow(tx, fn, row):
    i0 = tx.index('static Vector3 %s(int i)' % fn); i1 = tx.index('}', tx.index('return', i0))
    return np.array([float([s.strip() for s in a.split(',')][row]) for a in re.findall(r'static const double [xyz]\[\] = \{ ([^}]*) \};', tx[i0:i1])])
def hand(G, H, R, t, tag, fitdir):
    row = G['row']; spr = H['sprite']; md3 = H['md3_name']; L = H['label']; c = G['cls']
    COPIES.append((os.path.join(fitdir, H['md3']), os.path.join(SRC, 'models/rsq/fbx', md3)))
    note('hand md3', md3, '<-', H['md3'])
    FR = '\tFrameIndex %s A 0 0\t// %s, finger on the trigger\n\tFrameIndex %s B 0 1\t// %s, squeezed\n' % (spr, c, spr, c)
    hb = lambda cls: 'Model %s\n{\n\tPath "models/rsq/fbx"\n\tModel 0 "%s"\n\tSkin 0 "fbx_hand.png"\n\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n%s}\n' % (cls, md3, FR)
    Hd = '\n// %s (lane B): %s (row %d) holds the FBX gun hand fitted from 1.92\'s %s hold (frames baked in place, hook 0)\n' % (tag, c, row, c)
    wr('MODELDEF.rsq', rd('MODELDEF.rsq').rstrip('\n') + '\n' + Hd + hb('RSQ_GunSide') + hb('RSQ_Hands')); note('hand blocks MODELDEF.rsq RSQ_GunSide, RSQ_Hands', spr)
    for f, cls in G['dual']:
        wr(f, rd(f).rstrip('\n') + '\n' + Hd.replace('(row %d)' % row, '(row %d), dual wield' % row) + hb(cls)); note('hand block (dual)', f, cls)
    tx = rd('zscript/rsq/hands.zs')
    a = '\tFist: RQGF A -1; Stop;'; tx = sub1(tx, a, '\t// %s: %s (row %d)\n\tFbxTrg%s: %s A -1; Stop;\n\tFbxSqz%s: %s B -1; Stop;\n' % (tag, c, row, L, spr, L, spr) + a, 'states')
    m = first(r'\t\tif \(i == \d+\)\t// batch \d: \w+ squeezes', tx, 'gun label anchor')
    tx = tx[:m.start()] + ('\t\tif (i == %d' + H.get('cond', '') + ')\t// %s: %s squeezes on its %s or fullbright, trigger otherwise\n\t\t{\n\t\t\tbool msq = false;\n'
        '\t\t\tlet mgp = p.FindPSprite(PSP_WEAPON);\n\t\t\tif (mgp && mgp.CurState)\n\t\t\t{\n\t\t\t\tint mf = mgp.Frame;\n\t\t\t\tmsq = mgp.CurState.bFullbright || %s;\n\t\t\t}\n'
        '\t\t\tgl = msq ? "FbxSqz%s" : "FbxTrg%s";\n\t\t}\n') % (row, tag, c, H.get('squeeze_note', 'FIRE frames (gunmoves rows)'), H['squeeze'], L, L) + tx[m.start():]
    m = list(re.finditer(r'\tDFbx\w+: \w+ B -1; Stop;\n', tx)); assert m, 'dual states anchor'; e = m[-1].end()	# after the last dual FBX state
    tx = tx[:e] + '\tDFbxTrg%s: %s A -1; Stop;\t// %s: dual wield, %s\n\tDFbxSqz%s: %s B -1; Stop;\n' % (L, spr, tag, c, L, spr) + tx[e:]
    if H.get('support') and H['support'] != 'move':	# the FBX palm-under replaces the Ermac support pose; 'move' keeps the gun's own pose
        m = first(r'\t\tif \(i == \d+\)\n\t\t\tspl = "FbxSupF";', tx, 'support anchor')
        tx = tx[:m.start()] + '\t\tif (i == %d)\n\t\t\tspl = "FbxSupF";\t// %s: %s, the FBX open palm under its barrel (handtable SupportHook / SupportRot row %d)\n' % (row, tag, c, row) + tx[m.start():]
    wr('zscript/rsq/hands.zs', tx); note('hands.zs labels FbxTrg%s / FbxSqz%s (+ dual)' % (L, L))
    if G['dual']:
        tx = rd('zscript/rsq/dualhands.zs'); m = first(r'\t\t\t\tif \(i == \d+\)\t// batch', tx, 'dual label anchor')
        tx = tx[:m.start()] + ('\t\t\t\tif (i == %d' + H.get('dcond', H.get('cond', '')) + ')\t// %s: %s\n\t\t\t\t\tlabel = firing ? "DFbxSqz%s" : "DFbxTrg%s";\n') % (row, tag, c, L, L) + tx[m.start():]
        wr('zscript/rsq/dualhands.zs', tx); note('dualhands.zs label')
    tx = rd('zscript/rsq/handtable.zs')
    tx = setrow(tx, 'GunHook', (0, 0, 0), row); tx = setrow(tx, 'GunHookTwo', (0, 0, 0), row); note('handtable GunHook / GunHookTwo row %d = 0' % row)
    S = H.get('support')
    if S == 'move':	# the existing support pose rides with the gun
        h0 = getrow(tx, 'SupportHook', row); r0 = getrow(tx, 'SupportRot', row); sp = getrow(tx, 'SupportPoint', row)
        h, r = support_move(G, h0, r0, R, t, None, H.get('support_frame', 0)); sp1 = (R @ (sp * 100) + t) / 100
        tx = setrow(tx, 'SupportHook', h, row); tx = setrow(tx, 'SupportRot', r, row); tx = setrow(tx, 'SupportPoint', sp1, row)
        note('handtable Support row %d moved with the gun' % row, 'hook', h0, '->', np.round(h, 3), 'rot', r0, '->', np.round(r, 3), 'point', sp, '->', np.round(sp1, 3))
    elif S:
        tx = setrow(tx, 'SupportHook', S['sup_hook'], row); tx = setrow(tx, 'SupportRot', S['sup_rot'], row); tx = setrow(tx, 'SupportPoint', S['sup_point_m'], row)
        note('handtable Support row %d' % row, S['sup_hook'], S['sup_rot'], S['sup_point_m'])
    if S:
        m = first(r'\t// batch \d: row \d+ \(', tx, 'support comment anchor')
        tx = tx[:m.start()] + '\t// %s: row %d (%s) = %s\n' % (tag, row, c, H.get('support_note', 'the support pose moved with the gun')) + tx[m.start():]
    wr('zscript/rsq/handtable.zs', tx)

# ---------------------------------------------------------------- 8. FBX support hand on an already ported gun (batch 5, support_gun.py's solve)
def support_only(G, S, tag):
    """Writes support_gun.py's sup_hook / sup_rot / sup_point_m into the gun's handtable row and selects the FBX support
    label (FbxSupF = RQFS B palm under, FbxSupP = RQFS A cup) in hands.zs. 'purist': the purist rifle's own hook (no launcher)."""
    row = G['row']; c = G['cls']; lab = 'FbxSupF' if S['pose'] == 'B' else 'FbxSupP'
    what = 'the FBX open palm under its handguard / M203' if S['pose'] == 'B' else 'the FBX cup under the gun hand'
    tx = rd('zscript/rsq/hands.zs')
    if S.get('purist'):
        m = re.search(r'\t\t\thook = \(([-\d., ]+)\);\t// batch 4: purist\'s rifle[^\n]*\n\t\t\thookTurn = \(([-\d., ]+)\);', tx); assert m, 'purist hook'
        tx = tx[:m.start()] + '\t\t\thook = (%.3f, %.3f, %.3f);\t// %s: purist\'s rifle (no launcher): the FBX palm under its handguard (RQFS B, support_gun.py)\n\t\t\thookTurn = (%.3f, %.3f, %.3f);' % (tuple(S['sup_hook']) + (tag,) + tuple(S['sup_rot'])) + tx[m.end():]
        assert re.search(r'\t\tif \(i == 18\)\n\t\t\tspl = "FbxSupF";', tx), 'run the Rifle --support first: its row 18 label (FbxSupF) covers the purist rifle too'
        wr('zscript/rsq/hands.zs', tx); note('hands.zs purist rifle hook', S['sup_hook'], S['sup_rot'], '(label FbxSupF: row 18)'); return
    m = first(r'\t\tif \(i == \d+\)\n\t\t\tspl = "FbxSupF";', tx, 'support anchor')
    cond = 'i == %d' % row + S.get('cond', '')
    tx = tx[:m.start()] + '\t\tif (%s)\n\t\t\tspl = "%s";\t// %s: %s, %s (handtable SupportHook / SupportRot row %d)\n' % (cond, lab, tag, c, what, row) + tx[m.start():]
    wr('zscript/rsq/hands.zs', tx); note('hands.zs support label', cond, lab)
    tx = rd('zscript/rsq/handtable.zs')
    tx = setrow(tx, 'SupportHook', S['sup_hook'], row); tx = setrow(tx, 'SupportRot', S['sup_rot'], row); tx = setrow(tx, 'SupportPoint', S['sup_point_m'], row)
    m = first(r'\t// [\w ]+: row \d+ \(', tx, 'support comment anchor')
    tx = tx[:m.start()] + '\t// %s: row %d (%s) = %s (RQFS %s) at 1.92\'s SupportPoint moved with the gun (support_gun.py)\n' % (tag, row, c, what, S['pose']) + tx[m.start():]
    wr('zscript/rsq/handtable.zs', tx); note('handtable Support row %d' % row, S['sup_hook'], S['sup_rot'], S['sup_point_m'])

# ---------------------------------------------------------------- main
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cls'); ap.add_argument('fit'); ap.add_argument('--src'); ap.add_argument('--tag', default='batch 4'); ap.add_argument('--dry', action='store_true'); ap.add_argument('--support', help='support_gun.py json: only the FBX support hand on the already ported gun')
    ARGS = ap.parse_args()
    if ARGS.src: SRC = os.path.abspath(ARGS.src)
    G = dict(GUNS[ARGS.cls], cls=ARGS.cls); G['md3'] = os.path.join(SRC, G['md3'])
    if ARGS.support:
        support_only(G, json.load(open(ARGS.support)), ARGS.tag); flush(); print('moved %d items%s' % (len(MOVED), ' (dry run: nothing written)' if ARGS.dry else '')); sys.exit(0)
    F = json.load(open(ARGS.fit)); fitdir = os.path.dirname(os.path.abspath(ARGS.fit))
    if 'place' in F: p = np.array(F['place'], float); res = None
    else:
        p, res, R0, t0 = place(G, F['shift'])
    R, t = rigid_move(G, p)
    print('%s: MODELDEF Offset %.3f %.3f  ZOffset %.3f  Angle/Pitch/Roll %.3f/%.3f/%.3f' % ((ARGS.cls,) + tuple(p)), '' if res is None else '(chain residual %.4f cm)' % res)
    gun_blocks_cache = {ARGS.cls: gun_blocks(G)}
    modeldef(G, p, ARGS.tag)
    if G.get('row') is not None and G.get('bdblock'): gunmoves(G, p, ARGS.tag)
    else: note('gunmoves: no handtable row / bd block for %s: rows NOT moved (flag)' % ARGS.cls)
    if G.get('rsr'): rsr(G, p, R, t, ARGS.tag)
    if G.get('rsb'): rsb(G, p, R, t, ARGS.tag)
    if G.get('casing'): casing(G, R, t, ARGS.tag)
    if not F.get('no_muzzle'): muzzle(G, R, t, ARGS.tag)
    if G.get('scope'): scope(G, R, t, ARGS.tag)
    if G.get('m203'): m203(G, p, R, t, ARGS.tag)
    if F.get('hand'): hand(G, F['hand'], R, t, ARGS.tag, fitdir)
    flush()
    print('moved %d items%s' % (len(MOVED), ' (dry run: nothing written)' if ARGS.dry else ''))
    json.dump(dict(cls=ARGS.cls, place=list(p), R=R.tolist(), t=t.tolist(), moved=MOVED), open(os.path.join(fitdir, 'ported_%s.json' % ARGS.cls), 'w'), indent=1)
