"""Turn a solved hand (vertices in the controller frame, cm F/L/U) into what QZD draws without engine changes:
an MD3 vertex frame + a hand-table row (hook translation, hook rotation yaw/pitch/roll), for a MODELDEF block with
1.92's hand placement (Scale -1 1 1, Offset 0 -24 -10: RSQ_GunSide in MODELDEF.rsq).
Chain = hudrender.to_local (rsq_weapondepot/tools/kit; = models.cpp RenderHUDModel, hook rotation about pivot 0,
the assumption every 1.92 rotated hook (minigun, chainsaw) was fitted with):
   FLU = P( S R (J v + h) + off' ),  P: local(x right,y up,z back)->FLU, S=diag(-1,1,1), J = jDoom turn * vr_weaponScale
We bake the frame in the CONTROLLER GRIP pose (the solved fingers, wrist where the real hand is), and put the wrist's
remaining rigid offset into the hook, so GunRot/GunHook read directly as "how far the drawn wrist is from the real hand"."""
import numpy as np
from scipy.spatial.transform import Rotation as Rot
import hudrender
PL=dict(scale=[-1.0,1.0,1.0],off=[0.0,-24.0,-10.0])
WS=1.02
P=np.array([[0,0,-1],[-1,0,0],[0,1,0.]])     # local -> FLU (gunview.to_fl, without the x100)
S=np.diag([-1.,1,1])                          # scale (x, z, y) = (-1, 1, 1)
OFF=np.array([0.0,-10.0,-24.0])+np.array([0,5,30])   # (xo, zo, yo) + (0,5,30)
def J(v): r=np.stack([v[:,0],v[:,2],v[:,1]],1)*WS; return np.stack([r[:,2],r[:,1],-r[:,0]],1)
def Jinv(p):
    r=np.stack([-p[:,2],p[:,1],p[:,0]],1)/WS; return np.stack([r[:,0],r[:,2],r[:,1]],1)
def flu_to_md3(X):
    """inverse placement with hook 0, rot 0: controller-frame cm -> md3 vertex units"""
    loc=(np.asarray(X)/100.0)@P            # to_fl: FLU = 100 * P loc  ->  loc = P^T FLU / 100 ; row form: loc = FLU @ P /100
    p=loc*100.0-OFF                         # undo 0.01*(p + (0,5,30)) and offsets
    p=p@S.T                                 # undo scale (its own inverse)
    return Jinv(p)
def hook_from_rigid(Rw,tw):
    """controller-frame rigid motion (Rw, tw cm) of the baked frame -> (hook xyz, (yaw, pitch, roll) deg)"""
    R=S@P.T@Rw@P@S
    h=R.T@S@(P.T@Rw@P@OFF+P.T@tw-OFF)
    yaw,pitch,roll=Rot.from_matrix(R).as_euler('YXZ',degrees=True)
    return h,np.array([yaw,pitch,roll])
def check(md3_xyz,hook,rot,X):
    it=dict(hook=list(hook),rot=list(rot),**PL)
    Y=100*(hudrender.to_local(md3_xyz,it)@P.T)
    return float(np.abs(Y-X).max())
