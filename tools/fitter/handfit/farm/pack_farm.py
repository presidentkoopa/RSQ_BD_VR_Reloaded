"""Cloud side: build the fit-farm package (the full FBX fitter + every input its fits read) as one zip, split into <=28 MB parts.
usage: python3 pack_farm.py <out_dir> [--repo <set>] [--ref origin/hands-heavies] [--part-mb 28]
The package mirrors the cloud's <work>/fitter_home/ subtree under  home/ ; every '<work>/fitter_home/...' literal in a packed .py is rewritten
to  __import__('farmpaths').HOME + '/...'  so it resolves to the farm's copy on any OS (farmpaths.py reads farm.json / FITFARM_HOME).
The BD22 repo (tools/handfit + src/models meshes + handtable.zs) is exported read-only with git archive from <ref> into home/lane_b_hv
(where fit_hv.py's REPO resolves). Nothing in the shared checkout is touched."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, re, io, glob, json, zipfile, hashlib, subprocess, argparse
H = _DP.WORK + '/fitter_home/'
HERE = os.path.dirname(os.path.abspath(__file__))
REWRITE = re.compile(r"""(['"])<work>/fitter_home/""")
def rewrite_py(src):
    # 'x<work>/fitter_home/...' string literal -> __import__('farmpaths').HOME + '/...'  (% and () bind tighter than +, so
    # '<work>/fitter_home/a_%s.npy' % g  stays  HOME + ('/a_%s.npy' % g)). Literals inside docstrings/comments only change text.
    out = []
    for line in src.splitlines(keepends=True):
        s = line.lstrip()
        if s.startswith('#'): out.append(line); continue
        out.append(REWRITE.sub(lambda m: "__import__('farmpaths').HOME + " + m.group(1) + '/', line))
    return ''.join(out)
def files_from(root, pats, skip_ext=('.png', '.jpg', '.pyc', '.log')):
    for p in pats:
        for f in glob.glob(os.path.join(root, p), recursive=True):
            if os.path.isfile(f) and not f.endswith(skip_ext) and '__pycache__' not in f: yield f
def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--repo', default=H + '/rs_brutal22weaponsq')
    ap.add_argument('--ref', default='origin/hands-heavies'); ap.add_argument('--part-mb', type=float, default=28.0); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True); members = {}
    def add(f, arc=None): members[arc or os.path.relpath(f, H).replace(os.sep, '/')] = f
    # the fitter (lane_c) + its data
    for f in files_from(H + '/lane_c', ['hands_tool/**/*.py', '*.json', '*.npy', 'results/**/*', 'bd22q_192/**/*',
                                         'cache/field_BrutalPistol_*.npz', 'cache/field_pistol_*.npz', 'cache/*.npy'], skip_ext=('.png', '.jpg', '.pyc')): add(f)
    # batch 1-4 tools the batch3 / heavies fits import, and the solved seats they start from
    for r in ('lane_b_b1run', 'lane_b_b2run', 'lane_b_b3run', 'lane_b_b4run'):
        for f in files_from(H + '/' + r, ['tools/*.py', 'st2_*.npy', 'curl3_*.json', 'place_*.json', 'revindex_*.json']): add(f)
    for f in files_from(H + '/lane_b_hvrun', ['st2_*.npy', 'curl3_*.json']): add(f)
    # gun meshes those tools name from the batch worktrees (SRC + '/models/...md3') + the approved FBX hand md3s
    for wt, tool in (('lane_b_b2', 'lane_b_b2run/tools'), ('lane_b_b3', 'lane_b_b3run/tools'), ('lane_b_b4', 'lane_b_b4run/tools')):
        for py in glob.glob(H + '/' + tool + '/*.py') + glob.glob(os.path.join(HERE, '..', 'fitter_lib', '*.py')):	# run folders deleted 2026-10-27: the modules are in tools/handfit/fitter_lib
            for rel in re.findall(r"SRC \+ '(/models/[^']+?\.md3)'", open(py, encoding='latin1').read()) + re.findall((r"(?:" + _DP.WORK + '/fitter_home/' + r"|_HOME \+ ')/%s/src(/models/[^']+?\.md3)") % wt, open(py, encoding='latin1').read()):
                if os.path.exists(H + '/' + wt + '/src' + rel): add(H + '/' + wt + '/src' + rel)
        for f in files_from(H + '/' + wt, ['src/models/rsq/fbx/*']): add(f)
    add(H + '/dxr/models/hands/hand_final.fbx')
    for f in files_from(H + '/rsq_weapondepot/docs/reference/bd22q_192_poses', ['**/*'], skip_ext=('.pyc',)): add(f)
    # the BD22 repo at <ref>: tools/handfit, src/models (meshes, no textures), handtable.zs -> home/lane_b_hv
    tar = subprocess.run(['git', '-C', a.repo, 'archive', '--format=zip', a.ref, 'tools/handfit', 'src/models', 'src/zscript/rsq/handtable.zs'],
                         check=True, capture_output=True).stdout
    sha = subprocess.run(['git', '-C', a.repo, 'rev-parse', a.ref], check=True, capture_output=True, text=True).stdout.strip()
    zr = zipfile.ZipFile(io.BytesIO(tar)); repo_members = [n for n in zr.namelist() if not n.endswith('/') and not n.lower().endswith(('.png', '.jpg'))]
    zpath = os.path.join(a.out, 'fitfarm.zip'); nrw = 0
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for arc, f in sorted(members.items()):
            if f.endswith('.py'):
                s = open(f, encoding='utf-8', errors='surrogateescape').read(); s2 = rewrite_py(s); nrw += s2 != s
                z.writestr('home/' + arc, s2.encode('utf-8', errors='surrogateescape'))
            else: z.write(f, 'home/' + arc)
        for n in repo_members:
            b = zr.read(n)
            if n.endswith('.py'):
                s = b.decode('utf-8', errors='surrogateescape'); s2 = rewrite_py(s); nrw += s2 != s; b = s2.encode('utf-8', errors='surrogateescape')
            z.writestr('home/lane_b_hv/' + n, b)
        for n in ('farmpaths.py', 'fit_batch.py', 'farm.json', 'unpack_farm.py', 'compare_fit.py'):
            if os.path.exists(os.path.join(HERE, n)): z.write(os.path.join(HERE, n), n)
        z.writestr('PACK.json', json.dumps(dict(repo_ref=a.ref, repo_sha=sha, files=len(members) + len(repo_members), py_rewritten=nrw), indent=1))
    data = open(zpath, 'rb').read(); digest = hashlib.sha256(data).hexdigest(); step = int(a.part_mb * 1024 * 1024); parts = []
    for i in range(0, len(data), step):
        p = os.path.join(a.out, 'fitfarm.part%02d.bin' % (i // step)); open(p, 'wb').write(data[i:i + step]); parts.append(os.path.basename(p))
    man = dict(zip='fitfarm.zip', bytes=len(data), sha256=digest, parts=parts, repo_ref=a.ref, repo_sha=sha, files=len(members) + len(repo_members), py_rewritten=nrw)
    json.dump(man, open(os.path.join(a.out, 'manifest.json'), 'w'), indent=1); print(json.dumps(man))
if __name__ == '__main__': main()
