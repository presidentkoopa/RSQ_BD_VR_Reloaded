"""Distance field of a gun mesh in the controller frame (cm): signed distance on a regular grid (trilinear lookup).
Sign: generalized winding number (robust to the small holes BD22 meshes have), computed on the grid points within
1.5 cm of the surface; farther points take the sign of their nearest near-surface neighbour region (flood by nearest).
Unsigned distance: exact point-to-triangle distance for the nearest candidate triangles (KD-tree over dense samples)."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import map_coordinates
def winding(P,A,B,C,chunk=None):
    """generalized winding number of points P wrt triangles (A,B,C) (Jacobson et al. 2013 solid-angle sum)"""
    out=np.zeros(len(P))
    if chunk is None: chunk=max(8,int(2.5e7/max(1,len(A))))   # keeps each chunk ~ <1.5 GB peak... ~25M pairs
    chunk=min(chunk,max(8,int(6e6/max(1,len(A)))))
    for s in range(0,len(P),chunk):
        p=P[s:s+chunk][:,None,:]
        a=A[None]-p; b=B[None]-p; c=C[None]-p
        la,lb,lc=(np.linalg.norm(x,axis=2) for x in (a,b,c))
        det=np.einsum('ijk,ijk->ij',a,np.cross(b,c))
        den=la*lb*lc+np.einsum('ijk,ijk->ij',a,b)*lc+np.einsum('ijk,ijk->ij',b,c)*la+np.einsum('ijk,ijk->ij',c,a)*lb
        out[s:s+chunk]=np.arctan2(det,den).sum(1)/(2*np.pi)
    return out
def sample_surface(V,F,step=0.15):
    A,B,C=V[F[:,0]],V[F[:,1]],V[F[:,2]]
    area=0.5*np.linalg.norm(np.cross(B-A,C-A),axis=1)
    n=np.maximum(1,(area/(step*step)).astype(int))
    tri=np.repeat(np.arange(len(F)),n)
    r1=np.random.default_rng(0).random(len(tri)); r2=np.random.default_rng(1).random(len(tri))
    s=np.sqrt(r1); u=1-s; v=s*(1-r2); w=s*r2
    P=A[tri]*u[:,None]+B[tri]*v[:,None]+C[tri]*w[:,None]
    N=np.cross(B-A,C-A); N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-12
    edges=np.r_[np.linspace(0,1,4)]
    # add vertices and edge points so thin parts are covered
    E=np.concatenate([A*(1-t)+B*t for t in edges]+[B*(1-t)+C*t for t in edges]+[C*(1-t)+A*t for t in edges])
    TE=np.tile(np.arange(len(F)),12)
    return np.r_[P,E],np.r_[tri,TE],N
class Field:
    def __init__(s,V,F,lo,hi,h=0.25,band=1.5):
        s.V,s.F=V,F
        s.lo=np.asarray(lo,float); s.h=h
        s.shape=tuple(np.ceil((np.asarray(hi)-s.lo)/h).astype(int)+1)
        g=[s.lo[i]+h*np.arange(s.shape[i]) for i in range(3)]
        G=np.stack(np.meshgrid(*g,indexing='ij'),-1).reshape(-1,3)
        S,ST,N=sample_surface(V,F)
        s.S,s.ST,s.N=S,ST,N
        s.tree=cKDTree(S)
        d,i=s.tree.query(G)
        # sign by winding number near the surface (and everywhere in the band), nearest-propagated beyond
        near=d<band
        A,B,C=V[F[:,0]],V[F[:,1]],V[F[:,2]]
        # only triangles that matter: within the box + margin
        cen=(A+B+C)/3; m=np.all((cen>s.lo-6)&(cen<np.asarray(hi)+6),axis=1)
        w=np.zeros(len(G))
        w[near]=winding(G[near],A[m],B[m],C[m])
        far=~near
        if far.any():
            from scipy.ndimage import label
            lab,nl=label(far.reshape(s.shape))
            lab=lab.ravel()
            for k in range(1,nl+1):
                idx=np.where(lab==k)[0]
                probe=idx[:: max(1,len(idx)//5)][:5]
                w[idx]=np.median(winding(G[probe],A[m],B[m],C[m]))
        sign=np.where(np.abs(w)>0.5,-1.0,1.0)   # |w|: the mirrored placement flips orientation; overlapping shells stack
        s.grid=(d*sign).reshape(s.shape)
        s.wind=w.reshape(s.shape)
    def __call__(s,P):
        c=((np.asarray(P)-s.lo)/s.h).T
        return map_coordinates(s.grid,c,order=1,mode='nearest')
    def grad(s,P,e=0.1):
        P=np.asarray(P); g=np.zeros_like(P)
        for k in range(3):
            d=np.zeros(3); d[k]=e; g[:,k]=(s(P+d)-s(P-d))/(2*e)
        return g

import os, hashlib
def cached(name,V,F,lo,hi,h=0.25,band=1.0,root=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'cache')):
    os.makedirs(root,exist_ok=True)
    key=hashlib.md5(np.r_[V.ravel(),F.ravel(),lo,hi,h,band].astype(np.float64).tobytes()).hexdigest()[:12]
    p=os.path.join(root,f'field_{name}_{key}.npz')
    f=Field.__new__(Field)
    if os.path.exists(p):
        d=np.load(p); f.grid=d['grid']; f.lo=d['lo']; f.h=float(d['h']); f.shape=f.grid.shape; f.V,f.F=V,F
        return f
    f=Field(V,F,lo,hi,h,band); np.savez_compressed(p,grid=f.grid,lo=f.lo,h=f.h); return f
