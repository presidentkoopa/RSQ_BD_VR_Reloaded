#!/usr/bin/env python3
"""LD mode, Choked on BD22 VR's shotguns: our own tight patterns, built the way LegenDoom built its two.

  python3 ldl_patch/tools/g2_choked.py      (run from the repo root; writes src/zscript/rsld/ld_g2_choked.zs)

Owner 2026-11-06 round 2: "our own tight pattern with our pellet count, built the way LegenDoom built its pattern".

HOW LEGENDOOM BUILT ITS PATTERNS (read from its FireChoked states; numbers_g2.zs rows Choked|sg_* / ss_*):
  * fixed points, no randomness (A_FireBullets(h, v, -1, ..., FBF_EXPLICITANGLE)), all mirror-symmetric about the aim;
  * the points sit on a square grid of one step in both directions: Shotgun 1.5 deg, SuperShotgun 2.0 deg (the
    vertical uses the same step although LD's shotgun has no vertical spread at all);
  * the pattern is a fixed fraction of the gun's normal horizontal spread: Shotgun out to 3.0 of 5.6, SuperShotgun
    out to 4.0 of 11.2 (NormalFire A_FireBullets 5.6 / 11.2);
  * filled from the centre outwards; an odd count has the centre point (Shotgun 7), an even count has none
    (SuperShotgun 20: the full first ring, then the second ring's 12 off-axis points, its 4 axis points left out).
  In grid steps: Shotgun 7 = (0,0) (+-2,0) (+-1,+-1); SuperShotgun 20 = ring 1 (8) + (+-2,+-1) (+-1,+-2) (+-2,+-2).

OURS (this tool): for each of our shotgun fire sequences' pattern pellet counts (ld_g2_spread.zs: pump 9 / Tactical
14, SSG 18 / 28, SSG one barrel 9 / 14), on the LegenDoom slot's grid:
  1. centre point if the count is odd;
  2. LegenDoom's own points for that slot, in LegenDoom's firing order, a whole mirror group at a time (its centre is
     step 1's business), as long as a group fits;
  3. then further points outward on the same grid: by ring (max(|x|,|y|)), then off-axis points, corners, axis points
     (LegenDoom's SuperShotgun order: it never reached the axis of ring 2), then distance, vertical before horizontal
     on a tie; whole mirror groups (4 or 2 points) that fit.
  The grid step at run time is LegenDoom's step x (our volley's horizontal spread / LegenDoom's), so the pattern keeps
  LegenDoom's fraction of the spread (ld_g2_fx.zs RSLD_Fx_Choked). The table holds grid steps only.
Checked: with LegenDoom's own counts (7, 20) the rule gives back LegenDoom's own point sets.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NUMS = os.path.join(ROOT, 'src', 'zscript', 'rsld', 'numbers_g2.zs')
SPREAD = os.path.join(ROOT, 'src', 'zscript', 'rsld', 'ld_g2_spread.zs')
OUT = os.path.join(ROOT, 'src', 'zscript', 'rsld', 'ld_g2_choked.zs')

# our shotgun fire sequences and the LegenDoom slot whose pattern style they take
SEQ_KEY = {'pump': 'sg', 'ssg': 'ss', 'ssg_one': 'ss'}
LD_STEP_KEY = {'sg': ('sg_h3', 'Choked'), 'ss': ('ss_h0', 'Choked')}	# LD's grid step: its first off-centre value


def numbers():
	rows = {}
	for m in re.finditer(r'"(\w+)\|(\w+)\|([-\d.]+)\|([^|]+)\|', open(NUMS).read()):
		rows[(m.group(1), m.group(2))] = (float(m.group(3)), m.group(4))
	return rows


def ld_points(rows, k):
	pts = []
	i = 0
	while ('Choked', '%s_h%d' % (k, i)) in rows:
		pts.append((rows[('Choked', '%s_h%d' % (k, i))][0], rows[('Choked', '%s_v%d' % (k, i))][0]))
		i += 1
	step = abs(rows[('Choked', LD_STEP_KEY[k][0])][0])
	grid = [(round(h / step), round(v / step)) for h, v in pts]
	for (h, v), (gx, gy) in zip(pts, grid):
		assert abs(gx * step - h) < 1e-6 and abs(gy * step - v) < 1e-6, 'LD point off its grid: %s' % ((h, v),)
	return step, grid


def mirror(p):
	x, y = p
	return sorted(set([(x, y), (-x, y), (x, -y), (-x, -y)]))


def cat(p):
	x, y = abs(p[0]), abs(p[1])
	r = max(x, y)
	if x == 0 or y == 0:
		return 2		# axis
	if x == y:
		return 1		# corner
	return 0			# off-axis


def candidates(ring_max=8):
	c = [(x, y) for x in range(-ring_max, ring_max + 1) for y in range(-ring_max, ring_max + 1) if (x, y) != (0, 0)]
	return sorted(c, key=lambda p: (max(abs(p[0]), abs(p[1])), cat(p), p[0] * p[0] + p[1] * p[1], abs(p[0]) > abs(p[1]), p))


def build(n, ld):
	pts = []
	if n % 2:
		pts.append((0, 0))
	used = set(pts)
	for src in (ld, candidates()):
		for p in src:
			if p == (0, 0) or p in used:
				continue
			g = mirror(p)
			if any(q in used for q in g) or len(pts) + len(g) > n:
				continue
			pts += g
			used.update(g)
		if len(pts) == n:
			break
	assert len(pts) == n, 'cannot fill %d' % n
	return pts


def our_counts():
	"""pattern pellet counts per sequence, normal and Tactical (volleys of range 0), from ld_g2_spread.zs"""
	txt = open(SPREAD).read()
	cnt = {}
	for m in re.finditer(r'AddVolley\("(\w+)", (\d+), [-\d.]+, [-\d.]+, [-\d.]+, [-\d.]+, \d+, ([-\d.]+), (true|false)\);\s*// (\S+)', txt):
		s, n, rng, tac, src = m.group(1), int(m.group(2)), float(m.group(3)), m.group(4) == 'true', m.group(5)
		if s not in SEQ_KEY or rng != 0:
			continue
		c = cnt.setdefault(s, [0, 0, []])
		if not tac:
			c[0] += n
		c[1] += n
		c[2].append(src)
	return cnt


def main():
	rows = numbers()
	lds = {k: ld_points(rows, k) for k in ('sg', 'ss')}
	# the check: LegenDoom's own counts give back LegenDoom's own sets
	for k, (step, grid) in lds.items():
		assert sorted(build(len(grid), grid)) == sorted(grid), 'rule does not give back LegenDoom %s' % k
	out = ['// ld_g2_choked.zs -- GENERATED by ldl_patch/tools/g2_choked.py. Do not edit by hand.',
		'// Choked on our shotguns (owner 2026-11-06 round 2): our own tight pattern for each of our pellet counts, built the',
		'// way LegenDoom built its Shotgun 7 / SuperShotgun 20 (the tool\'s header has the rule). Points in grid steps; the step',
		'// at run time = LegenDoom\'s step (Choked|sg_h3 %g, Choked|ss_h0 %g deg) x our volley spread / LegenDoom\'s spread.' % (lds['sg'][0], lds['ss'][0]),
		'// Check (tool): LegenDoom\'s own counts 7 and 20 give back LegenDoom\'s own point sets.',
		'',
		'class RSLD_G2_Choked',
		'{',
		'	Array<String> key;		// "sg|9": LegenDoom slot key | our pattern pellet count',
		'	Array<int> first, count;	// into px / py',
		'	Array<int> px, py;',
		'',
		'	void Add(String k, Array<int> xs, Array<int> ys) { key.Push(k); first.Push(px.Size()); count.Push(xs.Size()); px.Append(xs); py.Append(ys); }',
		'	int Find(String k, int n) { return key.Find(String.Format("%s|%d", k, n)); }',
		'',
		'	void Fill()',
		'	{',
		'		Array<int> x, y;']
	done = set()
	for s, (n0, n1, srcs) in sorted(our_counts().items()):
		k = SEQ_KEY[s]
		for n in (n0, n1):
			if (k, n) in done:
				continue
			done.add((k, n))
			pts = build(n, lds[k][1])
			out.append('\t\t// %s %d (our %s, %s): %s' % (k, n, s, ' '.join(srcs), ' '.join('(%d,%d)' % p for p in pts)))
			out.append('\t\tx.Clear(); y.Clear();')
			out.append('\t\t' + ' '.join('x.Push(%d); y.Push(%d);' % p for p in pts))
			out.append('\t\tAdd("%s|%d", x, y);' % (k, n))
			print(k, n, s, pts)
	out += ['\t}', '}', '']
	open(OUT, 'w').write('\n'.join(out))
	print(OUT)


if __name__ == '__main__':
	main()
