#!/usr/bin/env python3
"""build_pose_library.py [--poses DIR] [--out pose_library.json] [--reference CLASS ...]

The pose library the Blender Handfit add-on reads (docs: README.md beside this file). Two sources, one shape:

  * the approved BD22 VR Weapons Q 2.0.1 holds: every <Class>.json in the set's handfit/poses (RSQ_SET, default the
    RS_Brutal22WeaponsQ checkout beside this repo; the Depot's copy is the same data), evaluated through the same
    forward kinematics the fitter used (tools/handfit/core/hands_tool/handmodel.py: 18 parameters -> joint frames),
  * the FBX hand's own authored poses: the five holds in hand_final.fbx's take (open, relaxed, half-curl, fist, grip),
    for the right and the left rig, read straight from the take (fbxhand.py).

Each pose is stored as the 4x4 frame of every joint relative to HANDPALM_joint (FBX units), which is how the add-on
applies it: Blender's imported armature has the same joints, and a joint's pose is set from its library frame after
one fixed conversion solved from the rest pose, so no axis convention is typed anywhere. The library also carries
the bind reference (the take's open frame, 56, the frame handmodel.py measures everything from), each BD22 pose's
gun_move (the six MODELDEF numbers that put that gun in the hand) and, for the classes named with --reference,
the FK vertex cloud (palm frame): the add-on's acceptance test bakes the pose in Blender and must land on it.
"""
import os, sys, json, argparse
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, TOOLS)
import depot  # noqa: E402
sys.path.insert(0, depot.HANDS_TOOL)
import fbxhand, handmodel  # noqa: E402

TAKE_POSES = {  # name: representative frame of the held pose (recheck: the hold spans in docs/README)
    'open': 68, 'relaxed': 168, 'halfcurl': 211, 'fist': 500, 'grip': 1000,
}
BIND_FRAME = handmodel.OPEN  # 56


def m2l(M):
    return [[round(float(x), 6) for x in row] for row in np.asarray(M)]


def take_pose(hand, f):
    """joint frames relative to HANDPALM_joint at take frame f, straight from the FBX take"""
    J = hand.joints_in(f, frame='HANDPALM_joint')
    return {n: m2l(M) for n, M in J.items()}


def fk_pose(H, q):
    """handmodel's FK: joint frames (palm frame, wrist applied) and the skinned vertices, for one 18-vector"""
    R = H.local_rots(np.asarray(q, float)); G = H._glob_raw(R)
    fl, dv = q[16], q[17]
    W = np.eye(4); W[:3, :3] = handmodel.axrot(H.ax_y, -fl) @ handmodel.axrot(H.ax_n, dv)
    root = H.jn['Root_joint']; G[root] = W @ G[root]
    V, _ = H.pose(np.asarray(q, float))
    return {H.h.jname[j]: m2l(G[j]) for j in G}, V


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--poses', default=depot.POSES, help='BD22 handfit/poses folder')
    ap.add_argument('--out', default=os.path.join(HERE, 'pose_library.json'))
    ap.add_argument('--reference', nargs='*', default=['BrutalPistol'], help='classes whose FK vertex cloud is stored for the acceptance test')
    a = ap.parse_args()

    lib = dict(
        fbx='tools/handfit/core/fbx_hand/hand_final.fbx',
        frame='every joint 4x4 relative to HANDPALM_joint, FBX units; bind = take frame %d (open)' % BIND_FRAME,
        take_holds={'open': '0-136', 'relaxed': '154-183', 'halfcurl': '206-217 (with a 45 deg wrist turn)', 'fist': '334-685', 'grip': '807-1278 (ring + pinky curled, index + middle straight, thumb out)'},
        joints={}, parents={}, bind={}, poses={}, reference={},
    )
    hands = {'R': fbxhand.Hand(depot.FBX, 0), 'L': fbxhand.Hand(depot.FBX, 1)}
    for side, h in hands.items():
        order = []
        def add(j):
            if j in order: return
            p = h.par.get(j)
            if p in h.jname: add(p)
            order.append(j)
        for j in h.joints: add(j)
        lib['joints'][side] = [h.jname[j] for j in order]
        lib['parents'][side] = {h.jname[j]: (h.jname[h.par[j]] if h.par.get(j) in h.jname else None) for j in order}
        lib['bind'][side] = take_pose(h, BIND_FRAME)
        for name, f in TAKE_POSES.items():
            lib['poses']['fbx:%s:%s' % (name, side)] = dict(side=side, kind='seed', source='hand_final.fbx Take 001 frame %d' % f, joints=take_pose(h, f))

    H = handmodel.FbxHand('R')
    cal = json.load(open(os.path.join(depot.CORE, 'calib.json')))
    lib['hand_scale'] = cal['scale']   # FBX units -> controller cm (calib.json), the scale solve.hand_X places the hand with
    # the controller-grip reference (solve.Ctx): calib '1' p = [rotvec(3), t_cm(3), ?, q(18)]; the LEFT hand mirrors it.
    # Its cuff (landmarks_fbx 'cuff', 185 verts) is where a baked frame's wrist sits (bake.py: T = the rigid from this cuff
    # to the solved cuff goes into the hook row). The add-on needs these to export rows the same way.
    from scipy.spatial.transform import Rotation as Rot
    p1 = np.asarray(cal['1']['p'], float); LM = json.load(open(os.path.join(depot.CORE, 'landmarks_fbx.json')))
    lib['controller_grip'] = {}
    for side in 'RL':
        Mi = np.diag([1, -1, 1.]) if side == 'L' else np.eye(3)
        R1 = Rot.from_rotvec(p1[:3]).as_matrix(); rv = Rot.from_matrix(Mi @ R1 @ Mi).as_rotvec(); t = Mi @ p1[3:6]; q = p1[7:]
        Hs = H if side == 'R' else handmodel.FbxHand('L')
        Vp, _ = Hs.pose(q); X = cal['scale'] * Vp @ Rot.from_rotvec(rv).as_matrix().T + t
        cuff = LM[side]['cuff']
        Vb, _ = Hs.pose(handmodel.q_open())
        lib['controller_grip'][side] = dict(rotvec=[float(v) for v in rv], t_cm=[float(v) for v in t], q=[float(v) for v in q],
                                            cuff_index=[int(i) for i in cuff],
                                            cuff_ref_cm=[[round(float(v), 4) for v in X[i]] for i in cuff],
                                            cuff_open_palm=[[round(float(v), 4) for v in Vb[i]] for i in cuff],
                                            landmarks={k: int(v) for k, v in LM[side].items() if isinstance(v, int)})
    lib['placement'] = dict(hand_modeldef=dict(Scale=[-1, 1, 1], Offset=[0, -24], ZOffset=-10, note='RSQ_GunSide, 1.92 hand placement (hook.PL)'),
                            weapon_scale=1.02, chain='models.cpp RenderHUDModel: see tools/handfit/core/hands_tool/hook.py and gunplace.py')
    n = 0
    for fn in sorted(os.listdir(a.poses)):
        if not fn.endswith('.json'): continue
        d = json.load(open(os.path.join(a.poses, fn)))
        cls = d.get('cls', fn[:-5])
        # three pose-file shapes, one vector: the fitter's x (30): [0:3] hand rotvec, [3:6] hand translation (controller cm),
        # [6:24] the 18 handmodel parameters, [24:30] the gun move it was solved with (solve.hand_X / gun_T)
        x = d.get('q_trigger') or ((d.get('poses') or {}).get('trigger') or {}).get('pose_vector') or (d.get('joints') or {}).get('pistol')
        if not x: continue
        x = np.asarray(x, float); q = x[6:24]
        J, V = fk_pose(H, q)
        ent = dict(side='R', kind='gun', source='BD22 2.0.1 handfit/poses/%s (%s)' % (fn, d.get('form', d.get('fit', ''))) if isinstance(d.get('form', d.get('fit', '')), str) else 'BD22 2.0.1 handfit/poses/%s' % fn,
                   gun_move={k: d['gun_move'][k] for k in ('Offset_x', 'Offset_y', 'ZOffset', 'AngleOffset', 'PitchOffset', 'RollOffset') if k in (d.get('gun_move') or {})},
                   hand_place=dict(rotvec=[float(v) for v in x[0:3]], t_cm=[float(v) for v in x[3:6]], how='controller = hand_scale * R(rotvec) @ palm_frame + t_cm (solve.hand_X)'),
                   q=[float(v) for v in q], joints=J, support=d.get('support'), md3=d.get('md3') or d.get('baked') or d.get('bake_md3') or d.get('baked_md3'))
        xs = d.get('q_squeeze') or ((d.get('poses') or {}).get('squeeze') or {}).get('pose_vector')
        if xs is not None and not np.allclose(np.asarray(xs, float)[6:24], q):
            ent['squeeze'] = fk_pose(H, np.asarray(xs, float)[6:24])[0]
        lib['poses']['bd22:%s' % cls] = ent; n += 1
        if cls in a.reference:
            lib['reference']['bd22:%s' % cls] = dict(frame='HANDPALM_joint, FBX units, handmodel.py vertex order (%d verts)' % len(V), verts=[[round(float(x), 4) for x in v] for v in V])
    json.dump(lib, open(a.out, 'w'), separators=(',', ':'))
    print('%s: %d BD22 holds + %d take poses, %d reference cloud(s), %.1f MB' % (a.out, n, len(TAKE_POSES) * 2, len(lib['reference']), os.path.getsize(a.out) / 1e6))


if __name__ == '__main__':
    main()
