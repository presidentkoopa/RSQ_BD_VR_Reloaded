"""support_md3.py <Class> <sup.json> --sprite RQXA --label FbxSupMini [--row N] [--tag TEXT] [--note TEXT] [--dry]   (r12 port lane)

Wires an FBX SUPPORT hand that has its OWN baked md3 (hands r4 sup_r4.py / melee support_melee.py: one L frame baked with the wrist
where fbx_b1_L.md3 frame 1 (RQFS B) has it, so it swaps in for RQFS B, plus the handtable sup_hook / sup_rot / sup_point_m):
  - copies the md3 to src/models/rsq/fbx/
  - MODELDEF.rsq: RSQ_GunSide + RSQ_Hands blocks drawing it as RQFS B is drawn (Scale -1 1 1, Offset 0 -24 -10), FrameIndex <sprite> A 0 <frame>
  - hands.zs: the state <label>: <sprite> A -1 (RSQ_GunSide, next to FbxSupF) and the support label chosen for the row
    (inserted right before the SUPPORT SetLayer, so it is the last word for that row)
  - handtable.zs: SupportHook / SupportRot / SupportPoint row = the json's sup_hook / sup_rot / sup_point_m, plus a comment line
The gun is NOT moved here (the support was solved on the gun as it is drawn now, or as the port moves it)."""
import os, re, sys, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'heavies'))
import port_gun as pg
import port_hv	# noqa: registry

def wire(cls, S, sprite, label, row, tag, note, src_md3, frame=0, cond=None):
    md3 = os.path.basename(src_md3)
    pg.COPIES.append((src_md3, os.path.join(pg.SRC, 'models/rsq/fbx', md3))); pg.note('support md3', md3, '<-', os.path.relpath(src_md3, pg.REPO))
    blk = lambda c: 'Model %s\n{\n\tPath "models/rsq/fbx"\n\tModel 0 "%s"\n\tSkin 0 "fbx_hand.png"\n\tScale -1.0 1.0 1.0\n\tOffset 0.0 -24.0 -10.0\n\tFrameIndex %s A 0 %d\t// %s support\n}\n' % (c, md3, sprite, frame, cls)
    hd = '\n// %s (lane B): %s (row %d) support hand, its own FBX L frame drawn as RQFS B is (handtable SupportHook / SupportRot row %d): %s\n' % (tag, cls, row, row, note)
    pg.wr('MODELDEF.rsq', pg.rd('MODELDEF.rsq').rstrip('\n') + '\n' + hd + blk('RSQ_GunSide') + blk('RSQ_Hands')); pg.note('MODELDEF.rsq RSQ_GunSide + RSQ_Hands', sprite)
    tx = pg.rd('zscript/rsq/hands.zs')
    a = '\tFbxSupF: RQFS B -1; Stop;\n'; tx = pg.sub1(tx, a, a + '\t%s: %s A -1; Stop;\t// %s: %s (row %d) support\n' % (label, sprite, tag, cls, row), 'FbxSupF state')
    a = '\t\tinvoker.SetLayer(p, RSQ_Layers.SUPPORT, gs, '
    tx = pg.sub1(tx, a, '\t\tif (%s)\n\t\t\tspl = "%s";\t// %s: %s, %s (handtable SupportHook / SupportRot row %d)\n' % (cond or 'i == %d' % row, label, tag, cls, note, row) + a, 'support SetLayer')
    pg.wr('zscript/rsq/hands.zs', tx); pg.note('hands.zs', label, 'row', row)
    tx = pg.rd('zscript/rsq/handtable.zs')
    tx = pg.setrow(tx, 'SupportHook', S['sup_hook'], row); tx = pg.setrow(tx, 'SupportRot', S['sup_rot'], row); tx = pg.setrow(tx, 'SupportPoint', S['sup_point_m'], row)
    m = pg.first(r'\t// [\w ]+: row \d+ \(', tx, 'support comment anchor')
    tx = tx[:m.start()] + '\t// %s: row %d (%s) = %s (%s, %s)\n' % (tag, row, cls, note, md3, label) + tx[m.start():]
    pg.wr('zscript/rsq/handtable.zs', tx); pg.note('handtable Support row %d' % row, S['sup_hook'], S['sup_rot'], S['sup_point_m'])

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cls'); ap.add_argument('sup'); ap.add_argument('--sprite', required=True); ap.add_argument('--label', required=True)
    ap.add_argument('--row', type=int); ap.add_argument('--tag', default='r12 port'); ap.add_argument('--note', default='the FBX support hand'); ap.add_argument('--src'); ap.add_argument('--dry', action='store_true')
    pg.ARGS = A = ap.parse_args()
    if A.src: pg.SRC = os.path.abspath(A.src)
    S = json.load(open(A.sup)); row = A.row if A.row is not None else pg.GUNS[A.cls]['row']
    wire(A.cls, S, A.sprite, A.label, row, A.tag, A.note, os.path.join(os.path.dirname(os.path.abspath(A.sup)), S['md3']), S.get('frame', 0))
    pg.flush(); print('moved %d items%s' % (len(pg.MOVED), ' (dry run: nothing written)' if A.dry else ''))
