"""TEST ONLY (never ships): a copy of BD22Q 1.92 (lane_c/bd22q_192, unzipped from the depot's build/BD22Q_192.pk3)
whose BrutalPistol hands are the baked FBX hand: models/rsq/fbx/*.md3 + fbx_hand.png (the FBX base colour, 512 px),
MODELDEF.rsq's RQGT C / RQGU C / RQSP A frames pointed at them, and handtable.zs row 4 hooks replaced by the bake rows.
usage: testpack.py <report.json> <out.pk3>"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import json, os, re, shutil, sys, zipfile
from PIL import Image
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=_DP.GUNPACK192
def patch_row(txt,fn,i,vals):
    m=re.search(r'(static Vector3 '+fn+r'\(int i\)\s*\{)(.*?)(\n\t\})',txt,re.S)
    body=m.group(2)
    for k,v in zip('xyz',vals):
        def rep(mm):
            arr=[a.strip() for a in mm.group(2).split(',')]; arr[i]='%.3f'%v
            return mm.group(1)+', '.join(arr)+mm.group(3)
        body=re.sub(r'(static const double '+k+r'\[\] = \{ )([^}]*)( \};)',rep,body,count=1)
    return txt[:m.start(2)]+body+txt[m.end(2):]
def main(report,out):
    R=json.load(open(report)); rows={r['side']:r for r in R['bake']}
    tmp=os.path.join(LANE,'cache','testpack'); shutil.rmtree(tmp,ignore_errors=True); shutil.copytree(SRC,tmp)
    fb=os.path.join(tmp,'models','rsq','fbx'); os.makedirs(fb)
    for s,r in rows.items(): shutil.copy(os.path.join(LANE,'out',r['md3']),os.path.join(fb,r['md3']))
    Image.open((_DP.FBX_TEX + '/lambert1_Base_Color.png')).convert('RGB').resize((512,512),Image.LANCZOS).save(os.path.join(fb,'fbx_hand.png'))
    md=open(os.path.join(tmp,'MODELDEF.rsq'),encoding='latin-1').read()
    for line in ('\tFrameIndex RQGT C 0 14\t// index finger on the trigger\n','\tFrameIndex RQGU C 0 15\t// trigger squeezed\n','\tFrameIndex RQSP A 0 0\t// Ermac hand2.md3 frame 4\n'):
        assert line in md, line; md=md.replace(line,'')
    md+='''
// lane_c TEST: the baked FBX hand on BrutalPistol (RQGT C / RQGU C gun hand, RQSP A support)
Model RSQ_GunSide
{
	Path "models/rsq/fbx"
	Model 0 "%s"
	Skin 0 "fbx_hand.png"
	Scale -1.0 1.0 1.0
	Offset 0.0 -24.0 -10.0
	FrameIndex RQGT C 0 %d
	FrameIndex RQGU C 0 %d
}
Model RSQ_GunSide
{
	Path "models/rsq/fbx"
	Model 0 "%s"
	Skin 0 "fbx_hand.png"
	Scale -1.0 1.0 1.0
	Offset 0.0 -24.0 -10.0
	FrameIndex RQSP A 0 %d
}
'''%(rows['R']['md3'],rows['R']['frame'],rows['R']['frame'],rows['L']['md3'],rows['L']['frame'])
    open(os.path.join(tmp,'MODELDEF.rsq'),'w',encoding='latin-1').write(md)
    ht=os.path.join(tmp,'zscript','rsq','handtable.zs'); t=open(ht).read()
    t=patch_row(t,'GunHook',4,rows['R']['hook']); t=patch_row(t,'GunRot',4,rows['R']['rot'])
    t=patch_row(t,'SupportHook',4,rows['L']['hook']); t=patch_row(t,'SupportRot',4,rows['L']['rot'])
    open(ht,'w').write(t)
    if os.path.exists(out): os.remove(out)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for root,_,files in os.walk(tmp):
            for f in files:
                p=os.path.join(root,f); z.write(p,os.path.relpath(p,tmp))
    print(out,os.path.getsize(out))
if __name__=='__main__': main(*sys.argv[1:3])
