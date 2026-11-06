# LegenDoom x BD22 VR: compatibility patch (LD_BD22VR_Patch.pk3)

A small patch that lets **LegenDoom 3.0** run on top of **BD22 VR Weapons 2.0.x** (Brutal Doom v22 in VR on
QuestZDoom 17.3), with **Champions** alongside. LegenDoom's legendary monsters still spawn, still evolve and still
drop legendary weapons. The weapon you pick up is **our BD22 VR gun**, with its hands, models and reloads, and the
legendary power works on that gun. Stock engine, ZScript only; LegenDoom, Champions and BD22 VR are not edited.

Everything below was checked on the test rig only. **Nothing here is headset-confirmed yet.**

## Load order

```
doom2.wad -> brutal22test6.pk3 -> BD_VoxelPack.pk3 -> BD22_VR-Reloaded_2.0.x.pk3 -> (XMVE 04-07, optional)
          -> LegenDoom_3.0.pk3 -> Champions (mk-champions) -> LD_BD22VR_Patch.pk3
```

The patch goes **last**. It works without Champions and without XMVE.

## What "LDL BD edition" means here

Neither LegenDoom 3.0 nor LegenDoom Lite 4.2 has a Brutal Doom mode, branch or cvar (no "brutal" anywhere in either
pk3). LegenDoom 3.0 is the full mod: it brings its own nine sprite weapons and puts its legendary powers inside them.
LegenDoom Lite 4.2 is the weapon-free version: legendary monsters drop health/ammo loot, no weapons. You asked for
legendary weapons that are our BD22 VR guns, so this patch is the "BD edition" of LegenDoom 3.0: LegenDoom's monsters,
drops, rarities, effect names, pickup screen and info screen, on BD22 VR's guns.

## What it does

1. **Gives BD22 its game back.** LegenDoom 3.0 replaces 56 classes: all nine weapons, every ammo/health/armor/key
   pickup, all 17 monsters and the player. Loaded after BD22 VR and XMVE, that would remove BD22's guns, ammo and
   health and XMVE's monsters. The patch hands each of the 56 back to the class it had before LegenDoom (measured on
   the rig, `tools/parsed/repl_*.txt`); a skill's own ReplaceActor still applies. On the rig the patched table is
   identical to the no-LegenDoom table for all 56 (`evidence/logs/t1.log` vs `evidence/logs/base_nold.log`).
2. **Legendary monsters keep working.** LegenDoom chooses them with an OPEN script that gives every monster its
   chance, so BD22 and XMVE monsters become legendary, glow, evolve at half health and drop a legendary weapon.
3. **The drop is a BD22 VR gun.** LegenDoom rolls rarity and effect with its own randomizer; the patch then swaps the
   sprite pickup for one that shows the BD22 gun's own pickup sprite (the voxel from BD_VoxelPack where there is one)
   and LegenDoom's rarity glow. Picking it up gives that BD22 gun (unless you already have it, or its Purist/Dual copy) and
   LegenDoom's own tokens, and shows LegenDoom's pickup screen. One legendary per gun, as in LegenDoom.
4. **The power works on the gun in your hand.** 56 of LegenDoom's 180 effects are carried; see the table below. A
   drop that rolls an effect BD22 guns can't use is re-rolled within the same slot and rarity (option, on by
   default), so you never get a dead legendary.
5. **HUD.** BD22 VR's status bar stays (LegenDoom ships its own SBARINFO, which would replace it). The held gun's
   legendary name can show at the top of the view in its rarity colour ("Legendary Name on Screen", off by default). LegenDoom's info screen opens from the menu. RSQ Wheel
   (its 11-04 build) shows it on the gun's data card: the card in the rarity colour, "EPIC  MURDEROUS SHOTGUN" and
   LegenDoom's description (rig only, not headset-confirmed).

### Which BD22 VR gun stands for which LegenDoom weapon

| LegenDoom slot | Gun given on pickup | Guns that carry that slot's power while held |
|---|---|---|
| Fists | Melee_Attacks | Melee_Attacks |
| Chainsaw | Chain_Saw | Chain_Saw |
| Pistol | BrutalPistol (BrutalRevolver, the Silvergun, with "Silvergun Replaces Pistol") | BrutalPistol, DualPistols, PuristPistol, BrutalRevolver |
| Shotgun | Shot_Gun | Shot_Gun, PuristShot_Gun |
| Super Shotgun | SSG | SSG, PuristSSG |
| Chaingun | MiniGun | MiniGun, PuristMiniGun, Rifle, DualRifles, PuristRifle |
| Rocket Launcher | Rocket_Launcher | Rocket_Launcher, PuristRocket_Launcher |
| Plasma Rifle | Plasma_Gun | Plasma_Gun, DualPlasmaRifles, PuristPlasma_Gun |
| BFG 9000 | BIG_FUCKING_GUN | BIG_FUCKING_GUN, PuristBIG_FUCKING_GUN |

The "given" column is what brutal22test6's own spawner gives for that vanilla weapon (WeaponSpawners.dec). The Rifle
is in the Chaingun family because it is BD22's slot-4 bullet gun that every player starts with. BD22's other guns
(SMG, MP40, Revolver/Shotvolver, Assault Shotgun, Sniper, MG42, Railgun, Grenade/Incendiary Launcher, Devastator,
Nuke, BFG10k, Unmaker, Flamethrowers, Axe, Dragonslayer) have no LegenDoom counterpart and take no legendary.

### Effects carried (56)

| How | Effects |
|---|---|
| On kill, LegenDoom's own reward item | Artifact, Battlerage (+ BD22 guns fire twice as fast while its timer runs), Bloodthirsty, Bloody, Divine, Endless, Hopeful, Infiltrator, Killstreaker, Murderous, Unstoppable, WarmUp |
| On hit, LegenDoom's own debuff on the monster | Crippling, Whittling, Freezing, Gravitic, Incinerating, Violent, Persistent, Igniting |
| On hit, for you | Vampiric (50% of damage as health), Scavenging (50% as armor), Sadistic, Painful, Thieving (BD22 ammo) |
| Damage x | Pristine 2x, Raging 3x, Rampaging/Serious/ProStrat 2x, SteadyShot 3x, Machine 2x, CQC 3x, Patient, Lucky 5x, Berserker, AntiTree, Annoying (1 damage, no ammo), Bloody |
| Against a monster type, x3 (x4) | Exorcist, Extinguishing, Wrangler, Antiair, Scrapper, Blessed, Heroic, DemonSlayer (x4 on legendaries) |
| Ammo | Unlikely 33%, Improbable 66%, Efficient (every 2nd shot free), Impossible |
| While held | Replicating, Regenerating, Determined, Sensing, Desperate |
| Map start | Resupplying (fills BD22 ammo) |

Multipliers are LegenDoom's numbers from its descriptions or code (comments in `effects.zs` name the source).
Parts not carried: Machine's fire rate, CQC's accuracy penalty. LegenDoom's start buffs (Restoring, Vanguard,
Wildfire, Chronostrike, Scrambling) come from LegenDoom's own scripts, untested here.

**Not carried (124):** effects that change how LegenDoom's own guns fire (spreads, projectiles, bounces, beams, fire
rate, burst, homing, reload...), and passives that live in LegenDoom's own item pickups (Sustained, Spiritual,
Hoarder, Survivor, Scrounger, Medic, ...), because BD22's own items are kept. With re-roll on, they do not drop.

## Menu: Options -> LegenDoom x BD22 VR

- Legendary Info Screen (LegenDoom's own screen of all your legendaries)
- Drop Held Gun's Legendary (drops the power as a pickup, the gun stays; use it to swap powers)
- Legendary Name on Screen (Off: the held gun's legendary name at the top of the view; RSQ Wheel's card names it)
- Legendary Guns Only From Bossfights (On: with Champions and RSQ Miniboss's Bossfights, see below)
- Re-roll Effects BD22 VR Can't Use (On)
- Debug Log (Off)
- LegenDoom Options (LegenDoom's own menu)

## Champions

Champions works by tokens on monsters and by its own event handler; the patch touches neither. With Champions'
"Legendoom Compatibility Enabled?" on (champion_legendoom), every legendary monster is also a champion, boosted when
"Boosted Legendary Champions?" is on: the stack works as it does without the patch (rig proof in the report).

**Bossfights are the only source of legendary weapons (owner, 11-05).** With LegenDoom 3.0 AND Champions loaded, and RSQ
Miniboss's Bossfights on, a legendary weapon drops only from a monster that came with a Bossfight (its miniboss or
thralls; the patch asks RSQ Miniboss by name, RSQMB_Service "bossfight"). Other legendaries stay Champions' boosted
champions with their own loot, and their weapon drop is removed. A legendary you dropped yourself is never touched.
LegenDoom without Champions, or without RSQ Miniboss, is unchanged. Row: Legendary Guns Only From Bossfights (on).
Rig (doom2 + BD22 VR 2.0.3x + XMVE + LegenDoom 3.0 + Champions + patch + RSQ Miniboss, 11-05): a legendary Imp's drop
"suppressed (not from a Bossfight)"; three legendary Bossfight thralls and the Bossfight miniboss each dropped theirs
("kept (from a Bossfight)"). Rig only, not headset-confirmed.

## Rig results (rig only, not headset-confirmed)

See `evidence/EVIDENCE.md` for every log. Script errors, not counting BD_VoxelPack's 4 voxeldef lines:

| Load order | BD22 VR | Script errors |
|---|---|---|
| full, with Champions and the patch | 2.0.3u | 0 |
| without Champions | 2.0.3u | 0 |
| full + RSQ Wheel | 2.0.3u | 0 |
| full without the patch (for comparison: no errors, but BD22's guns/items/XMVE monsters are replaced) | 2.0.3q | 0 |

Shown on the rig: legendary monsters (forced with LegenDoom's own LDMonsterInit, and natural ones from its OPEN script)
spawn on XMVE monsters, stack with Champions (an Imp3 legendary + bronze champion at 702 health beside a plain one at
117), die and drop; the drop becomes a BD22 VR gun pickup; picking it up gives the BD22 gun and LegenDoom's tokens and
shows LegenDoom's pickup screen; Exorcist (x3 on a zombie), Vampiric, Murderous, Unlikely, Replicating and Violent
fire through the bridge; dropping and re-picking a legendary works. Not yet shown: the other carried
effects one by one, and anything in a headset.

## Build

```
python ldl_patch/build.py        -> pk3/LDL_BD22VR_Patch.pk3
```

The build still writes the old name; the file in `pk3/` was renamed `LD_BD22VR_Patch.pk3` on 11-05. Rename a new
build the same way.

It regenerates `src/zscript/rsldp/tables.zs` from `tools/parsed/` (`tools/gen_tables.py`) and copies BD22 VR's
`src/SBARINFO.rsq` in. To re-measure: `tools/parse_ld.py` (LegenDoom's replacements, tokens and rolls) and the probe
command `netevent rsldpp_repl` on the rig (`tools/rig.sh`, test only, never ships).

## Credits

- **LegenDoom** by **Yholl**, with Kyle873, Marrub, Sgt_Shivers, Edward850, KeksDose, TerminusEst13 and everyone in
  LegenDoom's CREDITS lump. Its effects, tokens, rarity glows, pickup and info screens, monster system and strings
  are used as LegenDoom ships them; the patch only reads and gives them.
- **Champions** (mk-champions, 2021-03-09 build) by **Mikk-** (the author's name is not in the pk3's credits.txt,
  which lists resource credits: game-icons.net, Yuyu3, Edmund McMillen / Nicalis, Freedoom, Amuscaria, Dazz).
- **Brutal Doom v22** by Sergeant_Mark_IV; **BD22 VR Weapons** by PresidentKoopa (code by agentic Claude);
  **XMVE** by its authors; **BD_VoxelPack** by its authors.
- Patch: PresidentKoopa, coded by agentic Claude.
