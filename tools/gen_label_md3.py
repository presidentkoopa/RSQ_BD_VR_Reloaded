# writes a two-sided label plate md3: quads lying on the box's +y and -y faces (ammobox.md3: x 18, y 5.07, z 11.18)
import struct, math, sys
out, W, H, Y, skin = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
ROT = len(sys.argv) > 6 and sys.argv[6] == 'rot180'   # the words the right way up as the box lands (rig mag, 11-24)
def nenc(n):
    x,y,z=n; lat=math.acos(max(-1,min(1,z))); lng=math.atan2(y,x)
    return (int(lng*255/(2*math.pi))&255) | ((int(lat*255/(2*math.pi))&255)<<8)
verts=[]; uvs=[]; tris=[]
def quad(y, nrm, flip):
    b=len(verts)
    # corners in x (length) and z (width); u along x, v along z
    for (x,z,u,v) in [(-W/2,-H/2,0,1),(W/2,-H/2,1,1),(W/2,H/2,1,0),(-W/2,H/2,0,0)]:
        if flip: u=1-u
        if ROT: v=1-v
        verts.append((x,y,z,nrm)); uvs.append((u,v))
    if nrm[1]>0: tris.extend([(b,b+2,b+1),(b,b+3,b+2)])
    else: tris.extend([(b,b+1,b+2),(b,b+2,b+3)])
quad(Y,(0,1,0),False); quad(-Y,(0,-1,0),True)
nv=len(verts); nt=len(tris)
sh=struct.pack('<64si',skin.encode(),0)
surf_hdr=108
ot=surf_hdr; osh=ot+12*nt; ost=osh+68; oxyz=ost+8*nv; oend=oxyz+8*nv
s=struct.pack('<4s64siiiiiiiiii',b'IDP3',b'label',0,1,1,nv,nt,ot,osh,ost,oxyz,oend)
s+=b''.join(struct.pack('<3i',*t) for t in tris)+sh+b''.join(struct.pack('<2f',*uv) for uv in uvs)
s+=b''.join(struct.pack('<3hH',int(x*64),int(y*64),int(z*64),nenc(n)) for x,y,z,n in verts)
frame=struct.pack('<3f3f3ff16s',-W/2,-Y,-H/2,W/2,Y,H/2,0,0,0,max(W,H),b'f0')
hdr_len=108; ofs_frames=hdr_len; ofs_tags=ofs_frames+len(frame); ofs_surf=ofs_tags; ofs_end=ofs_surf+len(s)
hdr=struct.pack('<4si64siiiiiiiii',b'IDP3',15,b'label',0,1,0,1,0,ofs_frames,ofs_tags,ofs_surf,ofs_end)
open(out,'wb').write(hdr+frame+s)
print('wrote',out,nv,nt)
