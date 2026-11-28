"""Round 4: Flamethrower2 support = open palm cupped UNDER the tank (owner, round-3 review). Solved in the gun's 1.92 frame
against the gun's distance field ('tank' crop + full gun) and the round-3 gun hand (C + projection, round3_final.json).
Tank (measured, ROUND4_notes.json): axis +F, centre (L 0.02, U -10.59), r 6.45 cm, usable F 22..34.
Terms (solve.under_terms): palm touching, within palm_ang of straight down, F inside the tank; palm normal within
normal_deg of the direction to the axis; pads + proximal segments touching; each fingertip wraps wrap_lo..wrap_hi deg
from the palm around the axis; forearm within fore_deg of the axis in top view and cuff below the axis; S6 (off controller)
as round 3; penetration tolerance pen. Pose prior: toward a half-open hand (their fbx_cup family), not the fist.
usage: run_under.py <key> [json overrides]"""
import numpy as np, json, os, sys
from scipy.spatial.transform import Rotation as Rot
import solve, fields, evaluate, handmodel, offwrist, exactpen, scene
LANE=solve.LANE; cls='Flamethrower2@nozzle'
key=sys.argv[1]; OV=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
R3=json.load(open(os.path.join(LANE,'results','round3_final.json')))['Flamethrower2']
gx=np.array(R3['x_gun']); Xg=np.array(R3['Xg'])
gctx=solve.Ctx(cls,'R',None,'gunhand'); Rg,tg=solve.gun_T(gctx,gx)
hsdf=evaluate.HandSDF(Xg,gctx.H.F,'Flamethrower2_r3final_gunhand')
ft=fields.get('Flamethrower2','tank'); fg=fields.get('Flamethrower2','gun')
def fld(P): return np.minimum(ft(P),fg(P))
ctx=solve.Ctx(cls,'L',fld,'under',other_sdf=hsdf); ctx.Lg=gctx.L
ctx.T=dict(axis=[1.0,-0.0001,-0.0005],c=[0.0,0.02,-10.59],r=6.45,t_lo=23.0,t_hi=33.0,contact=-0.05,palm_ang=25.0,normal_deg=25.0,wrap_lo=45.0,wrap_hi=110.0,fore_deg=40.0)
ctx.T.update(OV.get('T',{}))
th=json.load(open(os.path.join(LANE,'offwrist192.json')))['thresholds']
ctx.s6_kind='stab'; ctx.s6_gun=(Rg,tg); ctx.s6_ref=dict(dist=0,rot=0,cm=th['stab_mismatch_cm'][0],deg=th['stab_reaim_deg'][0])
solve.TOL['pen']=OV.get('pen',0.2); solve.TOL['pen_other']=0.1
w=dict(solve.W); w.update(dict(palm=2.0,pads=1.5,side=2.0,wrap=1.5,fore_u=1.0,s6=OV.get('s6',0.5),prior=0.4)); w.update(OV.get('w',{}))
# pose prior: an open, slightly cupped hand = 0.35 of the FBX fist curl, spreads 0, wrist neutral
qp=np.clip(0.35*handmodel.q_fist(),handmodel.QLO,handmodel.QHI); ctx.q_prior=qp
x_,y_,n_=ctx.H.axes()
def start(yaw,roll,f0):
    up=np.array([0,0,1.]); nt=Rot.from_rotvec(np.array([1.,0,0])*np.radians(roll)).apply(up)
    xt=np.array([np.cos(np.radians(yaw)),-np.sin(np.radians(yaw)),0.]); xt-=(xt@nt)*nt; xt/=np.linalg.norm(xt); yt=np.cross(nt,xt)
    R=np.stack([xt,yt,nt],1)@np.stack([x_,y_,n_],1).T
    x=np.r_[Rot.from_matrix(R).as_rotvec(),np.zeros(3),qp,np.zeros(6)]
    X,_=solve.hand_X(ctx,x); x[3:6]=np.array([f0,0.0,-17.1])-X[ctx.L['palm']]
    return x
starts=[start(yw,rl,f0) for yw in (20,45,70) for rl in (-15,15) for f0 in (26.0,29.0)]
for extra in OV.get('seeds',[]): starts.append(np.array(json.load(open(os.path.join(LANE,'results',extra)))['x']))
res=solve.solve(ctx,'S',starts=starts,log=sys.stdout,max_nfev=OV.get('nfev',250),w=w)
cost,x,k=res[0]
json.dump(dict(x=x.tolist(),cost=cost,start=int(k),T=ctx.T,w=w,pen=solve.TOL['pen']),open(os.path.join(LANE,'results',f'Flamethrower2_under_{key}.json'),'w'),indent=1,default=float)
print('== under',key,'cost %.2f start %d'%(cost,k))
