"""bake_gun.py <Class> <curl.json> <out_prefix>: bake a curl3 solve (Xt trigger, Xs squeeze) into FBX gun-hand MD3 frames
0 trigger, 1 squeeze, 2 the approved pistol re-bake (check: must equal fbx_b1_R frame 0). The hand is baked with the PISTOL's
r5 controller move, so the wrist stays where the approved pistol hand's wrist is; port_gun.py then moves the GUN to it
(the gun shift d is already in Xt/Xs). bake_b4.py (stopped run) with repo-relative paths. Needs the FBX source (env
RSQ_FBX, see fbx_fitter/handmodel.py) and lane_c's round-4 pistol result, as revindex.setup does."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET
# the fitter reads its lane data (ref192_pistol.json, results/) from the folder ABOVE its own: the repo snapshot does not carry it,
# so point RSQ_HANDS_TOOL at a full fitter checkout (lane_c/hands_tool in the cloud workspace)
sys.path.insert(0, os.path.join(HERE, '..', 'fitter_lib')); sys.path.insert(0, _DP.HANDS_TOOL)
import solve, bake, scene, revindex
G, J, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
ctx, x, to_g, Xf, delta = revindex.setup(); Rg, tg = solve.gun_T(ctx, x)
to_c = lambda X: solve.gmove(ctx, Rg, tg, X)
ent = [dict(name=G + '_trg', side='R', X=to_c(np.array(J['Xt']))), dict(name=G + '_sqz', side='R', X=to_c(np.array(J['Xs']))), dict(name='PISTOL_chk', side='R', X=to_c(Xf))]
for e in ent: e['cuff_ref'] = e['X'][ctx.cuff]
rows, paths, _ = bake.bake(ent, out + '.md3')
for r in rows: print({k: r[k] for k in ('name', 'frame', 'wrist_rot_deg', 'wrist_move_cm', 'bake_check_max_cm') if k in r})
s_new = scene.md3_full(paths['R'])[0]['xyz'][2]; s_b1 = scene.md3_full(os.path.join(REPO, 'src/models/rsq/fbx/fbx_b1_R.md3'))[0]['xyz'][0]
print('pistol re-bake vs fbx_b1_R frame 0: max %.4f md3 units' % np.abs(s_new - s_b1).max()); print(paths['R'])
