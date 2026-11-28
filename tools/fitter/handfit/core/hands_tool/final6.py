"""Round 6 final assembly: Flamethrower2 gun hand = Z3 (gas-pump, pitch 0, wrist dev -17.8) + depen2 edge projection;
squeeze = index/middle/ring follow the lever's 15 deg turn (fire frame 3); support = round-4 hand (gun frame, unchanged)
re-measured with the new gun move; spout tip measured; gun MODELDEF fit; pistol copied from round 4/5 untouched.
Writes results/round6_final.json, results/squeeze_r6.json, results/gun_modeldef_R6.json."""
import numpy as np, json, os
from scipy.optimize import least_squares
import solve, scene, metrics, exactpen, evaluate, handmodel, squeeze, pump_rules, depen2, gunplace, gunview, hudrender, gunfield, eval_under, under_rules
LANE=solve.LANE; R=lambda p:os.path.join(LANE,'results',p)
c,x=pump_rules.ctx_from('Z3'); X,J=solve.hand_X(c,x); Rg,tg=solve.gun_T(c,x); tog=lambda A:(np.atleast_2d(A)-c.c-tg)@Rg+c.c
Xraw=tog(X); S=scene.item_verts(scene.GUNS['Flamethrower2'])
Y,rep_t=depen2.project_out_of(Xraw,c.H.F,S); delta=Y-Xraw
# squeeze: follow the lever (ready frame 0 -> fire frame 3, body aligned)
fr,ttris=squeeze.gun_frames('Flamethrower2'); Rk,tk=metrics.rigid(fr[0]['trig'],fr[3]['trig'])
L=c.L; regs={f:evaluate.reg(L,'pad_'+f) for f in 'IMR'}; tgt={f:Rk@Y[regs[f]].mean(0)+tk for f in 'IMR'}
fing=np.isin(c.H.dom,[f+s for f in ('INDEX','MIDDLE_F','RING') for s in ('_BASE_joint','_MID_joint','_TOP_joint','_UP_TOP_joint')])
def X_of(q9): y=x.copy(); y[6:15]=q9; return tog(solve.hand_X(c,y)[0])+np.where(fing[:,None],0,delta)
def res(q9):
    Xn=X_of(q9); r=[]
    for f in 'IMR': r+=list(3.0*(Xn[regs[f]].mean(0)-tgt[f]))
    return np.array(r+list(0.05*(q9-x[6:15])/np.array([1,1,30]*3)))
s=least_squares(res,x[6:15],bounds=(handmodel.QLO[0:9]-1e-9,handmodel.QHI[0:9]+1e-9)); Xs=X_of(s.x)
Xs2,rep_s=depen2.project_out_of(Xs,c.H.F,[(fr[3]['F'],fr[3]['V'])])
exr=exactpen.Exact(fr[0]['V'],fr[0]['F']); ex3=exactpen.Exact(fr[3]['V'],fr[3]['F'])
pen=dict(trigger_hand_in_gun_ready=float(exr.depth(Y).max()),squeeze_hand_in_gun_fire=float(ex3.depth(Xs2).max()))
for nm,XX,ff in (('trigger_gun_in_hand_ready',Y,fr[0]),('squeeze_gun_in_hand_fire',Xs2,fr[3])):
    P=gunfield.sample_surface(ff['V'],ff['F'],0.06)[0]; lo,hi=XX.min(0)-1,XX.max(0)+1; P=P[np.all((P>lo)&(P<hi),1)]; pen[nm]=float(exactpen.Exact(XX,c.H.F).depth(P).max())
m=pump_rules.measure(c,x,Y); rr=pump_rules.rules_of(m)
# support (round 4 hand, gun frame) with the new gun move
R4=json.load(open(R('round4_final.json'))); F4=R4['Flamethrower2']
d=json.load(open(R('Flamethrower2_under_D.json'))); cu,fld,_,_=eval_under.ctx_for(d['T']); Xsup=np.array(F4['Xs'])
mu=under_rules.measure(cu,np.array(d['x']),Xsup,Y,fld,(Rg,tg)); ru=under_rules.rules(mu)
# spout tip (gun frame): centroid of surface-0 points within 0.5 cm of its front end
P0=gunfield.sample_surface(S[0][1],S[0][0],0.1)[0]; tip=P0[P0[:,0]>P0[:,0].max()-0.5].mean(0); tip_c=solve.gmove(c,Rg,tg,tip[None])[0]
it=scene.GUNS['Flamethrower2']; V=np.concatenate([s_['xyz'][it['frame']] for s_ in scene.md3_full(it['path'])]); Pf=gunview.to_fl(hudrender.to_local(V,it))
md=gunplace.fit(it,solve.gmove(c,Rg,tg,Pf))
GM=json.load(open(R('gun_modeldef_R3.json'))); GM['Flamethrower2']=md; json.dump(GM,open(R('gun_modeldef_R6.json'),'w'),indent=1)
F6=dict(F4); F6.update(x_gun=x.tolist(),Xg=Y.tolist(),rules=[list(a[:3]) for a in rr]+[list(a[:3]) for a in ru],rule_sources={a[0]:a[3] for a in rr+ru},pump=m,under=mu,
      pen=pen,projection=dict(trigger=rep_t,squeeze=rep_s),wrist=dict(flex=float(x[22]),dev=float(x[23])),tip_gun=tip.tolist(),tip_controller_cm=tip_c.tolist(),support_pose='under (round 4, unchanged)',gun_pose='gas-pump (round 6)')
R6=dict(R4); R6['Flamethrower2']=F6; json.dump(R6,open(R('round6_final.json'),'w'),default=float)
SQ=json.load(open(R('squeeze_r5.json'))); SQ['Flamethrower2']=dict(Xsq=Xs2.tolist(),q_trigger=x[6:15].tolist(),q_squeeze=s.x.tolist(),pad_err_cm={f:float(np.linalg.norm(Xs[regs[f]].mean(0)-tgt[f])) for f in 'IMR'},pad_moved_cm={f:float(np.linalg.norm(tgt[f]-Y[regs[f]].mean(0))) for f in 'IMR'})
json.dump(SQ,open(R('squeeze_r6.json'),'w'))
print(' '.join(a[0]+a[2] for a in rr+ru)); [print('  ',a[2],a[0],a[1]) for a in rr+ru]
print('pen',json.dumps(pen)); print('squeeze pads',SQ['Flamethrower2']['pad_err_cm'],SQ['Flamethrower2']['pad_moved_cm']); print('tip gun',tip.round(2),'controller',tip_c.round(2)); print('modeldef',md)
