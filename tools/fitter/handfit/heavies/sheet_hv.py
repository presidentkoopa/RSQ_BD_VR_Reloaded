"""Heavies lane rig check, TWO engine runs per gun (QZD 17.3 rig, doom2 > brutal22test6 > BD_VoxelPack > pack), one at a time
under $RSQ_RIGLOCK:
  eye run:  give, select, rest -> steadied (off hand at the gun's ported SupportPoint, grip pressed) -> firing -> alt-fire -> reload
            button -> fire; log scanned for script errors (probe on).
  side run: rest -> steadied -> firing.
Between segments the head turns away (yaw 180) for 16 tics, and both runs end in that away view: frames that look like the last
frame are away frames, the rest split into view segments; the last three are rest, steadied, firing (each pick = its last frame). Picks are written as PNG and
the run's frame dumps deleted.
usage: python3 sheet_hv.py <pk3> <Gun> [<Gun> ...]       -> RUN/shots/hv_<view>_<Gun>_<state>.png, RUN/shots/hv_<Gun>.json"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, glob, shutil, json, numpy as np
from PIL import Image
RIGD = _DP.RIG; sys.path.insert(0, RIGD)
RUN = os.environ.get('HV_RUN', _DP.WORK + '/runs/lane_b_hvrun'); OUT = RUN + '/shots'; os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__)); FITS = os.path.join(_DP.FITS)
os.environ.update(B22_IWAD=(_DP.GAMEDATA + '/doom2.wad'), B22_BD22=(_DP.GAMEDATA + '/brutal22test6.pk3'),
                  B22_VOX=(_DP.GAMEDATA + '/BD_VoxelPack.pk3'), B22_BUILD=RUN, B22_PK3=os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else '')
import rig
VIEWS = {'eye': '0.25 1.45 0.15 -25 0 0', 'side': '0.85 1.30 -0.50 0 90 0'}
AWAY = '0.25 1.45 0.15 0 180 0'
def sup(g):
    try: return [100 * v for v in json.load(open(os.path.join(FITS, '%s_hv.json' % g)))['hand']['support']['sup_point_m']]
    except Exception: return [30.0, 0.0, -5.0]
def script(g, view):
    rh = '%.4f %.4f %.4f 30 0 0' % rig.RHAND; A = 'qz_hmd "%s"; wait 16; ' % AWAY; V = 'qz_hmd "%s"; wait 6; ' % VIEWS[view]
    s = 'wait 100; god; notarget; screenblocks 12; crosshair 0; rsq_extra_weapons 1; rsq_ballistics 2; rsr_reload 1; qz_rhand "%s"; give ammo; give %s; wait 2; use %s; wait 150; ' % (rh, g, g)
    s += V + 'wait 30; ' + A + 'qz_lhand "%s"; wait 10; qz_lgrip 1; ' % rig.lpose(*sup(g)) + V + 'wait 30; ' + A + V + '+attack; wait 24; '
    if view == 'eye':
        s += A + '-attack; wait 20; +altattack; wait 20; -altattack; wait 40; +reload; wait 6; -reload; wait 80; +attack; wait 10; -attack; wait 30; '
    else:
        s += A + '-attack; wait 10; '
    return s + 'quit'
def shoot(g, view, pk3):
    d = os.path.join(OUT, 'dump_%s_%s' % (view, g)); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    os.environ.update(QZ_RES='480', QZ_DUMP_EVERY='1', QZ_DUMP_DIR=d, B22_PK3=pk3)
    if view == 'eye': os.environ.pop('B22_NOPROBE', None)
    else: os.environ['B22_NOPROBE'] = '1'
    rc, text = rig.run('hv_%s_%s' % (view, g), script(g, view), 360)
    fr = sorted(glob.glob(d + '/*.ppm'))
    errs = [l for l in text.splitlines() if ('Script error' in l or 'VM execution aborted' in l or 'Unknown' in l and 'class' in l) and 'BD_VoxelPack' not in l and 'voxeldef' not in l]
    out = dict(frames=len(fr), errs=errs[:6], rc=rc)
    if fr:
        sm = [np.asarray(Image.open(f).convert('L').resize((96, 96)), float) for f in fr]
        # both runs END in the away view: frames like the last one are away frames; the view segments are the runs of the others.
        # Picks from the end: the last 3 view segments are rest, steadied, firing; each pick is its segment's last frame.
        dl = np.array([np.abs(x - sm[-1]).mean() for x in sm]); thr = 0.35 * dl.max(); isv = dl > thr
        segs = []; k = 0
        while k < len(fr):
            if isv[k]:
                e = k
                while e + 1 < len(fr) and isv[e + 1]: e += 1
                segs.append((k, e)); k = e + 1
            else: k += 1
        segs = [x for x in segs if x[1] - x[0] >= 1] or segs
        last = segs[-3:] if len(segs) >= 3 else (segs + [(len(fr) - 1, len(fr) - 1)] * 3)[:3]
        picks = {'rest': last[0][1], 'steady': last[1][1], 'fire': last[2][1]}
        out['segments'] = [[int(a), int(b)] for a, b in segs]
        for st, k in picks.items(): Image.open(fr[k]).save(os.path.join(OUT, 'hv_%s_%s_%s.png' % (view, g, st)))
        out['picks'] = {k: int(v) for k, v in picks.items()}
    shutil.rmtree(d, ignore_errors=True)
    if view == 'eye':
        out['log_tail'] = [l for l in text.splitlines() if l.startswith('B22 ') and ('reload' in l.lower() or 'state' in l.lower())][-12:]
    return out
if __name__ == '__main__':
    pk3 = sys.argv[1]
    for g in sys.argv[2:]:
        res = {v: shoot(g, v, pk3) for v in ('eye', 'side')}
        json.dump(res, open(os.path.join(OUT, 'hv_%s.json' % g), 'w'), indent=1)
        print(g, json.dumps({v: dict(frames=r['frames'], errs=r['errs'], picks=r.get('picks')) for v, r in res.items()}), flush=True)
        os.system(('git -C ' + _DP.DEPOT + ' checkout -q tools/rig/bin/config/qzdoom.ini 2>/dev/null'))
