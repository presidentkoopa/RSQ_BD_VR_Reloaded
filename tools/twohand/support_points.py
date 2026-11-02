"""support_points.py [--write] [--json OUT] : the per-gun two-hand support-point table, MEASURED off the drawn support hands.

2.0.3n: DATA ONLY. It was the table of the script "Two-Hand Aim" (2.0.3k-2.0.3m), which is removed (it turned the drawn gun
at tic rate and lagged the hands in the owner's headset); two-handing is the engine's Two-Hand Grip. Nothing in the shipped
pk3 reads this table. It is kept for later: where each gun's support hand is drawn, in the main controller's frame.

For every gun in the pack it reads, from the pack's own files (src/):
  - zscript/rsq/handtable.zs   Index() (class -> row), SupportHook / SupportRot (the support layer's hook and turn)
  - zscript/rsq/hands.zs       which state label the support layer shows for a row (`if (i == N) spl = "..."`), and
                               that label's sprite frame (RQWS D ...)
  - MODELDEF.rsq               the RSQ_GunSide block that draws that sprite frame (md3, frame, Scale, Offset)
  - zscript/rsq/muzzle.zs      Muzzle() / HasBore(): which guns have a bore (the shots Two-Hand Aim can steer)
  - zscript/rsr/vreload.zs     RSR.PalmGrab(): the off palm point every grab measures from, in the off controller's frame

THE SUPPORT POINT of a gun = where the off palm point (PalmGrab) is when the player's real off hand sits exactly where
the support hand is drawn on that gun. Measured, not taken from handtable SupportPoint (that is 1.92's reference point,
"unchanged" by port192.py; the drawn hands were re-fitted away from it): the free off hand (fbx_oh_free_R.md3, the
mesh the engine draws on the off controller, in its mirrored frame) and the drawn support hand (main controller frame,
through its MODELDEF block and hand-table hook, hudrender.to_local = models.cpp RenderHUDModel) are the same FBX
topology (1937 vertices). The free hand, un-mirrored, is fitted rigidly onto the support hand over the vertices that
move together (trimmed Kabsch: the palm and back of the hand; the fingers are posed differently and drop out). That
rigid motion is where the off controller would be; PalmGrab carried by it is the support point, cm F L U in the main
controller's frame. Both free-hand frames (0 open, 1 closed) are fitted; the closed one (PalmGrab is "the middle of
the closed hand") is used and the open one's answer is printed as the check.

THE GRAB RADIUS (a rule, applied to measured numbers): 15 cm (the Rifle test's), but never more than half the distance
from the support point to the gun hand's own palm point (PalmGrab un-mirrored: the main hand is not mirrored), so a
palm nearer the gun hand than the support point never takes hold.

THE TURN PIVOT (2.0.3m, the drawn gun follows the two hands): the gun model is turned by its weapon layer's offset
(hw_weapon.cpp:108: yaw psp.x / 4, pitch (psp.y - 32) / -4) about Weapon.BobPivot3D, in the model's own turn space
(models.cpp RenderHUDModel: after scale(xscale, zscale, yscale), the offsets and the player's vr_3dweaponOffset). The gun
must turn about the main CONTROLLER (the grip: where the shots and every table here are measured from), so its pivot is
the controller's origin in that space, PARSED from the gun's own MODELDEF block (the gun block with the most frames):
    pivot = S^-1 (-(0, 5, 30) - (xoffset, zoffset, yoffset)),  S = (xscale, zscale, yscale)
(less the player's (-vr_3dweaponOffsetX, Y, Z), added at run time). The same for the hand meshes (hook.PL) gives HandGrip,
the point the hands turn about with the gun. Checked against gunmoves.zs Pivot (the gun origin in hand space).

--write writes the table to tools/twohand/support_table.zs.txt (a ZScript block, not part of src/ and not shipped).
"""
import os, re, sys, json, argparse
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.environ.get('RSQ_SRC', os.path.join(REPO, 'src'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'handfit', 'fbx_fitter'))
import hudrender, hook

def rd(p): return open(os.path.join(SRC, p), encoding='latin-1').read()

def handtable():
	tx = rd('zscript/rsq/handtable.zs')
	idx = {}
	for m in re.finditer(r"if \(w is '(\w+)'\)\s*return (\d+);", tx):
		idx.setdefault(m.group(1), int(m.group(2)))
	def arr(fn):
		b = tx[tx.index('static Vector3 %s(int i)' % fn):]
		v = [list(map(float, re.search(r'%s\[\] = \{([^}]*)\}' % a, b).group(1).split(','))) for a in 'xyz']
		return np.array(v).T
	sup = re.search(r'static String Support\(int i\)\s*\{\s*static const String v\[\] = \{([^}]*)\}', tx).group(1)
	sup = [s.strip().strip('"') for s in sup.split(',')]
	return idx, arr('SupportHook'), arr('SupportRot'), arr('SupportPoint'), sup

def support_labels():
	tx = rd('zscript/rsq/hands.zs')
	lab = {int(m.group(1)): m.group(2) for m in re.finditer(r'if \(i == (\d+)\)\s*\n\s*spl = "(\w+)";', tx)}
	gs = tx[tx.index('class RSQ_GunSide'):]
	frm = {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(r'^\s*(Fbx\w+): (RQ\w\w) ([A-Z]) -1;', gs, re.M)}
	return lab, frm

def gunside_blocks():
	out = {}
	for p in sorted(os.listdir(SRC)):
		if not p.upper().startswith('MODELDEF'):
			continue
		tx = rd(p)
		for m in re.finditer(r'Model RSQ_GunSide\s*\{(.*?)\}', tx, re.S):
			b = m.group(1)
			path = re.search(r'Path "([^"]+)"', b).group(1)
			md3 = re.search(r'Model 0 "([^"]+)"', b).group(1)
			sc = list(map(float, re.search(r'Scale ([-\d. ]+)', b).group(1).split()))
			of = list(map(float, re.search(r'Offset ([-\d. ]+)', b).group(1).split()))
			zo = re.search(r'ZOffset ([-\d.]+)', b)
			for f in re.finditer(r'FrameIndex (RQ\w\w) ([A-Z]) 0 (\d+)', b):
				out[(f.group(1), f.group(2))] = dict(md3=os.path.join(SRC, path, md3), frame=int(f.group(3)), scale=sc, off=of,
					zoff=float(zo.group(1)) if zo else 0.0, file=p)
	return out

def bores():
	tx = rd('zscript/rsq/muzzle.zs')
	b = tx[tx.index('static Vector3 Muzzle(Weapon w)'):tx.index('static bool HasBore')]
	have = set(re.findall(r"if \(n == '(\w+)'\)\s*return \(", b)) | set(re.findall(r"if \(w is '(\w+)'\)\s*return \(", b))
	return have - {'FlameCannon'}	# HasBore: !(w is 'FlameCannon')

SHARED = None
def shared_paths():
	"""model paths that several weapon classes (hand-table classes) draw (the kick boot, the grenade, the fists): not a
	gun's own block"""
	global SHARED
	if SHARED is None:
		weapons = set(handtable()[0])
		use = {}
		for p in sorted(os.listdir(SRC)):
			if p.upper().startswith('MODELDEF'):
				for m in re.finditer(r'^Model (\w+)\s*\{(.*?)^\}', rd(p), re.S | re.M):
					pm = re.search(r'Path "([^"]+)"', m.group(2))
					if pm and m.group(1) in weapons:
						use.setdefault(pm.group(1).lower(), set()).add(m.group(1))
		SHARED = {k for k, v in use.items() if len(v) >= 4}
	return SHARED

def gun_block(classes):
	"""the gun's own MODELDEF block: Scale, Offset, ZOffset of the block with the most FrameIndex lines (not a hand block,
	not a model several weapons share)"""
	best = None
	for p in sorted(os.listdir(SRC)):
		if not p.upper().startswith('MODELDEF'):
			continue
		tx = rd(p)
		for c in classes:
			for m in re.finditer(r'^Model %s\s*\{(.*?)^\}' % c, tx, re.S | re.M):
				b = m.group(1)
				pm = re.search(r'Path "([^"]+)"', b)
				path = pm.group(1) if pm else 'models/rsq'
				if path.startswith('models/rsq') or path.lower() in shared_paths():
					continue
				n = len(re.findall(r'FrameIndex', b))
				sc = list(map(float, re.search(r'^\s*Scale ([-\d. ]+)', b, re.M).group(1).split()))
				of = list(map(float, re.search(r'^\s*Offset ([-\d. ]+)', b, re.M).group(1).split()))
				zo = re.search(r'^\s*ZOffset ([-\d.]+)', b, re.M)
				if zo:
					of[2] = float(zo.group(1))
				if best is None or n > best['frames']:
					best = dict(file=p, cls=c, path=path, frames=n, scale=sc, off=of)
	return best

def turn_pivot(scale, off):
	"""the controller's origin in a HUD model's turn space (models.cpp RenderHUDModel), vr_3dweaponOffset 0"""
	S = np.array([scale[0], scale[2], scale[1]])
	O = np.array([off[0], off[2], off[1]])
	return (-np.array([0.0, 5.0, 30.0]) - O) / S

def gunmoves_pivot():
	tx = rd('zscript/rsq/gunmoves.zs')
	v = list(map(float, re.search(r'Pivot\(int i\).*?v\[\] = \{([^}]*)\}', tx, re.S).group(1).split(',')))
	return np.array(v).reshape(-1, 3)

def palm_grab():
	tx = rd('zscript/rsr/vreload.zs')
	m = re.search(r'static Vector3 PalmGrab\(\) \{ return \(([-\d.]+), ([-\d.]+), ([-\d.]+)\); \}', tx)
	return np.array([float(m.group(i)) for i in (1, 2, 3)])

def draw(md3, fr, h=(0, 0, 0), r=(0, 0, 0)):
	s = hudrender.load(md3)
	V = np.concatenate([x[min(fr, len(x) - 1)] for _, x in s])
	return 100 * (hudrender.to_local(V, dict(hook=list(h), rot=list(r), **hook.PL)) @ hook.P.T)

def kabsch(A, B):
	ca, cb = A.mean(0), B.mean(0)
	U, S, Vt = np.linalg.svd((A - ca).T @ (B - cb))
	d = np.sign(np.linalg.det(Vt.T @ U.T))
	R = Vt.T @ np.diag([1, 1, d]) @ U.T
	return R, cb - R @ ca

def fit(Xf, Xs, keep=0.25, iters=20):
	idx = np.arange(len(Xf))
	for _ in range(iters):
		R, t = kabsch(Xf[idx], Xs[idx])
		res = np.linalg.norm(Xf @ R.T + t - Xs, axis=1)
		idx = np.argsort(res)[:int(keep * len(Xf))]
	return R, t, res, idx

M = np.diag([1.0, -1.0, 1.0])	# the off controller's frame is mirrored (its L points right): free-hand coords -> a true frame
FREE = 'fbx_oh_free_R.md3'

def measure():
	idx, shook, srot, spoint, sup = handtable()
	lab, frm = support_labels()
	blocks = gunside_blocks()
	bore = bores()
	pg = palm_grab()
	free = os.path.join(SRC, 'models/rsq/fbx', FREE)
	Xf = {fr: draw(free, fr) @ M for fr in (0, 1)}
	gun_palm = M @ pg	# the gun hand's own palm point, main frame (not mirrored)
	hand_grip = turn_pivot(hook.PL['scale'], hook.PL['off'])
	gmp = gunmoves_pivot()
	rows = {}
	for cls, r in idx.items():
		rows.setdefault(r, []).append(cls)
	guns, left = [], []
	for r in sorted(rows):
		names = rows[r]
		if not any(c in bore for c in names):
			left.append(dict(row=r, classes=names, why='no bore in muzzle.zs (no shot Two-Hand Aim can steer)'))
			continue
		if sup[r] == 'A':
			left.append(dict(row=r, classes=names, why='support "A", the pistol cup: the hands are together on the grip, no line between them (hands.zs 2026-10-16 rule)'))
			continue
		if r not in lab:
			left.append(dict(row=r, classes=names, why='no support hand drawn (hands.zs selects none)'))
			continue
		label = lab[r]
		spr, f = frm[label]
		B = blocks[(spr, f)]
		assert B['scale'] == hook.PL['scale'] and B['off'] == hook.PL['off'] and B['zoff'] == 0.0, (label, B)
		Xs = draw(B['md3'], B['frame'], shook[r], srot[r])
		out = {}
		for fr in (1, 0):
			R, t, res, keep = fit(Xf[fr], Xs)
			out[fr] = dict(point=R @ (M @ pg) + t, R=R, t=t, rms=float(np.sqrt((res[keep] ** 2).mean())), n03=int((res < 0.3).sum()))
		p = out[1]['point']
		grab = min(15.0, 0.5 * float(np.linalg.norm(p - gun_palm)))
		gb = gun_block(names)
		piv = turn_pivot(gb['scale'], gb['off'])
		sx = abs(gb['scale'][0])
		assert all(abs(abs(s) - sx) < 1e-6 for s in gb['scale']) and gb['scale'][0] < 0, ('a turn is rigid only under a uniform scale mirrored like the hands', gb)
		gm = gmp[r] if r < len(gmp) else np.zeros(3)
		guns.append(dict(row=r, classes=names, label=label, pivot=piv.round(3).tolist(), pivot_block='%s %s (%d frames) Scale %s Offset %s' % (gb['file'], gb['path'], gb['frames'], gb['scale'], gb['off']),
			pivot_vs_gunmoves_cm=round(float(np.linalg.norm((hand_grip - gm) - piv)), 3) if sx == 1.0 else None, md3=os.path.relpath(B['md3'], SRC), frame=B['frame'], block=B['file'],
			hook=shook[r].tolist(), rot=srot[r].tolist(), point=p.round(2).tolist(), open_check=out[0]['point'].round(2).tolist(),
			open_vs_closed_cm=round(float(np.linalg.norm(out[0]['point'] - p)), 2), fit_rms_cm=round(out[1]['rms'], 3),
			fit_vertices_within_0_3cm=out[1]['n03'], grab_cm=round(grab, 1), steer=1.0,
			old_supportpoint_cm=(spoint[r] * 100).round(1).tolist(),
			off_controller_R=out[1]['R'].round(5).tolist(), off_controller_t=out[1]['t'].round(3).tolist()))
	return guns, left

def zs_block(guns):
	n = max(g['row'] for g in guns) + 1
	def col(k, j=None, fmt='%.2f', default=0):
		v = [default] * n
		for g in guns:
			v[g['row']] = g[k][j] if j is not None else g[k]
		return ', '.join(fmt % x for x in v)
	lines = ['// twohand-table BEGIN: generated by tools/twohand/support_points.py --write (do not edit by hand)']
	for g in guns:
		lines.append('// row %d %s: %s (%s frame %d), point %.2f %.2f %.2f cm (open-hand check %.2f cm off), fit rms %.2f cm over %d vertices <= 0.3 cm, grab %.1f cm'
			% (g['row'], '/'.join(g['classes']), g['label'], os.path.basename(g['md3']), g['frame'], g['point'][0], g['point'][1], g['point'][2],
			   g['open_vs_closed_cm'], g['fit_rms_cm'], g['fit_vertices_within_0_3cm'], g['grab_cm']))
	lines.append('\tconst ROWS = %d;' % n)
	lines.append('\tclearscope static bool Gun(int i)\n\t{\n\t\tstatic const int v[] = { %s };\n\t\treturn i > 0 && i < ROWS && v[i] != 0;\n\t}'
		% col('steer', fmt='%d', default=0).replace('1', '1'))
	lines.append('\t// the support point, cm F L U in the main controller\'s frame')
	lines.append('\tclearscope static Vector3 Support(int i)\n\t{\n\t\tstatic const double x[] = { %s };\n\t\tstatic const double y[] = { %s };\n\t\tstatic const double z[] = { %s };\n\t\treturn Gun(i) ? (x[i], y[i], z[i]) : (0, 0, 0);\n\t}'
		% (col('point', 0), col('point', 1), col('point', 2)))
	lines.append('\t// the palm within this of Support at the grip\'s press: two hands on the gun (cm)')
	lines.append('\tclearscope static double Grab(int i)\n\t{\n\t\tstatic const double v[] = { %s };\n\t\treturn Gun(i) ? v[i] : 0;\n\t}' % col('grab_cm', fmt='%.1f'))
	lines.append('\t// how much of the turn from the barrel line onto the two-hand line the shots take (1 = all of it, as the Rifle test)')
	lines.append('\tclearscope static double Steer(int i)\n\t{\n\t\tstatic const double v[] = { %s };\n\t\treturn Gun(i) ? v[i] : 0;\n\t}' % col('steer', fmt='%.2f'))
	lines.append('\t// 2.0.3m: where the gun model turns (Weapon.BobPivot3D) so that it turns about the main controller: the controller\'s origin in')
	lines.append('\t// the gun\'s MODELDEF turn space, parsed from its block (vr_3dweaponOffset 0); and the same for the hand meshes')
	for g in guns:
		lines.append('\t//   row %d %s: %s, pivot %.3f %.3f %.3f%s' % (g['row'], '/'.join(g['classes']), g['pivot_block'], g['pivot'][0], g['pivot'][1], g['pivot'][2],
			'' if g['pivot_vs_gunmoves_cm'] is None else ' (gunmoves.zs Pivot agrees to %.3f cm)' % g['pivot_vs_gunmoves_cm']))
	lines.append('\tclearscope static Vector3 Pivot(int i)\n\t{\n\t\tstatic const double x[] = { %s };\n\t\tstatic const double y[] = { %s };\n\t\tstatic const double z[] = { %s };\n\t\treturn Gun(i) ? (x[i], y[i], z[i]) : (0, 0, 0);\n\t}'
		% (col('pivot', 0, '%.3f'), col('pivot', 1, '%.3f'), col('pivot', 2, '%.3f')))
	hg = turn_pivot(hook.PL['scale'], hook.PL['off'])
	lines.append('\tclearscope static Vector3 HandGrip() { return (%.3f, %.3f, %.3f); }	// hook.PL %s' % (hg[0], hg[1], hg[2], hook.PL))
	lines.append('// twohand-table END')
	return '\n'.join(lines) + '\n'

if __name__ == '__main__':
	ap = argparse.ArgumentParser()
	ap.add_argument('--write', action='store_true')
	ap.add_argument('--json')
	a = ap.parse_args()
	guns, left = measure()
	print('PalmGrab (vreload.zs):', palm_grab().tolist())
	print('%-4s %-34s %-20s %-24s %-22s %6s %5s %5s  %s' % ('row', 'classes', 'label', 'support point cm F L U', 'open-hand check', 'rms', 'n.3', 'grab', 'old handtable SupportPoint'))
	for g in guns:
		print('%-4d %-34s %-20s %-24s %-22s %6.3f %5d %5.1f  %s' % (g['row'], '/'.join(g['classes'])[:34], g['label'], '%.2f %.2f %.2f' % tuple(g['point']),
			'%.2f %.2f %.2f' % tuple(g['open_check']), g['fit_rms_cm'], g['fit_vertices_within_0_3cm'], g['grab_cm'], g['old_supportpoint_cm']))
	print('turn pivots (MODELDEF-parsed; HandGrip %s):' % turn_pivot(hook.PL['scale'], hook.PL['off']).round(3).tolist())
	for g in guns:
		print('  row %-3d %-24s %-28s %s  vs gunmoves %s' % (g['row'], g['classes'][0], g['pivot'], g['pivot_block'], g['pivot_vs_gunmoves_cm']))
	print('left out:')
	for l in left:
		print('  row %d %s: %s' % (l['row'], '/'.join(l['classes']), l['why']))
	if a.json:
		json.dump(dict(guns=guns, left=left, palm_grab=palm_grab().tolist()), open(a.json, 'w'), indent=1)
	if a.write:
		p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'support_table.zs.txt')
		open(p, 'w', encoding='latin-1', newline='').write(zs_block(guns))
		print('wrote', p)
