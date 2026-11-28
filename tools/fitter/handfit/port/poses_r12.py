"""poses_r12.py: record what the r12 port shipped in tools/handfit/poses/<Class>.json (gun move, two-handed blocks, melee moves, the
support as shipped), read from fits/ported_<Class>.json and the src/ handtable. Run after the port; rebake.py check reads the result."""
import os as _dpo, sys as _dps; _dps.path.append(_dpo.path.normpath(_dpo.path.join(_dpo.path.dirname(_dpo.path.abspath(__file__)), '../..'))); import depot as _DP	# Depot paths (tools/depot.py)
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); POSES = os.path.join(_DP.POSES); sys.path.insert(0, HERE)
import port_gun as pg
TAG = 'r12 port (lane B, 2026-10-28)'
def ht(row):
    tx = open(os.path.join(pg.SRC, 'zscript/rsq/handtable.zs'), encoding='latin1').read()
    return {fn: pg.getrow(tx, fn, row).tolist() for fn in ('GunHook', 'GunRot', 'GunHookTwo', 'GunRotTwo', 'SupportHook', 'SupportRot', 'SupportPoint')}
def P(c): return json.load(open(os.path.join(_DP.FITS, 'ported_%s.json' % c)))
def load(c): return json.load(open(os.path.join(POSES, c + '.json')))
def save(c, J): json.dump(J, open(os.path.join(POSES, c + '.json'), 'w'), indent=1); print('poses/%s.json' % c)
ROWS = dict(Minigun=13, Unmaker=23, HellishMissileLauncher=9, BFG10k=2, NukeLauncher=14, FlameCannon=28, BrutalAxe=24, Chain_saw=25, DSweap=26)
if __name__ == '__main__':
    # Minigun: the shipped support is now the r4 bar fist
    J = load('Minigun'); s = J['poses']
    if s['support'].get('source', '').startswith('FLAG'): s['support_r9_ermac'] = s['support']
    s['support'] = dict(s['support_r4_bar'], shipped='%s: MODELDEF.rsq RQXA (fbx_r4_Minigun_bar_L.md3 frame 0), hands.zs FbxSupMini, handtable row 13' % TAG, handtable=ht(13)); save('Minigun', J)
    for c in ('Unmaker', 'HellishMissileLauncher'):
        J = load(c); s = J['poses']
        if 'fbx_b1_L' in s['support'].get('source', ''): s['support_farm_not_shipped'] = s['support']
        s['support'] = dict(source="%s: the OLD support kept (owner 2026-10-28: a support lane is redoing it): Ermac hand2.md3 pose D (frame 3) moved with the gun (port_gun support 'move')" % TAG, hook=ht(ROWS[c])['SupportHook'], rot=ht(ROWS[c])['SupportRot'], point_m=ht(ROWS[c])['SupportPoint'])
        J['port'] = dict(tag=TAG, ported=P(c)['place']); save(c, J)
    for c in ('BFG10k', 'NukeLauncher'):
        J = load(c); q = P(c)
        J['port'] = dict(tag=TAG, how='reseat_gun.py: re-fit of the gun hand on the already ported gun; the gun moved again by the relative move', reseated_from=q['reseated_from']['place'], relative_turn_deg=q['relative']['turn_deg'], relative_t_cm=q['relative']['t'],
                         support_shipped='NOT touched by r12 (support lane owns it): handtable row %d as shipped' % ROWS[c], support_shipped_rows=ht(ROWS[c]))
        save(c, J)
    J = load('FlameCannon'); q = P('FlameCannon')
    J['port'] = dict(tag=TAG, how='flamecannon_r12.py: handtable row 28 added (no gun hand), MODELDEF place, gunmoves Pivot 28, RSQ_Muzzle + flamespout at the nozzle tip', nozzle_tip_flu=q['nozzle_tip'], barrel_axis_flu=q['barrel_axis'], handtable=ht(28))
    J['poses']['support']['shipped'] = '%s: MODELDEF.rsq RQXB (fbx_r4_FlameCannon_under40_L.md3 frame 0), hands.zs FbxSupFC, handtable row 28' % TAG; save('FlameCannon', J)
    for c, spr in (('BrutalAxe', None), ('Chain_saw', 'RQXC FbxSupSaw'), ('DSweap', 'RQXD FbxSupDS')):
        J = load(c); q = P(c)
        J['gun_move'] = dict(modeldef_place=q['place'], R=q['R'], t=q['t'], note='%s (melee_r12.py): one method, the weapon moved to the hand (port_gun.place of the fit shift)' % TAG, melee_moves_by_poseFrame=q['moves'],
                             two_handed=[s for s in q['moved'] if s.startswith('TWO-HANDED')], handtable=ht(ROWS[c]))
        J.pop('gun_move_note', None)
        if spr: J['poses']['support']['shipped'] = '%s: MODELDEF.rsq %s, handtable row %d SupportHook / SupportRot = the support row hook / rot, SupportPoint moved with the weapon' % (TAG, spr, ROWS[c])
        else: J['poses']['support'] = dict(J['poses'].get('support') or {}, shipped="%s: no FBX support fitted for the axe; the old Ermac pose E moved with the weapon" % TAG)
        save(c, J)
