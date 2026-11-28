"""Landmarks on Ermac's hands (hand.md3 / hand2.md3, 1021 vertices, same topology in every frame), PER FRAME:
the posable FBX hand (scale fixed at the controller calibration) is fitted to that very frame (rigid + 18 pose
parameters, trimmed symmetric chamfer), and each landmark is the Ermac vertex nearest to the fitted FBX landmark.
The fit rms and each landmark's transfer distance are kept, so a 1.92 metric can be read with its error bar.
hand2 frames are LEFT hands in the controller frame: they are fitted with the FBX left rig."""
import numpy as np, json, sys, os
from scipy.spatial.transform import Rotation as Rot
import scene, handmodel, calib
def fit_frame(path,frame,side,scale,Lfbx,H,cal):
    """start from the calibrated controller fist (mirrored for a left hand) moved onto this frame's cuff, so the
    roll is right; then rigid + 18 pose parameters by trimmed chamfer (scale fixed)."""
    _,E=scene.merged(dict(path=path,frame=frame,**scene.ERMAC_PL))
    HR=handmodel.FbxHand('R') if side=='L' else H
    ref=calib.place(HR,np.array(cal['1']['p']))
    E0,E1,xE,nE,still=calib.ermac_axes(); st=np.where(still)[0]
    Mi=np.diag([1,-1,1.]) if side=='L' else np.eye(3)
    import metrics
    Rc,tc=metrics.rigid(E1[st]@Mi.T,E[st])          # controller fist (mirrored if left) -> this frame, by the cuff
    p1=np.array(cal['1']['p'])
    R1=Rot.from_rotvec(p1[:3]).as_matrix(); t1=p1[3:6]
    # FBX left rig = mirrored right rig: palm-frame coords mirror too, so R_left = Mi R1 Mi
    R0=Rc@(Mi@R1@Mi); t0=Rc@(Mi@t1)+tc
    p=np.r_[Rot.from_matrix(R0).as_rotvec(),t0,np.log(scale),p1[7:]]
    p,rms,med=calib.fit(H,E,p,free_q=False,iters=2,fix_scale=True)
    p,rms,med=calib.fit(H,E,p,free_q=True,iters=4,fix_scale=True)
    X=calib.place(H,p); out={'fit_rms_cm':rms,'fit_median_cm':med,'p':p.tolist()}
    for k,v in Lfbx.items():
        if isinstance(v,int):
            d=np.linalg.norm(E-X[v],axis=1); out[k]=int(np.argmin(d)); out[k+'_err']=float(d.min())
    from scipy.spatial import cKDTree
    out['cuff']=sorted(set(cKDTree(E).query(X[Lfbx['cuff']])[1].tolist()))
    return out
def run(rows_json,lm_json,calib_json,out_json):
    rows=json.load(open(rows_json)); Lf=json.load(open(lm_json)); cal=json.load(open(calib_json))
    s=cal['scale']; HR=handmodel.FbxHand('R'); HL=handmodel.FbxHand('L')
    jobs=set()
    for r in rows.values():
        jobs.add(('hand',r['gframe']))
        if r['sframe'] is not None: jobs.add(('hand2',r['sframe']))
    jobs|={('hand',0),('hand',1),('mshand',38),('mshand2',1)}   # ModelSwapper today: its own cut hand.md3 frame 38 (RQGT O), hand2.md3 frame 1 (RQSP B)
    out=json.load(open(out_json)) if os.path.exists(out_json) else {}
    for mesh,fr in sorted(jobs):
        key=f'{mesh}:{fr}'
        if key in out: continue
        path={'hand':scene.HAND192,'hand2':scene.HAND2_192,'mshand':scene.MSR+'/models/rsq/hand.md3','mshand2':scene.MSR+'/models/rsq/hand2.md3'}[mesh]
        if fr in (0,1) and mesh=='hand': path=handmodel.ERMAC
        side='L' if mesh.endswith('2') else 'R'
        out[key]=fit_frame(path,fr,side,s,Lf[side],HR if side=='R' else HL,cal)
        o=out[key]; print(key,'rms %.2f'%o['fit_rms_cm'],' '.join('%s %.1f'%(k[:-4],v) for k,v in o.items() if k.endswith('_err')),flush=True)
        json.dump(out,open(out_json,'w'))
if __name__=='__main__': run(*sys.argv[1:5])
