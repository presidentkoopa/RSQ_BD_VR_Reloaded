"""Contact projection, the last bake step (round 3): every hand vertex that is inside a target mesh (gun, other hand)
by more than `keep` cm is moved out to `keep` cm below the target's surface (exact closest point, exactpen), and the
displacement is spread to its mesh neighbours (3 Jacobi smoothing passes over the hand's edge graph, re-imposing the
constrained vertices each pass) so the skin stays smooth. Only vertices that were inside move toward the surface, so
no contact is opened into an air gap (the moved skin stays at -keep, touching). Reported: vertices moved, max move."""
import numpy as np
from scipy.sparse import coo_matrix
import exactpen
def closest(ex,P):
    out=np.zeros_like(P)
    for i,p in enumerate(P):
        d0,_=ex.tree.query(p); idx=np.asarray(ex.tree.query_ball_point(p,d0+2*ex.rmax+1e-6))
        A,B,C=ex.A[idx],ex.B[idx],ex.C[idx]; pp=np.repeat(p[None],len(idx),0)
        # closest point via pt_tri internals: recompute Q
        ab=B-A; ac=C-A; ap=pp-A
        best=None
        for j in range(len(idx)):
            q=_cp(pp[j],A[j],B[j],C[j]); dd=np.linalg.norm(q-p)
            if best is None or dd<best[0]: best=(dd,q)
        out[i]=best[1]
    return out
def _cp(p,a,b,c):
    ab=b-a; ac=c-a; ap=p-a; d1=ab@ap; d2=ac@ap
    if d1<=0 and d2<=0: return a
    bp=p-b; d3=ab@bp; d4=ac@bp
    if d3>=0 and d4<=d3: return b
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0: return a+ab*(d1/(d1-d3))
    cp=p-c; d5=ab@cp; d6=ac@cp
    if d6>=0 and d5<=d6: return c
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0: return a+ac*(d2/(d2-d6))
    va=d3*d6-d5*d4
    if va<=0 and (d4-d3)>=0 and (d5-d6)>=0: return b+(c-b)*((d4-d3)/((d4-d3)+(d5-d6)))
    den=1/(va+vb+vc); return a+ab*(vb*den)+ac*(vc*den)
def adjacency(F,n):
    e=np.r_[F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]; e=np.r_[e,e[:,::-1]]
    A=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(n,n)).tocsr(); A.data[:]=1
    deg=np.asarray(A.sum(1)).ravel(); return A,deg
def project(X,F,targets,keep=0.1,iters=4,target=None):
    """X hand verts, F hand tris, targets: list of exactpen.Exact. returns X', report"""
    X=np.array(X,float); A,deg=adjacency(F,len(X)); X0=X.copy(); rep=[]
    for it in range(iters):
        D=np.zeros_like(X); fix=np.zeros(len(X),bool)
        for ex in targets:
            dep=ex.depth(X); m=dep>keep
            if m.any():
                Q=closest(ex,X[m]); v=Q-X[m]; v/=np.linalg.norm(v,axis=1,keepdims=True)+1e-12
                D[m]+=(Q-X[m])+v*(-(keep*0.5 if target is None else target))        # to `target` below the surface (still touching)
                fix|=m
        if not fix.any(): break
        S=D.copy()
        for _ in range(3):
            S=np.where(fix[:,None],D,(A@S)/np.maximum(deg,1)[:,None]*0.6)
        X=X+S; rep.append(int(fix.sum()))
    mv=np.linalg.norm(X-X0,axis=1)
    return X,dict(passes=rep,moved_vertices=int((mv>0.01).sum()),max_move_cm=float(mv.max()),mean_move_cm=float(mv[mv>0.01].mean()) if (mv>0.01).any() else 0.0)
