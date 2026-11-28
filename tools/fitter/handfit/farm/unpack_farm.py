"""PC side: unzip the joined fitfarm.zip into this folder (the farm root). Refuses any member that would land outside it.
usage: python unpack_farm.py <fitfarm.zip> [<sha256>]"""
import sys, os, zipfile, hashlib, json
z, want = sys.argv[1], (sys.argv[2].lower() if len(sys.argv) > 2 else None)
root = os.path.dirname(os.path.abspath(__file__))
if want:
    h = hashlib.sha256(open(z, 'rb').read()).hexdigest()
    if h != want: print('SHA FAIL', h); sys.exit(1)
n = 0
with zipfile.ZipFile(z) as zf:
    for m in zf.infolist():
        dst = os.path.abspath(os.path.join(root, m.filename))
        if not dst.startswith(root + os.sep): print('refused', m.filename); sys.exit(2)
        if m.is_dir(): continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with zf.open(m) as s, open(dst, 'wb') as d: d.write(s.read())
        n += 1
print('UNPACK OK', n, 'files into', root)
print(open(os.path.join(root, 'PACK.json')).read())
