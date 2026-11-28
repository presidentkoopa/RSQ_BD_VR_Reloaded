"""TEST ONLY: engine_check.py for any gun: <pk3> <tag> <GunClass> <row>. The off hand goes to the 1.92 SupportPoint of that
row (handtable.zs, metres in the gun hand's frame -> cm), as engine_check.py does for the pistol. One engine, under
$RSQ_RIGLOCK (caller wraps with flock -o -s). Prints rc, frame count, error-ish lines, the engine line."""
import os, sys, re, importlib
import engine_check as E
from PIL import Image
LANE=E.LANE
def support_point(row):
    t=open(os.path.join(LANE,'bd22q_192','zscript','rsq','handtable.zs')).read()
    b=re.search(r'static Vector3 SupportPoint\(int i\)\s*\{(.*?)\n\t\}',t,re.S).group(1)
    v=[[float(a) for a in re.search(r'static const double '+k+r'\[\] = \{ ([^}]*) \};',b).group(1).split(',')][row] for k in 'xyz']
    return [100*a for a in v]
def run(pk3,tag,gun,row,pose='0.0 1.68 -0.40 20 -70 0'):
    d=os.path.join(LANE,'rigout','shots',tag); import shutil,glob; shutil.rmtree(d,ignore_errors=True); os.makedirs(d)
    os.environ.update(QZ_RES='480',QZ_DUMP_EVERY='30',QZ_DUMP_DIR=d,B22_PK3=pk3,B22_NOPROBE='1')
    importlib.reload(E.rig); sp=support_point(row); lp=E.rig.lpose(*sp)
    body=('wait 100; god; notarget; screenblocks 12; crosshair 0; qz_rhand "%s"; rsq_extra_weapons 1; give ammo; give %s; wait 2; use %s; wait 150; qz_lhand "%s"; wait 120; quit'%(pose,gun,gun,lp))
    rc,text=E.rig.run('lanec_'+tag,body,400)
    frames=sorted(glob.glob(d+'/*.ppm'))
    errs=[l for l in text.splitlines() if 'error' in l.lower() and 'GL_' not in l and 'voxeldef' not in l.lower()]
    vox=[l for l in text.splitlines() if 'Script error' in l and 'voxeldef' in l.lower()]
    if frames: Image.open(frames[-1]).save(os.path.join(LANE,'rigout',f'{tag}_last.png'))
    print('rc',rc,'frames',len(frames),'support point cm',[round(a,1) for a in sp])
    print('error lines not from BD_VoxelPack (%d):'%len(errs)); print('\n'.join(errs[:20]))
    print('BD_VoxelPack voxeldef script errors (known, not ours): %d'%len(vox))
    print('engine line:',[l for l in text.splitlines() if 'engine OK' in l or 'WRONG ENGINE' in l][:1])
if __name__=='__main__': run(*sys.argv[1:4],int(sys.argv[4]))
