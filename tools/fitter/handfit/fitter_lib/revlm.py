"""BD 2.0 b2: grip landmarks of the revolver meshes, measured exactly as lane_c gunlm.pistol measures the pistol
(silhouettes of the grip in the side view, backstrap notch = web target, trigger lower-third front face = pad target),
in the same frame (scene/hudrender chain, controller F/L/U cm, gun at its 1.99 MODELDEF placement).
CHOICES are named: which surface is the trigger and which box holds the grip, per mesh (read from the surface boxes)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, numpy as np
import os as _os; _LIB = _os.path.dirname(_os.path.abspath(__file__)); _HOME = _os.environ.get('RS_FITTER_HOME', _DP.WORK + '/fitter_home/').rstrip('/')	# fitter_lib: sibling modules here; data under RS_FITTER_HOME
sys.path.insert(0, _DP.CORE + '/hands_tool')
import scene, gunfield, gunlm
SRC = _HOME + '/lane_b_b2/src'
GUNS = {
 # Revolver.md3 (Shotvolver), MODELDEF.bd.txt Revolver: Scale -1 1 1, Offset 0 0 0, ZOffset -5, ready REVO A = frame 0
 'Revolver': dict(it=dict(path=SRC + '/models/bd/Revolver/Revolver.md3', frame=0, scale=[-1.0, 1.0, 1.0], off=[0.0, 0.0, -5.0]),
                  grip_surf=[0], trig_surf=3, fmax=2.5, bore_surf=1),
 # rev.md3 (Moonlight), MODELDEF.rsqmoon BrutalRevolver: Scale 1.35, Offset 0.0262 0.9224 0, ZOffset 0.5878, ready RVMA A = frame 0
 # BrutalSMG.md3 (Kriss Vector), MODELDEF.bd.txt BrutalSMG: Scale -1 1 1, Offset 0 0 0, ZOffset -5, ready = frame 3 (1.92 rows / lane_c rows192.json)
 'BrutalSMG': dict(it=dict(path=SRC + '/models/bd/BrutalSMG/BrutalSMG.md3', frame=3, scale=[-1.0, 1.0, 1.0], off=[0.0, 0.0, -5.0]),
                  grip_surf=[1], trig_surf=2, fmax=None, bore_surf=1),
 'BrutalRevolver': dict(it=dict(path=SRC + '/models/bd/Moonlight/rev.md3', frame=0, scale=[1.35, 1.35, 1.35], off=[0.0262, 0.9224, 0.5878]),
                  grip_surf=[0], trig_surf=0, trig_box=dict(f=(-0.6, 2.6), l=(-0.45, 0.45), u=(-6.0, -2.9)), fmax=None, bore_surf=3),
}
def samples(it, step=0.1):
    P = []; I = []
    for k, (T, V) in enumerate(scene.item_verts(it)):
        S, _, _ = gunfield.sample_surface(V, T, step); P.append(S); I.append(np.full(len(S), k))
    return np.concatenate(P), np.concatenate(I)
def measure(g):
    c = GUNS[g]; S, I = samples(c['it']); out = {}
    T = S[I == c['trig_surf']]
    if 'trig_box' in c: b = c['trig_box']; T = T[gunlm.box(T, **b)]
    tf_ = T[:, 0].min() if c['fmax'] is None else c['fmax']
    G = np.isin(I, c['grip_surf'])
    # grip: below the trigger's top, behind the trigger (the grip panels / frame behind the guard)
    utop = T[:, 2].max()
    def sil(lo, hi, fn):
        o = []
        for u in np.arange(lo, hi, 0.25):
            q = S[(np.abs(S[:, 2] - u) < 0.13) & (np.abs(S[:, 1]) < 1.0) & (S[:, 0] < tf_ - 0.3) & G]
            if len(q): o.append(q[fn(q[:, 0])])
        return np.array(o)
    umin = S[G][:, 2].min()
    rear = sil(umin + 0.3, utop, np.argmin); front = sil(umin + 0.3, T[:, 2].min(), np.argmax)
    def line(P, lo, hi):
        m = (P[:, 2] > lo) & (P[:, 2] < hi); cc, a, _ = gunlm.pca_axis(P[m]); return cc, (a if a[2] > 0 else -a)
    h = T[:, 2].min()
    cr, ar = line(rear, umin + 0.8, h); cf, af = line(front, umin + 0.8, h); a = ar + af; a /= np.linalg.norm(a)
    out['grip_axis'] = a; out['grip_c'] = 0.5 * (cr + cf); out['grip_axis_rear'] = ar
    out['grip_d'] = float(np.linalg.norm(np.cross(cf - cr, a)))
    up = rear[rear[:, 2] > 0.5 * (umin + h)]	# CHOICE (revolvers): the spur is the rear-most point of the UPPER half (their butt flares back below)
    spur_u = up[np.argmin(up[:, 0]), 2]
    band = rear[(rear[:, 2] < spur_u - 0.2) & (rear[:, 2] > spur_u - 2.5)]
    out['backstrap_top'] = band[np.argmax(band[:, 0])]
    u0, u1 = T[:, 2].min(), T[:, 2].max()
    band = T[np.abs(T[:, 2] - (u0 + 0.35 * (u1 - u0))) < 0.3]
    out['trigger_face'] = band[np.argmax(band[:, 0])]
    B = S[I == c['bore_surf']]; _, ba, _ = gunlm.pca_axis(B); ba = ba if ba[0] > 0 else -ba
    out['bore_axis'] = ba; out['muzzle'] = S[S[:, 0] > S[:, 0].max() - 0.4].mean(0)
    out['rake_deg'] = float(np.degrees(np.arctan2(-ar[0], ar[2])))
    out['trigger_from_backstrap_cm'] = float(np.linalg.norm(out['trigger_face'] - out['backstrap_top']))
    return out, S, I
def pistol():
    m = json.load(open(_DP.CORE + '/gun_landmarks.json'))['BrutalPistol']
    m = {k: (np.array(v) if isinstance(v, list) else v) for k, v in m.items()}
    m['rake_deg'] = float(np.degrees(np.arctan2(-m['grip_axis_rear'][0], m['grip_axis_rear'][2])))
    m['trigger_from_backstrap_cm'] = float(np.linalg.norm(m['trigger_face'] - m['backstrap_top']))
    return m
if __name__ == '__main__':
    P = pistol(); print('BrutalPistol rake %.1f  trig-backstrap %.2f  grip_d %.2f' % (P['rake_deg'], P['trigger_from_backstrap_cm'], P['grip_d']))
    for g in GUNS:
        o, S, I = measure(g)
        print(g, 'rake %.1f  trig-backstrap %.2f  grip_d %.2f' % (o['rake_deg'], o['trigger_from_backstrap_cm'], o['grip_d']),
              'bs', o['backstrap_top'].round(2), 'tf', o['trigger_face'].round(2), 'bore', o['bore_axis'].round(3), 'muzzle', o['muzzle'].round(2))
