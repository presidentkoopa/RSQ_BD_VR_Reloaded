"""Small numpy z-buffer rasteriser (orthographic or perspective) for check sheets.
meshes: list of dict(V[n,3] in F/L/U cm, F[m,3], col (rgb) or fcol[m,3], alpha)"""
import numpy as np
from PIL import Image, ImageDraw
VIEWS={ # right, up, toward-viewer (F/L/U unit vectors); all proper (right x up = toward viewer), no mirror images
 'side':  (np.array([1,0,0.]),np.array([0,0,1.]),np.array([0,-1,0.])),   # from the gun's right side, F right, U up
 'left':  (np.array([-1,0,0.]),np.array([0,0,1.]),np.array([0,1,0.])),   # from its left side
 'bottom':(np.array([1,0,0.]),np.array([0,-1,0.]),np.array([0,0,-1.])),  # from below, F right, right side (-L) up
 'top':   (np.array([1,0,0.]),np.array([0,1,0.]),np.array([0,0,1.])),    # from above, F right, left side (+L) up
 'front': (np.array([0,1,0.]),np.array([0,0,1.]),np.array([1,0,0.])),    # from the muzzle looking back
 'back':  (np.array([0,-1,0.]),np.array([0,0,1.]),np.array([-1,0,0.])),  # from behind = the player's view: player's right to the right
}
def basis_eye(eye,look,up=(0,0,1.)):
    eye=np.asarray(eye,float); f=np.asarray(look,float)-eye; f/=np.linalg.norm(f)
    if abs(f@np.asarray(up,float))>0.98: up=(0,1.,0)
    r=np.cross(f,up); r/=np.linalg.norm(r); u=np.cross(r,f)
    return r,u,-f
def render(meshes,kind='side',rng=None,px=10,W=None,H=None,eye=None,look=None,fov=60,marks=(),lines=(),title='',bg=(46,48,60),grid=5,light=(0.3,-0.5,0.8)):
    persp=eye is not None
    if persp: R,U,T=basis_eye(eye,look); eye=np.asarray(eye,float)
    else: R,U,T=VIEWS[kind]
    allV=np.concatenate([m['V'] for m in meshes])
    if not persp:
        h=allV@R; v=allV@U
        if rng is None: rng=(np.floor(h.min()/5)*5-3,np.ceil(h.max()/5)*5+3,np.floor(v.min()/5)*5-3,np.ceil(v.max()/5)*5+3)
        h0,h1,v0,v1=rng; W=int((h1-h0)*px); H=int((v1-v0)*px)
        def proj(P): return np.stack([(P@R-h0)*px, H-(P@U-v0)*px],-1), P@T
    else:
        W=W or 640; H=H or 480; fpx=(W/2)/np.tan(np.radians(fov/2))
        def proj(P):
            q=P-eye; z=-(q@T); z=np.maximum(z,1e-3)
            return np.stack([W/2+(q@R)/z*fpx, H/2-(q@U)/z*fpx],-1), -z
    zb=np.full((H,W),-1e9); img=np.zeros((H,W,3)); img[:]=bg
    Ld=np.asarray(light,float); Ld/=np.linalg.norm(Ld)
    for m in meshes:
        V=m['V']; F=m['F']; p,d=proj(V)
        a,b,c=V[F[:,0]],V[F[:,1]],V[F[:,2]]
        n=np.cross(b-a,c-a); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
        Lw=Ld[0]*R+Ld[1]*U+Ld[2]*T  # light in view space -> world
        sh=0.35+0.65*np.abs(n@Lw)
        fc=m['fcol'] if 'fcol' in m else np.tile(np.asarray(m.get('col',(200,200,200)),float),(len(F),1))
        cols=fc*sh[:,None]
        alpha=m.get('alpha',1.0)
        P0,P1,P2=p[F[:,0]],p[F[:,1]],p[F[:,2]]; D0,D1,D2=d[F[:,0]],d[F[:,1]],d[F[:,2]]
        xmin=np.floor(np.minimum(np.minimum(P0[:,0],P1[:,0]),P2[:,0])).astype(int).clip(0,W-1)
        xmax=np.ceil(np.maximum(np.maximum(P0[:,0],P1[:,0]),P2[:,0])).astype(int).clip(0,W-1)
        ymin=np.floor(np.minimum(np.minimum(P0[:,1],P1[:,1]),P2[:,1])).astype(int).clip(0,H-1)
        ymax=np.ceil(np.maximum(np.maximum(P0[:,1],P1[:,1]),P2[:,1])).astype(int).clip(0,H-1)
        for i in range(len(F)):
            if xmax[i]<xmin[i] or ymax[i]<ymin[i]: continue
            xs=np.arange(xmin[i],xmax[i]+1); ys=np.arange(ymin[i],ymax[i]+1)
            X,Y=np.meshgrid(xs+0.5,ys+0.5)
            x0,y0=P0[i];x1,y1=P1[i];x2,y2=P2[i]
            den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
            if abs(den)<1e-9: continue
            w0=((y1-y2)*(X-x2)+(x2-x1)*(Y-y2))/den; w1=((y2-y0)*(X-x2)+(x0-x2)*(Y-y2))/den; w2=1-w0-w1
            ins=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
            if not ins.any(): continue
            z=w0*D0[i]+w1*D1[i]+w2*D2[i]
            yy,xx=np.nonzero(ins); zz=z[ins]; Yi=ys[yy]; Xi=xs[xx]
            upd=zz>zb[Yi,Xi]
            Yi,Xi,zz=Yi[upd],Xi[upd],zz[upd]
            zb[Yi,Xi]=zz
            img[Yi,Xi]=cols[i] if alpha>=1 else img[Yi,Xi]*(1-alpha)+cols[i]*alpha
    im=Image.fromarray(img.clip(0,255).astype(np.uint8)); dr=ImageDraw.Draw(im)
    def P2(q):
        pp,_=proj(np.asarray(q,float)[None]); return tuple(pp[0])
    if not persp and grid:
        for g in range(int(np.ceil(rng[0]/grid)*grid),int(rng[1])+1,grid):
            x=(g-rng[0])*px; dr.line([(x,0),(x,4)],fill=(150,150,170)); 
            if g%10==0: dr.text((x+1,5),str(g),fill=(150,150,170))
        for g in range(int(np.ceil(rng[2]/grid)*grid),int(rng[3])+1,grid):
            y=H-(g-rng[2])*px; dr.line([(0,y),(4,y)],fill=(150,150,170))
            if g%10==0: dr.text((5,y-6),str(g),fill=(150,150,170))
    for a,b,col in lines:
        dr.line([P2(a),P2(b)],fill=col,width=2)
    for q,lab,col in marks:
        x,y=P2(q); dr.ellipse((x-4,y-4,x+4,y+4),fill=col,outline=(0,0,0)); 
        if lab: dr.text((x+6,y-6),lab,fill=col)
    if title: dr.rectangle((0,H-14,W,H),fill=(20,20,28)); dr.text((3,H-13),title,fill=(255,255,255))
    return im
def sheet(ims,cols,pad=4,bg=(20,20,28)):
    w=max(i.width for i in ims); h=max(i.height for i in ims); rows=(len(ims)+cols-1)//cols
    S=Image.new('RGB',(cols*(w+pad),rows*(h+pad)),bg)
    for k,i in enumerate(ims): S.paste(i,((k%cols)*(w+pad),(k//cols)*(h+pad)))
    return S
