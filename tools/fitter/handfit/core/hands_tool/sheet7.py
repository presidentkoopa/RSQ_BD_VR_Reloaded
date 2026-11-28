"""Round 7 engine sheet: side, eye view and finger close-up at rest (RQFG C) and firing (RQFG D), from gate3.py frame dumps
picked by the probe's tic log; last row = the engine close-up (rest) beside the owner's gas-pump reference photo.
Adapted from the round-6 engine_sheet.py (same pick rule). usage: sheet7.py <side tag> <eye tag> <close tag> <out.png>"""
import re,glob,os,sys,numpy as np
from PIL import Image, ImageDraw
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); RIG=os.path.join(LANE,'rigout')
def pick(t,want):
    txt=open(os.path.join(RIG,'logs',f'lanec3_{t}.log'),errors='replace').read()
    fm=np.array([(int(a),int(b)) for a,b in re.findall(r'LANEC FRAME (\d+) t (\d+)',txt)])
    hand={int(a):(int(b),int(c)) for a,b,c in re.findall(r'LANEC T (\d+) gun \S+ hand RQFG (\d+) sup \S+ \S+ stab \S+ gf (-?\d+)',txt)}
    out=[]
    for f in sorted(glob.glob(os.path.join(RIG,'shots',t,'*.ppm'))):
        n=int(os.path.basename(f)[1:6]); tc=np.interp(n,fm[:,0],fm[:,1])
        if abs(tc-round(tc))<0.3 and hand.get(int(round(tc)),(-1,))[0]==want: out.append((f,int(round(tc)),'ABCDEFGH'[hand[int(round(tc))][1]]))
    return out
def main(ts,te,tc_,png,crop=(60,140,330,410)):
    sr=pick(ts,2)[-1]; sf=pick(ts,3)[-1]; er=pick(te,2)[-1]; ef=pick(te,3)[-1]; cr=pick(tc_,2)[-1]; cf=pick(tc_,3)[-1]
    items=[(sr,'SIDE, at rest, tic %d, gun frame %s',None),(sf,'SIDE, FIRING (squeeze), tic %d, gun frame %s',None),
           (er,'EYE VIEW, at rest, tic %d, gun frame %s',None),(ef,'EYE VIEW, FIRING, tic %d, gun frame %s',None),
           (cr,'CLOSE-UP, rest, tic %d, gun frame %s',crop),(cf,'CLOSE-UP, FIRING, tic %d, gun frame %s',crop),
           (cr,'COMPARE: engine close-up (rest), tic %d, gun frame %s',crop),(None,'COMPARE: owner reference (gas-pump grip)',None)]
    W=480; S=Image.new('RGB',(W*2,W*4)); d=ImageDraw.Draw(S)
    for i,(it,lab,cp) in enumerate(items):
        if it is None:
            im=Image.open(os.path.join(LANE,'owner_ref','gas_pump_grip_reference.jpg')).convert('RGB'); im.thumbnail((W,W)); bg=Image.new('RGB',(W,W)); bg.paste(im,(0,(W-im.height)//2)); im=bg; txt=lab
        else:
            f,tc,gf=it; im=Image.open(f); im=im.crop(cp).resize((W,W),Image.LANCZOS) if cp else im.resize((W,W)); txt=lab%(tc,gf)
        S.paste(im,((i%2)*W,(i//2)*W)); d.rectangle(((i%2)*W,(i//2)*W,(i%2)*W+W,(i//2)*W+16),fill=(0,0,0)); d.text(((i%2)*W+5,(i//2)*W+2),'QZD 17.3 r7: '+txt if it else txt,fill=(255,255,0))
    S.save(png); print([(a[0][0] if a[0] else None) for a in items])
if __name__=='__main__': main(*sys.argv[1:5])
