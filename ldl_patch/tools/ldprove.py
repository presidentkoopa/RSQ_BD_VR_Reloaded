"""TEST ONLY (never ships): prove LD-mode effects on the QuestZDoom 17.3 rig, one log section per effect.

  python3 -I ldl_patch/tools/ldprove.py <batch> [effect ...]      batches: see BATCHES below; 'list' prints them

For each effect: the rig probe forces it on the held gun (netevent rsld_fx:<Effect>), spawns a target where the
gun points (netevent rsld_target:<class> <dist> <health> <friendly>), fires, and checks with rsld_has / rsld_thas /
rsld_amm. Each effect's lines go between 'RSLDT begin <Effect>' and 'RSLDT end <Effect>' (console echo).
Writes the rig log to /tmp/ldrig/prove_<batch>.log and one file per effect to
ldl_patch/evidence/ldmode/<Effect>.log (the proof: "rig only, not headset-confirmed").
Uses ldl_patch/tools/ldrig.sh (the rig lock, full load order with LegenDoom 3.0, qzdoom.ini restored).
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVD = os.path.join(os.path.dirname(HERE), 'evidence', 'ldmode')

def fire(n=1, hold=3, gap=45):
    return '; '.join('+attack; wait %d; -attack; wait %d' % (hold, gap) for _ in range(n))

def shots(n, cls='BaronofHell2', hp=30000, gap=45):	# a fresh still target before every shot (BD22 monsters change class when hurt)
    return '; '.join(tgt(cls, hp) + '; ' + fire(1, 3, gap) for _ in range(n))

def tgt(cls='BaronofHell2', hp=30000, dist=96, friendly=1):
    return 'netevent rsld_cleartargets; netevent rsld_target:%s %d %d %d; wait 8' % (cls, dist, hp, friendly)

# effect: (gun, script after the effect is forced)
SG = 'Shot_Gun'
CASES = {
    # damage x (R)
    'Lucky': (SG, shots(8)),
    'Pristine': (SG, 'netevent rsld_health:100; ' + shots(1) + '; netevent rsld_health:60; ' + shots(1)),
    'Raging': (SG, shots(1) + '; give PowerStrength; ' + shots(1) + '; take PowerStrength'),
    'Rampaging': (SG, shots(1) + '; ' + tgt() + '; +forward; wait 2; ' + fire(1, 3, 2) + '; -forward; wait 40'),
    'Serious': (SG, shots(1) + '; ' + tgt() + '; +back; wait 2; ' + fire(1, 3, 2) + '; -back; wait 40'),
    'ProStrat': (SG, shots(1) + '; ' + tgt() + '; +moveright; wait 2; ' + fire(1, 3, 2) + '; -moveright; wait 40'),
    'Berserker': (SG, 'netevent rsld_health:100; ' + shots(1) + '; netevent rsld_health:45; ' + shots(1) + '; netevent rsld_health:100'),
    'CQC': (SG, shots(2)),
    'AntiTree': (SG, tgt() + '; ' + fire(1)),
    'Annoying': (SG, 'netevent rsld_amm:; ' + shots(3) + '; netevent rsld_amm:'),
    'Patient': (SG, tgt() + '; wait 110; ' + fire(1)),
    # groups (one damage event, x3 / x4)
    'Exorcist': (SG, tgt('RifleZombie') + '; ' + fire(1)),
    'Extinguishing': (SG, tgt('Imp') + '; ' + fire(1)),
    'Wrangler': (SG, tgt('BullDemon') + '; ' + fire(1)),
    'Antiair': (SG, tgt('Cacodemon_') + '; ' + fire(1)),
    'Scrapper': (SG, tgt('Revenant1') + '; ' + fire(1)),
    'Blessed': (SG, tgt('BaronofHell2') + '; ' + fire(1)),
    'Heroic': (SG, tgt('TheCyberdemon', 30000, 160) + '; ' + fire(1)),
    'DemonSlayer': (SG, shots(1) + '; ' + tgt() + '; netevent rsld_legtarget; ' + fire(1)),
    # ammo (owner Q7: the magazine)
    'Unlikely': (SG, 'netevent rsld_amm:; ' + shots(6) + '; netevent rsld_amm:'),
    'Improbable': (SG, 'netevent rsld_amm:; ' + shots(6) + '; netevent rsld_amm:'),
    'Impossible': (SG, 'netevent rsld_amm:; ' + shots(6) + '; netevent rsld_amm:'),
    'Efficient': ('SSG', tgt() + '; netevent rsld_amm:; ' + fire(2, 3, 70) + '; netevent rsld_amm:'),
    # on kill (E: LegenDoom's own items)
    'Artifact': (SG, tgt(hp=10) + '; ' + fire(1) + '; netevent rsld_has:Powerup'),
    'Bloodthirsty': (SG, 'netevent rsld_health:50; ' + tgt(hp=10) + '; ' + fire(1) + '; wait 10; netevent rsld_has:LDBloodthirstyEffectDeath'),
    'Divine': (SG, tgt(hp=10) + '; ' + fire(1, 3, 2) + '; netevent rsld_has:PowerInvulnerable; wait 40'),
    'Endless': (SG, tgt(hp=10) + '; ' + fire(1, 3, 2) + '; netevent rsld_has:PowerInfiniteAmmo; wait 40'),
    'Hopeful': (SG, 'netevent rsld_health:20; ' + tgt(hp=10) + '; ' + fire(1, 3, 2) + '; netevent rsld_has:Health; wait 40; netevent rsld_health:100'),
    'Infiltrator': (SG, tgt(hp=10) + '; ' + fire(1, 3, 2) + '; netevent rsld_has:PowerInvisibility; wait 40'),
    'Killstreaker': (SG, tgt(hp=10) + '; ' + fire(1, 3, 2) + '; netevent rsld_has:PowerSpeed; wait 40'),
    'Murderous': (SG, tgt(hp=10) + '; ' + fire(1, 3, 2) + '; netevent rsld_has:PowerDamage; wait 40'),
    'Unstoppable': (SG, tgt(hp=10) + '; ' + fire(1, 3, 2) + '; netevent rsld_has:PowerProtection; wait 40'),
    'WarmUp': (SG, 'take PowerStrength; ' + '; '.join(tgt(hp=10) + '; ' + fire(1) for _ in range(6)) + '; netevent rsld_has:PowerStrength'),
    'Violent': (SG, 'netevent rsld_cleartargets; netevent rsld_target:RifleZombie 96 10 1; netevent rsld_target:Imp 260 500 1; wait 8; netevent rsld_thas:LDViolentFear; ' + fire(1) + '; wait 10; netevent rsld_thas:LDViolentFear'),
    # debuffs (E)
    'Crippling': (SG, tgt() + '; ' + fire(1) + '; netevent rsld_thas:LDCripplingDebuff'),
    'Whittling': (SG, tgt() + '; ' + fire(1) + '; netevent rsld_thas:LDWhittlingDebuff1; netevent rsld_thas:LDWhittlingDebuff2; ' + fire(1) + '; netevent rsld_thas:LDWhittlingDebuff2'),
    'Freezing': (SG, tgt() + '; ' + fire(1) + '; netevent rsld_thas:LDFreezingSpeedDebuff'),
    'Gravitic': (SG, tgt() + '; ' + fire(1) + '; netevent rsld_thas:LDGraviticSpeedDebuff'),
    'Persistent': (SG, tgt() + '; ' + fire(1) + '; netevent rsld_thas:Health; wait 150; netevent rsld_thas:Health'),
    'Igniting': (SG, tgt() + '; ' + fire(1) + '; netevent rsld_thas:LDIgnitingActive'),
    'Incinerating': (SG, tgt(hp=10) + '; ' + fire(1) + '; netevent rsld_thas:LDIncineratingEffect'),
    # on hit, for the player
    'Sadistic': (SG, 'netevent rsld_health:50; ' + tgt() + '; ' + fire(1) + '; netevent rsld_has:Health'),
    'Painful': (SG, tgt() + '; ' + fire(1)),
    # while held
    'Determined': (SG, tgt() + '; wait 20; netevent rsld_has:LDDeterminedResistanceBuff; ' + fire(1, 3, 2) + '; netevent rsld_has:LDDeterminedResistanceBuff; wait 40'),
    'Desperate': (SG, tgt() + '; netevent rsld_health:20; ' + fire(1, 3, 2) + '; wait 10; netevent rsld_has:PowerInvulnerable; netevent rsld_health:100; wait 40'),
    'Replicating': (SG, 'take AmmoShell 10; netevent rsld_amm:; wait 80; netevent rsld_amm:'),
    'Regenerating': (SG, 'netevent rsld_health:50; wait 80; netevent rsld_has:Health; netevent rsld_health:100'),
    'Sensing': (SG, tgt(dist=400) + '; netevent rsld_count:LDSensingEffectVisual; wait 75; netevent rsld_count:LDSensingEffectVisual'),
    # pistol
    'SteadyShot': ('BrutalPistol', tgt() + '; ' + fire(1) + '; +crouch; wait 25; ' + fire(1) + '; -crouch; wait 20'),
    'Machine': ('BrutalPistol', tgt() + '; ' + fire(1, 40, 40)),
    # chainsaw / fists (melee)
    # Fists (LegenDoom's Fi slot) with BD22's canned trigger punch (rsq_no_trigger_punch 0): the rig cannot swing an arm,
    # and BD22 VR's chainsaw cuts by bar contact, which the rig's fixed pose did not reach (VR punches/cuts land the same
    # BD22 strike actors). Bloody is a Chainsaw effect in LegenDoom: forced on the shotgun here (same counter and rule;
    # the canned punch did not land on the rig in a run of its own).
    'Thieving': ('Melee_Attacks', 'rsq_no_trigger_punch 0; take Clip2 999; take AmmoShell 999; ' + '; '.join(tgt(dist=48) + '; ' + fire(1, 4, 30) for _ in range(4)) + '; netevent rsld_has:Clip2; netevent rsld_has:AmmoShell'),
    'Vampiric': ('Melee_Attacks', 'rsq_no_trigger_punch 0; netevent rsld_health:50; ' + tgt(dist=48) + '; ' + fire(2, 4, 30) + '; netevent rsld_has:Health; netevent rsld_health:100'),
    'Scavenging': ('Melee_Attacks', 'rsq_no_trigger_punch 0; ' + tgt(dist=48) + '; ' + fire(2, 4, 30) + '; netevent rsld_has:BasicArmor'),
    'Bloody': (SG, '; '.join(tgt(hp=10) + '; ' + fire(1) for _ in range(5)) + '; netevent rsld_has:LDBloodyCounter; ' + shots(1)),
    'Battlerage': ('Melee_Attacks', 'rsq_no_trigger_punch 0; ' + tgt(hp=10, dist=48) + '; ' + fire(2, 4, 30) + '; netevent rsld_has:LDBattlerageSpeedBoost; netevent rsld_has:RSLD_Haste'),
}

# map start / respawn effects: forced on six different guns, then a map change runs LD_ApplyStartBuffs and OnMapStart
START = [('Resupplying', 'Shot_Gun'), ('Restoring', 'SSG'), ('Vanguard', 'BrutalPistol'), ('Scrambling', 'Chain_Saw'),
         ('Wildfire', 'Rocket_Launcher'), ('Chronostrike', 'Plasma_Gun')]

GUNS = 'give Shot_Gun; give SSG; give BrutalPistol; give Chain_Saw; give Rocket_Launcher; give Plasma_Gun; give AmmoShell 50; give Clip1 100'

BATCHES = {
    'dmg': ['Lucky', 'Pristine', 'Raging', 'Rampaging', 'Serious', 'ProStrat', 'Berserker', 'CQC', 'AntiTree', 'Annoying', 'Patient'],
    'grp': ['Exorcist', 'Extinguishing', 'Wrangler', 'Antiair', 'Scrapper', 'Blessed', 'Heroic', 'DemonSlayer'],
    'ammo': ['DemonSlayer', 'Unlikely', 'Improbable', 'Impossible', 'Efficient', 'Replicating', 'Regenerating', 'Sensing', 'Determined', 'Desperate'],
    'kill': ['Artifact', 'Bloodthirsty', 'Divine', 'Endless', 'Hopeful', 'Infiltrator', 'Killstreaker', 'Murderous', 'Unstoppable', 'WarmUp', 'Violent'],
    'debuff': ['Crippling', 'Whittling', 'Freezing', 'Gravitic', 'Persistent', 'Igniting', 'Incinerating', 'Sadistic', 'Painful'],
    'melee': ['SteadyShot', 'Machine', 'Thieving', 'Vampiric', 'Scavenging', 'Bloody', 'Battlerage'],
}

def script(effects):
    s = ['rsld_debug %s' % os.environ.get('DBG', '1'), 'rsr_reload 0', 'god', 'notarget', GUNS, 'wait 5']
    gun = None
    for e in effects:
        g, body = CASES[e]
        if g != gun:
            s += ['use %s' % g, 'wait 120']
            gun = g
        s += ['echo RSLDT begin %s' % e, 'netevent rsld_fx:%s' % e, body, 'wait 5', 'netevent rsld_fx_clear', 'echo RSLDT end %s' % e]
    s += ['wait 10', 'quit']
    return '; '.join(x for x in s if x)

def start_script():
    s = ['rsld_debug %s' % os.environ.get('DBG', '1'), 'rsr_reload 0', 'god', 'notarget', GUNS, 'wait 5']
    for e, g in START:
        s += ['use %s' % g, 'wait 60', 'netevent rsld_fx:%s' % e]
    # LegenDoom's own RESPAWN script "LDPlayerRespawn" (LEGENDPLY.acs:12, it calls LD_ApplyStartBuffs) run with pukename,
    # then the LD mode's map start (rsld_mapstart = what runs at map tic 6 and on PlayerRespawned). A changemap cannot
    # be used: its intermission screen waits for a key on the rig.
    s += ['netevent rsld_owned', 'netevent rsld_health:40', 'take AmmoShell 40', 'take Clip1 80', 'netevent rsld_amm:',
          'wait 5', 'echo RSLDT begin START', 'pukename LDPlayerRespawn', 'wait 3', 'netevent rsld_mapstart', 'wait 10',
          'netevent rsld_has:Health', 'netevent rsld_has:BasicArmor', 'netevent rsld_has:PowerInvulnerable',
          'netevent rsld_has:PowerTimeFreezer', 'netevent rsld_has:LDScramblingEffect', 'netevent rsld_amm:',
          'wait 5', 'echo RSLDT end START', 'wait 5', 'quit']
    return '; '.join(s)

def run(batch, effects):
    sc = start_script() if batch == 'start' else script(effects)
    secs = 420 if batch == 'start' else 120 + 25 * max(1, len(effects))
    env = dict(os.environ, ARGS=os.environ.get('ARGS', '-nomonsters'))
    r = subprocess.run([os.path.join(HERE, 'ldrig.sh'), 'prove_' + batch, str(secs), sc], env=env, capture_output=True, text=True)
    print(r.stdout.strip().split('\n')[0])
    log = open('/tmp/ldrig/prove_%s.log' % batch, errors='replace').read()
    log = log[:log.find('\n', log.rfind('RSLDT end')) + 1] if ('RSLDT end' in log and batch != 'start') else log
    os.makedirs(EVD, exist_ok=True)
    names = ['START'] if batch == 'start' else effects
    for e in names:
        m = re.search(r'RSLDT begin %s\n(.*?)RSLDT end %s' % (e, e), log, re.S) or (re.search(r'RSLDT begin %s\n(.*)' % e, log, re.S) if e == 'START' else None)
        body = m.group(1) if m else '(no section: the run did not reach it)\n'
        lines = [l for l in body.split('\n') if l.startswith('RSLD') or 'probe' in l]
        tag = os.environ.get('ORDER', 'full')
        fn = os.path.join(EVD, (('%s.log' % e) if batch != 'start' else 'START_G9_Resupplying.log').replace('.log', '.log' if tag == 'full' else '.' + tag + '.log'))
        with open(fn, 'w') as f:
            f.write('# %s: rig only, not headset-confirmed. QuestZDoom 17.3 rig, full order doom2 -> brutal22test6 -> '
                    'BD_VoxelPack -> BD22 VR (test build) -> XMVE 04-07 -> LegenDoom 3.0 (ORDER=%s). Batch %s.\n' % (e, os.environ.get('ORDER', 'full'), batch))
            f.write('\n'.join(lines) + '\n')
        print('---', e, '(%d lines)' % len(lines))
        for l in lines[:14]:
            print('   ', l[:200])

if __name__ == '__main__':
    b = sys.argv[1]
    if b == 'list':
        for k, v in BATCHES.items():
            print(k, ' '.join(v))
        sys.exit(0)
    eff = sys.argv[2:] or BATCHES.get(b, [])
    run(b, eff)
