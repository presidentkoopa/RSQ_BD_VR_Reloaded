"""scope_eye.py <pk3> <out_prefix> [iterations] [Gun]: batch 5, the Sniper scope (r9: also RailGun, scope row 1; Gun default Sniper) re-checked with the LEFT eye 8 cm behind the
eyepiece, after the gun moved (port_gun.py moves RSQ_ScopeTable Lens / Axis with the gun).
Method (lane B scope, r6-scope): the right hand held level at the rig's RHAND, the HMD placed so the left eye sits at
Lens - 8 cm * Axis in the hand frame (target read from scope.zs in the tree), corrected from the eye position the
probe logs (RSQ_Scope.EyeInHandFrame); the scope test probe (lane_b_scope_rig/test.pk3: RSQT lines) logs the REAL
state (skinOn, cam, along, fov); frames dumped at the last pose. Rig only: not a headset test.
Env: RSQ_DEPOT, RSQ_GAMEDATA, RSQ_RIGLOCK as gate_gun.py; RSQ_SCOPE_PROBE (default <work>/scope_rig/test.pk3)."""
import os, re, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gate_gun as GG
rig = GG.rig; REPO = GG.REPO
def table(fn, i=2):
    tx = open(os.path.join(REPO, 'src/zscript/rsq/scope.zs')).read(); k = tx.index('static Vector3 %s(int i)' % fn); seg = tx[k:tx.index('return', k)]
    return np.array([float(re.search(r'%s\[\] = \{([^}]*)\}' % a, seg).group(1).split(',')[i]) for a in 'flu'])
SC = {'Sniper': 2, 'RailGun': 1}
def run(pk3, out, it=3, gun='Sniper'):
    ix = SC[gun]; L = table('Lens', ix); A = table('Axis', ix); tgt = L - 8.0 * A / np.linalg.norm(A); print('lens', L, 'axis', A, 'eye target (F L U cm)', tgt.round(2))
    probe = os.environ.get('RSQ_SCOPE_PROBE', os.path.join(_DP.WORK, 'scope_rig', 'test.pk3'))
    GG.setpk3(pk3); os.environ['B22_NOPROBE'] = '1'
    off = np.array([0.0, -3.2, 0.0])	# the head centre is half the IPD to the right of the left eye (first guess; corrected below)
    res = []
    for k in range(it):
        c = tgt + off; hmd = '%.4f %.4f %.4f 0 0 0' % (rig.RHAND[0] - c[1] / 100, rig.RHAND[1] + c[2] / 100, rig.RHAND[2] - c[0] / 100)
        last = k == it - 1
        if last:
            d = out + '_dump'; os.makedirs(d, exist_ok=True); os.environ.update(QZ_RES='480', QZ_DUMP_EVERY='4', QZ_DUMP_DIR=d)
        s = ('wait 100; ' + GG.SET + 'screenblocks 12; crosshair 0; qz_rhand "%.4f %.4f %.4f 0 0 0"; give ammo; give %s; wait 2; use %s; wait 120; qz_hmd "%s"; wait 160; ' % (rig.RHAND + (gun, gun, hmd))
             + '+attack; wait 3; -attack; wait 40; quit')
        rc, text = GG.locked(rig.run, 'scope_eye_%s_%d' % (gun, k), s, 300, extra=[probe])
        for v in ('QZ_RES', 'QZ_DUMP_EVERY', 'QZ_DUMP_DIR'): os.environ.pop(v, None)
        rows = [(r[0], r[1] if gun == 'Sniper' else r[2]) + r[3:] for r in re.findall(r'RSQT t=(\d+) gun=%s idx=%d sniper=(\d) rail=(\d) eyeL=\(([-\d. ]+)\) skinOn=(-?\d) cam=(\d) along=([-\d.]+) fov=([-\d.]+)' % (gun, ix), text, re.I)]
        errs = [l for l in re.findall(r'Script error, "([^"]+)"', text) if 'BD_VoxelPack' not in l]
        if not rows: res.append(dict(k=k, hmd=hmd, rc=rc, errors=errs, note='no RSQT %s line' % gun)); print(res[-1]); continue
        t, mode, e, skin, cam, along, fov = rows[-1]; e = np.array([float(v) for v in e.split()])
        r = dict(k=k, hmd=hmd, eyeL=e.tolist(), miss_cm=float(np.linalg.norm(e - tgt)), mode_cvar=int(mode), skinOn=int(skin), cam=int(cam), along=float(along), fov=float(fov), errors=errs, rc=rc)
        res.append(r); print(json.dumps(r), flush=True)
        off = off - (e - tgt)
    json.dump(dict(target=tgt.tolist(), lens=L.tolist(), axis=A.tolist(), runs=res), open(out + '.json', 'w'), indent=1); return res
if __name__ == '__main__':
    run(sys.argv[1], os.path.abspath(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 3, sys.argv[4] if len(sys.argv) > 4 else 'Sniper')
