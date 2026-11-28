"""Calibrate the FBX hand to the controller (where the player's real hand is).
Reference = Ermac's free hand as 1.92 draws it on the controller (hand.md3 frame 0 open / frame 1 fist;
1.92 MODELDEF.rsq RSQ_Hands: Scale -1 1 1, Offset 0 -24 -10, no hook). In the controller frame that mesh is a
right hand (hw_vrmodes.cpp GetWeaponTransform mirrors the off controller), so FBX rig 0 (a right hand) is fitted.
Fit: scale s, rotation R, translation t of the FBX palm frame + its 18 pose parameters, by trimmed symmetric
chamfer (least squares), started from semantic axes (fingers = cuff->tips, palm side = where tips go from open to fist).
The fist fit (frame 1) is THE controller grip pose: the displayed wrist must stay near it (KEY VR RULE)."""
import numpy as np, json, sys
from scipy.spatial import cKDTree
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
import scene, handmodel
ERMAC=handmodel.ERMAC
def ermac_axes():
    _,E0=scene.merged(dict(path=ERMAC,frame=0,**scene.ERMAC_PL)); _,E1=scene.merged(dict(path=ERMAC,frame=1,**scene.ERMAC_PL))
    mv=np.linalg.norm(E1-E0,axis=1); still=mv<np.percentile(mv,20); tips=mv>np.percentile(mv,90)
    x=E0[tips].mean(0)-E0[still].mean(0); x/=np.linalg.norm(x)
    n=(E1-E0)[tips].mean(0); n-=(n@x)*x; n/=np.linalg.norm(n)
    return E0,E1,x,n,still
def frame_of(x,n): return np.stack([x,np.cross(n,x),n],1)
def place(H,p):
    R=Rot.from_rotvec(p[:3]).as_matrix(); t=p[3:6]; s=np.exp(p[6]); V,J=H.pose(p[7:])
    return s*V@R.T+t
def fit(H,target,p,free_q=True,iters=4,keep=0.9,fix_scale=False):
    tree=cKDTree(target); lo=np.r_[[-np.inf]*7,handmodel.QLO]; hi=np.r_[[np.inf]*7,handmodel.QHI]
    if fix_scale: lo[6]=p[6]-1e-9; hi[6]=p[6]+1e-9
    for it in range(iters):
        X=place(H,p); d,i=tree.query(X); k1=d<np.quantile(d,keep)
        d2,j=cKDTree(X).query(target); k2=d2<np.quantile(d2,keep)
        A=np.where(k1)[0]; At=target[i[k1]]; B=j[k2]; Bt=target[k2]
        def res(q):
            pp=q if free_q else np.r_[q,p[7:]]
            X=place(H,pp); return np.r_[(X[A]-At).ravel(),(X[B]-Bt).ravel(),0.5*(pp[7:]-p[7:])*0]
        if free_q: sol=least_squares(res,p,bounds=(lo,hi),max_nfev=80); p=sol.x
        else: sol=least_squares(res,p[:7],bounds=(lo[:7],hi[:7]),max_nfev=80); p=np.r_[sol.x,p[7:]]
    X=place(H,p); d,_=tree.query(X); d2,_=cKDTree(X).query(target)
    return p,float(np.sqrt(np.mean(np.r_[d,d2]**2))),float(np.median(np.r_[d,d2]))
def thumb_tip_ermac(E0):
    """Ermac's open free hand (frame 0) has its thumb up: its highest vertex is the thumb tip (checked on the render)."""
    return E0[np.argmax(E0[:,2])]
def calibrate(H,frame,scale=None,thumb_w=1.0,log=None):
    """multi-start over roll about the finger axis (chamfer alone cannot tell a fist's roll: 90 deg apart fit
    within 0.1 cm rms); the thumb-tip correspondence on the open frame picks the roll, and the fist frame is
    started from the open frame's solution."""
    E0,E1,xE,nE,_=ermac_axes(); T=E0 if frame==0 else E1
    x,y,n=H.axes(); V,J=H.pose(handmodel.q_open())
    s0=scale if scale is not None else np.ptp(E0@xE)/np.ptp(V@x)
    thE=thumb_tip_ermac(E0); best=None
    for roll in range(0,360,30):
        nn=Rot.from_rotvec(xE*np.radians(roll)).apply(nE); nn-= (nn@xE)*xE; nn/=np.linalg.norm(nn)
        R0=frame_of(xE,nn)@frame_of(x,n).T
        q0=handmodel.q_open() if frame==0 else 0.85*handmodel.q_fist()
        p=np.r_[Rot.from_matrix(R0).as_rotvec(),T.mean(0)-s0*R0@V.mean(0),np.log(s0),q0]
        p,_,_=fit(H,T,p,free_q=False,iters=2,fix_scale=scale is not None)
        p,rms,med=fit(H,T,p,free_q=True,iters=3,fix_scale=scale is not None)
        X,Jx=None,None
        Vp,Jp=H.pose(p[7:]); R=Rot.from_rotvec(p[:3]).as_matrix(); th=np.exp(p[6])*R@Jp['THUMB_UP_TOP_joint']+p[3:6]
        dth=float(np.linalg.norm(th-thE)) if frame==0 else 0.0
        score=rms+thumb_w*0.1*dth
        if log: print('   roll %3d rms %.2f thumb-tip %.1f cm palm n %s'%(roll,rms,dth,(R@n).round(2)),file=log)
        if best is None or score<best[0]: best=(score,p,rms,med,dth)
    return best[1],best[2],best[3],best[4]
def calibrate_fist_from(H,p_open,log=None):
    E0,E1,_,_,_=ermac_axes()
    p=np.array(p_open,float); p[7:]=0.85*handmodel.q_fist()
    p,_,_=fit(H,E1,p,free_q=False,iters=2,fix_scale=True)
    return fit(H,E1,p,free_q=True,iters=4,fix_scale=True)
if __name__=='__main__':
    H=handmodel.FbxHand('R'); out={}
    p0,rms0,med0,dth=calibrate(H,0,log=sys.stdout)
    s_open=float(np.exp(p0[6]))
    p1,rms1,med1=calibrate_fist_from(H,p0)
    x,y,n=H.axes()
    for fr,p,rms,med in ((0,p0,rms0,med0),(1,p1,rms1,med1)):
        R=Rot.from_rotvec(p[:3]).as_matrix()
        print('Ermac frame',fr,'scale cm per FBX unit %.3f  rms %.2f cm  median %.2f cm'%(np.exp(p[6]),rms,med),
              ' fingers(FLU)',(R@x).round(2),' palm side(FLU)',(R@n).round(2),flush=True)
        out[str(fr)]=dict(p=p.tolist(),rms=rms,med=med)
    print('open frame thumb tip vs Ermac thumb tip: %.2f cm'%dth)
    V,J=H.pose(handmodel.q_open())
    L=lambda a,b:np.linalg.norm(J[a]-J[b])*s_open
    print('hand size at that scale: wrist(Root_joint)->middle knuckle %.1f cm, knuckle width (index->pinky base) %.1f cm'%(L('Root_joint','MIDDLE_F_BASE_joint'),L('INDEX_BASE_joint','PINK_BASE_joint')))
    out['scale']=s_open; out['thumb_tip_err_cm']=dth
    json.dump(out,open(sys.argv[1],'w'),indent=1)
