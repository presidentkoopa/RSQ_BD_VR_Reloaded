"""2.0.5d: THE UNDER-BARREL LAUNCHERS' RSQ GRENADE ROUNDS -- the small grenade in the off hand and in the tube.

Owner 2026-11-17: "we grab grenade, alt fire cycle to the one we want ... and we load it into the launcher". The
round taken from RSQ Tactical Rig's grenade spot is RSQ Grenade's grenade, scaled down to the 40 mm round's size,
in the skin of its kind (zscript/rsr/rsr_m203.zs). This script makes everything it is drawn with:

  src/models/rsq/m203_nade_hand.md3   the grenade baked where the hand's 40 mm round is (m203_round_hand.md3's
                                      space: drawn by the same RSQ_Hands block as the hand, as RQ2H A is)
  src/models/bd/Rifle/m203_nade.md3   the grenade baked where the gun's 40 mm round is (m203_round.md3's space:
                                      the RSR_GunParts blocks of the Rifle (RQ2P B) and the Machinegun (RQ3P B))
  src/models/bd/Grenade/kinds/*.png   the eight kinds' skins, 256 px, from RSQ Grenade's own (its tools/gen_kinds.py
                                      makes them from the same nade.png this pack ships); the frag is nade.png
  src/MODELDEF.rsmnade                the frames: RQ2H C..K (the hand), RQ2P C..K (the Rifle's tube), RQ3P C..K (the
                                      Machinegun's), C the frag, D..K the eight kinds in RSQ Grenade's order

How the grenade is placed: the grenade mesh (models/bd/Grenade/nade.md3, frame 2: ring and spoon on) is scaled so
its body is as long as the round (8.4 units), its body's middle put on the round's middle, its top (ring and spoon)
pointing the way the round's nose points (the round's long axis, measured; the nose is its narrow end).

Run from the repo root:  python tools/rsm_nades/gen_rsm_nades.py <RSQ_UBQSeries checkout>
"""
import os, re, sys, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import md3io

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC = os.path.join(ROOT, 'src')
KINDS = ['frag', 'impact', 'incendiary', 'freeze', 'stun', 'smoke', 'flash', 'charm', 'infight']   # RSQ Grenade kinds.zs
LETTERS = 'CDEFGHIJK'      # frame letter of kind k: LETTERS[k]
NADE_FRAME = 2             # ring and spoon on (as RSQ Grenade's held QGNH and the rig's grenade spot)


def axis_and_nose(V):
    """The round's middle (its box along the axis), its long axis, pointing to the nose (the narrow end), and length."""
    c = V.mean(0)
    _, _, wt = np.linalg.svd(V - c)
    ax = wt[0]
    t = (V - c) @ ax
    r = np.linalg.norm((V - c) - np.outer(t, ax), axis=1)
    span = t.max() - t.min()
    lo = r[t < t.min() + span * 0.15].max()
    hi = r[t > t.max() - span * 0.15].max()
    if hi > lo:            # the far end is the wide one (the case's rim): the nose is the other way
        ax = -ax
        t = -t
    mid = c + ax * (t.max() + t.min()) / 2
    return mid, ax, span


def rot_to(a, b):
    """Rotation matrix turning unit a onto unit b."""
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); s = np.linalg.norm(v); c = float(a @ b)
    if s < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * ((1 - c) / s ** 2)


# md3 normals as QuestZDoom reads them (models_md3.cpp UnpackVector): hi byte h, lo byte l, angles x pi/128;
# n = (cos h sin l, sin h sin l, cos l)
def unpack_n(p):
    p = p.astype(np.int64) & 0xffff
    h = ((p >> 8) & 0xff) * math.pi / 128
    l = (p & 0xff) * math.pi / 128
    return np.stack([np.cos(h) * np.sin(l), np.sin(h) * np.sin(l), np.cos(l)], 1)


def pack_n(n):
    n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    l = np.round(np.arccos(np.clip(n[:, 2], -1, 1)) * 128 / math.pi).astype(np.int64) & 0xff
    h = np.round(np.arctan2(n[:, 1], n[:, 0]) * 128 / math.pi).astype(np.int64) & 0xff
    v = (h << 8) | l
    return np.where(v >= 32768, v - 65536, v).astype(np.int16)


def bake(round_md3, out_md3):
    R = md3io.read(round_md3)['surfs'][0]['xyz'][0]
    mid, nose, length = axis_and_nose(R)
    N = md3io.read(os.path.join(SRC, 'models/bd/Grenade/nade.md3'))
    body = N['surfs'][0]['xyz'][NADE_FRAME]
    bmin, bmax = body.min(0), body.max(0)
    bmid = (bmin + bmax) / 2
    s = length / (bmax[2] - bmin[2])            # the body's height (its z) to the round's length
    M = rot_to(np.array([0.0, 0.0, 1.0]), nose)  # its top (+z: ring, spoon) to the round's nose
    xyz, st, tris, nrm = [], [], [], []
    base = 0
    for i, sf in enumerate(N['surfs']):
        if len(sf['st']) < 8:                  # a stray 3-vertex surface in the mesh (nothing drawn)
            continue
        v = (sf['xyz'][NADE_FRAME] - bmid) * s @ M.T + mid
        xyz.append(v); st.append(sf['st']); tris.append(sf['tris'] + base)
        nrm.append(pack_n(unpack_n(sf['nrm'][NADE_FRAME]) @ M.T))
        base += len(v)
    surf = dict(name=b'rsm_nade', tris=np.concatenate(tris), st=np.concatenate(st), xyz=np.concatenate(xyz),
                nrm=np.concatenate(nrm), shader=b'')
    md3io.write(out_md3, b'rsm_nade', [surf])
    print('%s: scale %.4f, middle %s, nose %s, %d vertices' % (os.path.relpath(out_md3, ROOT), s, mid.round(3), nose.round(3), len(surf['xyz'])))


def block_of(text, cls, spr, frame):
    for m in re.finditer(r'Model\s+%s\s*\{(.*?)\}' % cls, text, re.S):
        if re.search(r'FrameIndex\s+%s\s+%s\s' % (spr, frame), m.group(1)):
            return m.group(1)
    raise SystemExit('no %s %s %s block' % (cls, spr, frame))


def placement(body):
    keep = []
    for ln in body.splitlines():
        w = ln.strip().split()
        if w and w[0] in ('Scale', 'Offset', 'ZOffset', 'AngleOffset', 'PitchOffset', 'RollOffset', 'NoInterpolation'):
            keep.append('\t' + ln.strip())
    return '\n'.join(keep)


def skin(k):
    return 'models/bd/Grenade/nade.png' if k == 0 else 'models/bd/Grenade/kinds/nade_%s.png' % KINDS[k]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    ubq = os.path.abspath(sys.argv[1])
    bake(os.path.join(SRC, 'models/rsq/m203_round_hand.md3'), os.path.join(SRC, 'models/rsq/m203_nade_hand.md3'))
    bake(os.path.join(SRC, 'models/bd/Rifle/m203_round.md3'), os.path.join(SRC, 'models/bd/Rifle/m203_nade.md3'))
    kd = os.path.join(SRC, 'models/bd/Grenade/kinds')
    os.makedirs(kd, exist_ok=True)
    for k in range(1, len(KINDS)):
        im = Image.open(os.path.join(ubq, 'Grenade/models/rsqgn/nade_%s.png' % KINDS[k])).convert('RGB')
        im.resize((256, 256), Image.LANCZOS).save(os.path.join(kd, 'nade_%s.png' % KINDS[k]), optimize=True)
    rsm = open(os.path.join(SRC, 'MODELDEF.rsm'), encoding='latin-1').read()
    hand = block_of(rsm, 'RSQ_Hands', 'RQ2H', 'A')
    rifle = placement(block_of(rsm, 'RSR_GunParts', 'RQ2P', 'B'))
    mg = placement(block_of(rsm, 'RSR_GunParts', 'RQ3P', 'B'))
    hand_place = placement(hand)
    hand_frame = re.search(r'FrameIndex\s+RQ2H\s+A\s+0\s+(\d+)', hand).group(1)
    out = ['// 2.0.5d GENERATED by tools/rsm_nades/gen_rsm_nades.py -- edit the script, not this.',
           '// The under-barrel launchers\' RSQ Grenade rounds (zscript/rsr/rsr_m203.zs): frame C the frag, D..K Impact,',
           '// Incendiary, Freeze, Stun, Smoke, Flash, Charm, Infight (RSQ Grenade kinds.zs order), each in its kind\'s skin.',
           '// RQ2H: the off hand holding it (RQ2H A\'s hand and placement); RQ2P / RQ3P: in the Rifle\'s / Machinegun\'s tube.', '']
    for k in range(len(KINDS)):
        L = LETTERS[k]
        out += ['// %s' % KINDS[k].upper(),
                'Model RSQ_Hands', '{',
                '\tPath "models/rsq"',
                '\tModel 1 "m203_nade_hand.md3"',
                '\tSkin 1 "%s"' % skin(k),
                '\t// the hand\'s Model line LAST (build.py moves it to slot 7; QZD 17.3 sizes a block by its last Model line)',
                '\tModel 0 "fbx/fbx_oh_hold_R.md3"',
                '\tSkin 0 "fbx/fbx_hand.png"',
                hand_place,
                '\tFrameIndex RQ2H %s 0 %s' % (L, hand_frame),
                '\tFrameIndex RQ2H %s 1 0' % L,
                '}', '']
        for spr, place in (('RQ2P', rifle), ('RQ3P', mg)):
            out += ['Model RSR_GunParts', '{',
                    '\tPath "models/bd/Rifle"',
                    '\tModel 0 "m203_nade.md3"',
                    '\tSkin 0 "%s"' % skin(k),
                    place,
                    '\tFrameIndex %s %s 0 0' % (spr, L),
                    '}', '']
    open(os.path.join(SRC, 'MODELDEF.rsmnade'), 'w', encoding='latin-1', newline='\n').write('\n'.join(out))
    print('src/MODELDEF.rsmnade: %d kinds x 3 blocks' % len(KINDS))


if __name__ == '__main__':
    main()
