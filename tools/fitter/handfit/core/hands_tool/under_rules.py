"""Round 4 support rules for an open palm UNDER the Flamethrower2 tank (owner's words, round-3 review). All thresholds are
DEFINITIONS from the owner's request (not 1.92 statistics: 1.92 never held the tank), except S6 (1.92 steadied rows).
 U1 penetration (exact, into gun and gun hand): green <= 0.5 cm (owner), yellow <= 1.0
 U2 palm contact on the underside: |palm gap| <= 0.3 cm green (0.6 yellow) and palm within 30 deg of straight down (45)
 U3 palm normal up into the tank: angle to the direction palm->axis <= 30 deg green (45 yellow)
 U4 fingers follow the curve: every pad within 0.5 cm of the surface (1.0 yellow) and no finger loops the tank
 U5 wrap: fingertips 45..120 deg round the circumference from the palm (owner: at most ~90-120); yellow 30..150
 U6 forearm under or behind the tank, not across: top-view angle to the tank axis <= 40 deg green (60 yellow), cuff below the axis
 S6 support wrist vs the OFF controller, steadied (as round 3, 1.92's 20 steadied rows)"""
import numpy as np, json, os
import solve, exactpen, scene, offwrist, evaluate, fistwrap
LANE=solve.LANE
def light(v,g,y): return 'G' if v<=g else ('Y' if v<=y else 'R')
def measure(ctx,x,Xs,Xg,fld,gun_move):
    T=ctx.T; L=ctx.L; F,V=scene.merged(scene.GUNS['Flamethrower2']); exg=exactpen.Exact(V,F); exh=exactpen.Exact(Xg,solve.Ctx('Flamethrower2@nozzle','R',None,'gunhand').H.F)
    m={}; m['pen_gun']=float(exg.depth(Xs).max()); m['pen_gunhand']=float(exh.depth(Xs).max())
    d=fld(Xs); v=lambda k:Xs[evaluate.reg(L,k)].mean(0)
    m['palm_gap']=float(evaluate.rmin_d(d,L,'palm'))
    ang,rad,t=solve.tank_geom(ctx,v('palm')[None]); m['palm_ang']=float(ang[0]); m['palm_t']=float(t[0])
    from scipy.spatial.transform import Rotation as Rot
    n=Rot.from_rotvec(x[:3]).as_matrix()@ctx.H.axes()[2]; to=np.asarray(T['c'])+np.asarray(T['axis'])*t[0]-v('palm'); to/=np.linalg.norm(to)
    m['normal_deg']=float(np.degrees(np.arccos(np.clip(n@to,-1,1))))
    m['pads']={f:float(evaluate.rmin_d(d,L,'pad_'+f)) for f in 'IMRPT'}
    _,J=solve.hand_X(ctx,x)
    m['wrap']={}; 
    for f,fb in zip('IMRP',('INDEX','MIDDLE_F','RING','PINK')):
        a,_,_=solve.tank_geom(ctx,J[fb+'_UP_TOP_joint'][None]); m['wrap'][f]=float(abs(a[0]-ang[0]))
    # a finger LOOPS the tank if its palm->tip chain encloses the axis (fistwrap's winding test on the tank axis)
    a=np.asarray(T['axis']); c=np.asarray(T['c']); e1=np.cross(a,[0,1.,0]); e1/=np.linalg.norm(e1); e2=np.cross(a,e1)
    loops={}
    for f,fb in zip('IMRP',('INDEX','MIDDLE_F','RING','PINK')):
        P=np.array([v('palm')]+[J[fb+s] for s in ('_BASE_joint','_MID_joint','_TOP_joint','_UP_TOP_joint')])
        Q=np.stack([(P-c)@e1,(P-c)@e2],1); Q=np.vstack([Q,Q[:1]]); A=np.unwrap(np.arctan2(Q[:,1],Q[:,0])); loops[f]=bool(round((A[-1]-A[0])/(2*np.pi))!=0)
    m['loops']=loops
    cuf=Xs[ctx.cuff].mean(0); fa=v('palm')-cuf; fa2=fa.copy(); fa2[2]=0; ax=a.copy(); ax[2]=0
    m['fore_yaw']=float(np.degrees(np.arccos(np.clip(fa2@ax/np.linalg.norm(fa2)/np.linalg.norm(ax),-1,1)))); m['cuff_U']=float(cuf[2]); m['cuff_F']=float(cuf[0])
    Rg,tg=gun_move; cuff_c=(Xs[ctx.cuff]-ctx.c)@Rg.T+ctx.c+tg; m['s6']=offwrist.s6(ctx.cuff_ref,cuff_c,'stab')
    return m
def rules(m):
    th=json.load(open(os.path.join(LANE,'offwrist192.json')))['thresholds']; out=[]
    pen=max(m['pen_gun'],m['pen_gunhand'])
    out.append(('U1','no penetration (exact; gun %.2f, gun hand %.2f cm)'%(m['pen_gun'],m['pen_gunhand']),light(pen,0.5,1.0),'owner: <= 0.5 cm'))
    l2=max(light(abs(m['palm_gap']),0.3,0.6),light(abs(m['palm_ang']),30,45),key='GYR'.index)
    out.append(('U2','palm on the tank underside: gap %.2f cm, %.0f deg from straight down, %.1f cm along the tank'%(m['palm_gap'],m['palm_ang'],m['palm_t']),l2,'definition: |gap| <= 0.3 cm, <= 30 deg from the bottom'))
    out.append(('U3','palm normal up into the tank: %.0f deg off the direction to the axis'%m['normal_deg'],light(m['normal_deg'],30,45),'definition: <= 30 deg'))
    pw=max(m['pads'][f] for f in 'IMRP'); lp=light(pw,0.5,1.0); lp='R' if any(m['loops'].values()) else lp
    out.append(('U4','fingers follow the curve: worst pad gap %.2f cm (I %.2f M %.2f R %.2f P %.2f), loops %d'%(pw,m['pads']['I'],m['pads']['M'],m['pads']['R'],m['pads']['P'],sum(m['loops'].values())),lp,'definition: pads within 0.5 cm, no finger loops the tank'))
    ws=[m['wrap'][f] for f in 'IMRP']; lw='G' if min(ws)>=45 and max(ws)<=120 else ('Y' if min(ws)>=30 and max(ws)<=150 else 'R')
    out.append(('U5','wrap round the tank from the palm: %s deg (I M R P)'%' '.join('%.0f'%a for a in ws),lw,'owner: at most ~90-120 deg; green 45..120'))
    l6=light(m['fore_yaw'],40,60); l6=l6 if m['cuff_U']<-10.59 else max(l6,'Y',key='GYR'.index)
    out.append(('U6','forearm under/behind the tank: %.0f deg to the tank axis (top view), cuff at F %.1f U %.1f (axis U -10.6)'%(m['fore_yaw'],m['cuff_F'],m['cuff_U']),l6,'definition: <= 40 deg, cuff below the axis'))
    s=m['s6']; l='G' if s['support_mismatch_cm']<=th['stab_mismatch_cm'][0] and s['reaim_deg']<=th['stab_reaim_deg'][0] else ('Y' if s['support_mismatch_cm']<=th['stab_mismatch_cm'][1] and s['reaim_deg']<=th['stab_reaim_deg'][1] else 'R')
    out.append(('S6','support wrist vs the OFF controller (steadied): re-aim %.1f deg, drawn vs real off hand %.1f cm; off controller at F %.1f L %.1f U %.1f'%(s['reaim_deg'],s['support_mismatch_cm'],*s['off_origin_cm']),l,'1.92 steadied rows: median %.1f deg / %.1f cm green, 80th %.1f / %.1f yellow'%(th['stab_reaim_deg'][0],th['stab_mismatch_cm'][0],th['stab_reaim_deg'][1],th['stab_mismatch_cm'][1])))
    return out
