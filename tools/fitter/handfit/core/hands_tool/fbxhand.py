"""Evaluate the rigged FBX hand (hand_final.fbx) at any frame: skeleton + skinned mesh.
Pure numpy on top of fbxbin.py. Output frame: the joint chain's parent frame (FBX units),
which is then normalised to a palm frame by the caller."""
import numpy as np, fbxbin
from collections import defaultdict
TS=46186158000  # FBX ticks per second
FPS=60

def euler_xyz(deg):
    x,y,z=np.radians(deg)
    cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]); Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]); Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rz@Ry@Rx   # FBX eEulerXYZ: X applied first

def M4(R=None,t=None):
    M=np.eye(4)
    if R is not None: M[:3,:3]=R
    if t is not None: M[:3,3]=t
    return M

class Hand:
    def __init__(s,path,which=0):
        s.ver,s.root=fbxbin.load(path)
        o=s.root.find('Objects'); s.objs=objs={c.props[0]:c for c in o.children}
        s.nm=lambda i: objs[i].props[1].split('\x00')[0]
        par={}; cn2m={}; cu2cn={}; geo2model={}; skin2geo={}; cl2skin={}; bone2cl={}
        for C in s.root.find('Connections').children:
            t,a,b=C.props[0],C.props[1],C.props[2]
            A=objs.get(a); B=objs.get(b)
            if t=='OO':
                if A is not None and A.name=='Model' and (b==0 or (B is not None and B.name=='Model')): par[a]=b
                if A is not None and A.name=='Geometry' and B is not None and B.name=='Model': geo2model[a]=b
                if A is not None and A.name=='Deformer' and A.props[2]=='Skin': skin2geo[a]=b
                if A is not None and A.name=='Deformer' and A.props[2]=='Cluster': cl2skin[a]=b
                if A is not None and A.name=='Model' and B is not None and B.name=='Deformer': bone2cl[b]=a
            else:
                if A is not None and A.name=='AnimationCurveNode': cn2m[a]=(b,C.props[3])
                if A is not None and A.name=='AnimationCurve': cu2cn[a]=(b,C.props[3])
        s.par=par
        meshes=[g for g in objs.values() if g.name=='Geometry' and g.props[2]=='Mesh']
        g=meshes[which]; s.geo=g; s.model=geo2model[g.props[0]]
        s.V=g.find('Vertices').props[0].reshape(-1,3).astype(float)
        P=g.find('PolygonVertexIndex').props[0]
        polys=[]; cur=[]
        for i in P:
            if i<0: cur.append(-i-1); polys.append(cur); cur=[]
            else: cur.append(int(i))
        s.polys=polys
        tris=[]; s.tri_poly=[]; corner=0; tri_corners=[]
        for pi,p in enumerate(polys):
            for k in range(1,len(p)-1):
                tris.append((p[0],p[k],p[k+1])); tri_corners.append((corner,corner+k,corner+k+1))
            corner+=len(p)
        s.F=np.array(tris); s.Fc=np.array(tri_corners)
        uvn=g.find('LayerElementUV'); uv=uvn.find('UV').props[0].reshape(-1,2); uvi=uvn.find('UVIndex').props[0]
        s.uv_corner=uv[uvi]  # per polygon-vertex
        s.uv_mapping=(uvn.find('MappingInformationType').props[0],uvn.find('ReferenceInformationType').props[0])
        # skin
        skin=[k for k,v in skin2geo.items() if v==g.props[0]][0]
        s.clusters=[]
        for cl,sk in cl2skin.items():
            if sk!=skin: continue
            C=objs[cl]; bone=bone2cl[cl]
            idx=C.find('Indexes'); w=C.find('Weights')
            TL=C.find('TransformLink').props[0].reshape(4,4).T; T=C.find('Transform').props[0].reshape(4,4).T
            s.clusters.append(dict(bone=bone,name=s.nm(bone),idx=idx.props[0] if idx else np.zeros(0,int),w=w.props[0] if w else np.zeros(0),TL=TL,T=T))
        # joints: those LimbNodes under this mesh's rig = cluster bones and their ancestors that are LimbNodes
        s.joints=[c['bone'] for c in s.clusters]
        s.jname={j:s.nm(j) for j in s.joints}
        # curves
        s.curves=defaultdict(dict)
        for cu,(cn,ch) in cu2cn.items():
            m,p=cn2m[cn]
            c=objs[cu]
            s.curves[m][(p,ch)]=(c.find('KeyTime').props[0]/TS*FPS,c.find('KeyValueFloat').props[0].astype(float))
        s.nframes=int(round(max(t[-1] for d in s.curves.values() for t,_ in d.values())))+1
        s.p70={j:fbxbin.props70(objs[j]) for j in s.joints}
        s.name2j={s.jname[j]:j for j in s.joints}
    def chan(s,j,prop,f):
        p=s.p70[j]; base=list(p[prop][1]) if prop in p else ([1.,1.,1.] if 'Scal' in prop else [0.,0.,0.])
        out=[]
        for k,ax in enumerate('XYZ'):
            c=s.curves[j].get((prop,'d|'+ax))
            out.append(float(np.interp(f,c[0],c[1])) if c is not None else base[k])
        return np.array(out)
    def local(s,j,f):
        p=s.p70[j]
        pre=euler_xyz(p['PreRotation'][1]) if 'PreRotation' in p else np.eye(3)
        R=pre@euler_xyz(s.chan(j,'Lcl Rotation',f))
        S=np.diag(s.chan(j,'Lcl Scaling',f))
        return M4(R@S,s.chan(j,'Lcl Translation',f))
    def globals_rel(s,f):
        """joint transforms relative to the parent of Root_joint (whatever controls do above)."""
        G={}
        def g(j):
            if j in G: return G[j]
            pj=s.par.get(j)
            G[j]=(g(pj) if pj in s.jname else np.eye(4))@s.local(j,f)
            return G[j]
        for j in s.joints: g(j)
        return G
    def bind_rel(s):
        """bind-pose globals in the same rel frame: TL relative to Root_joint's parent at bind."""
        root=s.name2j['Root_joint']; cr=[c for c in s.clusters if c['bone']==root][0]
        # Root parent at bind = TL_root @ inv(local_root at bind). Bind local unknown -> use frame 0 local? use TL directly (rel = inv(TLroot)@TL then root local applied)
        return cr
    def skin(s,f,frame='Root_joint'):
        """Skinned vertices expressed in joint `frame`'s local space at frame f.
        v = sum_b w_b * inv(G_frame) @ G_b @ inv(TL_b) @ v_bind  (control rig above the root cancels)."""
        G=s.globals_rel(f); Fi=np.linalg.inv(G[s.name2j[frame]])
        out=np.zeros((len(s.V),3)); wsum=np.zeros(len(s.V))
        Vh=np.c_[s.V,np.ones(len(s.V))]
        for c in s.clusters:
            if len(c['idx'])==0: continue
            M=Fi@G[c['bone']]@np.linalg.inv(c['TL'])  # this file: Transform==inv(TransformLink) (mesh global = I), checked
            out[c['idx']]+=(Vh[c['idx']]@M.T)[:,:3]*c['w'][:,None]; wsum[c['idx']]+=c['w']
        return out/np.maximum(wsum,1e-9)[:,None]
    def bind_mesh(s):
        return s.V.copy()
    def joints_in(s,f,frame='Root_joint'):
        G=s.globals_rel(f); Fi=np.linalg.inv(G[s.name2j[frame]])
        return {s.jname[j]:(Fi@G[j]) for j in s.joints}
    def joint_pos(s,f):
        G=s.globals_rel(f)
        return {s.jname[j]:G[j][:3,3].copy() for j in s.joints}, G
