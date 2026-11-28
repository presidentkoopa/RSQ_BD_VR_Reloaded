"""Does the bar run THROUGH the fist? Cross-section measures around the support bar axis (cm, deg), for any solved
FBX support hand. S4 (pads) = rules.py's definition. Added, per finger I/M/R/P:
  wrap_deg  = how far the chain palm -> base -> mid -> top -> tip turns around the bar axis (unwrapped angle)
  enclosed  = the bar axis lies inside the closed loop palm, base, mid, top, tip (2-D winding number in the
              cross-section != 0): the bar is INSIDE that finger's loop, i.e. through the fist
  S4_mid    = S4 with the middle joints in place of the pads (palm and middle phalanges on opposite sides)"""
import numpy as np, json, sys, os
import solve
FING=[('I','INDEX'),('M','MIDDLE_F'),('R','RING'),('P','PINK')]
def measure(cls,x,side='L'):
    ctx=solve.Ctx(cls,side,None,'vgrip'); X,J=solve.hand_X(ctx,np.asarray(x))
    S=ctx.S; a=np.asarray(S['axis']); c=np.asarray(S['c'])
    e1=np.cross(a,[0,1.,0]); e1/=np.linalg.norm(e1); e2=np.cross(a,e1)
    q2=lambda p:np.array([(p-c)@e1,(p-c)@e2])
    palm=X[ctx.L['palm']]; out={}
    pc=q2(palm)
    for t,fb in FING:
        pts=[palm]+[J[fb+s] for s in ('_BASE_joint','_MID_joint','_TOP_joint','_UP_TOP_joint')]
        P0=np.array([q2(p) for p in pts])
        dense=lambda P:np.concatenate([P[i]+np.linspace(0,1,40,endpoint=False)[:,None]*(P[(i+1)%len(P)]-P[i]) for i in range(len(P))])
        P=dense(P0[:,:]) [:40*(len(P0)-1)+1]          # open chain palm..tip, densely sampled (valid unwrap)
        ang=np.unwrap(np.arctan2(P[:,1],P[:,0])); wrap=float(np.degrees(ang[-1]-ang[0]))
        Q=dense(P0); Q=np.vstack([Q,Q[:1]]); A=np.unwrap(np.arctan2(Q[:,1],Q[:,0])); wn=int(round((A[-1]-A[0])/(2*np.pi)))
        minr=round(float(np.linalg.norm(Q,axis=1).min()),2)
        out[t]=dict(wrap_deg=round(abs(wrap),0),enclosed=bool(wn!=0))
    pm=np.mean([q2(J[fb+'_MID_joint']) for _,fb in FING],0)
    pd=np.mean([q2(X[ctx.L['pad_'+t]]) for t,_ in FING],0)
    s4=float(-(pc@pd)/(np.linalg.norm(pc)*np.linalg.norm(pd)+1e-9)); s4m=float(-(pc@pm)/(np.linalg.norm(pc)*np.linalg.norm(pm)+1e-9))
    return dict(S4_pads=round(s4,2),S4_mid=round(s4m,2),fingers=out,n_enclosed=sum(v['enclosed'] for v in out.values()),
                bar_d_cm=float(S['d']),bar_w_cm=float(S['w']))
if __name__=='__main__':
    for f in sys.argv[1:]:
        d=json.load(open(f)); print(os.path.basename(f),json.dumps(measure('Flamethrower2@nozzle',d['x'])))
