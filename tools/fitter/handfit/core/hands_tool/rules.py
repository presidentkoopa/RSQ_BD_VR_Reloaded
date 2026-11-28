"""The grip rules as numbers + traffic lights. Thresholds: green/yellow bounds LEARNED from BD22Q 1.92
(metrics192.json: 22 guns, the owner judged 1.92's hands good) where the metric can be measured on 1.92 without
per-gun landmarks; otherwise from 1.92's BrutalPistol (the owner's reference "awesome" hold) measured with the same
landmarks, or a stated definition. Every rule carries its source string."""
import numpy as np, json, os
import metrics
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M192=json.load(open(os.path.join(LANE,'metrics192.json')))
def stat(k,q):
    a=np.array([m[k] for m in M192.values() if k in m]); return float(np.percentile(a,q))
def stat_abs(k,q):
    a=np.abs(np.array([m[k] for m in M192.values() if k in m])); return float(np.percentile(a,q))
def pad_mean(prefix):
    return np.array([np.mean([m[prefix+f] for f in 'MRP']) for m in M192.values() if prefix+'M' in m])
def light(v,g,y,higher_better=False):
    if higher_better: return 'G' if v>=g else ('Y' if v>=y else 'R')
    return 'G' if v<=g else ('Y' if v<=y else 'R')
def gun_rules(m,ref_pistol=None):
    """m: dict from evaluate_gun(); returns list of (id, label, value_str, light, source)"""
    out=[]
    g,y=stat('pen_max',50),stat('pen_max',100)
    out.append(('G1','no penetration into the gun: deepest vertex %.2f cm'%m['pen_max'],light(m['pen_max'],g,y),f'1.92 pen_max median {g:.2f} / max {y:.2f} (22 guns)'))
    g=1.5; y=3.0
    out.append(('G2','web of thumb/index on the backstrap top: %.2f cm off'%m['web_to_backstrap_cm'],light(m['web_to_backstrap_cm'],g,y),'definition: green <=1.5 cm, yellow <=3 (Ermac landmark transfer error 2.3 cm, so 1.92 cannot be measured finer)'))
    g,y=stat_abs('palm_gap',50),stat_abs('palm_gap',80)
    out.append(('G3','palm on the back of the grip: gap %.2f cm, %s the grip axis'%(m['palm_gap_cm'],'behind' if m['palm_behind_axis_cm']>0 else 'IN FRONT OF'),light(abs(m['palm_gap_cm']),g,y) if m['palm_behind_axis_cm']>0 else 'R',f'1.92 |palm gap| median {g:.2f} / 80th pct {y:.2f}'))
    a=m['grip_vs_knuckles_deg']
    ref=ref_pistol['grip_vs_knuckles_deg'] if ref_pistol else json.load(open(os.path.join(LANE,'ref192_pistol.json')))['grip_vs_knuckles_deg']
    out.append(('G4','grip axis diagonal across the palm: %.0f deg to the knuckle line (1.92 pistol %.0f)'%(a,ref),light(abs(a-ref),10,20),'1.92 BrutalPistol, same landmarks: green within 10 deg, yellow 20'))
    pm=max(m['pad_M_gap_cm'],m['pad_R_gap_cm'],m['pad_P_gap_cm']); wrap=min(m['pad_M_front_cm'],m['pad_R_front_cm'],m['pad_P_front_cm'])
    pg=pad_mean('pad_'); g,y=float(np.percentile(pg,50)),float(np.percentile(pg,80))
    out.append(('G5','middle/ring/little wrap the front strap: worst pad gap %.2f cm, %s'%(pm,'all in front of the axis' if wrap>0 else 'a pad BEHIND the axis'),light(pm,max(g,0.6),max(y,1.5)) if wrap>0 else 'R',f'1.92 mean M/R/P pad gap median {g:.2f} / 80th {y:.2f}'))
    g,y=stat_abs('pad_T',50),stat_abs('pad_T',80)
    side=m['thumb_side_cm']>0
    out.append(('G6','thumb on the far side: %.1f cm %s of the grip centre, gap %.2f cm'%(abs(m['thumb_side_cm']),'past' if side else 'SHORT of',m['pad_T_gap_cm']),light(abs(m['pad_T_gap_cm']),g,y) if side else 'R',f'1.92 |thumb pad gap| median {g:.2f} / 80th {y:.2f}'))
    out.append(('G7','index pad on the trigger face: %.2f cm off'%m['index_to_trigger_cm'],light(m['index_to_trigger_cm'],1.0,2.0),'definition: green <=1 cm, yellow <=2 (1.92 RQGT frames were fitted onto each trigger)'))
    g,y=stat('wrist_rot',50),stat('wrist_rot',80); g2,y2=stat('wrist_move',50),stat('wrist_move',80)
    l1=light(m['wrist_rot_vs_controller_deg'],g,y); l2=light(m['wrist_move_vs_controller_cm'],g2,y2)
    out.append(('G8','VR: displayed wrist vs the real hand (controller grip): %.1f deg, %.1f cm'%(m['wrist_rot_vs_controller_deg'],m['wrist_move_vs_controller_cm']),max(l1,l2,key='GYR'.index),f'1.92 median {g:.1f} deg / {g2:.1f} cm, 80th {y:.1f} / {y2:.1f}'))
    g,y=stat('fore_yaw',50),stat('fore_yaw',100)
    out.append(('G9','forearm in line behind the gun: %.0f deg yaw off the bore'%m['forearm_yaw_deg'],light(m['forearm_yaw_deg'],g,y),f'1.92 forearm yaw median {g:.0f} / max {y:.0f} deg'))
    return out
def support_rules(m,kind):
    out=[]
    g,y=stat('s_pen_max',50),stat('s_pen_max',100)
    out.append(('S1','no penetration (gun and gun hand): deepest %.2f cm'%m['pen_max_cm'],light(m['pen_max_cm'],g,y),f'1.92 support pen_max median {g:.2f} / max {y:.2f}'))
    pads=np.array([m['pads_gap'][f] for f in 'IMRP'])
    sp=np.array([np.mean([mm['s_pad_'+f] for f in 'IMRP']) for mm in M192.values() if 's_pad_I' in mm])
    g,y=float(np.percentile(sp,50)),float(np.percentile(sp,80))
    out.append(('S2','finger pads touch (no air gaps): mean gap %.2f cm, worst %.2f'%(pads.mean(),pads.max()),light(pads.mean(),g,y),f'1.92 support mean pad gap median {g:.2f} / 80th {y:.2f}'))
    g,y=stat_abs('s_palm_gap',50),stat_abs('s_palm_gap',80)
    out.append(('S3','palm touches: gap %.2f cm'%m['palm_gap'],light(abs(m['palm_gap']),max(g,0.3),y),f'1.92 |support palm gap| median {g:.2f} / 80th {y:.2f}'))
    if kind=='vgrip':
        out.append(('S4','the bar runs THROUGH the fist: %.2f (1 = palm and pads on opposite sides)'%m['axis_through_fist'],light(m['axis_through_fist'],0.5,0.0,True),'definition (handlebar rule, HAND_FITTING.md): green >=0.5, yellow >=0'))
        out.append(('S5','knuckle line along the bar: %.0f deg'%m['grip_vs_knuckles_deg'],light(min(m['grip_vs_knuckles_deg'],180-m['grip_vs_knuckles_deg']),25,40),'definition: green <=25 deg, yellow <=40'))
    if kind=='cup':
        out.append(('S4','support thumb on the gun\'s left side: %.1f cm %s'%(abs(m['thumb_side_cm']),'left of the grip centre' if m['thumb_side_cm']>0 else 'RIGHT of it'),'G' if m['thumb_side_cm']>0.5 else ('Y' if m['thumb_side_cm']>0 else 'R'),'definition (thumbs-forward cup)'))
        out.append(('S5','support fingers wrap the gun hand\'s front: %d of 4 pads right of the grip centre'%m['pads_right'],'G' if m['pads_right']>=3 else ('Y' if m['pads_right']>=2 else 'R'),'definition'))
    return out
