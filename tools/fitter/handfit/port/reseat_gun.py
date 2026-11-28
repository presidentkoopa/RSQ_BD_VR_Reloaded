"""reseat_gun.py <Class> <fit.json> [--src DIR] [--tag TEXT] [--dry]   (r12 port lane)

A gun ALREADY ported (fits/ported_<Class>.json: its placement p_old, R_old, t_old) gets a new fit of its gun hand (e.g. the r4
dense re-fits of BFG10k / NukeLauncher). Same one method: the wrist stays pinned, the GUN moves again, from p_old to the new
placement p_new (port_gun.place of the fit's `shift`, or its `place`), and every table that hangs off the gun moves with it by the
relative move  x -> Rrel x + trel,  Rrel = R_new R_old^T, trel = t_new - Rrel t_old  (both moves from the gun's ORIGINAL frame):
  - every MODELDEF block of the gun's meshes that carries p_old (6 numbers, %.3f, port_gun.modeldef's form) -> p_new
  - gunmoves Pivot row (asserted = pivot(p_old)) and fire rows (asserted to reproduce fire_rows(p_old) to 0.011, refitted at p_new)
  - rsr_guns.bd.zs case (Well / MagCentre / Grab points, Axis, WellHook, Pull, HandleHook keep their length, Offset = p_new[:3])
  - RSQ_Muzzle row (moved), casing port (moved)
  - the FBX gun-hand md3 (same file name, replaced by the fit's bake)
NOT touched (owner / coordinator 2026-10-28): the support rows (handtable SupportHook / SupportRot / SupportPoint, hands.zs support
label): a support lane owns them. Registries: port_gun + heavies/port_hv. Writes fits/ported_<Class>.json (new place, R, t, moved)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, re, sys, json, shutil, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'heavies'))
import port_gun as pg
import port_hv	# noqa: registers GUNS_HV (and its MODELDEF normaliser for the M32)

def line_sub(tx, fn, case, new_vec, tag, what='moved with the gun to the r12 hand'):
    i0 = tx.index(' %s(int i)' % fn); i1 = tx.index('\n\t}', i0); seg = tx[i0:i1]
    m = re.search(r'\t\tcase %d:\treturn \(([^)]*)\);[^\n]*' % case, seg); assert m, (fn, case)
    new = '\t\tcase %d:\treturn %s;\t// %s: %s (was (%s))' % (case, new_vec, tag, what, m.group(1))
    pg.note('reload %s case %d' % (fn, case), m.group(1), '->', new_vec)
    return tx[:i0] + seg.replace(m.group(0), new, 1) + tx[i1:], np.array([float(s) for s in m.group(1).split(',')])

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cls'); ap.add_argument('fit'); ap.add_argument('--src'); ap.add_argument('--tag', default='r12 port'); ap.add_argument('--dry', action='store_true')
    pg.ARGS = ARGS = ap.parse_args()
    if ARGS.src: pg.SRC = os.path.abspath(ARGS.src)
    G = dict(pg.GUNS[ARGS.cls], cls=ARGS.cls); G['md3'] = os.path.join(pg.SRC, G['md3']); pg.CUR = G
    F = json.load(open(ARGS.fit)); fitdir = os.path.dirname(os.path.abspath(ARGS.fit))
    P0 = json.load(open(os.path.join(_DP.FITS, 'ported_%s.json' % ARGS.cls))); p0 = np.array(P0['place'])
    if 'place' in F: p1 = np.array(F['place'], float); res = None
    else: p1, res, _, _ = pg.place(G, F['shift'])
    R0, t0 = pg.rigid_move(G, p0); R1, t1 = pg.rigid_move(G, p1)
    assert np.abs(R0 - np.array(P0['R'])).max() < 1e-9 and np.abs(t0 - np.array(P0['t'])).max() < 1e-9, 'ported json R, t do not match its place'
    Rr = R1 @ R0.T; tr = t1 - Rr @ t0; mv = lambda v: Rr @ np.asarray(v, float) + tr
    ang = np.degrees(np.arccos(np.clip((np.trace(Rr) - 1) / 2, -1, 1)))
    print('%s: MODELDEF %s -> %s %s' % (ARGS.cls, np.round(p0, 3), np.round(p1, 3), '' if res is None else '(chain residual %.4f cm)' % res))
    print('  relative move: turn %.4f deg, translation %s cm (|%.3f|)' % (ang, np.round(tr, 3), np.linalg.norm(tr)))
    old = ['%.3f' % v for v in p0]; new = ['%.3f' % v for v in p1]; names = G['names'] + G.get('names_extra', []); nblk = 0
    # 1. MODELDEF: blocks of the gun's meshes carrying the old moved placement
    import glob
    for f in sorted(glob.glob(os.path.join(pg.SRC, 'MODELDEF*'))):
        f = os.path.basename(f); tx = pg.rd(f); out = []; last = 0; n = 0
        for m in pg.BLK.finditer(tx):
            b = m.group(0)
            if any('"%s"' % nm in b for nm in names) and re.search(r'(?m)^\s*AngleOffset\s+%s\b' % re.escape(old[3]), b):
                o = re.search(r'(?m)^([ \t]*)Offset[ \t]+(\S+)[ \t]+(\S+)[ \t]+0\.0\n', b); z = re.search(r'(?m)^[ \t]*ZOffset[ \t]+(\S+)\n', b)
                a = [re.search(r'(?m)^[ \t]*%sOffset[ \t]+(\S+)' % k, b) for k in ('Angle', 'Pitch', 'Roll')]
                got = [o.group(2), o.group(3), z.group(1)] + [x.group(1) for x in a]
                if got == old:
                    ind = o.group(1); rl = re.search(r'(?m)^[ \t]*RollOffset[^\n]*\n', b)
                    head = b[:o.start()]; tail = b[rl.end():]
                    b = head + '%sOffset %s %s 0.0\n%sZOffset %s\n%sAngleOffset %s\n%sPitchOffset %s\n%sRollOffset %s\t// %s (lane B): gun to the FBX hand fitted from 1.92, re-fitted (r4 dense; was %s)\n' % (
                        ind, new[0], new[1], ind, new[2], ind, new[3], ind, new[4], ind, new[5], ARGS.tag, ' '.join(old)) + tail
                    n += 1
            out.append(tx[last:m.start()]); out.append(b); last = m.end()
        out.append(tx[last:])
        if n: pg.wr(f, ''.join(out)); pg.note('MODELDEF', f, 'x%d' % n); nblk += n
    assert nblk > 0, 'no MODELDEF block carries the ported placement'
    # 2. gunmoves
    tx = pg.rd('zscript/rsq/gunmoves.zs'); row = G['row']
    spr = re.findall(r'"([^"]+)"', pg.first(r'static const String spr\[\] = \{([^}]*)\}', tx, 'spr').group(1))
    key = [int(v) for v in pg.first(r'static const int key\[\] = \{([^}]*)\}', tx, 'key').group(1).split(',')]
    frows = {}
    for k in range(len(spr)):
        if key[2 * k] == row and key[2 * k + 1] not in frows: frows[key[2 * k + 1]] = spr[k]
    f, cls = G['bdblock']; b = [m.group(0) for m in pg.BLK.finditer(pg.rd(f)) if m.group(1) == cls and '"%s"' % G['names'][0] in m.group(0)][0]
    fi = {(a, c): int(n) for a, c, n in re.findall(r'FrameIndex\s+(\S+)\s+(\S)\s+\d+\s+(\d+)', b)}
    order = sorted(frows); frames = [fi[(frows[r][:4], frows[r][4])] for r in order]
    i0 = tx.index('clearscope static Vector3 Pivot'); i1 = tx.index('};', i0); seg = tx[i0:i1]; pre, body = seg.split('{ ', 1); vals = [s.strip() for s in body.split(',')]
    pv0 = pg.pivot(p0[:2], p0[2]); assert np.abs(np.array([float(v) for v in vals[3 * row:3 * row + 3]]) - pv0).max() < 2e-3, ('pivot not at p_old', vals[3 * row:3 * row + 3], pv0)
    pv1 = pg.pivot(p1[:2], p1[2]); vals[3 * row:3 * row + 3] = ['%.3f' % v for v in pv1]; tx = tx[:i0] + pre + '{ ' + ', '.join(vals) + ' ' + tx[i1:]
    pg.note('gunmoves Pivot row %d' % row, np.round(pv0, 3), '->', np.round(pv1, 3))
    r0 = pg.fire_rows(G, p0[:3], p0[3:], frames); r1 = pg.fire_rows(G, p1[:3], p1[3:], frames)
    i0 = tx.index('static Vector3, Vector3 Frame('); head = tx[:i0]; lines = tx[i0:].split('\n')
    rx = re.compile(r'^(\s*)(-?\d+\.\d+(?:, -?\d+\.\d+){5}),?(.*)$'); idx = [n for n, l in enumerate(lines) if rx.match(l)]
    for r, a, c in zip(order, r0, r1):
        n = idx[r]; m = rx.match(lines[n]); shipped = np.array([float(v) for v in m.group(2).split(',')])
        assert np.abs(shipped - a).max() < 0.011, ('row %d: p_old does not reproduce the shipped row' % r, shipped, a.round(2))
        cm = ',' if lines[n][m.end(2):m.end(2) + 1] == ',' else ''	# the table's last row has no comma
        lines[n] = '%s%s%s\t// %s: row %d %s, refitted for the re-fitted gun' % (m.group(1), ', '.join('%.2f' % pg.z0(v, 0.005) for v in c), cm, ARGS.tag, r, G['cls'])
        pg.note('gunmoves row %d (%s, md3 frame %d)' % (r, frows[r], frames[order.index(r)]), m.group(2), '->', ', '.join('%.2f' % pg.z0(v, 0.005) for v in c))
    pg.wr('zscript/rsq/gunmoves.zs', head + '\n'.join(lines))
    # 3. rsr case
    if G.get('rsr'):
        tx = pg.rd('zscript/rsr/rsr_guns.bd.zs'); c = G['rsr']
        for fn in ('Well', 'MagCentre', 'Grab'):
            v, s = pg.getcase(tx, fn, c)
            if v is not None: tx, _ = line_sub(tx, fn, c, pg.v3(mv(v)), ARGS.tag)
        ax, s = pg.getcase(tx, 'Axis', c); ax1 = Rr @ ax; tx, _ = line_sub(tx, 'Axis', c, pg.v3(ax1), ARGS.tag)
        v, s = pg.getcase(tx, 'WellHook', c); tx, _ = line_sub(tx, 'WellHook', c, pg.v3(np.linalg.norm(v) * np.array([-ax1[1], -ax1[2], ax1[0]])), ARGS.tag)
        pu, s = pg.getcase(tx, 'Pull', c)
        if pu is not None:
            pu1 = Rr @ pu; tx, _ = line_sub(tx, 'Pull', c, pg.v3(pu1), ARGS.tag)
            v, s = pg.getcase(tx, 'HandleHook', c); tx, _ = line_sub(tx, 'HandleHook', c, pg.v3(np.linalg.norm(v) * np.array([pu1[1], pu1[2], -pu1[0]])), ARGS.tag)
        v, s = pg.getcase(tx, 'Offset', c); assert np.abs(v - p0[:3]).max() < 1e-3, ('rsr Offset is not p_old', v)
        tx, _ = line_sub(tx, 'Offset', c, '(%.3f, %.3f, %.3f)' % tuple(p1[:3]), ARGS.tag)
        pg.wr('zscript/rsr/rsr_guns.bd.zs', tx)
    # 4. muzzle, casing
    tx = pg.rd('zscript/rsq/muzzle.zs'); m = re.search(r"\t\tif \((?:w is|n ==) '%s'\)\treturn \(([^)]*)\);[^\n]*" % G['cls'], tx); assert m, 'muzzle row'
    v = np.array([float(s) for s in m.group(1).split(',')]); nv = mv(v)
    tx = tx.replace(m.group(0), m.group(0).split('\treturn')[0] + '\treturn (%.2f, %.2f, %.2f);\t// %s: moved with the re-fitted gun (was %s)' % (tuple(nv) + (ARGS.tag, m.group(1))), 1)
    pg.wr('zscript/rsq/muzzle.zs', tx); pg.note('muzzle row', G['cls'], m.group(1), '->', '%.2f, %.2f, %.2f' % tuple(nv))
    if G.get('casing'):
        tx = pg.rd('zscript/rsq/casings.zs'); m = pg.first(r"\t\tif \(w is '%s'\)(\t+)return \(([^)]*)\);([^\n]*)" % G['casing'], tx, 'casing')
        v = np.array([float(s) for s in m.group(2).split(',')]); nv = mv(v)
        tx = tx.replace(m.group(0), "\t\tif (w is '%s')%sreturn (%.1f, %.1f, %.1f);\t// %s: moved with the re-fitted gun (was %s)" % (G['casing'], m.group(1), nv[0], nv[1], nv[2], ARGS.tag, m.group(2)), 1)
        pg.wr('zscript/rsq/casings.zs', tx); pg.note('casing port', m.group(2), '->', np.round(nv, 1))
    # 5. hand md3
    H = F['hand']; src = os.path.join(fitdir, H['md3']); dst = os.path.join(pg.SRC, 'models/rsq/fbx', H['md3_name']); assert os.path.exists(dst), dst
    pg.COPIES.append((src, dst)); pg.note('hand md3', H['md3_name'], '<-', os.path.relpath(src, pg.REPO))
    pg.note('support rows NOT touched (support lane): handtable SupportHook / SupportRot / SupportPoint row %d stay as shipped' % row)
    pg.flush()
    print('moved %d items%s' % (len(pg.MOVED), ' (dry run: nothing written)' if ARGS.dry else ''))
    if not ARGS.dry: json.dump(dict(cls=ARGS.cls, place=list(p1), R=R1.tolist(), t=t1.tolist(), reseated_from=dict(place=list(p0), R=R0.tolist(), t=t0.tolist()), relative=dict(R=Rr.tolist(), t=tr.tolist(), turn_deg=ang), moved=pg.MOVED),
                             open(os.path.join(_DP.FITS, 'ported_%s.json' % ARGS.cls), 'w'), indent=1)
