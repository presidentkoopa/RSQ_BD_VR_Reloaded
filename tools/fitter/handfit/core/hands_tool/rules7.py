"""Round 7 wrap rules (Flamethrower2 gun hand), thresholds from the owner's round-7 brief:
 W1 palm centre within 1 cm of the handle surface (palm landmark region, signed distance to the gun)
 W2 thumb and the fingers' proximal pads on OPPOSITE sides of the handle: angle about the handle centreline between the
    thumb pad and each proximal pad (I, M, R) >= 120 deg (green), >= 90 (yellow)
 W3 the handle centreline INSIDE the closed hand loop: winding number of thumb tip -> thumb joints -> palm -> finger joints
    -> finger tip -> (closing segment) about the centreline, |w| >= 0.5 for I, M and R (green; any two yellow)
 W4 penetration <= 0.5 cm both ways (exact: hand vertices in the gun; gun/lever surface samples in the hand)
 W5 index pad on the lever (<= 0.5 cm)
 W6 thumb along the top of the handle: thumb pad above the centreline, thumb distal direction within 40 deg of the handle
 G7 nozzle level: pitch 0, bore on the aim (exact by construction); drawn wrist position on the controller (cuff centre)
 H  the drawn hand's turn off the controller (reported, released by the owner)"""
import numpy as np
import solve, scene, exactpen, gunfield, evaluate, metrics, wrap7
def light(v,g,y): return 'G' if v<=g else ('Y' if v<=y else 'R')
def measure(ctx,x,Xg=None):
    X,J=solve.hand_X(ctx,x); Xg=X if Xg is None else Xg; m={}
    F,V=scene.merged(scene.GUNS['Flamethrower2']); m['pen_hand_in_gun']=float(exactpen.Exact(V,F).depth(Xg).max())
    S=scene.item_verts(scene.GUNS['Flamethrower2']); exh=exactpen.Exact(Xg,ctx.H.F)
    near=np.concatenate([gunfield.sample_surface(v_,t_,0.08)[0] for t_,v_ in S]); lo_,hi_=Xg.min(0)-1,Xg.max(0)+1
    near=near[np.all((near>lo_)&(near<hi_),1)]; near=near[__import__('scipy.spatial',fromlist=['cKDTree']).cKDTree(Xg).query(near)[0]<2.0]; m['pen_gun_in_hand']=float(exh.depth(near).max()) if len(near) else 0.0
    d=ctx.sdf(Xg); v=lambda k:Xg[evaluate.reg(ctx.L,k)].mean(0)
    m['palm_gap']=float(evaluate.rmin_d(d,ctx.L,'palm')); m['palm_centre_gap']=float(d[ctx.L['palm']]); m['palm_F']=float(Xg[ctx.L['palm']][0])
    th=v('pad_T'); aT=wrap7.ang(ctx,th[None])[0]; m['thumb_ang']=float(np.degrees(aT))
    m['opp']={f:float(abs(np.degrees(np.angle(np.exp(1j*(wrap7.ang(ctx,v('prox_'+f)[None])[0]-aT)))))) for f in 'IMR'}
    m['winding']={f:wrap7.winding(ctx,wrap7.chain(ctx,Xg,J,f)) for f in 'IMRP'}
    m['sweep']={f:wrap7.sweep(ctx,wrap7.chain(ctx,Xg,J,f)) for f in 'IMRP'}
    m['lever']={f:float(np.min(np.abs(ctx.lever(Xg[evaluate.reg(ctx.L,'pad_'+f)])))) for f in 'IMRP'}
    m['index_from_r5']=float(np.linalg.norm(v('pad_I')-ctx.idx_t))
    td=J['THUMB_UP_TOP_joint']-J['THUMB_MID_joint']; td/=np.linalg.norm(td); m['thumb_along_deg']=float(np.degrees(np.arccos(np.clip(td@ctx.a,-1,1))))
    m['thumb_above_cl']=float(wrap7.cs(ctx,th[None])[0][0])
    return m
def rules(m,g):
    out=[]; pen=max(m['pen_hand_in_gun'],m['pen_gun_in_hand'])
    out.append(('W1','palm centre on the handle: %.2f cm from its surface (palm region min %.2f)'%(m['palm_centre_gap'],m['palm_gap']),light(abs(m['palm_centre_gap']),1.0,1.5),'owner r7: within 1 cm'))
    mo=min(m['opp'].values()); out.append(('W2','thumb vs proximal pads around the handle: I %.0f M %.0f R %.0f deg apart'%tuple(m['opp'][f] for f in 'IMR'),'G' if mo>=120 else ('Y' if mo>=90 else 'R'),'owner r7: opposite sides; definition >= 120 deg'))
    ins=[f for f in 'IMR' if abs(m['winding'][f])>=0.5]
    out.append(('W3','handle centreline inside the closed loop (winding I %.2f M %.2f R %.2f P %.2f)'%tuple(m['winding'][f] for f in 'IMRP'),'G' if len(ins)==3 else ('Y' if len(ins)>=2 else 'R'),'owner r7: centreline inside the loop; |winding| >= 0.5'))
    out.append(('W4','penetration both ways (exact): hand into gun %.2f cm, gun/lever into hand %.2f cm'%(m['pen_hand_in_gun'],m['pen_gun_in_hand']),light(pen,0.5,1.0),'owner: <= 0.5 cm'))
    out.append(('W5','index on the lever: pad %.2f cm from it (middle %.2f, ring %.2f, little %.2f)'%tuple(m['lever'][f] for f in 'IMRP'),light(m['lever']['I'],0.5,1.0),'owner r7: index on the lever'))
    out.append(('W6','thumb along the top: pad %.1f cm above the centreline, distal %.0f deg off the handle'%(m['thumb_above_cl'],m['thumb_along_deg']),'G' if m['thumb_above_cl']>0 and m['thumb_along_deg']<=40 else ('Y' if m['thumb_above_cl']>-1 else 'R'),'owner r7 photo: thumb lying along the top'))
    out.append(('G7','nozzle pitch %.2f deg, yaw %.2f deg, roll %.2f deg; drawn wrist (cuff centre) %.2f cm from the controller grip'%(g['pitch'],g['yaw'],g['roll'],g['cuff_cm']),'G' if abs(g['pitch'])<0.05 and abs(g['yaw'])<0.05 and g['cuff_cm']<0.05 else 'R','owner r7: nozzle level, bore on the aim, wrist position at the controller'))
    out.append(('H','drawn hand turned %.1f deg off the controller grip (released by the owner: report only)'%g['hand_turn_deg'],'-','owner r7'))
    return out
