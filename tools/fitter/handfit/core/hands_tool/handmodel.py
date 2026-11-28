"""The FBX hand (hand_final.fbx) as a posable model. Coordinates: the HANDPALM_joint frame (FBX units),
mirrored for the left hand. The caller places it with (scale s, rotation R, translation t) -> controller cm.

Pose parameters q (18), all on/near the FBX's own authored motion:
  per finger I,M,R,P: curl_base, curl_dist (slerp each joint's local rotation from the authored OPEN frame 56
                      toward the authored FIST frame 517; extrapolates mildly past 1), spread (deg, about the palm normal)
  thumb:              curl_base, curl_dist, spread (deg, about the palm normal), twist (deg, about its own metacarpal)
  wrist:              flex (deg, about the palm's side axis: + bends toward the palm), dev (deg, about the palm normal)
The wrist moves the forearm (Root_joint) relative to the palm, so the palm frame stays the reference.
Left hand = the FBX's second rig (Hand_Low1, under a Scale -1 control in the file), mirrored here."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import numpy as np
from scipy.spatial.transform import Rotation as Rot, Slerp
import fbxhand
FBX=_DP.FBX
ERMAC=(_DP.ERMAC + '/hand/hand.md3')
ERMAC2=(_DP.ERMAC + '/hand/hand2.md3')
OPEN,FIST=56,517
FING=['INDEX','MIDDLE_F','RING','PINK']
NQ=18
# limits: curl ranges = what the FBX's own 1279-frame take reaches per joint (fbx_limits.json, measured: base -0.4..1.0,
# distal -0.1..1.0, up to 1.37 on the ring's middle joint) widened by 0.15 past the fist; spreads/twist/wrist from the
# take where it moves them (palm joint about its side axis -22..58 deg, about the palm normal -11..4 deg), else +-25..40.
QLO=np.array([-0.4,-0.1,-20]*4+[-0.7,-0.9,-35,-40]+[-25,-15])
QHI=np.array([1.15,1.15,20]*4+[1.15,1.15,35,40]+[55,15])
def q_open(): return np.zeros(NQ)
def q_fist(): q=np.zeros(NQ); q[[0,1,3,4,6,7,9,10,12,13]]=1; return q
def axrot(axis,deg): return Rot.from_rotvec(np.asarray(axis)*np.radians(deg)).as_matrix()
class FbxHand:
    def __init__(s,side='R'):
        s.side=side; s.h=h=fbxhand.Hand(FBX,0 if side=='R' else 1)
        s.order=[]
        def add(j):
            if j in s.order: return
            p=h.par.get(j)
            if p in h.jname: add(p)
            s.order.append(j)
        for j in h.joints: add(j)
        s.parent={j:(h.par[j] if h.par.get(j) in h.jname else None) for j in s.order}
        s.jn={h.jname[j]:j for j in s.order}
        s.T={}; s.Ro={}; s.Rf={}
        for j in s.order:
            Lo=h.local(j,OPEN); Lf=h.local(j,FIST); s.T[j]=Lo[:3,3]; s.Ro[j]=Lo[:3,:3]; s.Rf[j]=Lf[:3,:3]
        s.dlog={j:(Rot.from_matrix(s.Rf[j])*Rot.from_matrix(s.Ro[j]).inv()).as_rotvec() for j in s.order}
        s.clusters=[(c['bone'],c['idx'],c['w'],np.linalg.inv(c['TL'])) for c in h.clusters if len(c['idx'])]
        s.Vh=np.c_[h.V,np.ones(len(h.V))]
        s.F=h.F if side=='R' else h.F[:,::-1]
        s.M=np.diag([1,-1,1.]) if side=='L' else np.eye(3)
        # palm-frame axes from the authored open/fist frames (right-hand rig coordinates)
        G0=s._glob_raw({}); P=lambda G,n:G[s.jn[n]][:3,3]
        x=P(G0,'MIDDLE_F_BASE_joint')-P(G0,'HANDPALM_joint'); x/=np.linalg.norm(x)
        Gf=s._glob_raw({j:s.Rf[j] for j in s.order})
        tips=np.mean([P(Gf,f+'_UP_TOP_joint') for f in FING],0); kn=np.mean([P(Gf,f+'_BASE_joint') for f in FING],0)
        n=tips-kn; n-=(n@x)*x; n/=np.linalg.norm(n)
        s.ax_x=x; s.ax_n=n; s.ax_y=np.cross(n,x)   # rig coords (before mirror)
        # bone index per vertex (dominant)
        W=np.zeros((len(h.V),len(h.clusters))); 
        for k,c in enumerate(h.clusters): W[c['idx'],k]=c['w']
        s.dom=np.array([h.clusters[i]['name'] for i in W.argmax(1)])
    def _rot(s,j,t):
        return Rot.from_rotvec(s.dlog[j]*t).as_matrix()@s.Ro[j]
    def _glob_raw(s,Rloc):
        G={}
        for j in s.order:
            L=np.eye(4); L[:3,:3]=Rloc.get(j,s.Ro[j]); L[:3,3]=s.T[j]
            p=s.parent[j]; G[j]=(G[p] if p is not None else np.eye(4))@L
        Pi=np.linalg.inv(G[s.jn['HANDPALM_joint']]); return {j:Pi@G[j] for j in G}
    def local_rots(s,q):
        q=np.asarray(q,float); R={}
        Gp=None
        for k,f in enumerate(FING):
            cb,cd,sp=q[3*k:3*k+3]
            b,m,t=(s.jn[f+x] for x in ('_BASE_joint','_MID_joint','_TOP_joint'))
            R[b]=s._rot(b,cb); R[m]=s._rot(m,cd); R[t]=s._rot(t,cd)
            R[b]=s._about_palm(b,s.ax_n,sp)@R[b]
        cb,cd,sp,tw=q[12:16]
        b,m,t=(s.jn['THUMB'+x] for x in ('_BASE_joint','_MID_joint','_TOP_joint'))
        R[b]=s._rot(b,cb); R[m]=s._rot(m,cd); R[t]=s._rot(t,cd)
        G0=s._glob_raw({})
        thax=G0[m][:3,3]-G0[b][:3,3]; thax/=np.linalg.norm(thax)
        R[b]=s._about_palm(b,thax,tw)@s._about_palm(b,s.ax_n,sp)@R[b]
        return R
    def _about_palm(s,j,axis_palm,deg):
        """rotation, in joint j's parent frame, equal to turning about a palm-frame axis"""
        if deg==0: return np.eye(3)
        G0=s._glob_raw({}); p=s.parent[j]; Rp=G0[p][:3,:3]
        return Rp.T@axrot(axis_palm,deg)@Rp
    def pose(s,q):
        """vertices (palm frame, mirrored for L) and joint frames"""
        R=s.local_rots(q); G=s._glob_raw(R)
        fl,dv=q[16],q[17]
        # wrist: turn the forearm (Root) about the palm-joint origin: G_root' = W @ G_root
        W=np.eye(4); W[:3,:3]=axrot(s.ax_y,-fl)@axrot(s.ax_n,dv)
        root=s.jn['Root_joint']; G[root]=W@G[root]
        out=np.zeros((len(s.Vh),3)); w=np.zeros(len(s.Vh))
        for j,idx,ww,invTL in s.clusters:
            M=G[j]@invTL; out[idx]+=(s.Vh[idx]@M.T)[:,:3]*ww[:,None]; w[idx]+=ww
        V=(out/w[:,None])@s.M.T
        J={s.h.jname[j]:s.M@G[j][:3,3] for j in G}
        return V,J
    def axes(s):
        """palm frame axes after mirroring: x fingers, n palm side, y = n x x"""
        x=s.M@s.ax_x; n=s.M@s.ax_n; return x,np.cross(n,x),n
