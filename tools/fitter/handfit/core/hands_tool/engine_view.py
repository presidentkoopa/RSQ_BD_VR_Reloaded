"""TEST ONLY: gun hand at rig.RHAND (where rig.lpose's off-hand support point is valid), off hand on the 1.92 support
point, several head (qz_hmd) poses in one run; one frame dump per pose. <pk3> <tag> <Gun> <row>"""
import os, sys, glob, shutil, importlib
import engine_check as E, engine_check2 as E2
LANE=E.LANE
HMD=[h for h in os.environ.get('LANEC_HMD','0.70 1.40 -0.45 15 80 0|0.25 1.45 0.15 25 0 0').split('|')]
def run(pk3,tag,gun,row):
    d=os.path.join(LANE,'rigout','shots',tag); shutil.rmtree(d,ignore_errors=True); os.makedirs(d)
    os.environ.update(QZ_RES='480',QZ_DUMP_EVERY='20',QZ_DUMP_DIR=d,B22_PK3=pk3,B22_NOPROBE='1')
    importlib.reload(E.rig); rh='%.4f %.4f %.4f 30 0 0'%E.rig.RHAND; lp=E.rig.lpose(*E2.support_point(row))
    body='wait 100; god; notarget; screenblocks 12; crosshair 0; qz_rhand "%s"; rsq_extra_weapons 1; give ammo; give %s; wait 2; use %s; wait 150; qz_lhand "%s"; wait 10; qz_lgrip 1; wait 40; '%(rh,gun,gun,lp)
    body+=''.join('qz_hmd "%s"; wait 40; '%h for h in HMD)+'quit'
    rc,text=E.rig.run('lanec_'+tag,body,500)
    fr=sorted(glob.glob(d+'/*.ppm')); errs=[l for l in text.splitlines() if 'error' in l.lower() and 'GL_' not in l and 'voxeldef' not in l.lower()]
    shutil.copy(fr[-1],os.path.join(LANE,'rigout',tag+'_last.ppm')) if fr else None
    import PIL.Image as I
    for k,f in enumerate(fr[-2*len(HMD)::2] if fr else []): I.open(f).save(os.path.join(LANE,'rigout',f'{tag}_v{k}.png'))
    print('rc',rc,'frames',len(fr),'non-voxelpack error lines',len(errs),errs[:5])
    print([l for l in text.splitlines() if 'engine OK' in l][:1])
if __name__=='__main__': run(*sys.argv[1:4],int(sys.argv[4]))
