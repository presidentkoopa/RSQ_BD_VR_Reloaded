"""port_sg.py <Class> <fit.json> [--src DIR] [--tag TEXT] [--dry]

Shotguns lane: port_gun.py (tools/handfit/port, the one method: the drawn wrist stays pinned, the GUN moves to the fitted
hand and every table hanging off it moves with it) run for Shot_Gun / AssaultShotgun / SSG. It adds those guns to
port_gun's registry and the two tables port_gun does not know yet:
  - the pump (rsr_pump_guns.zs case 1, Shot_Gun): Grab, Port (points), Pull, Push (directions), PumpHook, SupportHook
    (hook form of the turned Pull), PortHook (hook form of the turned shell offset), Offset; and the side port's
    literals in rsr_pump.zs (PortK / PushK / the casing-out point / the bore the shell's angle is read against)
  - the break-open rows in their case form (rsb_guns.zs, SSG = case 1): Hinge (point), Axis, PushRef (directions),
    Offset; the hand-frame rows are kept (as port_gun.rsb)
Every text edit asserts the exact text it replaces."""
import os, re, sys, json, argparse, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'port'))
import port_gun as P

P.GUNS.update({
 # Shotgun.md3 ready frame 4 (MODELDEF.bd.txt SHTN A). Off-hand shell (RSQ_Hands) and the dropped shell (RSP_DroppedShell) are not gun blocks.
 'Shot_Gun': dict(md3='models/bd/ShotGun/Shotgun.md3', names=['Shotgun.md3'], ready=4, scale=[-1, 1, 1], off=[0, 0, -5], row=21, pump=1,
    casing='Shot_Gun', blocks={('MODELDEF.bd.txt', 'Shot_Gun'): 1, ('MODELDEF.purist', 'PuristShot_Gun'): 2, ('MODELDEF.rsqoff', 'RSQ_Off_Shot_Gun'): 2,
    ('MODELDEF.rsrpump', 'Shot_Gun'): 1, ('MODELDEF.rsrpump', 'RSR_GunParts'): 3}, skip=['RQUW'], skipcls=['RSQ_Hands', 'RSP_DroppedShell'],
    bdblock=('MODELDEF.bd.txt', 'Shot_Gun'), dual=[('MODELDEF.rsqdual', 'Shot_Gun'), ('MODELDEF.rsqoff', 'RSQ_Off_Shot_Gun'), ('MODELDEF.purist', 'PuristShot_Gun')]),
 # AssaultShotgun.md3 ready frame 4 (rows192); RSR magazine case 5
 'AssaultShotgun': dict(md3='models/bd/AssaultShotgun/AssaultShotgun.md3', names=['AssaultShotgun.md3'], ready=4, scale=[-1, 1, 1], off=[0, 0, -5], row=1, rsr=5,
    casing='AssaultShotgun', blocks=None, skip=['RQAW'], skipcls=['RSQ_Hands', 'RSR_DroppedMag'], bdblock=('MODELDEF.bd.txt', 'AssaultShotgun'),
    dual=[('MODELDEF.rsqdual', 'AssaultShotgun'), ('MODELDEF.rsqoff', 'RSQ_Off_AssaultShotgun'), ('MODELDEF.purist', 'PuristAssaultShotgun')]),
 # SSG.md3 ready frame 1 (rows192); RSB break-open case 1
 'SSG': dict(md3='models/bd/SSG/SSG.md3', names=['SSG.md3'], ready=1, scale=[-1, 1, 1], off=[0, 0, -5], row=20, rsbc=[1],
    casing='SSG', blocks=None, skip=['RBSW'], skipcls=['RSQ_Hands', 'RSB_Round'], bdblock=('MODELDEF.bd.txt', 'SSG'),
    dual=[('MODELDEF.rsqdual', 'SSG'), ('MODELDEF.rsqoff', 'RSQ_Off_SSG'), ('MODELDEF.purist', 'PuristSSG')]),
})

def caseval(tx, fn, c):
    i0 = tx.index(' %s(int i)' % fn); i1 = tx.index('\n\t}', i0); seg = tx[i0:i1]
    m = re.search(r'\t\tcase %d:\treturn \(([^)]*)\);' % c, seg); assert m, (fn, c)
    return np.array([float(s) for s in m.group(1).split(',')]), '(%s)' % m.group(1)
hookof = lambda d: np.array([d[1], d[2], -d[0]])		# RSP.HookOf with Scale (-1, 1, 1)
unhook = lambda h: np.array([-h[2], h[0], h[1]])

def pump(G, p, R, t, tag):
    c = G['pump']; tx = P.rd('zscript/rsr/rsr_pump_guns.zs'); pt = lambda q: R @ q + t
    for fn, kind in (('Grab', 'p'), ('Port', 'p'), ('Pull', 'd'), ('Push', 'd'), ('PumpHook', 'h'), ('SupportHook', 'h'), ('PortHook', 'h'), ('Offset', 'o')):
        v, s = caseval(tx, fn, c)
        nv = pt(v) if kind == 'p' else R @ v if kind == 'd' else hookof(R @ unhook(v)) if kind == 'h' else np.array(p[:3])
        if kind == 'o': assert np.abs(v - np.array(G['off'])).max() < 1e-3, ('pump Offset not base', v)
        tx = P.setcase(tx, fn, c, s, P.v3(nv), tag)
    P.wr('zscript/rsr/rsr_pump_guns.zs', tx)
    # the side port (Shot_Gun only, rsr_sideport): its literals are gun-frame numbers too
    tx = P.rd('zscript/rsr/rsr_pump.zs'); bore = R @ np.array([1.0, 0, 0]); push1 = R @ np.array([0, 1.0, 0])
    V = lambda q: '(%.3f, %.3f, %.3f)' % tuple(P.z0(x) for x in q)
    for a, b in (
        ('Vector3 at = i == 1 ? (12.8, -2.2, 0.5) : RSP_Guns.Port(i);',
         'Vector3 at = i == 1 ? %s : RSP_Guns.Port(i);\t// %s: moved with the gun to the FBX hand (was 12.8, -2.2, 0.5)' % (V(pt(np.array([12.8, -2.2, 0.5]))), tag)),
        ('clearscope static Vector3 PortK(int i, int k) { return k == 1 ? (12.8, -1.9, 0.2) : RSP_Guns.Port(i); }',
         'clearscope static Vector3 PortK(int i, int k) { return k == 1 ? %s : RSP_Guns.Port(i); }\t// %s: moved with the gun (was 12.8, -1.9, 0.2)' % (V(pt(np.array([12.8, -1.9, 0.2]))), tag)),
        ('clearscope static Vector3 PushK(int i, int k) { return k == 1 ? (0, 1, 0) : RSP_Guns.Push(i); }',
         'clearscope static Vector3 PushK(int i, int k) { return k == 1 ? %s : RSP_Guns.Push(i); }\t// %s: turned with the gun (was 0, 1, 0)\n'
         '\tclearscope static Vector3 BoreK(int i) { return %s; }\t// %s: the moved Shot_Gun\'s bore (was 1, 0, 0)' % (V(push1), tag, V(bore), tag)),
        ('double sv1 = rel1 dot (0, 1, 0);', 'double sv1 = rel1 dot PushK(gun, 1);'),
        ('Vector3 lv1 = rel1 - (0, 1, 0) * sv1;', 'Vector3 lv1 = rel1 - PushK(gun, 1) * sv1;'),
        ('acos(clamp(abs(a1.x), 0, 1))', 'acos(clamp(abs(a1 dot BoreK(gun)), 0, 1))'),
        ('+ (RSP_State.SHELL_HALF, 0, 0) +', '+ RSP_State.BoreK(i) * RSP_State.SHELL_HALF +')):
        tx = P.sub1(tx, a, b, a[:40])
    P.wr('zscript/rsr/rsr_pump.zs', tx)
    P.note('pump case %d: Grab, Port, Pull, Push, PumpHook, SupportHook, PortHook, Offset; side port PortK/PushK/BoreK/casing-out' % c)

def rsbc(G, p, R, t, tag):
    tx = P.rd('zscript/rsr/rsb_guns.zs')
    for c in G['rsbc']:
        for fn, kind in (('Hinge', 'p'), ('Axis', 'd'), ('PushRef', 'd'), ('Offset', 'o')):
            v, s = caseval(tx, fn, c)
            nv = R @ v + t if kind == 'p' else R @ v if kind == 'd' else np.array(p[:3])
            if kind == 'o': assert np.abs(v - np.array(G['off'])).max() < 1e-3, ('rsb Offset not base', v)
            tx = P.setcase(tx, fn, c, s, '(%.4f, %.4f, %.4f)' % tuple(P.z0(x) for x in nv), tag)
        v, s = caseval(tx, 'Casing', c)
        if np.abs(v).max() > 0: tx = P.setcase(tx, 'Casing', c, s, '(%.4f, %.4f, %.4f)' % tuple(R @ v + t), tag)
    P.wr('zscript/rsr/rsb_guns.zs', tx)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cls'); ap.add_argument('fit'); ap.add_argument('--src'); ap.add_argument('--tag', default='shotguns'); ap.add_argument('--dry', action='store_true')
    P.ARGS = A = ap.parse_args()
    if A.src: P.SRC = os.path.abspath(A.src)
    G = dict(P.GUNS[A.cls], cls=A.cls); G['md3'] = os.path.join(P.SRC, G['md3'])
    F = json.load(open(A.fit)); fitdir = os.path.dirname(os.path.abspath(A.fit))
    if 'place' in F: p = np.array(F['place'], float); res = None
    else: p, res, R0, t0 = P.place(G, F['shift'])
    R, t = P.rigid_move(G, p)
    print('%s: MODELDEF Offset %.3f %.3f  ZOffset %.3f  Angle/Pitch/Roll %.3f/%.3f/%.3f' % ((A.cls,) + tuple(p)), '' if res is None else '(chain residual %.4f cm)' % res)
    P.gun_blocks_cache = {A.cls: P.gun_blocks(G)}
    P.modeldef(G, p, A.tag)
    P.gunmoves(G, p, A.tag)
    if G.get('rsr'): P.rsr(G, p, R, t, A.tag)
    if G.get('pump'): pump(G, p, R, t, A.tag)
    if G.get('rsbc'): rsbc(G, p, R, t, A.tag)
    P.casing(G, R, t, A.tag)
    if not F.get('no_muzzle'): P.muzzle(G, R, t, A.tag)
    if F.get('hand'): P.hand(G, F['hand'], R, t, A.tag, fitdir)
    if hasattr(P, 'flush'): P.flush()
    print('moved %d items%s' % (len(P.MOVED), ' (dry run: nothing written)' if A.dry else ''))
    json.dump(dict(cls=A.cls, place=list(p), R=R.tolist(), t=t.tolist(), moved=P.MOVED), open(os.path.join(fitdir, 'ported_%s.json' % A.cls), 'w'), indent=1)
