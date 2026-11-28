"""Round 6: Flamethrower2 gun hand = GAS-PUMP grip (owner, r5 headset). Mode C (wrist pinned to the controller grip, the gun
moves to the hand, bore within 4 deg of the controller aim, roll about the bore capped), terms solve.pump_terms.
Geometry measured from the mesh (results/nozzle_profile_r6.json): handle bar F -12..-5 (top U -3.5..-1.3, 3.6 cm wide,
~3.3 cm tall), lever (surface 1) F -4..+3, U -11.3..-5.7, turning 15 deg up toward the handle in the fire frames.
usage: run_pump.py <key> [json overrides]"""
import numpy as np, json, os, sys
from scipy.spatial.transform import Rotation as Rot
import solve, fields, gunfield, scene, metrics, handmodel, evaluate
LANE=solve.LANE; cls='Flamethrower2@nozzle'; key=sys.argv[1]; OV=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
prof=json.load(open(os.path.join(LANE,'results','nozzle_profile_r6.json')))
Fs=np.array(sorted(float(k) for k in prof['top'])); top=np.array([prof['top'][str(f) if str(f) in prof['top'] else f] for f in Fs]) if False else np.array([prof['top'][k] for k in sorted(prof['top'],key=float)])
low=np.array([prof['bottom_of_body'][k] for k in sorted(prof['top'],key=float)])
lv=[prof['lever'][k] for k in sorted(prof['top'],key=float)]; lever_lo=np.array([a[0] if a else np.nan for a in lv])
S=scene.item_verts(scene.GUNS['Flamethrower2']); lev=gunfield.cached('Flamethrower2_lever',S[1][1],S[1][0],(-7,-4,-14),(8,4,-3),h=0.1,band=1.0)
fld=fields.get('Flamethrower2','gun')
ctx=solve.Ctx(cls,'R',fld,'pump')
R4=json.load(open(os.path.join(LANE,'results','round4_final.json')))['Flamethrower2']
regI=evaluate.reg(ctx.L,'pad_I'); idx_t=np.array(R4['Xg'])[regI].mean(0)
m=~np.isnan(lever_lo)
ctx.P=dict(F=Fs,top=top,low=low,lever_lo=np.interp(Fs,Fs[m],lever_lo[m],left=np.nan,right=np.nan),lever=lev,bar_axis=[0.957,-0.001,0.292],
           contact=0.05,palm_f=(-11.0,-3.5),palm_below_top=1.2,normal_deg=35.0,under_tol=0.4,little_w=0.3,index_target=idx_t.tolist())
ctx.P['lever_lo']=np.where((Fs>=-4.0)&(Fs<=3.0),ctx.P['lever_lo'],np.nan)
ctx.P.update(OV.get('P',{}))
if OV.get('dev_max'): handmodel.QLO[17]=-OV['dev_max']; handmodel.QHI[17]=OV['dev_max']
if OV.get('dev_fix') is not None: handmodel.QLO[17]=OV['dev_fix']-0.01; handmodel.QHI[17]=OV['dev_fix']+0.01
if OV.get('bore_deg') is not None: solve.TOLC['bore_deg']=OV['bore_deg']
if OV.get('fore_from_C'):   # the controller grip's forearm, seen from the gun as round 5 placed it (mode C move)
    xc=np.array(R4['x_gun']); Rgc,tgc=solve.gun_T(ctx,xc); fr=ctx.ref[ctx.L['palm']]-ctx.cuff_ref.mean(0)
    ctx.P['fore_dir']=(Rgc.T@fr).tolist(); ctx.P['fore_tol']=OV.get('fore_tol',20.0)
    ctx.P['cuff_pt']=((ctx.cuff_ref.mean(0)-ctx.c-tgc)@Rgc+ctx.c).tolist(); ctx.P['cuff_tol']=OV.get('cuff_tol',4.0)
solve.TOL['pen']=OV.get('pen',0.25); solve.TOLC['cant']=OV.get('cant',10.0); solve.TOLC['gun_rot_max']=None
solve.TOLC['roll_free']=OV.get('roll_free',False); solve.TOLC['wrist_deg']=OV.get('wrist_deg',6.0); solve.TOLC['wrist_cm']=OV.get('wrist_cm',6.0)
w=dict(solve.W); w.update(dict(fore_p=2.0,palm=2.0,pads=2.0,side=2.0,index_keep=0.8,thumb_top=0.8,g4=0.0,web=0.0,index=0.0,prior=0.3)); w.update(OV.get('w',{}))
x_,y_,n_=ctx.H.axes()
def seed(lat,fwd,pf,flex):
    a=np.asarray(ctx.P['bar_axis']); dn=np.array([0,0,-1.]); dn-=(dn@a)*a; dn/=np.linalg.norm(dn)
    xt=np.array([fwd,lat,0.]); xt-=(xt@dn)*dn; xt/=np.linalg.norm(xt); yt=np.cross(dn,xt)
    R=np.stack([xt,yt,dn],1)@np.stack([x_,y_,n_],1).T
    q=np.clip(0.8*ctx.q_prior,handmodel.QLO,handmodel.QHI); q[16]=flex
    x=np.r_[Rot.from_matrix(R).as_rotvec(),np.zeros(3),q,np.zeros(6)]
    X,_=solve.hand_X(ctx,x); x[3:6]+=np.array([pf,0,np.interp(pf,Fs,top)+0.3])-X[ctx.L['palm']]
    if OV.get('mode')=='S': return np.r_[x[:24],np.zeros(6)]
    if OV.get('roll_free'):
        X0,_=solve.hand_X(ctx,x); fa=X0[ctx.L['palm']]-X0[ctx.cuff].mean(0); fr=ctx.ref[ctx.L['palm']]-ctx.cuff_ref.mean(0)
        ax=np.cross(fa,fr); s_=np.linalg.norm(ax); ang=np.arctan2(s_,fa@fr); Rt=Rot.from_rotvec(ax/s_*ang).as_matrix() if s_>1e-9 else np.eye(3)
        cen=X0[ctx.cuff].mean(0); tt=ctx.cuff_ref.mean(0)-Rt@cen
        y=x.copy(); y[:3]=Rot.from_matrix(Rt@Rot.from_rotvec(x[:3]).as_matrix()).as_rotvec(); y[3:6]=Rt@x[3:6]+tt
        y[24:27]=Rot.from_matrix(Rt).as_rotvec(); y[27:30]=Rt@ctx.c+tt-ctx.c; return y
    # move hand + gun rigidly so the cuff sits on the controller grip
    Rt,tt=metrics.rigid(X[ctx.cuff]+(x[3:6]-x[3:6]),ctx.cuff_ref) if False else metrics.rigid(solve.hand_X(ctx,x)[0][ctx.cuff],ctx.cuff_ref)
    y=x.copy(); y[:3]=Rot.from_matrix(Rt@Rot.from_rotvec(x[:3]).as_matrix()).as_rotvec(); y[3:6]=Rt@x[3:6]+tt
    y[24:27]=Rot.from_matrix(Rt).as_rotvec(); y[27:30]=Rt@ctx.c+tt-ctx.c
    return y
starts=[seed(lat,fwd,pf,fl) for lat in OV.get('lats',(1.0,-1.0)) for fwd in OV.get('fwds',(0.0,0.6)) for pf in OV.get('pfs',(-8.0,-5.5)) for fl in OV.get('flex',(0.0,40.0))]
for e in OV.get('seeds',[]): starts.append(np.array(json.load(open(os.path.join(LANE,'results',e)))['x']))
if OV.get('pitch_seeds'):   # round 6c: constructive seeds: r5 pinned hand, gun turned so its handle bar tilts toward the fist axis
    xr=np.array(R4['x_gun']); Rg0,tg0=solve.gun_T(ctx,xr)
    Rp=json.load(open(os.path.join(LANE,'results','round4_final.json')))['BrutalPistol']; cp=solve.Ctx('BrutalPistol','R',None,'gunhand'); Rgp,tgp=solve.gun_T(cp,np.array(Rp['x_gun']))
    fist=Rgp@np.asarray(cp.G['grip_axis']); fc=solve.gmove(cp,Rgp,tgp,np.asarray(cp.G['grip_c'])[None])[0]   # fist axis + hole centre (controller frame)
    for P_ in OV['pitch_seeds']:
        for dv in OV.get('dev_seeds',(0.0,)):
            bar=Rg0@np.asarray(ctx.P['bar_axis']); ax=np.cross(bar,fist); ax/=np.linalg.norm(ax); Rq=Rot.from_rotvec(ax*np.radians(P_)).as_matrix()
            Rn=Rq@Rg0
            for dF in OV.get('bar_f',(-6.0,)):
                pc=np.array([dF,0.0,0.5*(np.interp(dF,Fs,top)+np.interp(dF,Fs,low))])      # point on the handle (gun frame) -> fist centre
                tn=fc-Rn@(pc-ctx.c)-ctx.c
                y=xr.copy(); y[24:27]=Rot.from_matrix(Rn).as_rotvec(); y[27:30]=tn; y[23]=dv; starts.append(y)
    if OV.get('only_pitch'): starts=starts[-len(OV['pitch_seeds'])*len(OV.get('dev_seeds',(0.0,)))*len(OV.get('bar_f',(-6.0,))):]
if OV.get('r5_slide'):   # round 6b seeds: the r5 hand (pinned to the controller) with the GUN slid back along the handle, i.e. the hand forward
    xr=np.array(R4['x_gun']); Rg0,tg0=solve.gun_T(ctx,xr)
    for dF in OV['r5_slide']:
        for c in (1.0,1.15):
            y=xr.copy(); y[27:30]=tg0-Rg0@np.asarray(ctx.P['bar_axis'])*dF; y[6:24]=np.clip(xr[6:24]*np.r_[[c,c,1]*4,[1]*6],handmodel.QLO,handmodel.QHI); starts.append(y)
    if OV.get('only_slide'): starts=starts[-2*len(OV['r5_slide']):]
res=solve.solve(ctx,OV.get('mode','C'),starts=starts,log=sys.stdout,max_nfev=OV.get('nfev',250),w=w)
cost,x,k=res[0]
json.dump(dict(x=x.tolist(),cost=cost,start=int(k),P={kk:(vv.tolist() if isinstance(vv,np.ndarray) else vv) for kk,vv in ctx.P.items() if kk!='lever'},w=w,pen=solve.TOL['pen'],cant=solve.TOLC['cant']),open(os.path.join(LANE,'results',f'Flamethrower2_pump_{key}.json'),'w'),indent=1,default=float)
print('== pump',key,'cost %.2f start %d'%(cost,k))
