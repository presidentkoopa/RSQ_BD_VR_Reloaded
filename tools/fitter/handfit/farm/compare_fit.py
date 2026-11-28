"""Compare two fits of the same gun (e.g. the PC farm's result vs the cloud's): hand vertex positions (curl3 Xt/Xs, cm),
the baked md3 frames (md3 units / 64), and the fit-json metrics.
usage: python compare_fit.py <dirA> <dirB> <Gun>     each dir holds curl3_<Gun>.json, <Gun>_hv.json and fbx_hv_<Gun>_R.md3 (or bake/)"""
import sys, os, json, struct, numpy as np
def md3_xyz(p):
    d = open(p, 'rb').read(); nfr, ntag, nsurf = struct.unpack_from('<3i', d, 76)[:3]; osurf = struct.unpack_from('<i', d, 76 + 4 * 6)[0]; out = []; off = osurf
    for s in range(nsurf):
        flags, snfr, nsh, nv, nt, otri, osh, ost, oxyz, oend = struct.unpack_from('<10i', d, off + 68)
        out.append(np.frombuffer(d, '<i2', snfr * nv * 4, off + oxyz).reshape(snfr, nv, 4)[:, :, :3].astype(float) / 64.0); off += oend
    return np.concatenate(out, 1)
def find(d, names):
    for n in names:
        p = os.path.join(d, n)
        if os.path.exists(p): return p
def main(a, b, g):
    o = {}
    ca, cb = find(a, ['curl3_%s.json' % g]), find(b, ['curl3_%s.json' % g])
    if ca and cb:
        A, B = json.load(open(ca)), json.load(open(cb))
        for k in ('Xt', 'Xs'): o[k + '_max_cm'] = float(np.abs(np.array(A[k]) - np.array(B[k])).max())
        o['R_max'] = float(np.abs(np.array(A['R']) - np.array(B['R'])).max()); o['t_max_cm'] = float(np.abs(np.array(A['t']) - np.array(B['t'])).max())
        o['metrics_A'] = {k: A[k] for k in ('trigger', 'squeeze') if k in A}; o['metrics_B'] = {k: B[k] for k in ('trigger', 'squeeze') if k in B}
    ma = find(a, ['fbx_hv_%s_R.md3' % g, 'bake/fbx_hv_%s_R.md3' % g]); mb = find(b, ['fbx_hv_%s_R.md3' % g, 'bake/fbx_hv_%s_R.md3' % g])
    if ma and mb: o['md3_max_units'] = float(np.abs(md3_xyz(ma) - md3_xyz(mb)).max()); o['md3_identical'] = open(ma, 'rb').read() == open(mb, 'rb').read()
    ja, jb = find(a, ['%s_hv.json' % g]), find(b, ['%s_hv.json' % g])
    if ja and jb:
        A, B = json.load(open(ja)), json.load(open(jb))
        o['shift_max_cm'] = float(np.abs(np.array(A['shift']) - np.array(B['shift'])).max())
        sa, sb = A['hand']['support'], B['hand']['support']
        o['support_max'] = float(max(np.abs(np.array(sa[k]) - np.array(sb[k])).max() for k in ('sup_hook', 'sup_rot', 'sup_point_m')))
    print(json.dumps(o, indent=1, default=float)); return o
if __name__ == '__main__': main(*sys.argv[1:4])
