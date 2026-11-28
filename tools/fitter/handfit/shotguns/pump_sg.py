"""TEST ONLY (shotguns lane: the Depot rig pump.py with its gun-frame numbers moved by the port, ported_Shot_Gun.json R, t): two shells into BD22's pump shotgun through the loading port, then a hand pump stroke."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import re, sys
sys.path.insert(0, _DP.RIG)
import rig, handrot as h, json, numpy as np
J = json.load(open((_DP.WORK + '/runs/lane_b_sg' + '/tools/handfit/port/fits/ported_Shot_Gun.json'))); R = np.array(J['R']); t = np.array(J['t'])
mp = lambda p: tuple(R @ np.array(p) + t); md = lambda v: tuple(R @ np.array(v))
PORT = mp((19.0, 0.0, -2.8)); PUSH = md((1.0, 0.0, 0.0)); DEPTH = 6.0
SHELL = (1.489, 2.834, -2.439); AXIS = (0.537, -0.009, 0.844)
GRAB = mp((40.1, 0.0, -2.8)); PULL = md((-1.0, 0.0, -0.002)); BORE = md((1.0, 0.0, 0.0)); TRAVEL = 6.4
PALM = (-1.5, 2.0, -4.5)
def at(sv):
    return h.place(SHELL, AXIS, tuple(PORT[k] + PUSH[k] * sv for k in range(3)), PUSH)[0]
def pump(f):
    return h.place(PALM, (1, 0, 0), tuple(GRAB[k] + PULL[k] * TRAVEL * f for k in range(3)), BORE)[0]
FAR = '-0.25 1.3 -0.3 30 0 0'
load = ''
for n in range(2):
    load += ('qz_lhand "%s"; wait 10; qz_ltrigger 1; wait 10; qz_lhand "%s"; wait 12; qz_lhand "%s"; wait 12; '
             'qz_lhand "%s"; wait 15; qz_ltrigger 0; wait 10; ' % (FAR, at(-6), at(-2), at(DEPTH + 0.5)))
s = ('wait 120; god; rsr_reload 1; rsr_grab_with 0; rsr_debug 1; give Shot_Gun; give AmmoShell 40; use Shot_Gun; wait 80; '
     '+attack; wait 3; -attack; wait 50; +attack; wait 3; -attack; wait 50; +reload; wait 4; -reload; wait 25; ' + load +
     ('qz_lhand "%s"; wait 10; +attack; wait 3; -attack; wait 6; qz_lhand "%s"; wait 6; qz_ltrigger 1; wait 8; qz_lhand "%s"; wait 10; qz_lhand "%s"; wait 10; qz_ltrigger 0; wait 40; quit'
     % (FAR, pump(0), pump(1.0), pump(0))))
rig.run('pump', s, 260)
t = open(rig.OUT + '/pump.log', errors='replace').read()
for l in t.splitlines():
    if re.search(r'^rsp t|PROBE|B22 S .*Shot_Gun', l): print(l[:170])
