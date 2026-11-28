"""Grip-rule metrics, identical for any hand mesh that carries the landmark vertex indices
(FBX hand: landmarks_fbx.json; Ermac's hand.md3/hand2.md3: landmarks_ermac.json). Controller frame, cm.

Signed distance to the gun: unsigned = nearest of dense surface samples (0.1 cm); inside = |generalized winding| > 0.5.
Hand axes: x = fingers, n = palm side, y = n x x (thumb side for a right hand is -y... measured, see hand_axes).
Wrist pose vs the controller: rigid fit of the CUFF vertices (forearm stub) now vs the reference grip pose on the
controller (Ermac's free-hand fist, hand.md3 frame 1, as 1.92 draws it on the controller; the FBX hand calibrated onto it)."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
import gunfield
class GunSDF:
    def __init__(s,V,F,step=0.1):
        s.V,s.F=V,F; S,_,_=gunfield.sample_surface(V,F,step); s.tree=cKDTree(S)
        s.A,s.B,s.C=V[F[:,0]],V[F[:,1]],V[F[:,2]]
    def __call__(s,P):
        d,_=s.tree.query(P)
        near=d<4.0; w=np.zeros(len(P))
        if near.any(): w[near]=gunfield.winding(P[near],s.A,s.B,s.C)
        return np.where(np.abs(w)>0.5,-d,d)
def rigid(A,B):
    ca,cb=A.mean(0),B.mean(0); U,S,Vt=np.linalg.svd((B-cb).T@(A-ca)); D=np.eye(3); D[2,2]=np.sign(np.linalg.det(U@Vt))
    R=U@D@Vt; return R,cb-R@ca
def wrist_dev(cuff_now,cuff_ref):
    R,t=rigid(cuff_ref,cuff_now)
    return float(np.degrees(Rot.from_matrix(R).magnitude())), float(np.linalg.norm(cuff_now.mean(0)-cuff_ref.mean(0)))
def angle(a,b):
    a=a/np.linalg.norm(a); b=b/np.linalg.norm(b); return float(np.degrees(np.arccos(np.clip(a@b,-1,1))))
def gun_hand(X,L,sdf,G,cuff_ref,side='R'):
    """X hand vertices; L landmark indices; G gun landmarks dict; returns {rule: value}"""
    d=sdf(X); m={}
    v=lambda k:X[L[k]]
    m['pen_max_cm']=float(max(0,-d.min())); m['pen_frac']=float((d<-0.05).mean())
    m['web_to_backstrap_cm']=float(np.linalg.norm(v('web')-np.asarray(G['backstrap_top'])))
    m['palm_gap_cm']=float(d[L['palm']])
    # palm on the BACK of the grip: palm point behind the grip axis (toward -F side of the grip's front/back direction)
    a=np.asarray(G['grip_axis']); c=np.asarray(G['grip_c'])
    back=np.cross(np.array([0,1.,0]),a); back*=-np.sign(back[0]) if back[0]!=0 else 1   # unit pointing rearward in the grip's plane
    m['palm_behind_axis_cm']=float((v('palm')-c)@back)
    kn=v('prox_P')-v('prox_I'); m['grip_vs_knuckles_deg']=angle(a,kn)
    for f in 'MRP':
        m[f'pad_{f}_gap_cm']=float(d[L['pad_'+f]])
        m[f'pad_{f}_front_cm']=float(-(v('pad_'+f)-c)@back)   # >0: in front of the grip axis (wrapping the front strap)
    m['thumb_side_cm']=float((v('pad_T')-c)[1]*(1 if side=='R' else -1))   # >0: on the gun's far (+L) side for a right hand
    m['pad_T_gap_cm']=float(d[L['pad_T']])
    m['index_to_trigger_cm']=float(np.linalg.norm(v('pad_I')-np.asarray(G['trigger_face'])))
    cuff=X[L['cuff']]; fore=cuff.mean(0); m['forearm_vs_bore_deg']=angle(v('palm')-fore,np.asarray(G['bore_axis']))
    fa=v('palm')-fore; fa_top=fa*np.array([1,1,0]); m['forearm_yaw_deg']=angle(fa_top,np.asarray(G['bore_axis'])*np.array([1,1,0]))
    m['wrist_rot_vs_controller_deg'],m['wrist_move_vs_controller_cm']=wrist_dev(cuff,cuff_ref)
    return m
def support(X,L,sdf,G,other=None):
    d=sdf(X); m={}
    m['pen_max_cm']=float(max(0,-d.min())); m['pen_frac']=float((d<-0.05).mean())
    if other is not None:
        do=other(X); m['pen_into_gunhand_cm']=float(max(0,-do.min()))
    S=G['support']
    pads=[L['pad_'+f] for f in 'IMRP']
    if S['type']=='vgrip':
        a=np.asarray(S['axis']); c=np.asarray(S['c'])
        q=X[pads]-c; r=np.linalg.norm(q-np.outer(q@a,a),axis=1)
        m['pads_gap_cm_max']=float(np.max(d[pads])); m['pads_gap_cm_mean']=float(np.mean(d[pads]))
        m['palm_gap_cm']=float(d[L['palm']])
        # the bar runs THROUGH the fist: the axis passes between the palm and the finger pads
        pc=X[L['palm']]-c; pc-= (pc@a)*a; pd=np.mean(q-np.outer(q@a,a),0)
        m['axis_through_fist']=float(-(pc@pd)/(np.linalg.norm(pc)*np.linalg.norm(pd)+1e-9))   # 1 = palm and pads on opposite sides
        m['grip_vs_knuckles_deg']=angle(a,X[L['prox_P']]-X[L['prox_I']])
    else:
        m['pads_gap_cm_max']=float(np.max(d[pads])); m['palm_gap_cm']=float(d[L['palm']])
    return m
