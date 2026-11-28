"""Round 7 final assembly (Flamethrower2 gun hand only): wrap7 solve <key> (gun frame) + depen2 edge projection;
gun turned ONLY to put the bore exactly on the aim (pitch 0, yaw 0, roll 0) and translated so the drawn cuff centre is the
controller grip's cuff centre; squeeze = the pads ON the lever (<= 1 cm) follow its 15 deg turn (fire frame 3), as r6;
support = round-4 hand (gun frame, unchanged) re-measured; spout tip + gun MODELDEF refit. Pistol and others: round 6 as is.
Writes results/round7_final.json, squeeze_r7.json, gun_modeldef_R7.json.  usage: final7.py <key>"""
import numpy as np, json, os, sys
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
import time; T0=time.time()
import solve, scene, metrics, exactpen, evaluate, handmodel, squeeze, depen2, gunplace, gunview, hudrender, gunfield, eval_under, under_rules, wrap7, rules7
LANE=solve.LANE; R=lambda p:os.path.join(LANE,'results',p); key=sys.argv[1]
c=wrap7.make_ctx(); x=np.array(json.load(open(R(f'Flamethrower2_wrap7_{key}.json')))['x']); X,J=solve.hand_X(c,x)   # gun frame
S=scene.item_verts(scene.GUNS['Flamethrower2']); Y,rep_t=depen2.project_out_of(X,c.H.F,S,near=2.0); delta=Y-X
# gun move: level the bore exactly, then translate so the drawn cuff centre = the controller grip's cuff centre
b=np.asarray(c.G['bore_axis'],float); b/=np.linalg.norm(b); ax=np.cross(b,[1.,0,0]); s_=np.linalg.norm(ax)
Rg=Rot.from_rotvec(ax/s_*np.arcsin(s_)).as_matrix() if s_>1e-12 else np.eye(3)
cu=Y[c.cuff].mean(0); tg=c.cuff_ref.mean(0)-((cu-c.c)@Rg.T+c.c)
print('projected %.0fs'%(time.time()-T0),rep_t,flush=True)
x_gun=np.r_[x[:24],Rot.from_matrix(Rg).as_rotvec(),tg]
Yc=solve.gmove(c,Rg,tg,Y); turn,cuff_cm=metrics.wrist_dev(Yc[c.cuff],c.cuff_ref)
ba=Rg@b; pitch=float(np.degrees(np.arcsin(ba[2]))); yaw=float(np.degrees(np.arctan2(ba[1],ba[0])))
import run_wrist; roll=float(run_wrist.cant_of(c.G,Rg))
fa=Yc[c.L['palm']]-Yc[c.cuff].mean(0); fr=c.ref[c.L['palm']]-c.cuff_ref.mean(0)
g=dict(pitch=pitch,yaw=yaw,roll=roll,cuff_cm=cuff_cm,hand_turn_deg=turn,forearm_dir_deg=metrics.angle(fa,fr))
# squeeze: fingers on the lever follow it (ready frame 0 -> fire frame 3, body aligned)
fr_,_=squeeze.gun_frames('Flamethrower2'); Rk,tk=metrics.rigid(fr_[0]['trig'],fr_[3]['trig'])
regs={f:evaluate.reg(c.L,'pad_'+f) for f in 'IMRP'}
onl=[f for f in 'IMRP' if np.min(np.abs(c.lever(Y[regs[f]])))<=1.0]
tgt={f:Rk@Y[regs[f]].mean(0)+tk for f in onl}
fing=np.isin(c.H.dom,[wrap7.FING[f]+s for f in onl for s in ('_BASE_joint','_MID_joint','_TOP_joint','_UP_TOP_joint')])
def X_of(q12): y=x.copy(); y[6:18]=q12; return solve.hand_X(c,y)[0]+np.where(fing[:,None],0,delta)
def res(q12):
    Xn=X_of(q12); r=[]
    for f in onl: r+=list(3.0*(Xn[regs[f]].mean(0)-tgt[f]))
    return np.array(r+list(0.05*(q12-x[6:18])/np.array([1,1,30]*4)))
lo=handmodel.QLO[0:12]; hi=handmodel.QHI[0:12]
s=least_squares(res,np.clip(x[6:18],lo+1e-9,hi-1e-9),bounds=(lo,hi)); Xs=X_of(s.x)
Xs2,rep_s=depen2.project_out_of(Xs,c.H.F,[(fr_[3]['F'],fr_[3]['V'])],near=2.0)
exr=exactpen.Exact(fr_[0]['V'],fr_[0]['F']); ex3=exactpen.Exact(fr_[3]['V'],fr_[3]['F'])
pen=dict(trigger_hand_in_gun_ready=float(exr.depth(Y).max()),squeeze_hand_in_gun_fire=float(ex3.depth(Xs2).max()))
for nm,XX,ff in (('trigger_gun_in_hand_ready',Y,fr_[0]),('squeeze_gun_in_hand_fire',Xs2,fr_[3])):
    P=gunfield.sample_surface(ff['V'],ff['F'],0.06)[0]; lo_,hi_=XX.min(0)-1,XX.max(0)+1; P=P[np.all((P>lo_)&(P<hi_),1)]; P=P[cKDTree(XX).query(P)[0]<2.0]; pen[nm]=float(exactpen.Exact(XX,c.H.F).depth(P).max())
m=rules7.measure(c,x,Y); rr=rules7.rules(m,g)
msq=rules7.measure(c,np.r_[x[:6],s.x,x[18:]],Xs2)
# support (round-4 hand, gun frame) with the new gun move
R4=json.load(open(R('round4_final.json'))); F4=R4['Flamethrower2']
d=json.load(open(R('Flamethrower2_under_D.json'))); cu_,fld,_,_=eval_under.ctx_for(d['T']); Xsup=np.array(F4['Xs'])
mu=under_rules.measure(cu_,np.array(d['x']),Xsup,Y,fld,(Rg,tg)); ru=under_rules.rules(mu)
# spout tip: centre of the heat-shield's front opening (r6 definition: results/round6_final.json tip_gun), moved
tip=np.array(json.load(open(R('round6_final.json')))['Flamethrower2']['tip_gun']); tip_c=solve.gmove(c,Rg,tg,tip[None])[0]
it=scene.GUNS['Flamethrower2']; V=np.concatenate([s__['xyz'][it['frame']] for s__ in scene.md3_full(it['path'])]); Pf=gunview.to_fl(hudrender.to_local(V,it))
md=gunplace.fit(it,solve.gmove(c,Rg,tg,Pf))
GM=json.load(open(R('gun_modeldef_R6.json'))); GM['Flamethrower2']=md; json.dump(GM,open(R('gun_modeldef_R7.json'),'w'),indent=1)
R6=json.load(open(R('round6_final.json'))); F7=dict(R6['Flamethrower2'])
F7.update(x_gun=x_gun.tolist(),Xg=Y.tolist(),Xs=Xsup.tolist(),rules=[list(a[:3]) for a in rr]+[list(a[:3]) for a in ru],rule_sources={a[0]:a[3] for a in rr+ru},wrap=m,wrap_squeeze=msq,under=mu,
          pen=pen,projection=dict(trigger=rep_t,squeeze=rep_s),wrist=dict(flex=float(x[22]),dev=float(x[23])),gun=g,tip_gun=tip.tolist(),tip_controller_cm=tip_c.tolist(),
          support_pose='under (round 4, unchanged)',gun_pose='gas-pump wrap, hand rotation released (round 7, wrap7 %s)'%key,on_lever=onl)
R6['Flamethrower2']=F7; json.dump(R6,open(R('round7_final.json'),'w'),default=float)
SQ=json.load(open(R('squeeze_r6.json'))); SQ['Flamethrower2']=dict(Xsq=Xs2.tolist(),q_trigger=x[6:18].tolist(),q_squeeze=s.x.tolist(),on_lever=onl,
   pad_err_cm={f:float(np.linalg.norm(Xs[regs[f]].mean(0)-tgt[f])) for f in onl},pad_moved_cm={f:float(np.linalg.norm(tgt[f]-Y[regs[f]].mean(0))) for f in onl})
json.dump(SQ,open(R('squeeze_r7.json'),'w'))
for a in rr+ru: print('  ',a[2],a[0],a[1])
print('squeeze-frame wrap: W3',msq['winding'],'lever',msq['lever'])
print('pen',json.dumps(pen)); print('squeeze',onl,SQ['Flamethrower2']['pad_err_cm'],SQ['Flamethrower2']['pad_moved_cm']); print('gun',g); print('tip',tip_c.round(2)); print('modeldef',md)
