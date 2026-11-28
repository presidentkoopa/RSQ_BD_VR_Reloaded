"""Solve the support hand (FBX left rig) for a gun, given the solved gun hand. holds: 'vgrip' (flamer riser), 'cup' (pistol)."""
import numpy as np, sys, json, os
import solve, fields, evaluate, rules, handmodel, scene
LANE=solve.LANE
def run_support(cls,hold,gunhand_x,log=sys.stdout,mode='A',wextra=None,rolls=None):
    gun=cls.split('@')[0]
    fld=fields.get(gun,'sup') if hold=='vgrip' else fields.get(gun,'gun')
    gctx=solve.Ctx(cls,'R',None,'gunhand'); Xg,_=solve.hand_X(gctx,np.array(gunhand_x))
    Rg,tg=solve.gun_T(gctx,np.array(gunhand_x)); Xg=(Xg-gctx.c-tg)@Rg+gctx.c     # gun hand in the gun's frame
    hsdf=evaluate.HandSDF(Xg,gctx.H.F,f'{cls}_gunhand_{mode}'.replace('@','_'))
    ctx=solve.Ctx(cls,'L',fld,hold,other_sdf=hsdf); ctx.Lg=gctx.L
    q=lambda c:np.clip(ctx.q_prior*c,handmodel.QLO,handmodel.QHI)
    if hold=='vgrip':
        starts=[(r,s,q(c)) for r in (rolls or (-60,0,60,120,180,240)) for s in (-2.0,1.0) for c in (0.8,1.0)]
        fn=solve.start_vgrip
    else:
        starts=[(r,s,q(c)) for r in (-60,-30,0,30,60) for s in (-1.0,1.0) for c in (0.6,0.9)]
        fn=lambda c_,r,s,qq:solve.start_cup(c_,r,s,qq,Xg)
    w=dict(solve.W); w.update(wextra or {})
    if hold=='cup': w['side']=4.0
    res=solve.solve(ctx,'A',starts=starts,start_fn=fn,log=log,max_nfev=150,w=w)
    cost,x,st=res[0]; X,_=solve.hand_X(ctx,x)
    m=evaluate.evaluate_support(ctx.G,ctx.S,fld,X,ctx.L,hold,gunhand=hsdf); m['cost']=cost
    print(f'== {cls} support ({hold}): cost {cost:.2f}',file=log)
    for rid,lab,lt,src in rules.support_rules(m,hold): print(f'   {lt} {rid} {lab}',file=log)
    log.flush()
    return dict(x=x.tolist(),m=m,Xg=Xg.tolist())
if __name__=='__main__':
    cls,hold=sys.argv[1],sys.argv[2]
    gh=json.load(open(os.path.join(LANE,'results',f'{cls.replace("@","_")}_gunhand.json')))
    key=sys.argv[3] if len(sys.argv)>3 else 'A'
    wx=dict(s4_target=0.9,s4_gain=8,mid_contact=0.5) if hold=='vgrip' and key!='A' else None
    o=run_support(cls,hold,gh[key]['x'],mode=key,wextra=wx,rolls=(-60,240,300) if hold=='vgrip' and key!='A' else None)
    o['gunhand_key']=key; o['w_extra']=wx
    json.dump(o,open(os.path.join(LANE,'results',f'{cls.replace("@","_")}_support{"" if key=="A" else "_"+key}.json'),'w'),indent=1)
