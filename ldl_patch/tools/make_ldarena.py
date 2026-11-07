"""TEST ONLY (never ships): the LD mode's open test arena for the rig (round 4).

  python3 -I ldl_patch/tools/make_ldarena.py [out.wad]      (default /tmp/ldrig/ldarena.wad)

MAP01 (UDMF, Doom 2 textures): one open room 4096 x 4096 (x and y -2048..2048), floor 0, ceiling 1024, light 192, no
things but player 1's start at (-1600, 0) facing east: 3600 units of open floor ahead, so a target 1200 units out has
no wall behind it for 2000 more (round 3's MAP01 had a wall about 350 ahead: rockets and balls died on it before their
in-flight effects showed). Loaded last (ldrig.sh EXTRA), it replaces doom2's MAP01 for the run.
Made the way RSQ_UBQSeries TestRig/maps/make_rig01.py makes its arena (one sector, the boundary clockwise).
"""
import os, struct, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/ldrig/ldarena.wad'
H = 2048
verts = [(-H, -H), (H, -H), (H, H), (-H, H)]
# clockwise boundary: the room on the right of every line (a -> d -> c -> b -> a in this vertex order)
lines = [(0, 3), (3, 2), (2, 1), (1, 0)]
t = ['namespace = "zdoom";']
for (x, y) in verts:
    t.append('vertex { x = %d; y = %d; }' % (x, y))
for i, (v1, v2) in enumerate(lines):
    t.append('linedef { v1 = %d; v2 = %d; sidefront = %d; blocking = true; }' % (v1, v2, i))
for i in range(len(lines)):
    t.append('sidedef { sector = 0; texturemiddle = "STARTAN2"; }')
t.append('sector { heightfloor = 0; heightceiling = 1024; texturefloor = "FLOOR0_1"; textureceiling = "CEIL1_1"; lightlevel = 192; }')
t.append('thing { x = -1600; y = 0; angle = 0; type = 1; skill1 = true; skill2 = true; skill3 = true; skill4 = true; skill5 = true; single = true; coop = true; dm = true; }')
textmap = ('\n'.join(t) + '\n').encode('ascii')
lumps = [('MAP01', b''), ('TEXTMAP', textmap), ('ENDMAP', b'')]
data, dirs, off = b'', [], 12
for name, d in lumps:
    dirs.append((off, len(d), name))
    data += d
    off += len(d)
hdr = struct.pack('<4sii', b'PWAD', len(lumps), 12 + len(data))
body = b''.join(struct.pack('<ii8s', o, n, nm.encode('ascii')) for o, n, nm in dirs)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'wb').write(hdr + data + body)
print(OUT)
