"""Round 3 headset pack: BD22Q 1.92 with ONLY BrutalPistol (hand-table row 4) and Flamethrower2 (row 7) changed.
Every edit is listed in out/headset_manifest.json (file, what, before, after). TEST/prototype: never committed anywhere.

Edits
 A. hands: new sprites RQFG (gun hand) / RQFS (support) on RSQ_GunSide + RSQ_Hands (dual wield) and their Model blocks
    (MODELDEF.rsq), states FbxTrgP/FbxSqzP/FbxTrgF/FbxSqzF/FbxSupP/FbxSupF and DFbx.. (hands.zs); hands.zs picks them for
    rows 4 / 7 only (gunhand label, support label); dualhands.zs picks DFbx.. for rows 4 / 7. Hand table rows 4 and 7:
    GunHook/GunRot/SupportHook/SupportRot = 0 (the frames are baked where they are drawn). handtable.zs Support(4) stays
    "A" (hands.zs 227: the cup-by-closeness rule keys on it), Trigger(4)/(7) stay (dual wield / other code read them).
 B. the gun model: every MODELDEF block that draws BrutalPistol.md3 / Flamethrower2.md3 on a HUD layer gets the round-3
    placement (results/gun_modeldef_R3.json: Offset, ZOffset, Angle/Pitch/RollOffset; fit residual < 1e-13 cm):
    MODELDEF.bd.txt BrutalPistol / Flamethrower2, MODELDEF.purist PuristPistol / PuristFlamethrower2 + PuristPistol RQPM x2,
    MODELDEF.rsqoff RSQ_Off_BrutalPistol (gun) + its RQPM x3, MODELDEF.rsr BrutalPistol RQPM x3, RSR_GunParts RQPP x2,
    RSQ_Hands RQPP (the magazine in the off hand: hooked by HandHook in the off-hand frame, NOT the gun: left alone, see
    below). Not changed: RSR_DroppedMag (a world actor), the voxel/pickup models (world), nade/boot/fist blocks (they
    draw other meshes in the hand's place, not the gun).
 C. RSQ_GunMoves (gunmoves.zs): Pivot(4)/(7) = S (gun offset - hand offset) and the recoil rows 15,16,17 (pistol) and
    28,29 (flamer), recomputed for the new placement (gunmoves3.py; reproduces the shipped rows exactly at 1.92's).
 D. RSR real reload, BrutalPistol (RSR gun 2): Well, Axis, MagCentre, Grab, Pull moved with the gun (rigid: point
    p' = Rg (p - c) + c + tg, direction d' = Rg d, controller frame cm); WellHook / HandleHook (ModifyBobLayer3D units in
    the gun model's frame) turned with the gun's model-frame turn; Offset(2) table = the new MODELDEF values.
    TopInHand / HandHook are in the OFF hand's frame (the magazine held in the hand): unchanged.
 E. casings.zs Port(BrutalPistol): the ejection port moved with the gun.
 F. muzzle / projectiles: BD22 fires from AttackPos (the controller) along the controller aim (p_mobj.cpp 7331-7342,
    p_map.cpp 4597-4608), and its PlayerMuzzle1 / FlamethrowerProjectile spawn offsets are BD22's own (brutal22test6,
    not edited). There is no flash or muzzle table in the 1.92 pack for these guns (searched: zscript, MODELDEF). The
    gun model's muzzle moves with the new placement (pistol 9.7 cm, flamer 9.6 cm); the shot does not. Reported.
usage: headsetpack.py <out.pk3> [--rows-only]"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import json, os, re, shutil, sys, zipfile, hashlib
import numpy as np
from scipy.spatial.transform import Rotation as Rot
from PIL import Image
LANE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD3=os.environ.get('LANEC_MD3','fbx_r3'); FINAL=os.environ.get('LANEC_FINAL','round3_final.json'); MANI=os.environ.get('LANEC_MANI','headset_manifest.json'); SQZ=bool(os.environ.get('LANEC_SQUEEZE')); SQP='2' if SQZ else '0'; SQF='3' if SQZ else '1'
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import solve, gunmoves3, hook as HK
SRC=_DP.GUNPACK192
MAN=[]
def note(f,what,before,after): MAN.append(dict(file=f,what=what,before=before,after=after))
def sub1(txt,old,new,f,what):
    n=txt.count(old); assert n==1,(f,what,n); note(f,what,old.strip()[:200],new.strip()[:200]); return txt.replace(old,new)
def gun_move(cls):
    lm={'BrutalPistol':'BrutalPistol','Flamethrower2':'Flamethrower2@nozzle'}[cls]
    R=json.load(open(os.path.join(LANE,'results',FINAL)))[cls]; ctx=solve.Ctx(lm,'R',None,'gunhand')
    Rg,tg=solve.gun_T(ctx,np.array(R['x_gun'])); return ctx,Rg,tg
def fmt(v): return '%.3f'%v
def patch_md_block(txt,f,blk,md,label):
    """set Offset/ZOffset/Angle/Pitch/RollOffset inside one Model block text span"""
    s,e=blk; body=txt[s:e]; nb=body
    nb,n=re.subn(r'(?im)^(\s*)Offset\s+\S+\s+\S+\s+\S+',lambda m:m.group(1)+'Offset %s %s 0.0'%(fmt(md['Offset'][0]),fmt(md['Offset'][1])),nb,count=1); assert n==1,(f,label)
    nb,n=re.subn(r'(?im)^(\s*)ZOffset\s+\S+',lambda m:m.group(1)+'ZOffset %s'%fmt(md['ZOffset']),nb,count=1); assert n==1,(f,label,'z')
    for k in ('AngleOffset','PitchOffset','RollOffset'): assert not re.search(r'(?im)^\s*'+k,nb),(f,label,k)
    ind=re.search(r'(?im)^(\s*)ZOffset',nb).group(1)
    nb=re.sub(r'(?im)^(\s*ZOffset[^\n]*)',lambda m:m.group(1)+'\n%sAngleOffset %s\n%sPitchOffset %s\n%sRollOffset %s\t// lane_c R3: gun to the FBX hand'%(ind,fmt(md['AngleOffset']),ind,fmt(md['PitchOffset']),ind,fmt(md['RollOffset'])),nb,count=1)
    note(f,'gun placement: '+label,re.sub(r'\s+',' ',body[:0]+' '.join(re.findall(r'(?im)^\s*(?:Offset|ZOffset)[^\n]*',body))).strip(),'Offset %s %s, ZOffset %s, Angle/Pitch/Roll %s %s %s'%(fmt(md['Offset'][0]),fmt(md['Offset'][1]),fmt(md['ZOffset']),fmt(md['AngleOffset']),fmt(md['PitchOffset']),fmt(md['RollOffset'])))
    return txt[:s]+nb+txt[e:]
def blocks(txt):
    import mdblocks
    return mdblocks.blocks(txt)
def main(out):
    tmp=os.path.join(LANE,'cache','headset'); shutil.rmtree(tmp,ignore_errors=True); shutil.copytree(SRC,tmp)
    GM=json.load(open(os.path.join(LANE,'results',os.environ.get('LANEC_GM','gun_modeldef_R3.json'))))
    # ---- A. hand models + skin
    fb=os.path.join(tmp,'models','rsq','fbx'); os.makedirs(fb)
    for s in 'RL': shutil.copy(os.path.join(LANE,'out',f'{MD3}_{s}.md3'),os.path.join(fb,f'fbx_r3_{s}.md3'))
    note('models/rsq/fbx/fbx_r3_%s.md3'%s,'source',MD3+'_%s.md3'%s,'packed under the round-3 name') if MD3!='fbx_r3' else None
    Image.open((_DP.FBX_TEX + '/lambert1_Base_Color.png')).convert('RGB').resize((512,512),Image.LANCZOS).save(os.path.join(fb,'fbx_hand.png'))
    note('models/rsq/fbx/','add: fbx_r3_R.md3 (gun hands: frame 0 pistol, 1 flamer), fbx_r3_L.md3 (support), fbx_hand.png (FBX base colour, 512 px)','-','added')
    blk='''
// lane_c R3 (prototype): the FBX hands on BrutalPistol (row 4) and Flamethrower2 (row 7) only. Frames baked where
// they are drawn (hand-table hook 0): Ermac's placement Scale -1 1 1, Offset 0 -24 -10. New sprites RQFG / RQFS.
Model %s
{
	Path "models/rsq/fbx"
	Model 0 "fbx_r3_R.md3"
	Skin 0 "fbx_hand.png"
	Scale -1.0 1.0 1.0
	Offset 0.0 -24.0 -10.0
	FrameIndex RQFG A 0 0	// pistol, finger on the trigger
	FrameIndex RQFG B 0 %(SQP)s	// pistol, squeezed
	FrameIndex RQFG C 0 1	// flamethrower, finger on the trigger
	FrameIndex RQFG D 0 %(SQF)s	// flamethrower, squeezed
}
Model %s
{
	Path "models/rsq/fbx"
	Model 0 "fbx_r3_L.md3"
	Skin 0 "fbx_hand.png"
	Scale -1.0 1.0 1.0
	Offset 0.0 -24.0 -10.0
	FrameIndex RQFS A 0 0	// pistol cup
	FrameIndex RQFS B 0 1	// flamethrower support (round 3: fist on the riser bar; round 4: open palm under the tank)
}
'''
    p=os.path.join(tmp,'MODELDEF.rsq'); t=open(p,encoding='latin-1').read(); blk=blk.replace('%(SQP)s',SQP).replace('%(SQF)s',SQF); t+=blk%('RSQ_GunSide','RSQ_GunSide')+blk%('RSQ_Hands','RSQ_Hands'); open(p,'w',encoding='latin-1').write(t)
    note('MODELDEF.rsq','append Model blocks RSQ_GunSide (RQFG A-D, RQFS A-B) and RSQ_Hands (same, for dual wield)','-','appended')
    # dual wield blocks of the guns' own classes (the dual hand layer is called by the gun): MODELDEF.rsqdual / rsqoff / purist
    dual='''
// lane_c R3: dual wield, the FBX hand (the layer is called by the gun, so the block is the gun's class)
Model %s
{
	Path "models/rsq/fbx"
	Model 0 "fbx_r3_R.md3"
	Skin 0 "fbx_hand.png"
	Scale -1.0 1.0 1.0
	Offset 0.0 -24.0 -10.0
	FrameIndex RQFG A 0 0
	FrameIndex RQFG B 0 %(SQP)s
	FrameIndex RQFG C 0 1
	FrameIndex RQFG D 0 %(SQF)s
}
'''
    dual=dual.replace('%(SQP)s',SQP).replace('%(SQF)s',SQF)
    for f,classes in (('MODELDEF.rsqdual',('BrutalPistol','Flamethrower2')),('MODELDEF.rsqoff',('RSQ_Off_BrutalPistol',)),('MODELDEF.purist',('PuristPistol','PuristFlamethrower2'))):
        p=os.path.join(tmp,f); t=open(p,encoding='latin-1').read(); t+=''.join(dual%c for c in classes); open(p,'w',encoding='latin-1').write(t)
        note(f,'append dual-wield FBX hand block(s): '+', '.join(classes),'-','appended')
    # hands.zs: states + selection for rows 4 / 7
    p=os.path.join(tmp,'zscript','rsq','hands.zs'); t=open(p).read()
    t=sub1(t,'\tSupF: RQSP F -1; Stop;\n','\tSupF: RQSP F -1; Stop;\n\t// lane_c R3: the FBX hands (rows 4 BrutalPistol, 7 Flamethrower2)\n\tFbxTrgP: RQFG A -1; Stop;\n\tFbxSqzP: RQFG B -1; Stop;\n\tFbxTrgF: RQFG C -1; Stop;\n\tFbxSqzF: RQFG D -1; Stop;\n\tFbxSupP: RQFS A -1; Stop;\n\tFbxSupF: RQFS B -1; Stop;\n','zscript/rsq/hands.zs','RSQ_GunSide states for the FBX hands')
    t=sub1(t,'\tDGunH: RQGS H -1; Stop;','\tDGunH: RQGS H -1; Stop;\n\tDFbxTrgP: RQFG A -1; Stop;\t// lane_c R3: dual wield, the FBX hands\n\tDFbxSqzP: RQFG B -1; Stop;\n\tDFbxTrgF: RQFG C -1; Stop;\n\tDFbxSqzF: RQFG D -1; Stop;','zscript/rsq/hands.zs','RSQ_Hands dual-wield states for the FBX hands')
    old='\t\tString gl = tf != "" ? ((p.cmd.buttons & BT_ATTACK) ? "Sqz" .. tf : "Trg" .. tf) : "Gun" .. g;\n'
    new=old+'\t\tif (i == 4 || i == 7)\t// lane_c R3: the FBX hands on BrutalPistol / Flamethrower2\n\t\t\tgl = ((p.cmd.buttons & BT_ATTACK) ? "FbxSqz" : "FbxTrg") .. (i == 4 ? "P" : "F");\n'
    if SQZ: new=old+('\t\tif (i == 4 || i == 7)\t// lane_c R3/R5: the FBX hands; R5: squeeze on the gun\'s FIRE tics (the frames its Fire / Hold states show), trigger otherwise\n'
        '\t\t{\n\t\t\tbool fsq = false;\n\t\t\tlet fgp = p.FindPSprite(PSP_WEAPON);\n'
        '\t\t\tif (fgp && fgp.CurState)\n\t\t\t{\n\t\t\t\tint ff = fgp.Frame;\n'
        '\t\t\t\tif (i == 4)\t// BD22 Pistol.dec ResumeFireFrame / Fire2: "####" A 1 BRIGHT (the shot), then B, C, D 1\n'
        '\t\t\t\t\tfsq = (fgp.Sprite == Actor.GetSpriteIndex(\'PIST\') || fgp.Sprite == Actor.GetSpriteIndex(\'2IST\')) && (fgp.CurState.bFullbright || ff == 1 || ff == 2 || ff == 3);\n'
        '\t\t\t\telse\t// BD22 Flamethrower.dec Fire / Hold: D E G H 1 BRIGHT\n'
        '\t\t\t\t\tfsq = (fgp.Sprite == Actor.GetSpriteIndex(\'FLMT\') || fgp.Sprite == Actor.GetSpriteIndex(\'2LMT\')) && (fgp.CurState.bFullbright || ff == 3 || ff == 4 || ff == 6 || ff == 7);\n'
        '\t\t\t}\n\t\t\tgl = (fsq ? "FbxSqz" : "FbxTrg") .. (i == 4 ? "P" : "F");\n\t\t}\n')
    t=sub1(t,old,new,'zscript/rsq/hands.zs','gun-hand label for rows 4 / 7')
    old='\t\tinvoker.SetLayer(p, RSQ_Layers.SUPPORT, gs, hold && sp != "" ? "Sup" .. sp : "Hidden");'
    new='\t\tString spl = (i == 4 || i == 7) ? (i == 4 ? "FbxSupP" : "FbxSupF") : "Sup" .. sp;\t// lane_c R3\n\t\tinvoker.SetLayer(p, RSQ_Layers.SUPPORT, gs, hold && sp != "" ? spl : "Hidden");'
    t=sub1(t,old,new,'zscript/rsq/hands.zs','support label for rows 4 / 7')
    open(p,'w').write(t)
    p=os.path.join(tmp,'zscript','rsq','dualhands.zs'); t=open(p).read()
    old='\t\t\t\tlabel = tf != "" ? (firing ? "DSqz" : "DTrg") .. tf : "DGun" .. RSQ_HandTable.GunOne(i);\n'
    new=old+'\t\t\t\tif (i == 4 || i == 7)\t// lane_c R3: the FBX hands\n\t\t\t\t\tlabel = (firing ? "DFbxSqz" : "DFbxTrg") .. (i == 4 ? "P" : "F");\n'
    t=sub1(t,old,new,'zscript/rsq/dualhands.zs','dual-wield label for rows 4 / 7'); open(p,'w').write(t)
    # hand table rows 4 / 7: hooks 0
    import testpack
    p=os.path.join(tmp,'zscript','rsq','handtable.zs'); t=open(p).read()
    for row in (4,7):
        for fn in ('GunHook','GunRot','SupportHook','SupportRot'): t=testpack.patch_row(t,fn,row,(0,0,0))
        note('zscript/rsq/handtable.zs','row %d GunHook/GunRot/SupportHook/SupportRot'%row,'1.92 values','0 0 0 (frames baked in place)')
    open(p,'w').write(t)
    # ---- B. gun MODELDEF placement
    import mdblocks
    for f in ('MODELDEF.bd.txt','MODELDEF.purist','MODELDEF.rsqoff','MODELDEF.rsr'):
        p=os.path.join(tmp,f); t=open(p,encoding='latin-1').read()
        # walk blocks from the end so spans stay valid
        bl=[b for b in mdblocks.blocks(t)]
        for b in reversed(bl):
            path=' '.join(b['path']).lower(); mdl=' '.join(b['model']).lower()
            for cls,m3 in (('BrutalPistol','brutalpistol.md3'),('Flamethrower2','flamethrower2.md3')):
                if m3 in mdl and ('models/bd/'+cls.lower()) in path:
                    if b['name'] in ('RSR_DroppedMag',): continue          # world actor
                    if b['name']=='RSQ_Hands': continue                     # the magazine in the off hand (off-hand frame)
                    sc=' '.join(b['scale']).split()
                    if [float(a) for a in sc]!=[-1.0,1.0,1.0]: continue    # only the HUD placement (Scale -1 1 1)
                    t=patch_md_block(t,f,(b['start'],b['end']),GM[cls],'%s block "%s" line %d (%s)'%(cls,b['name'],b['line'],','.join(sorted(set(fr[0] for fr in b['frames'])))[:40]))
        open(p,'w',encoding='latin-1').write(t)
    # ---- C. gunmoves
    p=os.path.join(tmp,'zscript','rsq','gunmoves.zs'); t=open(p).read()
    m=re.search(r'(clearscope static Vector3 Pivot\(int i\)\s*\{\s*static const double v\[\] = \{ )([^}]*)( \};)',t)
    pv=[a.strip() for a in m.group(2).split(',')]
    fr=t.index('static Vector3, Vector3 Frame'); mv=re.search(r'(static const double v\[\] = \{)(.*?)(\};)',t[fr:],re.S)
    vals=re.findall(r'-?\d+\.\d+',mv.group(2)); vals=[float(a) for a in vals]
    for cls,row in (('BrutalPistol',4),('Flamethrower2',7)):
        rows,piv=gunmoves3.new_rows(cls,GM[cls])
        before=pv[3*row:3*row+3]; pv[3*row:3*row+3]=['%.3f'%a for a in piv]
        note('zscript/rsq/gunmoves.zs','Pivot(%d) %s'%(row,cls),' '.join(before),' '.join(pv[3*row:3*row+3]))
        for r,(turn,move) in rows.items():
            b=vals[6*r:6*r+6]; vals[6*r:6*r+6]=list(np.round(turn,2))+list(np.round(move,2))
            note('zscript/rsq/gunmoves.zs','recoil row %d (%s)'%(r,cls),' '.join('%.2f'%a for a in b),' '.join('%.2f'%a for a in vals[6*r:6*r+6]))
    t=t[:m.start(2)]+', '.join(pv)+t[m.end(2):]
    fr=t.index('static Vector3, Vector3 Frame'); mv=re.search(r'(static const double v\[\] = \{)(.*?)(\};)',t[fr:],re.S)
    body='\n'+''.join('\t\t\t'+', '.join('%.2f'%a for a in vals[6*k:6*k+6])+(',' if k<len(vals)//6-1 else '')+'\n' for k in range(len(vals)//6))+'\t\t'
    t=t[:fr+mv.start(2)]+body+t[fr+mv.end(2):]
    open(p,'w').write(t)
    # ---- D. RSR pistol (gun 2)
    ctx,Rg,tg=gun_move('BrutalPistol')
    P=lambda v:solve.gmove(ctx,Rg,tg,np.array(v,float)[None])[0]; D=lambda v:Rg@np.array(v,float)
    # model-frame turn of the gun, in ModifyBobLayer3D units of the gun model (local x right? use the hook chain): the
    # hooks are translations of a layer drawn with the gun's placement; under the new AngleOffsets the md3 axes turn by
    # J_g(new) J_g(old)^-1 relative to the hands' inner frame, so a hook vector h (old inner units) -> Jn Jo^-1 h.
    Jn=gunmoves3.J_of((GM['BrutalPistol']['AngleOffset'],GM['BrutalPistol']['PitchOffset'],GM['BrutalPistol']['RollOffset'])); Jo=gunmoves3.J_of()
    TJ=Jn@np.linalg.inv(Jo)
    p=os.path.join(tmp,'zscript','rsr','rsr_guns.bd.zs'); t=open(p).read()
    def setcase(t,fn,val,kind='v'):
        mm=re.search(r'(clearscope static \w+ '+fn+r'\(int i\)\s*\{\s*switch \(i\)\s*\{.*?case 2:\treturn )([^;]*)(;)',t,re.S); assert mm,fn
        before=mm.group(2); after='(%s)'%', '.join('%.3f'%a for a in val)
        note('zscript/rsr/rsr_guns.bd.zs','RSR pistol %s(2)'%fn,before,after); return t[:mm.start(2)]+after+t[mm.end(2):]
    def getcase(fn):
        mm=re.search(r'clearscope static \w+ '+fn+r'\(int i\)\s*\{\s*switch \(i\)\s*\{.*?case 2:\treturn \(([^)]*)\)',t,re.S); return [float(a) for a in mm.group(1).split(',')]
    for fn in ('Well','MagCentre','Grab'): t=setcase(t,fn,P(getcase(fn)))
    for fn in ('Axis','Pull'): t=setcase(t,fn,D(getcase(fn)))
    for fn in ('WellHook','HandleHook'): t=setcase(t,fn,TJ@np.array(getcase(fn)))
    g=GM['BrutalPistol']; t=setcase(t,'Offset',(g['Offset'][0],g['Offset'][1],g['ZOffset']))
    open(p,'w').write(t)
    # ---- E. casings
    p=os.path.join(tmp,'zscript','rsq','casings.zs'); t=open(p).read()
    pt=P((-1.0,-1.0,1.3)); t=sub1(t,"if (w is 'BrutalPistol')\t\treturn (-1.0, -1.0, 1.3);","if (w is 'BrutalPistol')\t\treturn (%.1f, %.1f, %.1f);\t// lane_c R3: moved with the gun"%tuple(pt),'zscript/rsq/casings.zs','BrutalPistol ejection port'); open(p,'w').write(t)
    # ---- G. round 6: the flame starts at the drawn spout tip (owner: weapon code may change; only the start point)
    if os.environ.get('LANEC_FLAMESPOUT'):
        tip=json.load(open(os.path.join(LANE,'results',FINAL)))['Flamethrower2']['tip_controller_cm']
        z=open(os.path.join(LANE,'pack_extra','zscript','rsq','flamespout.zs')).read().replace('%TIPF%','%.2f'%tip[0]).replace('%TIPL%','%.2f'%tip[1]).replace('%TIPU%','%.2f'%tip[2])
        open(os.path.join(tmp,'zscript','rsq','flamespout.zs'),'w').write(z); note('zscript/rsq/flamespout.zs','add: RSA_FlameSpout (flame projectiles start at the drawn spout tip, F L U cm %s)'%[round(a,2) for a in tip],'-','added')
        p=os.path.join(tmp,'ZSCRIPT.rsvr'); t=open(p).read(); t=sub1(t,'#include "zscript/rsq/casings.zs"','#include "zscript/rsq/casings.zs"\n#include "zscript/rsq/flamespout.zs"\t// lane_c R6','ZSCRIPT.rsvr','include flamespout.zs'); open(p,'w').write(t)
        p=os.path.join(tmp,'MAPINFO.rsvr'); t=open(p).read(); t=sub1(t,'"RSA_Casings",','"RSA_Casings", "RSA_FlameSpout",','MAPINFO.rsvr','register RSA_FlameSpout'); open(p,'w').write(t)
    # ---- F. muzzle: measured, not editable here
    for cls in ('BrutalPistol','Flamethrower2'):
        c,R_,t_=gun_move(cls); b=np.array(c.G['bore_c']); nb=solve.gmove(c,R_,t_,b[None])[0]
        note('(none: BD22 actors)','%s muzzle: the shot spawns at the controller (AttackPos) along its aim; the drawn muzzle moved'%cls,str(b.round(2).tolist()),str(nb.round(2).tolist())+' (%.1f cm)'%np.linalg.norm(nb-b))
    if os.path.exists(out): os.remove(out)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        for root,_,files in os.walk(tmp):
            for f in sorted(files): pp=os.path.join(root,f); z.write(pp,os.path.relpath(pp,tmp))
    h=hashlib.sha256(open(out,'rb').read()).hexdigest()
    json.dump(dict(pk3=out,sha256=h,edits=MAN),open(os.path.join(LANE,'out',MANI),'w'),indent=1)
    for e in MAN: print('%-34s %-70s | %s -> %s'%(e['file'],e['what'][:70],str(e['before'])[:60],str(e['after'])[:60]))
    print(out,os.path.getsize(out),h)
if __name__=='__main__': main(sys.argv[1])
