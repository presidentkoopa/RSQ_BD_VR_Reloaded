"""gate_gun.py: the per-gun rig gate for a gun ported with port_gun.py (QuestZDoom 17.3 rig, doom2 -> brutal22test6 ->
BD_VoxelPack -> pack, ONE engine at a time under an exclusive lock, the rig ini restored after every run).
  gate_gun.py smoke  <pk3> <Class...>      give, select, steady, fire, alt-fire, reload, fire: script errors, held, shots, reload phases
  gate_gun.py sheet  <pk3> <Class...>      rest / steady / fire frames from the eye and the side (PNG tiles)
  gate_gun.py hands  <pk3> <job...>        Depot mags.py <ids> / brk<ids> (brk.py) / m203 (the moved rifle's launcher reload)
  gate_gun.py compose <out.png> <Class...> the sheet beside each gun's 1.92 eye / side render
Env (all optional, tools/depot.py): RSQ_SET (the set; default ../rs_brutal22weaponsq), RSQ_GAMEDATA (doom2.wad,
brutal22test6.pk3, BD_VoxelPack.pk3; default <depot>/../gamedata), RSQ_RIGLOCK (default <depot>/../rig.lock),
RSQ_GATE (logs and shots; default <work>/gate). Rig only: nothing here is a headset test."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, re, json, glob, shutil, fcntl, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = _DP.SET
DEPOT = _DP.DEPOT; RIGD = _DP.RIG
GD = _DP.GAMEDATA; LOCK = _DP.LOCK
OUT = os.path.abspath(os.environ.get('RSQ_GATE', os.path.join(_DP.WORK, 'gate'))); os.makedirs(OUT + '/shots', exist_ok=True)
os.environ.update(B22_IWAD=GD + '/doom2.wad', B22_BD22=GD + '/brutal22test6.pk3', B22_VOX=GD + '/BD_VoxelPack.pk3', B22_BUILD=OUT)
os.environ.pop('B22_RIG', None)
sys.path.insert(0, RIGD); sys.path.insert(0, HERE)
import rig
rig.OUT = OUT + '/logs'; rig.PROBE = OUT + '/probe.pk3'
if not os.path.exists(rig.PROBE):	# the Depot's probe (B22 S / SHOT / T log lines), zipped from tools/rig/probe
    import zipfile
    with zipfile.ZipFile(rig.PROBE, 'w') as z:
        for f in ('MAPINFO.txt', 'zscript.txt'): z.write(os.path.join(RIGD, 'probe', f), f)
def setpk3(pk3): rig.PK3 = pk3; os.environ['B22_PK3'] = pk3
CUP = ('BrutalPistol', 'Revolver', 'BrutalRevolver')	# one-hand guns steady by closeness (hands.zs: off hand within 13 cm)
SET = 'god; notarget; rsq_hands 1; rsq_extra_weapons 1; rsq_ballistics 2; rsr_reload 1; rsq_scope2_sniper 1; rsq_scope2_railgun 1; rsb_revolver_feed 0; '
def locked(fn, *a, **k):
    with open(LOCK, 'a') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try: return fn(*a, **k)
        finally:
            subprocess.run(['git', '-C', DEPOT, 'checkout', '-q', 'tools/rig/bin/config/qzdoom.ini'])
def support_cm(cls):
    """the gun's SupportPoint (handtable row, m -> cm) from the tree, so the steady pose follows the moved gun."""
    sys.path.insert(0, HERE); import port_gun
    row = port_gun.GUNS[cls]['row']; tx = open(os.path.join(REPO, 'src/zscript/rsq/handtable.zs')).read()
    return tuple(100 * port_gun.getrow(tx, 'SupportPoint', row))
def steady(cls):
    if cls in CUP: return 'qz_lhand "%s"; wait 40; ' % rig.lpose(-3.0, 3.0, -8.0)
    return 'qz_lhand "%s"; wait 10; qz_lgrip 1; wait 40; ' % rig.lpose(*support_cm(cls))
def check(text, cls):
    errs = [l for l in re.findall(r'Script error, "([^"]+)"[^\n]*', text) if 'BD_VoxelPack' not in l]
    vm = len(re.findall(r'VM execution aborted|Unhandled exception|Segmentation|signal 11', text))
    held = cls in set(re.findall(r'B22 S \d+ main (\S+)', text)); shots = len(re.findall(r'B22 SHOT', text))
    ph = sorted(set(re.findall(r'B22 T \d+ gun \d+ (\S+)', text)))
    return dict(errors=errs[:5], vm=vm, held=held, shots=shots, phases=ph)
def smoke(pk3, cls):
    setpk3(pk3); os.environ.pop('B22_NOPROBE', None)
    s = ('wait 120; ' + SET + 'give ammo; give RevolverRounds; give %s; wait 2; use %s; wait 170; ' % (cls, cls) + steady(cls) +
         '+attack; wait 20; -attack; wait 40; +altattack; wait 20; -altattack; wait 60; +reload; wait 6; -reload; wait 80; +attack; wait 10; -attack; wait 40; quit')
    rc, text = locked(rig.run, 'smoke_' + cls, s, 600); r = check(text, cls); r['rc'] = rc; return r
EYE = {'eye': '0.25 1.45 0.15 -25 0 0', 'side': '0.85 1.30 -0.50 0 90 0'}	# batch 3's two camera poses
def sheet(pk3, cls, state, view):
    d = os.path.join(OUT, 'dump_%s_%s_%s' % (cls, state, view)); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    setpk3(pk3); os.environ.update(QZ_RES='480', QZ_DUMP_EVERY='2', QZ_DUMP_DIR=d, B22_NOPROBE='1')
    s = 'wait 100; ' + SET + 'screenblocks 12; crosshair 0; qz_rhand "%.4f %.4f %.4f 30 0 0"; give ammo; give RevolverRounds; give %s; wait 2; use %s; wait 150; qz_hmd "%s"; wait 5; ' % (rig.RHAND + (cls, cls, EYE[view]))
    if state in ('steady', 'fire'): s += steady(cls)
    s += (('+attack; wait 3; -attack; wait 6; ' * 3 if cls in CUP else '+attack; wait 30; ') + '+attack; wait 2; ') if state == 'fire' else 'wait 20; '
    rc, text = locked(rig.run, 'sheet_%s_%s_%s' % (cls, state, view), s + 'quit', 300)
    for k in ('QZ_RES', 'QZ_DUMP_EVERY', 'QZ_DUMP_DIR', 'B22_NOPROBE'): os.environ.pop(k, None)
    fr = sorted(glob.glob(d + '/*.ppm')); from PIL import Image
    if fr: Image.open(fr[-1]).save(os.path.join(OUT, 'shots', '%s_%s_%s.png' % (cls, view, state)))
    shutil.rmtree(d, ignore_errors=True)	# frame dumps deleted; the last frame kept as PNG
    return dict(frames=len(fr), errors=check(text, cls)['errors'])
def m203(pk3, mg=False):
    """the M203 reload on the MOVED rifle: the Depot m203.py script with every tube / round target moved by the port's R, t.
    r10: mg=True ('m203mg') = the Machinegun's launcher (RSM gun 2): rsr_m203_geo.zs gun-2 numbers (bore U -6.517, AxisU(2); the Depot
    m203.py GUN=mg uses -1.517, 5 cm above the bore: it scraped in at ENTER_SIDE 5 on the unmoved gun, not on the moved one), moved by ported_Machinegun.json."""
    import numpy as np, handrot as h
    P = json.load(open(os.path.join(_DP.FITS, 'ported_%s.json' % ('Machinegun' if mg else 'Rifle')))); R = np.array(P['R']); t = np.array(P['t'])
    MV = lambda q: tuple(R @ np.array(q, float) + t); MD = lambda v: tuple(R @ np.array(v, float))
    L, U, TR, REAR = (-0.068, -6.517, 9.694, 29.272) if mg else (0.520, -5.000, 11.0, 28.44); PALM = (-1.5, 2.0, -4.5); RND, RAX = (-1.930, 4.560, -4.500), (0, 0, 1)
    palm_at = lambda x: h.place(PALM, (1, 0, 0), MV((x, L, U - 2.0)), MD((1, 0, 0)))[0]
    round_at = lambda x: h.place(RND, RAX, MV((x, L, U)), MD((1, 0, 0)))[0]
    FAR = '-0.25 1.3 -0.3 30 0 0'
    s = ('wait 120; god; rsr_reload 1; rsr_grab_with 0; rsr_debug 1; give %s; give Clip2 100; give AmmoRocket 10; use %s; wait 80; '
         '+altattack; wait 3; -altattack; wait 60; '
         'qz_lhand "%s"; wait 10; qz_lgrip 1; wait 10; qz_ltrigger 1; wait 6; '
         'qz_lhand "%s"; wait 8; qz_lhand "%s"; wait 8; qz_lhand "%s"; wait 10; qz_ltrigger 0; qz_lgrip 0; wait 6; '
         'qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 10; qz_lhand "%s"; wait 12; qz_lhand "%s"; wait 15; qz_ltrigger 0; wait 8; '
         'qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 8; qz_lhand "%s"; wait 8; qz_lhand "%s"; wait 10; qz_ltrigger 0; wait 8; '
         'qz_lhand "%s"; wait 10; +altattack; wait 3; -altattack; wait 40; quit'
         % ((('Machinegun',) * 2 if mg else ('Rifle',) * 2) + (palm_at(40),) + (palm_at(40 + TR * 0.4), palm_at(40 + TR * 0.75), palm_at(40 + TR + 0.5), FAR, round_at(REAR + 3.5), round_at(REAR + TR + 0.4 + 4.3),
            palm_at(40 + TR), palm_at(40 + TR / 2), palm_at(39.5), FAR)))
    setpk3(pk3); rc, text = locked(rig.run, 'm203mg_moved' if mg else 'm203_moved', s, 260)
    return [l[:160] for l in text.splitlines() if re.match(r'rs[mk]', l) or 'm203' in l.lower()] + ['script errors: %s' % check(text, 'Machinegun' if mg else 'Rifle')['errors']]
BOOTED = {}
def hands(pk3, job):
    if job in ('m203', 'm203mg'): return m203(pk3, job == 'm203mg')
    setpk3(pk3); os.environ.pop('B22_NOPROBE', None)
    if BOOTED.get('pk3') != pk3:	# mags.py / brk.py read the pack's own tables from the probe's dump in logs/boot.log
        locked(rig.run, 'boot', 'wait 60; quit', 120); BOOTED['pk3'] = pk3
    env = dict(os.environ, B22_PK3=pk3)
    if job.startswith('brk'):	# brk<Class>:<ammo>:<feed>  e.g. brkRevolver:AmmoShell:0 (feed 0 = a round at a time, 1 = speedloader)
        c, ammo, feed = job[3:].split(':'); env['FEED'] = feed
        locked(rig.run, 'open_' + c, 'wait 120; god; rsq_extra_weapons 1; rsb_revolver_feed %s; rsr_reload 1; rsr_debug 1; give %s; give %s 100; use %s; wait 90; '
               '+attack; wait 3; -attack; wait 30; +attack; wait 3; -attack; wait 40; +reload; wait 4; -reload; wait 60; quit' % (feed, c, ammo, c), 200)
        cmd = ['python3', 'brk.py', c, ammo]
    else: cmd = ['python3', 'mags.py'] + job.split()
    r = locked(subprocess.run, cmd, cwd=RIGD, env=env, capture_output=True, text=True)
    return (r.stdout + r.stderr).splitlines()[-25:]
def compose(out, guns):
    from PIL import Image, ImageDraw
    REF = os.path.join(_DP.SET, 'reference', '192_poses'); sts = ['rest', 'steady', 'fire']	# REF: the owner's 1.92 holds, rendered
    rows = [(g, v) for g in guns for v in ('eye', 'side')]; w, h = 480, 360; lh = 22; top = 34
    for f in glob.glob(OUT + '/shots/*.png'): w, h = Image.open(f).size; break
    sheet = Image.new('RGB', (w * 4, top + (h + lh) * len(rows)), (24, 24, 24)); dr = ImageDraw.Draw(sheet)
    dr.text((8, 8), os.environ.get('RSQ_SHEET_TITLE', 'batch 4: FBX hands, the gun moved to the hand (port_gun.py)') + '. QZD 17.3 rig, doom2 > brutal22test6 > BD_VoxelPack > pack. Rig only, not headset-confirmed', fill=(230, 230, 230))
    for r, (g, v) in enumerate(rows):
        y = top + r * (h + lh); refs = glob.glob(os.path.join(REF, '%s_%s.*' % (g, v)))
        dr.text((6, y + 4), '%s: 1.92 (%s)%s' % (g, v, '' if refs else ': NO 1.92 render'), fill=(150, 200, 255))
        if refs:
            ref = Image.open(refs[0]).convert('RGB'); ref = ref.resize((w, int(ref.size[1] * w / ref.size[0]))); sheet.paste(ref.crop((0, 0, w, h)), (0, y + lh))
        for c, s in enumerate(sts):
            f = os.path.join(OUT, 'shots', '%s_%s_%s.png' % (g, v, s)); dr.text(((c + 1) * w + 6, y + 4), '%s, %s: %s' % (g, v, s), fill=(255, 220, 120))
            if os.path.exists(f): sheet.paste(Image.open(f).convert('RGB'), ((c + 1) * w, y + lh))
    sheet.save(out); print(out, sheet.size)
if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'compose': compose(sys.argv[2], sys.argv[3:]); sys.exit()
    pk3 = os.path.abspath(sys.argv[2]); res = {}
    for a in sys.argv[3:]:
        if cmd == 'smoke': res[a] = smoke(pk3, a)
        elif cmd == 'sheet': res[a] = {'%s_%s' % (st, v): sheet(pk3, a, st, v) for st in os.environ.get('SHEET_STATES', 'rest,steady,fire').split(',') for v in os.environ.get('SHEET_VIEWS', 'eye,side').split(',')}	# r12: SHEET_STATES / SHEET_VIEWS narrow the runs
        elif cmd == 'hands': res[a] = hands(pk3, a)
        print(a, json.dumps(res[a], indent=1), flush=True)
    json.dump(res, open(os.path.join(OUT, '%s_%s.json' % (cmd, '_'.join(sys.argv[3:]).replace(' ', ''))), 'w'), indent=1)
