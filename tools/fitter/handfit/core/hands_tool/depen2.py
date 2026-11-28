"""Round 6: the other direction of the contact projection: thin gun parts / sharp edges that poke INTO the hand between
hand vertices. For every gun surface sample inside the hand by more than keep (exact: winding + closest point), the hand
skin around its exit point is pulled back past the sample (smooth falloff, radius rad), iterated. Reports moves."""
import numpy as np
from scipy.spatial import cKDTree
import exactpen, gunfield
def project_out_of(Xh,Fh,gun_parts,keep=0.3,target=0.25,rad=1.2,iters=6,near=None):
    X=np.array(Xh,float); X0=X.copy(); P=np.concatenate([gunfield.sample_surface(v,t,0.06)[0] for t,v in gun_parts])
    lo,hi=X.min(0)-1,X.max(0)+1; P=P[np.all((P>lo)&(P<hi),1)]; rep=[]
    if near is not None: P=P[cKDTree(X).query(P)[0]<near]   # round 7: only samples near the skin (speed; deeper ones are farther than any hand thickness)
    for it in range(iters):
        ex=exactpen.Exact(X,Fh); d=ex.depth(P); m=d>keep
        rep.append(float(d.max()))
        if not m.any(): break
        tree=cKDTree(X); D=np.zeros_like(X); W=np.zeros(len(X))
        for p,dd in zip(P[m],d[m]):
            _,i=tree.query(p); q=X[i]; u=p-q; u/=np.linalg.norm(u)+1e-12   # from the skin toward the buried sample
            idx=tree.query_ball_point(q,rad); w=np.clip(1-np.linalg.norm(X[idx]-q,axis=1)/rad,0,1)
            mv=u*(dd-target+0.05)          # skin moves toward/past the sample so it ends `target` deep at most
            for j,ww in zip(idx,w):
                if ww>W[j]: W[j]=ww; D[j]=mv*ww
        X=X+D
    mvn=np.linalg.norm(X-X0,axis=1)
    return X,dict(max_depth_per_pass=rep,moved_vertices=int((mvn>0.01).sum()),max_move_cm=float(mvn.max()))
