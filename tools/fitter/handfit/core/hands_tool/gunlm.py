"""Gun landmarks measured from the mesh (controller frame, cm, F/L/U). Every number printed comes from the
gun's ready-frame mesh as QZD places it (scene.GUNS, parsed from 1.92 MODELDEF.bd.txt). What is a CHOICE
(which surface is the trigger, which box holds the grip) is written here per gun and named as such.
Output per gun:
  grip_axis (unit, pointing UP the grip toward the bore), grip_c (a point on the axis), grip_len, grip_w (L width),
  grip_d (depth across the axis in the F-U plane), backstrap_top (web target), trigger_face (index pad target),
  bore_axis/bore_c, support (type, axis, centre, length/width)"""
import numpy as np, json, sys
from scipy.spatial import cKDTree
import scene, gunfield
def samples(gun,step=0.1):
    parts=scene.item_verts(gun); P=[];I=[]
    for k,(T,V) in enumerate(parts):
        S,_,_=gunfield.sample_surface(V,T,step); P.append(S); I.append(np.full(len(S),k))
    return np.concatenate(P),np.concatenate(I)
def box(P,f=(-1e9,1e9),l=(-1e9,1e9),u=(-1e9,1e9)):
    return (P[:,0]>=f[0])&(P[:,0]<=f[1])&(P[:,1]>=l[0])&(P[:,1]<=l[1])&(P[:,2]>=u[0])&(P[:,2]<=u[1])
def pca_axis(Q):
    c=Q.mean(0); _,S,Vt=np.linalg.svd(Q-c,full_matrices=False); return c,Vt[0],S
def handle_section(P,c,a,t,half=0.25):
    """samples within a slab of the axis parameter t; returns them in (a, d1, d2) coordinates"""
    q=P-c; s=q@a; m=np.abs(s-t)<half; return P[m]
def measure_handle(P,c,a,lat=np.array([0,1.,0])):
    """width (along lat) and depth (perp to a and lat) of a handle at its middle, from samples P near the axis"""
    d=np.cross(a,lat); d/=np.linalg.norm(d)
    q=P-c; return np.ptp(q@lat), np.ptp(q@d), d
def pistol(S,I):
    out={}
    # CHOICE: the grip = the frame + grip panels behind the trigger guard (F < -1.6) and under the slide (U < -3)
    g=box(S,f=(-12,-1.6),u=(-14.6,-3.0),l=(-2.5,2.5)) & np.isin(I,[3,4])
    G=S[g]; c,a,_=pca_axis(G); a=a if a[2]>0 else -a
    out['grip_axis']=a; out['grip_c']=c
    tt=(G-c)@a; out['grip_len']=float(np.ptp(tt))
    mid=handle_section(G,c,a,0.0,0.4); w,dpt,dvec=measure_handle(mid,c,a); out['grip_w']=float(w); out['grip_d']=float(dpt)
    # silhouettes in the side view (|L| < 1): rear = min F per height, front = max F per height (below the guard)
    def sil(lo,hi,fn,fmax=-1.6):
        out=[]
        for u in np.arange(lo,hi,0.25):
            q=S[(np.abs(S[:,2]-u)<0.13)&(np.abs(S[:,1])<1.0)&(S[:,0]<fmax)&np.isin(I,[3,4])]
            if len(q): k=fn(q[:,0]); out.append(q[k])
        return np.array(out)
    rear=sil(-14.0,-2.6,np.argmin); front=sil(-14.0,-6.6,np.argmax)
    # grip axis: mean direction of the two silhouettes over the hand's height (U -13..-6)
    def line(P):
        m=(P[:,2]>-13)&(P[:,2]<-6); c,a_,_=pca_axis(P[m]); return c,(a_ if a_[2]>0 else -a_)
    cr,ar=line(rear); cf,af=line(front); a=(ar+af); a/=np.linalg.norm(a)
    c=0.5*(cr+cf); out['grip_axis']=a; out['grip_c']=c; out['grip_axis_rear']=ar; out['grip_axis_front']=af
    out['grip_d']=float(np.linalg.norm(np.cross(cf-cr,a)))
    # web target: the backstrap notch = the most forward rear-silhouette point between the spur and 2.5 cm below it
    spur_u=rear[np.argmin(rear[:,0]),2]
    band=rear[(rear[:,2]<spur_u-0.2)&(rear[:,2]>spur_u-2.5)]
    out['backstrap_top']=band[np.argmax(band[:,0])]; out['rear_profile']=rear; out['front_profile']=front
    # CHOICE: the trigger is surface 5 (bbox F -0.4..1.8, U -6.8..-2.2, |L|<0.3: the blade inside the guard)
    T=S[I==5]; u0,u1=T[:,2].min(),T[:,2].max()
    band=T[np.abs(T[:,2]-(u0+0.35*(u1-u0)))<0.3]          # lower third of the blade, where a pad pulls
    out['trigger_face']=band[np.argmax(band[:,0])]          # its front face (the finger is in front of the blade)
    # bore: the slide (surface 1) long axis through the muzzle-end centre
    Sl=S[I==1]; _,ba,_=pca_axis(Sl); ba=ba if ba[0]>0 else -ba
    front=S[S[:,0]>S[:,0].max()-0.4]; out['bore_axis']=ba; out['bore_c']=front.mean(0)
    back=np.cross(np.array([0,1.,0]),out['grip_axis']); back*=-np.sign(back[0]); out['palm_side']=back/np.linalg.norm(back)
    out['support']=dict(type='cup')
    return out
def _flamer_common(S,I,out):
    T=S[I==1]; u0,u1=T[:,2].min(),T[:,2].max()
    band=T[np.abs(T[:,2]-(u0+0.35*(u1-u0)))<0.3]; out['trigger_face']=band[np.argmax(band[:,0])]   # CHOICE: lever = surface 1 ('13.l')
    tube=box(S,f=(20,60),u=(-2,4),l=(-2,2)); _,ba,_=pca_axis(S[tube]); ba=ba if ba[0]>0 else -ba
    out['bore_axis']=ba; out['bore_c']=S[S[:,0]>S[:,0].max()-1.0].mean(0)
    # CHOICE: support = the vertical riser pipe under the canister (F 13..19, U -23..-14): held as a vertical grip
    r=box(S,f=(13,19),u=(-23,-14),l=(-2,2))&(I==0); R=S[r]; rc,ra,_=pca_axis(R); ra=ra if ra[2]>0 else -ra
    rt=(R-rc)@ra; w,dpt,_=measure_handle(handle_section(R,rc,ra,0,0.4),rc,ra)
    out['support']=dict(type='vgrip',axis=ra,c=rc,len=float(np.ptp(rt)),w=float(w),d=float(dpt))
    tank=box(S,f=(18,40),u=(-17,-4),l=(-7,7))
    out['support_alt']=dict(type='under',c=np.array([S[tank][:,0].mean(),0,S[tank][:,2].min()]))
    return out
def _bar(S,I,lo,hi,step,axis_idx,sel):
    """centre line of a bar sliced along coordinate axis_idx between lo..hi; sel(q) picks the slice's points"""
    cs=[];ext=[]
    for v in np.arange(lo,hi,step):
        q=sel(S[np.abs(S[:,axis_idx]-v)<0.12])
        if len(q)<3: continue
        cs.append(0.5*(q.min(0)+q.max(0))); cs[-1][axis_idx]=v; ext.append(np.ptp(q,0))
    return np.array(cs),np.array(ext)
def flamer_post(S,I):
    """grip candidate 1: the lever guard's REAR POST (F -7.8..-4.4, U -6..-11.5), held like a pistol grip"""
    out={}
    sel=lambda q:q[(q[:,0]>-8.5)&(q[:,0]<-3.5)&(np.abs(q[:,1])<1.6)]
    m=I==0; cs,ext=_bar(S[m],I[m],-11.0,-5.99,0.25,2,sel)
    c,a,_=pca_axis(cs); a=a if a[2]>0 else -a
    out['grip_axis']=a; out['grip_c']=c; out['grip_len']=float(np.ptp((cs-c)@a)); out['grip_w']=float(np.median(ext[:,1])); out['grip_d']=float(np.median(ext[:,0]))
    back=np.cross(np.array([0,1.,0]),a); back*=-np.sign(back[0]); out['palm_side']=back
    q=S[(S[:,0]>-9)&(S[:,0]<-3)&(np.abs(S[:,1])<1.0)&(S[:,2]>-6.5)&(S[:,2]<-5)&(I==0)]
    out['backstrap_top']=q[np.argmin(q[:,0])]
    return _flamer_common(S,I,out)
def flamer_nozzle(S,I):
    """grip candidate 2: the NOZZLE BODY above the guard (F -12..-1), runs 17 deg off the bore: palm on top"""
    out={}
    sel=lambda q:q[(q[:,2]>-7.6)&(q[:,2]<2.5)&(np.abs(q[:,1])<2.6)]
    m=I==0; cs,ext=_bar(S[m],I[m],-12.0,-1.0,0.25,0,sel)
    c,a,_=pca_axis(cs); a=a if a[0]>0 else -a
    out['grip_axis']=a; out['grip_c']=c; out['grip_len']=float(np.ptp((cs-c)@a)); out['grip_w']=float(np.median(ext[:,1])); out['grip_d']=float(np.median(ext[:,2]))
    up=np.array([0,0,1.])-a[2]*a; up/=np.linalg.norm(up); out['palm_side']=up
    q=S[(np.abs(S[:,0]-(cs[:,0].min()+1.0))<0.2)&(np.abs(S[:,1])<0.6)&(I==0)&(S[:,2]>-6)]
    out['backstrap_top']=q[np.argmax(q[:,2])]
    return _flamer_common(S,I,out)
def flamer_hose(S,I):
    """grip candidate 3: the HOSE's rear vertical run (F ~-19, U -8..-12.5) behind the nozzle"""
    out={}
    sel=lambda q:q[(q[:,0]<-15)&(np.abs(q[:,1])<1.6)]
    m=I==0; cs,ext=_bar(S[m],I[m],-12.5,-7.99,0.25,2,sel)
    c,a,_=pca_axis(cs); a=a if a[2]>0 else -a
    out['grip_axis']=a; out['grip_c']=c; out['grip_len']=float(np.ptp((cs-c)@a)); out['grip_w']=float(np.median(ext[:,1])); out['grip_d']=float(np.median(ext[:,0]))
    back=np.cross(np.array([0,1.,0]),a); back*=-np.sign(back[0]); out['palm_side']=back
    q=S[(S[:,0]<-15)&(np.abs(S[:,1])<1.0)&(S[:,2]>-8.5)&(S[:,2]<-7)&(I==0)]
    out['backstrap_top']=q[np.argmin(q[:,0])]
    return _flamer_common(S,I,out)
MEASURE={'BrutalPistol':pistol,'Flamethrower2@post':flamer_post,'Flamethrower2@nozzle':flamer_nozzle,'Flamethrower2@hose':flamer_hose}
def measure(cls):
    S,I=samples(scene.GUNS[cls.split('@')[0]]); return MEASURE[cls](S,I),S,I
def jsonable(d):
    if isinstance(d,dict): return {k:jsonable(v) for k,v in d.items()}
    if isinstance(d,np.ndarray): return np.round(d,3).tolist()
    if isinstance(d,(np.floating,float)): return round(float(d),3)
    return d
if __name__=='__main__':
    out={}
    for cls in MEASURE:
        m,S,I=measure(cls); [m.pop(k,None) for k in ('rear_profile','front_profile')]; out[cls]=jsonable(m)
        print(cls,json.dumps(out[cls]),flush=True)
        a=np.array(m['grip_axis']); print('   grip axis angle from vertical (deg, in F-U):',round(float(np.degrees(np.arctan2(a[0],a[2]))),1),
              ' bore-grip angle:',round(float(np.degrees(np.arccos(abs(a@np.array(m['bore_axis']))))),1))
    json.dump(out,open(sys.argv[1],'w'),indent=1)
