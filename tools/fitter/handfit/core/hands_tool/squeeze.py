"""Round 5: the `squeeze` pose = the round-4 `trigger` gun hand with ONLY the index finger's three pose parameters
(curl base, curl distal, spread) re-solved; every other joint, the hand placement and the contact projection of the
other vertices are kept exactly. Index target = the trigger pose's index pad moved by the trigger travel:
  Flamethrower2: MEASURED from the mesh: the trigger lever (surface 1) is a separate part that turns 15.0 deg between the
    ready frame 0 and the fire frames 3/4 (rigid fit residual 0.014 cm); the pad follows that motion.
  BrutalPistol: the trigger (surface 5) is a separate part, but in the fire frames 4-6 it turns 37 deg the OTHER way
    (its face moves 0.7-1.4 cm FORWARD of the ready frame), so the mesh has no pull to measure; a 0.6 cm pull straight back
    along the reverse of that arc at the face is used (the coordinator's 0.5-0.8 cm allowance).
Penetration checked (exact) against the gun at the ready frame and at every fire frame, body-aligned; tolerance 0.5 cm."""
import numpy as np, json, os, sys
from scipy.optimize import least_squares
import solve, scene, metrics, gunview, hudrender, exactpen, fields, evaluate, handmodel
LANE=solve.LANE
CFG={'BrutalPistol':dict(lm='BrutalPistol',ready=3,fire=(4,5,6),body=4,surf=5),'Flamethrower2':dict(lm='Flamethrower2@nozzle',ready=0,fire=(3,4),body=0,surf=1)}
def gun_frames(g):
    c=CFG[g]; it=scene.GUNS[g]; S=scene.md3_full(it['path']); flu=lambda xyz: gunview.to_fl(hudrender.to_local(xyz,it))
    B0=flu(S[c['body']]['xyz'][c['ready']]); out={}
    for f in (c['ready'],)+c['fire']:
        R,t=metrics.rigid(flu(S[c['body']]['xyz'][f]),B0); V=[];F=[];n=0
        for s in S: v=flu(s['xyz'][f])@R.T+t; V.append(v); F.append(s['tris']+n); n+=len(v)
        T=flu(S[c['surf']]['xyz'][f])@R.T+t
        out[f]=dict(V=np.concatenate(V),F=np.concatenate(F),trig=T)
    return out,S[c['surf']]['tris']
def run(g):
    c=CFG[g]; R4=json.load(open(os.path.join(LANE,'results','round4_final.json')))[g]
    ctx=solve.Ctx(c['lm'],'R',None,'gunhand'); x=np.array(R4['x_gun']); Rg,tg=solve.gun_T(ctx,x)
    to_g=lambda X:(X-ctx.c-tg)@Rg+ctx.c
    Xr=to_g(solve.hand_X(ctx,x)[0]); Xf=np.array(R4['Xg']); delta=Xf-Xr
    fr,ttris=gun_frames(g); L=ctx.L; regI=evaluate.reg(L,'pad_I')
    pad0=Xf[regI].mean(0)
    if g=='Flamethrower2':
        Rk,tk=metrics.rigid(fr[c['ready']]['trig'],fr[c['fire'][0]]['trig']); target=Rk@pad0+tk; travel=float(np.linalg.norm(target-pad0)); src='mesh'
    else:
        Rk,tk=metrics.rigid(fr[c['ready']]['trig'],fr[c['fire'][1]]['trig']); fwd=Rk@pad0+tk-pad0; d=-fwd/np.linalg.norm(fwd); travel=0.6; target=pad0+travel*d; src='chosen 0.6 cm (mesh trigger moves forward on fire)'
    dom=ctx.H.dom; idx=np.isin(dom,['INDEX_BASE_joint','INDEX_MID_joint','INDEX_TOP_joint','INDEX_UP_TOP_joint'])
    exr=exactpen.Exact(fr[c['ready']]['V'],fr[c['ready']]['F']); fld=fields.get(g,'gun')
    def X_of(qi):
        y=x.copy(); y[6:9]=qi; Xn=to_g(solve.hand_X(ctx,y)[0]); return Xn+np.where(idx[:,None],0,delta)
    def res(qi):
        Xn=X_of(qi); r=list(3.0*(Xn[regI].mean(0)-target)); d_=fld(Xn[idx]); r+=list(4.0*np.maximum(0,-d_-0.25))
        r+=list(0.05*(qi-x[6:9])/np.array([1,1,30])); return np.array(r)
    lo=handmodel.QLO[0:3]; hi=handmodel.QHI[0:3]
    best=None
    for s0 in (x[6:9],x[6:9]+[0.2,0.2,0],x[6:9]+[0.4,0.1,0]):
        s=least_squares(res,np.clip(s0,lo+1e-6,hi-1e-6),bounds=(lo,hi))
        if best is None or s.cost<best.cost: best=s
    qi=best.x; Xs=X_of(qi)
    # exact penetration of the index vertices against ready + fire frames; and pad to trigger part distance per frame
    rep={}
    for f,d in fr.items():
        ex=exactpen.Exact(d['V'],d['F']); te=exactpen.Exact(d['trig'],ttris)
        rep[f]=dict(pen_index_cm=float(ex.depth(Xs[idx]).max()),pen_whole_hand_cm=float(ex.depth(Xs).max()),pad_to_trigger_cm=float(te.unsigned(Xs[regI]).min()),
                    trigger_pose_pad_to_trigger_cm=float(te.unsigned(Xf[regI]).min()))
    moved=np.linalg.norm(Xs-Xf,axis=1)
    out=dict(gun=g,travel_cm=travel,travel_source=src,q_index_trigger=x[6:9].tolist(),q_index_squeeze=qi.tolist(),pad_target_err_cm=float(np.linalg.norm(Xs[regI].mean(0)-target)),
             pad_moved_cm=float(np.linalg.norm(Xs[regI].mean(0)-pad0)),non_index_vertices_moved_max_cm=float(moved[~idx].max()),frames=rep,Xsq=Xs.tolist())
    return out
if __name__=='__main__':
    P=os.path.join(LANE,'results','squeeze_r5.json'); R=json.load(open(P)) if os.path.exists(P) else {}
    for g in sys.argv[1:]:
        o=run(g); R[g]=o; print(json.dumps({k:v for k,v in o.items() if k!='Xsq'},indent=1))
    json.dump(R,open(P,'w'))
