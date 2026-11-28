import numpy as np, sys, scene, render, solve, fields
def show(cls,x,out,title='',hold='gunhand'):
    ctx=solve.Ctx(cls,'R',None,hold)
    X,J=solve.hand_X(ctx,x); Rg,tg=solve.gun_T(ctx,x); gF,gV=scene.merged(scene.GUNS[cls]); gV=solve.gmove(ctx,Rg,tg,gV)
    L=ctx.L; G=ctx.G
    mk=[(X[L['web']],'web',(255,255,0)),(solve.gmove(ctx,Rg,tg,G['backstrap_top']),'bs',(255,0,0)),(X[L['pad_I']],'I',(0,255,255)),(solve.gmove(ctx,Rg,tg,G['trigger_face']),'trg',(0,120,255)),(X[L['palm']],'palm',(255,128,0)),(X[L['pad_T']],'T',(0,255,0))]
    ms=[dict(V=gV,F=gF,col=(150,155,170)),dict(V=X,F=ctx.H.F,col=(90,140,230)),dict(V=ctx.ref,F=ctx.H.F,col=(230,230,120),alpha=0.25)]
    ims=[render.render(ms,k,px=9,rng=None,marks=mk,title=title+' '+k) for k in ('side','left','bottom','back')]
    render.sheet(ims,2).save(out)
if __name__=='__main__': show(sys.argv[1],np.load(sys.argv[2]),sys.argv[3])
