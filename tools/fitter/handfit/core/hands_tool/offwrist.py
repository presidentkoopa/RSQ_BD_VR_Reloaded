"""S6, the support wrist vs the OFF controller (round 3). The engine draws the support hand on the MAIN controller
(RSQ_GunSide layer; off-hand-weapon layers are skipped while stabilised: hw_weapon.cpp 832/917), so the drawn support
hand and the player's real off hand only agree if the real off controller is where the drawn hand implies.
  P_off  = the off controller pose implied by the drawn support hand: the rigid that takes the support hand's
           controller-grip cuff (calib '1', mirrored: the hand as it sits on its own controller) to the drawn cuff.
  Stabilised holds (grip pressed, distance < 0.5 m: VrInputDefault.cpp 123-175): the engine re-aims the gun frame at the
  off controller's POSITION (pitch/yaw from the main->off line, roll kept). With the player's real off controller at
  P_off, the frame turns by a = angle(F, P_off.origin), about the main controller origin. After the turn:
     support: drawn cuff (turned) vs real off-controller cuff  -> rot a, move 2|o| sin(a/2)  (o = P_off origin)
     gun hand: drawn wrist turned by a vs the real main controller -> G8 seen while stabilised
  Cup holds (pistol: shown by closeness < 13 cm, no grip press, hands.zs 222-230): no re-aim; S6 = P_off origin
  distance to the main controller (must be < 13 cm or the cup never shows) and P_off's rotation vs the main controller.
Thresholds: the 1.92 medians of the same metrics over its 22 support rows (this file, main), like G8."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import numpy as np, json, os, sys
from scipy.spatial.transform import Rotation as Rot
import metrics
def p_off(cuff_ref_L,cuff_drawn):
    R,t=metrics.rigid(cuff_ref_L,cuff_drawn); return R,t       # point p on the off controller -> R p + t (main frame)
def s6(cuff_ref_L,cuff_drawn,hold):
    R,t=p_off(cuff_ref_L,cuff_drawn); o=t                        # controller origin maps to t
    rot_vs_main=float(np.degrees(Rot.from_matrix(R).magnitude()))
    if hold=='cup':
        return dict(kind='cup',off_origin_cm=np.round(o,2).tolist(),dist_main_cm=float(np.linalg.norm(o)),off_rot_vs_main_deg=rot_vs_main,
                    reaim_deg=0.0,support_mismatch_deg=0.0,support_mismatch_cm=0.0)
    a=float(np.degrees(np.arccos(np.clip(o[0]/np.linalg.norm(o),-1,1))))
    return dict(kind='stabilised',off_origin_cm=np.round(o,2).tolist(),dist_main_cm=float(np.linalg.norm(o)),off_rot_vs_main_deg=rot_vs_main,
                reaim_deg=a,support_mismatch_deg=a,support_mismatch_cm=float(2*np.linalg.norm(o)*np.sin(np.radians(a)/2)))
if __name__=='__main__':
    # 1.92: every support row, Ermac hand2 drawn with its hook; reference = Ermac's free hand fist (hand.md3 frame 1) as
    # the off controller draws it (1.92 RSQ_Hands: same Scale -1 1 1 / Offset 0 -24 -10 on the off controller; the off
    # controller mirrors the model, so in the off controller's own frame it is the same mesh mirrored in L)
    import scene, handmodel, ermaclm
    rows=json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'rows192.json')))
    _,E1=scene.merged(dict(path=handmodel.ERMAC,frame=1,**scene.ERMAC_PL)); L=ermaclm.get(); cuff=L['cuff']
    refL=E1[cuff]*np.array([1,-1,1.])
    sp=open((_DP.GUNPACK192 + '/zscript/rsq/handtable.zs')).read()
    import re
    sup=re.search(r'String Support\(int i\)\s*\{\s*static const String v\[\] = \{([^}]*)\}',sp).group(1).replace('"','').split(',')
    idx=dict(zip(['AssaultShotgun','BFG10k','BIG_FUCKING_GUN','BrutalPistol','BrutalSMG','Devastator','Flamethrower2','GrenadeLauncher','HellishMissileLauncher','IncendiaryLauncher','MG42','MP40','Minigun','NukeLauncher','Plasma_Gun','RailGun','Revolver','Rifle','Rocket_Launcher','SSG','Shot_Gun','Sniper','Unmaker'],range(1,24)))
    out={}
    for g,r in rows.items():
        if r.get('sframe') is None: continue
        _,S=scene.merged(dict(path=scene.HAND2_192,frame=r['sframe'],hook=r['shook'],rot=r['srot'],**scene.ERMAC_PL))
        hold='cup' if sup[idx[g]].strip()=='A' else 'stab'
        m=s6(refL,S[cuff],hold); out[g]=m
        print('%-22s %-5s origin %s dist %.1f rot %.1f reaim %.1f mismatch %.1f cm'%(g,hold,m['off_origin_cm'],m['dist_main_cm'],m['off_rot_vs_main_deg'],m['reaim_deg'],m['support_mismatch_cm']))
    st=[m for m in out.values() if m['kind']=='stabilised']; cu=[m for m in out.values() if m['kind']=='cup']
    q=lambda a,k:(float(np.median([m[k] for m in a])),float(np.percentile([m[k] for m in a],80)))
    th=dict(stab_reaim_deg=q(st,'reaim_deg'),stab_mismatch_cm=q(st,'support_mismatch_cm'),stab_rot_deg=q(st,'off_rot_vs_main_deg'),
            cup_dist_cm=q(cu,'dist_main_cm'),cup_rot_deg=q(cu,'off_rot_vs_main_deg'),n_stab=len(st),n_cup=len(cu))
    print(json.dumps(th)); json.dump(dict(rows=out,thresholds=th),open((_DP.CORE + '/offwrist192.json'),'w'),indent=1)
