"""hold_fit.py <outdir> <job...>: the FBX hand round each reload hold's object (ohfit.seed on the Ermac hold, then ohfit.grip).
jobs: rsr<i> (objects.rsr), rsb<i> (objects.rsb), rsp<i> (objects.pump), rsm (objects.m203). Writes <outdir>/<name>.json (z, y, metrics, seed) and <name>.png (Ermac + object / FBX + object)."""
import os, sys, json, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ohfit as O, objects as B, look
EYES_REL = [np.array(e) for e in ([-30.0, -12.0, 22.0], [-25.0, -25.0, 15.0], [-35.0, 0.0, 25.0])]	# from the object's centre, drawn cm (head behind, inside, above)
SEEDS = {}
def get(job):
    if job.startswith('rsr'): return B.rsr(int(job[3:]))
    if job.startswith('rsb'): return B.rsb(int(job[3:]))
    if job.startswith('rsp'): return B.pump(int(job[3:]))
    if job == 'rsm': return B.m203()
    raise SystemExit('unknown job ' + job)
def run(job, out, W=None, move=False, nfev=150):
    t0 = time.time(); o = get(job); E, Fe = O.ermac(*o['ermac'])
    key = o['ermac']
    if key not in SEEDS: SEEDS[key] = O.seed(E)
    z0, sm = SEEDS[key]; Ob = O.Obj(o['V'], o['F']); X0 = O.hand(O.zp(z0)); cref = X0[O.cuff_idx()]
    yi = None
    if os.environ.get('SEEDFIT'):	# another hold's FINISHED fit as the seed (same Ermac frame): its hand, and this object centred where that object was
        S = json.load(open(os.environ['SEEDFIT'])); assert tuple(S['ermac']) == tuple(o['ermac']); z0 = np.array(S['z']); so = get(S['job'])
        yi = (so['V'].min(0) + so['V'].max(0)) / 2 + np.array(S['y']) - (o['V'].min(0) + o['V'].max(0)) / 2; sm = dict(sm, seed_fit=S['name'])
    c = (o['V'].min(0) + o['V'].max(0)) / 2; eyes = [c + e for e in EYES_REL]
    m0 = O.measure(z0, Ob, cuff_ref=cref, eyes=eyes)
    z, y, cost = O.grip(z0, Ob, cuff_ref=cref, W=W, move=move, nfev=nfev, y_init=yi, fingers=os.environ.get('FINGERS', 'IMRPT'), palm=os.environ.get('PALM', '1') == '1')	# FINGERS=IT PALM=0: a pinch (a small round held out where it shows)
    m = O.measure(z, Ob, y, cuff_ref=cref, eyes=eyes)
    # Ermac's own hold, same measures (his mesh in place of the hand)
    ve = O.visible(E, Fe, o['V'], o['F'], eyes); de = Ob.ex.depth(E)
    J = dict(job=job, name=o['name'], ermac=o['ermac'], z=z.tolist(), y=y.tolist(), cost=cost, seed=dict(z=z0.tolist(), **sm), seed_m=m0, m=m, rows=o['rows'],
             ermac_m=dict(visible=[round(v, 2) for v in ve], pen_cm=round(float(de.max()), 2)), W=W, move=move, secs=round(time.time() - t0))
    json.dump(J, open(os.path.join(out, o['name'] + '.json'), 'w'), indent=1)
    obj = look.m(o['V'], o['F'], (150, 150, 160)); X = O.hand(O.zp(z)); objm = look.m(o['V'] + y, o['F'], (150, 150, 160))
    look.views([('Ermac %s %d + object' % o['ermac'], [obj, dict(look.m(E, Fe, (60, 45, 40)), centre=False)]),
                ('FBX fit (pen %.2f, touch %d, visible %s; Ermac visible %s)' % (m['pen_cm'], m['touch'], m['visible'], J['ermac_m']['visible']), [objm, dict(look.m(X, O.H.F, (235, 150, 90)), centre=False)])],
               os.path.join(out, o['name'] + '.png'), '%s: %s' % (o['name'], json.dumps(m)), box=16)
    print(o['name'], 'seed', json.dumps(m0), '\n  fit', json.dumps(m), 'ermac', J['ermac_m'], '%ds' % J['secs'], flush=True)
    return J
if __name__ == '__main__':
    out = os.path.abspath(sys.argv[1]); os.makedirs(out, exist_ok=True)
    W = json.loads(os.environ['W']) if os.environ.get('W') else None
    for j in sys.argv[2:]: run(j, out, W, move=bool(os.environ.get('MOVE')))
