"""Round 2 Flamethrower support fist: wrap term (each finger's chain turns >= 300 deg round the bar axis) + S4 target 0.9,
started from round 1's support solve and round 2's first try, plus the standard vgrip starts. Gun hand = mode C."""
import numpy as np, json, os, sys
import solve, fields, evaluate, rules, handmodel, fistwrap
LANE=solve.LANE; cls='Flamethrower2@nozzle'
gh=json.load(open(os.path.join(LANE,'results','Flamethrower2_nozzle_gunhand.json')))['C']['x']
fld=fields.get('Flamethrower2','sup')
gctx=solve.Ctx(cls,'R',None,'gunhand'); Xg,_=solve.hand_X(gctx,np.array(gh)); Rg,tg=solve.gun_T(gctx,np.array(gh)); Xg=(Xg-gctx.c-tg)@Rg+gctx.c
hsdf=evaluate.HandSDF(Xg,gctx.H.F,'Flamethrower2_nozzle_gunhand_C')
ctx=solve.Ctx(cls,'L',fld,'vgrip',other_sdf=hsdf); ctx.Lg=gctx.L
w=dict(solve.W); WX=json.loads(sys.argv[1]) if len(sys.argv)>1 else dict(s4_target=0.9,s4_gain=8,wrap=2.0,wrap_deg=300); w.update(WX)
seeds=[np.array(json.load(open(os.path.join(LANE,'results',p)))['x']) for p in ('round1/Flamethrower2_nozzle_support.json','Flamethrower2_nozzle_support_C.json')]
q=lambda c:np.clip(ctx.q_prior*c,handmodel.QLO,handmodel.QHI)
for r in (-60,240,300):
    for s in (-2.0,1.0): seeds.append(np.r_[solve.start_vgrip(ctx,r,s,q(1.0)),np.zeros(6)])
res=solve.solve(ctx,'S',starts=seeds,log=sys.stdout,max_nfev=250,w=w)
cost,x,k=res[0]; X,_=solve.hand_X(ctx,x)
m=evaluate.evaluate_support(ctx.G,ctx.S,fld,X,ctx.L,'vgrip',gunhand=hsdf); m['cost']=cost
fw=fistwrap.measure(cls,x); m['fistwrap']=fw; m={k_:(float(v_) if isinstance(v_,(np.floating,)) else v_) for k_,v_ in m.items()}
print(f'== {cls} support (vgrip, round 2 wrap): cost {cost:.2f} start {k}')
for rid,lab,lt,src in rules.support_rules(m,'vgrip'): print(f'   {lt} {rid} {lab}')
print('   fist wrap:',json.dumps(fw))
json.dump(dict(x=x.tolist(),m=m,gunhand_key='C',w_extra=WX,start=k),
          open(os.path.join(LANE,'results','Flamethrower2_nozzle_support_'+(sys.argv[2] if len(sys.argv)>2 else 'C2')+'.json'),'w'),indent=1,default=float)
