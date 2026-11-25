#!/usr/bin/env python3
"""gen_noammo_box.py -- the chaingun's spent box, dropped on a hand reload (MODELDEF.rsr RSR_DroppedMag, sprite RQCW).

Owner 2026-11-24 21:54: "you made a flare voxel box out of the ammobox ... do it again and have the box say NO AMMO
instead of FLARE". So this is RSQ FnF's flare box (FlashFlare/tools/gen_flarebox.py) made again, step for step, from
BD_VoxelPack's ammo box (Voxels/Ammo/AMMOA.kvx, DooMAD's "Ammo Box"):
  - the belt and the open lid flap off, the lid closed flat (gen_flarebox.make_box)
  - each long side one plain panel (gen_flarebox.one_panel)
  - recoloured the flare box's dark red, shading kept (gen_flarebox.recolour)
  - "NO AMMO" in 2x2-voxel letters across each long side, in the flare box's lighter red, and its silver latch
then turned into an MD3 the way the Minigun magazine was (WoS_Reloaded tools/ammobox_md3.py): every voxel face open to
the air is a quad, coloured from the box's own palette (a 16 x 16 skin). Same voxel size as ammobox.md3 (18 units for
AMMOA's 103 voxels), the box's middle at the origin.

    python3 -I tools/gen_noammo_box.py <path to RSQ_UBQSeries/FlashFlare/tools>
writes src/models/rsq/ammobox/noammo_box.md3 and noammo_box.png
"""
import os, random, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FF = sys.argv[1]
sys.path.insert(0, FF)
from kvx import Kvx
import gen_flarebox as fb
from PIL import Image

FONT = {   # 5 rows; widths vary (M and N need more than 3 to read)
    'N': ['#..#', '##.#', '#.##', '#..#', '#..#'],
    'O': ['###', '#.#', '#.#', '#.#', '###'],
    'A': ['.#.', '#.#', '###', '#.#', '#.#'],
    'M': ['#...#', '##.##', '#.#.#', '#...#', '#...#'],
    ' ': ['..', '..', '..', '..', '..'],
}
TEXT = 'NO AMMO'


def stamp(k, panels, ink, latch):
    widths = [len(FONT[c][0]) for c in TEXT]
    cells_w = sum(widths) + len(TEXT) - 1
    for step, out, (x0, x1, z0, z1) in panels:
        w = cells_w * 2
        cx = (x0 + x1 + 1) // 2
        start = cx - w // 2
        ztop = (z0 + z1 + 1) // 2 - 5
        at = 0
        for ch, cw in zip(TEXT, widths):
            for row in range(5):
                for col in range(cw):
                    if FONT[ch][row][col] != '#':
                        continue
                    for dx in range(2):
                        for dz in range(2):
                            u = (at + col) * 2 + dx
                            # the MD3 turns voxel z over (down to up), which mirrors the sides: so the run is the flare box's, reversed
                            x = start + u if step < 0 else start + w - 1 - u   # reads left to right from outside
                            z = ztop + row * 2 + dz
                            if (x, out, z) in k.vox:
                                k.vox[(x, out, z)] = ink
            at += cw + 1
        for x in range(cx - 3, cx + 3):
            for z in range(z0 - 3, z0 + 4):
                y = fb.surface(k, x, z, step, k.size[1] - 1 if step > 0 else 0)
                if y is not None:
                    k.vox[(x, y, z)] = latch


def to_md3(k, out_md3, skin_name):
    X, Y, Z = k.size
    S = 18.0 / 103.0
    ctr = (X / 2.0, Y / 2.0, Z / 2.0)
    verts, uvs, tris = [], [], []
    # the inside filled (a KVX stores only the surface): solid between the top and bottom voxel of each column
    solid = set(k.vox)
    cols = {}
    for (x, y, z) in k.vox:
        lo, hi = cols.get((x, y), (z, z)); cols[(x, y)] = (min(lo, z), max(hi, z))
    for (x, y), (lo, hi) in cols.items():
        for z in range(lo, hi + 1):
            solid.add((x, y, z))
    for (x, y, z), ci in k.vox.items():
        for axis in range(3):
            for sign in (-1, 1):
                n = [x, y, z]; n[axis] += sign
                if tuple(n) in solid:
                    continue
                a1, a2 = [a for a in range(3) if a != axis]
                f = [float(x), float(y), float(z)]
                if sign > 0:
                    f[axis] += 1
                pts = []
                for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    q = list(f); q[a1] += u; q[a2] += v; pts.append(q)
                if (sign > 0) != (axis == 1):
                    pts = pts[::-1]
                uv = ((ci % 16 + 0.5) / 16, (ci // 16 + 0.5) / 16)
                i0 = len(verts)
                for q in pts:
                    verts.append(((q[0] - ctr[0]) * S, (q[1] - ctr[1]) * S, -(q[2] - ctr[2]) * S))
                    uvs.append(uv)
                tris.extend([(i0, i0 + 1, i0 + 2), (i0, i0 + 2, i0 + 3)])

    def s64(s, n=64):
        return s.encode()[:n - 1].ljust(n, b'\0')

    def surface(name, v, uv, tri):
        nv, nt = len(v), len(tri)
        o_tri = 108; o_sh = o_tri + nt * 12; o_st = o_sh + 68; o_xyz = o_st + nv * 8; o_end = o_xyz + nv * 8
        s = b'IDP3' + s64(name) + struct.pack('<10i', 0, 1, 1, nv, nt, o_tri, o_sh, o_st, o_xyz, o_end)
        s += b''.join(struct.pack('<3i', *t) for t in tri) + s64(skin_name) + struct.pack('<i', 0)
        s += b''.join(struct.pack('<2f', *u) for u in uv)
        s += b''.join(struct.pack('<3hBB', *[int(round(c * 64)) for c in q], 0, 0) for q in v)
        return s

    bodies = []
    step = 4096 // 4 * 4
    for s0 in range(0, len(verts), step):
        v = verts[s0:s0 + step]; uv = uvs[s0:s0 + step]
        tr = [(a - s0, b - s0, c - s0) for a, b, c in tris if s0 <= a < s0 + step]
        bodies.append(surface('box%d' % (s0 // step), v, uv, tr))
    mn = [min(p[i] for p in verts) for i in range(3)]
    mx = [max(p[i] for p in verts) for i in range(3)]
    rad = sum((mx[i] - mn[i]) ** 2 for i in range(3)) ** 0.5 / 2
    frame = struct.pack('<3f3f3ff', *mn, *mx, 0, 0, 0, rad) + s64('box', 16)
    head = b'IDP3' + struct.pack('<i', 15) + s64('noammo_box') + struct.pack(
        '<9i', 0, 1, 0, len(bodies), 0, 108, 108 + len(frame), 108 + len(frame), 108 + len(frame) + sum(map(len, bodies)))
    open(out_md3, 'wb').write(head + frame + b''.join(bodies))
    return len(tris) // 2, [round(mx[i] - mn[i], 2) for i in range(3)]


def main():
    src = Kvx.read(os.path.join(FF, 'src', 'AMMOA.kvx'))
    rng = random.Random(7)
    k = fb.make_box(src)
    panels = list(fb.one_panel(k, rng))
    ink, latch = fb.recolour(k)
    stamp(k, panels, ink, latch)
    outdir = os.path.join(ROOT, 'src', 'models', 'rsq', 'ammobox')
    faces, size = to_md3(k, os.path.join(outdir, 'noammo_box.md3'), 'noammo_box.png')
    im = Image.new('RGB', (16, 16))
    for i in range(256):
        r, g, b = k.pal[i]
        im.putpixel((i % 16, i // 16), (min(255, r * 4 + r // 16), min(255, g * 4 + g // 16), min(255, b * 4 + b // 16)))
    im.save(os.path.join(outdir, 'noammo_box.png'))
    print('noammo_box.md3: %d faces, size %s units; box %s voxels; panels %s' % (faces, size, k.size, [p[2] for p in panels]))


if __name__ == '__main__':
    main()
