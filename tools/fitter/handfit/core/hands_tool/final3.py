"""Round 3 final hands, in the gun's 1.92 frame, after the contact projection (depen.py: vertices deeper than 0.15 cm go back to 0.12 cm, touching) against the gun
and the other hand. Writes results/round3_final.json: per gun the gun-hand and support vertices (gun frame), the gun move
(x[24:30]), every rule, exact penetration before/after per hand, the projection report, S6.
Choices (logged in r3_*.log): pistol gun hand K5, support R3e; flamethrower gun hand C (round-2 grip) + projection,
support <SUP> (argv)."""
import numpy as np, json, os, sys
import solve, scene, exactpen, depen, evaluate, rules, fields, offwrist, fistwrap
LANE=solve.LANE
CH={'BrutalPistol':('BrutalPistol','BrutalPistol_gunhand','K5','cup'),'Flamethrower2':('Flamethrower2@nozzle','Flamethrower2_nozzle_gunhand','C','vgrip')}
def run(cls,supfile,keep=0.15,target=0.12):
    lm,gf,gk,hold=CH[cls]; F,V=scene.merged(scene.GUNS[cls]); exg=exactpen.Exact(V,F)
    x=np.array(json.load(open(os.path.join(LANE,'results',gf+'.json')))[gk]['x']); g=solve.Ctx(lm,'R',None,'gunhand')
    X,_=solve.hand_X(g,x); Rg,tg=solve.gun_T(g,x); Xg=(X-g.c-tg)@Rg+g.c; cref=(g.cuff_ref-g.c-tg)@Rg+g.c
    sx=np.array(json.load(open(os.path.join(LANE,'results',supfile)))['x']); s=solve.Ctx(lm,'L',None,hold); Xs,_=solve.hand_X(s,sx)
    rep={'gun_hand':{},'support':{}}
    rep['gun_hand']['before']=dict(into_gun=float(exg.depth(Xg).max()))
    rep['support']['before']=dict(into_gun=float(exg.depth(Xs).max()),into_gun_hand=float(exactpen.Exact(Xg,g.H.F).depth(Xs).max()))
    # 1. gun hand out of the gun; 2. support out of the gun and the (projected) gun hand; 3. gun hand out of the support
    Xg2,p1=depen.project(Xg,g.H.F,[exg],keep,target=target)
    exh=exactpen.Exact(Xg2,g.H.F); Xs2,p2=depen.project(Xs,s.H.F,[exg,exh],keep,target=target)
    Xg3,p3=depen.project(Xg2,g.H.F,[exactpen.Exact(Xs2,s.H.F),exg],keep,target=target)
    exh3=exactpen.Exact(Xg3,g.H.F); exs3=exactpen.Exact(Xs2,s.H.F)
    rep['gun_hand']['after']=dict(into_gun=float(exg.depth(Xg3).max()),into_support=float(exs3.depth(Xg3).max()))
    rep['support']['after']=dict(into_gun=float(exg.depth(Xs2).max()),into_gun_hand=float(exh3.depth(Xs2).max()))
    rep['projection']=dict(gun_hand=p1,support=p2,gun_hand_vs_support=p3)
    fld=fields.get(cls,'gun'); sfld=fields.get(cls,'sup') if hold=='vgrip' else fld
    gm=evaluate.evaluate_gun(g.G,fld,Xg3,g.L,cref); gr=rules.gun_rules(gm)
    hs=evaluate.HandSDF(Xg3,g.H.F,f'{lm}_final3_gh'.replace('@','_'))
    sm=evaluate.evaluate_support(g.G,g.S if hold=='vgrip' else {},sfld,Xs2,s.L,hold,gunhand=hs); sr=rules.support_rules(sm,hold)
    cuff_c=(Xs2[s.cuff]-g.c)@Rg.T+g.c+tg; s6=offwrist.s6(s.cuff_ref,cuff_c,'cup' if hold=='cup' else 'stab')
    th=json.load(open(os.path.join(LANE,'offwrist192.json')))['thresholds']
    if hold=='cup': s6l='G' if s6['dist_main_cm']<=13.0 and s6['off_rot_vs_main_deg']<=th['cup_rot_deg'][1]+5 else 'Y'
    else: s6l='G' if s6['support_mismatch_cm']<=th['stab_mismatch_cm'][0] and s6['reaim_deg']<=th['stab_reaim_deg'][0] else ('Y' if s6['support_mismatch_cm']<=th['stab_mismatch_cm'][1] and s6['reaim_deg']<=th['stab_reaim_deg'][1] else 'R')
    src6=('cup shows only within 13 cm (hands.zs 229); rotation vs 1.92 cup %.1f deg +5'%th['cup_rot_deg'][1]) if hold=='cup' else ('1.92 stabilised supports (20 rows): mismatch median %.1f cm / re-aim %.1f deg green, 80th %.1f / %.1f yellow'%(th['stab_mismatch_cm'][0],th['stab_reaim_deg'][0],th['stab_mismatch_cm'][1],th['stab_reaim_deg'][1]))
    lab6=('S6 support wrist vs the OFF controller (cup): off controller %.1f cm from the gun hand, turned %.1f deg'%(s6['dist_main_cm'],s6['off_rot_vs_main_deg'])) if hold=='cup' else ('S6 support wrist vs the OFF controller (two-hand steadied): gun re-aim %.1f deg, drawn vs real off hand %.1f cm'%(s6['reaim_deg'],s6['support_mismatch_cm']))
    sr=sr+[('S6',lab6,s6l,src6)]
    fw=fistwrap.measure(lm,sx) if hold=='vgrip' else None
    out=dict(cls=cls,gun_key=gk,support_file=supfile,x_gun=x.tolist(),Xg=Xg3.tolist(),Xs=Xs2.tolist(),pen=rep,gun=gm,support=sm,s6=s6,
             rules=[list(r[:3]) for r in gr+sr],rule_sources={r[0]:r[3] for r in gr+sr},fistwrap=fw)
    return out
if __name__=='__main__':
    P=os.path.join(LANE,'results','round3_final.json'); R=json.load(open(P)) if os.path.exists(P) else {}
    cls,sup=sys.argv[1],sys.argv[2]; o=run(cls,sup); R[cls]=o; json.dump(R,open(P,'w'),default=float)
    print(cls,'rules',' '.join(r[0]+r[2] for r in o['rules'])); print(json.dumps(o['pen'],default=float)); print(json.dumps(o['s6'],default=float))
    for r in o['rules']: print('  ',r[2],r[1])
