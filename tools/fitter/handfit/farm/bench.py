"""Per-core speed check of the fitter's hot calls (same code on both machines): revindex.setup(), exactpen on the M79, one curl residual."""
import os, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import farmpaths
sys.path.insert(0, farmpaths.P('lane_b_hv/tools/handfit/heavies'))
import numpy as np
T = {}; t = time.time()
import fit_hv as H; T['import'] = time.time() - t
t = time.time(); ctx, x, to_g, Xf, delta = H.revindex.setup(); T['setup'] = time.time() - t
t = time.time(); F, V = H.scene.merged(H.revlm.GUNS['GrenadeLauncher']['it']); ex = H.exactpen.Exact(V, F); T['exact_build'] = time.time() - t
t = time.time()
for _ in range(5): ex.depth(Xf); ex.unsigned(Xf)
T['depth_x5'] = time.time() - t
t = time.time()
for _ in range(20): H.solve.hand_X(ctx, x)
T['hand_X_x20'] = time.time() - t
t = time.time(); a = np.random.rand(600, 600); [a @ a for _ in range(20)]; T['matmul600_x20'] = time.time() - t
print(json.dumps({k: round(v, 2) for k, v in T.items()}), sys.version.split()[0], np.__version__, os.environ.get('OMP_NUM_THREADS'))
