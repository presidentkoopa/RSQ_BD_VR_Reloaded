"""Landmark REGIONS (vertex sets) instead of single vertices, so a metric is the closest point of a patch of skin
(robust to a 1-2 cm landmark transfer error between hand meshes).
FBX: defined on the FBX mesh at its authored open pose (frame 56) around landmarks.py's points, limited to the
right bones. Ermac: the same regions transferred by nearest vertex at the controller calibration fits
(calib.json '0' open and '1' fist on hand.md3 frames 0/1; a vertex is in a region if it is in it in both fits,
or in either for the small pad regions); one topology, so one index set for hand.md3 and hand2.md3."""
import numpy as np, json, os, sys
from scipy.spatial import cKDTree
import handmodel, calib, scene
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R_WEB=1.4; R_PALM=2.2; R_PAD=1.2   # cm on the hand at the calibrated scale
BONES={'web':('HANDPALM_joint','INDEX_BASE_joint','THUMB_BASE_joint','THUMB_MID_joint'),'palm':('HANDPALM_joint','Root_joint')}
for f,t in (('INDEX','I'),('MIDDLE_F','M'),('RING','R'),('PINK','P'),('THUMB','T')): BONES['pad_'+t]=(f+'_TOP_joint',f+'_UP_TOP_joint')
RAD={'web':R_WEB,'palm':R_PALM}
def fbx_regions():
    L=json.load(open(os.path.join(LANE,'landmarks_fbx.json')))['R']; s=json.load(open(os.path.join(LANE,'calib.json')))['scale']
    H=handmodel.FbxHand('R'); V,_=H.pose(handmodel.q_open()); V=V*s
    out={}
    for k,b in BONES.items():
        r=RAD.get(k,R_PAD); m=(np.linalg.norm(V-V[L[k]],axis=1)<r)&np.isin(H.dom,b)
        out[k]=np.where(m)[0].tolist()
    return out
def ermac_regions(Rf):
    """Ermac vertex in region k if it is within TRANSFER_CM of region k's FBX vertices in the calibrated fit,
    summed over the open and fist fits (kept if close in at least one; web/palm: in both)."""
    H=handmodel.FbxHand('R'); cal=json.load(open(os.path.join(LANE,'calib.json')))
    TRANSFER_CM=1.0
    hits={k:[] for k in Rf}
    for fr in ('0','1'):
        X=calib.place(H,np.array(cal[fr]['p']))
        _,E=scene.merged(dict(path=handmodel.ERMAC,frame=int(fr),**scene.ERMAC_PL))
        for k,idx in Rf.items():
            d,_=cKDTree(X[idx]).query(E); hits[k].append(d<TRANSFER_CM)
    out={}
    for k,h in hits.items():
        m=(h[0]&h[1]) if k in ('web','palm') else (h[0]|h[1])
        if m.sum()<3: m=(h[0]|h[1])
        out[k]=np.where(m)[0].tolist()
    return out
if __name__=='__main__':
    Rf=fbx_regions(); Re=ermac_regions(Rf)
    json.dump(dict(fbx=Rf,ermac=Re),open(os.path.join(LANE,'regions.json'),'w'))
    print({k:(len(Rf[k]),len(Re[k])) for k in Rf})
