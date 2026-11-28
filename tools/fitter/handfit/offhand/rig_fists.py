"""rig_fists.py <pk3> <tag>: the Fists weapon on the rig (TEST ONLY): idle fists from the eye; a BD22 PistolZombie with speed 0 34 units in front
(test probe oht_dmg.pk3: netevent oht_spawn), main punches (+attack) and off-hand punches (rsq_punch 1, off trigger), every hit
logged (OHT DMG). The frame of the FIRST logged hit of each run is kept (tics before quit = OHT MARK at quit - hit tic)."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigshot as R
pk3, tag = sys.argv[1], sys.argv[2]
DMG = os.path.join(R.G.OUT, 'oht_dmg.pk3')
HMD = '0.10 1.50 0.10 -15 0 0'; LH = '-0.10 1.32 -0.40 30 0 0'; RH = '0.28 1.30 -0.35 30 0 0'
base = ('wait 100; ' + R.G.SET + 'rsq_punch 1; screenblocks 12; crosshair 0; give Melee_Attacks; wait 2; use Melee_Attacks; wait 120; '
        'qz_hmd "%s"; qz_lhand "%s"; qz_rhand "%s"; ' % (HMD, LH, RH))
END = 'netevent oht_mark; wait 5; quit'
def at_hit(png, k=0, lead=0):
    def f(text):
        h = [int(x) for x in re.findall(r'OHT DMG t (\d+)', text)]; q = re.findall(r'OHT MARK t (\d+)', text)
        hk = [x for x in h if x > 230]; return {png: ('tic', hk[k] + lead)} if hk else {}
    return f
def hits(t): return [l for l in t.splitlines() if l.startswith('OHT ')]
if __name__ == '__main__':
    t, o = R.shot(pk3, 'fists_idle_' + tag, base + 'wait 60; ' + END, lambda text: {'fists_idle_%s.png' % tag: ('tic', int(re.findall(r'OHT MARK t (\d+)', text)[-1]) - 20)}, extra=[DMG]); print('idle', o, R.errors(t))
    s2 = base + 'netevent oht_spawn 34; wait 30; ' + '+attack; wait 8; -attack; wait 22; ' * 4 + END
    t2, o2 = R.shot(pk3, 'fists_main_' + tag, s2, at_hit('fists_main_%s.png' % tag), extra=[DMG]); print('main', o2, R.errors(t2)); print('\n'.join(hits(t2)))
    s3 = base + 'netevent oht_spawn 34; wait 30; ' + 'qz_ltrigger 1; wait 4; qz_ltrigger 0; wait 26; ' * 4 + END
    t3, o3 = R.shot(pk3, 'fists_off_' + tag, s3, at_hit('fists_off_%s.png' % tag), extra=[DMG]); print('off', o3, R.errors(t3)); print('\n'.join(hits(t3)))
