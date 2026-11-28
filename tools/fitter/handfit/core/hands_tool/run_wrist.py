"""Round 2, the wrist (mode C): the displayed wrist IS the controller grip, the gun is placed relative to the hand.
Starts: round 1's mode-A and mode-B solves, each moved RIGIDLY (hand + gun together) so its cuff lands on the controller
grip cuff -- that keeps every contact (G1-G7) and turns the gun off the aim instead; the solver then trades the gun's
turn back into the wrist joint (q flex/dev) and fingers, under: cuff within 6 deg / 6 cm of the controller grip
(1.92 G8 green = median 7.5 deg / 7.3 cm, margin), bore within 4 deg of the controller aim (1.92 22 guns bore-off
80th pct 5.0, margin), G4 within 7 deg of 1.92's pistol knuckle angle (green band 10, margin).
usage: run_wrist.py <cls[@variant]>   -> results/<cls>_gunhand.json gains 'C'"""
import numpy as np, sys, json, os
from scipy.spatial.transform import Rotation as Rot
import solve, fields, evaluate, rules, metrics
LANE=solve.LANE
def seeds(ctx,res):
    out=[]
    for m in ('A','B'):
        x=np.array(res[m]['x']); X,_=solve.hand_X(ctx,x); Rg,tg=solve.gun_T(ctx,x)
        Rt,tt=metrics.rigid(X[ctx.cuff],ctx.cuff_ref)            # whole arrangement -> wrist on the controller
        Rh=Rot.from_rotvec(x[:3]).as_matrix(); y=x.copy()
        y[:3]=Rot.from_matrix(Rt@Rh).as_rotvec(); y[3:6]=Rt@x[3:6]+tt
        Rg2=Rt@Rg; tg2=Rt@(ctx.c+tg)+tt-ctx.c                    # gun point p'=Rg(p-c)+c+tg, then Rt p'+tt
        y[24:27]=Rot.from_matrix(Rg2).as_rotvec(); y[27:30]=tg2
        out.append((m,y))
        # and a half-way variant: only half the turn on the gun (the rest left for the wrist joint)
        h=Rot.from_matrix(Rt).as_rotvec()*0.5; Rh2=Rot.from_rotvec(h).as_matrix()
        z=x.copy(); z[:3]=Rot.from_matrix(Rh2@Rh).as_rotvec()
        X2,_=solve.hand_X(ctx,z); z[3:6]+=ctx.cuff_ref.mean(0)-X2[ctx.cuff].mean(0)
        Xz,_=solve.hand_X(ctx,z); Rq,tq=metrics.rigid(X,Xz)
        Rg3=Rq@Rg; tg3=Rq@(ctx.c+tg)+tq-ctx.c
        z[24:27]=Rot.from_matrix(Rg3).as_rotvec(); z[27:30]=tg3
        out.append((m+'half',z))
    return out
def cant_of(G,Rg):
    b=np.asarray(G['bore_axis']); b2=Rg@b; ax=np.cross(b,b2); sn=np.linalg.norm(ax)
    Rs=Rot.from_rotvec(ax/sn*np.arcsin(min(1,sn))).as_matrix() if sn>1e-9 else np.eye(3)
    return float(np.degrees(Rot.from_matrix(Rs.T@Rg).magnitude()))
def run(cls,log=sys.stdout,cant=None,key='C',rotmax=None,pen=None):
    solve.TOLC['cant']=cant; solve.TOLC['gun_rot_max']=rotmax
    if pen is not None: solve.TOL['pen']=pen
    gun=cls.split('@')[0]; fld=fields.get(gun,'gun')
    ctx=solve.Ctx(cls,'R',fld,'gunhand')
    p=os.path.join(LANE,'results',f'{cls.replace("@","_")}_gunhand.json'); res=json.load(open(p))
    S=seeds(ctx,res)
    starts=[]
    for _,y in S:
        y=y.copy()
        if rotmax is not None:
            a=np.radians(rotmax)/np.sqrt(3); y[24:27]=np.clip(y[24:27],-a+1e-9,a-1e-9)
        starts.append(y)
    w=dict(solve.W); w.update(json.loads(os.environ.get('LANEC_W','{}')))
    if os.environ.get('LANEC_ANCHOR'):
        ctx.x_anchor=np.array(res[os.environ['LANEC_ANCHOR']]['x']); starts=[ctx.x_anchor.copy()]
    extra=os.environ.get('LANEC_SEED')
    if extra:
        for k in extra.split(','): starts.append(np.array(res[k]['x']))
    out=solve.solve(ctx,'C',starts=starts,log=log,max_nfev=300,w=w)
    cost,x,k=out[0]
    X,_=solve.hand_X(ctx,x); Rg,tg=solve.gun_T(ctx,x)
    Xg=(X-ctx.c-tg)@Rg+ctx.c; cuffref_g=(ctx.cuff_ref-ctx.c-tg)@Rg+ctx.c
    m=evaluate.evaluate_gun(ctx.G,fld,Xg,ctx.L,cuffref_g)
    m['gun_corr_deg']=float(np.degrees(np.linalg.norm(x[24:27]))); m['gun_corr_cm']=float(np.linalg.norm(x[27:30]))
    m['bore_off_deg']=float(np.degrees(np.arccos(np.clip(Rg@ctx.G['bore_axis']@np.array([1.,0,0]),-1,1))))
    m['bore_off_deg_vs_192']=float(np.degrees(np.arccos(np.clip(Rg@ctx.G['bore_axis']@ctx.G['bore_axis'],-1,1))))
    m['cant_deg']=cant_of(ctx.G,Rg); m['cant_cap']=cant
    m['cost']=cost; m['seed']=S[k][0] if k<len(S) else 'extra%d'%(k-len(S))
    res[key]=dict(x=x.tolist(),m=m,starts=[r[0] for r in out]); json.dump(res,open(p,'w'),indent=1)
    print(f'== {cls} mode {key} cant cap {cant} (wrist on the controller, gun to the hand): cost {cost:.2f}, seed {m["seed"]}',file=log)
    for rid,lab,lt,src in rules.gun_rules(m): print(f'   {lt} {rid} {lab}',file=log)
    print(f'   gun moved: {m["gun_corr_deg"]:.1f} deg, {m["gun_corr_cm"]:.1f} cm; bore off the controller aim {m["bore_off_deg"]:.1f} deg, cant {m["cant_deg"]:.1f} deg (1.92 placement {m["bore_off_deg_vs_192"]:.1f} from it); wrist q flex {x[22]:.1f} dev {x[23]:.1f}',file=log)
    return res
if __name__=='__main__':
    cap=None if len(sys.argv)<3 or sys.argv[2]=='none' else float(sys.argv[2])
    rm=None if len(sys.argv)<5 or sys.argv[4]=='none' else float(sys.argv[4]); pen=None if len(sys.argv)<6 else float(sys.argv[5])
    run(sys.argv[1],cant=cap,key=sys.argv[3] if len(sys.argv)>3 else 'C',rotmax=rm,pen=pen)
