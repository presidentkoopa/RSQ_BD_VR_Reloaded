"""ohbake.py: the off-hand FBX frames as DATA -> MD3 (lane_c bake.bake, side R, each frame baked IN PLACE: cuff_ref = its own cuff,
hook 0), and the rebake check.
  python3 ohbake.py bake  <poses.json> <out.md3>     frames from the JSON's `frames` [{name, z}] (ohfit.hand(zp(z)), logscale fixed)
  python3 ohbake.py check [<poses.json>...]           rebakes every tools/handfit/poses/offhand/*.json to a temp dir and compares each
                                                      frame to the committed md3 (`md3`, src-relative): max difference in md3 units
The pose JSON: {md3, frames: [{name, z (24: rotvec, t cm, 18 FBX pose parameters)}], logscale, fbx, how, measurements...}."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, json, glob, tempfile, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ohfit as O
import bake as B
POSES = os.path.join(_DP.POSES, 'offhand')
def bake(J, out):
    assert abs(J.get('logscale', O.LOGS) - O.LOGS) < 1e-9, 'controller calibration scale changed'
    ent = []
    for f in J['frames']:
        X = O.hand(O.zp(np.array(f['z'], float))); ent.append(dict(name=f['name'], side='R', X=X, cuff_ref=X[O.cuff_idx()]))
    base = out[:-len('_R.md3')] + '.md3' if out.endswith('_R.md3') else out
    rows, paths, _ = B.bake(ent, base)
    if paths['R'] != out: os.replace(paths['R'], out)
    return rows
def frames_of(p):
    import struct
    d = open(p, 'rb').read(); off = struct.unpack_from('<i', d, 100)[0]; flags, snfr, nsh, nv, nt, otri, osh, ost, oxyz, oend = struct.unpack_from('<10i', d, off + 68)
    return np.frombuffer(d, '<i2', snfr * nv * 4, off + oxyz).reshape(snfr, nv, 4)[:, :, :3].astype(int)
def check(files):
    ok = True
    for jf in files:
        J = json.load(open(jf)); ref = os.path.join(O.SRC, J['md3'])
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, 'x_R.md3'); rows = bake(J, out); a = frames_of(out); b = frames_of(ref)
            same = a.shape == b.shape; mx = int(np.abs(a - b).max()) if same else -1
            print('%-28s %-40s frames %d  max diff %s md3 units  bake check %.4f cm' % (os.path.basename(jf), J['md3'], len(J['frames']), mx, max(r['bake_check_max_cm'] for r in rows)))
            ok &= same and mx <= 1
    print('rebake check:', 'OK' if ok else 'FAILED'); return ok
if __name__ == '__main__':
    if sys.argv[1] == 'bake': print(bake(json.load(open(sys.argv[2])), sys.argv[3]))
    else: sys.exit(0 if check(sys.argv[2:] or sorted(glob.glob(os.path.join(POSES, '*.json')))) else 1)
