"""rig_holds.py <pk3> <tag> <job...>: each reload hold on the rig (TEST ONLY): the reload is started, the off hand takes the part,
is brought up in front of the eye and held still (SHOW, 40 tics: the frame 20 tics in is kept, from the eye), then the part is put in
and the reload runs on; the log gives the phases (rsr / rsb / rsp / rsm lines) and script errors.
jobs: mag<i> (rsr row i, Depot mags.py geometry from the probe's own table dump), brk<Class>:<ammo>:<feed> (Depot brk.py chambers),
      pump (the moved Shot_Gun's port / pump from the probe's B22 PUMP dump), m203 (port/gate_gun.m203's moves).
Frames: lane_b_out/offhand_gate/shots/hold_<job>_<tag>.png; ppm dumps deleted. Rig only, not headset-confirmed."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigshot as R
G = R.G; rig = G.rig
sys.path.insert(0, G.RIGD)
import mags, brk, handrot as h
DMG = os.path.join(G.OUT, 'oht_dmg.pk3')
HMD = '0.10 1.58 0.08 -25 0 0'
SHOW = '-0.05 1.40 -0.33 30 0 0'
def show():
    return 'qz_lhand "%s"; wait 6; netevent oht_mark; wait 40; ' % SHOW
END = 'netevent oht_mark; wait 5; quit'
def pick(png):
    def f(text):
        q = [int(x) for x in re.findall(r'OHT MARK t (\d+)', text)]
        return {png: ('tic', q[0] + 20)} if q else {}	# the SHOW pose's middle, by game tic (rigshot: the probe's frame lines)
    return f
SET = G.SET + 'screenblocks 12; crosshair 0; rsr_grab_with 0; rsr_debug 1; rsq_reload_nonstd 1; qz_hmd "%s"; ' % HMD
BOOT = {}
def boot(pk3):
    if BOOT.get('pk3') != pk3:
        G.setpk3(pk3); G.locked(rig.run, 'boot', 'wait 100; quit', 150); BOOT['pk3'] = pk3
def job_mag(i):
    g = mags.tables()[i]; c = mags.CLS[i]
    # most guns: a burst, then the reload button
    start = '+attack; wait 12; -attack; wait 25; +reload; wait 4; -reload; wait 30; '
    if i == 15: start = '+attack; wait 20; -attack; wait 40; +attack; wait 30; -attack; wait 40; '	# the Nuker: one shot, then the trigger on empty
    if i == 17: start = 'take RSQ_Mag_Minigun 150; wait 10; +reload; wait 4; -reload; wait 30; '	# the Minigun: its magazine (RSQ_Mag_Minigun, counters.zs) part spent, then the button
    s = ('wait 100; ' + SET + 'give %s; give %s 400; use %s; wait 150; ' % (c, g['reserve'], c) + start +
         'qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 12; ' % rig.lpose(0, 40, -30) + show() +
         'qz_lhand "%s"; wait 15; qz_lhand "%s"; wait 15; qz_lhand "%s"; wait 25; qz_ltrigger 0; wait 40; ' % (mags.at(g, g['M'] + 3), mags.at(g, g['M'] * 0.5), mags.at(g, 0)) + END)
    return s, r'rsr t\d+ gun %d: (\w+) -> (\w+)' % i
def job_brk(spec):
    c, ammo, feed = spec.split(':')
    G.locked(rig.run, 'open_' + c, 'wait 120; god; rsq_extra_weapons 1; rsb_revolver_feed %s; rsr_reload 1; rsr_debug 1; give %s; give %s 100; use %s; wait 90; '
             '+attack; wait 3; -attack; wait 30; +attack; wait 3; -attack; wait 40; +reload; wait 4; -reload; wait 60; quit' % (feed, c, ammo, c), 200)
    hb, ht, ch = brk.chambers(c); load = ''
    for n, (tk, bk, dep) in enumerate(ch):
        a = ht - hb; p1 = h.place(ht, a, tk - bk * (dep + 1.0), bk)[0]; p2 = h.place(ht, a, tk - bk * (dep * 0.5), bk)[0]; p3 = h.place(ht, a, tk, bk)[0]
        load += 'qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 10; ' % brk.FAR + (show() if n == 0 else '') + \
                'qz_lhand "%s"; wait 12; qz_lhand "%s"; wait 10; qz_lhand "%s"; wait 15; qz_ltrigger 0; wait 10; ' % (p1, p2, p3)
    s = ('wait 100; ' + SET + 'rsb_revolver_feed %s; give %s; give %s 100; use %s; wait 120; +attack; wait 3; -attack; wait 30; +attack; wait 3; -attack; wait 40; '
         '+reload; wait 4; -reload; wait 30; ' % (feed, c, ammo, c) + load +
         'qz_lhand "%s"; wait 10; qz_rhand "%s"; wait 4; qz_rhand "%s"; wait 40; ' % (brk.FAR, brk.RH % (70, 0, 0), brk.RH % (30, 0, 0)) + END)
    return s, r'rsb t\d+[^\n]*'
def job_pump():
	# the moved Shot_Gun's port, push, shell-in-hand, grab, pull, travel from the probe's dump (B22 PUMP 1 ...)
    t = open(rig.OUT + '/boot.log', errors='replace').read()
    m = re.search(r'B22 PUMP 1 port (\S+) (\S+) (\S+) push (\S+) (\S+) (\S+) depth (\S+) shell (\S+) (\S+) (\S+) axis (\S+) (\S+) (\S+) grab (\S+) (\S+) (\S+) pull (\S+) (\S+) (\S+) travel (\S+)', t)
    v = [float(x) for x in m.groups()]; PORT, PUSH, DEPTH, SHELL, AXIS, GRAB, PULL, TRAVEL = v[0:3], v[3:6], v[6], v[7:10], v[10:13], v[13:16], v[16:19], v[19]
    at = lambda sv: h.place(SHELL, AXIS, tuple(PORT[k] + PUSH[k] * sv for k in range(3)), PUSH)[0]
    PALM = (-1.5, 2.0, -4.5); pmp = lambda f: h.place(PALM, (1, 0, 0), tuple(GRAB[k] + PULL[k] * TRAVEL * f for k in range(3)), (1, 0, 0))[0]
    FAR = '-0.25 1.3 -0.3 30 0 0'; load = ''
    for n in range(2):
        load += 'qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 10; ' % FAR + (show() if n == 0 else '') + \
                'qz_lhand "%s"; wait 12; qz_lhand "%s"; wait 12; qz_lhand "%s"; wait 15; qz_ltrigger 0; wait 10; ' % (at(-6), at(-2), at(DEPTH + 0.5))
    s = ('wait 100; ' + SET + 'give Shot_Gun; give AmmoShell 40; use Shot_Gun; wait 120; +attack; wait 3; -attack; wait 50; +attack; wait 3; -attack; wait 50; '
         '+reload; wait 4; -reload; wait 25; ' + load + 'qz_lhand "%s"; wait 10; +attack; wait 3; -attack; wait 6; qz_lhand "%s"; wait 6; qz_ltrigger 1; wait 8; '
         'qz_lhand "%s"; wait 10; qz_lhand "%s"; wait 10; qz_ltrigger 0; wait 40; ' % (FAR, pmp(0), pmp(1.0), pmp(0)) + END)
    return s, r'rsp t\d+[^\n]*'
def job_m203():
    import numpy as np, json as js
    P = js.load(open(os.path.join(_DP.FITS, 'ported_Rifle.json'))); Rm = np.array(P['R']); tm = np.array(P['t'])
    MV = lambda q: tuple(Rm @ np.array(q, float) + tm); MD = lambda v: tuple(Rm @ np.array(v, float))
    L, U, TR, REAR = (0.520, -5.000, 11.0, 28.44); PALM = (-1.5, 2.0, -4.5); RND, RAX = (-1.930, 4.560, -4.500), (0, 0, 1)
    palm_at = lambda x: h.place(PALM, (1, 0, 0), MV((x, L, U - 2.0)), MD((1, 0, 0)))[0]
    round_at = lambda x: h.place(RND, RAX, MV((x, L, U)), MD((1, 0, 0)))[0]
    FAR = '-0.25 1.3 -0.3 30 0 0'
    s = ('wait 100; ' + SET + 'give Rifle; give Clip2 100; give AmmoRocket 10; use Rifle; wait 120; +altattack; wait 3; -altattack; wait 60; '
         'qz_lhand "%s"; wait 10; qz_lgrip 1; wait 10; qz_ltrigger 1; wait 6; qz_lhand "%s"; wait 8; qz_lhand "%s"; wait 8; qz_lhand "%s"; wait 10; qz_ltrigger 0; qz_lgrip 0; wait 6; '
         'qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 10; ' % (palm_at(40), palm_at(40 + TR * 0.4), palm_at(40 + TR * 0.75), palm_at(40 + TR + 0.5), FAR) + show() +
         'qz_lhand "%s"; wait 12; qz_lhand "%s"; wait 15; qz_ltrigger 0; wait 8; '
         'qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 8; qz_lhand "%s"; wait 8; qz_lhand "%s"; wait 10; qz_ltrigger 0; wait 8; qz_lhand "%s"; wait 10; +altattack; wait 3; -altattack; wait 40; '
         % (round_at(REAR + 3.5), round_at(REAR + TR + 0.4 + 4.3), palm_at(40 + TR), palm_at(40 + TR / 2), palm_at(39.5), FAR) + END)
    return s, r'rs[mk] t?\d*[^\n]*|[^\n]*m203[^\n]*'
def run(pk3, tag, job):
    pk3 = os.path.abspath(pk3); boot(pk3); G.setpk3(pk3)
    if job.startswith('mag'): s, pat = job_mag(int(job[3:]))
    elif job.startswith('brk'): s, pat = job_brk(job[3:])
    elif job == 'pump': s, pat = job_pump()
    elif job == 'm203': s, pat = job_m203()
    nm = 'hold_%s_%s' % (job.replace(':', '_') if job.startswith('brk') else job, tag); text, o = R.shot(pk3, nm, s, pick(nm + '.png'), extra=[DMG], secs=400)
    ph = re.findall(pat, text); errs, vm = R.errors(text)
    return dict(job=job, frame=o, errors=errs, vm=vm, log=[(x if isinstance(x, str) else ' -> '.join(x)) for x in ph][-14:])
if __name__ == '__main__':
    pk3, tag = sys.argv[1], sys.argv[2]; out = {}
    for j in sys.argv[3:]:
        out[j] = run(pk3, tag, j); print(j, json.dumps(out[j], indent=1), flush=True)
    json.dump(out, open(os.path.join(G.OUT, 'holds_%s_%s.json' % (tag, '_'.join(x.split(':')[0] for x in sys.argv[3:])[:80])), 'w'), indent=1)
