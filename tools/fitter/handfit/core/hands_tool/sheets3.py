"""Round 3 check sheets: final hands (round3_final.json, gun's 1.92 frame) with the gun, rule panel incl. S6, and the
1.92 / current sheets from round 2 below it (unchanged builds)."""
import numpy as np, json, os, sys
import scene, solve, sheets, report_gun, evaluate
LANE=solve.LANE
def main(cls):
    c=report_gun.CFG[cls]; R=json.load(open(os.path.join(LANE,'results','round3_final.json')))[cls]
    lm,_,_,hold=__import__('final3').CH[cls]
    g=solve.Ctx(lm,'R',None,'gunhand'); s=solve.Ctx(lm,'L',None,hold)
    gF,gV=scene.merged(scene.GUNS[cls]); G={k:(np.array(v) if isinstance(v,list) else v) for k,v in json.load(open(os.path.join(LANE,'gun_landmarks.json')))[c['lm']].items()}
    S={k:(np.array(v) if isinstance(v,list) else v) for k,v in G['support'].items()}
    Xg=np.array(R['Xg']); Xs=np.array(R['Xs'])
    ms=[dict(V=gV,F=gF,col=(150,155,170)),dict(V=Xg,F=g.H.F,col=(214,168,140)),dict(V=Xs,F=s.H.F,col=(120,200,150))]
    gr=[tuple(r)+(R['rule_sources'][r[0]],) for r in R['rules'] if r[0].startswith('G')]; sr=[tuple(r)+(R['rule_sources'][r[0]],) for r in R['rules'] if r[0].startswith('S')]
    p=os.path.join(LANE,'sheets',f'{c["slug"]}_fbx_r3.png')
    sheets.arrangement_sheet(f'{cls} FBX round 3',ms,report_gun.marks(G,Xg,g.L,Xs,s.L,S),gr,sr,p,eye=c['eye'],look=c['look'])
    others=[os.path.join(LANE,'sheets',f'{c["slug"]}_192.png')]+([os.path.join(LANE,'sheets','flamethrower_current.png')] if cls=='Flamethrower2' else [])
    sheets.side_by_side([p]+others,os.path.join(LANE,'sheets',f'{c["slug"]}_compare.png'))
    print('wrote',p)
if __name__=='__main__': main(sys.argv[1])
