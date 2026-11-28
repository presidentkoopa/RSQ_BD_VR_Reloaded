"""poses_sg.py <Class>: the solved FBX hand pose as DATA (owner, 2026-10-27), so a future hand mesh on the same skeleton can be
re-baked in one run. Writes tools/handfit/poses/<Class>.json:
  joints: the solver's pose vector x (lane_c hands_tool solve/handmodel parametrisation, 6 wrist + 16 finger params) for
          trigger, squeeze (trigger with the index's 3 params replaced) and the approved pistol pose it started from
  wrist: stage-2 rigid placement R, t of the pistol hand in the gun's scene frame (X = Xf R^T + t) and the gun shift d
  gun_move: the MODELDEF placement and R, t that port_gun applied (ported_<Class>.json)
  support: the FBX support pose used (fbx_b1_L.md3 frame 1 = RQFS B) and its handtable hook / rot / point
  fbx_source: DXR models/hands/hand_final.fbx (never shipped), r5 approved pistol frame = fbx_b1_R.md3 frame 0"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, os, numpy as np
RUN = _DP.WORK + '/runs/lane_b_sgrun'; HERE = os.path.dirname(os.path.abspath(__file__)); g = sys.argv[1]
C = json.load(open(RUN + '/curl3_%s.json' % g)); a = np.load(RUN + '/st2_%s.npy' % g)
P = json.load(open(os.path.join(_DP.FITS, 'ported_%s.json' % g))); F = json.load(open(os.path.join(_DP.FITS, '%s_sg.json' % g)))
assert 'q_trigger' in C, 'curl3 json has no joint angles: re-run fit_sg.py %s +' % g
qs = list(C['q_trigger']); qs[6:9] = C['q_squeeze_index']
out = dict(cls=g, fbx_source=dict(fbx='DXR models/hands/hand_final.fbx (not shipped)', start_frame='fbx_b1_R.md3 frame 0 (r5 approved pistol)', parametrisation='lane_c hands_tool solve.hand_X(ctx, x)'),
           joints=dict(pistol=C['q_pistol'], trigger=C['q_trigger'], squeeze=qs),
           wrist=dict(R=a[:9].reshape(3, 3).tolist(), t=a[9:12].tolist(), gun_shift_cm=a[12:15].tolist(), note='wrist (cuff) pinned to the controller; the gun moves by gun_shift in its original frame'),
           gun_move=dict(place=P['place'], R=P['R'], t=P['t']),
           support=dict(pose='fbx_b1_L.md3 frame 1 (RQFS B, FBX palm-under / pump grip)', **F['hand']['support']),
           metrics=dict(trigger=C['trigger'], squeeze=C['squeeze']), baked_md3=F['hand']['md3_name'])
json.dump(out, open(os.path.join(_DP.POSES, '%s.json' % g), 'w'), indent=1); print('wrote poses/%s.json' % g)
