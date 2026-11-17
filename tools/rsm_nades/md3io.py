import struct, numpy as np
def read(path):
    d = open(path,'rb').read()
    ident, ver, name, flags, nF, nT, nS, nSk, oF, oT, oS, oE = struct.unpack_from('<4si64s'+'i'*9, d, 0)
    frames=[]
    for i in range(nF):
        o=oF+i*56
        mn=struct.unpack_from('<3f',d,o); mx=struct.unpack_from('<3f',d,o+12); org=struct.unpack_from('<3f',d,o+24); r=struct.unpack_from('<f',d,o+36)[0]; nm=d[o+40:o+56]
        frames.append(dict(min=mn,max=mx,origin=org,radius=r,name=nm))
    tags=[]
    surfs=[]
    o=oS
    for s in range(nS):
        sid, sname, sflags, snF, snSh, snV, snT, oTri, oSh, oST, oXyz, oEnd = struct.unpack_from('<4s64s'+'i'*10, d, o)
        tris = np.frombuffer(d, dtype='<i4', count=snT*3, offset=o+oTri).reshape(-1,3).copy()
        shaders=[d[o+oSh+k*68:o+oSh+k*68+68] for k in range(snSh)]
        st = np.frombuffer(d, dtype='<f4', count=snV*2, offset=o+oST).reshape(-1,2).copy()
        raw = np.frombuffer(d, dtype='<i2', count=snF*snV*4, offset=o+oXyz).reshape(snF,snV,4).copy()
        xyz = raw[:,:,:3].astype(float)/64.0
        nrm = raw[:,:,3].copy()
        surfs.append(dict(name=sname, flags=sflags, tris=tris, shaders=shaders, st=st, xyz=xyz, nrm=nrm))
        o += oEnd
    return dict(name=name, flags=flags, frames=frames, tags=tags, nT=nT, surfs=surfs)

def write(path, name, surfs, frame_name=b'frame0'):
    # one frame; surfs: list of dict(name, tris, st, xyz (V,3), nrm (V,) int16 encoded, shader bytes)
    allv = np.concatenate([s['xyz'] for s in surfs])
    mn = allv.min(0); mx = allv.max(0)
    org=(0.0,0.0,0.0); rad=float(np.linalg.norm(allv,axis=1).max())
    hdr_size = 108
    frames = struct.pack('<3f3f3ff16s', *mn, *mx, *org, rad, frame_name.ljust(16,b'\0')[:16])
    sblobs=[]
    for s in surfs:
        V=len(s['xyz']); T=len(s['tris'])
        sh = s['shader'].ljust(68,b'\0')[:68]
        shdr=108
        oTri=shdr; oSh=oTri+T*12; oST=oSh+68; oXyz=oST+V*8; oEnd=oXyz+V*8
        q = np.round(np.asarray(s['xyz'])*64.0)
        assert np.abs(q).max() < 32767
        raw = np.zeros((V,4),dtype='<i2'); raw[:,:3]=q.astype('<i2'); raw[:,3]=s['nrm']
        b = struct.pack('<4s64s'+'i'*10, b'IDP3', s['name'].ljust(64,b'\0')[:64], 0, 1, 1, V, T, oTri, oSh, oST, oXyz, oEnd)
        b += np.asarray(s['tris'],dtype='<i4').tobytes() + sh + np.asarray(s['st'],dtype='<f4').tobytes() + raw.tobytes()
        assert len(b)==oEnd
        sblobs.append(b)
    oF=hdr_size; oT=oF+len(frames); oS=oT; body=b''.join(sblobs); oE=oS+len(body)
    h = struct.pack('<4si64s'+'i'*9, b'IDP3', 15, name.ljust(64,b'\0')[:64], 0, 1, 0, len(surfs), 0, oF, oT, oS, oE)
    open(path,'wb').write(h+frames+body)
