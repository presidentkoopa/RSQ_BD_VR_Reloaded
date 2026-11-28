import re,sys,glob,os
def blocks(root):
    out=[]
    for f in sorted(glob.glob(os.path.join(root,'MODELDEF*'))):
        L=open(f,encoding='latin1').read().split('\n')
        i=0
        while i<len(L):
            m=re.match(r'\s*Model\s+(\S+)',L[i])
            if m and not re.match(r'\s*Model\s+\d',L[i]):
                j=i; depth=0; started=False
                while True:
                    depth+=L[j].count('{')-L[j].count('}')
                    if '{' in L[j]: started=True
                    if started and depth<=0: break
                    j+=1
                body='\n'.join(L[i:j+1])
                models=re.findall(r'Model\s+\d+\s+"([^"]+)"',body); path=re.findall(r'Path\s+"([^"]+)"',body)
                spr=sorted(set(re.findall(r'FrameIndex\s+(\S+)\s+\S+',body)))
                g=lambda k: (re.findall(k+r'\s+([-\d\. ]+)',body) or [''])[0].strip()
                out.append(dict(file=os.path.basename(f),line=i+1,cls=m.group(1),path=path,models=models,spr=spr,off=g('\n\s*Offset'),z=g('ZOffset'),ao=g('AngleOffset'),po=g('PitchOffset'),ro=g('RollOffset'),end=j+1))
                i=j
            i+=1
    return out
if __name__=='__main__':
    pat=re.compile(sys.argv[2],re.I)
    for b in blocks(sys.argv[1]):
        s=' '.join(b['path']+b['models'])
        if pat.search(s) or pat.search(b['cls']):
            print(b['file'],b['line'],b['cls'],b['path'],b['models'],' '.join(b['spr'])[:80],'|off',b['off'],'z',b['z'],'aor',b['ao'],b['po'],b['ro'])
