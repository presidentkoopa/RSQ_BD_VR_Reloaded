"""Write a one-surface MD3 with N vertex frames (Quake 3 MD3 v15), for QZD 17.3's MD3 loader.
Vertices are split per (position index, uv) so the FBX's per-corner UVs survive. Normals per frame from the mesh."""
import struct, numpy as np
def enc_normal(n):
    n=n/(np.linalg.norm(n,axis=1,keepdims=True)+1e-12)
    lat=(np.degrees(np.arccos(np.clip(n[:,2],-1,1)))*255/360).round().astype(int)&255
    lng=(np.degrees(np.arctan2(n[:,1],n[:,0]))*255/360).round().astype(int)&255
    return (lat<<8)|lng
def vnormals(V,F):
    N=np.zeros_like(V); fn=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]])
    for k in range(3): np.add.at(N,F[:,k],fn)
    return N
def split_uv(F,Fc,uv_corner):
    """F: tris of position indices, Fc: tris of corner indices -> (new tris, source position index per new vert, uv per new vert)"""
    key={}; src=[]; uvs=[]; T=np.zeros_like(F)
    for t in range(len(F)):
        for k in range(3):
            pi=int(F[t,k]); uv=tuple(np.round(uv_corner[Fc[t,k]],6))
            kk=(pi,uv)
            if kk not in key: key[kk]=len(src); src.append(pi); uvs.append(uv)
            T[t,k]=key[kk]
    return T,np.array(src),np.array(uvs)
def write(path,frames,F,uv,skin_name,surf_name='hand',frame_names=None):
    """frames: list of [nv,3] vertex arrays (md3 units); F: [nt,3] tris; uv: [nv,2] (s,t with t already flipped for md3)"""
    nf=len(frames); nv=len(frames[0]); nt=len(F)
    assert nv<=4096 and nt<=8192, (nv,nt)
    for X in frames: assert np.abs(X).max()*64<32767, 'vertex out of md3 range'
    hdr_size=108; frame_size=56; surf_hdr=108
    shaders=struct.pack('<64si',skin_name.encode()[:63],0)
    tris=np.asarray(F,'<i4').tobytes(); st=np.asarray(uv,'<f4').tobytes()
    xyzn=b''
    for X in frames:
        N=enc_normal(vnormals(X,F)); q=np.round(X*64).astype('<i2')
        xyzn+=np.c_[q,N.astype('<i2')].astype('<i2').tobytes()
    o_tri=surf_hdr; o_sh=o_tri+len(tris); o_st=o_sh+len(shaders); o_xyz=o_st+len(st); o_end=o_xyz+len(xyzn)
    surf=struct.pack('<4s64siiiiiiiiii',b'IDP3',surf_name.encode(),0,nf,1,nv,nt,o_tri,o_sh,o_st,o_xyz,o_end)+tris+shaders+st+xyzn
    fr=b''
    for i,X in enumerate(frames):
        mn=X.min(0); mx=X.max(0); c=(mn+mx)/2; r=float(np.linalg.norm(mx-c))
        nm=(frame_names[i] if frame_names else f'f{i}').encode()[:15]
        fr+=struct.pack('<3f3f3ff16s',*mn,*mx,0,0,0,r,nm)
    o_fr=hdr_size; o_tag=o_fr+len(fr); o_surf=o_tag; o_eof=o_surf+len(surf)
    hdr=struct.pack('<4si64siiiiiiiii',b'IDP3',15,b'rsq_fbxhand',0,nf,0,1,0,o_fr,o_tag,o_surf,o_eof)
    open(path,'wb').write(hdr+fr+surf)
    return o_eof
