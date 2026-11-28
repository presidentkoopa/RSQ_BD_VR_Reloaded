"""Pick the dumped frame nearest a tic: frames dumped every N rendered frames (fNNNNN.ppm = rendered frame N), the probe
logs 'LANEC FRAME n t tic'; the gate echoes markers whose tic = the preceding 'LANEC T' line."""
import re, os, glob, sys, json
import numpy as np
def load(log,shots):
    t=open(log,errors='replace').read(); fm=[(int(a),int(b)) for a,b in re.findall(r'LANEC FRAME (\d+) t (\d+)',t)]
    marks={}; last=None
    for l in t.splitlines():
        m=re.match(r'LANEC T (\d+)',l)
        if m: last=int(m.group(1))
        if l.startswith('LANEC_'): marks[l.strip()]=last
    files={int(os.path.basename(f)[1:6]):f for f in glob.glob(shots+'/*.ppm')}
    F=np.array([a for a,b in fm]); T=np.array([b for a,b in fm])
    def frame_at(tic):
        if not len(F): return None
        n=int(np.interp(tic,T,F)); k=min(files,key=lambda q:abs(q-n)) if files else None; return files.get(k)
    return marks,frame_at
if __name__=='__main__':
    marks,fa=load(sys.argv[1],sys.argv[2]); print(marks)
    for m,t in marks.items():
        for dt in [int(a) for a in sys.argv[3:]] or [0]: print(m,t+dt if t is not None else None,fa(t+dt) if t is not None else None)
