"""Melee hands lane: FBX gun-hand fits for BD22's melee weapons on the fit farm (fit_hv.py's method, unchanged).
Wrist pinned to the controller, the WEAPON moves to the hand (shift d), every dependent point moves with it at port time.
Lives next to the farm's farmpaths.py (work/fitfarm/); reads melee.json next to it. Does not touch fit_batch.py / guns.json.

usage: python fit_melee.py [--workers N] [--batch NAME] [--detach] JOB [JOB ...]
JOB = <Class>:hold=<key>[:idx][:as=<outdir>]
  hold=<key>  the Ermac hold the fit starts from (melee.json holds: 192 / 199): m192.T_of carries it onto the approved FBX pistol hand
  idx         curl with the index solved to its target straight away (a haft/hilt/grenade: every finger wraps) instead of auto
  as=<dir>    results/<dir> (default melee_<Class>_h<key>)
What differs from fit_hv.fit (nothing in the solver):
  - the Ermac hold comes from melee.json (m192.ROWS / m192.hand patched for this class only);
  - trigger_face(<Class>) returns melee.json's measured tf and bore (patched in fit3, rigid3, st2_b4, fit_hv for this class only);
  - the bake writes the gun hand only (trigger, squeeze, pistol check); no palm-under support (wrong for a top handle / a hilt):
    the supports are their own step (support_melee.py).
Per job: st2_<C>.npy, curl3_<C>.json, fbx_hv_<C>_R.md3, <C>_hv.json, log.txt, job.json (same keys as fit_batch)."""
import os, sys, json, time, shutil, argparse, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import farmpaths

def parse_job(tok):
    head, *opts = tok.split(':')
    j = dict(token=tok, gun=head, idx='auto', hold=None)
    for o in opts:
        if o.startswith('hold='): j['hold'] = o[5:]
        elif o == 'idx': j['idx'] = 'force'
        elif o.startswith('as='): j['out'] = o[3:]
        else: raise SystemExit('unknown job option %r in %r' % (o, tok))
    if not j['hold']: raise SystemExit('hold= is required: %r' % tok)
    j.setdefault('out', 'melee_%s_h%s%s' % (head, j['hold'], 'i' if j['idx'] == 'force' else ''))
    return j

def setup(H, g, hold):
    import numpy as np
    C = json.load(open(os.path.join(HERE, 'melee.json'), encoding='utf-8'))[g]; h = dict(C['holds'][hold])
    ax = h.pop('axis', None)
    if ax: h = dict(C['holds'][ax['from']], **{k: v for k, v in h.items() if k != 'axis'}); h['axis'] = ax
    it = dict(C['it']); it['path'] = H.M(it['path'])
    H.HV[g] = dict(cls=g, row=C['row'], it=it, trig_surf=C['trig_surf'], bore_surf=C['bore_surf'], src192=g)
    H.revlm.GUNS[g] = dict(it=it, grip_surf=[C['trig_surf']], trig_surf=C['trig_surf'], fmax=None, bore_surf=C['bore_surf'])
    m192 = H.m192; m192.ROWS[g] = dict(gframe=h['frame'], ghook=h['hook'], grot=h['rot'])
    hand0 = m192.hand; hpath = farmpaths.P(h['path'])
    def hand(gg, frame=None):
        if gg != g: return hand0(gg, frame)
        r = m192.ROWS[g]
        _, V = m192.scene.merged(dict(path=hpath, frame=r['gframe'] if frame is None else frame, hook=r['ghook'], rot=r['grot'], **m192.scene.ERMAC_PL))
        return V, m192.ermaclm.get()
    if h.get('mirror'):		# a support hold (Ermac L hand) solved as its mirror image: the R hand on the mirrored weapon
        hand1 = hand
        def hand(gg, frame=None):
            V, L = hand1(gg, frame); return (V * np.array([1.0, -1.0, 1.0]) if gg == g else V), L
    m192.hand = hand
    if it.get('mirror') or it.get('crop_box'):
        # mirror: Scale x sign flipped = L -> -L exactly (checked: max 0.0000 cm); re-wind the faces so normals stay outward.
        # crop_box {f,l,u: [lo, hi]} (fit_batch 'crop' rule, as a box): stage 2 and the curl collide only with faces whose every
        # vertex is inside it (the region the hand can reach); the bake does not use the mesh; support_melee.py measures on the whole mesh.
        sc = H.scene
        if not getattr(sc, '_melee_patch', False):
            merged0 = sc.merged
            def merged(it_, *a, **k):
                it2 = {kk: vv for kk, vv in it_.items() if kk not in ('mirror', 'crop_box')}; F, V = merged0(it2, *a, **k); F = np.asarray(F)
                if it_.get('mirror'): F = F[:, ::-1].copy()
                b = it_.get('crop_box')
                if b:
                    P = V[F]; keep = np.ones(len(F), bool)
                    for i, kk in enumerate('flu'):
                        if kk in b: keep &= ((P[:, :, i] >= b[kk][0]) & (P[:, :, i] <= b[kk][1])).all(1)
                    F = F[keep]
                return F, V
            sc.merged = merged; sc._melee_patch = True
    bore = np.array(C['bore'], float); bore /= np.linalg.norm(bore)
    if h.get('axis'):
        # 'axis' start: the approved pistol hold with the pistol's grip axis laid on the weapon's grip axis. The Ermac hold (ax['from'])
        # placed as m192 does, then turned by the MINIMAL rotation taking its carried pistol grip axis onto the weapon axis (so the
        # roll about the axis is the hold's), and slid so the pistol grip centre sits ON the weapon axis at the hold's axial position.
        # Pistol grip: lane_c gun_landmarks.json BrutalPistol grip_axis / grip_c (measured, the approved hand's own frame O).
        ax = h['axis']; GL = json.load(open(farmpaths.P('lane_c/gun_landmarks.json')))['BrutalPistol']
        ga = np.array(GL['grip_axis'], float); ga /= np.linalg.norm(ga); gc = np.array(GL['grip_c'], float)
        wa = np.array(ax['w_axis'], float); wa /= np.linalg.norm(wa); wp = np.array(ax['w_point'], float)
        T0 = m192.T_of
        Re, te, res_, P_, G_ = T0(g)
        ge = Re @ ga
        if wa @ ge < 0: wa = -wa		# the axis direction nearest the hold's own grip axis (an axis has no sign of its own)
        v = np.cross(ge, wa); s_, c_ = np.linalg.norm(v), float(ge @ wa)
        K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        Ra = np.eye(3) + K + K @ K * ((1 - c_) / (s_ ** 2)) if s_ > 1e-9 else np.eye(3)
        R0 = Ra @ Re; gce = Re @ gc + te; p = wp + wa * float((gce - wp) @ wa) + wa * float(ax.get('slide', 0.0)); t0 = p - R0 @ gc
        m192.T_of = lambda gg, _T0=T0: (R0, t0, res_, P_, G_) if gg == g else _T0(gg)
        ctx = H.revindex.setup()[0]; Xf = H.revindex.setup()[3]; X0 = Xf @ R0.T + t0
        S, I = H.revlm.samples(H.revlm.GUNS[g]['it']); T = S[I == C['trig_surf']]
        pad = X0[H.evaluate.reg(ctx.L, 'pad_I')].mean(0); tf = np.array(h['tf'], float) if ax.get('keep_tf') else T[np.argmin(np.linalg.norm(T - pad, axis=1))]
        print(g, 'axis start', json.dumps(dict(turn_from_hold_deg=float(np.degrees(np.arccos(np.clip(c_, -1, 1)))), tf=tf.round(3).tolist(), pad_to_tf=float(np.linalg.norm(tf - pad)))), flush=True)
    else: tf = np.array(h['tf'], float)
    import fit3, rigid3
    tf0 = fit3.trigger_face
    def trigger_face(gg):
        return (tf.copy(), bore.copy()) if gg == g else tf0(gg)
    for mod in (fit3, rigid3, H.st2_b4, H): mod.trigger_face = trigger_face

def bake_gun(H, g):		# fit_hv.bake_it's gun-hand half, verbatim
    import numpy as np, bake
    ctx, x, to_g, Xf, delta = H.revindex.setup(); Rg, tg = H.solve.gun_T(ctx, x); to_c = lambda X: H.solve.gmove(ctx, Rg, tg, X)
    J = json.load(open(H.RUN + '/curl3_%s.json' % g)); B1 = os.path.join(H.SRC, 'models/rsq/fbx/')
    ent = [dict(name=g[:10] + '_trg', side='R', X=to_c(np.array(J['Xt']))), dict(name=g[:10] + '_sqz', side='R', X=to_c(np.array(J['Xs']))), dict(name='PISTOL_chk', side='R', X=to_c(Xf))]
    for e in ent: e['cuff_ref'] = e['X'][ctx.cuff]
    rows, paths, _ = bake.bake(ent, H.RUN + '/bake/fbx_hv_%s.md3' % g)
    chk = float(np.abs(H.scene.md3_full(paths['R'])[0]['xyz'][2] - H.scene.md3_full(B1 + 'fbx_b1_R.md3')[0]['xyz'][0]).max())
    return dict(rows=[str(r_) for r_ in rows], pistol_rebake_max=chk), paths['R']

def fit(H, g, idx):
    o1 = H.stage(g); print(g, 'stage2', json.dumps(o1, default=float), flush=True)
    if idx == 'force': o2 = H.curl(g, idx=True)
    else:
        o2 = H.curl(g)
        if o2['trigger']['padI_trig'] > 1.0:
            print(g, 'curl (M/R/P only)', json.dumps(o2['trigger'], default=float), '-> index solved too', flush=True); o2 = H.curl(g, idx=True)
    print(g, 'curl', json.dumps({k: ({a: round(b, 2) for a, b in v.items()} if isinstance(v, dict) else v) for k, v in o2.items()}, default=float), flush=True)
    o3, md3 = bake_gun(H, g); print(g, 'bake', json.dumps(o3, default=float), flush=True)
    name = 'fbx_hv_%s_R.md3' % g; shutil.copyfile(md3, os.path.join(H.FITS, name))
    F = dict(shift=o2['shift'], hand=dict(md3=name, md3_name=name, sprite=None, label=None, squeeze='false', squeeze_note='melee: frame 1 unused except Chain_saw (its trigger)', support=None,
             support_note='melee: support is its own step (support_melee.py)'), metrics=dict(stage2=o1, curl={k: v for k, v in o2.items() if k != 'shift'}, bake=o3))
    json.dump(F, open(os.path.join(H.FITS, '%s_hv.json' % g), 'w'), indent=1, default=float); return F

def run_job(job):
    g = job['gun']; out = os.path.join(farmpaths.RESULTS, job['out']); os.makedirs(os.path.join(out, 'bake'), exist_ok=True)
    t0 = time.time(); rec = dict(job=job, pid=os.getpid(), start=time.strftime('%H:%M:%S'))
    log = open(os.path.join(out, 'log.txt'), 'w', buffering=1, encoding='utf-8'); so, se = sys.stdout, sys.stderr; sys.stdout = sys.stderr = log
    try:
        sys.path.insert(0, farmpaths.P('lane_b_hv/tools/handfit/heavies'))
        import fit_hv as H
        H.RUN = out.replace('\\', '/'); H.FITS = out; setup(H, g, job['hold'])
        F = fit(H, g, job['idx']); rec.update(status='ok', metrics=F['metrics'])
    except BaseException as e:
        rec.update(status='error', error=repr(e), trace=traceback.format_exc()); print(traceback.format_exc(), flush=True)
    finally:
        sys.stdout, sys.stderr = so, se; log.close()
    rec.update(minutes=round((time.time() - t0) / 60.0, 2), end=time.strftime('%H:%M:%S'))
    json.dump(rec, open(os.path.join(out, 'job.json'), 'w'), indent=1, default=float)
    return rec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('jobs', nargs='+')
    ap.add_argument('--workers', type=int, default=7); ap.add_argument('--batch', default=time.strftime('melee%H%M%S'))
    ap.add_argument('--detach', action='store_true'); ap.add_argument('--threads', type=int, default=1)
    a = ap.parse_args(); jobs = [parse_job(t) for t in a.jobs]; os.makedirs(farmpaths.RESULTS, exist_ok=True)
    if a.detach:
        import subprocess
        argv = [sys.executable, os.path.abspath(__file__), '--workers', str(a.workers), '--batch', a.batch, '--threads', str(a.threads)] + [j['token'] for j in jobs]
        flags = 0x00000008 | 0x00000200 if os.name == 'nt' else 0
        lf = open(os.path.join(farmpaths.RESULTS, 'batch_%s.log' % a.batch), 'w')
        p = subprocess.Popen(argv, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=HERE, creationflags=flags, close_fds=True, start_new_session=(os.name != 'nt'))
        print('detached batch', a.batch, 'pid', p.pid, 'jobs', [j['token'] for j in jobs]); return
    for v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ[v] = str(a.threads)
    os.environ['PYTHONUTF8'] = '1'
    import multiprocessing as mp
    T0 = time.time(); st_path = os.path.join(farmpaths.RESULTS, 'status_%s.json' % a.batch); done = []
    def status(final=False):
        json.dump(dict(batch=a.batch, workers=a.workers, jobs=[j['token'] for j in jobs], done=done, final=final, wall_minutes=round((time.time() - T0) / 60.0, 2)), open(st_path, 'w'), indent=1, default=float)
    status()
    with mp.get_context('spawn').Pool(min(a.workers, len(jobs)), maxtasksperchild=1) as pool:
        for rec in pool.imap_unordered(run_job, jobs):
            done.append({k: rec.get(k) for k in ('job', 'status', 'minutes', 'start', 'end', 'error')}); status()
    status(final=True)
if __name__ == '__main__': main()
