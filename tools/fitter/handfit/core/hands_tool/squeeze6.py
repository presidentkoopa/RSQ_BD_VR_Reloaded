"""Round 6 flamer squeeze for the gas-pump grip: the lever (separate part, surface 1) turns 15.0 deg up toward the handle
in fire frames 3/4 (measured round 5); EVERY finger on the lever (index, middle, ring) follows it: their curl/spread
re-solved so each pad lands on its trigger-pose spot moved with the lever; thumb, little finger, wrist, placement fixed.
Penetration checked both ways (hand into gun, gun/lever into hand), exact, against the fire frame."""
import numpy as np, json, os
from scipy.optimize import least_squares
import solve, scene, metrics, exactpen, evaluate, handmodel, squeeze, pump_rules, gunfield
LANE=solve.LANE
def run(key):
    ctx,x=pump_rules.ctx_from(key); X0,_=solve.hand_X(ctx,x)   # mode S: gun at identity -> gun frame
    fr,ttris=squeeze.gun_frames('Flamethrower2'); Rk,tk=metrics.rigid(fr[0]['trig'],fr[3]['trig'])
    L=ctx.L; regs={f:evaluate.reg(L,'pad_'+f) for f in 'IMR'}
    tg={f:Rk@X0[regs[f]].mean(0)+tk for f in 'IMR'}
    fld=lambda P: np.minimum(ctx.sdf(P),ctx.P['lever'](P))
    def X_of(q9): y=x.copy(); y[6:15]=q9; return solve.hand_X(ctx,y)[0]
    def res(q9):
        Xn=X_of(q9); r=[]
        for f in 'IMR': r+=list(3.0*(Xn[regs[f]].mean(0)-tg[f]))
        r+=list(0.05*(q9-x[6:15])/np.array([1,1,30]*3)); return np.array(r)
    lo=handmodel.QLO[0:9]; hi=handmodel.QHI[0:9]
    s=least_squares(res,np.clip(x[6:15],lo+1e-6,hi-1e-6),bounds=(lo,hi)); Xs=X_of(s.x)
    d3=fr[3]; ex=exactpen.Exact(d3['V'],d3['F']); exh=exactpen.Exact(Xs,ctx.H.F)
    S=scene.md3_full(scene.GUNS['Flamethrower2']['path'])
    P=gunfield.sample_surface(d3['V'],d3['F'],0.08)[0]; lo_,hi_=Xs.min(0)-1,Xs.max(0)+1; P=P[np.all((P>lo_)&(P<hi_),1)]
    out=dict(q_trigger=x[6:15].tolist(),q_squeeze=s.x.tolist(),pad_err_cm={f:float(np.linalg.norm(Xs[regs[f]].mean(0)-tg[f])) for f in 'IMR'},
             pad_moved_cm={f:float(np.linalg.norm(tg[f]-X0[regs[f]].mean(0))) for f in 'IMR'},
             pen_hand_in_gun_fire_cm=float(ex.depth(Xs).max()),pen_gun_in_hand_fire_cm=float(exh.depth(P).max()),Xsq=Xs.tolist())
    return out
if __name__=='__main__':
    import sys; o=run(sys.argv[1]); print(json.dumps({k:v for k,v in o.items() if k!='Xsq'},indent=1))
    json.dump(o,open(os.path.join(LANE,'results','flamer_pump_squeeze_r6.json'),'w'))
