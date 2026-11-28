"""rigsheet.py <pk3> <Class> [<Class> ...]: the support hands on the QZD 17.3 rig (Depot tools/rig, doom2 > brutal22test6 >
BD_VoxelPack > pack), TWO engine runs per gun (eye, side), one at a time under flock -x $RSQ_RIGLOCK, the rig ini restored after
every run, the .ppm dumps deleted right after the picks are converted.
One run: give, select, rest -> steadied (off hand at the gun's SupportPoint, grip pressed: the engine's two-hand hold, which is when
the support hand shows) -> the kick (3 tics into +attack) -> firing (24 tics) [-> reload: +reload, 30 tics, for --reload guns].
Between segments the head turns away (yaw 180) for 16 tics; the run ends in that away view; frames like the last one are away
frames, the rest split into segments; the last N are the states (each pick = the segment's last frame).
Log scanned for `Script error` / VM aborts not from BD_VoxelPack. Writes RUN/shots/<Class>_<view>_<state>.png and RUN/rig_<Class>.json."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, glob, shutil, json, fcntl, subprocess, numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
RIGD = _DP.RIG; DEPOT = _DP.DEPOT; LOCK = _DP.LOCK
RUN = os.environ.get('S192_RUN', _DP.WORK + '/runs/sup192run'); OUT = RUN + '/shots'; os.makedirs(OUT, exist_ok=True)
GD = _DP.GAMEDATA
os.environ.update(B22_IWAD=GD + '/doom2.wad', B22_BD22=GD + '/brutal22test6.pk3', B22_VOX=GD + '/BD_VoxelPack.pk3', B22_BUILD=RUN)
os.environ.pop('B22_RIG', None); sys.path.insert(0, RIGD)
import rig
rig.OUT = RUN + '/logs'; os.makedirs(rig.OUT, exist_ok=True); rig.PROBE = RUN + '/probe.pk3'
if not os.path.exists(rig.PROBE):
    import zipfile
    with zipfile.ZipFile(rig.PROBE, 'w') as z:
        for f in ('MAPINFO.txt', 'zscript.txt'): z.write(os.path.join(RIGD, 'probe', f), f)
VIEWS = {'eye': '0.25 1.45 0.15 -25 0 0', 'side': '0.85 1.30 -0.50 0 90 0', 'near': '0.20 1.58 -0.02 -45 0 0'}	# near: the player's eye looking down at the off hand (closer than 'eye')
AWAY = '0.25 1.45 0.15 0 180 0'
VIEWFOR = {('Rocket_Launcher', 'side'): '1.15 1.50 -0.45 -15 90 0'}	# the steadied RPG leaves the standard side camera's frame: further out, higher, tilted down
# the rig renders about one frame per 3-4 tics: segments are 40 tics; the kick = the 3rd frame of the firing segment
SET = 'god; notarget; rsq_hands 1; rsq_extra_weapons 1; rsq_ballistics 2; rsr_reload 1; rsq_scope2_sniper 1; rsq_scope2_railgun 1; screenblocks 12; crosshair 0; '
def support_cm(g):
    import s192
    sys.path.insert(0, os.path.join(HERE, '..', 'port')); import melee_r12	# BrutalAxe (row 24)
    return tuple(100 * s192.ht_row('SupportPoint', s192.PG.GUNS[g]['row']))
def script(g, view, reload):
    """the console script + its timeline (tic marks counted back from the end: the run is real time, 35 tics/s, and the frame dumps'
    mtimes give each frame's time; the side run cannot be cut by image similarity: BD22's recoil pushes the player)"""
    rh = '%.4f %.4f %.4f 30 0 0' % rig.RHAND; give = 'give %s; ' % g
    s = 'wait 100; ' + SET + 'qz_rhand "%s"; give ammo; give RevolverRounds; %swait 2; use %s; wait 150; ' % (rh, give, g)
    T = []; t = [0]
    def w(n, mark=None):
        if mark: T.append((mark, t[0]))
        t[0] += n; return 'wait %d; ' % n
    V = 'qz_hmd "%s"; ' % VIEWFOR.get((g, view), VIEWS[view]); A = 'qz_hmd "%s"; ' % AWAY
    s += V + w(40) + w(0, 'rest') + A + w(24) + 'qz_lhand "%s"; ' % rig.lpose(*support_cm(g)) + w(10) + 'qz_lgrip 1; ' + V + w(40) + w(0, 'steady') + A + w(24)
    s += V + w(8) + '+attack; ' + w(0, 'attack') + w(40) + w(0, 'fire') + A + '-attack; ' + w(34)
    if reload: s += V + '+reload; ' + w(4) + '-reload; ' + w(40) + w(0, 'reload') + A + w(24)
    s += w(4) + 'quit'
    return s, dict(T), t[0]
def shoot(g, view, pk3, reload):
    d = os.path.join(OUT, 'dump_%s_%s' % (view, g)); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    rig.PK3 = pk3; os.environ.update(QZ_RES='480', QZ_DUMP_EVERY='1', QZ_DUMP_DIR=d, B22_PK3=pk3); os.environ.pop('B22_NOPROBE', None)
    with open(LOCK, 'a') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        sc, MK, TOT = script(g, view, reload)
        try: rc, text = rig.run('s192_%s_%s' % (view, g), sc, 400)
        finally: subprocess.run(['git', '-C', DEPOT, 'checkout', '-q', 'tools/rig/bin/config/qzdoom.ini'])
    for k in ('QZ_RES', 'QZ_DUMP_EVERY', 'QZ_DUMP_DIR'): os.environ.pop(k, None)
    fr = sorted(glob.glob(d + '/*.ppm')); tm = np.array([os.path.getmtime(f) for f in fr])
    errs = [l for l in text.splitlines() if ('Script error' in l or 'VM execution aborted' in l) and 'BD_VoxelPack' not in l]
    vox = [l for l in text.splitlines() if 'Script error' in l and 'BD_VoxelPack' in l]
    out = dict(frames=len(fr), pack_errors=errs[:6], voxelpack_errors=len(vox), rc=rc, picks={})
    if fr:
        at = lambda tic: int(np.argmin(np.abs(tm - (tm[-1] - (TOT - tic) / 35.0))))	# the frame nearest that tic
        picks = {st: at(MK[st] - 2) for st in ('rest', 'steady', 'fire', 'reload') if st in MK}
        for j in (3, 6, 9): picks['kick%d' % j] = at(MK['attack'] + j)
        picks['kick'] = picks['kick3']
        for st, k in picks.items(): Image.open(fr[k]).save(os.path.join(OUT, '%s_%s_%s.png' % (g, view, st)))
        out['picks'] = picks
    if not os.environ.get('S192_KEEP'): shutil.rmtree(d, ignore_errors=True)	# .ppm dumps deleted right after the picks are converted
    return out
if __name__ == '__main__':
    pk3 = os.path.abspath(sys.argv[1]); rl = [a[2:] for a in sys.argv[2:] if a.startswith('+r')]
    views = [v for v in ('eye', 'side', 'near') if os.environ.get('S192_VIEWS', 'eye,side,near').find(v) >= 0]
    for g in [a for a in sys.argv[2:] if not a.startswith('+r')]:
        res = {v: shoot(g, v, pk3, g in rl) for v in views}
        json.dump(res, open(os.path.join(RUN, 'rig_%s.json' % g), 'w'), indent=1)
        print(g, json.dumps({v: dict(frames=r['frames'], pack_errors=r['pack_errors'], vox=r['voxelpack_errors'], picks=r.get('picks')) for v, r in res.items()}), flush=True)
