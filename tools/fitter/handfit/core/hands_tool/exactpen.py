"""Exact penetration check (not the 0.25 cm grid): for every hand vertex, inside/outside by the generalized winding
number of the target mesh, depth = exact point-to-triangle distance to the nearest triangle (candidates by KD-tree on
triangle centroids + bounding radius). Used for the round-3 <= 0.2 cm gate. usage: from code: depth(P, V, F)"""
import numpy as np
from scipy.spatial import cKDTree
import gunfield
def pt_tri(P,A,B,C):
    # Ericson, closest point on triangle; vectorised over pairs
    ab=B-A; ac=C-A; ap=P-A
    d1=np.einsum('ij,ij->i',ab,ap); d2=np.einsum('ij,ij->i',ac,ap)
    bp=P-B; d3=np.einsum('ij,ij->i',ab,bp); d4=np.einsum('ij,ij->i',ac,bp)
    cp=P-C; d5=np.einsum('ij,ij->i',ab,cp); d6=np.einsum('ij,ij->i',ac,cp)
    va=d3*d6-d5*d4; vb=d5*d2-d1*d6; vc=d1*d4-d3*d2
    den=np.where(np.abs(va+vb+vc)<1e-18,1e-18,va+vb+vc); v=vb/den; w=vc/den
    Q=A+ab*v[:,None]+ac*w[:,None]
    m=(d1<=0)&(d2<=0); Q[m]=A[m]
    m=(d3>=0)&(d4<=d3); Q[m]=B[m]
    m=(d6>=0)&(d5<=d6); Q[m]=C[m]
    vcm=(vc<=0)&(d1>=0)&(d3<=0); t=d1/np.where(d1-d3==0,1e-18,d1-d3); m=vcm&~((d1<=0)&(d2<=0))&~((d3>=0)&(d4<=d3)); Q[m]=(A+ab*t[:,None])[m]
    vbm=(vb<=0)&(d2>=0)&(d6<=0); t=d2/np.where(d2-d6==0,1e-18,d2-d6); m=vbm&~((d1<=0)&(d2<=0))&~((d6>=0)&(d5<=d6)); Q[m]=(A+ac*t[:,None])[m]
    vam=(va<=0)&((d4-d3)>=0)&((d5-d6)>=0); t=(d4-d3)/np.where((d4-d3)+(d5-d6)==0,1e-18,(d4-d3)+(d5-d6)); m=vam&~((d3>=0)&(d4<=d3))&~((d6>=0)&(d5<=d6)); Q[m]=(B+(C-B)*t[:,None])[m]
    return np.linalg.norm(P-Q,axis=1)
class Exact:
    def __init__(s,V,F):
        s.A,s.B,s.C=V[F[:,0]],V[F[:,1]],V[F[:,2]]; cen=(s.A+s.B+s.C)/3
        s.r=np.max([np.linalg.norm(x-cen,axis=1) for x in (s.A,s.B,s.C)],0); s.tree=cKDTree(cen); s.rmax=s.r.max(); s.cen=cen
    def unsigned(s,P,k=64):
        P=np.atleast_2d(P); d0,_=s.tree.query(P); out=np.full(len(P),np.inf)
        for i,p in enumerate(P):
            idx=s.tree.query_ball_point(p,d0[i]+2*s.rmax+1e-6)
            idx=np.asarray(idx); dd=pt_tri(np.repeat(p[None],len(idx),0),s.A[idx],s.B[idx],s.C[idx]); out[i]=dd.min()
        return out
    def depth(s,P,band=3.0):
        """>0 = how far inside (cm); 0 outside. Only points within band of the surface are tested for inside."""
        P=np.atleast_2d(P); d0,_=s.tree.query(P); near=d0<band+s.rmax
        out=np.zeros(len(P))
        if near.any():
            w=gunfield.winding(P[near],s.A,s.B,s.C); ins=np.abs(w)>0.5
            if ins.any():
                Pi=P[near][ins]; out_idx=np.where(near)[0][ins]; out[out_idx]=s.unsigned(Pi)
        return out
