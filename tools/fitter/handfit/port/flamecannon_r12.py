"""flamecannon_r12.py <fc_place.json> <sup_FlameCannon_under40.json> [--tag TEXT] [--dry]   (r12 port lane)

FlameCannon (owner items 21 / 29): worn on the arm, NO gun hand drawn. The wrist is pinned and the cannon moves so the wrist sits at
the rear flesh slit with the housing along the forearm (hands r4 r4/fc_place.py: MODELDEF place, exact). Its support is the hands r4
open palm under the barrel (sup_r4.py 'under', FlameCannon_under40).
FlameCannon had NO handtable row (RSQ_HandTable.Index 0: no hand layers at all), so this adds row 28:
  - handtable.zs: Index 'FlameCannon' (PuristFlameCannon inherits: `is`) -> 28; every per-row table gets a 29th entry: GunOne / GunTwo /
    Trigger "" (no gun hand is drawn: hands.zs shows "Hidden" for g == ""), Support "B" (non-empty, so the support layer can show),
    hooks / rotations 0; the support row is written by support_md3.wire
  - gunmoves.zs Pivot: row 27 (Machinegun, had none: (0, 0, 0) kept) and row 28 = the base pivot (0, 5, 24), then moved by the port
Then the one method's port (port_gun / port_hv functions): every gun-controller MODELDEF block of FlameCannon.md3 (bd + purist), the
Pivot row; no rsr / rsb case, no casing, no fire rows in gunmoves. RSQ_Muzzle: a row ADDED at the drawn NOZZLE TIP, moved with the gun:
the tip = the bore axis (fc_place's bore-face centre line, L/U) at the front lip of the nozzle ring (the furthest vertex 4-6 cm from the
bore axis), measured on the ready frame. The flame spawn (zscript/rsq/flamespout.zs) takes the same tip (edited by hand, numbers from here)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, re, sys, json, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'heavies'))
import port_gun as pg
import port_hv	# noqa
import support_md3
ROW = 28

def add_row(tag):
    tx = pg.rd('zscript/rsq/handtable.zs')
    a = "\t\tif (w is 'Machinegun')\treturn 27;"; i = tx.index(a); e = tx.index('\n', i)
    tx = tx[:e] + "\n\t\tif (w is 'FlameCannon')\treturn %d;\t// %s: the arm-worn FlameCannon (owner item 21): no gun hand, its support hand only" % (ROW, tag) + tx[e:]
    STR = {'GunOne': '""', 'GunTwo': '""', 'Support': '"B"', 'Trigger': '""'}
    def fix(m):
        fn = m.group(1); body = m.group(2)
        out = []
        for mm in re.finditer(r'(static const (String|double) (\w+)\[\] = \{ )([^}]*)( \};)', body):
            pass
        def arr(am):
            vals = [v.strip() for v in am.group(4).split(',')]; assert len(vals) == ROW, (fn, len(vals))
            vals.append(STR[fn] if am.group(2) == 'String' else '0.000'); return am.group(1) + ', '.join(vals) + am.group(5)
        return m.group(0).replace(body, re.sub(r'(static const (String|double) (\w+)\[\] = \{ )([^}]*)( \};)', arr, body))
    n0 = tx.count('static const'); tx2 = re.sub(r'clearscope static \w+ (\w+)\(int i\)\s*\{(.*?)\n\t\}', fix, tx, flags=re.S)
    assert tx2.count('static const') == n0; pg.wr('zscript/rsq/handtable.zs', tx2); pg.note('handtable row %d added (Index FlameCannon, %d tables)' % (ROW, n0))
    tx = pg.rd('zscript/rsq/gunmoves.zs'); i0 = tx.index('clearscope static Vector3 Pivot'); i1 = tx.index('};', i0); seg = tx[i0:i1]; pre, body = seg.split('{ ', 1)
    vals = [s.strip() for s in body.split(',')]; assert len(vals) == 3 * 27, len(vals)
    vals += ['0.000', '0.000', '0.000', '0.000', '5.000', '24.000']
    tx = tx[:i0] + pre + '{ ' + ', '.join(vals) + ' ' + tx[i1:]
    tx = tx.replace('\tclearscope static Vector3 Pivot(int i)', '\t// %s: row 27 (Machinegun) has no pivot: (0, 0, 0), as before; row 28 = FlameCannon (base (0, 5, 24), moved by its port)\n\tclearscope static Vector3 Pivot(int i)' % tag, 1)
    pg.wr('zscript/rsq/gunmoves.zs', tx); pg.note('gunmoves Pivot rows 27 (0 0 0) + 28 (0 5 24) added')

def nozzle_tip(G, P):
    V = pg.chain(G['scale'], G['off'], (0, 0, 0))(pg.raw(G['md3'], G['ready']))
    mu = np.array(P['measured']['muzzle_centre']); ax = np.array(P['measured']['housing_axis'])
    r = np.linalg.norm(np.cross(V - mu, ax), axis=1); ring = V[(r >= 4) & (r < 6)]; f = float(((ring - mu) @ ax).max())
    return mu + f * ax, f

if __name__ == '__main__' and sys.argv[1:2] != ['--fire-rows']:
    ap = argparse.ArgumentParser(); ap.add_argument('place'); ap.add_argument('sup'); ap.add_argument('--tag', default='r12 port'); ap.add_argument('--dry', action='store_true')
    pg.ARGS = A = ap.parse_args()
    P = json.load(open(A.place)); S = json.load(open(A.sup))
    G = dict(pg.GUNS['FlameCannon'], cls='FlameCannon'); G['md3'] = os.path.join(pg.SRC, G['md3']); pg.CUR = G
    p = np.array(P['place']); R, t = pg.rigid_move(G, p)
    assert np.abs(R - np.array(P['R'])).max() < 1e-9 and np.abs(t - np.array(P['t'])).max() < 1e-9, 'fc_place R, t'
    assert np.abs(np.array(S['scenario']['move']['R']) - R).max() < 1e-9 and np.abs(np.array(S['scenario']['move']['t']) - t).max() < 1e-9, 'support solved on another placement'
    print('FlameCannon: MODELDEF Offset %.3f %.3f  ZOffset %.3f  Angle/Pitch/Roll %.3f/%.3f/%.3f (fc_place, residual %.1e cm)' % (tuple(p) + (P['place_residual_cm'],)))
    add_row(A.tag)
    pg.gun_blocks_cache = {'FlameCannon': pg.gun_blocks(G)}
    pg.modeldef(G, p, A.tag)
    pg.gunmoves(G, p, A.tag)
    tip, f = nozzle_tip(G, P); nt = R @ tip + t
    tx = pg.rd('zscript/rsq/muzzle.zs'); a = "\t\treturn (0, 0, 0);\n\t}"; assert tx.count(a) == 1
    tx = tx.replace(a, "\t\t// %s: FlameCannon's drawn NOZZLE TIP (bore axis at the nozzle ring's front lip, %.2f %.2f %.2f before the move; bore-face centre +%.2f cm along the housing axis), moved with the gun (fc_place)\n\t\tif (w is 'FlameCannon')\treturn (%.2f, %.2f, %.2f);\n" % ((A.tag,) + tuple(tip) + (f,) + tuple(nt)) + a, 1)
    pg.wr('zscript/rsq/muzzle.zs', tx); pg.note('muzzle row ADDED FlameCannon nozzle tip', tip.round(2), '->', nt.round(2))
    fwd = R @ np.array(P['measured']['housing_axis']); pg.note('barrel axis after the move (F, L, U)', fwd.round(5), 'vs fc_place forearm axis', P['measured']['forearm_axis'])
    m = S['metrics'] if 'metrics' in S else {}
    support_md3.wire('FlameCannon', S, 'RQXB', 'FbxSupFC', ROW, A.tag, "the FBX open palm cupped under the barrel 38 cm from the slit (hands r4 FlameCannon_under40: pen %.2f, palm gap %.2f; owner-approved 2026-10-28)" % (m.get('pen_gun', float('nan')), m.get('palm_gap', float('nan'))),
                     os.path.join(os.path.dirname(os.path.abspath(A.sup)), S['md3']), S.get('frame', 0))
    pg.flush(); print('moved %d items%s' % (len(pg.MOVED), ' (dry run: nothing written)' if A.dry else ''))
    if not A.dry: json.dump(dict(cls='FlameCannon', place=list(p), R=R.tolist(), t=t.tolist(), nozzle_tip=nt.tolist(), barrel_axis=fwd.tolist(), moved=pg.MOVED), open(os.path.join(_DP.FITS, 'ported_FlameCannon.json'), 'w'), indent=1)

def add_fire_rows(tag='r12 port'):
    """r12 (rig: the support hand stayed put while the cannon kicked): FlameCannon.md3 carries its recoil in model frames 1-6 (vertex
    travel up to 22.6 cm off frame 0), and gunmoves had no rows for it. Adds them for row 28, fitted with port_gun.fire_rows at the
    ported placement (the same fit every other gun's rows use): sprites FLMG / 2LMG frames B C D E (md3 1-4), H J (5), I K (6),
    from MODELDEF.bd.txt FlameCannon's FrameIndex lines."""
    import json as _j
    P = _j.load(open(os.path.join(_DP.FITS, 'ported_FlameCannon.json'))); p = np.array(P['place'])
    G = dict(pg.GUNS['FlameCannon'], cls='FlameCannon'); G['md3'] = os.path.join(pg.SRC, G['md3'])
    tx = pg.rd('zscript/rsq/gunmoves.zs')
    i0 = tx.index('static const double v[] = {'); i1 = tx.index('\t\t};', i0); body = tx[i0:i1]
    nrow = len(re.findall(r'(?m)^\s*-?\d+\.\d+(?:, -?\d+\.\d+){5},?', body)); assert 'FLMG' not in tx
    groups = [('B', 1), ('C', 2), ('D', 3), ('E', 4), ('HJ', 5), ('IK', 6)]; rows = pg.fire_rows(G, p[:3], p[3:], [f for _, f in groups])
    lines = ['\t\t\t%s%s\t// %s: row %d FlameCannon md3 frame %d (FLMG / 2LMG %s), fitted at the ported placement' % (', '.join('%.2f' % pg.z0(v, 0.005) for v in r), ',' if k < len(rows) - 1 else '', tag, nrow + k, f, '/'.join(l), ) for k, ((l, f), r) in enumerate(zip(groups, rows))]
    last = body.rstrip('\n').split('\n')[-1]; assert not last.rstrip().split('//')[0].rstrip().endswith(','), last
    nb = body.rstrip('\n'); cut = nb.rfind('\n') + 1; ll = nb[cut:]; m = re.match(r'^(\s*-?\d+\.\d+(?:, -?\d+\.\d+){5})(.*)$', ll); nb = nb[:cut] + m.group(1) + ',' + m.group(2) + '\n' + '\n'.join(lines) + '\n'
    tx = tx[:i0] + nb + tx[i1:]
    spr_new = []; key_new = []
    for s in ('FLMG', '2LMG'):
        for k, (l, f) in enumerate(groups): spr_new.append('"%s%s"' % (s, l)); key_new += [str(ROW), str(nrow + k)]
    tx = re.sub(r'(static const String spr\[\] = \{ )([^}]*?)( \};)', lambda m_: m_.group(1) + m_.group(2) + ', ' + ', '.join(spr_new) + m_.group(3), tx, count=1)
    tx = re.sub(r'(static const int key\[\] = \{ )([^}]*?)( \};)', lambda m_: m_.group(1) + m_.group(2) + ', ' + ', '.join(key_new) + m_.group(3), tx, count=1)
    pg.wr('zscript/rsq/gunmoves.zs', tx)
    for (l, f), r in zip(groups, rows): pg.note('gunmoves FlameCannon row ADDED md3 frame %d (%s)' % (f, l), ', '.join('%.2f' % v for v in r))

if __name__ == '__main__' and sys.argv[1:2] == ['--fire-rows']:
    pg.ARGS = argparse.Namespace(dry='--dry' in sys.argv); add_fire_rows(); pg.flush(); print('moved %d items' % len(pg.MOVED))
