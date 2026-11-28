"""Exact penetration per hand solve (exactpen.Exact on the gun mesh in the gun's 1.92 frame): deepest, 99th pct,
count > 0.2 / > 0.1 cm, and the dominant bone of the deepest vertices. usage: penreport.py <cls> <lm> <file> <key>..."""
import numpy as np, json, sys, collections
import solve, scene, exactpen
def gun_hand_X(lm,x):
    ctx=solve.Ctx(lm,'R',None,'gunhand'); X,_=solve.hand_X(ctx,x); Rg,tg=solve.gun_T(ctx,x); return (X-ctx.c-tg)@Rg+ctx.c,ctx
if __name__=='__main__':
    cls,lm,f=sys.argv[1:4]; F,V=scene.merged(scene.GUNS[cls]); ex=exactpen.Exact(V,F)
    dom=np.array(json.load(open('../landmarks_fbx.json'))['R']['dom'])
    d=json.load(open('../results/'+f))
    for k in sys.argv[4:]:
        X,ctx=gun_hand_X(lm,np.array(d[k]['x'])); p=ex.depth(X)
        top=np.argsort(-p)[:15]; c=collections.Counter(dom[top[p[top]>0.05]])
        print('%-4s exact deepest %.3f p99 %.3f n>0.2 %d n>0.1 %d  where: %s'%(k,p.max(),np.percentile(p,99),(p>0.2).sum(),(p>0.1).sum(),dict(c.most_common(4))))
