"""Round 7: Flamethrower2 gun hand = gas-pump WRAP with the drawn hand's ROTATION released from the controller.
Owner (r6 rejection): the hand may turn away from the controller's orientation; the wrist POSITION stays at the
controller; the nozzle stays level (pitch 0, bore on the aim).
How: the hand is solved in the gun's 1.92 frame (gun fixed, mode-S style: pose + placement free); afterwards the gun is
turned ONLY to put its bore exactly on the aim (pitch 0, yaw 0, roll 0) and TRANSLATED so the drawn cuff centre sits on the
controller grip's cuff centre. The drawn hand's turn off the controller is then measured and reported.
Handle centreline = the line through grip_c along grip_axis (gun_landmarks.json, measured from the mesh).
usage: wrap7.py <key> [json overrides]  -> results/Flamethrower2_wrap7_<key>.json"""
import numpy as np, json, os, sys
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
import solve, fields, gunfield, scene, evaluate, handmodel
LANE=solve.LANE
FING={'I':'INDEX','M':'MIDDLE_F','R':'RING','P':'PINK'}
def make_ctx():
    ctx=solve.Ctx('Flamethrower2@nozzle','R',fields.get('Flamethrower2','gun'),'wrap7')
    S=scene.item_verts(scene.GUNS['Flamethrower2'])
    ctx.lever=gunfield.cached('Flamethrower2_lever',S[1][1],S[1][0],(-7,-4,-14),(8,4,-3),h=0.1,band=1.0)
    ctx.a=np.asarray(ctx.G['grip_axis'],float); ctx.a/=np.linalg.norm(ctx.a); ctx.c0=np.asarray(ctx.G['grip_c'],float)
    up=np.array([0,0,1.]); up-=(up@ctx.a)*ctx.a; ctx.eu=up/np.linalg.norm(up); ctx.el=np.cross(ctx.eu,ctx.a)   # el = +L
    R4=json.load(open(os.path.join(LANE,'results','round4_final.json')))['Flamethrower2']
    ctx.idx_t=np.array(R4['Xg'])[evaluate.reg(ctx.L,'pad_I')].mean(0)
    return ctx
def cs(ctx,P):
    """cross-section coords about the handle centreline: (u up, l left, t along)"""
    q=np.atleast_2d(P)-ctx.c0; t=q@ctx.a; return np.stack([q@ctx.eu,q@ctx.el,t],1)
def ang(ctx,P): c=cs(ctx,P); return np.arctan2(c[:,1],c[:,0])     # 0 = straight up, +90 = left (+L), -90 = right
def chain(ctx,X,J,f):
    """loop chain: thumb tip -> thumb joints -> palm -> finger f joints -> finger tip"""
    th=[J['THUMB'+s] for s in ('_UP_TOP_joint','_TOP_joint','_MID_joint','_BASE_joint')]
    fg=[J[FING[f]+s] for s in ('_BASE_joint','_MID_joint','_TOP_joint','_UP_TOP_joint')]
    return np.array(th+[X[ctx.L['palm']]]+fg)
def sweep(ctx,pts):
    A=ang(ctx,pts); st=np.angle(np.exp(1j*np.diff(A))); return float(np.degrees(st.sum()))
def winding(ctx,pts):
    """winding number of the CLOSED loop (chain + closing segment tip->thumb tip) about the centreline"""
    A=ang(ctx,np.vstack([pts,pts[:1]])); return float(np.angle(np.exp(1j*np.diff(A))).sum()/(2*np.pi))
P_=dict(contact=0.2,palm_f=(-5.5,-1.0),fore_f=0.3,fore_u=-0.2,fingers_u=-0.5,sweep=330.0,opp=140.0,thumb_along=0.75)
def terms(ctx,x,w):
    X,J=solve.hand_X(ctx,x); r=[solve.residuals(ctx,x,dict(solve.W,pen=w['pen'],prior=w['prior'],fore=0.0),'S')]
    d=ctx.sdf(X); v=lambda k:X[evaluate.reg(ctx.L,k)].mean(0)
    # palm: on the handle surface, beside it (palm sideways), F on the handle above the guard
    pp=X[ctx.L['palm']]; r.append([w['palm']*(d[ctx.L['palm']]-P_['contact'])])
    r.append([w['side']*max(0,P_['palm_f'][0]-pp[0]),w['side']*max(0,pp[0]-P_['palm_f'][1])])
    n=Rot.from_rotvec(x[:3]).as_matrix()@ctx.H.axes()[2]; cp=cs(ctx,pp[None])[0]
    tocl=-(cp[0]*ctx.eu+cp[1]*ctx.el); tocl/=np.linalg.norm(tocl)+1e-9
    r.append([w['side']*max(0,np.degrees(np.arccos(np.clip(n@tocl,-1,1)))-30)/10])
    r.append([w['side']*max(0,abs(n[2])-0.5)*5])                            # palm sideways (upright hand)
    # thumb along the top of the handle
    th=v('pad_T'); ct=cs(ctx,th[None])[0]; r.append([w['thumb']*max(0,1.0-ct[0])])   # thumb pad above the centreline
    r.append([w['thumb']*0.3*(ctx.sdf(th[None])[0]-P_['contact'])])
    td=J['THUMB_UP_TOP_joint']-J['THUMB_MID_joint']; td/=np.linalg.norm(td); r.append([w['thumb']*max(0,P_['thumb_along']-td@ctx.a)*5])
    # the loop: thumb -> palm -> finger closes round the centreline; proximal pads opposite the thumb
    for f,wt in (('I',1.0),('M',1.0),('R',0.7)):
        s=sweep(ctx,chain(ctx,X,J,f)); r.append([w['wrap']*wt*max(0,P_['sweep']-abs(s))/30])
        dA=abs(np.degrees(np.angle(np.exp(1j*(ang(ctx,v('prox_'+f)[None])[0]-ang(ctx,th[None])[0])))))
        r.append([w['wrap']*wt*max(0,P_['opp']-dA)/30])
    # index (and middle) on the lever
    for f,wt in (('I',1.0),('M',0.5)):
        pf=X[evaluate.reg(ctx.L,'pad_'+f)]; r.append([w['lever']*wt*(float(np.min(np.abs(ctx.lever(pf))))-P_['contact'])])
    r.append(w['index_keep']*(v('pad_I')-ctx.idx_t))
    # forearm comes from behind (toward the player), not through the gun
    fa=pp-X[ctx.cuff].mean(0); fa/=np.linalg.norm(fa); r.append([w['fore']*max(0,P_['fore_f']-fa[0])*5])
    r.append([w['fore']*max(0,fa[2]-P_['fore_u'])*5])                    # wrist above the palm: forearm comes down onto the handle
    xa=Rot.from_rotvec(x[:3]).as_matrix()@ctx.H.axes()[0]; r.append([w['upright']*max(0,xa[2]-P_['fingers_u'])*5])   # hand upright: knuckles below the wrist
    return np.concatenate([np.ravel(z) for z in r])
W7=dict(pen=8.0,prior=0.15,palm=2.0,side=2.0,thumb=1.5,wrap=2.0,lever=2.0,index_keep=0.4,fore=1.0,upright=1.5)
def seed(ctx,palm_f,roll,flex,curl,dz=0.0):
    x_,y_,n_=ctx.H.axes(); a=ctx.a
    nt=Rot.from_rotvec(a*np.radians(roll)).apply(ctx.el)         # palm faces +L (palm on the handle's right side)
    xt=Rot.from_rotvec(a*np.radians(roll)).apply(-ctx.eu)        # fingers down
    yt=np.cross(nt,xt); R=np.stack([xt,yt,nt],1)@np.stack([x_,y_,n_],1).T
    q=np.clip(ctx.q_prior.copy(),handmodel.QLO,handmodel.QHI)
    for k in range(4): q[3*k]=curl; q[3*k+1]=curl
    q[16]=flex
    x=np.r_[Rot.from_matrix(R).as_rotvec(),np.zeros(3),q,np.zeros(6)]
    X,_=solve.hand_X(ctx,x); c=ctx.c0+a*((palm_f-ctx.c0[0])/a[0])
    tgt=c-ctx.el*2.4+ctx.eu*dz; x[3:6]+=tgt-X[ctx.L['palm']]; return x
def run(key,OV):
    ctx=make_ctx(); w=dict(W7); w.update(OV.get('w',{})); P_.update(OV.get('P',{}))
    lo=np.r_[[-np.inf]*6,handmodel.QLO,[-1e-9]*6]; hi=np.r_[[np.inf]*6,handmodel.QHI,[1e-9]*6]
    starts=[seed(ctx,pf,ro,fl,cu,dz) for pf in OV.get('pfs',(-4.0,-2.5)) for ro in OV.get('rolls',(0.0,20.0,-20.0)) for fl in OV.get('flex',(10.0,)) for cu in OV.get('curl',(0.7,1.0)) for dz in OV.get('dz',(0.0,))]
    for e in OV.get('seeds',[]): starts.append(np.array(json.load(open(os.path.join(LANE,'results',e)))['x']))
    best=None
    for k,x0 in enumerate(starts):
        x0=np.clip(x0,lo+1e-12,hi-1e-12)
        s=least_squares(lambda z:terms(ctx,z,w),x0,bounds=(lo,hi),max_nfev=OV.get('nfev',200),x_scale=solve.XS)
        cost=float(np.sum(terms(ctx,s.x,w)**2)); print('  start',k,'cost %.2f'%cost,flush=True)
        if best is None or cost<best[0]: best=(cost,s.x,k)
    json.dump(dict(x=best[1].tolist(),cost=best[0],start=best[2],w=w,P=dict(P_)),open(os.path.join(LANE,'results',f'Flamethrower2_wrap7_{key}.json'),'w'),indent=1)
    print('== wrap7',key,'cost %.2f start %d'%(best[0],best[2])); return ctx,best[1]
if __name__=='__main__':
    run(sys.argv[1],json.loads(sys.argv[2]) if len(sys.argv)>2 else {})
