"""TEST ONLY (never ships). Round 2: BD22Q 1.92 copy with the baked FBX hands on BrutalPistol (row 4) AND Flamethrower2
(row 7), the hand rows' hooks from the bake, and each gun's MODELDEF block given the mode-C offsets
(results/gun_modeldef_C.json: Offset/ZOffset/AngleOffset/PitchOffset/RollOffset; models.cpp reads all five).
Frames replaced (1.92 letters, handtable.zs): pistol RQGT C / RQGU C / RQSP A; flamethrower RQGT E / RQGU E / RQSP B.
NOTE: those letters are shared with other guns (RQGT E: rows 6, 13, 23; RQSP B: rows 1, 5, 11, 12, 15, 16, 21), which in
this TEST pack show the FBX hand too. Only the two guns are judged.
usage: testpack2.py <out.pk3> [tint]"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import json, os, re, shutil, sys, zipfile
import numpy as np
from PIL import Image
from testpack import patch_row, SRC, LANE
GUNS=[('pistol',4,'BrutalPistol','C','A'),('flamethrower',7,'Flamethrower2','E','B')]
def main(out,tint=None):
    tmp=os.path.join(LANE,'cache','testpack2'); shutil.rmtree(tmp,ignore_errors=True); shutil.copytree(SRC,tmp)
    fb=os.path.join(tmp,'models','rsq','fbx'); os.makedirs(fb)
    im=Image.open((_DP.FBX_TEX + '/lambert1_Base_Color.png')).convert('RGB').resize((512,512),Image.LANCZOS)
    if tint:   # the glove question: a flat multiply toward Ermac's glove colour (measured from 1.92 hand.png, see REPORT.md)
        a=np.asarray(im,float)*np.asarray(json.loads(tint),float)[None,None,:]; im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
    im.save(os.path.join(fb,'fbx_hand.png'))
    md=open(os.path.join(tmp,'MODELDEF.rsq'),encoding='latin-1').read()
    ht=os.path.join(tmp,'zscript','rsq','handtable.zs'); t=open(ht).read()
    GM=json.load(open(os.path.join(LANE,'results','gun_modeldef_C.json')))
    bd=open(os.path.join(tmp,'MODELDEF.bd.txt'),encoding='latin-1').read()
    for slug,row,cls,trg,sup in GUNS:
        R=json.load(open(os.path.join(LANE,'results',f'{slug}_report.json'))); rows={r['side']:r for r in R['bake']}
        for s,r in rows.items(): shutil.copy(os.path.join(LANE,'out',r['md3']),os.path.join(fb,r['md3']))
        for pat in (rf'\tFrameIndex RQGT {trg} 0 \d+[^\n]*\n',rf'\tFrameIndex RQGU {trg} 0 \d+[^\n]*\n',rf'\tFrameIndex RQSP {sup} 0 \d+[^\n]*\n'):
            md,n=re.subn(pat,'',md); assert n==1,(pat,n)
        md+=f'''
// lane_c TEST round 2: baked FBX hand on {cls} (RQGT {trg} / RQGU {trg} gun hand, RQSP {sup} support)
Model RSQ_GunSide
{{
	Path "models/rsq/fbx"
	Model 0 "{rows['R']['md3']}"
	Skin 0 "fbx_hand.png"
	Scale -1.0 1.0 1.0
	Offset 0.0 -24.0 -10.0
	FrameIndex RQGT {trg} 0 {rows['R']['frame']}
	FrameIndex RQGU {trg} 0 {rows['R']['frame']}
}}
Model RSQ_GunSide
{{
	Path "models/rsq/fbx"
	Model 0 "{rows['L']['md3']}"
	Skin 0 "fbx_hand.png"
	Scale -1.0 1.0 1.0
	Offset 0.0 -24.0 -10.0
	FrameIndex RQSP {sup} 0 {rows['L']['frame']}
}}
'''
        t=patch_row(t,'GunHook',row,rows['R']['hook']); t=patch_row(t,'GunRot',row,rows['R']['rot'])
        t=patch_row(t,'SupportHook',row,rows['L']['hook']); t=patch_row(t,'SupportRot',row,rows['L']['rot'])
        g=GM[cls]
        m=re.search(r'Model '+cls+r'\n\{\n   Path "models/bd/'+cls+r'"\n   Model 0 "'+cls+r'\.md3"\n(.*?)\n\}',bd,re.S); assert m,cls
        body=m.group(1)
        body=re.sub(r'   Offset 0\.0 0\.0 0\.0','   Offset %.3f %.3f 0.0\n   AngleOffset %.3f\n   PitchOffset %.3f\n   RollOffset %.3f   // lane_c TEST round 2: gun to the hand'%(g['Offset'][0],g['Offset'][1],g['AngleOffset'],g['PitchOffset'],g['RollOffset']),body,count=1)
        body=re.sub(r'   ZOffset -5\b','   ZOffset %.3f'%g['ZOffset'],body,count=1)
        bd=bd[:m.start(1)]+body+bd[m.end(1):]
    open(os.path.join(tmp,'MODELDEF.rsq'),'w',encoding='latin-1').write(md); open(ht,'w').write(t)
    open(os.path.join(tmp,'MODELDEF.bd.txt'),'w',encoding='latin-1').write(bd)
    if os.path.exists(out): os.remove(out)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for root,_,files in os.walk(tmp):
            for f in files: p=os.path.join(root,f); z.write(p,os.path.relpath(p,tmp))
    print(out,os.path.getsize(out))
if __name__=='__main__': main(*sys.argv[1:3])
