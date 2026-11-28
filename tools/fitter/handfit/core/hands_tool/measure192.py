"""Measure BD22Q 1.92's displayed hands (every gun row in its handtable) with the rule metrics that need no
per-gun landmarks: penetration into the gun, gap at palm / each finger pad, wrist pose vs the controller.
These distributions are the tolerances (the owner judged 1.92's hands good)."""
import numpy as np, json, sys
import scene, metrics, handmodel, ermaclm, evaluate
def run(rows_json,lm_json,out_json):
    rows=json.load(open(rows_json))
    _,ref=scene.merged(dict(path=handmodel.ERMAC,frame=1,**scene.ERMAC_PL))
    out={}
    for cls,r in rows.items():
        gF,gV=scene.merged(r['gun']); sdf=metrics.GunSDF(gV,gF,step=0.12)
        hF,hV=scene.merged(dict(path=scene.HAND192,frame=r['gframe'],hook=r['ghook'],rot=r['grot'],**scene.ERMAC_PL))
        L=ermaclm.get('hand',r['gframe']); d=sdf(hV); m={}
        m['pen_max']=float(max(0,-d.min())); m['pen_p95']=float(max(0,-np.percentile(d,1)))
        m['palm_gap']=evaluate.rmin_d(d,L,'palm'); m['web_gap']=evaluate.rmin_d(d,L,'web')
        for f in 'IMRPT': m['pad_'+f]=evaluate.rmin_d(d,L,'pad_'+f)
        m['wrist_rot'],m['wrist_move']=metrics.wrist_dev(hV[L['cuff']],ref[L['cuff']])
        m['fore_yaw']=evaluate.forearm_yaw(hV,L,np.array([1.,0,0]))
        if r['sframe'] is not None:
            sF,sV=scene.merged(dict(path=scene.HAND2_192,frame=r['sframe'],hook=r['shook'],rot=r['srot'],**scene.ERMAC_PL))
            L=ermaclm.get('hand2',r['sframe']); ds=sdf(sV); m['s_pen_max']=float(max(0,-ds.min())); m['s_palm_gap']=evaluate.rmin_d(ds,L,'palm')
            for f in 'IMRPT': m['s_pad_'+f]=evaluate.rmin_d(ds,L,'pad_'+f)
        out[cls]=m
        print(cls.ljust(24),' '.join(f'{k}={v:.2f}' for k,v in m.items()),flush=True)
    json.dump(out,open(out_json,'w'),indent=1)
    keys=sorted({k for m in out.values() for k in m})
    print('\nacross %d guns: median / 80th pct / max'%len(out))
    for k in keys:
        a=np.array([m[k] for m in out.values() if k in m])
        print(f'  {k:12s} {np.median(a):6.2f} {np.percentile(a,80):6.2f} {a.max():6.2f}   (min {a.min():.2f})')
if __name__=='__main__': run(*sys.argv[1:4])
