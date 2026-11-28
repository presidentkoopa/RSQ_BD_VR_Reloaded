"""Hand landmarks as VERTEX INDICES of the FBX mesh (so they ride the skin in any pose), found from the
rig's joints and the mesh at the authored open pose (frame 56). All in the palm frame (FBX units).
  palm side n: the side the fingers close toward (fist frame 517 fingertips minus knuckles, minus its finger-axis part)
  web:   the skin in the thumb-index crotch: surface point on the ray from the thumb-base/index-base midpoint
         toward the gap between thumb tip and index middle joint (the point that sits on a pistol's backstrap)
  palm:  palm-side surface point over the middle of the metacarpals (palm centre)
  pad_X: palm-side surface of each finger's distal segment, mid-length; pad_T thumb likewise
  cuff:  vertices skinned mostly to Root_joint (the wrist/forearm stub)"""
import numpy as np, json
import handmodel
def compute(side='R'):
    H=handmodel.FbxHand(side); h=H.h
    V,J=H.pose(handmodel.q_open())    # authored open (frame 56)
    Vf,Jf=H.pose(handmodel.q_fist())  # authored fist (frame 517)
    P=lambda J,k:J[k]
    x=P(J,'MIDDLE_F_BASE_joint')-P(J,'HANDPALM_joint'); x/=np.linalg.norm(x)
    tips=np.mean([P(Jf,f+'_UP_TOP_joint') for f in ('INDEX','MIDDLE_F','RING','PINK')],0)
    kn=np.mean([P(Jf,f+'_BASE_joint') for f in ('INDEX','MIDDLE_F','RING','PINK')],0)
    n=tips-kn; n-=(n@x)*x; n/=np.linalg.norm(n)
    # dominant bone per vertex
    W=np.zeros((len(h.V),len(h.clusters)))
    names=[c['name'] for c in h.clusters]
    for k,c in enumerate(h.clusters): W[c['idx'],k]=c['w']
    dom=np.array([names[i] for i in W.argmax(1)])
    L={}
    M=0.5*(P(J,'THUMB_BASE_joint')+P(J,'INDEX_BASE_joint'))
    gap=0.5*(P(J,'THUMB_TOP_joint')+P(J,'INDEX_MID_joint')); d=gap-M; d/=np.linalg.norm(d)
    q=V-M; t=q@d; perp=np.linalg.norm(q-np.outer(t,d),axis=1)
    cand=np.where((t>0)&(t<0.6))[0]; L['web']=int(cand[np.argmin(perp[cand])])
    P0=0.5*(P(J,'HANDPALM_joint')+kn*0+np.mean([P(J,f+'_BASE_joint') for f in ('INDEX','MIDDLE_F','RING','PINK')],0))
    q=V-P0; lat=q-np.outer(q@n,n)
    cand=np.where((np.linalg.norm(lat,axis=1)<0.12)&(np.isin(dom,['HANDPALM_joint','Root_joint'])))[0]
    L['palm']=int(cand[np.argmax(q[cand]@n)])
    for f,tag in (('INDEX','I'),('MIDDLE_F','M'),('RING','R'),('PINK','P'),('THUMB','T')):
        a=P(J,f+'_TOP_joint'); b=P(J,f+'_UP_TOP_joint'); mid=0.5*(a+b)
        # the pad faces the way this finger closes: use the fist's TOP joint motion
        nf=P(Jf,f+'_UP_TOP_joint')-P(J,f+'_UP_TOP_joint') if f!='THUMB' else (P(Jf,'THUMB_UP_TOP_joint')-P(J,'THUMB_UP_TOP_joint'))
        ax=b-a; ax/=np.linalg.norm(ax); nf-= (nf@ax)*ax; nf/=np.linalg.norm(nf)
        q=V-mid; along=q@ax
        cand=np.where((np.abs(along)<0.6*np.linalg.norm(b-a))&(np.isin(dom,[f+'_TOP_joint',f+'_UP_TOP_joint'])))[0]
        L['pad_'+tag]=int(cand[np.argmax(q[cand]@nf)])
        # proximal-segment palm side (for "middle/ring/little wrap the front strap")
        a2=P(J,f+'_BASE_joint'); b2=P(J,f+'_MID_joint'); mid2=0.5*(a2+b2)
        q2=V-mid2; ax2=(b2-a2)/np.linalg.norm(b2-a2)
        cand2=np.where((np.abs(q2@ax2)<0.4*np.linalg.norm(b2-a2))&(dom==f+'_BASE_joint'))[0]
        if len(cand2): L['prox_'+tag]=int(cand2[np.argmax(q2[cand2]@n)])
    L['cuff']=np.where(dom=='Root_joint')[0].tolist()
    L['dom']=dom.tolist()
    L['n_palm']=n.tolist(); L['x_fingers']=x.tolist()
    return L
if __name__=='__main__':
    import sys
    out={'R':compute('R')}; out['L']=dict(out['R'])   # same topology in both rigs: the same vertex is the same skin spot
    json.dump(out,open(sys.argv[1],'w'))
    for s in out: print(s,{k:v for k,v in out[s].items() if isinstance(v,int)},'cuff',len(out[s]['cuff']))
