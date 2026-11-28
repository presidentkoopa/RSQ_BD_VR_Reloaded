"""sheets/fbx_poses.png: every held pose in hand_final.fbx's single take (Take 001, 1279 frames at 60 fps), both
hands, textured with lambert1_Base_Color.png. Held = joint motion < 0.004 units/frame for >= 4 frames
(poses_auto.json). Curl per finger = angle (deg) between the base->mid and mid->tip bones."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, json, numpy as np
from PIL import Image, ImageDraw
import fbxhand, render
FBX=_DP.FBX
TEX=(_DP.FBX_TEX + '/lambert1_Base_Color.png')
def face_colours(h,tex):
    T=np.asarray(Image.open(tex).convert('RGB').resize((512,512)),float)
    uv=h.uv_corner[h.Fc].mean(1); x=(uv[:,0]%1*511).astype(int); y=((1-uv[:,1]%1)*511).astype(int)
    return T[y,x]
def curl(J,f):
    p=J[f+'_BASE_joint'][:3,3]; m=J[f+'_MID_joint'][:3,3]; t=J[f+'_UP_TOP_joint'][:3,3]
    a=m-p; b=t-m; return float(np.degrees(np.arccos(a@b/np.linalg.norm(a)/np.linalg.norm(b))))
if __name__=='__main__':
    segs=json.load(open(sys.argv[1]))['segs']; out=sys.argv[2]
    H=[fbxhand.Hand(FBX,w) for w in (0,1)]; cols=face_colours(H[0],TEX)
    # merge consecutive segments with the same pose for both hands
    groups=[]
    for a,b in segs:
        f=(a+b)//2; sig=tuple(round(curl(h.joints_in(f,'HANDPALM_joint'),x)/5) for h in H for x in ('INDEX','MIDDLE_F','RING','PINK','THUMB'))
        if groups and groups[-1][2]==sig: groups[-1][1]=b; groups[-1][3].append((a,b))
        else: groups.append([a,b,sig,[(a,b)]])
    tiles=[]
    for a,b,sig,parts in groups:
        f=(parts[0][0]+parts[0][1])//2
        for w,h in enumerate(H):
            J=h.joints_in(f,'HANDPALM_joint'); V=h.skin(f,'HANDPALM_joint')*10
            Fm=h.F
            if w==1: V[:,1]*=-1; Fm=h.F[:,::-1]
            c=[round(curl(J,x)) for x in ('INDEX','MIDDLE_F','RING','PINK','THUMB')]
            for nm,eye in (('palm',(6,0,-25) if w==0 else (6,0,-25)),('side',(6,-25,0) if w==0 else (6,25,0))):
                rng=' + '.join(f'{p}-{q}' for p,q in parts[:3])+(' ...' if len(parts)>3 else '')
                im=render.render([dict(V=V,F=Fm,fcol=cols)],eye=eye,look=(6,0,0),W=230,H=190,fov=45,title=f'{"R" if w==0 else "L"} {nm}  fr {rng}',light=(0.3,0.5,0.8))
                ImageDraw.Draw(im).text((4,4),'curl I/M/R/P/T '+'/'.join(map(str,c)),fill=(255,255,180))
                tiles.append(im)
    S=render.sheet(tiles,8)
    hdr=Image.new('RGB',(S.width,40),(20,20,28)); d=ImageDraw.Draw(hdr)
    d.text((6,4),'hand_final.fbx (Maya 2019, FBX 7.5, 2020-06-24): 2 skinned meshes (Hand_Low R, Hand_Low1 L; 1667 verts, 1680 polys each), 22-joint rig each, one take 1279 frames @60fps.',fill=(255,255,255))
    d.text((6,20),'Held poses below (frames where the joints are still); each row = one pose, R and L hand, palm and side views. Curl = degrees between proximal and distal bones.',fill=(200,200,200))
    F=Image.new('RGB',(S.width,S.height+40)); F.paste(hdr,(0,0)); F.paste(S,(0,40)); F.save(out); print(out,F.size,len(groups),'pose groups')
