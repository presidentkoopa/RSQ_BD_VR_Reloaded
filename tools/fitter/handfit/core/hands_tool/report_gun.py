"""Per-gun deliverable: FBX solve vs 1.92 vs current, check sheets + baked MD3 + hand-table rows + metrics json.
usage: report_gun.py BrutalPistol|Flamethrower2"""
import numpy as np, json, os, sys
import scene, solve, rules, sheets, compare, evaluate, fields, bake, render, handmodel
LANE=solve.LANE
CFG={
 'BrutalPistol': dict(lm='BrutalPistol',sup='cup',builds=[('1.92',('BrutalPistol','1.92'))],slug='pistol',
                      eye=(-30,-12,12),look=(4,0,-5)),
 'Flamethrower2': dict(lm='Flamethrower2@nozzle',sup='vgrip',builds=[('1.92',('Flamethrower2','1.92')),('current (ModelSwapper)',('Flamethrower2','ModelSwapper'))],slug='flamethrower',
                      eye=(-45,-22,14),look=(15,0,-8)),
}
SUPFILE={'BrutalPistol':'BrutalPistol_support_C.json','Flamethrower2':'Flamethrower2_nozzle_support_C3.json'}
def fbx_meshes(cls,mode):
    c=CFG[cls]; gh=json.load(open(os.path.join(LANE,'results',f'{c["lm"].replace("@","_")}_gunhand.json')))[mode]
    sp=json.load(open(os.path.join(LANE,'results',SUPFILE[cls])))
    gctx=solve.Ctx(c['lm'],'R',None,'gunhand'); x=np.array(gh['x'])
    X,_=solve.hand_X(gctx,x); Rg,tg=solve.gun_T(gctx,x)
    Xg=(X-gctx.c-tg)@Rg+gctx.c                       # in the gun's 1.92 frame (where its landmarks are measured)
    sctx=solve.Ctx(c['lm'],'L',None,c['sup']); Xs,_=solve.hand_X(sctx,np.array(sp['x']))   # solved in the gun's frame
    gctx.cuff_ref_g=(gctx.cuff_ref-gctx.c-tg)@Rg+gctx.c   # the controller grip, seen from the gun's frame
    gctx.X_ctrl=X; gctx.Xs_ctrl=solve.gmove(gctx,Rg,tg,Xs)   # both hands where they are drawn (controller frame)
    return gctx,sctx,gh,sp,Xg,Xs,(Rg,tg)
def marks(G,Xh,Lh,Xs,Ls,S):
    v=lambda X,L,k:X[evaluate.reg(L,k)].mean(0)
    m=[(G['backstrap_top'],'',(255,60,60)),(G['trigger_face'],'',(60,140,255)),
       (v(Xh,Lh,'web'),'web',(255,255,0)),(v(Xh,Lh,'palm'),'palm',(255,140,0)),(v(Xh,Lh,'pad_I'),'index',(0,255,255))]
    if Xs is not None:
        m.append((v(Xs,Ls,'palm'),'sup palm',(120,255,120)))
        if 'c' in S: m.append((np.asarray(S['c']),'',(60,255,60)))
    return m
def main(cls):
    c=CFG[cls]; G={k:(np.array(v) if isinstance(v,list) else v) for k,v in json.load(open(os.path.join(LANE,'gun_landmarks.json')))[c['lm']].items()}
    S={k:(np.array(v) if isinstance(v,list) else v) for k,v in G['support'].items()}
    gF,gV=scene.merged(scene.GUNS[cls]); fld=fields.get(cls,'gun'); sfld=fields.get(cls,'sup') if c['sup']=='vgrip' else fld
    out=dict(gun=cls,arrangements={})
    os.makedirs(os.path.join(LANE,'sheets'),exist_ok=True); os.makedirs(os.path.join(LANE,'out'),exist_ok=True)
    paths=[]
    # FBX solve (mode A: ships with hooks only; mode B reported in the json)
    gctx,sctx,gh,sp,Xg,Xs,_=fbx_meshes(cls,'C')
    hs=evaluate.HandSDF(Xg,gctx.H.F,f'{c["lm"]}_gunhand_C'.replace('@','_'))
    gm=evaluate.evaluate_gun(G,fld,Xg,gctx.L,gctx.cuff_ref_g)
    sm=evaluate.evaluate_support(G,S,sfld,Xs,sctx.L,c['sup'],gunhand=hs)
    gr=rules.gun_rules(gm); sr=rules.support_rules(sm,c['sup'])
    ms=[dict(V=gV,F=gF,col=(150,155,170)),dict(V=Xg,F=gctx.H.F,col=(214,168,140)),dict(V=Xs,F=sctx.H.F,col=(120,200,150))]
    p=os.path.join(LANE,'sheets',f'{c["slug"]}_fbx_solve.png'); sheets.arrangement_sheet(f'{cls} FBX solve (round 2)',ms,marks(G,Xg,gctx.L,Xs,sctx.L,S),gr,sr,p,eye=c['eye'],look=c['look']); paths.append(p)
    out['arrangements']['FBX solve']=dict(gun=gm,support=sm,rules=[r[:3] for r in gr+sr],rule_sources={r[0]:r[3] for r in gr+sr},modeB=gh_modeB(c),modeC=dict(gun_move=gh['m'].get('gun_corr_deg'),gun_move_cm=gh['m'].get('gun_corr_cm'),bore_off_deg=gh['m'].get('bore_off_deg'),cant_deg=gh['m'].get('cant_deg'),chosen_from=gh.get('chosen_from')),round1=r1rules(c))
    # bake
    entries=[dict(name=f'{c["slug"]}_gun',side='R',X=gctx.X_ctrl,cuff_ref=gctx.cuff_ref),dict(name=f'{c["slug"]}_sup',side='L',X=gctx.Xs_ctrl,cuff_ref=sctx.cuff_ref)]
    rows,mp,_=bake.bake(entries,os.path.join(LANE,'out',f'{c["slug"]}_fbxhand.md3'))
    out['bake']=rows
    # existing builds
    for label,key in c['builds']:
        A,gm2,sm2,(L,Ls),_G=compare.measure(key,c['lm'],c['sup'])
        gr2=rules.gun_rules(gm2); sr2=rules.support_rules(sm2,c['sup'])
        ms=[dict(V=A['gun'][1],F=A['gun'][0],col=(150,155,170)),dict(V=A['hand'][1],F=A['hand'][0],col=(225,170,135)),dict(V=A['sup'][1],F=A['sup'][0],col=(120,200,140))]
        slug=label.split()[0].replace('.','')
        p=os.path.join(LANE,'sheets',f'{c["slug"]}_{slug}.png'); sheets.arrangement_sheet(f'{cls} {label}',ms,marks(G,A['hand'][1],L,A['sup'][1],Ls,S),gr2,sr2,p,eye=c['eye'],look=c['look']); paths.append(p)
        out['arrangements'][label]=dict(gun=gm2,support=sm2,rules=[r[:3] for r in gr2+sr2])
    sheets.side_by_side(paths,os.path.join(LANE,'sheets',f'{c["slug"]}_compare.png'))
    # baked-md3 render check: reload the md3s, place them with their rows, render next to the gun
    Rg_,tg_=solve.gun_T(gctx,np.array(gh['x'])); bm=[dict(V=solve.gmove(gctx,Rg_,tg_,gV),F=gF,col=(150,155,170))]
    import hudrender, hook
    for r in rows:
        sx=scene.md3_full(os.path.join(LANE,'out',r['md3']))[0]
        Y=100*(hudrender.to_local(sx['xyz'][r['frame']],dict(hook=r['hook'],rot=r['rot'],**hook.PL))@hook.P.T)
        bm.append(dict(V=Y,F=sx['tris'],col=(214,168,140) if r['side']=='R' else (120,200,150)))
    ims=[render.render(bm,k,px=7,title=f'{cls}: BAKED md3 frames reloaded + hand-table rows, {k}') for k in ('side','bottom')]+[render.render(bm,eye=c['eye'],look=c['look'],W=420,H=330,fov=55,title='baked md3 + gun MODELDEF offsets, player eye (controller frame)')]
    render.sheet(ims,3).save(os.path.join(LANE,'sheets',f'{c["slug"]}_baked_md3.png'))
    json.dump(out,open(os.path.join(LANE,'results',f'{c["slug"]}_report.json'),'w'),indent=1,default=float)
    for k,a in out['arrangements'].items():
        cnt={x:sum(1 for r in a['rules'] if r[2]==x) for x in 'GYR'}; print(f'{cls:14s} {k:24s} G {cnt["G"]} Y {cnt["Y"]} R {cnt["R"]}')
    for r in rows: print('   row',r['name'],'hook',r['hook'],'rot',r['rot'],'bake check %.3f cm'%r['bake_check_max_cm'])
def r1rules(c):
    p=os.path.join(LANE,'results','round1',f'{c["slug"]}_report.json')
    return json.load(open(p))['arrangements']['FBX solve']['rules'] if os.path.exists(p) else None
def gh_modeB(c):
    gh=json.load(open(os.path.join(LANE,'results',f'{c["lm"].replace("@","_")}_gunhand.json')))
    if 'B' not in gh: return None
    m=gh['B']['m']; return dict(cost=m['cost'],gun_corr_deg=m['gun_corr_deg'],gun_corr_cm=m['gun_corr_cm'],bore_off_deg=m['bore_off_deg'],
                                rules=[r[:3] for r in rules.gun_rules(m)])
if __name__=='__main__': main(sys.argv[1])
