"""Round 3 support hand: solved against the round-3 gun hand <gunkey>, in the gun's 1.92 frame; penetration tolerance
pen_tol into gun AND gun hand (grid fields; exact check after: exactpen), S6 = support wrist vs the off controller
(offwrist.py) held to the 1.92 median (offwrist192.json thresholds: stabilised re-aim 15.1 deg / mismatch 10.2 cm; cup
off-controller distance 8.9 cm / rotation 14.9 deg), S1-S5 kept (round-2 terms: vgrip wrap 0.7 / 270 deg, S4 0.9).
usage: run_support3.py <cls@v> <hold> <gunkey> <outkey> <pen_tol> [json weights]"""
import numpy as np, json, os, sys
import solve, fields, evaluate, rules, handmodel, fistwrap, offwrist, exactpen, scene
LANE=solve.LANE
cls,hold,gk,ok,pen=sys.argv[1:6]; pen=float(pen); WX=json.loads(sys.argv[6]) if len(sys.argv)>6 else {}
gun=cls.split('@')[0]; gfile=os.path.join(LANE,'results',f'{cls.replace("@","_")}_gunhand.json')
gx=np.array(json.load(open(gfile))[gk]['x'])
fld=fields.get(gun,'sup') if hold=='vgrip' else fields.get(gun,'gun')
fld_full=fields.get(gun,'gun') if hold=='vgrip' else None
gctx=solve.Ctx(cls,'R',None,'gunhand'); Xg,_=solve.hand_X(gctx,gx); Rg,tg=solve.gun_T(gctx,gx); Xg=(Xg-gctx.c-tg)@Rg+gctx.c
hsdf=evaluate.HandSDF(Xg,gctx.H.F,f'{cls}_gunhand_{gk}'.replace('@','_'))
if fld_full is not None:
    _f1,_f2=fld,fld_full
    def fld_both(P): return np.minimum(_f1(P),_f2(P))
    fld_s=fld_both
else: fld_s=fld
ctx=solve.Ctx(cls,'L',fld_s,hold,other_sdf=hsdf); ctx.Lg=gctx.L
th=json.load(open(os.path.join(LANE,'offwrist192.json')))['thresholds']
ctx.s6_kind='cup' if hold=='cup' else 'stab'; ctx.s6_gun=(Rg,tg)
ctx.s6_ref=dict(dist=th['cup_dist_cm'][0],rot=th['cup_rot_deg'][0],cm=th['stab_mismatch_cm'][0],deg=th['stab_reaim_deg'][0])
solve.TOL['pen']=pen; solve.TOL['pen_other']=float(os.environ.get('LANEC_PENOTHER',pen)); solve.TOL['contact']=float(os.environ.get('LANEC_CONTACT',solve.TOL['contact']))
w=dict(solve.W); w.update(dict(s4_target=0.9,s4_gain=8,wrap=0.7,wrap_deg=270) if hold=='vgrip' else dict(side=4.0)); w.update(dict(s6=1.0)); w.update(WX)
prev={'BrutalPistol':'BrutalPistol_support_C.json','Flamethrower2':'Flamethrower2_nozzle_support_C3.json'}[gun]
seeds=[np.array(json.load(open(os.path.join(LANE,'results',prev)))['x'])]
for extra in os.environ.get('LANEC_SSEED','').split(','):
    if extra: seeds.append(np.array(json.load(open(os.path.join(LANE,'results',extra)))['x']))
q=lambda c:np.clip(ctx.q_prior*c,handmodel.QLO,handmodel.QHI)
if hold=='vgrip':
    for r in (-60,240,300): seeds.append(np.r_[solve.start_vgrip(ctx,r,-2.0,q(1.0)),np.zeros(6)])
else:
    for r in (-30,0,30): seeds.append(np.r_[solve.start_cup(ctx,r,-1.0,q(0.9),Xg),np.zeros(6)])
if os.environ.get('LANEC_SANCHOR'):
    ctx.x_anchor=np.array(json.load(open(os.path.join(LANE,'results',os.environ['LANEC_SANCHOR'])))['x'])[:24]; seeds.insert(0,np.r_[ctx.x_anchor,np.zeros(6)])
res=solve.solve(ctx,'S',starts=seeds,log=sys.stdout,max_nfev=300,w=w)
cost,x,k=res[0]; X,_=solve.hand_X(ctx,x)
m=evaluate.evaluate_support(ctx.G,ctx.S,fld,X,ctx.L,hold,gunhand=hsdf); m['cost']=cost
F,V=scene.merged(scene.GUNS[gun]); exg=exactpen.Exact(V,F); exh=exactpen.Exact(Xg,gctx.H.F)
m['exact_pen_gun_cm']=float(exg.depth(X).max()); m['exact_pen_gunhand_cm']=float(exh.depth(X).max())
m['exact_gunhand_into_support_cm']=float(exactpen.Exact(X,ctx.H.F).depth(Xg).max())
cuff_c=(X[ctx.cuff]-ctx.c)@Rg.T+ctx.c+tg; m['s6']=offwrist.s6(ctx.cuff_ref,cuff_c,ctx.s6_kind)
if hold=='vgrip': m['fistwrap']=fistwrap.measure(cls,x)
print(f'== {cls} support {hold} on gun hand {gk}: cost {cost:.2f} start {k}')
for rid,lab,lt,src in rules.support_rules(m,hold): print(f'   {lt} {rid} {lab}')
print('   exact pen: into gun %.3f, into gun hand %.3f, gun hand into it %.3f'%(m['exact_pen_gun_cm'],m['exact_pen_gunhand_cm'],m['exact_gunhand_into_support_cm']))
print('   S6:',json.dumps({kk:(round(vv,2) if isinstance(vv,float) else vv) for kk,vv in m['s6'].items()}))
if hold=='vgrip': print('   fistwrap:',json.dumps(m['fistwrap']))
json.dump(dict(x=x.tolist(),m=m,gunhand_key=gk,w_extra=WX,pen_tol=pen),open(os.path.join(LANE,'results',f'{cls.replace("@","_")}_support_{ok}.json'),'w'),indent=1,default=float)
