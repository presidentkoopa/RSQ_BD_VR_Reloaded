"""Rigid gun move in the controller frame (F L U cm) implied by a MODELDEF change from
(Offset 0 0, ZOffset -5, no angle offsets) to the r5 values. Chain = lane_c gunplace.to_local_ao
(QZD 17.3 models.cpp RenderHUDModel). Validated against r5's own moved numbers."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, numpy as np
import os as _os; _LIB = _os.path.dirname(_os.path.abspath(__file__)); _HOME = _os.environ.get('RS_FITTER_HOME', _DP.WORK + '/fitter_home/').rstrip('/')	# fitter_lib: sibling modules here; data under RS_FITTER_HOME
sys.path.insert(0, _DP.CORE + '/hands_tool')
import gunplace, gunview
MOVES = {
 'BrutalPistol': dict(off=[0.820, -8.333, -1.408], ao=(3.854, 3.363, 10.974)),
 'Flamethrower2': dict(off=[-4.371, -8.313, -5.669], ao=(-3.798, 1.805, 0.100)),
}
def chain(off, ao):
    it = dict(scale=[-1.0, 1.0, 1.0], off=off, ao=ao)
    return lambda V: gunview.to_fl(gunplace.to_local_ao(np.atleast_2d(np.asarray(V, float)), it))
def affine(f):
    b = f(np.zeros(3))[0]; A = np.stack([f(np.eye(3)[i])[0] - b for i in range(3)], 1); return A, b
def move(gun):
    A0, b0 = affine(chain([0, 0, -5], (0, 0, 0))); m = MOVES[gun]; A1, b1 = affine(chain(m['off'], m['ao']))
    R = A1 @ np.linalg.inv(A0); t = b1 - R @ b0
    return R, t
if __name__ == '__main__':
    for g in MOVES:
        R, t = move(g); print(g, 'det', round(np.linalg.det(R), 6), 'orth err', np.abs(R @ R.T - np.eye(3)).max())
