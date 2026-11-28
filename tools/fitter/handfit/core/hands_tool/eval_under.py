import numpy as np, json, os, sys
import solve, fields, evaluate, under_rules
LANE=solve.LANE
def ctx_for(T):
    R3=json.load(open(os.path.join(LANE,'results','round3_final.json')))['Flamethrower2']
    g=solve.Ctx('Flamethrower2@nozzle','R',None,'gunhand'); Rg,tg=solve.gun_T(g,np.array(R3['x_gun']))
    ft=fields.get('Flamethrower2','tank'); fg=fields.get('Flamethrower2','gun'); fld=lambda P:np.minimum(ft(P),fg(P))
    c=solve.Ctx('Flamethrower2@nozzle','L',fld,'under'); c.T=T; return c,fld,np.array(R3['Xg']),(Rg,tg)
def run(key,Xs=None):
    d=json.load(open(os.path.join(LANE,'results',f'Flamethrower2_under_{key}.json'))); x=np.array(d['x'])
    c,fld,Xg,gm=ctx_for(d['T'])
    if Xs is None: Xs,_=solve.hand_X(c,x)
    m=under_rules.measure(c,x,Xs,Xg,fld,gm); r=under_rules.rules(m); return m,r
if __name__=='__main__':
    for k in sys.argv[1:]:
        m,r=run(k); print('==',k,' '.join(a[0]+a[2] for a in r))
        for a in r: print('  ',a[2],a[0],a[1])
