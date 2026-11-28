"""Ermac hand landmarks. hand.md3 and hand2.md3 share ONE 1021-vertex topology, so a vertex is the same spot of skin
in every frame: each Ermac vertex is labelled once with an FBX bone (the dominant skin bone of its nearest FBX vertex)
using the controller calibration fits (calib.json: hand.md3 frame 0 open, rms 1.43 cm; frame 1 fist, rms 1.00 cm);
where the two fits disagree the open fit wins (fingers apart there). Regions:
  pad_X = vertices labelled X_TOP / X_UP_TOP (the whole distal segment), prox_X = X_BASE
  web, palm = Ermac vertices within 1.0 cm of the FBX web / palm regions in the open fit
  cuff = the 20% least-moving vertices frame 0 -> 1 (the forearm stub)
Single landmark vertices (for directions) = the region's vertex nearest the FBX landmark in the open fit."""
import json, numpy as np, os
from scipy.spatial import cKDTree
import calib, handmodel, scene
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FN={'I':'INDEX','M':'MIDDLE_F','R':'RING','P':'PINK','T':'THUMB'}
def build():
    cal=json.load(open(os.path.join(LANE,'calib.json'))); Rf=json.load(open(os.path.join(LANE,'regions.json')))['fbx']
    Lf=json.load(open(os.path.join(LANE,'landmarks_fbx.json')))['R']; H=handmodel.FbxHand('R')
    lab={}; X0=None
    for fr in ('0','1'):
        X=calib.place(H,np.array(cal[fr]['p'])); _,E=scene.merged(dict(path=handmodel.ERMAC,frame=int(fr),**scene.ERMAC_PL))
        d,nn=cKDTree(X).query(E); lab[fr]=H.dom[nn]
        if fr=='0': X0,E0,d0=X,E,d
    L={'_reg':{}}
    for t,f in FN.items():
        pad=np.where(np.isin(lab['0'],[f+'_TOP_joint',f+'_UP_TOP_joint']) if t!='T' else (lab['0']=='THUMB_UP_TOP_joint')|((lab['0']=='THUMB_TOP_joint')&(d0<1.0)))[0]
        if t=='T':   # the thumb tip only: the distal 40% of the labelled thumb along its own axis
            th=np.where(np.isin(lab['0'],['THUMB_MID_joint','THUMB_TOP_joint','THUMB_UP_TOP_joint']))[0]
            tip=X0[Lf['pad_T']]; base=E0[th][np.argmax(np.linalg.norm(E0[th]-tip,axis=1))]
            s_=(E0[th]-base)@(tip-base)/np.linalg.norm(tip-base)**2; pad=th[s_>0.75]
        prox=np.where(lab['0']==f+'_BASE_joint')[0]
        L['_reg']['pad_'+t]=pad.tolist(); L['_reg']['prox_'+t]=prox.tolist()
        L['pad_'+t]=int(pad[np.argmin(np.linalg.norm(E0[pad]-X0[Lf['pad_'+t]],axis=1))])
        L['prox_'+t]=int(prox[np.argmin(np.linalg.norm(E0[prox]-X0[Lf['prox_'+t]],axis=1))]) if len(prox) else L['pad_'+t]
    for k in ('web','palm'):
        dk,_=cKDTree(X0[Rf[k]]).query(E0); m=np.where(dk<1.0)[0]
        if len(m)<3: m=np.argsort(dk)[:6]
        L['_reg'][k]=m.tolist(); L[k]=int(m[np.argmin(np.linalg.norm(E0[m]-X0[Lf[k]],axis=1))])
    L['cuff']=np.where(calib.ermac_axes()[4])[0].tolist()
    L['agree_open_fist']=float((lab['0']==lab['1']).mean())
    L['label_counts']={t:len(L['_reg']['pad_'+t]) for t in FN}
    json.dump(L,open(os.path.join(LANE,'landmarks_ermac.json'),'w'))
    return L
_L=None
def get(mesh=None,frame=None):
    global _L
    if _L is None: _L=json.load(open(os.path.join(LANE,'landmarks_ermac.json')))
    return _L
if __name__=='__main__':
    L=build(); print('labels agree between open and fist fits on %.0f%% of vertices'%(100*L['agree_open_fist']),L['label_counts'],{k:len(L['_reg'][k]) for k in ('web','palm')})
