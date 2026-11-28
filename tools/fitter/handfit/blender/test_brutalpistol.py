"""The Handfit add-on's acceptance test: the library's BrutalPistol hold, applied in Blender, must land on the hand
BD22 2.0.1 ships. Run on a machine with Blender (4.x), from the repo root:

    blender -b --python tools/handfit/blender/test_brutalpistol.py -- [--bd22 /path/to/rs_brutal22weaponsq] [--out work/handfit]

Three checks, numbers measured on 2026-11-08 with the kit's own forward kinematics (what the add-on must reproduce):
  1. pose:  the posed, skinned mesh in the palm frame vs the library's FK reference cloud (same mesh, same pose):
            nearest-vertex distance max < 0.05 FBX units. Anything else = the bone mapping (K) or scale is wrong.
  2. frame: the exported MD3 frame vs BD22's shipped `models/rsq/fbx/fbx_b1_R.md3` frame 0 (Brutal_gun), needs --bd22:
            nearest-vertex mean < 0.02 and max < 0.30 md3 units (the kit measured 0.008 / 0.24: the max is the few
            per-vertex corrections BD22's bake kept outside the index finger).
  3. round trip: the gun's six MODELDEF numbers read back from the gun object equal the ones it was placed with.
Prints PASS / FAIL per check and exits 1 on any FAIL. Written where Blender cannot run: the first run is the test of the
test too; if it fails in a way that smells like the harness (import names, API), say so rather than fitting around it.
"""
import os, sys, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import handfit_addon as H  # noqa: E402
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bd22 = args[args.index('--bd22') + 1] if '--bd22' in args else os.path.join(H.REPO, '..', 'rs_brutal22weaponsq')
out = args[args.index('--out') + 1] if '--out' in args else os.path.join(H.REPO, 'work', 'handfit')
fails = []


def check(name, ok, detail):
    print('%s  %s  %s' % ('PASS' if ok else 'FAIL', name, detail)); fails.append(name) if not ok else None


bpy.ops.wm.read_factory_settings(use_empty=True)
lib = H.load_library()
key = 'bd22:BrutalPistol'; ent = lib['poses'][key]

# the gun, placed with the hold's six numbers (BD22's MODELDEF.bd: Scale -1 1 1)
gun_objs, card = H.import_gun(os.path.join(H.REPO, 'cards', 'bd21', 'pistol'), lib, (-1.0, 1.0, 1.0), ent['gun_move'])
gn = H.gun_numbers(gun_objs[0])
want = ent['gun_move']
d_off = max(abs(gn['Offset'][0] - want['Offset_x']), abs(gn['Offset'][1] - want['Offset_y']), abs(gn['ZOffset'] - want['ZOffset']))
d_ang = max(abs(gn['AngleOffset'] - want['AngleOffset']), abs(gn['PitchOffset'] - want['PitchOffset']), abs(gn['RollOffset'] - want['RollOffset']))
check('3 gun numbers round trip', d_off < 0.002 and d_ang < 0.002, 'max |d offset| %.4f, max |d angle| %.4f deg; read back %s' % (d_off, d_ang, gn))

# the hand
rigs = H.import_hand()
rig = H.apply_library_pose(rigs, lib, key, seat=True)
print('bone-axis correction K error %.5f, importer unit scale %.5f' % (rig.K_err, rig.s_y))
check('0 bone mapping solved', rig.K_err < 1e-2, 'K error %.5f (a signed permutation must fit the rest pose exactly)' % rig.K_err)

# 1. pose vs the FK reference cloud (palm frame, FBX units)
ref = lib['reference'][key]['verts']
V = rig.palm_verts()
kd = KDTree(len(ref))
for i, v in enumerate(ref): kd.insert(v, i)
kd.balance()
d = [kd.find(v)[2] for v in V]
check('1 pose vs FK reference', max(d) < 0.05, 'nearest-vertex mean %.4f max %.4f FBX units over %d verts (ref %d)' % (sum(d) / len(d), max(d), len(V), len(ref)))

# 2. exported frame vs the shipped BD22 frame
rep = H.export_hand(rig, out, 'BrutalPistol', [('Brutal_gun', ent['joints'])])
shipped = os.path.join(bd22, 'src', 'models', 'rsq', 'fbx', 'fbx_b1_R.md3')
if os.path.exists(shipped):
    S = H.read_md3(shipped)['surfs'][0]['xyz'][0]; M = H.read_md3(rep['md3'])['surfs'][0]['xyz'][0]
    kd = KDTree(len(S))
    for i, v in enumerate(S): kd.insert(v, i)
    kd.balance()
    d = [kd.find(v)[2] for v in M]
    check('2 frame vs shipped fbx_b1_R frame 0', (sum(d) / len(d)) < 0.02 and max(d) < 0.30, 'nearest-vertex mean %.4f max %.4f md3 units (%d verts vs %d shipped)' % (sum(d) / len(d), max(d), len(M), len(S)))
else:
    print('SKIP  2 frame vs shipped: %s not found (pass --bd22)' % shipped)

print(H.report_line(rig, lib, key))
print('wrote', rep['md3'])
if fails:
    print('FAILED:', fails); sys.exit(1)
print('ALL PASS')
