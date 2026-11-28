"""Round 3 bake: the final hands (results/round3_final.json, gun's 1.92 frame) moved with the gun into the controller
frame and written as MD3 frames with NO hand-table hook/rot (identity: the frame IS where the hand is drawn), so the
same frames serve RSQ_GunSide (hand table hook 0, rot 0) and the dual-wield blocks (Offset = Ermac placement 0 -24 -10).
out/fbx_r3_gun.md3: frame 0 pistol, 1 flamethrower (gun hand, right rig); out/fbx_r3_sup.md3 likewise (support, left rig).
Sprites (new, unused anywhere in the pack / BD22 / BD_VoxelPack): RQFG A pistol trigger, B pistol squeeze, C flamer
trigger, D flamer squeeze (squeeze = trigger frame: no squeeze pose solved); RQFS A pistol support, B flamer support."""
import numpy as np, json, os
import solve, bake
LANE=solve.LANE
def main():
    R=json.load(open(os.path.join(LANE,'results',os.environ.get('LANEC_FINAL','round3_final.json')))); ents=[]
    for cls,lm,hold in (('BrutalPistol','BrutalPistol','cup'),('Flamethrower2','Flamethrower2@nozzle','vgrip')):
        o=R[cls]; g=solve.Ctx(lm,'R',None,'gunhand'); x=np.array(o['x_gun']); Rg,tg=solve.gun_T(g,x)
        Xg=solve.gmove(g,Rg,tg,np.array(o['Xg'])); Xs=solve.gmove(g,Rg,tg,np.array(o['Xs']))
        Lc=g.cuff
        ents.append(dict(name=cls[:6]+'_gun',side='R',X=Xg,cuff_ref=Xg[Lc])); ents.append(dict(name=cls[:6]+'_sup',side='L',X=Xs,cuff_ref=Xs[Lc]))
    if os.environ.get('LANEC_SQUEEZE'):   # round 5: squeeze frames appended (R md3 frame 2 pistol, 3 flamer)
        SQ=json.load(open(os.path.join(LANE,'results',os.environ.get('LANEC_SQFILE','squeeze_r5.json'))))
        for cls,lm in (('BrutalPistol','BrutalPistol'),('Flamethrower2','Flamethrower2@nozzle')):
            o=R[cls]; g=solve.Ctx(lm,'R',None,'gunhand'); x=np.array(o['x_gun']); Rg,tg=solve.gun_T(g,x)
            Xq=solve.gmove(g,Rg,tg,np.array(SQ[cls]['Xsq'])); ents.append(dict(name=cls[:6]+'_sqz',side='R',X=Xq,cuff_ref=Xq[g.cuff]))
    rows,paths,_=bake.bake(ents,os.path.join(LANE,'out',os.environ.get('LANEC_MD3','fbx_r3')+'.md3'))
    for r in rows: print(r['name'],r['side'],'frame',r['frame'],'hook',r['hook'],'rot',r['rot'],'bake check %.4f cm'%r['bake_check_max_cm'],r['md3'])
    json.dump(rows,open(os.path.join(LANE,'results','bake_'+os.environ.get('LANEC_MD3','fbx_r3')+'.json'),'w'),indent=1)
if __name__=='__main__': main()
