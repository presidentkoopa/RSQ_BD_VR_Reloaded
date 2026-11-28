"""Round 6 gas-pump grip rules (Flamethrower2 gun hand). Thresholds are DEFINITIONS from the owner's description (r5 headset
note + the reference photo); G8 / bore / roll as rounds 2-5 (1.92 statistics).
 N1 no penetration, BOTH directions, exact: hand vertices inside the gun, AND gun/lever surface inside the hand
    (the round-6 lesson from the pistol trigger): green <= 0.5 cm (owner), yellow <= 1.0
 N2 palm on TOP of the handle bar: |palm gap| <= 0.5 cm, palm within 1.2 cm of the bar's top line, F on the bar
    (-11..-3.5), palm facing down onto the bar within 35 deg
 N3 thumb over the top or the side of the handle: thumb pad above the handle's mid-height
 N4 index on the lever where round 5 had it: pad within 1.0 cm of that spot and within 0.5 cm of the lever
 N5 middle and ring on the lever, under it (through the guard): pads within 0.6 cm of the lever, not above its lower
    edge + 0.4 cm; little finger reported (green if middle+ring do it; the owner: 'at least middle and ring')
 G8 displayed wrist vs the controller grip (1.92 median 7.5 deg / 7.3 cm); bore within 4 deg of the controller aim"""
import numpy as np, json, os
import solve, scene, exactpen, evaluate, rules, metrics
from scipy.spatial.transform import Rotation as Rot
def light(v,g,y): return 'G' if v<=g else ('Y' if v<=y else 'R')
def measure(ctx,x,Xg=None):
    P=ctx.P; L=ctx.L; Rg,tg=solve.gun_T(ctx,x); X,J=solve.hand_X(ctx,x)
    if Xg is None: Xg=(X-ctx.c-tg)@Rg+ctx.c
    v=lambda k:Xg[evaluate.reg(L,k)].mean(0); m={}
    F,V=scene.merged(scene.GUNS['Flamethrower2']); exg=exactpen.Exact(V,F); m['pen_hand_in_gun']=float(exg.depth(Xg).max())
    S=scene.item_verts(scene.GUNS['Flamethrower2']); exh=exactpen.Exact(Xg,ctx.H.F)
    import gunfield
    near=np.concatenate([gunfield.sample_surface(v_,t_,0.08)[0] for t_,v_ in S]); lo_,hi_=Xg.min(0)-1,Xg.max(0)+1
    near=near[np.all((near>lo_)&(near<hi_),1)]; m['pen_gun_in_hand']=float(exh.depth(near).max()) if len(near) else 0.0
    d=ctx.sdf(Xg) if False else solve.gun_sdf(ctx,np.eye(3),np.zeros(3),Xg)
    m['palm_gap']=float(evaluate.rmin_d(d,L,'palm')); pp=v('palm'); m['palm_F']=float(pp[0])
    m['palm_below_top']=float(np.interp(pp[0],P['F'],P['top'])-pp[2])
    n=Rg.T@(Rot.from_rotvec(x[:3]).as_matrix()@ctx.H.axes()[2]); a=np.asarray(P['bar_axis']); dn=np.array([0,0,-1.]); dn-=(dn@a)*a; dn/=np.linalg.norm(dn)
    m['palm_normal_deg']=float(np.degrees(np.arccos(np.clip(n@dn,-1,1))))
    c0=np.array([pp[0],0.0,0.5*(np.interp(pp[0],P['F'],P['top'])+np.interp(pp[0],P['F'],P['low']))]); ds=c0-pp; ds-=(ds@a)*a; ds/=np.linalg.norm(ds)+1e-9
    m['palm_side_deg']=float(np.degrees(np.arccos(np.clip(n@ds,-1,1)))); m['palm_normal_up']=float(n[2]); m['palm_U_rel']=float(pp[2]-c0[2]); m['palm_side_L']=float(pp[1])
    th=v('pad_T'); m['thumb_above_mid_cm']=float(th[2]-0.5*(np.interp(th[0],P['F'],P['top'])+np.interp(th[0],P['F'],P['low'])))
    m['index_from_r5_cm']=float(np.linalg.norm(v('pad_I')-np.asarray(P['index_target'])))
    m['pads']={}
    for f in 'IMRP':
        q=v('pad_'+f); dl=float(np.min(np.abs(P['lever'](Xg[evaluate.reg(L,'pad_'+f)]))))
        lo=np.interp(q[0],P['F'],np.nan_to_num(np.asarray(P['lever_lo'],float),nan=99))
        on=(-4.0<=q[0]<=3.0)
        m['pads'][f]=dict(lever_cm=dl,above_lower_edge_cm=float(q[2]-lo) if on else None,F=float(q[0]))
    m['wrist_deg'],m['wrist_cm']=metrics.wrist_dev(X[ctx.cuff],ctx.cuff_ref)
    fa=X[ctx.L['palm']]-X[ctx.cuff].mean(0); fr=ctx.ref[ctx.L['palm']]-ctx.cuff_ref.mean(0)
    m['forearm_dir_deg']=float(np.degrees(np.arccos(np.clip(fa@fr/np.linalg.norm(fa)/np.linalg.norm(fr),-1,1))))
    # roll of the drawn forearm about its own axis vs the controller grip (after aligning direction)
    ax=np.cross(fa,fr); s_=np.linalg.norm(ax); Ra=Rot.from_rotvec(ax/s_*np.arctan2(s_,fa@fr)).as_matrix() if s_>1e-9 else np.eye(3)
    Rr,_=metrics.rigid((X[ctx.cuff]-X[ctx.cuff].mean(0))@Ra.T,ctx.cuff_ref-ctx.cuff_ref.mean(0)); m['forearm_roll_deg']=float(np.degrees(Rot.from_matrix(Rr).magnitude()))
    m['bore_off_deg']=float(np.degrees(np.arccos(np.clip(Rg@np.asarray(ctx.G['bore_axis'])@np.array([1.,0,0]),-1,1))))
    import run_wrist; m['roll_deg']=run_wrist.cant_of(ctx.G,Rg); m['gun_move']=(float(np.degrees(np.linalg.norm(x[24:27]))),float(np.linalg.norm(x[27:30])))
    return m
def rules_of(m):
    out=[]; pen=max(m['pen_hand_in_gun'],m['pen_gun_in_hand'])
    out.append(('N1','no penetration both ways (exact): hand into gun %.2f cm, gun/lever into hand %.2f cm'%(m['pen_hand_in_gun'],m['pen_gun_in_hand']),light(pen,0.5,1.0),'owner: <= 0.5 cm'))
    l2=max(light(abs(m['palm_gap']),0.5,1.0),light(m['palm_side_deg'],35,50),light(abs(m['palm_normal_up']),0.5,0.7),'G' if -10<=m['palm_F']<=0.5 else 'Y',key='GYR'.index)
    out.append(('N2','handle in the palm, palm sideways (handshake): gap %.2f cm, palm %.0f deg off the direction to the handle centreline, normal up-component %.2f, palm %.1f cm %s the handle centre, F %.1f'%(m['palm_gap'],m['palm_side_deg'],m['palm_normal_up'],abs(m['palm_U_rel']),'above' if m['palm_U_rel']>0 else 'below',m['palm_F']),l2,'definition (owner correction): palm sideways onto the handle, |gap| <= 0.5 cm, <= 35 deg off the centreline direction, |normal up| <= 0.5'))
    out.append(('N3','thumb over the top/side: %.1f cm above the handle mid-height'%m['thumb_above_mid_cm'],'G' if m['thumb_above_mid_cm']>=0 else ('Y' if m['thumb_above_mid_cm']>=-1 else 'R'),'definition'))
    pi=m['pads']['I']; out.append(('N4','index on the lever where r5 had it: %.2f cm from that spot, %.2f cm from the lever'%(m['index_from_r5_cm'],pi['lever_cm']),max(light(m['index_from_r5_cm'],1.0,2.0),light(pi['lever_cm'],0.5,1.0),key='GYR'.index),'definition'))
    def onl(f):
        p=m['pads'][f]; ok=p['above_lower_edge_cm'] is not None and p['above_lower_edge_cm']<=0.4
        return p['lever_cm']<=0.6 and ok
    mr=onl('M') and onl('R'); lt=onl('P')
    s=' '.join('%s %.2f cm @F %.1f, %s cm above the lower edge%s'%(f,m['pads'][f]['lever_cm'],m['pads'][f]['F'],('%.1f'%m['pads'][f]['above_lower_edge_cm']) if m['pads'][f]['above_lower_edge_cm'] is not None else 'n/a',' ok' if onl(f) else ' OFF') for f in 'MRP')
    out.append(('N5','middle/ring (little) on the lever, under it: %s'%s,'G' if mr else ('Y' if (onl('M') or onl('R')) else 'R'),'owner: at least middle and ring'))
    g8='G' if m['wrist_deg']<=7.53 and m['wrist_cm']<=7.26 else ('Y' if m['wrist_deg']<=24.8 and m['wrist_cm']<=8.19 else 'R')
    out.append(('G8','wrist vs the controller grip %.1f deg (forearm direction %.0f deg, forearm roll %.0f deg), %.1f cm; bore %.1f deg off the aim; gun roll %.1f deg'%(m['wrist_deg'],m['forearm_dir_deg'],m['forearm_roll_deg'],m['wrist_cm'],m['bore_off_deg'],m['roll_deg']),max(g8,'G' if m['bore_off_deg']<=5.0 else 'Y',key='GYR'.index),'1.92 median wrist 7.5 deg / 7.3 cm; bore: 1.92 80th pct 5.0 deg'))
    return out
def ctx_from(key):
    import fields,gunfield
    d=json.load(open(os.path.join(solve.LANE,'results',f'Flamethrower2_pump_{key}.json')))
    ctx=solve.Ctx('Flamethrower2@nozzle','R',fields.get('Flamethrower2','gun'),'pump'); P=dict(d['P'])
    for k in ('F','top','low','lever_lo'): P[k]=np.array(P[k],float)
    S=scene.item_verts(scene.GUNS['Flamethrower2']); P['lever']=gunfield.cached('Flamethrower2_lever',S[1][1],S[1][0],(-7,-4,-14),(8,4,-3),h=0.1,band=1.0)
    ctx.P=P; return ctx,np.array(d['x'])
if __name__=='__main__':
    import sys
    for k in sys.argv[1:]:
        c,x=ctx_from(k); m=measure(c,x); r=rules_of(m); print('==',k,' '.join(a[0]+a[2] for a in r))
        for a in r: print('  ',a[2],a[0],a[1])
