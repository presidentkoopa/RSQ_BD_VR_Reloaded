"""Check sheets: per arrangement (FBX solve / 1.92 / current) side, bottom, top, eye views with landmark dots
(web, trigger, palm centre, support contact) and one green/yellow/red line per rule with its number."""
import numpy as np, json, os
from PIL import Image, ImageDraw
import render, rules
COL=dict(G=(60,200,90),Y=(230,200,40),R=(230,70,60))
def eye_view(meshes,marks,title,eye=(-38,-14,14),look=(8,0,-6)):
    return render.render(meshes,eye=eye,look=look,W=420,H=330,fov=55,marks=marks,title=title)
def panel(title,gun_rules,sup_rules,W=420):
    lines=[(title,None)]+[(f'{rid} {lab}',lt) for rid,lab,lt,src in gun_rules]+([('support hand',None)] if sup_rules else [])+[(f'{rid} {lab}',lt) for rid,lab,lt,src in (sup_rules or [])]
    # wrap
    wrapped=[]
    for t,lt in lines:
        while len(t)>66: cut=t.rfind(' ',0,66); wrapped.append((t[:cut],lt)); t='     '+t[cut+1:]; lt=('-'+lt) if lt and not lt.startswith('-') else lt
        wrapped.append((t,lt))
    H=16*len(wrapped)+10
    im=Image.new('RGB',(W,H),(24,25,32)); dr=ImageDraw.Draw(im); y=5
    for t,lt in wrapped:
        if lt is None: dr.text((6,y),t,fill=(255,255,255))
        else:
            c=COL[lt.strip('-')]
            if not lt.startswith('-'): dr.rectangle((6,y+2,16,y+12),fill=c)
            dr.text((22,y),t,fill=c)
        y+=16
    return im
def counts(gr,sr):
    a=[lt for _,_,lt,_ in gr+(sr or [])]; return {k:a.count(k) for k in 'GYR'}
def arrangement_sheet(name,meshes,marks,gr,sr,out,rng_side=None,px=7,eye=None,look=None):
    views=[]
    for k in ('side','bottom','top'):
        views.append(render.render(meshes,k,px=px,rng=None if rng_side is None else (rng_side if k=='side' else (rng_side[0],rng_side[1],-12,12)),marks=marks,title=f'{name}  {k}'))
    views.append(eye_view(meshes,marks,f'{name}  player eye',**({} if eye is None else dict(eye=eye,look=look))))
    c=counts(gr,sr)
    pan=panel(f'{name}: rules  G {c["G"]}  Y {c["Y"]}  R {c["R"]}',gr,sr)
    tiles=views+[pan]
    w=max(v.width for v in views); 
    col1=render.sheet(views,2)
    S=Image.new('RGB',(col1.width+pan.width+8,max(col1.height,pan.height)),(20,20,28)); S.paste(col1,(0,0)); S.paste(pan,(col1.width+8,0))
    S.save(out); return S
def side_by_side(paths,out,labels=None):
    ims=[Image.open(p) for p in paths]; W=max(i.width for i in ims); H=sum(i.height for i in ims)+8*len(ims)
    S=Image.new('RGB',(W,H),(12,12,16)); y=0
    for i in ims: S.paste(i,(0,y)); y+=i.height+8
    S.save(out)
