"""Shared scene for lane_c: what QZD draws for a gun and its hands, in the controller frame (cm, F/L/U).
Placement chain = hudrender.to_local (copied from rsq_weapondepot/tools/kit, = models.cpp RenderHUDModel)."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, struct, numpy as np
import hudrender, gunview
L=os.path.dirname(os.path.abspath(__file__))
LANE=os.path.dirname(L)
P192=_DP.GUNPACK192
MS=_DP.MODELSWAPPER
ERMAC_PL=dict(scale=[-1.0,1.0,1.0],off=[0.0,-24.0,-10.0])
# hand.md3 index -> Ermac frame, from 1.92 MODELDEF.rsq comments (parsed by hand once; checked below)
def md3_full(path):
    """surfaces: list of dict(name, tris, xyz[nfr,nv,3] (md3 units), st[nv,2], shader)"""
    d=open(path,'rb').read()
    nfr,ntag,nsurf,nskin,ofr,otag,osurf,oeof=struct.unpack_from('<8i',d,76)
    out=[]; off=osurf
    for s in range(nsurf):
        name=d[off+4:off+68].split(b'\0')[0].decode('latin-1')
        flags,snfr,nsh,nv,nt,otri,osh,ost,oxyz,oend=struct.unpack_from('<10i',d,off+68)
        tris=np.frombuffer(d,'<i4',nt*3,off+otri).reshape(nt,3)
        raw=np.frombuffer(d,'<i2',snfr*nv*4,off+oxyz).reshape(snfr,nv,4)
        xyz=raw[:,:,:3].astype(float)/64.0
        st=np.frombuffer(d,'<f4',nv*2,off+ost).reshape(nv,2)
        sh=d[off+osh:off+osh+64].split(b'\0')[0].decode('latin-1') if nsh else ''
        out.append(dict(name=name,tris=tris.copy(),xyz=xyz,st=st.copy(),shader=sh,normal_raw=raw[:,:,3].copy()))
        off+=oend
    return out
def item_verts(it):
    """[(tris, V_flu_cm)] for an item dict (path, frame, scale, off, hook, rot)"""
    out=[]
    for s in md3_full(it['path']):
        v=gunview.to_fl(hudrender.to_local(s['xyz'][it['frame']],it))
        out.append((s['tris'],v))
    return out
def merged(it):
    T=[];V=[];n=0
    for t,v in item_verts(it): T.append(t+n); V.append(v); n+=len(v)
    return np.concatenate(T),np.concatenate(V)
GUNS={
 # cls: (md3 path, ready mesh frame, scale, off) -- parsed from 1.92 MODELDEF.bd.txt via pk3model (ready sprite PIST A / FLMT A)
 'BrutalPistol': dict(path=P192+'/models/bd/BrutalPistol/BrutalPistol.md3',frame=3,scale=[-1.0,1.0,1.0],off=[0.0,0.0,-5.0]),
 'Flamethrower2': dict(path=P192+'/models/bd/Flamethrower2/Flamethrower2.md3',frame=0,scale=[-1.0,1.0,1.0],off=[0.0,0.0,-5.0]),
}
HAND192=P192+'/models/rsq/hand.md3'; HAND2_192=P192+'/models/rsq/hand2.md3'
def letter_index(c): return ord(c)-ord('A')
# 1.92 MODELDEF.rsq RQGS letters -> hand.md3 frame index; RQSP -> hand2.md3 index; RQGT -> trigger frames
RQGS={'A':2,'B':3,'C':5,'D':6,'E':7,'F':8,'G':9,'H':4}
RQSP={'A':0,'B':1,'C':2,'D':3,'E':4}
RQGT={c:10+2*i for i,c in enumerate('ABCDEFGHIJKLMNOPQ')}

# ---- what each build draws (parsed rows; see REPORT.md for where each number was read) ----
MSR=_DP.MODELSWAPPER
BUILDS={
 # 1.92 = BD22Q tag 1.92 (bd22q_192/zscript/rsq/handtable.zs row 4 / 7, MODELDEF.rsq); BD22Q today has the same rows (checked)
 ('BrutalPistol','1.92'): dict(gun=GUNS['BrutalPistol'],hand=HAND192,gframe=RQGT['C'],ghook=(0.0,-5.02,3.18),grot=(0,0,0),
                               hand2=HAND2_192,sframe=RQSP['A'],shook=(0.0,-5.02,3.18),srot=(0,0,0)),
 ('Flamethrower2','1.92'): dict(gun=GUNS['Flamethrower2'],hand=HAND192,gframe=RQGT['E'],ghook=(0.22,-2.16,-1.64),grot=(0,0,0),
                               hand2=HAND2_192,sframe=RQSP['B'],shook=(-0.09,-12.71,-7.44),srot=(0,0,0)),
 # ModelSwapper today: handfit_report.json row MS_BD_Flamethrower2 (one F, sup B, trig O), modeldef block MS_BD_Flamethrower2,
 # MODELDEF.rsq RQGT O -> hand.md3 index 38, RQSP B -> hand2.md3 index 1
 ('Flamethrower2','ModelSwapper'): dict(gun=dict(path=MSR+'/models/hud/Flamethrower/Flamethrower2.md3',frame=0,scale=[-1.0,1.0,1.0],off=[-0.469,-57.031,-13.359]),
                               hand=MSR+'/models/rsq/hand.md3',gframe=38,ghook=(1.327,17.738,-0.666),grot=(0,0,0),
                               hand2=MSR+'/models/rsq/hand2.md3',sframe=1,shook=(-1.907,-4.126,11.696),srot=(0,0,0)),
}
def build_meshes(key):
    b=BUILDS[key]
    g=merged(b['gun'])
    h=merged(dict(path=b['hand'],frame=b['gframe'],hook=b['ghook'],rot=b['grot'],**ERMAC_PL))
    s=merged(dict(path=b['hand2'],frame=b['sframe'],hook=b['shook'],rot=b['srot'],**ERMAC_PL))
    return g,h,s
