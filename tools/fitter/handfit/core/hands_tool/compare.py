"""Measure an EXISTING arrangement (1.92 or ModelSwapper today) with the same rules: Ermac hands with the consensus
landmark indices (landmarks_ermac.json), the controller reference = Ermac's free fist (hand.md3 frame 1) cuff.
ModelSwapper's gun is drawn at its own MODELDEF placement: it is the same BD22 mesh (6 frames vs 5; ready frame 0
compared) shifted; we measure ITS hands against ITS gun by expressing them in the 1.92 gun's frame (rigid fit of
the two gun meshes' ready frames)."""
import numpy as np, json
import scene, evaluate, metrics, handmodel, fields, gunlm, ermaclm
def ermac_ref():
    _,E1=scene.merged(dict(path=handmodel.ERMAC,frame=1,**scene.ERMAC_PL)); return E1
def arrangement(key,cls_lm):
    """returns dict(gun=(F,V), hand=(F,V), sup=(F,V)) all expressed in the 1.92 gun frame, and the rigid used"""
    (gF,gV),(hF,hV),(sF,sV)=scene.build_meshes(key)
    _,ref=scene.merged(scene.GUNS[key[0]])
    if len(gV)==len(ref):
        R,t=metrics.rigid(gV,ref)
    else:
        R,t=np.eye(3),np.zeros(3)
    mv=lambda V:V@R.T+t
    return dict(gun=(gF,mv(gV)),hand=(hF,mv(hV)),sup=(sF,mv(sV)),rigid=(R,t),gun_shift_cm=float(np.linalg.norm(gV.mean(0)-ref.mean(0))))
def measure(key,cls_lm,hold,sup_field=None):
    A=arrangement(key,cls_lm); b=scene.BUILDS[key]
    pre='ms' if key[1]=='ModelSwapper' else ''
    L=ermaclm.get(pre+'hand',b['gframe']); Ls=ermaclm.get(pre+'hand2',b['sframe'])
    G={k:(np.array(v) if isinstance(v,list) else v) for k,v in json.load(open(scene.LANE+'/gun_landmarks.json'))[cls_lm].items()}
    fld=fields.get(key[0],'gun')
    E1=ermac_ref(); R,t=A['rigid']; cuff_ref=(E1[L['cuff']])@R.T+t   # the controller moves with the arrangement's gun placement
    gm=evaluate.evaluate_gun(G,fld,A['hand'][1],L,cuff_ref)
    hs=evaluate.HandSDF(A['hand'][1],A['hand'][0],f'{key[0]}_{key[1]}_gunhand')
    S={k:(np.array(v) if isinstance(v,list) else v) for k,v in G['support'].items()}
    sfld=fields.get(key[0],'sup') if hold=='vgrip' else fld
    sm=evaluate.evaluate_support(G,S,sfld,A['sup'][1],Ls,hold,gunhand=hs)
    return A,gm,sm,(L,Ls),G
