"""Round 7 quick look at a wrap7 solve in the gun frame: side (right), back-down (owner-ish), front cross-section; + rules.
usage: view7.py <key>  -> ../r7/view_<key>.png"""
import numpy as np, json, os, sys
from PIL import Image
import solve, scene, render, wrap7, rules7
def gun_level(ctx):
    b=np.asarray(ctx.G['bore_axis'],float); b/=np.linalg.norm(b); ax=np.cross(b,[1.,0,0]); s=np.linalg.norm(ax)
    return Rot.from_rotvec(ax/s*np.arcsin(s)).as_matrix() if s>1e-12 else np.eye(3)
from scipy.spatial.transform import Rotation as Rot
def main(key):
    ctx=wrap7.make_ctx(); x=np.array(json.load(open(os.path.join(solve.LANE,'results',f'Flamethrower2_wrap7_{key}.json')))['x'])
    X,J=solve.hand_X(ctx,x); m=rules7.measure(ctx,x)
    F,V=scene.merged(scene.GUNS['Flamethrower2']); k=np.all((V>[-30,-12,-25])&(V<[15,12,8]),1); FF=F[k[F].all(1)]
    ms=[dict(V=V,F=FF,col=(150,155,170)),dict(V=X,F=ctx.H.F,col=(214,168,140))]
    ims=[render.render(ms,'side',rng=(-30,12,-22,8),px=10),render.render(ms,'left',rng=(-12,30,-22,8),px=10),
         render.render(ms,eye=(-40,-25,25),look=(-4,0,-4),W=420,H=300,fov=35),render.render(ms,eye=(25,-30,5),look=(-4,0,-4),W=420,H=300,fov=35)]
    ims=[i if isinstance(i,Image.Image) else Image.fromarray(i) for i in ims]
    W=sum(i.width for i in ims[:2]); H=max(i.height for i in ims[:2])+300; S=Image.new('RGB',(max(W,840),H))
    S.paste(ims[0],(0,0)); S.paste(ims[1],(ims[0].width,0)); S.paste(ims[2],(0,H-300)); S.paste(ims[3],(420,H-300))
    S.save(os.path.join(solve.LANE,'r7',f'view_{key}.png'))
    print(json.dumps({k:v for k,v in m.items()},default=float))
if __name__=='__main__': main(sys.argv[1])
