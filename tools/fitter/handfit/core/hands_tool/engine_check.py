"""TEST ONLY: load the test pack in QuestZDoom 17.3 (the depot's rig, read-only use) on the owner's load order
doom2 -> brutal22test6 -> BD_VoxelPack -> pack, hold BrutalPistol two-handed (off hand on the 1.92 support point),
dump frames, and grep the log for script errors. One engine at a time under $RSQ_RIGLOCK (shared, -o).
usage: engine_check.py <pk3> <tag>"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, glob, subprocess, shutil
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIGDIR=_DP.RIG
os.environ.update(B22_BUILD=os.path.join(LANE,'rigout'),B22_RIG=RIGDIR+'/build/rig',
                  B22_IWAD=(_DP.GAMEDATA + '/doom2.wad'),B22_BD22=(_DP.GAMEDATA + '/brutal22test6.pk3'),B22_VOX=(_DP.GAMEDATA + '/BD_VoxelPack.pk3'))
sys.path.insert(0,RIGDIR)
import rig, importlib
from PIL import Image
def run(pk3,tag,pose='0.0 1.68 -0.40 20 -70 0'):
    d=os.path.join(LANE,'rigout','shots',tag); shutil.rmtree(d,ignore_errors=True); os.makedirs(d)
    os.environ.update(QZ_RES='480',QZ_DUMP_EVERY='30',QZ_DUMP_DIR=d,B22_PK3=pk3,B22_NOPROBE='1')
    lp=rig.lpose(-4.7,2.7,-12.7)       # 1.92 handtable SupportPoint row 4 (m, gun-hand frame) -> cm
    body=('wait 100; god; notarget; screenblocks 12; crosshair 0; qz_rhand "%s"; rsq_extra_weapons 1; give ammo; give BrutalPistol; wait 2; use BrutalPistol; wait 150; qz_lhand "%s"; wait 120; quit'%(pose,lp))
    importlib.reload(rig)          # rig reads B22_PK3 at import time
    rc,text=rig.run('lanec_'+tag,body,400)
    frames=sorted(glob.glob(d+'/*.ppm'))
    errs=[l for l in text.splitlines() if ('Script error' in l or 'script error' in l.lower() or 'error' in l.lower() and 'voxeldef' not in l.lower()) and 'GL_' not in l]
    return rc,frames,errs,text
if __name__=='__main__':
    rc,frames,errs,text=run(sys.argv[1],sys.argv[2],*(sys.argv[3:4]))
    print('rc',rc,'frames',len(frames)); print('error-ish lines (%d):'%len(errs)); print('\n'.join(errs[:40]))
    print('engine line:',[l for l in text.splitlines() if 'engine OK' in l or 'WRONG ENGINE' in l][:1])
    if frames: Image.open(frames[-1]).save(os.path.join(LANE,'rigout',f'{sys.argv[2]}_last.png'))
