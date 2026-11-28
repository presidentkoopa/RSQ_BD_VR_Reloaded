"""Melee hands lane: where each start hold (Ermac hand, m192 rule) sits on each melee mesh: landmark distances, penetration (measured).
usage: [MELEE_FITTER_HOME=<dir with lane_c>] [RS_FITTER_LIB=<fitter modules, default ../fitter_lib>] python3 probe_melee.py"""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import sys, os, json, numpy as np
import os as _fl_os; FITTER_LIB = _fl_os.environ.get('RS_FITTER_LIB', _fl_os.path.join(_fl_os.path.dirname(_fl_os.path.abspath(__file__)), '..', 'fitter_lib'))	# the batch 1-4 fitter modules (were <work>/runs/lane_b_b*run/tools)
FH = os.environ.get('MELEE_FITTER_HOME', _DP.WORK + '/fitter_home/'); sys.path.insert(0, FH)
for p in (_DP.CORE + '/hands_tool', FITTER_LIB, FITTER_LIB): sys.path.insert(0, p)
import scene, ermaclm, evaluate, m192, exactpen
W=os.path.join(_DP.SRC, 'models', 'bd')+'/'
R192=FH+'/lane_c/bd22q_192/models/rsq/'
C={
 'BrutalAxe': dict(it=dict(path=W+'BrutalAxe/BrutalAxe.md3',frame=5,scale=[-1,1,1],off=[0,0,-5]), holds={'192':(R192+'hand.md3',4,[-4.58,0.06,12.78],[0.89,16.59,0.93]),'199':(R192+'hand.md3',4,[-4.58,0.15,12.85],[0.89,16.59,0.93])}),
 'Chain_saw': dict(it=dict(path=W+'Chain_saw/Chain_saw.md3',frame=11,scale=[-1.5,1.5,1.5],off=[0,10,-5]), holds={'192':(R192+'hand.md3',4,[-4.39,3.43,-0.63],[0.88,-10.2,0.54]),'199':(R192+'hand.md3',4,[-8.91,5.61,1.04],[-17.47,-6.32,26.85])}),
 'DSweap': dict(it=dict(path=W+'DSweap/DSweap.md3',frame=0,scale=[-1,1,1],off=[0,0,-5]), holds={'199':(R192+'hand.md3',4,[-4.4,0.25,1.27],[0.97,31.45,1.16])}),
 'HandGrenades': dict(it=dict(path=W+'Grenade/nade.md3',frame=2,scale=[-0.92,0.92,0.92],off=[-4.01,-2.04,-6.45]), holds={'199':(R192+'ammo_hand.md3',3,[0,0,0],[0,0,0])}),
}
L=ermaclm.get()
def lms(path,fr,hook,rot):
    _,V=scene.merged(dict(path=path,frame=fr,hook=hook,rot=rot,**scene.ERMAC_PL)); return {k:V[np.array(evaluate.reg(L,k)).ravel()].mean(0) for k in m192.KEYS+['pad_I','pad_M','pad_R','pad_P','pad_T']},V
if __name__=='__main__':
  for g,c in C.items():
    F,V=scene.merged(c['it']); ex=exactpen.Exact(V,F)
    for h,(p,fr,hk,rt) in c['holds'].items():
        G,HV=lms(p,fr,hk,rt)
        print(g,h,'pen %.2f'%ex.depth(HV).max(), ' '.join('%s %s d%.1f'%(k,G[k].round(1),ex.unsigned(G[k][None])[0]) for k in ['web','palm','cuff','pad_I','pad_M','pad_T']))
