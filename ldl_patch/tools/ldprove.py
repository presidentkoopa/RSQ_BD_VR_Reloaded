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
# ldrig.sh's orders (default full = the owner's order since 2026-11-06 round 2: LegenDoom right after doom2)
ORDERS = {
    'full': 'doom2 -> LegenDoom 3.0 -> brutal22test6 -> BD_VoxelPack -> BD22 VR (test build) -> XMVE 04-07',
    'ldfirst': 'doom2 -> LegenDoom 3.0 -> brutal22test6 -> BD_VoxelPack -> BD22 VR (test build) -> XMVE 04-07',
    'ldlast': 'doom2 -> brutal22test6 -> BD_VoxelPack -> BD22 VR (test build) -> XMVE 04-07 -> LegenDoom 3.0',
    'nold': 'doom2 -> brutal22test6 -> BD_VoxelPack -> BD22 VR (test build) -> XMVE 04-07 (no LegenDoom)',
}
EVD = os.path.join(os.path.dirname(HERE), 'evidence', 'ldmode')

def fire(n=1, hold=3, gap=45):
    return '; '.join('+attack; wait %d; -attack; wait %d' % (hold, gap) for _ in range(n))

def shots(n, cls='BaronofHell2', hp=30000, gap=45):	# a fresh still target before every shot (BD22 monsters change class when hurt)
    return '; '.join(tgt(cls, hp) + '; ' + fire(1, 3, gap) for _ in range(n))

TGT_MODE = [1]	# round 4: 2 = a hostile still target (ldprove round4: seekers, sprays and autoaim take it)

def tgt(cls='BaronofHell2', hp=30000, dist=96, friendly=None):
    return 'netevent rsld_cleartargets; netevent rsld_target:%s %d %d %d; wait 8' % (cls, dist, hp, TGT_MODE[0] if friendly is None else friendly)

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

# round 2 (item 1): one trigger pull = one pull on the Rifle (its casing EmptyBrass made a 2nd pull at T+1) and the
# rocket launcher (RocketGlassBreaker, LiquidExplosionEffectSpawner made shots); the once-per-pull effects re-proven.
# Key 'Effect@Gun'. Upgrading at LegenDoom's level 5 (free shot 64/256).
def taps(n, gap=45):
    return '; '.join('netevent rsld_amm:; +attack; wait 1; -attack; wait %d' % gap for _ in range(n)) + '; netevent rsld_amm:'
for _g in ('Rifle', 'Rocket_Launcher'):
    _gap = 45 if _g == 'Rifle' else 70
    _pre = tgt() + '; '
    for _e in ('Lucky', 'NanoCircuit', 'Decaying', 'Agitating', 'Stealth'):
        CASES['%s@%s' % (_e, _g)] = (_g, _pre + taps(4, _gap))
    CASES['Upgrading@%s' % _g] = (_g, 'give LD%sUpgradeLevel 5; ' % ('Chaingun' if _g == 'Rifle' else 'RocketLauncher') + _pre + taps(8, _gap))

# ---------------------------------------------------------------- round 2 (2026-11-06): ONE engine run for every check
# (owner 17:05: no per-effect runs). Sections 'RSLDT begin <name>' ... 'end'; one evidence file per section.
def amm():
    return 'netevent rsld_amm:'

def r2_sections():
    S = []
    def sec(name, gun, body, fx=None):
        S.append((name, gun, body, fx))
    B = tgt()                     # a still Baron, 30000 hp, 96 ahead
    # item 1: the rocket launcher's free shot now refunds (ammo seen a tic before the rocket)
    if os.environ.get('R2_ALL'):	# passed in run 5 (prove_round2 #1): evidence R2_1_Upgrading_RL.log; not re-run
      sec('R2_1_Upgrading_RL', 'Rocket_Launcher', 'give LDRocketLauncherUpgradeLevel 5; ' + B + '; ' + taps(8, 70), 'Upgrading')
    # item 2: whose title map / HUD / sounds win; the sound lumps
    # item 3: Plasmatic / Gyrojet, True Bullets on and off
    for tb in (1, 0):
        sec('R2_3_Plasmatic_Shotgun_TB%d' % tb, 'Shot_Gun', 'sv_rsq_true_bullets %d; ' % tb + B + '; ' + fire(1, 3, 45), 'Plasmatic')
    sec('R2_3_Plasmatic_SSG', 'SSG', B + '; ' + fire(1, 3, 70), 'Plasmatic')
    sec('R2_3_Plasmatic_Pistol', 'BrutalPistol', B + '; ' + fire(1, 3, 45), 'Plasmatic')
    sec('R2_3_Gyrojet_Rifle_TB0', 'Rifle', 'sv_rsq_true_bullets 0; ' + B + '; ' + fire(1, 1, 45), 'Gyrojet')
    sec('R2_3_Gyrojet_Shotgun_TB1', 'Shot_Gun', 'sv_rsq_true_bullets 1; ' + B + '; ' + fire(1, 3, 45), 'Gyrojet')
    # item 4: LegenDoom's own visuals (counted while they play), no quakes
    sec('R2_4_Explosive', 'Shot_Gun', B + '; +attack; wait 3; -attack; wait 4; netevent rsld_count:LDExplosiveBulletPuff; wait 40', 'Explosive')
    sec('R2_4_Blastwave', 'Shot_Gun', B + '; +attack; wait 3; -attack; wait 4; netevent rsld_count:LDBlastwave; wait 40', 'Blastwave')
    sec('R2_4_Gauss', 'Shot_Gun', B + '; +attack; wait 3; -attack; wait 3; netevent rsld_count:LDGaussBulletPuff; wait 40', 'Gauss')
    sec('R2_4_Flak', 'BrutalPistol', tgt('Cacodemon_', 30000, 160) + '; +attack; wait 2; -attack; wait 6; netevent rsld_count:LDFlakEffectExplosion; wait 40', 'Flak')
    sec('R2_4_Quakes', None, 'LD_quakes')
    # item 5: Choked patterns
    sec('R2_5_Choked_Shotgun', 'Shot_Gun', B + '; ' + fire(1, 3, 45), 'Choked')
    sec('R2_5_Choked_SSG', 'SSG', B + '; ' + fire(1, 3, 70), 'Choked')
    # item 6: Machine 17.5 a second; Bloody +20% per 5 kills
    sec('R2_6_Machine', 'BrutalPistol', 'give BDPistolAmmo 15; ' + B + '; +attack; wait 24; -attack; wait 30; ' + amm(), 'Machine')
    sec('R2_6_Bloody', 'Shot_Gun', '; '.join(tgt(hp=10) + '; ' + fire(1, 3, 40) for _ in range(11)) + '; netevent rsld_has:LDBloodyCounter; ' + B + '; ' + fire(1, 3, 40), 'Bloody')
    # item 7: Perfect's jam on each gun (a wall miss jams; while jammed the trigger does nothing; 1 s later it fires)
    def jam(g):
        return ('netevent rsld_cleartargets; wait 2; ' + amm() + '; +attack; wait 2; -attack; wait 8; ' + amm()
                + '; +attack; wait 6; -attack; wait 6; ' + amm() + '; wait 40; +attack; wait 6; -attack; wait 20; ' + amm())
    for g in ('BrutalPistol', 'Rifle', 'MiniGun', 'BrutalRevolver'):
        sec('R2_7_Perfect_' + g, g, ('give RSQ_MinigunAmmo 200; ' if g == 'MiniGun' else '') + jam(g), 'Perfect')
    sec('R2_7_Perfect_OffPistol', 'BrutalPistol',
        'give RSQ_Off_BrutalPistol; +user3; wait 2; -user3; wait 60; give BDPistolAmmoOff 15; netevent rsld_cleartargets; '
        '+attack; wait 2; -attack; wait 14; netevent rsld_has:BDPistolAmmoOff; qz_ltrigger 1; wait 6; qz_ltrigger 0; wait 6; '
        'netevent rsld_has:BDPistolAmmoOff; wait 40; qz_ltrigger 1; wait 6; qz_ltrigger 0; wait 20; netevent rsld_has:BDPistolAmmoOff; +user3; wait 2; -user3; wait 40', 'Perfect')
    # item 9: Marksman / Decaying, fixed (b)
    sec('R2_9_Marksman', 'Shot_Gun', B + '; ' + fire(1, 3, 45), 'Marksman')
    sec('R2_9_Decaying', 'Shot_Gun', B + '; ' + fire(3, 3, 45), 'Decaying')
    # item 10: Favoured never rolls
    sec('R2_10_Favoured', 'Shot_Gun', 'netevent rsld_reroll:Favoured; netevent rsld_reroll:Lucky')
    # item 11: a BD22-only ammo pickup (Gas) counts for Scrounger
    sec('R2_11_Scrounger_Gas', 'Shot_Gun', 'netevent b_zero:Gas; netevent b_take:Gas; wait 60; netevent b_report', 'Scrounger')
    # item 13: a friendly BD22 marine near you: Medic / Armorer share, Comrade scales
    MAR = 'netevent rsld_cleartargets; netevent rsld_target:Marine_Rifle 120 40 1; wait 8; '
    sec('R2_13_Medic_marine', 'Shot_Gun', MAR + 'netevent b_hp:40; netevent b_take:Stimpack2; wait 60; netevent rsld_thas:Health', 'Medic')
    sec('R2_13_Armorer_marine', 'Shot_Gun', MAR + 'netevent b_ap:0; netevent b_take:LightArmor; wait 60; netevent rsld_thas:BasicArmor', 'Armorer')
    sec('R2_13_Comrade_marine', 'Shot_Gun', 'netevent rsld_cleartargets; netevent rsld_target:BaronofHell2 96 30000 1; netevent rsld_target:Marine_Rifle 300 100 1; wait 8; ' + fire(1, 3, 45), 'Comrade')
    sec('R2_2_LoadOrder', None, 'netevent rsld_loadorder; soundlist')   # last: a probe crash cannot cost the rest
    return S

# passed in prove_round2 run #2 (engine launch 6); evidence in ldl_patch/evidence/ldmode/R2_*.log; not re-run (owner)
R2_DONE = ['R2_3_Plasmatic_Shotgun_TB1', 'R2_3_Plasmatic_Shotgun_TB0', 'R2_3_Plasmatic_SSG', 'R2_3_Plasmatic_Pistol',
           'R2_3_Gyrojet_Rifle_TB0', 'R2_3_Gyrojet_Shotgun_TB1', 'R2_4_Explosive', 'R2_4_Blastwave', 'R2_4_Gauss', 'R2_4_Flak',
           'R2_4_Quakes', 'R2_5_Choked_Shotgun', 'R2_5_Choked_SSG', 'R2_6_Machine', 'R2_6_Bloody', 'R2_7_Perfect_Rifle',
           'R2_7_Perfect_BrutalRevolver', 'R2_9_Marksman', 'R2_9_Decaying']

def round2_script():
    secs = [x for x in r2_sections() if os.environ.get('R2_ALL') or x[0] not in R2_DONE]
    s = ['rsld_debug %s' % os.environ.get('DBG', '1'), 'rsr_reload 0', 'god', 'notarget', 'give all', GUNS,
         'give RSQ_MinigunAmmo 300; give BrutalRevolver; give MiniGun; give Rifle', 'wait 5']
    gun = None
    for name, g, body, fx in secs:
        if g and g != gun:
            s += ['use %s' % g, 'wait 90']
            gun = g
        s += ['echo RSLDT begin %s' % name]
        if fx:
            s += ['netevent rsld_fx:%s' % fx]
        s += [body, 'wait 5']
        if fx:
            s += ['netevent rsld_fx_clear']
        s += ['echo RSLDT end %s' % name]
    s += ['wait 10', 'quit']
    return '; '.join(x for x in s if x), [x[0] for x in secs]

# map start / respawn effects: forced on six different guns, then a map change runs LD_ApplyStartBuffs and OnMapStart
START = [('Resupplying', 'Shot_Gun'), ('Restoring', 'SSG'), ('Vanguard', 'BrutalPistol'), ('Scrambling', 'Chain_Saw'),
         ('Wildfire', 'Rocket_Launcher'), ('Chronostrike', 'Plasma_Gun')]

GUNS = 'give Shot_Gun; give SSG; give BrutalPistol; give Chain_Saw; give Rocket_Launcher; give Plasma_Gun; give Rifle; give AmmoShell 50; give Clip1 100; give AmmoRocket 30'

BATCHES = {
    'dmg': ['Lucky', 'Pristine', 'Raging', 'Rampaging', 'Serious', 'ProStrat', 'Berserker', 'CQC', 'AntiTree', 'Annoying', 'Patient'],
    'grp': ['Exorcist', 'Extinguishing', 'Wrangler', 'Antiair', 'Scrapper', 'Blessed', 'Heroic', 'DemonSlayer'],
    'ammo': ['DemonSlayer', 'Unlikely', 'Improbable', 'Impossible', 'Efficient', 'Replicating', 'Regenerating', 'Sensing', 'Determined', 'Desperate'],
    'kill': ['Artifact', 'Bloodthirsty', 'Divine', 'Endless', 'Hopeful', 'Infiltrator', 'Killstreaker', 'Murderous', 'Unstoppable', 'WarmUp', 'Violent'],
    'debuff': ['Crippling', 'Whittling', 'Freezing', 'Gravitic', 'Persistent', 'Igniting', 'Incinerating', 'Sadistic', 'Painful'],
    'melee': ['SteadyShot', 'Machine', 'Thieving', 'Vampiric', 'Scavenging', 'Bloody', 'Battlerage'],
    'pull': ['%s@%s' % (e, g) for g in ('Rifle', 'Rocket_Launcher') for e in ('Lucky', 'NanoCircuit', 'Decaying', 'Upgrading', 'Agitating', 'Stealth')],
}

def script(effects):
    s = ['rsld_debug %s' % os.environ.get('DBG', '1'), 'rsr_reload 0', 'god', 'notarget', GUNS, 'wait 5']
    gun = None
    for e in effects:
        g, body = CASES[e]
        if g != gun:
            s += ['use %s' % g, 'wait 120']
            gun = g
        s += ['echo RSLDT begin %s' % e, 'netevent rsld_fx:%s' % e.split('@')[0], body, 'wait 5', 'netevent rsld_fx_clear', 'echo RSLDT end %s' % e]
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


# ---------------------------------------------------------------- round 3 (2026-11-06 evening): ONE batched run
# (Round 3 rules: no per-effect runs). R3a's sections (G3 missile riders, G4 BFG, G6 ammo, the small items) and R3b's
# (G5 / G7: R3B_SECTIONS, read from /home/claude/ldmerge/R3B_SECTIONS.py when R3b wrote it). Evidence: R3_<name>.log.
RL, PR, BF = 'Rocket_Launcher', 'Plasma_Gun', 'BIG_FUCKING_GUN'

def r3_sections():
    S = []
    def sec(name, gun, body, fx=None):
        S.append((name, gun, body, fx))
    def far(d=320, hp=30000, cls='BaronofHell2'):
        return tgt(cls, hp, d)
    rk = lambda: fire(1, 3, 70)
    bfg = lambda: fire(1, 3, 110)
    pl = lambda: fire(1, 3, 40)
    none = 'netevent rsld_cleartargets; wait 2'
    # ---- G3 on the rocket launcher
    for e, body in [
        ('Kinetic', far() + '; ' + rk()), ('Penetrating', far() + '; ' + rk()), ('Tricky', none + '; ' + fire(1, 3, 90)),
        ('Spreadfire', far() + '; ' + rk() + '; ' + rk()), ('Cluster', far() + '; ' + rk()),
        ('Redirecting', none + '; ' + fire(1, 3, 90)), ('Mysterious', none + '; ' + fire(1, 3, 60)), ('Bouncy', none + '; ' + fire(1, 3, 90)),
        ('Sluggish', far(900) + '; ' + fire(1, 3, 230)), ('Hyper', none + '; ' + fire(1, 3, 50)), ('Arcing', none + '; ' + fire(1, 3, 160)),
        ('GroupTherapy', 'netevent rsld_cleartargets; netevent rsld_target:Imp 320 10 1; netevent rsld_target:BaronofHell2 420 30000 1; wait 8; ' + rk()),
        ('Proximity', far(620) + '; ' + fire(1, 3, 160)), ('Illuminating', far() + '; ' + rk()), ('Seeker', far(400) + '; ' + rk()),
        ('Accelerator', far(400) + '; ' + rk()), ('Vidmaster', far() + '; ' + rk()), ('HighExplosive', far() + '; ' + rk()),
        ('ShapedCharge', far() + '; ' + rk()), ('Spamtastic', none + '; ' + fire(1, 3, 60)), ('Concentrating', far(700) + '; ' + rk()),
        ('Vacuum', far(500) + '; ' + rk()),
        ('TORGUE', 'netevent rsld_cleartargets; netevent rsld_target:Imp 320 10 1; netevent rsld_target:BaronofHell2 360 30000 1; wait 8; ' + rk()),
        ('Irradiated', far(700) + '; ' + rk()), ('Overkill', far(400) + '; ' + fire(1, 3, 90)), ('Goldeneye', far(320) + '; ' + fire(1, 3, 120)),
        ('Plasmatic', far(320) + '; ' + rk()), ('Raycaster', far(320) + '; ' + rk()),
        ('Nuclear', amm() + '; ' + far() + '; ' + rk() + '; ' + amm()),
    ]:
        sec('R3_%s_RL' % e, RL, body, e)
    # ---- G3 on the plasma rifle
    for e in ('Penetrating', 'Tricky', 'Bouncy', 'Spreadfire', 'Cluster', 'Suppression', 'Waveform', 'Seeker', 'Hyper', 'Sluggish', 'Irradiated', 'Spamtastic'):
        sec('R3_%s_PR' % e, PR, far(400) + '; ' + pl(), e)
    # ---- G4 on the BFG
    for e, body in [
        ('Annihilating', far() + '; ' + bfg()), ('Energetic', far() + '; ' + bfg()), ('Energizing', none + '; ' + fire(1, 3, 160)),
        ('Nova', far() + '; ' + bfg()), ('Prototype', far() + '; ' + bfg()), ('Scattering', amm() + '; ' + far() + '; ' + bfg() + '; ' + amm()),
        ('Shockwave', far() + '; ' + bfg()), ('Stasis', far(320, 30000, 'Imp') + '; ' + bfg()), ('Kinetic', far() + '; ' + bfg()),
        ('Cluster', far() + '; ' + bfg()),
    ]:
        sec('R3_%s_BFG' % e, BF, body, e)
    # ---- G6 on the pump shotgun (owner Q7: the magazine): last-round shots take the magazine down to 1 first
    last = 'take ShotgunAmmo 99; give ShotgunAmmo 1; wait 2; ' + amm()
    for e, body in [
        ('Nuclear', amm() + '; ' + tgt() + '; ' + fire(2, 3, 45) + '; ' + amm()),
        ('Unknown', 'give PowerInvisibility; ' + amm() + '; ' + tgt() + '; ' + fire(2, 3, 45) + '; ' + amm() + '; take PowerInvisibility'),
        ('Illegal', 'give ShotgunAmmo 8; ' + tgt() + '; ' + fire(1, 3, 45) + '; ' + last + '; ' + tgt('Imp', 30000) + '; ' + fire(2, 3, 45) + '; netevent rsld_thas:LDIllegalActive; ' + amm()),
        ('Optional', 'give ShotgunAmmo 8; ' + tgt() + '; ' + fire(1, 3, 45) + '; ' + last + '; ' + tgt() + '; ' + fire(2, 3, 45) + '; ' + amm()),
        ('Transmogrifier', 'give ShotgunAmmo 8; ' + tgt() + '; ' + fire(1, 3, 45) + '; ' + last + '; netevent rsld_has:Clip2; ' + fire(1, 3, 45) + '; netevent rsld_has:Clip2; ' + amm()),
        ('Unfathomable', 'give ShotgunAmmo 8; ' + amm() + '; ' + tgt() + '; ' + fire(1, 3, 60) + '; ' + amm()),
        ('Recycling', 'take Clip2 50; take AmmoRocket 20; take AmmoCell 100; ' + tgt() + '; ' + fire(3, 3, 45) + '; netevent rsld_has:Clip2; netevent rsld_has:AmmoCell; netevent rsld_has:AmmoRocket'),
        ('Overflowing', 'give all; give ShotgunAmmo 8; ' + tgt() + '; ' + fire(1, 3, 60)),
    ]:
        sec('R3_%s_SG' % e, SG, body, e)
    sec('R3_Unfathomable_RL', RL, amm() + '; ' + far() + '; ' + rk() + '; ' + amm(), 'Unfathomable')
    sec('R3_Overflowing_RL', RL, 'give all; ' + far() + '; ' + rk(), 'Overflowing')
    # ---- small items
    # (b) Upgrading: a full-ammo pickup of BD22-only ammo (Gas: like cells) feeds the meter
    sec('R3_b_Upgrading_Gas', SG, 'netevent b_fill:Gas; netevent b_take:Gas; wait 60; netevent b_take:GrenadeAmmo; wait 60', 'Upgrading')
    # (c) passives only for the legendary gun in hand: Hoarder on the shotgun, a shell pickup with the shotgun in hand, then
    # with the Rifle in hand (no Hoarder bonus)
    sec('R3_c_Hoarder_hand', SG, 'netevent b_zero:AmmoShell; netevent b_take:AmmoShell; wait 60; netevent rsld_has:AmmoShell; echo RSLDT rifle in hand now; '
        'use Rifle; wait 90; netevent b_zero:AmmoShell; netevent b_take:AmmoShell; wait 60; netevent rsld_has:AmmoShell; use Shot_Gun; wait 90', 'Hoarder')
    # (d) alt-fire stand-down: Seeker on the rocket launcher (RSA_Opt_RLLock taken), Burst on the pistol (PistolBurstFire)
    sec('R3_d_Seeker_standdown', RL, 'wait 5; netevent rsld_has:RSLD_AltDown; netevent rsld_has:RSA_Opt_RLLock', 'Seeker')
    sec('R3_d_Seeker_cleared', RL, 'wait 5; netevent rsld_has:RSLD_AltDown; netevent rsld_has:RSA_Opt_RLLock')
    sec('R3_d_Burst_standdown', 'BrutalPistol', 'give PistolBurstFire; wait 5; netevent rsld_has:RSLD_AltDown; netevent rsld_has:PistolBurstFire', 'Burst')
    # (e) LegenDoom's non-gun sounds behind rsld_mute_ld_sounds (rig: -nosound, so the code path is logged)
    sec('R3_e_Sounds', SG, tgt() + '; netevent rsld_aura; wait 10; netevent rsld_auras; netevent rsld_jingle:Lucky 1; netevent rsld_jingle:Illegal 2; '
        'rsld_mute_ld_sounds 1; wait 5; netevent rsld_auras; netevent rsld_jingle:Lucky 3; rsld_mute_ld_sounds 0; wait 5; netevent rsld_auras')
    return S

def r3b_sections():
    f = '/home/claude/ldmerge/R3B_SECTIONS.py'
    if not os.path.exists(f):
        return []
    g = {'fire': fire, 'shots': shots, 'tgt': tgt, 'amm': amm, 'taps': taps}
    exec(open(f).read(), g)
    return list(g.get('SECTIONS', []))

def round3_script(nold=False):
    secs = r3_sections() + r3b_sections()
    only = os.environ.get('ONLY')
    if only:
        secs = [x for x in secs if any(o in x[0] for o in only.split(','))]
    s = ['rsld_debug %s' % os.environ.get('DBG', '1'), 'rsr_reload 0', 'god', 'notarget', 'give all', GUNS,
         'give RSQ_MinigunAmmo 300; give BrutalRevolver; give MiniGun; give Rifle; give BIG_FUCKING_GUN; give Plasma_Gun; give Rocket_Launcher; give AmmoCell 300; give AmmoRocket 50', 'wait 5']
    gun = None
    for name, g, body, fx in secs:
        if g and g != gun:
            s += ['use %s' % g, 'wait 90']
            gun = g
        s += ['echo RSLDT begin %s' % name]
        if fx:
            s += ['netevent rsld_fx:%s' % fx]
        s += [body, 'wait 5']
        if fx:
            s += ['netevent rsld_fx_clear']
        s += ['echo RSLDT end %s' % name]
    s += ['wait 10', 'quit']
    return '; '.join(x for x in s if x), [x[0] for x in secs]

# ---------------------------------------------------------------- round 4 (2026-11-06 evening): ONE batched run, in the
# open arena (make_ldarena.py, loaded last: MAP01 replaced), hostile still targets (rsld_target arg 3 = 2), the player put
# back at the arena start before every section (rsld_home), ammo topped up (give ammo). Order: the round-4 changes first,
# then round 3's sections that did not show (direct hits, seeking, in-flight, Energizing's heal, the BFG fixes, R3b's
# empty ones), then the rest of rounds 3 / 3b again (regression). Evidence: R4_<name>.log and R3*_<name>.log.
ARENA = '/tmp/ldrig/ldarena.wad'
HOME = 'netevent rsld_home -1600 0'
R3_UNSHOWN = ['R3_Goldeneye_RL', 'R3_Kinetic_RL', 'R3_Kinetic_BFG', 'R3_Stasis_BFG', 'R3_GroupTherapy_RL', 'R3_Plasmatic_RL',
              'R3_Seeker_RL', 'R3_Seeker_PR', 'R3_Proximity_RL', 'R3_Mysterious_RL', 'R3_Hyper_RL', 'R3_Hyper_PR', 'R3_Sluggish_RL',
              'R3_Sluggish_PR', 'R3_Arcing_RL', 'R3_Spamtastic_RL', 'R3_Spamtastic_PR', 'R3_Energizing_BFG', 'R3_Annihilating_BFG',
              'R3_Unfathomable_RL', 'R3_Unfathomable_SG', 'R3_Overflowing_SG', 'R3_Overflowing_RL', 'R3_Energetic_BFG', 'R3_Nova_BFG',
              'R3_Scattering_BFG', 'R3_Shockwave_BFG', 'R3_Cluster_BFG',
              'R3B_Burst_RL', 'R3B_Extended_CS', 'R3B_Lacerating', 'R3B_Imaginary', 'R3B_Quickdraw_BFG', 'R3B_Quickdraw_switch',
              'R3B_Perfect_DualPistols', 'R3B_Perfect_DualRifles']

def r4_sections():
    S = []
    def sec(name, gun, body, fx=None):
        S.append((name, gun, body, fx))
    RL, PR, BF, PI, SG, FI = 'Rocket_Launcher', 'Plasma_Gun', 'BIG_FUCKING_GUN', 'BrutalPistol', 'Shot_Gun', 'Melee_Attacks'
    hold = lambda t, after=30: '+attack; wait %d; -attack; wait %d' % (t, after)
    H = lambda cls='BaronofHell2', hp=30000, d=96: tgt(cls, hp, d, 2)
    # 1. DualWield: give all gave BD22's DualPistols: the gate takes it (no DualWield legendary); DualWield forced on the
    # pistol: DualPistols unlocked; cleared: taken again
    sec('R4_DualWield', PI, 'wait 10; netevent rsld_has:DualPistols; netevent rsld_fx:DualWield; wait 12; netevent rsld_has:DualPistols; '
        'netevent rsld_fx_clear; wait 12; netevent rsld_has:DualPistols; netevent rsld_has:BrutalPistol')
    # 2. SixShooter at half speed: a held trigger (cadence x0.50 lines), its damage
    sec('R4_SixShooter_PI', PI, 'give BDPistolAmmo 15; ' + H() + '; ' + hold(60), 'SixShooter')
    # 3. the streams: Beam (PR, BFG), Blazing (RL, PR, BFG), Prototype (BFG); trigger held, then let go
    sec('R4_Beam_PR', PR, amm() + '; ' + H(d=400) + '; ' + hold(50) + '; ' + amm(), 'Beam')
    sec('R4_Beam_BFG', BF, amm() + '; ' + H(d=400) + '; ' + hold(70) + '; ' + amm(), 'Beam')
    sec('R4_Blazing_RL', RL, amm() + '; ' + H(d=160) + '; ' + hold(50) + '; ' + amm(), 'Blazing')
    sec('R4_Blazing_PR', PR, amm() + '; ' + H(d=160) + '; ' + hold(40) + '; ' + amm(), 'Blazing')
    sec('R4_Blazing_BFG', BF, amm() + '; ' + H(d=160) + '; ' + hold(50) + '; ' + amm(), 'Blazing')
    sec('R4_Prototype_BFG', BF, amm() + '; ' + H(d=400) + '; ' + hold(50, 60) + '; ' + amm(), 'Prototype')
    # 4. Arcing / Proximity at our speed (open arena: the arc, the bounces, the fuse; Proximity deploys and drifts to a
    # hostile Baron near where it stops: RL k 2.5 -> about 1000 out, PR k 2.4 -> 950, BFG k from our ball's speed)
    sec('R4_Arcing_RL', RL, 'netevent rsld_cleartargets; wait 2; ' + fire(1, 3, 150), 'Arcing')
    sec('R4_Proximity_RL', RL, H(d=1150) + '; ' + fire(1, 3, 200), 'Proximity')
    sec('R4_Proximity_PR', PR, H(d=1100) + '; ' + fire(1, 3, 200), 'Proximity')
    sec('R4_Proximity_BFG', BF, H(d=500) + '; ' + fire(1, 3, 200), 'Proximity')
    # 5. the fists: both hands carry the Fists slot's legendary, damage x swing speed (test punches: netevent
    # rsld_punch:<hand> <m/s x 100>, recorded as rsq/fists.zs records a real one)
    sec('R4_Fists_both_Lunging', FI, 'rsq_no_trigger_punch 1; ' + H(d=48) + '; netevent rsld_punch:1 450; wait 20; ' + H(d=48) + '; netevent rsld_punch:0 700; wait 20; '
        + H(d=48) + '; netevent rsld_punch:0 150; wait 20', 'Lunging')
    sec('R4_Chargeup_FI', FI, 'rsq_no_trigger_punch 1; ' + H(d=48) + '; +attack; wait 45; -attack; wait 5; netevent rsld_punch:0 300; wait 20; '
        + 'qz_ltrigger 1; wait 25; qz_ltrigger 0; wait 5; netevent rsld_punch:1 700; wait 20', 'Chargeup')
    sec('R4_OnePunch_FI', FI, 'rsq_no_trigger_punch 1; ' + H(d=48) + '; +attack; wait 8; netevent rsld_punch:0 500; wait 4; -attack; wait 30; netevent rsld_has:LDOnePunchCooldown', 'OnePunch')
    sec('R4_Blaster_off', FI, 'rsq_no_trigger_punch 1; ' + H(d=200) + '; qz_ltrigger 1; wait 50; qz_ltrigger 0; wait 30', 'Blaster')
    sec('R4_NorthernStar_blow', FI, 'rsq_no_trigger_punch 1; ' + H(d=48) + '; netevent rsld_punch:0 450; wait 8; netevent rsld_punch:1 450; wait 8; netevent rsld_punch:0 450; wait 5; '
        'netevent rsld_thas:LDNorthernStarStunActive; wait 75; netevent rsld_thas:Health', 'NorthernStar')
    # 6. Transmogrifier / Overflowing count every BD22 ammo (Upgrading's mapping): the pump's last round with only Gas
    # left of the other kinds; Overflowing with only GrenadeAmmo at its maximum
    nocl = 'take Clip2 999; take Clip1 999; take RSQ_MinigunAmmo 999; take Mauser9mm 999; take SniperAmmo 999; take AmmoCell 999; take SoulAmmo 999; take AmmoRocket 999; take GrenadeAmmo 999; take AmmoM202 999; take MiniHellRocketAmmo 999; take Nuke 999; take DevastatorAmmo 999'
    sec('R4_Transmogrifier_Gas', SG, nocl + '; give Gas 50; netevent rsld_has:Gas; take ShotgunAmmo 99; give ShotgunAmmo 1; wait 2; ' + H() + '; ' + fire(1, 3, 45) + '; netevent rsld_has:Gas; ' + amm(), 'Transmogrifier')
    unmax = 'take AmmoRocket 1; take AmmoCell 1; take AmmoShell 1; take Clip2 1; take Clip1 1; take RSQ_MinigunAmmo 1; take Mauser9mm 1; take SniperAmmo 1; take Gas 1; take SoulAmmo 1; take AmmoM202 1; take MiniHellRocketAmmo 1; take Nuke 1; take DevastatorAmmo 1'
    sec('R4_Overflowing_Grenades', SG, unmax + '; give GrenadeAmmo 999; ' + H() + '; ' + fire(1, 3, 45), 'Overflowing')
    # 7. QuestZDoom's menu / info-screen sounds under the mute option (rig: -nosound, the code path is logged)
    sec('R4_MenuSounds', SG, 'netevent rsld_menusnd; pukename LDMenuToggle; wait 5; pukename LDMenuToggle; wait 5; rsld_mute_ld_sounds 1; wait 3; netevent rsld_menusnd; '
        'pukename LDMenuToggle; wait 5; pukename LDMenuToggle; wait 5; rsld_mute_ld_sounds 0; wait 3; netevent rsld_menusnd')
    return S

def round4_script():
    TGT_MODE[0] = 2
    r3 = {x[0]: x for x in r3_sections() + r3b_sections()}
    fixes = {	# round 3's sections that need more for the open arena (each: name -> new body)
        'R3_Energizing_BFG': 'netevent rsld_cleartargets; wait 2; netevent rsld_health:40; ' + fire(1, 3, 40) + '; +forward; wait 25; -forward; wait 90; netevent rsld_has:Health; netevent rsld_health:100',
        'R3B_Quickdraw_switch': 'rsq_switch_log 1; rsq_instant_switch 0; use Shot_Gun; wait 30; use BrutalPistol; wait 30; rsq_instant_switch 1; rsq_switch_log 0',
        'R3B_Perfect_DualPistols': 'netevent rsld_keepdual 1; use BrutalPistol; wait 60; ' + r3['R3B_Perfect_DualPistols'][2] + '; netevent rsld_keepdual 0; wait 10',
        'R3B_Perfect_DualRifles': 'use Rifle; wait 60; ' + r3['R3B_Perfect_DualRifles'][2],
    }
    unshown = [r3[n] for n in R3_UNSHOWN if n in r3]
    unshown = [(n, g, fixes.get(n, b), fx) for (n, g, b, fx) in unshown]
    dual = [x for x in unshown if 'Perfect_Dual' in x[0]]
    unshown = [x for x in unshown if 'Perfect_Dual' not in x[0]]
    rest = [x for x in r3_sections() + r3b_sections() if x[0] not in R3_UNSHOWN]
    secs = r4_sections() + unshown + rest + dual	# the dual guns last (they swap BD22's pistol / rifle)
    only = os.environ.get('ONLY')
    if only:
        secs = [x for x in secs if any(o in x[0] for o in only.split(','))]
    s = ['rsld_debug %s' % os.environ.get('DBG', '1'), 'rsr_reload 0', 'god', 'notarget', 'give all', GUNS,
         'give RSQ_MinigunAmmo 300; give BrutalRevolver; give MiniGun; give Rifle; give BIG_FUCKING_GUN; give Plasma_Gun; give Rocket_Launcher; give AmmoCell 300; give AmmoRocket 50', 'wait 5']
    gun = None
    for name, g, body, fx in secs:
        s += [HOME, 'give ammo']
        if g and g != gun:
            s += ['use %s' % g, 'wait 100']
            gun = g
        if not g:
            gun = None
        s += ['echo RSLDT begin %s' % name, 'netevent rsld_amm:']
        if fx:
            s += ['netevent rsld_fx:%s' % fx]
        s += [body, 'wait 5']
        if fx:
            s += ['netevent rsld_fx_clear']
        s += ['echo RSLDT end %s' % name]
    s += ['wait 10', 'quit']
    return '; '.join(x for x in s if x), [x[0] for x in secs]

def run(batch, effects):
    if batch == 'round4':
        sc, effects = round4_script()
        os.environ['EXTRA'] = (os.environ.get('EXTRA', '') + ' ' + ARENA).strip()
        subprocess.run([sys.executable, '-I', os.path.join(HERE, 'make_ldarena.py'), ARENA], check=True, capture_output=True)
    elif batch == 'round2':
        sc, effects = round2_script()
    elif batch == 'round3':
        sc, effects = round3_script()
    elif batch == 'round4':
        pass
    else:
        sc = start_script() if batch == 'start' else script(effects)
    secs = int(os.environ.get('SECS', 420 if batch == 'start' else 120 + 25 * max(1, len(effects))))
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
        lines = [l for l in body.split('\n') if l.startswith('RSLD') or 'probe' in l or (batch in ('round2', 'round3', 'round4') and (l.startswith('B probe') or l.startswith('RSQ ') or re.match(r'\s*\d+\. ', l) or 'LD_quakes' in l))]
        tag = os.environ.get('ORDER', 'full')
        fn = os.path.join(EVD, (('%s.log' % e.replace('@', '_on_')) if batch != 'start' else 'START_G9_Resupplying.log').replace('.log', '.log' if tag == 'full' else '.' + tag + '.log'))
        with open(fn, 'w') as f:
            f.write('# %s: rig only, not headset-confirmed. QuestZDoom 17.3 rig, %s (ORDER=%s). Batch %s.\n' % (e, ORDERS.get(tag, tag), tag, batch))
            f.write('\n'.join(lines) + '\n')
        print('---', e, '(%d lines)' % len(lines))
        for l in lines[:14]:
            print('   ', l[:200])

if __name__ == '__main__':
    b = sys.argv[1]
    if b == 'list':
        for k, v in BATCHES.items():
            print(k, ' '.join(v))
        print('round4', ' '.join(round4_script()[1]))
        sys.exit(0)
    eff = sys.argv[2:] or BATCHES.get(b, [])
    run(b, eff)
