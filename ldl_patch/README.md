> **2026-11-06: moving into BD22 VR.** The LegenDoom x BD22 VR merge puts this patch inside BD22 VR as its "LD mode"
> (`src/zscript/rsld/`, `src/ZSCRIPT.rsz`, `src/*.rsld`; interface `docs/INTERFACE.md`; proofs `evidence/ldmode/`).
> This folder's patch is the old version, kept for reference; do not load both (class RSLDP_Service would be defined twice).

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

**Replaced (2026-11-06):** the LD mode now lives inside BD22 VR (src/zscript/rsld) and this patch is not loaded. The
owner's load order for it (round 2): `doom2.wad -> LegenDoom_3.0.pk3 -> brutal22test6.pk3 -> BD_VoxelPack.pk3 ->
BD22 VR -> (XMVE 04-07)`: LegenDoom right after doom2, so Brutal Doom's title map, HUD and sounds win. The rig tools
(`tools/ldrig.sh`, `tools/ldprove.py`) use that order by default (ORDER=full; ORDER=ldlast for the old one).
`build.py` and `tools/rig.sh` (this patch's own build and rig runner) are retired: build.py refuses unless
RSLD_OLD_PATCH=1. Remove `LD_BD22VR_Patch.pk3` from the load order when using a BD22 VR build with the LD mode.

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
- Legendary Guns Only From Minibosses (On: with Champions and RSQ Miniboss's miniboss fights, see below)
- Re-roll Effects BD22 VR Can't Use (On)
- Debug Log (Off)
- LegenDoom Options (LegenDoom's own menu)

## Champions

Champions works by tokens on monsters and by its own event handler; the patch touches neither. With Champions'
"Legendoom Compatibility Enabled?" on (champion_legendoom), every legendary monster is also a champion, boosted when
"Boosted Legendary Champions?" is on: the stack works as it does without the patch (rig proof in the report).

**Miniboss fights are the only source of legendary weapons (owner, 11-05).** With LegenDoom 3.0 AND Champions loaded, and RSQ
Miniboss's miniboss fights on, a legendary weapon drops only from a monster that came with a miniboss fight (its miniboss or
thralls; the patch asks RSQ Miniboss by name, RSQMB_Service "bossfight"). Other legendaries stay Champions' boosted
champions with their own loot, and their weapon drop is removed. A legendary you dropped yourself is never touched.
LegenDoom without Champions, or without RSQ Miniboss, is unchanged. Row: Legendary Guns Only From Minibosses (on).
Rig (doom2 + BD22 VR 2.0.3x + XMVE + LegenDoom 3.0 + Champions + patch + RSQ Miniboss, 11-05): a legendary Imp's drop
"suppressed (not from a miniboss fight)"; three legendary miniboss-fight thralls and the miniboss each dropped theirs
("kept (from a miniboss fight)"). Rig only, not headset-confirmed.

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

## Round 3 (2026-11-06 evening): G3 missile effects, G4 BFG family, G6 ammo effects, small items (agent R3a)

Code: `src/zscript/rsld/g3_core.zs` (the per-projectile rider), `g3_fx.zs` (28 G3 effects + Plasmatic on the rocket
launcher), `g4_bfg.zs` (9 BFG family), `g6_ammo.zs` (8 ammo effects, the alt-fire stand-down), `ldsounds.zs` +
`src/SNDINFO.rsld` (option "Mute LegenDoom Pickup & Aura Sounds"); numbers `tools/numbers/g3.rules` -> `numbers_g3.zs`.
Passives now count only the legendary gun(s) in hand (`RSLD.Count`; `RSLD.CountOwned` is LegenDoom's every-owned rule).
One batched rig run (`tools/ldprove.py round3`, QuestZDoom 17.3, full order with LegenDoom: 0 script errors) and one
boot without LegenDoom (0 script errors, LD mode silent). Logs: `evidence/ldmode/R3_*.log` (rig only, not
headset-confirmed). What each log shows and what it does not: the round-3 report (coordinator).

## Round 4 (2026-11-06 late evening): the owner's round-4 answers (BD22 VR 2.0.4a)

Code: `src/zscript/rsld/ld_g11_stream.zs` (Beam, Blazing, Prototype as streams), `numbers/g11.rules` -> `numbers_g11.zs`;
DualWield (BD22's Dual Pistols only from the DualWield legendary: handler.zs DualWieldGate), SixShooter at half speed, fist
legendaries on both fists (the off hand's free fist), punch damage x swing speed (RSQ Melee's 2 -> 7 m/s rule, built in;
rsq/fists.zs records each punch's hand and speed), Chargeup on the fists, NorthernStar's closing blow (monsters only),
Arcing / Proximity at our projectile speed, Transmogrifier / Overflowing over every BD22 ammo, QuestZDoom's menu and
info-screen sounds under the mute option (MAPINFO.rsld MenuDelegateClass, ldsounds.zs). Registry: 179 effects (all but
Favoured), 647 numbers.
One batched rig run (`tools/ldprove.py round4`: the open arena `tools/make_ldarena.py` loaded last, hostile still targets,
126 sections, full order with LegenDoom first, god, give all: 0 script errors from ours) and one boot without LegenDoom
(0 script errors, LD mode silent: `evidence/ldmode/R4_nold.log`). Logs: `evidence/ldmode/R4_*.log` and the round-3
sections run again (`R3_*`, `R3B_*`; Upgrading_Gas and Hoarder_hand keep their round-3 logs: the run had no B probe).
Rig only, not headset-confirmed.

## 2.0.4b (2026-11-07): two owner-approved fixes

- **Chainsaw effects in VR.** In VR the saw cuts by bar contact (rsvr/melee.zs: BD22's SawDamageHorizontal), which the
  LD mode never counted as a chainsaw attack, so Lacerating, RazorEdge, Extended and Imaginary did nothing. Each cut is
  now recorded the way rsq/fists.zs records a punch (handler.zs IsStrike): a melee attack of the hand holding the saw
  (LegenDoom's Chainsaw slot). Owner: Extended and Imaginary are a longer blade reach: with Extended the cut reaches
  x3.94 (256/65) of the saw's own reach, measured from the hand to the bar's tip, along the bar; with Imaginary the saw
  cuts whatever the bar points at, up to 512 units from the hand (ld_g7_fx.zs RSLD_G7.SawReach).
- **Quickdraw on the BFG fired twice from one press** (the second ball 16 tics later, 50 more cells). Cause (one rig
  run with a per-tic psprite log, `evidence/ldmode/V2_Quickdraw_BFG_diagnosis_2.0.4a.log`): the shot counter looked
  for the new ball with a blockmap search, but projectiles are not in the blockmap, so the no-prefire stepping never
  saw the ball, ran on through RecoilFire to its A_Refire while the trigger was still down, and fired a second time.
  Quickdraw now finds the new ball in the sector lists and stops at the shot: one press, one ball (50 cells), and the
  prefire is still cut.
- Shown in one rig run (full order, LegenDoom first, open arena, 0 script errors from ours) plus a load-only check:
  `evidence/ldmode/V2_*.log`, frames `evidence/ldmode/frames_2.0.4b/` (f00270 / f00384: no legendary, the Baron at 160 /
  400 is not cut; f00318 Extended and f00438 Imaginary: the same Baron cut). Lacerating x1.25 -> x6.00 over 20 cuts;
  RazorEdge logged on every cut with the player not moved; Quickdraw: two presses, two balls, 600 -> 550 -> 500.
  Rig only, not headset-confirmed.

## 2.0.4c (2026-11-07): the shot counter sees projectiles for every user (owner-approved)

- 2.0.4b's sector-list count moved into the shared shot counter (`RSLD_G5.ShotCount`, ld_g5_core.zs), so Burst
  (its 2nd and 3rd shots) and every ShootNow user also see a fresh projectile; Quickdraw uses the shared counter again
  (same count as 2.0.4b). Pellets (hitscan) are counted as before.
- Shown in one rig run (full order, LegenDoom first, round 4's open arena, 0 script errors from ours) plus a load-only
  check: `evidence/ldmode/V3_*.log`, frames `evidence/ldmode/frames_2.0.4c/`. Burst on the rocket launcher: one press,
  3 rockets 4 tics apart (113, 117, 121), magazine 6 -> 3, no restart; on the BFG: 3 balls 4 tics apart, 600 -> 450
  cells; on the pump shotgun (hitscan): 3 blasts of 9 pellets 4 tics apart, magazine 9 -> 6 (as round 4). Quickdraw on
  the BFG: two presses, two balls, 600 -> 550 -> 500; on the rocket launcher: two presses, two rockets, 6 -> 5 -> 4.
  Rig only, not headset-confirmed.

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
