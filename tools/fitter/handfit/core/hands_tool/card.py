"""Each gun's round-2 result as the RS Avatar card contract (GUNS_IN_AVATAR_HANDS.md): palm, triggerat, supportat,
rake, seat (main hand) + supportaxis, supporthold, and the named poses (their names), in TWO frames:
  * gun-mesh frame: the gun's md3 file space (+X muzzle, +Y left, +Z up), units = md3 units (the cards' space);
  * controller frame (F/L/U cm) as QZD draws it, for the psprite layer.
Every point is MEASURED on the solved hands (landmark vertices) and moved into the gun's frames; poses are named by
nearest FBX frame per finger (avatar_poses.py, the frames listed in their fbx_poses.json), deg = rms over the
finger's 3 joints. Also: Quest cost per pose (MD3 bytes per frame), and Ermac's glove colour for the glove question."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import numpy as np, json, os, sys
from scipy.spatial.transform import Rotation as Rot
from PIL import Image
import solve, scene, hudrender, gunview, avatar_poses as AP, handmodel, evaluate
LANE=solve.LANE
CFG={'BrutalPistol':('BrutalPistol','BrutalPistol_gunhand','BrutalPistol_support_C.json','cup','pistol'),
     'Flamethrower2':('Flamethrower2@nozzle','Flamethrower2_nozzle_gunhand','Flamethrower2_nozzle_support_C3.json','vgrip','flamethrower')}
def flu_to_md3(cls,P):
    """controller-frame cm -> gun md3 file units (inverse of the 1.92 placement; hook/rot 0)"""
    it=scene.GUNS[cls]; V=np.concatenate([s['xyz'][it['frame']] for s in scene.md3_full(it['path'])])
    F=gunview.to_fl(hudrender.to_local(V,it)); A=np.c_[F,np.ones(len(F))]
    M,*_=np.linalg.lstsq(A,V,rcond=None); r=np.abs(A@M-V).max()
    return (np.c_[np.atleast_2d(P),np.ones(len(np.atleast_2d(P)))]@M), M[:3], float(r)
def main():
    FR,COMP=AP.frames_R_all(); out={}
    for cls,(lm,gf,sf,hold,slug) in CFG.items():
        d=json.load(open(os.path.join(LANE,'results',gf+'.json')))['C']; x=np.array(d['x'])
        ctx=solve.Ctx(lm,'R',None,'gunhand'); X,J=solve.hand_X(ctx,x); Rg,tg=solve.gun_T(ctx,x)
        g=lambda P:(np.asarray(P)-ctx.c-tg)@Rg+ctx.c          # controller frame -> gun's 1.92 frame
        sp=json.load(open(os.path.join(LANE,'results',sf))); sctx=solve.Ctx(lm,'L',None,hold); Xs,Js=solve.hand_X(sctx,np.array(sp['x']))
        L=ctx.L; v=lambda XX,k:XX[evaluate.reg(L,k)].mean(0)
        G=ctx.G; S=ctx.S
        pts={'palm':g(v(X,'palm')),'triggerat':g(v(X,'pad_I')),'seat':g(v(X,'web')),'supportat':v(Xs,'palm') if hold=='cup' else np.asarray(S['c'])}
        # rake: the handle's angle from vertical in the gun's side plane (gun file space, md3 X fwd Z up), as the cards state it
        ga=np.asarray(G['grip_axis']); _,Mlin,res=flu_to_md3(cls,np.zeros(3)); gam=ga@Mlin; gam/=np.linalg.norm(gam)
        rake=float(np.degrees(np.arctan2(gam[0],gam[2])))   # their convention (gun_fit_preview.grip_frame): handle-down H = (-sin rake, 0, -cos rake) = -grip_axis
        if hold=='vgrip': sax=np.asarray(S['axis'])@Mlin; sax/=np.linalg.norm(sax)
        else:   # cup: the support fingers wrap round the GUN HAND's front: the grip axis
            sax=gam
        md3={k:flu_to_md3(cls,p)[0][0].round(3).tolist() for k,p in pts.items()}
        # named poses (per finger nearest FBX frame) for the gun hand (right = rig0 frames are 'A'/'both') and the support hand
        names={}
        for tag,H,q in (('gun hand',ctx.H,x[6:24]),('support hand',sctx.H,np.array(sp['x'])[6:24])):
            per,Rq=AP.name_hand(H,q,None,FR)
            comp=sorted(((n,AP.composed_dist(Rq,FR,f)) for n,f in COMP.items()),key=lambda t:t[1])[:3]
            names[tag]=dict(per_finger=per,nearest_composed=[(n,round(dd,1)) for n,dd in comp])
        pose_main='trigger'; pose_sup=hold
        card=dict(palm=md3['palm'],triggerat=md3['triggerat'],seat=md3['seat'],supportat=md3['supportat'],rake=round(rake,1),
                  supportaxis=np.round(sax,3).tolist(),supporthold=hold,poses={'trigger':'gun hand as solved (index on the trigger face)','squeeze':'NOT SOLVED this round (1.92 uses the same frame for RQGU; see REPORT)',hold:'support hand as solved'},
                  frame_note='gun md3 file space of the 1.92 mesh frame drawn at ready (%s frame %d), md3 units; fit residual of the inverse placement %.1e'%(os.path.basename(scene.GUNS[cls]['path']),scene.GUNS[cls]['frame'],res))
        ctrl={k:np.round(p,2).tolist() for k,p in pts.items()}
        out[cls]=dict(card=card,controller_frame_cm_in_gun_192_frame=ctrl,named=names)
        print(cls,json.dumps(card)); print('  names',json.dumps(names))
    # Quest cost per pose: one MD3 vertex frame of the baked hand
    for p in sorted(os.listdir(os.path.join(LANE,'out'))):
        if p.endswith('.md3'):
            s=scene.md3_full(os.path.join(LANE,'out',p))[0]; nv=s['xyz'].shape[1]; nf=s['xyz'].shape[0]; nt=len(s['tris'])
            out.setdefault('quest_cost',{})[p]=dict(frames=nf,verts=nv,tris=nt,bytes_per_frame=nv*8+56,file_bytes=os.path.getsize(os.path.join(LANE,'out',p)))
    for p in ('hand.md3','hand2.md3'):
        s=scene.md3_full(os.path.join(LANE,'bd22q_192','models','rsq',p)); nv=sum(x['xyz'].shape[1] for x in s); nt=sum(len(x['tris']) for x in s)
        out.setdefault('quest_cost',{})['1.92 '+p]=dict(frames=s[0]['xyz'].shape[0],verts=nv,tris=nt,bytes_per_frame=nv*8+56,file_bytes=os.path.getsize(os.path.join(LANE,'bd22q_192','models','rsq',p)))
    # glove: Ermac's hand.png vs the FBX base colour (mean RGB over the texture's covered texels)
    def meanrgb(p):
        a=np.asarray(Image.open(p).convert('RGBA'),float); m=a[...,3]>0; m&=a[...,:3].sum(-1)>15
        return np.round(a[...,:3][m].mean(0),1).tolist(), np.round(np.median(a[...,:3][m],0),1).tolist()
    out['glove']=dict(ermac_hand_png=meanrgb(os.path.join(LANE,'bd22q_192','models','rsq','hand.png')),
                      fbx_base_color=meanrgb((_DP.FBX_TEX + '/lambert1_Base_Color.png')))
    print(json.dumps(out['quest_cost'],indent=0)); print(out['glove'])
    json.dump(out,open(os.path.join(LANE,'results','cards_round2.json'),'w'),indent=1)
if __name__=='__main__': main()
