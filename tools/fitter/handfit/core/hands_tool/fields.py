"""Cached signed distance fields (gunfield.cached) for the regions the solver works in (controller frame, cm)."""
import scene, gunfield
REGIONS={
 'BrutalPistol':{'gun':((-14,-8,-20),(18,8,6))},
 'Flamethrower2':{'gun':((-34,-10,-30),(14,10,6)),'sup':((6,-10,-28),(30,10,-2)),'tank':((12,-12,-27),(42,12,-1))},
}
def get(cls,which):
    F,V=scene.merged(scene.GUNS[cls]); lo,hi=REGIONS[cls][which]
    return gunfield.cached(f'{cls}_{which}',V,F,lo,hi)
if __name__=='__main__':
    import sys,time
    for cls,d in REGIONS.items():
        for w in d:
            t=time.time(); get(cls,w); print(cls,w,round(time.time()-t,1),'s',flush=True)
