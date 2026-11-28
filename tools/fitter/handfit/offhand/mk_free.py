"""mk_free.py <free_oh.json>: poses/offhand/free.json + src/models/rsq/fbx/fbx_oh_free_R.md3 (frame 0 open, 1 fist, 2 ring pinch) +
src/models/rsq/fbx/rsq_ring_oh.md3 (BD22's ring as Ermac's pinch held it, rsq_ring.md3, translated from Ermac's pinch point -- the
middle of his index and thumb pad regions -- to the FBX pinch point)."""
import os, sys, json, struct, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ohfit as O, ohbake, hook
F = json.load(open(sys.argv[1]))
J = dict(md3='models/rsq/fbx/fbx_oh_free_R.md3', logscale=O.LOGS, fbx=os.path.basename(O.handmodel.FBX),
         how='tools/handfit/offhand/free_oh.py (ohfit.seed onto Ermac hand.md3 0 / 1, ammo_hand.md3 1; the fist pulled to q_fist; the pinch closed), mk_free.py',
         frames=[dict(name='free_open', z=F['open']['z'], ermac=F['open']['ermac'], seed=F['open']['seed'], used='RQHN A (FreeHand)'),
                 dict(name='free_fist', z=F['fist']['z'], ermac=F['fist']['ermac'], seed=F['fist']['seed'], palm_to_knuckle_dir=F['fist']['palm_to_knuckle_dir'],
                      used='RQHN H (AmmoH: idle free fist, off-hand punch, closed hand on handles); RQGF A (Fists weapon / BD22 punches, gun hand; dual DFist)'),
                 dict(name='free_pinch', z=F['pinch']['z'], ermac=F['pinch']['ermac'], seed=F['pinch']['seed'], pad_gap_cm=F['pinch']['pad_gap_cm'], used='RQHR A (+ rsq_ring_oh.md3)')])
os.makedirs(ohbake.POSES, exist_ok=True)
rows = ohbake.bake(J, os.path.join(O.SRC, J['md3'])); J['bake_check_max_cm'] = max(r['bake_check_max_cm'] for r in rows)
E, _ = O.ermac('ammo_hand.md3', 1); pE = (E[O.EREG['pad_I']].mean(0) + E[O.EREG['pad_T']].mean(0)) / 2; pF = np.array(F['pinch']['pinch_point_cm'])
sh = hook.flu_to_md3(pF[None])[0] - hook.flu_to_md3(pE[None])[0]
d = bytearray(open(os.path.join(O.SRC, 'models/rsq/rsq_ring.md3'), 'rb').read()); nsurf = struct.unpack_from('<i', d, 84)[0]; off = struct.unpack_from('<i', d, 100)[0]
for k in range(nsurf):
    flags, snfr, nsh, nv, nt, otri, osh, ost, oxyz, oend = struct.unpack_from('<10i', d, off + 68); o = off + oxyz
    a = np.frombuffer(bytes(d), '<i2', snfr * nv * 4, o).reshape(snfr, nv, 4).copy(); a[:, :, :3] = np.round(a[:, :, :3] + sh * 64).astype('<i2'); d[o:o + a.nbytes] = a.tobytes(); off += oend
open(os.path.join(O.SRC, 'models/rsq/fbx/rsq_ring_oh.md3'), 'wb').write(bytes(d))
J['ring'] = dict(md3='models/rsq/fbx/rsq_ring_oh.md3', from_='models/rsq/rsq_ring.md3', ermac_pinch_cm=pE.round(3).tolist(), fbx_pinch_cm=pF.round(3).tolist(),
                 shift_cm=round(float(np.linalg.norm(pF - pE)), 2))
json.dump(J, open(os.path.join(ohbake.POSES, 'free.json'), 'w'), indent=1)
print(json.dumps(dict(bake=J['bake_check_max_cm'], ring_shift_cm=J['ring']['shift_cm'])))
