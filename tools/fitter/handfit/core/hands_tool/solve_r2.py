"""ModelSwapper_Hands prototype solver: solve, don't slide.

Unknowns  x = [hand rotvec(3), hand t(3) cm, q(18) pose (handmodel), gun rotvec(3), gun t(3) cm]
  hand placement: FBX palm frame -> controller frame (F/L/U cm), scale fixed by calib.json
  gun correction: rigid move of the gun about its grip centre c (x' = Rg (x-c) + c + tg). The engine can apply it
                  with MODELDEF Offset + Angle/Pitch/RollOffset (no engine change); it is reported as such.
Modes
  A 'hook'   gun fixed (as MODELDEF places it today); hand free; VR wrist rule soft (1.92 tolerance).
  B 'vr'     the displayed wrist IS the controller grip (hand rigid placement pinned to calib.json '1');
             the GUN moves to the hand instead; bore-off-aim is reported (aim comes from the controller, not the mesh).
Hard limits: penetration (signed distance field of the gun, cm) beyond TOL['pen']; joint limits as bounds
(handmodel.QLO/QHI, measured from the FBX take). Contacts, wraps and sides per the hold's rules (below).
Prior: q toward the FBX's own closed grip on the controller (calib '1'), so the result stays on the authored motion.
Multiple starts; best total cost kept."""
import numpy as np, json, os, time
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
import handmodel, calib, metrics
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load_json(n): return json.load(open(os.path.join(LANE,n)))
# tolerances learned from 1.92 (metrics192.json, 22 guns; see rules.py / REPORT.md)
TOL=dict(pen=0.5,contact=0.2,wrist_deg=13.3,wrist_cm=7.3)
W=dict(pen=6.0,web=1.0,palm=1.0,pads=1.0,thumb=0.8,index=1.0,prior=0.6,cuff=1.0,side=2.0,axis=0.05,bore=0.15,fore=0.05)
TOLC=dict(wrist_deg=6.0,wrist_cm=6.0,bore_deg=4.0,g4_band=7.0)
REF_G4=float(json.load(open(os.path.join(LANE,'ref192_pistol.json')))['grip_vs_knuckles_deg'])
W.update(cuffC=3.0,boreC=1.0,g4=0.5,cant=1.0)
XS=np.r_[[0.05]*3,[1]*3,[0.1,0.1,5]*4+[0.1,0.1,5,5]+[5,5],[0.03]*3,[1]*3]
MIDJ=dict(I='INDEX_MID_joint',M='MIDDLE_F_MID_joint',R='RING_MID_joint',P='PINK_MID_joint')
def V3(v): return np.asarray(v,float)
class Ctx:
    def __init__(s,cls,side,sdf,hold,other_sdf=None):
        s.cls=cls; s.gun=cls.split('@')[0]; s.hold=hold
        s.G={k:(np.array(v) if isinstance(v,list) else v) for k,v in load_json('gun_landmarks.json')[cls].items()}
        s.S={k:(np.array(v) if isinstance(v,list) else v) for k,v in s.G['support'].items()}
        s.L=dict(load_json('landmarks_fbx.json')[side]); s.L['_reg']=load_json('regions.json')['fbx']; s.cal=load_json('calib.json'); s.scale=s.cal['scale']
        s.H=handmodel.FbxHand(side); s.side=side; s.sgn=1.0 if side=='R' else -1.0
        s.sdf=sdf; s.other=other_sdf
        p1=np.array(s.cal['1']['p'])
        Mi=np.diag([1,-1,1.]) if side=='L' else np.eye(3)
        R1=Rot.from_rotvec(p1[:3]).as_matrix()
        s.p_ref=np.r_[Rot.from_matrix(Mi@R1@Mi).as_rotvec(),Mi@p1[3:6]]   # controller grip (mirrored for the off hand)
        s.q_prior=p1[7:].copy()
        s.ref,_=hand_X(s,np.r_[s.p_ref,s.q_prior])
        s.cuff=np.array(s.L['cuff']); s.cuff_ref=s.ref[s.cuff]
        s.c=s.G['grip_c']
def hand_X(ctx,x):
    R=Rot.from_rotvec(x[:3]).as_matrix(); V,J=ctx.H.pose(x[6:24])
    return ctx.scale*V@R.T+x[3:6], {k:ctx.scale*R@v+x[3:6] for k,v in J.items()}
def gun_T(ctx,x):
    if len(x)<30: return np.eye(3),np.zeros(3)
    return Rot.from_rotvec(x[24:27]).as_matrix(),x[27:30]
def gmove(ctx,Rg,tg,P): return (np.asarray(P)-ctx.c)@Rg.T+ctx.c+tg
def gdir(Rg,v): return Rg@np.asarray(v)
def gun_sdf(ctx,Rg,tg,X): return ctx.sdf((X-ctx.c-tg)@Rg+ctx.c)
def residuals(ctx,x,w=W,mode='A'):
    X,J=hand_X(ctx,x); Rg,tg=gun_T(ctx,x); L=ctx.L; G=ctx.G; sg=ctx.sgn
    d=gun_sdf(ctx,Rg,tg,X); r=[w['pen']*np.maximum(0,-d-TOL['pen'])]
    if ctx.other is not None:
        do=ctx.other(X); r.append(w['pen']*np.maximum(0,-do-TOL['pen']))
    v=lambda k:X[L[k]]
    if ctx.hold=='gunhand':
        a=gdir(Rg,G['grip_axis']); ps=gdir(Rg,G['palm_side']); c=gmove(ctx,Rg,tg,G['grip_c'])
        far=-np.cross(a,ps); far/=np.linalg.norm(far); far*=sg
        r.append(w['web']*(v('web')-gmove(ctx,Rg,tg,G['backstrap_top'])))
        r.append([w['palm']*(d[L['palm']]-TOL['contact'])])
        r.append([w['side']*min(0,(v('palm')-c)@ps)])                       # palm on the back of the grip
        half=0.5*float(G['grip_d'])
        for f in 'MRP':
            r.append([w['pads']*(d[L['pad_'+f]]-TOL['contact'])])
            r.append([w['side']*min(0,-(v('prox_'+f)-c)@ps-half)])        # proximal segments across the front strap
            r.append([w['side']*min(0,(v('pad_'+f)-c)@far-0.3)])           # tips reach the far side
        r.append([w['thumb']*(d[L['pad_T']]-TOL['contact'])])
        r.append([w['side']*min(0,(v('pad_T')-c)@far-0.5)])                # thumb on the far side
        r.append(w['index']*(v('pad_I')-gmove(ctx,Rg,tg,G['trigger_face'])))
        kn=v('prox_P')-v('prox_I'); kn/=np.linalg.norm(kn)
        r.append([w['axis']*max(0,abs(np.degrees(np.arccos(np.clip(abs(kn@a),-1,1))))-40)])   # knuckles not across the grip
    elif ctx.hold=='vgrip':
        S=ctx.S; a=gdir(Rg,S['axis']); c=gmove(ctx,Rg,tg,S['c']); half=0.5*S['len']
        pads=['pad_'+f for f in 'IMRP']; prox=['prox_'+f for f in 'IMRP']
        for k in pads+prox: r.append([w['pads']*(d[L[k]]-TOL['contact'])])
        r.append([w['palm']*(d[L['palm']]-TOL['contact'])])
        r.append([w['thumb']*(d[L['pad_T']]-TOL['contact'])])
        q=lambda P:(P-c)-((P-c)@a)*a
        pc=q(v('palm')); pd=np.mean([q(v(k)) for k in pads],0)
        r.append([w['side']*min(0,-(pc@pd)/(np.linalg.norm(pc)*np.linalg.norm(pd)+1e-9)-w.get('s4_target',0.5))*w.get('s4_gain',5)])     # bar through the fist (round 2: target raised)
        if w.get('wrap',0):                      # round 2: each finger's chain palm->base->mid->top->tip turns round the bar
            e1=np.cross(a,[0,1.,0]); e1/=np.linalg.norm(e1); e2=np.cross(a,e1)
            q2=lambda p:np.arctan2((p-c)@e2,(p-c)@e1)
            for fb in ('INDEX','MIDDLE_F','RING','PINK'):
                ch=[v('palm')]+[J[fb+s_] for s_ in ('_BASE_joint','_MID_joint','_TOP_joint','_UP_TOP_joint')]
                A=np.array([q2(p) for p in ch]); st=np.angle(np.exp(1j*np.diff(A))); tot=abs(st.sum())
                r.append([w['wrap']*max(0,np.radians(w.get('wrap_deg',300))-tot)])
        if w.get('mid_contact',0):
            for f in 'IMRP': r.append([w['mid_contact']*(gun_sdf(ctx,Rg,tg,J[MIDJ[f]][None])[0]-1.2)])   # middle joints on the bar's far side, close to it
            r.append([w['mid_contact']*max(0,0.6-(-(pc@q(np.mean([J[MIDJ[f]] for f in 'IMRP'],0))))/(np.linalg.norm(pc)*np.linalg.norm(q(np.mean([J[MIDJ[f]] for f in 'IMRP'],0)))+1e-9))*5])
        kn=v('prox_P')-v('prox_I'); kn/=np.linalg.norm(kn)
        r.append([w['side']*max(0,np.degrees(np.arccos(np.clip(abs(kn@a),0,1)))-20)/10])            # knuckles along the bar
        for k in ('prox_I','prox_P'):
            t=(v(k)-c)@a; r.append([w['side']*max(0,abs(t)-half)])                                   # on the bar, not past its ends
    elif ctx.hold=='cup':
        # pistol support: palm under the gun hand's fingers, fingers round the gun hand's front, thumb on the gun's left side
        c=gmove(ctx,Rg,tg,G['grip_c']); ps=gdir(Rg,G['palm_side'])
        for k in ['pad_'+f for f in 'IMRP']+['palm']: r.append([w['pads']*(ctx.other(X[[L[k]]])[0]-TOL['contact'])])
        r.append([w['thumb']*(min(d[L['pad_T']],ctx.other(X[[L['pad_T']]])[0])-TOL['contact'])])
        r.append([w['side']*min(0,(v('pad_T')-c)[1]-0.5)])                 # support thumb on the gun's left (+L)
        for f in 'IMRP': r.append([w['side']*min(0,-(v('pad_'+f)-c)[1]+0.5)])   # support fingertips on the right (-L), round the front
    # pose prior (toward the FBX's own closed grip)
    r.append(w['prior']*(x[6:24]-ctx.q_prior)/np.r_[[1,1,30]*4+[1,1,30,30]+[30,30]])
    # VR wrist rule
    if ctx.hold=='gunhand' and mode!='C':
        deg,cm=metrics.wrist_dev(X[ctx.cuff],ctx.cuff_ref)
        r.append([w['cuff']*max(0,deg-TOL['wrist_deg'])/3.0,w['cuff']*max(0,cm-TOL['wrist_cm'])])
    else:
        # support forearm comes from where 1.92's do: cuff->palm direction within the 1.92 spread
        fa=v('palm')-X[ctx.cuff].mean(0); fa/=np.linalg.norm(fa)
        tgt=np.array([0.77,-0.47,0.38]); tgt/=np.linalg.norm(tgt)   # 1.92 support forearm direction (cuff->palm), median over 22 guns
        r.append([w['fore']*max(0,np.degrees(np.arccos(np.clip(fa@tgt,-1,1)))-25)])
    if mode=='B':
        ba=gdir(Rg,G['bore_axis']); r.append([w['bore']*np.degrees(np.arccos(np.clip(ba@G['bore_axis'],-1,1)))])
    if mode=='C' and ctx.hold=='gunhand':
        # round 2: the real hand IS the controller. Wrist (cuff) held inside the 1.92 G8 green band with margin,
        # the GUN moves to the hand; its bore kept on the controller's aim (1.92 bore-off 80th pct 5.0 deg, margin);
        # G4 kept inside its green band (1.92 pistol knuckle angle +-10, margin 3).
        deg,cm=metrics.wrist_dev(X[ctx.cuff],ctx.cuff_ref)
        r.append([w['cuffC']*max(0,deg-TOLC['wrist_deg']),w['cuffC']*max(0,cm-TOLC['wrist_cm'])])
        ba=gdir(Rg,G['bore_axis']); bo=np.degrees(np.arccos(np.clip(ba@np.array([1.,0,0]),-1,1)))
        r.append([w['boreC']*max(0,bo-TOLC['bore_deg'])])
        a=gdir(Rg,G['grip_axis']); kn=v('prox_P')-v('prox_I'); g4=np.degrees(np.arccos(np.clip(abs(kn@a)/np.linalg.norm(kn),0,1)))
        r.append([w['g4']*max(0,abs(g4-REF_G4)-TOLC['g4_band'])])
        if TOLC.get('cant') is not None:   # roll of the gun about its own bore vs the controller (1.92: 0 on all 22 guns)
            b=np.asarray(G['bore_axis']); b2=ba; ax=np.cross(b,b2); sn=np.linalg.norm(ax)
            Rs=Rot.from_rotvec(ax/sn*np.arcsin(min(1,sn))).as_matrix() if sn>1e-9 else np.eye(3)
            cant=abs(np.degrees(Rot.from_matrix(Rs.T@Rg).magnitude()))
            r.append([w['cant']*max(0,cant-TOLC['cant'])])
    return np.concatenate([np.atleast_1d(np.asarray(z,float)).ravel() for z in r])
def start_gunhand(ctx,roll,slide,q):
    x_,y_,n_=ctx.H.axes(); a=ctx.G['grip_axis']; ps=ctx.G['palm_side']
    far=-np.cross(a,ps)*ctx.sgn
    nt=-ps*0.75+far*0.66; nt=Rot.from_rotvec(a*np.radians(roll)).apply(nt); nt-=(nt@a)*a; nt/=np.linalg.norm(nt)
    yt=-a*ctx.sgn; xt=np.cross(yt,nt)
    R=np.stack([xt,yt,nt],1)@np.stack([x_,y_,n_],1).T
    x=np.r_[Rot.from_matrix(R).as_rotvec(),np.zeros(3),q]
    X,_=hand_X(ctx,x); x[3:6]=ctx.G['backstrap_top']-X[ctx.L['web']]+slide*a
    return x
def start_vgrip(ctx,roll,slide,q):
    x_,y_,n_=ctx.H.axes(); S=ctx.S; a=S['axis']
    nt=Rot.from_rotvec(a*np.radians(roll)).apply(np.array([1.,0,0])); nt-=(nt@a)*a; nt/=np.linalg.norm(nt)   # palm faces forward-ish, rolled
    yt=a*(-1 if ctx.side=='L' else 1)*-1; xt=np.cross(yt,nt)
    R=np.stack([xt,yt,nt],1)@np.stack([x_,y_,n_],1).T
    x=np.r_[Rot.from_matrix(R).as_rotvec(),np.zeros(3),q]
    X,_=hand_X(ctx,x); L=ctx.L
    slot=0.5*(X[L['palm']]+np.mean([X[L['prox_'+f]] for f in 'MR'],0))
    x[3:6]=S['c']-slot+slide*a
    return x
def start_cup(ctx,roll,slide,q,gun_hand_X):
    # start from the controller grip mirrored, moved under the gun hand's fingers
    x=np.r_[ctx.p_ref,q]; X,_=hand_X(ctx,x)
    tgt=gun_hand_X[ctx.Lg['pad_M']]+np.array([0,0,-3.0])+slide*np.array([0,0,1.])
    R=Rot.from_rotvec(np.array([1.,0,0])*np.radians(roll))
    x[:3]=(R*Rot.from_rotvec(x[:3])).as_rotvec(); X,_=hand_X(ctx,x)
    x[3:6]+=tgt-X[ctx.L['palm']]
    return x
def solve(ctx,mode='A',starts=None,w=W,max_nfev=200,log=None,start_fn=None):
    lo=np.r_[[-np.inf]*6,handmodel.QLO,[-np.inf]*6]; hi=np.r_[[np.inf]*6,handmodel.QHI,[np.inf]*6]
    if mode in ('A','S'):   # gun fixed (S: explicit start vectors)
        lo[24:]=-1e-9; hi[24:]=1e-9
    if mode=='B':   # hand rigid pinned to the controller grip
        lo[:6]=ctx.p_ref-1e-9; hi[:6]=ctx.p_ref+1e-9
    res=[]; t0=time.time()
    for k,st in enumerate(starts):
        x=np.array(st,float) if mode in ('C','S') else np.r_[start_fn(ctx,*st),np.zeros(6)]
        if mode=='B':
            # move the GUN so its web target meets the pinned hand's web (start), hand at the controller grip
            xh=x.copy(); x[:6]=ctx.p_ref
            Xs,_=hand_X(ctx,xh); Xr,_=hand_X(ctx,x)
            # rigid that takes the start hand to the pinned hand, applied to the gun
            Rm,tm=metrics.rigid(Xs,Xr)
            x[24:27]=Rot.from_matrix(Rm).as_rotvec(); x[27:30]=Rm@ctx.c+tm-ctx.c
        x=np.clip(x,lo+1e-12,hi-1e-12)
        sol=least_squares(lambda z:residuals(ctx,z,w,mode),x,bounds=(lo,hi),max_nfev=max_nfev,x_scale=XS)
        cost=float(np.sum(residuals(ctx,sol.x,w,mode)**2))
        res.append((cost,sol.x,st if mode not in ('C','S') else k))
        if log: print(f'  [{ctx.cls} {ctx.hold} {mode}] start {k} {(st[:2] if mode not in ("C","S") else "")}: cost {cost:.2f} ({time.time()-t0:.0f}s)',file=log,flush=True)
    res.sort(key=lambda r:r[0]); return res
