"""sdf.py: a signed distance to a mesh, fast enough to sit inside a least-squares solve.
|d| = distance to dense surface samples (every ~0.1 cm on the triangles, KD-tree; error <= ~0.07 cm).
sign = inside by the generalized winding number (gunfield.winding, the exactpen rule) of 0.25 cm grid cells, computed the
first time a cell is visited and cached; all triangles (a cropped mesh is open: its winding number is wrong near the cut). The final numbers of every fit are re-checked with exactpen (no grid)."""
import numpy as np
from scipy.spatial import cKDTree
import gunfield
def samples(A, B, C, step=0.1):
    out = []
    for a, b, c in zip(A, B, C):
        L = max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)); n = int(np.ceil(L / step)) + 1
        if n == 2: out.append(np.array([a, b, c, (a + b + c) / 3])); continue
        u, v = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n)); m = u + v <= 1
        out.append(a + u[m][:, None] * (b - a) + v[m][:, None] * (c - a))
    return np.concatenate(out)
class SDF:
    def __init__(s, V, F, lo, hi, fine=0.15, margin=4.0, step=0.2):
        A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
        s.A, s.B, s.C = A, B, C; s.ntri = len(A)	# the sign uses EVERY triangle (exactpen's rule): a cropped mesh is open and its winding lies
        kk = ((np.minimum(np.minimum(s.A, s.B), s.C) < hi + 1) & (np.maximum(np.maximum(s.A, s.B), s.C) > lo - 1)).all(1)
        S = samples(s.A[kk], s.B[kk], s.C[kk], step) if kk.any() else np.zeros((1, 3)) + 1e6
        s.tree = cKDTree(S); s.lo = np.asarray(lo, float); s.hi = np.asarray(hi, float); s.fine = fine
        s.grids = {}	# cell size -> sign cells (-1 = not computed yet), filled when first visited
    def _cells(s, P, h):
        if h not in s.grids: n = np.ceil((s.hi - s.lo) / h).astype(int) + 1; s.grids[h] = (n, np.full(tuple(n), -1, np.int8))
        n, g = s.grids[h]; i = np.clip(np.round((P - s.lo) / h).astype(int), 0, n - 1); c = g[i[:, 0], i[:, 1], i[:, 2]]
        new = c < 0
        if new.any():
            u = np.unique(i[new], axis=0); w = gunfield.winding(s.lo + u * h, s.A, s.B, s.C) if s.ntri else np.zeros(len(u))
            g[u[:, 0], u[:, 1], u[:, 2]] = (np.abs(w) > 0.5).astype(np.int8); c = g[i[:, 0], i[:, 1], i[:, 2]]
        return c == 1
    def inside(s, P, d=None):
        """0.25 cm cells within 0.8 cm of the surface, 1 cm cells further out (a cell's sign is its centre's)"""
        P = np.atleast_2d(P); d = s.unsigned(P) if d is None else d; out = np.zeros(len(P), bool); oob = ((P < s.lo) | (P > s.hi)).any(1)
        nr = (d < 0.8) & ~oob; fr = (d >= 0.8) & ~oob
        if nr.any(): out[nr] = s._cells(P[nr], s.fine)
        if fr.any(): out[fr] = s._cells(P[fr], 1.0)
        return out
    def unsigned(s, P): return s.tree.query(np.atleast_2d(P))[0]
    def signed(s, P):
        """< 0 inside (cm), > 0 outside"""
        d = s.unsigned(P); return np.where(s.inside(P, d), -d, d)
