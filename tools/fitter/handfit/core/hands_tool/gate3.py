"""TEST ONLY: round-3 headset gate on QuestZDoom 17.3 (the depot rig, read-only use), owner's load order
doom2 -> brutal22test6 -> BD_VoxelPack -> pack (+ the rig's probe for the reload tables / phases).
Per gun, one engine run: give, select, rest (+ off hand on the support with grip held for the flamer / within 13 cm for
the pistol cup), fire (trigger held), alt-fire, VR reload driven by the off hand (pistol: rig mags.py geometry from the
probe's own dump of the pack's tables; flamer: +reload, BD22's own), frame dumps every N tics; logs grepped for
'Script error' (not BD_VoxelPack's voxeldef), 'VM abort', 'exception', 'Unknown'.
usage: gate3.py <pk3> <tag> <Gun> [row]"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, re, glob, shutil, importlib, json
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIGDIR=_DP.RIG
os.environ.update(B22_BUILD=os.path.join(LANE,'rigout'),B22_RIG=RIGDIR+'/build/rig',
                  B22_IWAD=(_DP.GAMEDATA + '/doom2.wad'),B22_BD22=(_DP.GAMEDATA + '/brutal22test6.pk3'),B22_VOX=(_DP.GAMEDATA + '/BD_VoxelPack.pk3'))
sys.path.insert(0,RIGDIR)
import rig
def errs_of(text):
    bad=[l for l in text.splitlines() if re.search(r'Script error|VM abort|exception|Unknown|Tried to|null pointer|out of bounds|aborted',l,re.I)]
    ours=[l for l in bad if 'voxeldef' not in l.lower() and 'Unknown type' not in l]
    vox=[l for l in bad if 'voxeldef' in l.lower()]
    return ours,vox
def body_close(gun,hmd,lp_far):
    rh='%.4f %.4f %.4f 30 0 0'%rig.RHAND
    return ('wait 100; god; notarget; screenblocks 12; crosshair 0; rsq_extra_weapons 1; set lanec_flamelog 1; qz_rhand "%s"; qz_lhand "%s"; give ammo; give %s; wait 2; use %s; wait 150; '
            'qz_hmd "%s"; wait 30; echo LANEC_CLOSE_REST; wait 20; echo LANEC_CLOSE_FIRE; +attack; wait 45; -attack; wait 40; echo LANEC_CLOSE_END; quit'%(rh,lp_far,gun,gun,hmd))
def body_for(gun,lp_sup,lp_far,mag=None):
    rh='%.4f %.4f %.4f 30 0 0'%rig.RHAND
    s=('wait 100; god; notarget; screenblocks 12; crosshair 0; rsq_extra_weapons 1; rsr_reload 1; rsr_debug 1; set lanec_flamelog 1; qz_rhand "%s"; '
       'qz_lhand "%s"; give ammo; give %s; wait 2; use %s; wait 150; echo LANEC_REST; '%(rh,lp_far,gun,gun))
    s+=('qz_hmd "0.70 1.40 -0.45 -15 80 0"; wait 20; qz_hmd "0 1.6 0 0 0 0"; wait 5; ')
    s+=('qz_lhand "%s"; wait 10; qz_lgrip 1; wait 30; echo LANEC_SUPPORT; qz_hmd "0.70 1.40 -0.45 -15 80 0"; wait 25; '%lp_sup)
    for k,h in enumerate([h for h in os.environ.get('LANEC_EXTRA_HMD','').split('|') if h]): s+='echo LANEC_VIEW%d; qz_hmd "%s"; wait 25; '%(k,h)
    s+='qz_hmd "0 1.6 0 0 0 0"; wait 5; '
    s+=('echo LANEC_FIRE; +attack; wait 6; qz_hmd "0.70 1.40 -0.45 -15 80 0"; wait 14; -attack; qz_hmd "0 1.6 0 0 0 0"; wait 20; qz_lgrip 0; wait 5; ')
    s+=('echo LANEC_ALTFIRE; +altattack; wait 20; -altattack; wait 30; ')
    if mag:
        s+=('echo LANEC_RELOAD; qz_hmd "0.70 1.40 -0.45 -15 80 0"; take %s 999; wait 10; +reload; wait 4; -reload; wait 30; qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 12; '
            'qz_lhand "%s"; wait 15; qz_lhand "%s"; wait 15; echo LANEC_MIDRELOAD; qz_lhand "%s"; wait 25; qz_ltrigger 0; wait 40; '%(mag['magammo'],rig.lpose(0,40,-30),mag['p1'],mag['p2'],mag['p3']))
    else:
        s+=('echo LANEC_RELOAD; qz_hmd "0.70 1.40 -0.45 -15 80 0"; +reload; wait 4; -reload; wait 20; echo LANEC_MIDRELOAD; wait 60; ')
    s+='quit'
    return s
def run(pk3,tag,gun,row=None):
    d=os.path.join(LANE,'rigout','shots',tag); shutil.rmtree(d,ignore_errors=True); os.makedirs(d)
    os.environ.update(QZ_RES='480',QZ_DUMP_EVERY=os.environ.get('LANEC_DUMP','3'),QZ_DUMP_DIR=d,B22_PK3=pk3)
    os.environ.pop('B22_NOPROBE',None)
    importlib.reload(rig)
    import engine_check2 as E2
    sp=[float(a) for a in os.environ['LANEC_SUP'].split(',')] if os.environ.get('LANEC_SUP') else (E2.support_point(row) if row else (30,0,-5))
    lp_sup=rig.lpose(*sp); lp_far=rig.lpose(0,40,-30)
    mag=None
    if gun=='BrutalPistol' and not os.environ.get('LANEC_CLOSE'):
        sys.path.insert(0,RIGDIR); import mags
        # geometry from the PACK's own tables: run the boot dump first (probe prints B22 GUN lines)
        rc,text=rig.run('boot','wait 80; quit',120); g=mags.tables()[2]
        mag=dict(magammo='BDPistolAmmo',p1=mags.at(g,g['M']+3),p2=mags.at(g,g['M']*0.5),p3=mags.at(g,0))
    body=body_close(gun,os.environ['LANEC_CLOSE'],lp_far) if os.environ.get('LANEC_CLOSE') else body_for(gun,lp_sup,lp_far,mag)
    rc,text=rig.run('lanec3_'+tag,body,900)
    ours,vox=errs_of(text)
    frames=sorted(glob.glob(d+'/*.ppm'))
    phases=re.findall(r'rsr t\d+ gun \d+: (\w+) -> (\w+)',text)
    ok=[l for l in text.splitlines() if 'engine OK' in l][:1]
    marks={m:None for m in ('LANEC_REST','LANEC_SUPPORT','LANEC_FIRE','LANEC_ALTFIRE','LANEC_RELOAD','LANEC_MIDRELOAD')}
    for m in marks: marks[m]=m in text
    res=dict(tag=tag,pk3=pk3,gun=gun,rc=rc,frames=len(frames),errors_ours=ours[:20],voxelpack_script_errors=len(vox),engine=ok,reload_phases=phases,markers=marks,
             shots=[os.path.basename(f) for f in frames])
    json.dump(res,open(os.path.join(LANE,'rigout',f'gate3_{tag}.json'),'w'),indent=1)
    print(json.dumps({k:v for k,v in res.items() if k!='shots'}))
    return res
if __name__=='__main__': run(sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]) if len(sys.argv)>4 else None)
