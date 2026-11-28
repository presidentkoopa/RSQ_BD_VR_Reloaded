"""Solve one gun-hand hold (mode A and B) and print the rule lights. usage: run_gun.py <cls[@variant]> [nstarts]"""
import numpy as np, sys, json, os, time
import solve, fields, evaluate, rules, handmodel
LANE=solve.LANE
def run_gunhand(cls,log=sys.stdout,modes=('A','B'),quick=False):
    gun=cls.split('@')[0]; fld=fields.get(gun,'gun')
    ctx=solve.Ctx(cls,'R',fld,'gunhand')
    q=lambda c:np.clip(ctx.q_prior*c,handmodel.QLO,handmodel.QHI)
    rolls=(-30,0,30) if not quick else (0,)
    starts=[(r,s,q(0.7)) for r in rolls for s in (-1.0,0.5)]
    out={}
    for mode in modes:
        res=solve.solve(ctx,mode,starts=starts,start_fn=solve.start_gunhand,log=log,max_nfev=150)
        cost,x,st=res[0]
        X,_=solve.hand_X(ctx,x); Rg,tg=solve.gun_T(ctx,x)
        # evaluate in the GUN's frame (move the hand by the inverse gun correction) so landmarks/sdf apply as measured
        Xg=(X-ctx.c-tg)@Rg+ctx.c; cuffref_g=(ctx.cuff_ref-ctx.c-tg)@Rg+ctx.c
        m=evaluate.evaluate_gun(ctx.G,fld,Xg,ctx.L,cuffref_g)
        m['gun_corr_deg']=float(np.degrees(np.linalg.norm(x[24:27]))); m['gun_corr_cm']=float(np.linalg.norm(x[27:30]))
        m['bore_off_deg']=float(np.degrees(np.arccos(np.clip(Rg@ctx.G['bore_axis']@ctx.G['bore_axis'],-1,1))))
        m['cost']=cost
        out[mode]=dict(x=x.tolist(),m=m,starts=[r[0] for r in res])
        os.makedirs(os.path.join(LANE,'results'),exist_ok=True)
        json.dump(out,open(os.path.join(LANE,'results',f'{cls.replace("@","_")}_gunhand.json'),'w'),indent=1)
        print(f'== {cls} mode {mode}: cost {cost:.2f}',file=log)
        for rid,lab,lt,src in rules.gun_rules(m):
            print(f'   {lt} {rid} {lab}',file=log)
        if mode=='B': print(f'   gun moved to the hand: {m["gun_corr_deg"]:.1f} deg, {m["gun_corr_cm"]:.1f} cm; bore off the controller aim {m["bore_off_deg"]:.1f} deg',file=log)
        log.flush()
    return out
if __name__=='__main__':
    cls=sys.argv[1]; quick='quick' in sys.argv
    o=run_gunhand(cls,quick=quick)
    os.makedirs(os.path.join(LANE,'results'),exist_ok=True)
    json.dump(o,open(os.path.join(LANE,'results',f'{cls.replace("@","_")}_gunhand.json'),'w'),indent=1)
