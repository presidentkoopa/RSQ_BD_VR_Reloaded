"""Build LDL_BD22VR_Patch.pk3 into the repo's pk3/ folder (load it last: after LegenDoom 3.0 and Champions).

  python ldl_patch/build.py

Packs ldl_patch/src/ and adds BD22 VR's own status bar (../src/SBARINFO.rsq, copied at build time so it always
matches this repo's BD22 VR): LegenDoom 3.0 ships a full SBARINFO that, loaded after BD22 VR, replaces its HUD.
Before packing it regenerates src/zscript/rsldp/tables.zs (tools/gen_tables.py) and checks that every effect the
bridge claims is handled by name in the code.
"""
import os, sys, zipfile, subprocess, re
here = os.path.dirname(os.path.abspath(__file__))
repo = os.path.dirname(here)
src = os.path.join(here, 'src')
out = os.path.join(repo, 'pk3', 'LDL_BD22VR_Patch.pk3')

subprocess.check_call([sys.executable, '-I', os.path.join(here, 'tools', 'gen_tables.py')], cwd=os.path.join(here, 'tools'),
                      stdout=subprocess.DEVNULL)
code = ''.join(open(os.path.join(src, 'zscript', 'rsldp', f)).read() for f in ('effects.zs', 'handler.zs'))
impl = re.findall(r'"(\w+)"', open(os.path.join(src, 'zscript', 'rsldp', 'tables.zs')).read().split('Implemented[] =')[1].split('};')[0])
missing = [e for e in impl if ('"%s"' % e) not in code]
if missing:
    sys.exit('effects claimed but not handled in effects.zs/handler.zs: %s' % missing)

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(src):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, src).replace(os.sep, '/'))
    sb = open(os.path.join(repo, 'src', 'SBARINFO.rsq'), encoding='latin-1').read()
    z.writestr('SBARINFO.rsldp', ('// BD22 VR\'s status bar (../src/SBARINFO.rsq, copied by ldl_patch/build.py): LegenDoom 3.0\'s SBARINFO\n'
                                  '// would otherwise replace it.\n' + sb).encode('latin-1'))
print(out, '(%d effects carried)' % len(impl))
