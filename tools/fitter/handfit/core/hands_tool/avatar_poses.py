"""RS Avatar / UZDXREMA pose names for our solved hands (read-only use of
$RSQ_DOOMWORK/UZDXREMA/tools/avatar/fbx_poses.json).

Their poses are FBX frames of the same hand_final.fbx (hand A = rig 0 'Hand_Low', hand B = rig 1 'Hand_Low1'),
measured against frame 1 (open). Ours are slerps of each joint's local rotation from frame 56 (open) toward frame 517
(fist) with a per-finger curl_base / curl_dist. This module:
  1. checks the two references agree (frame 1 vs 56, 319 vs 517: max joint angle);
  2. projects each of their frames onto our curl coordinates (the fraction of the 56->517 rotation, per joint, along
     the joint's own open->fist axis) and reports the off-axis residual;
  3. detects each rig's side with mkfbxposes.py's own rule (fist fingertip travel along knuckles x fingers);
  4. names a solved hand: per finger, the nearest of their named FBX poses (deg, over that finger's 3 joints).
usage: avatar_poses.py  -> ../avatar_poses.json"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import numpy as np, json, os, sys
from scipy.spatial.transform import Rotation as Rot
import fbxhand, handmodel
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSES=(_DP.DOOMWORK + '/UZDXREMA/tools/avatar/fbx_poses.json')
FING=[('thumb','THUMB'),('index','INDEX'),('middle','MIDDLE_F'),('ring','RING'),('pinky','PINK')]
SEG=('_BASE_joint','_MID_joint','_TOP_joint')
def nrm(M): return M/np.linalg.norm(M,axis=0)
def rig_side(h):
    J0,_=h.joint_pos(1); J1,_=h.joint_pos(319)
    f=J0['MIDDLE_F_BASE_joint']-J0['Root_joint']; f/=np.linalg.norm(f)
    kr=J0['INDEX_BASE_joint']-J0['PINK_BASE_joint']; k=kr-(kr@f)*f; k/=np.linalg.norm(k)
    pr=np.cross(k,f); tr=np.zeros(3)
    for t in ('INDEX_TOP_joint','MIDDLE_F_TOP_joint','RING_TOP_joint','PINK_TOP_joint'):
        tr+=(J1[t]-J1['Root_joint'])-(J0[t]-J0['Root_joint'])
    a=float(tr@pr/np.linalg.norm(tr)); return ('R' if a>0 else 'L'),a
def frame_rots(h,f):
    return {h.jname[j]:nrm(h.local(j,f)[:3,:3]) for j in h.joints}
def curl_coords(H,h,f):
    """their frame f -> our per-joint curl t (fraction of open->fist along our axis) + off-axis residual deg"""
    R=frame_rots(h,f); out={}
    for fn,fb in FING:
        for s in SEG:
            n=fb+s; j=H.jn[n]; d=H.dlog[j]; ang=np.linalg.norm(d)
            D=Rot.from_matrix(R[n]@np.linalg.inv(H.Ro[j]))      # rotation from OUR open local to theirs
            v=D.as_rotvec(); t=float(v@d/ang**2); off=float(np.degrees(np.linalg.norm(v-t*d)))
            out[n]=(t,off)
    return out
def joint_rots_q(H,q):
    R=H.local_rots(q); return {H.h.jname[j]:R.get(j,H.Ro[j]) for j in H.order}
def finger_dist(Ra,Rb,fb):
    return float(np.sqrt(np.mean([np.degrees(Rot.from_matrix(Ra[fb+s].T@Rb[fb+s]).magnitude())**2 for s in SEG])))
def named_frames():
    P=json.load(open(POSES)); out={}
    for k,v in P.items():
        if k.startswith('//') or isinstance(v,dict): continue
        out[k]=(int(v[0]),v[1])
    comp={k:v['fingers'] for k,v in P.items() if isinstance(v,dict)}
    return out,comp
def name_hand(H,q,rig,frames_R):
    """frames_R: {name: {joint: R}} for this rig. Per finger: nearest named pose + deg; whole-hand nearest composed pose."""
    Rq={k:nrm(v) for k,v in joint_rots_q(H,q).items()}; per={}
    for fn,fb in FING:
        d={nm:finger_dist(Rq,Rf,fb) for nm,Rf in frames_R.items()}
        best=sorted(d.items(),key=lambda kv:kv[1])[:3]; per[fn]=[(k,round(v,1)) for k,v in best]
    return per,Rq
def composed_dist(Rq,frames_R,fingers):
    return float(np.sqrt(np.mean([finger_dist(Rq,frames_R[fingers[fn]],fb)**2 for fn,fb in FING])))
if __name__=='__main__':
    FBX=handmodel.FBX; res={}
    hs=[fbxhand.Hand(FBX,0),fbxhand.Hand(FBX,1)]
    res['sides']={f'rig{i}':rig_side(h) for i,h in enumerate(hs)}
    Hs={'R':handmodel.FbxHand('R'),'L':handmodel.FbxHand('L')}
    # 1. reference agreement
    agree={}
    for i,h in enumerate(hs):
        for a,b in ((1,56),(319,517)):
            A=frame_rots(h,a); B=frame_rots(h,b)
            agree[f'rig{i} {a} vs {b}']=round(max(np.degrees(Rot.from_matrix(A[n].T@B[n]).magnitude()) for fn,fb in FING for n in [fb+s for s in SEG]),2)
    res['reference_agreement_max_deg']=agree
    # 2. their frames in our curl coordinates (rig0 = our 'R' model; rig1 frames read through rig1's own rest)
    frames,comp=named_frames(); res['their_frames_in_our_curl']={}
    for nm,(f,src) in frames.items():
        ri=1 if src=='B' else 0; H0=Hs['L' if ri else 'R']
        cc=curl_coords(H0,hs[ri],f)
        res['their_frames_in_our_curl'][f'{nm} (frame {f}, rig{ri})']={fn:[round(cc[fb+s][0],2) for s in SEG]+[round(max(cc[fb+s][1] for s in SEG),1)] for fn,fb in FING}
    json.dump(res,open(os.path.join(LANE,'avatar_poses.json'),'w'),indent=1)
    print(json.dumps(res['sides'])); print(json.dumps(agree))
    for k,v in res['their_frames_in_our_curl'].items(): print(k,v)

def frames_R_all():
    hs=[fbxhand.Hand(handmodel.FBX,0),fbxhand.Hand(handmodel.FBX,1)]; frames,comp=named_frames(); out={}
    for nm,(f,src) in frames.items():
        if nm in ('open','fist'): continue
        out[nm]=frame_rots(hs[1 if src=='B' else 0],f)
    return out,comp
