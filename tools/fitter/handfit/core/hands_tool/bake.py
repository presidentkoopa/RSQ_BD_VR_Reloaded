"""Bake solved FBX hands into MD3 vertex frames + hand-table rows (no skeleton at runtime).
For each solved hand (vertices X in the controller frame, cm):
  frame verts  = flu_to_md3( T^-1 X ), with T the rigid that takes the CONTROLLER GRIP cuff to the solved cuff
                 (so the baked frame's wrist sits where the real hand is: the frame carries only the finger pose)
  row          = hook_from_rigid(T): GunHook / GunRot (or SupportHook / SupportRot) in ModifyBobLayer3D units
Then reload the MD3 and re-place it with the row through the kit's own placement chain (hudrender.to_local) and
report the max deviation from the solved vertices (the bake check)."""
import numpy as np, json, os, sys
import handmodel, md3write, hook, metrics, scene, hudrender, solve
LANE=solve.LANE
def bake(entries,out_md3,skin='fbx_hand.png'):
    """entries: list of dict(name, side, X, cuff_ref) -> writes one md3 per side; returns rows + checks"""
    rows=[]; frames={'R':[],'L':[]}; names={'R':[],'L':[]}
    H={'R':handmodel.FbxHand('R'),'L':handmodel.FbxHand('L')}
    T,src,uv=md3write.split_uv(H['R'].h.F,H['R'].h.Fc,H['R'].h.uv_corner)
    st=np.c_[uv[:,0],1-uv[:,1]]
    Lc=json.load(open(os.path.join(LANE,'landmarks_fbx.json')))['R']['cuff']
    for e in entries:
        X=np.asarray(e['X']); Rw,tw=metrics.rigid(e['cuff_ref'],X[Lc])
        base=(X-tw)@Rw                                  # = T^-1 X : the hand with its wrist on the controller grip
        h,r=hook.hook_from_rigid(Rw,tw)
        m=hook.flu_to_md3(base)[src]
        side=e['side']; frames[side].append(m); names[side].append(e['name'][:15])
        rows.append(dict(name=e['name'],side=side,frame=len(frames[side])-1,hook=h.round(3).tolist(),rot=r.round(3).tolist(),
                         wrist_rot_deg=float(np.degrees(np.arccos(np.clip((np.trace(Rw)-1)/2,-1,1)))),wrist_move_cm=float(np.linalg.norm(tw))))
    Tl=T[:,::-1]   # the left rig's winding is mirrored (handmodel flips F for 'L'); keep outward normals
    paths={}
    for side in 'RL':
        if not frames[side]: continue
        p=out_md3.replace('.md3',f'_{side}.md3')
        md3write.write(p,frames[side],T if side=='R' else Tl,st,skin,frame_names=names[side]); paths[side]=p
    # reload + re-place check
    for r,e in zip(rows,entries):
        s=scene.md3_full(paths[r['side']])[0]
        it=dict(hook=r['hook'],rot=r['rot'],**hook.PL)
        Y=100*(hudrender.to_local(s['xyz'][r['frame']],it)@hook.P.T)
        X=np.asarray(e['X'])[src]
        r['bake_check_max_cm']=float(np.abs(Y-X).max()); r['md3']=os.path.basename(paths[r['side']])
    return rows,paths,(T,Tl,st)
