"""Rule metrics for one displayed arrangement (gun mesh + gun hand + support hand), any hand family.
hand = dict(X=vertices FLU cm, L=landmark index dict (FBX or Ermac), cuff_ref=controller grip cuff for THIS family)"""
import numpy as np
from scipy.spatial import cKDTree
import metrics
def forearm_axis(X,L):
    """cuff (forearm stub) centroid -> knuckle centroid (the four proximal-segment regions)"""
    kn=np.mean([X[reg(L,'prox_'+f)].mean(0) for f in 'IMRP'],0); return kn-X[L['cuff']].mean(0)
def forearm_yaw(X,L,bore):
    fa=forearm_axis(X,L); fa[2]=0; b=np.array(bore,float); b[2]=0
    return float(np.degrees(np.arccos(np.clip(fa@b/np.linalg.norm(fa)/np.linalg.norm(b),-1,1))))
def reg(L,k): return L['_reg'][k] if '_reg' in L and k in L['_reg'] else [L[k]]
def rmin_d(d,L,k): return float(np.min(d[reg(L,k)]))
def rmin_dist(X,L,k,p): return float(np.min(np.linalg.norm(X[reg(L,k)]-np.asarray(p),axis=1)))
def evaluate_gun(G,sdf,X,L,cuff_ref,side='R'):
    d=sdf(X); v=lambda k:X[reg(L,k)].mean(0)
    a=np.asarray(G['grip_axis']); c=np.asarray(G['grip_c']); ps=np.asarray(G['palm_side'])
    far=-np.cross(a,ps); far/=np.linalg.norm(far); far*= (1 if side=='R' else -1)
    m=dict(pen_max=float(max(0,-d.min())),pen_p99=float(max(0,-np.percentile(d,1))))
    m['web_to_backstrap_cm']=rmin_dist(X,L,'web',G['backstrap_top'])
    m['palm_gap_cm']=rmin_d(d,L,'palm'); m['palm_behind_axis_cm']=float((v('palm')-c)@ps)
    kn=X[L['prox_P']]-X[L['prox_I']]; m['grip_vs_knuckles_deg']=float(np.degrees(np.arccos(abs(kn@a)/np.linalg.norm(kn))))
    for f in 'MRP':
        m[f'pad_{f}_gap_cm']=rmin_d(d,L,'pad_'+f); m[f'pad_{f}_front_cm']=float(-(X[L['prox_'+f]]-c)@ps)
    m['thumb_side_cm']=float((v('pad_T')-c)@far); m['pad_T_gap_cm']=rmin_d(d,L,'pad_T')
    m['index_to_trigger_cm']=rmin_dist(X,L,'pad_I',G['trigger_face'])
    m['index_gap_cm']=rmin_d(d,L,'pad_I')
    m['wrist_rot_vs_controller_deg'],m['wrist_move_vs_controller_cm']=metrics.wrist_dev(X[L['cuff']],cuff_ref)
    m['forearm_yaw_deg']=forearm_yaw(X,L,G['bore_axis'])
    return m
def evaluate_support(G,S,sdf,X,L,kind,gunhand=None):
    d=sdf(X); v=lambda k:X[reg(L,k)].mean(0); m={}
    dd=d.copy()
    if gunhand is not None:
        gtree=gunhand; dg=gtree(X); dd=np.minimum(d,dg)
        m['pen_into_gunhand_cm']=float(max(0,-dg.min()))
    m['pen_max_cm']=float(max(0,-d.min(),m.get('pen_into_gunhand_cm',0)))
    m['pads_gap']={f:rmin_d(dd,L,'pad_'+f) for f in 'IMRPT'}; m['palm_gap']=rmin_d(dd,L,'palm')
    if kind=='vgrip':
        a=np.asarray(S['axis']); c=np.asarray(S['c'])
        q=lambda P:(P-c)-((P-c)@a)*a
        pc=q(v('palm')); pd=np.mean([q(v('pad_'+f)) for f in 'IMRP'],0)
        m['axis_through_fist']=float(-(pc@pd)/(np.linalg.norm(pc)*np.linalg.norm(pd)+1e-9))
        kn=X[L['prox_P']]-X[L['prox_I']]; m['grip_vs_knuckles_deg']=float(np.degrees(np.arccos(abs(kn@a)/np.linalg.norm(kn))))
        m['on_bar']=float(np.mean([np.linalg.norm(q(X[L['prox_'+f]])) for f in 'MR']))
    if kind=='cup':
        c=np.asarray(G['grip_c'])
        m['thumb_side_cm']=float((v('pad_T')-c)[1]); m['pads_right']=int(sum((v('pad_'+f)-c)[1]<-0.5 for f in 'IMRP'))
    return m
class HandSDF:
    """signed distance to a (closed) hand mesh on a cached 0.3 cm grid around it (gunfield.Field: unsigned from
    dense samples, inside by generalized winding number), for support-into-gun-hand penetration and contact."""
    def __init__(s,V,F,name='hand'):
        import gunfield
        lo=V.min(0)-4; hi=V.max(0)+4
        s.f=gunfield.cached(name,V,F,lo,hi,h=0.3,band=1.0)
    def __call__(s,P): return s.f(P)
