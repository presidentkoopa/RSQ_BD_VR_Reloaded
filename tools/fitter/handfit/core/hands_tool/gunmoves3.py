"""Recompute RSQ_GunMoves rows for a gun whose MODELDEF placement changes (round 3).
Derivation (models.cpp RenderHUDModel chain, hands.zs RSQ_Turn.Place):
  gun inner = R_q J_g (v), hand inner = R_E (t + J u); J_g = jDoom turn . angle offsets . swizzle . ws (gunplace).
  A model frame f moves the gun rigidly in md3 space: v_f = K v_r + m (fit on all vertices).
  In the hands' inner frame: Kj = J_g K J_g^-1, and with p = Pivot = S (off_g - off_h) [world offsets (xo, zo, yo)],
  Place gives hand = Q Kj m' + p - Q p + Q Kj J u, which equals the gun's motion applied to the hand when
     m' = Kj^T (J_g m + p - Kj p).
  Turn stored as (yaw about y, pitch about x, roll about z) with R = Ry Rx Rz (RSQ_Turn.Rows/Angles).
Validation: with the 1.92 placement this must reproduce the shipped rows (printed)."""
import numpy as np, re, json, sys
from scipy.spatial.transform import Rotation as Rot
import scene, metrics, gunplace, hudrender
def J_of(ao=(0,0,0),ws=1.02):
    E=np.eye(3); it=dict(scale=[1,1,1],off=[0,0,0],ao=ao)
    cols=[(gunplace.to_local_ao(E[k][None],it,ws)*100-gunplace.to_local_ao(np.zeros((1,3)),it,ws)*100)[0] for k in range(3)]
    return np.stack(cols,1)
def euler(R):
    # R = Ry(a) Rx(b) Rz(c) -> (a,b,c) deg, matching RSQ_Turn.Angles
    a=np.degrees(np.arctan2(R[0,2],R[2,2])); b=np.degrees(np.arcsin(np.clip(-R[1,2],-1,1))); c=np.degrees(np.arctan2(R[1,0],R[1,1])); return np.array([a,b,c])
def rows_from(R): return R
def frame_motion(path,fr,f):
    V=np.concatenate([s['xyz'][fr] for s in scene.md3_full(path)]); W=np.concatenate([s['xyz'][f] for s in scene.md3_full(path)])
    K,m=metrics.rigid(V,W); res=np.abs(V@K.T+m-W).max(); return K,m,res
def row(path,ready,f,ao,pivot,ws=1.02):
    Jg=J_of(ao,ws); K,m,res=frame_motion(path,ready,f); Kj=Jg@K@np.linalg.inv(Jg)
    U,S,Vt=np.linalg.svd(Kj); Kj=U@Vt
    p=np.asarray(pivot,float); mm=Kj.T@(Jg@m+p-Kj@p)
    return euler(Kj),mm,res
def pivot_of(off_g,zoff_g,off_h=(0,-24),zoff_h=-10,sx=-1):
    w=np.array([off_g[0]-off_h[0],zoff_g-zoff_h,off_g[1]-off_h[1]]); return np.array([sx*w[0],w[1],w[2]])
if __name__=='__main__':
    P=scene.GUNS
    # 1.92 check: pistol rows 15,16,17 = model frames 4,5,6 (PIST B/C/D) vs ready 3; flamer rows 28,29 = FLMT D/H (3), E/G (4) vs 0
    for g,ready,frs in (('BrutalPistol',3,(4,5,6)),('Flamethrower2',0,(3,4))):
        for f in frs:
            t,m,res=row(P[g]['path'],ready,f,(0,0,0),pivot_of((0,0),-5)); print('1.92',g,f,'turn',t.round(2),'move',m.round(2),'(fit res %.3f)'%res)
SURF={'BrutalPistol':[4],'Flamethrower2':[0]}   # the surfaces the shipped rows were fitted on (reproduced exactly, above)
READY={'BrutalPistol':3,'Flamethrower2':0}
ROWS={'BrutalPistol':{15:4,16:5,17:6},'Flamethrower2':{28:3,29:4}}
def new_rows(g,md):
    """md: gun_modeldef dict (Offset, ZOffset, AngleOffset, PitchOffset, RollOffset) -> {row: (turn, move)}, pivot"""
    S=scene.md3_full(scene.GUNS[g]['path']); ao=(md['AngleOffset'],md['PitchOffset'],md['RollOffset'])
    piv=pivot_of(md['Offset'],md['ZOffset']); out={}
    V=np.concatenate([S[k]['xyz'][READY[g]] for k in SURF[g]])
    for r,f in ROWS[g].items():
        W=np.concatenate([S[k]['xyz'][f] for k in SURF[g]]); K,m=metrics.rigid(V,W)
        Jg=J_of(ao); Kj=Jg@K@np.linalg.inv(Jg); U,_,Vt=np.linalg.svd(Kj); Kj=U@Vt
        mm=Kj.T@(Jg@m+piv-Kj@piv); out[r]=(euler(Kj),mm)
    return out,piv
