"""offhand_r12.py <outdir>   (r12 port lane; coordinator 2026-10-28: "the EMPTY off hand is still Ermac's black glove")

Bakes the FBX LEFT hand frames for the free off hand (MODELDEF.rsq RSQ_Hands RQHN A / H, RQHR A), drawn as Ermac's were: Scale -1 1 1,
Offset 0 -24 -10, no hook (the free-hand layer has none), so each frame is baked IN PLACE at the off controller (hook 0).
The wrist: the approved FBX pistol hand's wrist on its controller (lane_c r5, fbx_b1_R frame 0), mirrored to the left hand (L -> -L in
the controller's F/L/U frame; the FBX L rig is the R rig mirrored). Fingers (handmodel pose vector, the 18 FBX parameters):
  frame 0 OPEN  : relaxed open hand (all curls 0.12, thumb 0)               -> RQHN A (FreeHand: open while the grenade is out, after the throw)
  frame 1 FIST  : handmodel.q_fist()                                         -> RQHN H (AmmoH: the idle free hand, a fist; it punches)
  frame 2 PINCH : index and thumb pads closed on each other (solved: pad_I to pad_T distance minimised over the index curls and the
                  thumb), middle / ring / pinky curled 0.6                   -> RQHR A (the grenade ring between finger and thumb)
The ring mesh (rsq_ring.md3, baked in Ermac's pinch frame) is translated so its centre sits at the FBX pinch point (the midpoint of the
two pads): rsq_ring_fbx.md3. Writes <outdir>/fbx_r12_free_L.md3, rsq_ring_fbx.md3, offhand_r12.json (numbers).
Needs RSQ_HANDS_TOOL (full fitter checkout, e.g. lane_c hands_tool) and the FBX (handmodel.FBX / RSQ_FBX), as rebake.py."""
import os, sys, json, struct, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import rebake	# its fitter setup (RSQ_HANDS_TOOL, poses/sources lane_c round4_final.json)
import solve, bake, hook, handmodel, scene
from scipy.optimize import least_squares
OUT = os.path.abspath(sys.argv[1]); os.makedirs(OUT, exist_ok=True)
ctx, x, to_g, Xf, delta = rebake._hand_setup(); Rg, tg = solve.gun_T(ctx, x)
LM = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(solve.__file__))), 'landmarks_fbx.json')))['R']
def hand_c(q18):
    xx = np.array(x, float).copy(); xx[6:24] = q18
    return solve.gmove(ctx, Rg, tg, to_g(solve.hand_X(ctx, xx)[0]))	# controller F/L/U cm, R hand
mir = lambda X: X * np.array([1.0, -1.0, 1.0])
q_wr = np.array(x[22:24], float)
q_open = np.r_[[0.12, 0.12, 0.0] * 4, [0.0, 0.0, 0.0, 0.0], q_wr]
q_fist = handmodel.q_fist().copy(); q_fist[16:18] = q_wr
# pinch: free = index curls (0, 1), thumb (12..15); M / R / P curled 0.6
def q_pinch(p):
    q = np.r_[[0.0, 0.0, 0.0], [0.6, 0.6, 0.0] * 3, [0, 0, 0, 0], q_wr]; q[0], q[1] = p[0], p[1]; q[12:16] = p[2:6]; return np.clip(q, handmodel.QLO, handmodel.QHI)
pI = np.atleast_1d(LM['pad_I']); pT = np.atleast_1d(LM['pad_T'])	# single vertex ids
def res(p):
    X = hand_c(q_pinch(p)); return np.r_[X[pI].mean(0) - X[pT].mean(0), 0.05 * (p - np.r_[0.5, 0.5, 0, 0, 0, 0])]
s = least_squares(res, np.r_[0.5, 0.5, 0.3, 0.3, 0, 0], bounds=(np.r_[handmodel.QLO[[0, 1]], handmodel.QLO[12:16]], np.r_[handmodel.QHI[[0, 1]], handmodel.QHI[12:16]]))
Xp = hand_c(q_pinch(s.x)); gap = float(np.linalg.norm(Xp[pI].mean(0) - Xp[pT].mean(0)))
ent = []
for nm, X in (('free_open', hand_c(q_open)), ('free_fist', hand_c(q_fist)), ('free_pinch', Xp)):
    XL = mir(X); ent.append(dict(name=nm, side='L', X=XL, cuff_ref=XL[ctx.cuff]))
rows, paths, _ = bake.bake(ent, os.path.join(OUT, 'fbx_r12_free.md3'))
pinch_L = mir(Xp)[pI].mean(0) * 0.5 + mir(Xp)[pT].mean(0) * 0.5	# FLU cm at the off controller
# the ring: Ermac's rsq_ring.md3 (frame 0) centre -> the FBX pinch point, in md3 units (the block's chain is the same for both models)
src = os.path.join(rebake.REPO, 'src', 'models', 'rsq', 'rsq_ring.md3'); d = bytearray(open(src, 'rb').read())
nfr, ntag, nsurf = struct.unpack_from('<3i', d, 76); osurf = struct.unpack_from('<i', d, 100)[0]; off = osurf; allv = []
for k in range(nsurf):
    flags, snfr, nsh, nv, nt, otri, osh, ost, oxyz, oend = struct.unpack_from('<10i', d, off + 68); allv.append((off + oxyz, snfr, nv)); off += oend
V = np.concatenate([np.frombuffer(bytes(d), '<i2', sf * nv * 4, o).reshape(sf, nv, 4)[0, :, :3] / 64.0 for o, sf, nv in allv])
c_md3 = (V.min(0) + V.max(0)) / 2; tgt_md3 = hook.flu_to_md3(pinch_L[None])[0]; sh = tgt_md3 - c_md3
for o, sf, nv in allv:
    a = np.frombuffer(bytes(d), '<i2', sf * nv * 4, o).reshape(sf, nv, 4).copy(); a[:, :, :3] = np.round(a[:, :, :3] + sh * 64).astype('<i2'); d[o:o + a.nbytes] = a.tobytes()
open(os.path.join(OUT, 'rsq_ring_fbx.md3'), 'wb').write(bytes(d))
J = dict(rows=rows, md3=os.path.basename(paths['L']), frames=['open (RQHN A)', 'fist (RQHN H)', 'pinch (RQHR A)'], pinch_params=s.x.tolist(), pinch_pad_gap_cm=gap,
         pinch_point_flu_cm=pinch_L.tolist(), ring_centre_md3_was=c_md3.tolist(), ring_shift_md3=sh.tolist(), ring_shift_cm=float(np.linalg.norm(sh) * 1.02),
         wrist='approved FBX pistol hand (lane_c r5) wrist, mirrored to L', q_open=q_open.tolist(), q_fist=q_fist.tolist(), q_pinch=q_pinch(s.x).tolist())
json.dump(J, open(os.path.join(OUT, 'offhand_r12.json'), 'w'), indent=1)
print(json.dumps({k: J[k] for k in ('md3', 'pinch_pad_gap_cm', 'ring_shift_cm')}), [r['hook'] for r in rows], [round(r['bake_check_max_cm'], 4) for r in rows])
