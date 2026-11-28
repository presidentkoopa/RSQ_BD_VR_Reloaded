"""Round 3 option: GUN FIXED where 1.92 draws it (no MODELDEF change => no layer moves), hand wrist held to the
controller grip within TOLC (6 deg / 6 cm, 1.92 G8 green = 7.5 / 7.3), contact penetration tolerance pen_tol.
Seeds: round 1 mode A, round 2 mode C (hand moved by the inverse gun move so the gun is back at 1.92), and their
wrists pulled onto the controller grip. usage: run_fixed.py <cls[@v]> <pen_tol> <key>"""
import numpy as np, sys, json, os
from scipy.spatial.transform import Rotation as Rot
import solve, fields, evaluate, rules, metrics
LANE=solve.LANE
def run(cls,pen,key):
    gun=cls.split('@')[0]; fld=fields.get(gun,'gun'); ctx=solve.Ctx(cls,'R',fld,'gunhand')
    p=os.path.join(LANE,'results',f'{cls.replace("@","_")}_gunhand.json'); res=json.load(open(p))
    seeds=[]
    for m in ('A','C'):
        x=np.array(res[m]['x']); Rg,tg=solve.gun_T(ctx,x); X,_=solve.hand_X(ctx,x)
        Xg=(X-ctx.c-tg)@Rg+ctx.c; Rm,tm=metrics.rigid(X,Xg)        # hand into the 1.92 gun frame
        y=x.copy(); y[:3]=Rot.from_matrix(Rm@Rot.from_rotvec(x[:3]).as_matrix()).as_rotvec(); y[3:6]=Rm@x[3:6]+tm; y[24:]=0
        seeds.append(y)
        # the same, wrist pulled half way onto the controller grip by rotating the whole hand about the palm
        Y,_=solve.hand_X(ctx,y); Rw,tw=metrics.rigid(Y[ctx.cuff],ctx.cuff_ref)
        h=Rot.from_matrix(Rw).as_rotvec()*0.5; z=y.copy(); Rh=Rot.from_rotvec(h).as_matrix()
        z[:3]=Rot.from_matrix(Rh@Rot.from_rotvec(y[:3]).as_matrix()).as_rotvec(); pc=Y[ctx.L['palm']]; z[3:6]=Rh@(y[3:6]-pc)+pc
        seeds.append(z)
    solve.TOL['pen']=pen; solve.TOLC['cant']=None
    out=solve.solve(ctx,'D',starts=seeds,log=sys.stdout,max_nfev=250)
    cost,x,k=out[0]; X,_=solve.hand_X(ctx,x)
    m=evaluate.evaluate_gun(ctx.G,fld,X,ctx.L,ctx.cuff_ref); m['cost']=cost; m['pen_tol']=pen
    res[key]=dict(x=x.tolist(),m=m); json.dump(res,open(p,'w'),indent=1)
    print(f'== {cls} {key} gun FIXED, pen tol {pen}: cost {cost:.2f}')
    for rid,lab,lt,src in rules.gun_rules(m): print(f'   {lt} {rid} {lab}')
if __name__=='__main__': run(sys.argv[1],float(sys.argv[2]),sys.argv[3])
