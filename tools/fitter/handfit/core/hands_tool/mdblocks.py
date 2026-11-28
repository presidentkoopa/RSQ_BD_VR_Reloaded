"""Parse every MODELDEF lump of the 1.92 pack into blocks: file, line, model name, path, model files, offsets,
frame sprites. Used to find every block tied to BrutalPistol / Flamethrower2 (by class name, by the gun's model path,
or by a sprite those weapons' states use)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import re, os, json, sys
SRC=_DP.GUNPACK192
def blocks(text):
    out=[]; i=0
    for m in re.finditer(r'(?im)^\s*Model\s+(\S+)\s*\{',text):
        st=m.end(); depth=1; j=st
        while depth and j<len(text):
            if text[j]=='{': depth+=1
            elif text[j]=='}': depth-=1
            j+=1
        body=text[st:j-1]; line=text.count('\n',0,m.start())+1
        g=lambda k:[l.split(None,1)[1].strip() if len(l.split(None,1))>1 else '' for l in re.findall(r'(?im)^\s*'+k+r'\b[^\n]*',body)]
        fr=re.findall(r'(?im)^\s*FrameIndex\s+(\S+)\s+(\S+)\s+(\d+)\s+(\d+)',body)
        out.append(dict(name=m.group(1),line=line,start=m.start(),end=j,path=g('Path'),model=g('Model'),off=g('Offset'),zoff=g('ZOffset'),
                        ang=g('AngleOffset'),pit=g('PitchOffset'),rol=g('RollOffset'),scale=g('Scale'),frames=fr))
    return out
def all_blocks():
    res=[]
    for f in sorted(os.listdir(SRC)):
        if f.upper().startswith('MODELDEF'):
            for b in blocks(open(os.path.join(SRC,f),encoding='latin-1').read()): b['file']=f; res.append(b)
    return res
if __name__=='__main__':
    B=all_blocks(); keys=sys.argv[1:]
    for b in B:
        hit=b['name'] in keys or any(k.lower() in ' '.join(b['path']).lower() for k in keys)
        if hit:
            spr=sorted(set(f[0] for f in b['frames']))
            print('%-18s %5d %-28s path=%s model=%s off=%s z=%s ang=%s pit=%s rol=%s nframes=%d spr=%s'%(b['file'],b['line'],b['name'],b['path'],b['model'],b['off'],b['zoff'],b['ang'],b['pit'],b['rol'],len(b['frames']),' '.join(spr)[:120]))
