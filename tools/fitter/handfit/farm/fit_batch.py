"""Fit farm: run FBX gun-hand fits (heavies/fit_hv.py's method, unchanged) in parallel, one process per job.

usage:
  python fit_batch.py [--workers N] [--batch NAME] [--detach] JOB [JOB ...]
  python fit_batch.py --jobs jobs.json ...
JOB tokens (fit_hv.py's own syntax, plus two farm options):
  Gun                      full fit: stage 2 from 1.92's hold (or fit_hv.START), curl (index solved too if the pad is >1 cm off), bake
  =Gun                     reuse a saved stage-2 seat (seat= or <results>/<Gun>/st2_<Gun>.npy)
  ==Gun                    bake only, from the saved curl3_<Gun>.json
  Gun:seat=<rel.npy>       start from that saved seat (path relative to farm HOME, e.g. lane_b_hvrun/st2_RailGun.npy) = '=Gun'
  Gun:from=<Src>:<rel.npy> stage 2 starts from <Src>'s SOLVED placement (fit_hv.START rule: moved by the trigger-face difference)
  Gun:idx                  curl with the index solved to the trigger straight away (curl4's '+' mode) instead of auto
  options join with ':' e.g.  RailGun:seat=lane_b_hvrun/st2_RailGun.npy:idx
Each job writes into <results>/<Gun>/: st2_<Gun>.npy, curl3_<Gun>.json, fbx_hv_<Gun>_R.md3, <Gun>_hv.json (port_gun.py's fit json),
log.txt, job.json (timing, status). The batch writes <results>/summary_<batch>.json (per-job minutes) and status_<batch>.json while running.
--detach: start the batch in a detached background process and return at once (the bridge runs one request at a time)."""
import os, sys, json, time, shutil, argparse, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import farmpaths

def parse_job(tok):
    if isinstance(tok, dict): return tok
    head, *opts = tok.split(':')
    j = dict(token=tok, gun=head.lstrip('='), skip_stage=head.startswith('='), bake_only=head.startswith('=='), idx='auto')
    i = 0
    while i < len(opts):
        o = opts[i]
        if o.startswith('seat='): j['seat'] = o[5:]; j['skip_stage'] = True
        elif o.startswith('from='): j['from'] = [o[5:], opts[i + 1]]; i += 1
        elif o == 'idx': j['idx'] = 'force'
        elif o.startswith('as='): j['out'] = o[3:]
        elif o == 'dense': j['dense'] = True; j['idx'] = 'force'
        elif o == 'wrap': j['dense'] = True; j['wrap'] = True
        elif o.startswith('thr='): j['thr'] = float(o[4:])
        else: raise SystemExit('unknown job option %r in %r' % (o, tok))
        i += 1
    return j

def _fit(H, g, skip_stage, bake_only, idx, dense=False, thr=None, wrap=False, seeded=False):
    """fit_hv.fit(), verbatim except: idx='force' runs curl(idx=True) at once (curl4 '+' mode) instead of after a failed M/R/P pass;
    dense (round 4, dense_hv.py): re-seat from the given seat and curl with every vertex tested for penetration (hinge thr)."""
    import numpy as np
    if dense:
        import dense_hv
        if thr is not None: dense_hv.THR[0] = thr
        if seeded or not wrap:
            a = np.load(H.RUN + '/st2_%s.npy' % g); np.save(H.RUN + '/st2_seed_%s.npy' % g, a); R0, t0 = a[:9].reshape(3, 3), a[9:12]
        else:	# no seat given: 1.92's own hold on this gun (fit_hv.stage's start)
            R0, t0 = H.m192.T_of(H.HV[g]['src192'])[:2]
        o1, R, t, d = dense_hv.stage(H, g, R0, t0, nfev=60, wrap=wrap); np.save(H.RUN + '/st2_%s.npy' % g, np.r_[R.ravel(), t, d])
        print(g, 'stage2 dense', json.dumps(o1, default=float), flush=True)
        o2 = dense_hv.curl(H, g, idx=True, nfev=40, wrap=wrap); bake_only = True; idx = 'done'
    elif skip_stage: o1 = dict(reused=H.RUN + '/st2_%s.npy' % g)
    else: o1 = H.stage(g); print(g, 'stage2', json.dumps(o1, default=float), flush=True)
    if dense: pass
    elif bake_only:
        J = json.load(open(H.RUN + '/curl3_%s.json' % g)); o2 = {k: v for k, v in J.items() if k not in ('Xt', 'Xs', 'R', 't')}
    elif idx == 'force':
        o2 = H.curl(g, idx=True)
    else:
        o2 = H.curl(g)
        if o2['trigger']['padI_trig'] > 1.0:
            print(g, 'curl (M/R/P only)', json.dumps(o2['trigger'], default=float), '-> index solved too', flush=True); o2 = H.curl(g, idx=True)
    print(g, 'curl', json.dumps({k: ({a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()} if isinstance(v, dict) else v) for k, v in o2.items()}, default=float), flush=True)
    CROP[0] = False   # the bake places the support hand forward on the gun: it measures against the whole mesh
    o3, sup, md3 = H.bake_it(g); print(g, 'bake', json.dumps(o3, default=float), flush=True)
    os.makedirs(H.FITS, exist_ok=True); name = 'fbx_hv_%s_R.md3' % g; shutil.copyfile(md3, os.path.join(H.FITS, name))
    F = dict(shift=o2['shift'], hand=dict(md3=name, md3_name=name, sprite=None, label=None, squeeze='false', squeeze_note='fullbright (firing) frames', support=sup,
             support_note="the FBX palm-under (RQFS B) under the gun at its SupportPoint, moved with the gun (fit_hv.py)"),
             metrics=dict(stage2=o1, curl={k: v for k, v in o2.items() if k != 'shift'}, bake=o3))
    json.dump(F, open(os.path.join(H.FITS, '%s_hv.json' % g), 'w'), indent=1, default=float); return F

CROP = [True]
def add_guns(H):
    """guns.json (next to this file): guns fit_hv.HV does not list, in HV's own form (measured: mesh surfaces from surf_hv.py at the
    1.99 ready frame, ready frame / scale / offset from MODELDEF.bd.txt + BD22's Ready state, row from handtable.zs Index()).
    'crop' (fit_sg.py's rule): stage 2 and the curl collide only with faces whose every vertex is at F < crop cm; the bake uses the whole gun."""
    p = os.path.join(HERE, 'guns.json')
    if not os.path.exists(p): return
    G = {k: v for k, v in json.load(open(p, encoding='utf-8')).items() if not k.startswith('_')}
    for k, v in G.items():
        it = dict(v['it']); it['path'] = H.M(it['path'])
        H.HV[k] = dict(cls=v.get('cls', k), row=v['row'], it=it, trig_surf=v['trig_surf'], bore_surf=v['bore_surf'], src192=v.get('src192', k))
        H.revlm.GUNS[k] = dict(it=it, grip_surf=v.get('grip_surf', [v['bore_surf']]), trig_surf=v['trig_surf'], fmax=None, bore_surf=v['bore_surf'])
    if any('crop' in v['it'] for v in G.values()):
        import numpy as np
        _merged = H.scene.merged
        def merged_crop(it, *a, **k):
            it2 = {kk: vv for kk, vv in it.items() if kk != 'crop'}; F, V = _merged(it2, *a, **k)
            if 'crop' not in it or not CROP[0]: return F, V
            keep = (V[np.asarray(F)][:, :, 0] < it['crop']).all(1); return np.asarray(F)[keep], V
        H.scene.merged = merged_crop

def run_job(job):
    g = job['gun']; out = os.path.join(farmpaths.RESULTS, job.get('out', g)); os.makedirs(os.path.join(out, 'bake'), exist_ok=True)
    t0 = time.time(); rec = dict(job=job, pid=os.getpid(), start=time.strftime('%H:%M:%S'))
    log = open(os.path.join(out, 'log.txt'), 'w', buffering=1, encoding='utf-8'); so, se = sys.stdout, sys.stderr; sys.stdout = sys.stderr = log
    try:
        sys.path.insert(0, farmpaths.P('lane_b_hv/tools/handfit/heavies'))
        import fit_hv as H
        H.RUN = out.replace('\\', '/'); H.FITS = out; add_guns(H)
        if job.get('seat'):
            shutil.copyfile(farmpaths.P(job['seat']), os.path.join(out, 'st2_%s.npy' % g))
        if job.get('from'):
            H.START[g] = (job['from'][0], farmpaths.P(job['from'][1]))
        F = _fit(H, g, job.get('skip_stage', False), job.get('bake_only', False), job.get('idx', 'auto'), job.get('dense', False), job.get('thr'), job.get('wrap', False), bool(job.get('seat')))
        rec.update(status='ok', metrics=F['metrics'])
    except BaseException as e:
        rec.update(status='error', error=repr(e), trace=traceback.format_exc()); print(traceback.format_exc(), flush=True)
    finally:
        sys.stdout, sys.stderr = so, se; log.close()
    rec.update(minutes=round((time.time() - t0) / 60.0, 2), end=time.strftime('%H:%M:%S'))
    json.dump(rec, open(os.path.join(out, 'job.json'), 'w'), indent=1, default=float)
    return rec

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('jobs', nargs='*'); ap.add_argument('--jobs', dest='jobfile')
    ap.add_argument('--workers', type=int, default=farmpaths.WORKERS); ap.add_argument('--batch', default=time.strftime('b%H%M%S'))
    ap.add_argument('--detach', action='store_true'); ap.add_argument('--threads', type=int, default=1)
    a = ap.parse_args()
    jobs = [parse_job(t) for t in a.jobs] + ([parse_job(t) for t in json.load(open(a.jobfile))] if a.jobfile else [])
    if not jobs: ap.error('no jobs')
    os.makedirs(farmpaths.RESULTS, exist_ok=True)
    if a.detach:
        import subprocess
        argv = [sys.executable, os.path.abspath(__file__), '--workers', str(a.workers), '--batch', a.batch, '--threads', str(a.threads)] + [j['token'] for j in jobs]
        flags = 0x00000008 | 0x00000200 if os.name == 'nt' else 0   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        lf = open(os.path.join(farmpaths.RESULTS, 'batch_%s.log' % a.batch), 'w')
        p = subprocess.Popen(argv, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=HERE, creationflags=flags, close_fds=True,
                             start_new_session=(os.name != 'nt'))
        print('detached batch', a.batch, 'pid', p.pid, 'jobs', [j['token'] for j in jobs]); return
    for v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ[v] = str(a.threads)   # one core per job
    os.environ['PYTHONUTF8'] = '1'   # workers start in UTF-8 mode: the tools open() text files without an encoding (cp1252 on Windows)
    import multiprocessing as mp
    T0 = time.time(); st_path = os.path.join(farmpaths.RESULTS, 'status_%s.json' % a.batch); done = []
    def status(final=False):
        json.dump(dict(batch=a.batch, workers=a.workers, jobs=[j['token'] for j in jobs], done=done, final=final,
                       wall_minutes=round((time.time() - T0) / 60.0, 2), cpu_count=os.cpu_count()), open(st_path, 'w'), indent=1, default=float)
    status(); print('batch', a.batch, 'jobs', len(jobs), 'workers', min(a.workers, len(jobs)), flush=True)
    with mp.get_context('spawn').Pool(min(a.workers, len(jobs)), maxtasksperchild=1) as pool:
        for rec in pool.imap_unordered(run_job, jobs):
            done.append({k: rec.get(k) for k in ('job', 'status', 'minutes', 'start', 'end', 'error')}); status()
            print(rec['job']['token'], rec['status'], rec['minutes'], 'min', flush=True)
    status(final=True)
    summ = dict(batch=a.batch, wall_minutes=round((time.time() - T0) / 60.0, 2), workers=a.workers, jobs=done)
    json.dump(summ, open(os.path.join(farmpaths.RESULTS, 'summary_%s.json' % a.batch), 'w'), indent=1, default=float)
    print('summary', json.dumps(summ, default=float), flush=True)
if __name__ == '__main__': main()
