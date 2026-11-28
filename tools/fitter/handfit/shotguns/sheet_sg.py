"""TEST ONLY (batch 2): each changed gun at rest, steadied and firing, in QZD 17.3, from the eye.
One engine run per (gun, state), under the shared lock, one at a time. Writes PNG tiles + the sheet."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, glob, shutil, subprocess, json
from PIL import Image, ImageDraw
RIGD = _DP.RIG; sys.path.insert(0, RIGD)
OUT = (_DP.WORK + '/runs/lane_b_sgrun' + '/shots')
PK3 = sys.argv[1] if len(sys.argv) > 1 else (_DP.WORK + '/runs/lane_out_missing' + '.pk3')
os.environ.update(B22_IWAD=(_DP.GAMEDATA + '/doom2.wad'), B22_BD22=(_DP.GAMEDATA + '/brutal22test6.pk3'),
                  B22_VOX=(_DP.GAMEDATA + '/BD_VoxelPack.pk3'), B22_BUILD=_DP.WORK + '/runs/lane_b_sgrun', B22_NOPROBE='1')
import rig
EYE = os.environ.get('B1_EYE', '0.25 1.45 0.15 25 0 0')	# behind and above the gun hand, looking down the gun (lane_c's eye pose)
import json as _j
SUP = {k: tuple(v) for k, v in _j.load(open((_DP.WORK + '/runs/lane_b_sgrun' + "/sup.json"))).items()}	# moved handtable SupportPoint (cm) per gun
def shoot(gun, state, tag):
    d = os.path.join(OUT, tag); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    os.environ.update(QZ_RES='480', QZ_DUMP_EVERY='2', QZ_DUMP_DIR=d, B22_PK3=PK3)
    rh = '%.4f %.4f %.4f 30 0 0' % rig.RHAND
    s = 'wait 100; god; notarget; screenblocks 12; crosshair 0; rsq_extra_weapons 1; qz_rhand "%s"; give ammo; give %s; wait 2; use %s; wait 150; qz_hmd "%s"; wait 5; ' % (rh, gun, gun, EYE)
    if state in ('steady', 'fire'):
        # pistol: a cup gun steadies by CLOSENESS (hands.zs: off hand within 13 cm), no grip press;
        # the flamer steadies as stock (grip pressed, off hand at its support point)
        s += ('qz_lhand "%s"; wait 40; ' % rig.lpose(-3.0, 3.0, -8.0)) if gun in ('BrutalPistol', 'Revolver', 'BrutalRevolver') else ('qz_lhand "%s"; wait 10; qz_lgrip 1; wait 40; ' % rig.lpose(*SUP[gun]))
    if state == 'fire':
        s += ('+attack; wait 3; -attack; wait 6; ' * 3) if gun in ('BrutalPistol', 'Revolver', 'BrutalRevolver') else '+attack; wait 30; '
        s += '+attack; wait 2; '
    else:
        s += 'wait 20; '
    s += 'quit'
    rc, text = rig.run('sheet_' + tag, s, 300)
    fr = sorted(glob.glob(d + '/*.ppm'))
    errs = [l for l in text.splitlines() if 'Script error' in l and 'BD_VoxelPack' not in l]
    return fr, errs
if __name__ == '__main__':
    res = {}
    GUNS = os.environ.get('B1_GUNS', 'BrutalSMG').split(','); STS = os.environ.get('B1_STATES', 'rest,steady,fire').split(',')
    for gun in GUNS:
        for st in STS:
            fr, errs = shoot(gun, st, 'sg%s_%s_%s' % (os.environ.get('B2_TAG', ''), gun, st))
            res['%s_%s' % (gun, st)] = dict(frames=len(fr), errs=errs[:3])
            keep = fr[-6:]
            for k, f in enumerate(keep):
                Image.open(f).save(os.path.join(OUT, 'sg%s_%s_%s_%d.png' % (os.environ.get('B2_TAG', ''), gun, st, k)))
            print(gun, st, len(fr), errs[:2], flush=True)
    json.dump(res, open(os.path.join(OUT, 'sg_sheet_runs.json'), 'w'), indent=1)
