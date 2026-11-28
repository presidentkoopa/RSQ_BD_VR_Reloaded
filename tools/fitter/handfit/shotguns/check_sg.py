import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import re, os, sys
def read(p): return open(p, errors='replace').read() if os.path.exists(p) else ''
for name in sys.argv[1:]:
    w = name.split('_', 1)[1]; t = read((_DP.WORK + '/runs/lane_b_sgrun' + '/logs/%s.log') % name) + read((_DP.WORK + '/runs/lane_b_sgrun' + '/logs/%s.log.out') % name)
    errs = [l for l in re.findall(r'Script error, "([^"]+)"', t) if 'BD_VoxelPack' not in l]
    vm = re.findall(r'.*(?:VM execution aborted|Unhandled exception|Segmentation|signal 11).*', t)
    held = set(re.findall(r'B22 S \d+ main (\S+)', t)); shots = len(re.findall(r'B22 SHOT', t)); ph = sorted(set(re.findall(r'B22 T \d+ gun \d+ (\S+)', t)))
    print('%-28s err %d %s vm %d %s held %s shots %d phases %s' % (name, len(errs), errs[:3], len(vm), vm[:2], w in held, shots, ','.join(ph) or '-'))
