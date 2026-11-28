"""Heavies lane: list each gun mesh's surfaces at its ready frame in the controller frame (F L U cm, 1.99 MODELDEF placement):
name, vertex count, bbox. Used to name the grip / trigger / bore surfaces for revlm.GUNS entries (measured, not guessed)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, numpy as np
sys.path.insert(0, _DP.HANDS_TOOL)
import scene
def show(path, frame, scale=(-1.0, 1.0, 1.0), off=(0.0, 0.0, -5.0)):
    it = dict(path=path, frame=frame, scale=list(scale), off=list(off)); S = scene.md3_full(path)
    for k, ((T, V), s) in enumerate(zip(scene.item_verts(it), S)):
        print('%2d %-28s nv %5d  F %6.1f..%6.1f  L %6.1f..%6.1f  U %6.1f..%6.1f' % (k, s['name'], len(V), V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
if __name__ == '__main__':
    a = sys.argv; show(a[1], int(a[2]), *( [tuple(map(float, a[3].split(','))), tuple(map(float, a[4].split(',')))] if len(a) > 4 else []))
