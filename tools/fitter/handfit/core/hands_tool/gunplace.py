"""Mode C moves the GUN to the hand (the hand stays on the controller). Express that move as what QZD 17.3 reads
with no engine change: the gun's MODELDEF Offset (x y) / ZOffset and AngleOffset / PitchOffset / RollOffset.
Chain = models.cpp RenderHUDModel (rig build src, lines 244-277):
   scale(xs,zs,ys) . translate(xo/xs, zo/zs, yo/ys) . [pivot rot = 0 for the gun layer at rest] . translate(bob)
   . rotate(90, y) . rotate(-angle, y) . rotate(pitch, z) . rotate(-roll, x) . scale(ws)
hudrender.to_local is the same chain without the three offsets; to_local_ao adds them. The 6 numbers are FITTED
(least squares on every gun vertex) to the solved rigid move, and the residual is reported: that is the check."""
import numpy as np
from scipy.optimize import least_squares
import hudrender, gunview
def ry(a): return hudrender.rot_y(a)
def rz(a): return hudrender.rot_z(a)
def rx(a): return hudrender.rot_x(a)
def to_local_ao(v,it,ws=1.02):
    xs,ys,zs=it['scale']; xo,yo,zo=it['off']; ang,pit,rol=it.get('ao',(0,0,0))
    r=np.stack([v[:,0],v[:,2],v[:,1]],1)*ws                      # md3 (x,y,z) -> GL (x,z,y), weapon scale
    r=r@(ry(-ang)@rz(pit)@rx(-rol)).T                           # offsets rotate the model first (innermost)
    p=r@ry(90).T                                                # jDoom turn
    p=p*np.array([xs,zs,ys])+np.array([xo,zo,yo])
    return 0.01*(p+np.array([0,5,30]))
def check_chain(v,it):
    """with ao = 0 this must equal hudrender.to_local (hook 0)"""
    a=to_local_ao(v,dict(it,ao=(0,0,0))); b=hudrender.to_local(v,dict(it,hook=(0,0,0),rot=(0,0,0)))
    return float(np.abs(a-b).max())
def fit(item,target_flu):
    """item: scene.GUNS entry (path, frame, scale, off); target_flu: [n,3] cm FLU of every md3 vertex of the frame"""
    V=np.concatenate([s['xyz'][item['frame']] for s in __import__('scene').md3_full(item['path'])])
    def f(p):
        it=dict(item,off=list(p[:3]),ao=tuple(p[3:])); return (gunview.to_fl(to_local_ao(V,it))-target_flu).ravel()
    best=None
    for a0 in (-30,0,30):
        for r0 in (-30,0,30):
            s=least_squares(f,np.r_[item['off'],a0,0,r0])
            if best is None or s.cost<best.cost: best=s
    res=np.abs(f(best.x)).reshape(-1,3); p=best.x
    return dict(Offset=[round(float(p[0]),3),round(float(p[1]),3)],ZOffset=round(float(p[2]),3),note='all five are ABSOLUTE MODELDEF values (1.92: Offset 0 0, ZOffset -5, no angle offsets)',
                AngleOffset=round(float(p[3]),3),PitchOffset=round(float(p[4]),3),RollOffset=round(float(p[5]),3),
                fit_max_cm=float(np.linalg.norm(res,axis=1).max()),chain_check_cm=100*check_chain(V,item))
