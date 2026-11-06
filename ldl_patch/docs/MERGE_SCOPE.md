# LegenDoom 3.0 x BD22 VR: merge scope (all 180 effects on our guns)

Scoping only (2026-11-06). Nothing was built, changed or committed; nothing here is rig-shown or headset-confirmed.
Owner, 11-06: "begin scoping ld and bd22 merge. i want it all, and i want it on OUR fuckin weapons and sounds, not LDs,
I want those effects optimized but unchanged."

Read as: all 180 LegenDoom 3.0 legendary effects working on BD22 VR's own guns (our models, hands, reloads, sounds),
each behaving as in LegenDoom (same numbers, same rule), built cheaply. Today's patch (`ldl_patch/`) carries 56.

**Where every number comes from.** LegenDoom 3.0 (`/mnt/user-data/uploads/1f3eb79e-LegenDoom_3.0.pk3`, unzipped to an
empty /tmp dir) parsed: `LANGUAGE.effectname/effectdesc` (180 effects), the nine weapons' `decorate/<Gun>/<Gun>.dec`
Fire/Ready/Transfer states per effect, `decorate/*SpecialEffects.dec` (puffs, projectiles, items), `source/*.acs`
(pickups, start buffs, beam), `SNDINFO`. BD22 VR: `src/actors/Weapons/*.dec`, `src/zscript/rsq/*.zs`
(playerrounds, muzzle, recoil, dual, fists, rlock). brutal22test6: `actors/Weapons/*.dec` (BFG, Melee), `SNDINFO.*`.
The patch: `ldl_patch/src/zscript/rsldp/*.zs`, `tools/parsed/*`. Shotgun numbers below (7 pellets of 5*random(1,3))
are LegenDoom's Shotgun.dec; ours are BD22 VR's Shotgun.dec (4+5 = 9 pellets of 13, FBF_NORANDOM; a third volley of 5 makes 14 in BD22's Tactical class).

**What "unchanged" can mean on our guns.** LegenDoom writes each effect into its OWN gun's fire states, with numbers
tuned to that gun (its shotgun: 7 pellets of 5*random(1,3)). Our shotgun is not that gun. So each effect is one of:
- **E (exact)**: the effect is gun-independent (an item on a monster, a reward on kill, a pickup rule, a projectile
  behaviour like x1.05 speed a tic). LegenDoom's numbers carry unchanged.
- **R (rule)**: LegenDoom's rule applied to our gun's own numbers (x2 damage, +57% pellets, half the fire cycle,
  spread 0). The ratio is LegenDoom's; the base is ours. This is the only way the shotgun stays our shotgun.
- **Call**: LegenDoom's behaviour leans on something our gun does not have or has differently (its 7-pellet pattern,
  its 4 ammo types, its 9 weapons, no magazines). Needs the owner's pick (section 7).

**The hooks BD22 VR already has (measured in src/zscript/rsq):**
- **BUL, the shared bullet path.** Every player hitscan raises `WorldHitscanPreFired` once per pellet with its damage,
  angle, pitch, range, puff and flags. `muzzle.zs` already cancels it and re-fires the same shot from the drawn muzzle
  (`LineAttack(..., LAF_ABSPOSITION)`); `playerrounds.zs` turns it into a flying round (True Bullets). A LegenDoom
  handler ordered before muzzle.zs can cancel a pellet and re-fire N pellets with LegenDoom's spread/damage/puff rule;
  everything downstream (muzzle, rounds, flash, recoil, tracers) still sees ordinary shots.
- **MIS, per missile.** `WorldThingSpawned` on a missile whose target is the player (muzzle.zs moves them to the
  muzzle; rlock.zs homes them). A rider (a Thinker or token on the missile) can add LegenDoom's per-tic behaviour,
  flags (RIPPER, bounce) or death behaviour to OUR rocket/plasma/BFG ball, so our model and sounds stay.
- **FIRE, per-weapon fire states.** Fire rate, burst, charge, beam, double-tap need the gun's own states. CLAUDE.md:
  "weapon code is ours to change", so these are small hooks in BD22 VR's `.dec` fire states (one `A_JumpIf` to a
  shared ZScript query), not LegenDoom's states.
- **AMMO.** BD22 guns hold a magazine (Ammo2: ShotgunAmmo, BDPistolAmmo, RocketRounds, PlasmaAmmo...) and a reserve
  (Ammo1: AmmoShell, Clip1, AmmoRocket, AmmoCell); LegenDoom's guns have no magazine.
- **MEL.** VR fists land BD22's own MeleeStrike from the hand (`fists.zs`); the saw is BD22's A_Saw / SawDamage missiles.
- **PICK.** An Inventory token on the player sees every pickup (`HandlePickup`) of BD22's own items (the patch restores
  BD22's 56 classes, so LegenDoom's item scripts never run).
- **DMG / HIT.** `RSLDP_Amp.ModifyDamage` (outgoing) and `RSLDP_Handler.WorldThingDamaged` (per hit), as today.
- **PLR / MAP.** Per-tic player state; LegenDoom's ENTER/RESPAWN script `LD_ApplyStartBuffs`.


## 1. All 180 effects

Source: `LANGUAGE.effectdesc` (180 entries) and the weapon/effect DECORATE of LegenDoom 3.0, parsed (`decorate/*/*.dec`, `decorate/*SpecialEffects.dec`, `source/*.acs`). Rarity/slot is LegenDoom's own roll table (`LD<Slot>RandomLegendary`, the patch's `tools/parsed/ld_rolls.txt`): C/U/R/E = Common/Uncommon/Rare/Epic; Fi Fists (Melee_Attacks), Cs Chainsaw (Chain_Saw), Pi Pistol (BrutalPistol, DualPistols, PuristPistol, the Moonlight), Sg Shotgun (Shot_Gun), SS Super Shotgun (SSG), Cg Chaingun (MiniGun, Rifle, DualRifles + Purists), RL Rocket Launcher, PR Plasma Rifle (Plasma_Gun, DualPlasmaRifles), BF BFG 9000. Every effect has exactly one rarity. "Today" for a carried effect: E = LegenDoom's own item/numbers, unchanged; R = LegenDoom's rule applied to our gun's own numbers; G = a gap against LegenDoom (listed). Nothing in this table is rig-shown by this scoping; "carried" is what the patch's `tables.zs Implemented[]` lists (56), and the patch README says only Exorcist, Vampiric, Murderous, Unlikely, Replicating and Violent were shown on the rig.

| # | Effect | Rarity: slots | What it does (LegenDoom's text) | How LegenDoom does it | Status | Today (carried only) |
|---|---|---|---|---|---|---|
| 1 | Agitating | C:Fi,Cs,Sg,SS,Cg,RL,PR,BF | AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA | every shot: SetMugShotState(Ouch) + effects/agitating* screams, bone casings; no gameplay change | NOT CARRIED |  |
| 2 | Annoying | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Flinches enemies and doesn't use ammo, but only does 1 damage | damage 1, puff +FORCEPAIN, no ammo used | CARRIED | G: 1 damage + no ammo; +FORCEPAIN flinch missing |
| 3 | AntiTree | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Counts all trees in the level and increases weapon damage accordingly | LEGENDWRD.acs counts trees at map start -> LDTreesDamageDisplay percent damage | CARRIED | E |
| 4 | Armorer | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | You share armors with other players | [PASSIVE] armor pickups shared with other players | NOT CARRIED |  |
| 5 | Battlerage | C:Fi | Killing enemies gives you an extendible attack speed boost | Fists only: knife puff, on kill LDBattlerageSpeedBoost (timer item) that LD's fist states read to swing faster | CARRIED | R: engine PowerDoubleFiringSpeed for LD's timer; also halves drawn reload/pump frames (gap in VR) |
| 6 | Blastwave | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Does additional damage at close range | extra invisible short-range missile (LDBlastwave<Gun>) that explodes on contact (shotgun: 105 dmg, r96) | NOT CARRIED |  |
| 7 | Choked | C:Sg,SS | Shotguns have fixed spread instead of random shots | 7 pellets on a fixed pattern (0; +-3.0 h; +-1.5/+-1.5 diagonals), FBF_EXPLICITANGLE | NOT CARRIED |  |
| 8 | ColdBlooded | C:Fi | Damage starts off at Berserk levels, Berserk reduces it | Fists: damage at berserk level without berserk; berserk lowers it | NOT CARRIED |  |
| 9 | Determined | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | While not attacking, makes you 50% tougher | Ready: gives LDDeterminedResistance (50% resist) with cooldown while not attacking | CARRIED | E |
| 10 | Energizing | C:BF | After impact, creates an anomaly that gives health bonuses to nearby players | BFG impact leaves an anomaly (LDEnergizingHealing) giving health bonuses to nearby players | NOT CARRIED |  |
| 11 | Exorcist | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks do triple damage to Former Humans | puff DamageType Exorcist; LD's own monsters carry DamageFactor Exorcist 3 | CARRIED | R: extra hit dmg x2 on name/class-matched BD22/XMVE monsters (LD uses a DamageFactor on its own monsters) |
| 12 | Extinguishing | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks do triple damage to Imps and Arch-viles | DamageType Extinguishing, x3 on LD imps/archviles | CARRIED | R (as Exorcist) |
| 13 | Gravitic | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Damaged enemies move slower and cannot fly | puff gives LDGraviticEffect: speed debuff, -NOGRAVITY/-FLOAT, checker actor | CARRIED | E |
| 14 | Hoarder | C:Pi,Sg,SS,Cg,RL,PR,BF | Pickup extra ammo of this weapon's type from sources of that type | [PASSIVE, STACKS] ammo pickup scripts give extra of this weapon's ammo type | NOT CARRIED |  |
| 15 | Kinetic | C:RL,BF | Projectiles do not explode, instead do all impact damage | LDKineticRocket / LDKineticBFGBall: no explosion, all damage on impact | NOT CARRIED |  |
| 16 | Nova | C:BF | Unleashes a cascade of energy from the blast itself | BFG ball spawns a cascade of LDNovaBFGBall2 + lightning from the blast | NOT CARRIED |  |
| 17 | Penetrating | C:RL,PR,BF | Projectiles rip through enemies, have lowered damage | LDPenetrating* projectiles: +RIPPER, lowered damage | NOT CARRIED |  |
| 18 | Pristine | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | While at 100+ health, does double damage | A_JumpIfHealthLower(100): 2x damage shot (or LDPristine* projectile) | CARRIED | R |
| 19 | Quartermaster | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | You share ammo pickups with other players | [PASSIVE] ammo pickup scripts share pickups with other players (LDQuartermaster*) | NOT CARRIED |  |
| 20 | Quickdraw | C:Cs,Pi,Sg,SS,Cg,RL,PR,BF | Weapon switches instantly, has no prefire time | instant select/deselect states, no prefire frames | NOT CARRIED |  |
| 21 | Raging | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Damage is tripled while berserk is active | while PowerStrength: 3x damage shot / LDRaging* projectile, effects/rageattack | CARRIED | R |
| 22 | RazorEdge | C:Fi,Cs | Doesn't move the player when attacking enemies | Fists/Chainsaw: punch/saw without pulling or moving the player | NOT CARRIED |  |
| 23 | Recursive | C:Pi,Sg,SS,Cg,RL,PR,BF | Fires more shots from their originally fired position for a short time | spawns LDRecursiveEffect<Gun> at the firing spot that re-fires the shot for a short time | NOT CARRIED |  |
| 24 | Regenerating | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Slowly generates health bonuses when not fired | ReadyRegenerating: 35 idle tics then LDHealthBonus | CARRIED | E |
| 25 | Renegade | C:Sg,SS | Fires 50% more pellets | 11 pellets instead of 7 (+57%); 32/256 chance of the effects/renegade scream | NOT CARRIED |  |
| 26 | Replicating | C:Pi,Sg,SS,Cg,RL,PR,BF | Slowly generates ammo type when not fired | ReadyReplicating: 35 tics of A_WeaponReady then one LD_<Ammo>Single | CARRIED | R: +1 reserve per 35 idle tics |
| 27 | Restoring | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Start maps or respawn with 200 health | [PASSIVE] ENTER/RESPAWN LD_ApplyStartBuffs: 200 health | NOT CARRIED |  |
| 28 | Resupplying | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Start maps or respawn with max ammo | ENTER script LD_ApplyStartBuffs: max ammo at map start/respawn (LD's vanilla ammo) | CARRIED | R: fills every BD22 gun's reserve at map tic 6 |
| 29 | Scanner | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Computer maps give tracking map | [PASSIVE] computer map pickup also gives LDScannerActive (tracking map) | NOT CARRIED |  |
| 30 | Scrambling | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Seeker missiles can't lock onto you | [PASSIVE] start buff LDScramblingEffect: PowerInvisibility subclass with +CANTSEEK (seekers can't lock) | NOT CARRIED |  |
| 31 | Slug | C:Sg,SS | Fire accurate single shots with strong knockback | one bullet, spread 1.6, 7*random(5,15) damage, strong knockback | NOT CARRIED |  |
| 32 | Spiritual | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Health and Armor bonuses give +1 more | [PASSIVE, STACKS] health/armor bonus scripts give +1 more per copy | NOT CARRIED |  |
| 33 | Spreadfire | C:RL,PR,BF | Fires spreads of three smaller projectiles in patterns | 3 smaller projectiles in patterns, LDSpreadfireMode cycles the pattern | NOT CARRIED |  |
| 34 | Stasis | C:BF | Does no damage, stuns enemies forever, bosses for a short time | BFG ball: no damage; LDStasisEffect freezes enemies forever, bosses briefly (effects/stasis) | NOT CARRIED |  |
| 35 | Stealth | C:Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks do not alert enemies at long range | no A_AlertMonsters; own fire sound at 0.1 + effects/stealth<gun> quiet shot; LDStealth* projectiles | NOT CARRIED |  |
| 36 | Survivor | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Healing items heal for an extra +100% of normal | [PASSIVE, STACKS] stimpack/medikit scripts heal +100% per copy | NOT CARRIED |  |
| 37 | Sustained | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Powerup items have +50% of original length | [PASSIVE, STACKS] LEGENDITM.acs pickup scripts: powerups +50% length per copy owned | NOT CARRIED |  |
| 38 | Trailblazing | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Fires faster the lower your health is | fire states shorten as health drops | NOT CARRIED |  |
| 39 | Tricky | C:RL,PR,BF | Projectiles bounce off surfaces | LDTricky* projectiles: bounce off walls/floors (effects/bouncy*) | NOT CARRIED |  |
| 40 | Unknown | C:Pi,Sg,SS,Cg,RL,PR,BF | Has unlimited ammo while invisibility is active | ammo check skipped while PowerInvisibility/Ghost/Shadow; effects/unknown (LD's Scrambling is a PowerInvisibility, so Unknown+Scrambling = always free) | NOT CARRIED |  |
| 41 | Upgrading | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Picking up ammo when maxed will upgrade your gun's stats at certain thresholds | ammo pickups while maxed fill an upgrade meter (LD_UpgradingUpgrader); 5 tiers of stronger shots/projectiles | NOT CARRIED |  |
| 42 | Vanguard | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Start maps or respawn with 200 blue armor | [PASSIVE] start/respawn with 200 blue armor | NOT CARRIED |  |
| 43 | Violent | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Enemies gib, damaging and scaring nearby enemies | puff gives LDViolentEffect; on death the body gibs: LDViolentExplosion damages + scares nearby | CARRIED | E |
| 44 | Wrangler | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks do triple damage to Demons | DamageType Wrangler, x3 on LD demons/spectres | CARRIED | R (as Exorcist) |
| 45 | ActionHero | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Ammo pickups give 1 stacking second of infinite ammo | [PASSIVE, STACKS] ammo pickups give 1 s of infinite ammo each | NOT CARRIED |  |
| 46 | AntiAir | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks do triple damage to aerial monsters | DamageType AntiAir, x3 on lost souls/cacos/pain elementals | CARRIED | R (as Exorcist) |
| 47 | Arcing | U:RL | Fires grenades that bounce off surfaces | Rocket Launcher fires bouncing grenades (LDArcingRocket) | NOT CARRIED |  |
| 48 | Berserker | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Does more damage the lower your health is | damage 5 at 100+ health, +1 per 10 health below (Shotgun.dec FireBerserker) | CARRIED | R |
| 49 | Bloody | U:Cs | Every 5 enemies killed with this increases damage for the level | Chainsaw only: LDBloodyChainsawPuff; every 5 kills +1 LDBloodyCounter; damage x (counter+5)/5 for the map | CARRIED | E |
| 50 | Bouncy | U:RL,PR,BF | Projectiles start bouncing on impact | projectile starts bouncing on impact (effects/bouncy*) | NOT CARRIED |  |
| 51 | Burst | U:Fi,Pi,Sg,SS,RL,BF | Fires three rapid attacks | one trigger pull = three rapid attacks, needs 3 ammo | NOT CARRIED |  |
| 52 | Chargeup | U:Fi,Pi,Sg,SS,Cg,RL,PR,BF | Can store multiple attacks and unleash them at once | holding fire stores attacks (LD<Gun>Chargeup counter, effects/chargeup), release fires them all | NOT CARRIED |  |
| 53 | Cluster | U:RL,PR,BF | Projectiles explode into smaller projectiles | LDCluster* projectiles burst into LDMiniCluster* projectiles | NOT CARRIED |  |
| 54 | Comrade | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Increases in damage the more players are in the game | damage x player count (ACS PlayerCount) | NOT CARRIED |  |
| 55 | Efficient | U:SS,BF | Uses only half ammo per attack | BFG/SSG: every second attack uses no ammo | CARRIED | R (as Unlikely) |
| 56 | Energetic | U:BF | Emits twice as many BFG rays | BFG ball emits twice as many rays | NOT CARRIED |  |
| 57 | Flak | U:Pi,Cg | Aerial enemies are surrounded by explosions on hit | puff: on a NOGRAVITY target spawns LDFlakDamage explosions around it | NOT CARRIED |  |
| 58 | Focusing | U:Cg,PR | Increases in damage and accuracy the longer you shoot | LDFocusingCounter while firing: 5 tiers of damage/accuracy | NOT CARRIED |  |
| 59 | GroupTherapy | U:RL | Does no splash damage, but if it kills, nearby enemies explode | Rocket: no splash; a kill makes nearby enemies explode (LDGroupTherapyEffect chain) | NOT CARRIED |  |
| 60 | Hardened | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Green armors count as Blue armors | [PASSIVE] green armor pickups give blue armor | NOT CARRIED |  |
| 61 | Heavy | U:Fi,Pi,Sg,SS,Cg,RL,PR,BF | Greatly increased knockback | puff ProjectileKickBack 4000 / heavy projectiles | NOT CARRIED |  |
| 62 | Hunting | U:Fi,Pi,Sg,SS,Cg,RL,PR,BF | Slower firerate, but higher damage and knockback | 3x damage, knockback puff, slower cycle, pushes player back (A_ChangeVelocity), effects/hunting | NOT CARRIED |  |
| 63 | Hyper | U:RL,PR,BF | Projectiles accelerate constantly | A_ScaleVelocity(1.05) per tic | NOT CARRIED |  |
| 64 | Igniting | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Enemies periodically generate an AOE fire after being hit | puff gives LDIgnitingPowerGiver: target periodically emits an AOE fire | CARRIED | E |
| 65 | Illuminating | U:RL,PR,BF | Projectiles light up levels greatly, glow while idle | projectiles with big dynamic lights; idle glow actor while the gun is held | NOT CARRIED |  |
| 66 | Incinerating | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killed enemies burn up after a short time, destroying corpse | puff gives LDIncineratingEffect; dead body burns away after a delay (corpse destroyed) | CARRIED | E |
| 67 | Infiltrator | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing enemies gives you a short extendable invisibility | puff -> on death: short extendable invisibility (LD_InfiltratorActivate) | CARRIED | E |
| 68 | Lunging | U:Fi | Launches you fist extended in the direction you are looking | Fists: A_ChangeVelocity launches the player forward fist-first (LDLungingStrike) | NOT CARRIED |  |
| 69 | Medic | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | You share health items with other players | [PASSIVE] stimpack/medikit shared with other players, effects/medic | NOT CARRIED |  |
| 70 | Mysterious | U:RL,PR,BF | It is a mystery | projectile randomly teleports +-32 units every few tics (A_Warp) | NOT CARRIED |  |
| 71 | Optional | U:Pi,Sg,SS,Cg,RL,PR,BF | Can fire weaker shots without ammo | with no ammo, fires a weaker shot (shotgun 2 vs 5 per pellet; LDOptional* projectiles) | NOT CARRIED |  |
| 72 | Painful | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks always flinch enemies | puff with +FORCEPAIN | CARRIED | E |
| 73 | ProStrat | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | While strafing, does 2x damage | strafing input: 2x damage shot | CARRIED | R |
| 74 | Proximity | U:RL,PR,BF | Fires stationary projectiles that float towards nearby enemies | projectiles stop and drift toward nearby enemies (effects/seekerrocket) | NOT CARRIED |  |
| 75 | Rampaging | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | While holding forwards, does 2x damage | LDForwards token (ACS reads input): 2x damage shot | CARRIED | R |
| 76 | Recycling | U:Pi,Sg,SS,Cg,RL,PR,BF | Gives small amounts of all other ammo types when fired | each shot gives counters towards every other ammo type (LDRecycling*Counter) | NOT CARRIED |  |
| 77 | Redirecting | U:RL,PR,BF | Shots bounce off surfaces towards enemies once | projectile bounces once and turns toward an enemy | NOT CARRIED |  |
| 78 | Scattering | U:BF | Fires BFG rays directly for less ammo | BFG fires its rays directly (A_BFGSpray from the gun) for less ammo | NOT CARRIED |  |
| 79 | Scrounger | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Pickup 20% more ammo from ammo items | [PASSIVE, STACKS] ammo pickups +20% | NOT CARRIED |  |
| 80 | Sensing | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Displays nearby enemies, barrels and items on the map | ReadySensing every 35 tics: A_RadiusGive LDSensingEffect 1024 (monsters, objects, items, no sight) -> map markers; effects/sensing | CARRIED | E (LD's radius give; costly, see 5) |
| 81 | Serious | U:Pi,Sg,SS,Cg,RL,PR,BF | While holding backwards, does 2x damage | backwards input: 2x damage shot | CARRIED | R |
| 82 | Shielding | U:Cg,PR | While attacking, deploys an energy shield in front of you | while firing spawns LDShieldingShield in front of the player | NOT CARRIED |  |
| 83 | Shockwave | U:BF | Explodes instead of emitting BFG rays | BFG ball explodes (LDShockwaveBFGBall) instead of rays | NOT CARRIED |  |
| 84 | Sluggish | U:RL,PR,BF | Projectiles deaccelerate constantly, rip through enemies | A_ScaleVelocity(0.98) per tic, +RIPPER, damage by ACS speed scaling, detonates when stopped | NOT CARRIED |  |
| 85 | Thieving | U:Fi,Cs | Gain small amounts of random ammo when hitting enemies | Fists/Chainsaw puff -> LDThievingEffect: 75% chance, cooldown, a pickup of a RANDOM ammo type | CARRIED | G: gives the held gun's ammo, LD gives a random ammo type |
| 86 | Transmogrifier | U:Pi,Sg,SS,Cg,RL,PR,BF | Uses other ammo types when it runs out of main ammo type | out of its ammo, fires using Shell/Clip/Cell/Rocket in turn (LD<Gun>TransmogrifierAmmo) | NOT CARRIED |  |
| 87 | Unlikely | U:Pi,Sg,SS,Cg,RL,PR,BF | Shots have a 33% chance of not consuming ammo | 33% of shots skip FBF_USEAMMO | CARRIED | R: refund from per-tic ammo diff; off-hand copy's shots not seen |
| 88 | WarmUp | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing five enemies on the level gives you berserk | puff -> per-map kill counter; 5th kill gives berserk | CARRIED | E |
| 89 | Accelerator | R:RL,PR,BF | Fires instant hitting attacks | Rocket/Plasma/BFG fire instant attacks (A_RailAttack / hitscan with exploding puffs) | NOT CARRIED |  |
| 90 | Advanced | R:Pi | Fires rapidly, does more damage, but needs reloading | Pistol: rapid, stronger shots from a magazine (LDAdvancedPistolAmmo) with a reload, effects/advancedreload* | NOT CARRIED |  |
| 91 | Beam | R:PR,BF | Fires a constant, high damage energy beam | Plasma/BFG: constant high-damage beam (LEGENDBEM.acs emitters, effects/beam* loops) | NOT CARRIED |  |
| 92 | Blaster | R:Fi | Holding fire will cause you to fire plasma balls slowly | Fists: holding fire launches slow plasma balls (LDBlasterProjectile) | NOT CARRIED |  |
| 93 | Blazing | R:RL,PR,BF | Fires a constant, short range, flamethrower | Rocket/Plasma/BFG: constant short-range flame stream (LDBlazing* fuel/projectiles, effects/blazing* loops) | NOT CARRIED |  |
| 94 | Blessed | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks do triple damage to Hell Nobles | DamageType Blessed, x3 on knights/barons | CARRIED | R (as Exorcist) |
| 95 | Chronostrike | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Start maps or respawn with 10 seconds of timefreeze | [PASSIVE, STACKS] start/respawn with 10 s of time freeze | NOT CARRIED |  |
| 96 | Concentrating | R:RL,PR,BF | Projectiles increase in damage the longer they fly | projectile damage grows with flight time (LDConcentratingCounter) | NOT CARRIED |  |
| 97 | CQC | R:Pi,Sg,SS,Cg | Triple damage, but with greatly decreased accuracy | spread x3 (16.8 vs 5.6) and damage x3 | CARRIED | G: 3x only; spread x3 not carried |
| 98 | Decaying | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Extreme damage randomization | damage random(1,30) per pellet instead of 5*random(1,3) | NOT CARRIED |  |
| 99 | Desperate | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | When attacking below 26% health, gives moments of invincibility | on attack below 26 health: LDDesperateInvulnerabilityChecker -> short invulnerability with cooldown | CARRIED | E |
| 100 | Doubletap | R:Sg,SS | Attack twice before reloading, costs only 1 shot | Shotgun/SSG: two shots before pump/reload for one shell (LD<Gun>DoubleTap token) | NOT CARRIED |  |
| 101 | DualWield | R:Pi | Twin pistols with increased stats | Pistol: twin pistols (LDDualWieldState) with better stats | NOT CARRIED |  |
| 102 | Entrenched | R:Cg,PR | While firing, makes you immobile and gives you 50% resist and 2x damage | while firing: speed 0 (LDEntrenchedSpeedDebuff), 50% resist, 2x damage | NOT CARRIED |  |
| 103 | Explosive | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Shots explode for small radius damage | bullet puffs explode for small radius (LDExplosiveBulletPuff); projectiles explode bigger | NOT CARRIED |  |
| 104 | Extended | R:Fi,Cs | Has longer range | Fists/Chainsaw: longer melee range | NOT CARRIED |  |
| 105 | Ghostly | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Invisibility gives 90% damage resistance and AOE immunity | [PASSIVE] invisibility (incl. Infiltrator/Artifact) gives 90% resist and AOE immunity | NOT CARRIED |  |
| 106 | HighExplosive | R:RL | Explosions are twice as big | Rocket: explosion radius x2 | NOT CARRIED |  |
| 107 | Hopeful | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing an enemy while below 33% health restores you to 33% | puff -> on death: if health < 33, set to 33 | CARRIED | E |
| 108 | Illegal | R:Pi,Sg,SS,Cg,RL,PR,BF | Can attack without ammo, but makes enemies angry | fires without ammo; LDIllegalizer makes enemies angry (LDIllegalActive) | NOT CARRIED |  |
| 109 | Improbable | R:Pi,Sg,SS,Cg,RL,PR,BF | Shots have a 66% chance of not consuming ammo | 66% of shots skip FBF_USEAMMO | CARRIED | R (as Unlikely) |
| 110 | Intimidating | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Invulnerability also gives you damage and fright effects | [PASSIVE] invulnerability (incl. Divine/Desperate/Artifact) also damages and frightens nearby | NOT CARRIED |  |
| 111 | Killstreaker | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing enemies gives you a short, extendable speed boost | puff -> on death: short extendable speed powerup | CARRIED | E |
| 112 | Lucky | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Has a chance of firing a max damage 5x strength attack | per trigger pull A_Jump(58/256): one max-damage 5x shot (75 vs 5*random(1,3)), effects/lucky | CARRIED | G: rolled per damage event (per pellet); LD rolls once per trigger pull |
| 113 | Marksman | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Always does maximum damage | FBF_NORANDOM at max damage (shotgun 15 = 5*3 per pellet); max-damage projectiles | NOT CARRIED |  |
| 114 | Nuclear | R:Pi,Sg,SS,Cg,RL,PR,BF | Does less damage, has infinite ammo | lower damage (shotgun 3 vs 5 per pellet), never uses ammo | NOT CARRIED |  |
| 115 | Patient | R:Pi,Sg,SS,Cg,RL,PR,BF | Builds up damage multipliers slowly, consumed upon firing | ReadyPatient: +1 LDPatientCounter per 35 idle tics (effects/patient); shot damage x(counter+10)/10, emptied on fire | CARRIED | R: 18-tic window approximation |
| 116 | Perfect | R:Pi,Cg | Shots do max double damage, 100% accuracy, misses jam the gun | 2x max damage, 0 spread; a miss gives LDPerfectJammed (gun jams) | NOT CARRIED |  |
| 117 | PointBlank | R:Pi,Cg | Decreased accuracy, but any shots that hit don't consume ammo | wider spread; shots fire free, a miss (puff Crash) takes 1 ammo | NOT CARRIED |  |
| 118 | Rapid | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Fires twice as fast | hand-made fire states at twice the speed (per gun: rapid pump, quick refire) | NOT CARRIED |  |
| 119 | Resourceful | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Health and Armor Bonuses also give their alternate bonus type | [PASSIVE] health bonuses also give an armor bonus and back | NOT CARRIED |  |
| 120 | Sadistic | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Each shot that hits an enemy without killing gives you a health bonus | puff: a hit that does not kill gives a health bonus | CARRIED | E |
| 121 | Scavenging | R:Fi,Cs | Attacks give you armor from enemies | Fists/Chainsaw only: CPF_STEALARMOR lifesteal 0.5 + LDScavengingEffect armor bonuses | CARRIED | E |
| 122 | Scrapper | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks do triple damage to cybernetic enemies | DamageType Scrapper, x3 on arachnotrons/revenants/mancubi | CARRIED | R (as Exorcist) |
| 123 | Seeker | R:RL,PR,BF | Shots home in on enemies | projectiles A_SeekerMissile(5,5,SMF_LOOK/SMF_PRECISE,256,20) every tic | NOT CARRIED |  |
| 124 | Shaman | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Powerups affect all players | [PASSIVE] powerup pickups affect all players (LDShaman*Effect), effects/shaman | NOT CARRIED |  |
| 125 | ShapedCharge | R:RL | Explosions won't harm owner | Rocket: explosion does not hurt the shooter | NOT CARRIED |  |
| 126 | Sniper | R:Pi,Sg,SS,Cg | 100% accurate | spread 0 | NOT CARRIED |  |
| 127 | Spamtastic | R:RL,PR,BF | Projectiles rapidly fire smaller projectiles randomly | projectile randomly fires smaller projectiles (A_CustomMissile, 26/256 per tic) | NOT CARRIED |  |
| 128 | SteadyShot | R:Pi | While crouching, do triple damage and have perfect accuracy | Pistol: crouched (LDSteadyShotCrouchCheck view height): 3x damage AND 0 spread | CARRIED | G: 3x only; LD's 0 spread not carried |
| 129 | Suppression | R:PR | Fires inaccurate miniplasma, but only uses 1 ammo per 5 shots | Plasma: inaccurate mini plasma, 1 cell per 5 shots | NOT CARRIED |  |
| 130 | Suspenseful | R:Pi,Sg,SS,Cg | Each missed shot gives you a damage boost for your next shot | each miss (puff Crash) raises LDSuspensefulCounter; next shot damage x counter | NOT CARRIED |  |
| 131 | TORGUE | R:RL | Amplified explosion, causes enemies to explode on death | Rocket: bigger explosion; killed enemies explode (LDTORGUEEffect/Exploder) | NOT CARRIED |  |
| 132 | Vacuum | R:RL,PR,BF | Projectiles pull in enemies as they travel | projectile A_RadiusThrust(-160, 1024) every tic: pulls enemies in | NOT CARRIED |  |
| 133 | Vampiric | R:Fi,Cs | Attacks drain life from enemies | Fists/Chainsaw only: A_CustomPunch / A_Saw lifesteal 0.5 | CARRIED | E (GiveBody dmg/2) |
| 134 | Vidmaster | R:RL | Explosions do full damage over their entire radius | Rocket: A_Explode with full damage over the whole radius | NOT CARRIED |  |
| 135 | Waveform | R:PR | Fires a double wave of plasma back and forth | Plasma: two plasma balls weaving in a sine wave | NOT CARRIED |  |
| 136 | Whittling | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Each attack applies a stacking damage resistance debuff to your targets | puff gives monster stacking LDWhittlingEffect (damage resistance down) + checker actor | CARRIED | E |
| 137 | Wildfire | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Start maps or respawn FUCKING INVINCIBLE | [PASSIVE, STACKS] start/respawn invulnerable for a time | NOT CARRIED |  |
| 138 | WindUp | R:Cg,PR | Starts slowly, winds up to 1 tic firing speed | Chaingun/Plasma: starts slow, LDWindUpCounter winds to 1-tic refire | NOT CARRIED |  |
| 139 | Annihilating | E:BF | Dangerous explosion on impact, rays also explode | BFG: dangerous explosion, rays explode too | NOT CARRIED |  |
| 140 | Artifact | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Gain a random powerup on kill every 30 seconds | puff gives LDArtifactEffect; on death LDArtifactEffectDeath gives a random powerup, 30 s LDArtifactEffectCooldown | CARRIED | E (LD death item) |
| 141 | Augmented | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Armor bonuses give damage resist, health gives 1.5x damage | [PASSIVE] armor bonuses give damage resist, health bonuses 1.5x damage | NOT CARRIED |  |
| 142 | Bloodthirsty | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing enemies gives you multiple health bonuses | puff -> LDBloodthirstyEffect; on death LDBloodthirstyEffectDeath gives several health bonuses | CARRIED | E |
| 143 | Champion | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Berserks give an additional five extra powerups | [PASSIVE, STACKS] berserk pickup gives five extra powerups | NOT CARRIED |  |
| 144 | Collector | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Gain a health bonus from picking up ammo | [PASSIVE, STACKS] ammo pickups give a health bonus | NOT CARRIED |  |
| 145 | Convincing | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Does no damage, but can mindcontrol enemies you hit | no damage; LDConvincingEffect adds 30 tokens per hit; tokens >= health -> monster FRIENDLY (not bosses/transformed legendaries) | NOT CARRIED |  |
| 146 | Crippling | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks give the enemy a 50% damage debuff | puff gives monster LDCripplingEffect (50% outgoing damage) + visual checker actor | CARRIED | E (LD items) |
| 147 | Cursed | E:Pi,Sg,SS,Cg,RL,PR,BF | Does 4x damage, but any missed shot hurts you | 4x damage (shotgun 20 vs 5); a puff that misses gives you LDCursedEffect (self damage) | NOT CARRIED |  |
| 148 | DemonSlayer | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Does quad damage to Legendary enemies | DamageType DemonSlayer, x4 on monsters with LDLegendaryMonsterToken | CARRIED | R (x4 on LDLegendaryMonsterToken) |
| 149 | Divine | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing an enemy gives you momentary stackable invulnerability | puff -> on death LDDivineEffectDeath: momentary stackable invulnerability (LD_DivineActivate, Sustained-aware) | CARRIED | E |
| 150 | Endless | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing an enemy gives you a burst of stackable infinite ammo | puff -> on death: stackable burst of PowerInfiniteAmmo | CARRIED | E |
| 151 | Facekicking | E:Fi | Kicks enemies, can do jump kicks in midair | Fists become kicks, jump kicks in midair (A_ChangeVelocity), reflector actor | NOT CARRIED |  |
| 152 | Favoured | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Does more damage the less weapons you have | damage (50 - 5 x weapons owned) x random(1,3) per pellet | NOT CARRIED |  |
| 153 | Freezing | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Impacts cause constant low AOE damage to enemies and slows them | puff gives LDFreezingEffect: slow debuff + constant low AOE (LDFreezingImpact actors) | CARRIED | E |
| 154 | Gauss | E:Pi,Sg,SS,Cg | Shots pierce through enemies | piercing A_RailAttack pellets (shotgun 7 x 5*random(1,3)), effects/gauss | NOT CARRIED |  |
| 155 | Goldeneye | E:RL | Direct hits cause constant explosions around enemies | Rocket direct hit: LDGoldeneyeDamage keeps exploding around the enemy | NOT CARRIED |  |
| 156 | Gyrojet | E:Pi,Sg,SS,Cg | Fires mini-missiles | bullet guns fire mini-missiles (LDGyrojet<Gun>Projectile) | NOT CARRIED |  |
| 157 | Heroic | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks do triple damage to bosses | DamageType Heroic, x3 on cyberdemon/mastermind | CARRIED | R (as Exorcist; bBOSS too) |
| 158 | Imaginary | E:Cs | Uses the power of your mind | Chainsaw: spawns 'EEEE' attack actors (meme), effects/imaginary voice | NOT CARRIED |  |
| 159 | Impossible | E:Pi,Sg,SS,Cg,RL,PR,BF | Shots have a 50% chance of generating ammo instead of using ammo | 50%: shot uses no ammo and gives one LD_<Ammo>Single | CARRIED | R (as Unlikely) |
| 160 | Irradiated | E:RL,PR,BF | Fires radiation pulses that do AOE damage constantly | projectile A_Explode(20*random(1,8), 256) about every 16 tics in flight + radiation particles | NOT CARRIED |  |
| 161 | Lacerating | E:Cs | Does more damage the longer you saw enemies | Chainsaw: damage grows the longer you saw (LDLaceratingCounter/Timer) | NOT CARRIED |  |
| 162 | Machine | E:Pi | Fires extremely rapidly and does double damage | Pistol: extremely fast loop (LDMachineCounter) at 2x damage, effects/machineloop/end | CARRIED | G: 2x only; fire rate not carried |
| 163 | Murderous | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing enemies gives you a short, extendable 3x damage boost | puff -> on death: short extendable 3x damage powerup | CARRIED | E |
| 164 | NanoCircuit | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Attacks have a chance of giving a health and armor bonus | each attack has a chance of a health and an armor bonus, effects/nanocircuit | NOT CARRIED |  |
| 165 | NorthernStar | E:Fi | Rapid punching that stuns and delays damage | Fists: rapid hitscan punches stun, damage delivered later (LDNorthernStarDamager), Kenshiro sounds | NOT CARRIED |  |
| 166 | OnePunch | E:Fi | Attack has a huge cooldown, unleashes a line of destruction | Fists: long charge, LDOnePunchProjectile line of destruction + shockwave, big cooldown | NOT CARRIED |  |
| 167 | Overflowing | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Gains a bonus effect for each ammo type maxed | each maxed ammo type adds a bonus (AOE puffs, extra cell/rocket effects) | NOT CARRIED |  |
| 168 | Overkill | E:RL | Fires giga-missiles that use 5x the ammo | Rocket: giga missile for 5x ammo, cooldown (LDOverkillCooldown) | NOT CARRIED |  |
| 169 | Persistent | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Does a stacking DoT to enemies when hit | puff gives LDPersistentBlood: stacking bleed DoT items (LDPersistentBleedingEffectDamage) | CARRIED | E |
| 170 | Plasmatic | E:Pi,Sg,SS,Cg,RL | Fires powerful plasma projectiles | bullet guns fire plasma projectiles (LDPlasmatic<Gun>Ball), effects/plasmaattack | NOT CARRIED |  |
| 171 | Prototype | E:BF | Sprays huge amounts of plasma projectiles | BFG sprays huge amounts of small plasma (LDPrototypeBFGBall*) | NOT CARRIED |  |
| 172 | Raycaster | E:RL | Rockets emit BFG rays | Rockets emit BFG rays | NOT CARRIED |  |
| 173 | ShortRange | E:Pi,Sg,SS,Cg,RL,PR,BF | Fires multiple attacks that disappear very quickly | several attacks with short range (shotgun 200/150/100) or short-lived projectiles | NOT CARRIED |  |
| 174 | SixShooter | E:Pi | Does 10x damage, slower fire rate | Pistol: 10x damage, slow, 6-shot counter (LDSixShooterCounter), effects/sixshooter | NOT CARRIED |  |
| 175 | Soulstorm | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Soulspheres and Megaspheres are enhanced | [PASSIVE] soulsphere/megasphere scripts add regeneration and more | NOT CARRIED |  |
| 176 | Thematic | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Does more damage the more Thematic weapons you have | damage grows with the number of Thematic legendaries owned | NOT CARRIED |  |
| 177 | TripleThreat | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Fires a spread of three shots | three spreads (centre, +-15 deg) for one ammo | NOT CARRIED |  |
| 178 | TwinShot | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Fires two shots for the price of one | two shots (shotgun 14 pellets) for one ammo | NOT CARRIED |  |
| 179 | Unfathomable | E:Pi,Sg,SS,Cg,RL,PR,BF | Fires all your ammo in one shot | fires all your ammo in one shot (damage scales with ammo spent) | NOT CARRIED |  |
| 180 | Unstoppable | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | Killing enemies gives you a short, extendable 50% damage resistance | puff -> on death: short extendable 50% damage resistance | CARRIED | E |

Counts by rarity (all / carried): Common 44/14, Uncommon 44/15, Rare 50/14, Epic 42/13. Total 180 / 56.

## 2. The 124 not carried: hook, exactness, conflicts, identity risk

Hook codes as above. "Keeps LegenDoom's behaviour?" uses E / R / Call. Conflicts name BD22 VR's own mechanics
(hand reload and hand pump, two-hand, off-hand copies, BD22's alt fires, BD22 VR options). Identity risk = would the
gun stop being that gun (CLAUDE.md: "the shotgun is still a shotgun"): flagged, not decided. Q-numbers point to
section 7.

Conflicts that apply to every row and are not repeated:
- **Off-hand copies** (`dual.zs`): a copy is the same gun with its own magazine, firing with `LAF_ISOFFHAND`. Today
  the patch reads the effect of `ReadyWeapon` only and counts shots by the main gun's ammo, so a copy's shots get the
  main hand's effect (or none). Every hook needs the shot's own hand (Q8).
- **Event order.** Shot-shape effects must re-fire BEFORE `RSQ_Muzzle` (muzzle start, bore), `RSQ_PlayerRounds`
  (SetOrder 1000), `RSQ_Recoil` and `RSQ_FlashHandler`, and mark re-fired pellets so recoil/flash/casings count one
  shot, not 14 pellets.
- **Our sounds.** Every LegenDoom projectile or puff we spawn carries LegenDoom's SeeSound/DeathSound; each must be
  overridden with ours (section 4).


| Effect | Rarity: slots | Hook | Keeps LegenDoom's behaviour? | VR / BD22 conflicts | Identity risk | Group |
|---|---|---|---|---|---|---|
| Agitating | C:Fi,Cs,Sg,SS,Cg,RL,PR,BF | PLR | E is sounds + mugshot only | VR has no mugshot in view; behaviour IS LD's scream sounds (Q2) | none | G10 |
| Armorer | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E (multiplayer only) | none | none | G8 |
| Blastwave | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | BUL | E: LD's LDBlastwave<Gun> missile from our muzzle | none | none | G2 |
| Choked | C:Sg,SS | BUL | Call: LD's fixed 7-pellet pattern; ours fires 9 (14 Tactical): the pattern has to be scaled | rsq_pump_spread option overlaps | low | G2 |
| ColdBlooded | C:Fi | MEL | R: BD22 fist damage at its berserk level, berserk lowers it | VR real punches (fists.zs) use BD22's MeleeStrike: hook there | none | G7 |
| Energizing | C:BF | MIS | E: LD's anomaly actor at BD22 ball impact | none | low | G4 |
| Hoarder | C:Pi,Sg,SS,Cg,RL,PR,BF | PICK | R: extra = LD's ratio on BD22 ammo pickups (Clip2, AmmoShell...) | none | none | G8 |
| Kinetic | C:RL,BF | MIS | R: our rocket/BFG ball's splash moved to impact | none | med: rocket no longer splashes | G3 |
| Nova | C:BF | MIS | R: cascade from BD22's BFGBall death | BD22 BFG ball has its own death/rays | low | G4 |
| Penetrating | C:RL,PR,BF | MIS | R: +RIPPER, LD's damage ratio | none | low | G3 |
| Quartermaster | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E (multiplayer only) | none | none | G8 |
| Quickdraw | C:Cs,Pi,Sg,SS,Cg,RL,PR,BF | FIRE | R: instant raise/lower | BD22 VR switch.zs / select animations and hand poses must not be skipped mid-pose | low | G5 |
| RazorEdge | C:Fi,Cs | MEL | R: no pull/push on BD22 saw/punch | check if BD22 saw already pulls; may be a no-op | none | G7 |
| Recursive | C:Pi,Sg,SS,Cg,RL,PR,BF | FIRE | R: re-fire from the muzzle position at fire time | VR: muzzle moves with the hand; anchor at fire time | low | G5 |
| Renegade | C:Sg,SS | BUL | R: +57% pellets (9 -> 14 on the pump; 14 -> 22 Tactical), 32/256 scream | recoil/flash/rounds handlers see re-fired pellets: needs a 'not a new shot' mark | low | G2 |
| Restoring | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | MAP | E: LD's script already runs (untested) | none | none | G9 |
| Scanner | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E: BD22 Allmap gives LD's tracking map | none | none | G8 |
| Scrambling | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | MAP | E: LD's start buff (untested) | is a PowerInvisibility: interacts with Unknown/Ghostly as in LD | none | G9 |
| Slug | C:Sg,SS | BUL | R: one round, LD's x(5..15) of a pellet, knockback | BD22 VR already has a Slug alt fire (RSA_Opt_Slug): Q12 | med | G2 |
| Spiritual | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E: +1 per copy on BD22's HealthPlus/ArmorShardVOX | none | none | G8 |
| Spreadfire | C:RL,PR,BF | MIS | R: 3 smaller copies of our projectile in LD's patterns | none | med | G3 |
| Stasis | C:BF | MIS | E: LD's stasis items on enemies; ball does no damage | none | med: BFG that does no damage | G4 |
| Stealth | C:Cs,Pi,Sg,SS,Cg,RL,PR,BF | FIRE | R: no alert at range, quiet fire | BD22 alerts via A_AlertMonsters + Alerter/DistantFireSound missiles: suppress those | none | G10 |
| Survivor | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E: +100% per copy on Stimpack2/Medikit2 | none | none | G8 |
| Sustained | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E: +50% powerup length per copy (BD22 powerups) | none | none | G8 |
| Trailblazing | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | FIRE | R: our fire cycle shortened by LD's health curve | hand actions (pump, bolt, reload) (Q6) | low | G5 |
| Tricky | C:RL,PR,BF | MIS | R: our projectile gets LD's bounce | BD22 VR missile muzzle start (muzzle.zs) ok | low | G3 |
| Unknown | C:Pi,Sg,SS,Cg,RL,PR,BF | AMMO | E: free shots while invisible | which pool: magazine or reserve (Q7) | none | G6 |
| Upgrading | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | R: LD's meter on BD22 ammo pickups; 5 damage tiers as ratios | none | low | G8 |
| Vanguard | C:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | MAP | E: LD's script (untested); BD22 armor class? | LD gives its BlueArmor: BD22 uses HeavyArmor | none | G9 |
| ActionHero | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E: 1 s infinite ammo per pickup | none | none | G8 |
| Arcing | U:RL | MIS | R: rocket becomes bouncing grenade | BD22 already has a Grenade Launcher | high | G3 |
| Bouncy | U:RL,PR,BF | MIS | R: bounce on impact | none | low | G3 |
| Burst | U:Fi,Pi,Sg,SS,RL,BF | FIRE | R: 3 shots per pull for 3 ammo | BD22 pistol has its own burst mode; pump/SSG between shots (Q6, Q12) | med | G5 |
| Chargeup | U:Fi,Pi,Sg,SS,Cg,RL,PR,BF | FIRE | R: store N shots, release all | Plasma alt fire is already a charge shot (do not touch); BFG charge | med | G5 |
| Cluster | U:RL,PR,BF | MIS | R: our projectile bursts into LD's count of minis | none | low | G3 |
| Comrade | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | DMG | E: x player count (1 in single player) | none | none | G1 |
| Energetic | U:BF | MIS | R: 2x BD22's ray count | none | none | G4 |
| Flak | U:Pi,Cg | BUL | E: LD's LDFlakDamage on airborne targets | none | none | G2 |
| Focusing | U:Cg,PR | FIRE | R: 5 tiers while firing | spread in VR is the controller's aim (only cone spread can shrink) | none | G5 |
| GroupTherapy | U:RL | MIS | E: LD's chain on kill, no splash | Champions death effects can chain too (perf) | low | G3 |
| Hardened | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E: LightArmor counts as HeavyArmor | none | none | G8 |
| Heavy | U:Fi,Pi,Sg,SS,Cg,RL,PR,BF | BUL | E: kickback 4000 on our puff/projectile | none | none | G2 |
| Hunting | U:Fi,Pi,Sg,SS,Cg,RL,PR,BF | FIRE | R: 3x, knockback, slower cycle, self push | self push = artificial locomotion (Q11); hand actions (Q6) | low | G5 |
| Hyper | U:RL,PR,BF | MIS | E: x1.05/tic | none | none | G3 |
| Illuminating | U:RL,PR,BF | MIS | E: lights + idle glow | dynamic lights on Quest are costly (section 5) | none | G3 |
| Lunging | U:Fi | MEL | E: LD's velocity | artificial locomotion burst in VR (Q11) | low | G7 |
| Medic | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E (multiplayer only) | none | none | G8 |
| Mysterious | U:RL,PR,BF | MIS | E: random warp +-32 every few tics | none | low | G3 |
| Optional | U:Pi,Sg,SS,Cg,RL,PR,BF | AMMO | R: empty -> LD's ratio of a shot (40% on the shotgun) | empty magazine normally means hand reload (Q7) | low | G6 |
| Proximity | U:RL,PR,BF | MIS | R: projectiles stop and drift to enemies | none | high: rockets become mines | G3 |
| Recycling | U:Pi,Sg,SS,Cg,RL,PR,BF | AMMO | R: LD's counters mapped to BD22 ammo types | none | none | G6 |
| Redirecting | U:RL,PR,BF | MIS | R: one bounce then turn to nearest enemy | none | low | G3 |
| Scattering | U:BF | FIRE | R: rays straight from the gun for less ammo | none | med | G4 |
| Scrounger | U:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E: +20% per copy | none | none | G8 |
| Shielding | U:Cg,PR | PLR | E: LD's shield actor | VR: in front of the gun or the body? (Q11b) | low | G5 |
| Shockwave | U:BF | MIS | R: explosion instead of rays | none | med | G4 |
| Sluggish | U:RL,PR,BF | MIS | R: x0.98/tic, ripper, LD's damage-by-speed | none | low | G3 |
| Transmogrifier | U:Pi,Sg,SS,Cg,RL,PR,BF | AMMO | Call: which BD22 ammo feeds which gun | magazine loading by hand with foreign ammo (Q7) | med | G6 |
| Accelerator | R:RL,PR,BF | FIRE | R: instant attack with our projectile's explosion | none | high: launcher becomes hitscan | G3 |
| Advanced | R:Pi | FIRE | R: faster, stronger | BD22 pistol already has a magazine + hand reload: LD's mag maps onto ours | low | G5 |
| Beam | R:PR,BF | FIRE | R: constant beam from our muzzle | costly as written; drawn beam must start at the drawn muzzle | high | G5 |
| Blaster | R:Fi | MEL | R: plasma balls while holding fire | VR fists punch by swinging; what is 'holding fire' (Q11) | med | G7 |
| Blazing | R:RL,PR,BF | FIRE | R: constant flame stream from our muzzle | BD22 VR flamethrowers (flamespout.zs) exist | high | G5 |
| Chronostrike | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | MAP | E: LD's script (untested) | time freeze at map start in VR (comfort fine) | none | G9 |
| Concentrating | R:RL,PR,BF | MIS | R: damage grows with flight time | none | none | G3 |
| Decaying | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | DMG | R: LD's random(1,30)/avg spread as a ratio of our damage | none | none | G1 |
| Doubletap | R:Sg,SS | FIRE | R: two shots per shell before pump | hand pump / break action (Q6) | med | G5 |
| DualWield | R:Pi | FIRE | Call: better stats on two pistols | BD22 VR has DualPistols / off-hand copies (Q8) | low | G5 |
| Entrenched | R:Cg,PR | PLR | E: immobile, 50% resist, 2x | none (stopping is comfortable) | none | G5 |
| Explosive | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | BUL | E: LD's explosive puff/explosion on our hits | none | low | G2 |
| Extended | R:Fi,Cs | MEL | R: longer reach | VR fist reach is the arm; saw is a hitscan | none | G7 |
| Ghostly | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PLR | E: LD's protection on invisibility | none | none | G8 |
| HighExplosive | R:RL | MIS | E: radius x2 | self damage with VR muzzle start | none | G3 |
| Illegal | R:Pi,Sg,SS,Cg,RL,PR,BF | AMMO | E: free shots, enemies angry | magazine/reload (Q7) | none | G6 |
| Intimidating | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PLR | E: LD's items on invulnerability | none | none | G8 |
| Marksman | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | DMG | Call: BD22 bullets are already fixed (FBF_NORANDOM): no-op there; max on random projectiles | none | none | G1 |
| Nuclear | R:Pi,Sg,SS,Cg,RL,PR,BF | AMMO | R: LD's 60% damage, no ammo | does the magazine still empty / reload (Q7) | low | G6 |
| Perfect | R:Pi,Cg | BUL | R: 2x max, 0 spread, miss jams | jam needs a VR clear action: hand rack? (Q6) | low | G2 |
| PointBlank | R:Pi,Cg | BUL | R: LD spread, refund on hit | which pool the refund goes to (Q7) | none | G2 |
| Rapid | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | FIRE | R: 2x the gun's own fire cycle | pump/bolt/hand reload are by hand (Q6) | med | G5 |
| Resourceful | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E | none | none | G8 |
| Seeker | R:RL,PR,BF | MIS | E: LD's seeker call on our projectile | BD22 VR RL lock-on alt (rlock.zs) also homes (Q12) | low | G3 |
| Shaman | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E (multiplayer only) | none | none | G8 |
| ShapedCharge | R:RL | MIS | E: no self damage | none | none | G3 |
| Sniper | R:Pi,Sg,SS,Cg | BUL | E: 0 spread | VR aim is the controller; only the cone goes | none | G2 |
| Spamtastic | R:RL,PR,BF | MIS | E: LD's spawn chance per tic | none | low | G3 |
| Suppression | R:PR | MIS | R: small inaccurate plasma, 1 cell per 5 | none | med | G3 |
| Suspenseful | R:Pi,Sg,SS,Cg | BUL | E: LD's counter | needs miss detection per pellet | none | G2 |
| TORGUE | R:RL | MIS | E: LD's death explosions | Champions/BD22 gibs chain (perf) | low | G3 |
| Vacuum | R:RL,PR,BF | MIS | E: LD's pull | costly as written (section 5) | none | G3 |
| Vidmaster | R:RL | MIS | E: full damage over radius | none | none | G3 |
| Waveform | R:PR | MIS | R: two weaving plasma balls | none | med | G3 |
| Wildfire | R:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | MAP | E: LD's script (untested) | none | none | G9 |
| WindUp | R:Cg,PR | FIRE | R: slow start to 1-tic refire | Minigun already spins up | low | G5 |
| Annihilating | E:BF | MIS | E: LD's explosion + exploding rays | none | low | G4 |
| Augmented | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E | none | none | G8 |
| Champion | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E on BerserkPack | none | none | G8 |
| Collector | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E | none | none | G8 |
| Convincing | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | HIT | E: LD's token rule | Champions' champions are not BOSS: can be converted | med: gun does no damage | G1 |
| Cursed | E:Pi,Sg,SS,Cg,RL,PR,BF | BUL | R: x4, a miss hurts you | miss detection per pellet | none | G2 |
| Facekicking | E:Fi | MEL | E: kicks, jump kicks | BD22 has a kick; jump kick = locomotion (Q11) | low | G7 |
| Favoured | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | DMG | Call: LD counts its 9 weapons; BD22 VR has ~30 | none | none | G1 |
| Gauss | E:Pi,Sg,SS,Cg | BUL | R: our pellets as piercing rails | True Bullets: RSQ_PiercingRound exists (Ruger) | med | G2 |
| Goldeneye | E:RL | MIS | E: LD's damage actor | costly (section 5) | none | G3 |
| Gyrojet | E:Pi,Sg,SS,Cg | BUL | R: mini-missiles at our damage | rounds/tracers skipped | high | G2 |
| Imaginary | E:Cs | MEL | E is a joke actor + LD voice | sound is the effect (Q2) | low | G7 |
| Irradiated | E:RL,PR,BF | MIS | E: LD's pulses | costly as written (section 5) | low | G3 |
| Lacerating | E:Cs | MEL | E: LD's ramp | none | none | G7 |
| NanoCircuit | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | HIT | E: LD's chance and bonuses | none | none | G1 |
| NorthernStar | E:Fi | MEL | E: LD's stun and delayed damage | VR: rapid punching is the player's arms | med | G7 |
| OnePunch | E:Fi | MEL | E: LD's projectile and cooldown | VR: what charges a real punch (Q11) | med | G7 |
| Overflowing | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | AMMO | Call: which BD22 ammo types count (BD22 has more than LD's four) | none | none | G6 |
| Overkill | E:RL | FIRE | R: 5x ammo giga rocket | magazine: 5 rockets in a mag? (Q7) | med | G3 |
| Plasmatic | E:Pi,Sg,SS,Cg,RL | BUL | R: our hitscan replaced by LD's plasma, our damage ratio | rounds/tracers (playerrounds.zs) skipped | high | G2 |
| Prototype | E:BF | MIS | R: plasma spray from the BFG | none | med | G4 |
| Raycaster | E:RL | MIS | R: BD22 BFG rays from our rocket | none | low | G4 |
| ShortRange | E:Pi,Sg,SS,Cg,RL,PR,BF | BUL | R: our shot x3 at LD's ranges | none | med | G2 |
| SixShooter | E:Pi | FIRE | R: 10x, slower | the Moonlight revolver stands in for the pistol | med | G5 |
| Soulstorm | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | PICK | E on LifeSphere_Vox/EnergySphere_Vox | none | none | G8 |
| Thematic | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | DMG | E: counts Thematic legendaries | none | none | G1 |
| TripleThreat | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | BUL | R: our pattern three times at +-15 deg | none | med | G2 |
| TwinShot | E:Fi,Cs,Pi,Sg,SS,Cg,RL,PR,BF | BUL | R: two shots for one ammo | none | low | G2 |
| Unfathomable | E:Pi,Sg,SS,Cg,RL,PR,BF | AMMO | Call: 'all your ammo' = magazine or reserve | magazine/reload (Q7) | med | G6 |

Identity risk (flagged, not decided): high 7, med 24, low 35, none 58. High: Accelerator, Arcing, Beam, Blazing, Gyrojet, Plasmatic, Proximity. Med: Blaster, Burst, Chargeup, Convincing, Doubletap, Gauss, Kinetic, NorthernStar, OnePunch, Overkill, Prototype, Rapid, Scattering, Shockwave, ShortRange, SixShooter, Slug, Spreadfire, Stasis, Suppression, Transmogrifier, TripleThreat, Unfathomable, Waveform.

## 3. Groups by shared hook (batch order)

Size: S about one working session, M two to three, L four to six (each including the rig proof of every effect in it: a log line or frames per effect, per CLAUDE.md "shown working only"). Order is the order I would build them: cheapest proofs and fewest VR conflicts first, the hand-driven weapon code last.

| Order | Group | What it is | Size | Effects |
|---|---|---|---|---|
| 1 | G0 | Foundation: effect registry, shot context, off-hand source, passives counter, rig probe; fixes to the carried 56 | M | re-proof and fixes of the 56 carried |
| 2 | G9 | Map start / respawn buffs (LD's own scripts, prove on rig, fix BD22 classes) | S | Chronostrike, Restoring, Scrambling, Vanguard, Wildfire (5) |
| 3 | G1 | Damage rules and on-hit items (RSLDP_Amp / WorldThingDamaged) | S | Comrade, Convincing, Decaying, Favoured, Marksman, NanoCircuit, Thematic (7) |
| 4 | G8 | Pickup passives (a HandlePickup token on the player; BD22 items) | M | ActionHero, Armorer, Augmented, Champion, Collector, Ghostly, Hardened, Hoarder, Intimidating, Medic, Quartermaster, Resourceful, Scanner, Scrounger, Shaman, Soulstorm, Spiritual, Survivor, Sustained, Upgrading (20) |
| 5 | G2 | Shared bullet path: shot shape (WorldHitscanPreFired cancel + re-fire, before muzzle.zs) | L | Blastwave, Choked, Cursed, Explosive, Flak, Gauss, Gyrojet, Heavy, Perfect, Plasmatic, PointBlank, Renegade, ShortRange, Slug, Sniper, Suspenseful, TripleThreat, TwinShot (18) |
| 6 | G6 | Ammo and magazine effects | M | Illegal, Nuclear, Optional, Overflowing, Recycling, Transmogrifier, Unfathomable, Unknown (8) |
| 7 | G3 | Per-missile riders (rockets, plasma, grenades) | L | Accelerator, Arcing, Bouncy, Cluster, Concentrating, Goldeneye, GroupTherapy, HighExplosive, Hyper, Illuminating, Irradiated, Kinetic, Mysterious, Overkill, Penetrating, Proximity, Redirecting, Seeker, ShapedCharge, Sluggish, Spamtastic, Spreadfire, Suppression, TORGUE, Tricky, Vacuum, Vidmaster, Waveform (28) |
| 8 | G4 | BFG ball and ray family | M | Annihilating, Energetic, Energizing, Nova, Prototype, Raycaster, Scattering, Shockwave, Stasis (9) |
| 9 | G10 | Alerts and cosmetic-only effects | S | Agitating, Stealth (2) |
| 10 | G7 | Melee (VR fists, saw) | M | Blaster, ColdBlooded, Extended, Facekicking, Imaginary, Lacerating, Lunging, NorthernStar, OnePunch, RazorEdge (10) |
| 11 | G5 | Fire cadence and trigger effects (BD22 VR weapon code) | L | Advanced, Beam, Blazing, Burst, Chargeup, Doubletap, DualWield, Entrenched, Focusing, Hunting, Quickdraw, Rapid, Recursive, Shielding, SixShooter, Trailblazing, WindUp (17) |

Notes per group:
- **G0 Foundation (M), first.** Replace the string `if` chains in `effects.zs`/`handler.zs` with one table: effect ->
  hooks it uses -> its LegenDoom numbers (generated from LegenDoom's DECORATE by `tools/`, so every number names its
  source line). A per-shot context (one roll per trigger pull, not per pellet: fixes Lucky; which hand fired: fixes
  off-hand copies; shot seen from `WorldHitscanPreFired` / missile spawn / melee strike instead of per-tic ammo diffs).
  A passives counter that counts every owned legendary like LegenDoom's `LD_CountEffect` (passives stack across all
  owned guns, not the gun in hand). A rig probe (`netevent` that forces effect X onto the held gun and logs what it
  did), so each of the 180 gets its own log line as proof. Re-prove and fix the 56 (gaps in section 1, "G").
- **G9 Map start (S).** LegenDoom's own `LD_ApplyStartBuffs` already runs; Vanguard/Restoring give LegenDoom's
  vanilla classes (BlueArmor, health), which must become BD22's (HeavyArmor). Untested today (patch README).
- **G1 Damage rules (S).** Same place as Pristine/Raging today. Comrade is 1x in single player. Marksman and Favoured
  need Q13/Q14.
- **G8 Pickup passives (M).** One HandlePickup token, a table BD22 item -> LegenDoom script rule
  (`LEGENDITM.acs` LD_<Item>Activate). Quartermaster/Armorer/Medic/Shaman are multiplayer-only.
- **G2 Shared bullet path (L).** The biggest single gain: one re-fire layer serves pistol, shotgun, SSG, minigun,
  rifle, revolver and their copies. Miss detection (Cursed, Suspenseful, PointBlank, Perfect) comes from the
  re-fired `LineAttack`'s result / `WorldHitscanFired`. Plasmatic and Gyrojet replace the pellet with a missile from
  the muzzle (then G3 rules apply).
- **G6 Ammo (M).** Needs Q7 first: every row depends on magazine vs reserve.
- **G3 Missile riders (L).** 28 effects on 3-4 projectile classes each (Rocket2, Rocket2Fast, RocketDM, PlasmaBall75,
  Plasma_Ball, PlasmaBallDM, and the Rifle's ShortGrenade if the Chaingun family keeps its M203). Most are one flag or
  one per-tic line (Hyper, Sluggish, Seeker, Mysterious, Vacuum, Irradiated); Cluster/Spreadfire/Spamtastic spawn
  copies of OUR projectile; Accelerator and Overkill also touch fire states.
- **G4 BFG family (M).** BD22's `BFGBall` death and its `A_BFGSpray` (brutal22test6 BFG.dec): Energetic/Shockwave/
  Nova/Annihilating/Raycaster change the death; Scattering fires the spray from the gun; Prototype is a spray of
  small plasma.
- **G10 Alerts and cosmetics (S).** Stealth suppresses BD22's alert paths (A_AlertMonsters, the `Alerter` and
  `DistantFireSound*` missiles); Agitating is only LegenDoom's scream + mugshot (Q2).
- **G7 Melee (M).** On BD22's MeleeStrike from the real VR punch; Lunging/Facekicking/OnePunch/NorthernStar/Blaster
  need Q11 (what a "charge" or "hold" is with real arms, and locomotion pushes).
- **G5 Fire cadence (L), last.** Rapid, Trailblazing, WindUp, Burst, Doubletap, Chargeup, SixShooter, Advanced,
  DualWield, Recursive, Focusing, Hunting, Blazing, Beam, Shielding, Entrenched, Quickdraw touch every family gun's
  own states (about 22 classes with Purist/Dual copies) and the hand-driven actions (pump `RSP_*`, break action
  `RSB_*`, magazine `RSR_*`, flick reload). Each needs Q6 and frames on the rig per gun.

**Total, in plain terms:** about 36 working sessions (G0 3, G9 1, G1 1-2, G8 3, G2 5, G6 2-3, G3 6, G4 3, G10 1,
G7 3-4, G5 6-8), with a rig log for each of the 180. Roughly the first half (G0, G9, G1, G8, G2) brings the count from
56 to about 125 with almost no touch on hand-driven weapon code; the second half is the hard part.

## 4. Sounds (owner: OUR sounds, not LegenDoom's)

What carries over with no work: LegenDoom's per-rarity gun sounds (`shotgun/commonfire` ... `epicfire`, `*/rarepump`,
`rocketlauncher/rareexplode`, ...) are only in LegenDoom's own weapon states, which we never run: our guns keep their
fire, pump, reload and BD22 VR hand sounds for every effect.

LegenDoom sounds the patch ALREADY plays today (to be replaced): `effects/patient`, `effects/sensing`
(handler.zs WhileHeld); LegenDoom's `rocketlauncher/explode` + `misc/gibbed` (LDViolentExplosion, Violent),
`rocketlauncher/epicexplode` (LDFreezingImpact, Freezing), `items/berserkpickup` (WarmUp's berserk), LegenDoom's
pickup jingles (`effects/newlegendarypickup`, `epicnewlegendarypickup`, `effects/<effect>pickup`) on its pickup
screen, and the legendary-monster loops (`effects/legendaryenemy*`, `legendaryrobot*`).

Effect sounds and the BD22 / BD22 VR sound that would replace each (names from brutal22test6 SNDINFO.* and
BD22 VR SNDINFO.rsq; a proposal, the owner picks by ear):

| LegenDoom sound | Effect(s) | Ours instead |
|---|---|---|
| effects/stealth<gun> (quiet shot) | Stealth | our gun's own fire sound at low volume and short attenuation (no new sound) |
| effects/renegade1-6 (screams) | Renegade (32/256 per shot) | Q2: BD22 player taunt (TAUNT01-18) / silent |
| effects/agitating* (screams, bone casings) | Agitating | Q2: the effect IS these sounds |
| effects/imaginary, imaginaryidle ("EEEE") | Imaginary | Q2: Chainsaw/Idle, Chainsaw/Loop |
| effects/kenshiroloop/yell/stop, northernstarloop, northernstargib | NorthernStar | KICKHIT1-3 per strike, BD22 gib sound; Q2 for the voice |
| effects/rageattack | Raging | BERSPKUP (BD22 berserk) or none |
| effects/unknown | Unknown | Pickup/Invis |
| effects/chargeup, chargeupdone | Chargeup | Plasma/Charge, Plasma/FullyCharged |
| effects/hunting, huntingenergy | Hunting | our fire sound + BD22 VR's exterior tail (rsb/tail/*) |
| effects/bouncyrocket/plasma/bfg9000 | Bouncy, Tricky, Redirecting, Arcing | Grenade/Bounce |
| effects/seekerrocket | Seeker, Proximity | Rocket/Fly (BD22's rocket loop) |
| effects/lucky | Lucky | Plasma/BeepBeep (proposal) |
| effects/patient | Patient (each stack) | Plasma/Beep |
| effects/sensing | Sensing (each pulse) | Plasma/BeepQuiet |
| effects/gauss | Gauss | Railgun/Fire |
| effects/plasmaattack, plasmarocket | Plasmatic | Plasma/Fire, Plasma/AltFire |
| effects/gyrojet | Gyrojet | Weapons/GrenadeFire or Rocket/Fire, quiet |
| effects/machineloop, machineend | Machine | our pistol's fire per shot (no loop) |
| effects/sixshooter, sixshooter2 | SixShooter | Revolver/Fire, Revolver/Hammer |
| effects/advancedreloadout/in/cock | Advanced | our pistol's BD22 VR hand-reload sounds (already there) |
| effects/blazingstart/loop<gun>, blazing<gun>, blazingimpact | Blazing | Flamer/loop, Flamer/stop, burn, rsb/flame/hiss1-2 |
| effects/beamstart/loop/end<gun> | Beam | Unmaker/Start, Unmaker/Loop, Unmaker/Stop (or BFG10K/Charge, Idle, Stop) |
| effects/irradiated1-4 | Irradiated | rsb/impact/electric1-5 (proposal) |
| effects/stasis, stasis2 | Stasis | SLOWON, SLOWOFF |
| effects/energizingstart, energizing | Energizing | BFG/Charge; BD22 health bonus pickup per heal |
| effects/vidmaster, vidmasterexplode | Vidmaster | Devastator/explode |
| effects/goldeneye, goldeneyeexplode | Goldeneye | Explode5 / Explode6 |
| effects/grouptherapy, torgue | GroupTherapy, TORGUE | Barrel/explode, Explode1 |
| effects/raycaster | Raycaster | BFG/Fire |
| effects/annihilating | Annihilating | BFG/Explosion |
| effects/blastwave | Blastwave | Explode2 |
| effects/onepunch, onepunchloop, onepunchcharge, onepunchshockwave | OnePunch | Plasma/Charge, Kick/Swing, BFG/Explosion |
| effects/facekickinghitflesh, facekickinghitwall | Facekicking | KICKHIT1-3, KICKWAL1-3 (BD22's own kick) |
| effects/blaster | Blaster | Plasma/Fire |
| effects/nanocircuit | NanoCircuit | BD22 health bonus + armor shard pickup sounds |
| effects/medic, shaman, quartermaster | Medic, Shaman, Quartermaster | the shared BD22 item's own pickup sound |
| effects/restoring, vanguard, resupplying, wildfire, chronostrike | start buffs | MEGAPKUP, Pickup/HeavyArmor, BD22 backpack pickup, invulnerability pickup, SLOWON / announcer timefreeze |
| effects/upgradinglevel, upgradingmeter | Upgrading | Plasma/FullyCharged, Plasma/Beep |
| LegenDoom projectile See/Death sounds (rocketlauncher/*, plasmarifle/impact, bfg9000/*) | any LegenDoom projectile we spawn | our projectile's BD22 sounds (Rocket/Fire, explosions, Plasma/Fire, BFG/Explosion) |

## 5. Performance: costly as LegenDoom wrote them, and the cheaper same-behaviour version

Parsed from LegenDoom's DECORATE/ACS; not measured on the Quest. Each line keeps the behaviour (same numbers, same
timing) and changes only how it is computed.
- **Death and debuff checkers.** Every on-hit/on-kill effect gives the monster an item that spawns a checker actor
  polling its master every tic (`LD<Effect>EffectChecker`, `...CheckerSpawner`). With BD22's 9-pellet shotgun (14 Tactical)
  that is up to 9-14 gives per blast. Cheaper: the patch already skips the checker for kills (gives `LD<Effect>EffectDeath`
  from `WorldThingDied`); extend that to debuffs: one ZScript list of (monster, effect, timer) ticked once per tic.
- **Sensing.** `A_RadiusGive(LDSensingEffect, 1024, MONSTERS|OBJECTS|ITEMS|NOSIGHT)` every 35 tics spawns a marker per
  thing in range; in BD22 that includes gore objects. Cheaper: one BlockThingsIterator pass for monsters, barrels and
  items only, markers kept in a list and drawn on the automap overlay (no actors). Same radius, same period.
- **Vacuum.** `A_RadiusThrust(-160, 1024)` every tic per projectile: each plasma ball scans a 1024 radius every tic
  (12 balls in flight = 12 scans a tic). Cheaper: one scan per tic for all vacuum projectiles of a player, the same
  thrust applied per pair.
- **Irradiated / Freezing / Igniting / Goldeneye / Flak.** Repeating A_Explode pulses and impact actors, plus 10
  particle actors per pulse (Irradiated). Cheaper: keep the pulses (they are the behaviour), drop LegenDoom's
  particle actors for our own client-side particles (A_SpawnParticle, no actors), cap concurrent pulse actors.
- **Projectile visuals.** LegenDoom's rockets spawn a smoke-trail ACTOR every tic and about 80 particles on death;
  its projectiles carry dynamic lights. We keep BD22's own projectiles and visuals, so none of this comes over. Only
  Illuminating's lights are the effect itself; dynamic lights cost on the Quest GPU: one light per projectile, no
  idle glow light when the light radius is off screen.
- **Beam.** `LEGENDBEM.acs` (376 lines, 98 references) builds the beam from emitter actors along the line every tic.
  Cheaper: one LineTrace per tic for damage and a single stretched beam model or a few particles, from the drawn
  muzzle.
- **Recursive / Spamtastic / Cluster / Prototype.** Spawn many projectiles; keep the counts (they are the behaviour),
  spawn our lightest projectile class and skip per-tic smoke.
- **Patch-side costs today.** `EffectOf` walks the whole inventory with string compares every 8 tics per player;
  `InGroup` does `String.Split` per hit; `RSLDP_Amp` calls `EventHandler.Find` per damage event. Cheaper: resolve the
  effect once on weapon change and on pickup (cache a class -> effect map), precompute monster groups per class once.
- **Shot detection.** Today's per-tic ammo diff misses off-hand shots and melee; the event hooks (G0) are cheaper and
  exact.
- **Chains with Champions.** Violent, TORGUE, GroupTherapy explode on death; Champions' own death effects and BD22's
  gibs can chain. Cap chain depth per tic (same total damage, spread over tics), and prove a worst case on the rig.

## 6. What it means for the existing patch and the owner's other systems

**Keep as it is:** the 56-class replacement restore (CheckReplacement + `tables.zs Repl`), LegenDoom's legendary
monsters, the drop converter and pickup (`pickup.zs`), unlock tokens, death-spot fix, "Legendary Guns Only From
Bossfights" (RSQMB_Service), the menu, `RSLDP_Service` (`ld_prefix`) for RSQ Wheel, the Debug Log.

**Rewrite:** `effects.zs` and the effect half of `handler.zs` become the G0 registry; `RSLDP_Amp` stays as the outgoing
damage hook but reads the shot context; shot detection moves from ammo diffs to events. Fix the carried gaps: Lucky
(per trigger pull), Annoying (+FORCEPAIN), Thieving (random ammo type, mapped to BD22's), SteadyShot (0 spread),
Machine (fire rate), CQC (spread x3), Battlerage (must not speed hand actions, Q6), the group x3 effects (one damage
event, not a second hit, so Champions' resistances and pain chance see one hit), Patient (the window), and the LD
sounds listed in section 4. `rsldp_reroll` loses its purpose once all 180 are carried; keep it only for effects the
owner turns down (Q5, Q11, Q14). The README's "Effects carried (56)" and "Not carried (124)" sections are rewritten
per batch, each effect only once its rig log exists ("Option names promise only what has been proved").

**Where the code lives (Q1).** Fire-cadence effects (G5) need hooks inside BD22 VR's own weapon states; everything
else can stay in the patch. A merge means BD22 VR ships those hooks (no-ops without LegenDoom).

**RSQ Wheel legendary card.** Reads the gun's tokens through `ld_prefix` and shows LegenDoom's name and description:
no change needed for new effects. If the owner picks a non-LegenDoom behaviour anywhere (Q2, Q5, Q7, Q11, Q13), the
card's LegenDoom text for that effect would no longer be true and needs our text. With off-hand copies (Q8), the card
needs to know which hand's legendary to show.

**Bossfight-only legendary drops.** Untouched (it judges the drop, not the effect). With all 180 rollable, the re-roll
no longer narrows the pool, so drops follow LegenDoom's real odds per rarity.

**Champions.** Untouched code, but effects meet it: Convincing can turn a champion friendly (LegenDoom only excludes
BOSS and its own transformed legendaries); Stasis freezes champions forever unless BOSS; DemonSlayer x4 hits only
LegenDoom legendaries (a legendary champion is both); Heroic's "bosses" are bBOSS / Cyberdemon / Mastermind (RSQ
Miniboss's minibosses only if they are bBOSS, Q15); Whittling/Crippling stack with champion resistances; death
explosions chain (section 5).

## 7. Questions for the owner

1. **Where does the merged code live?** (a) It stays a separate patch loaded last; BD22 VR adds only small no-op
   hooks in its fire states. (b) Everything moves into BD22 VR as an "LD mode" that turns on when LegenDoom is loaded.
   (c) Separate patch, and the fire-cadence effects (G5) are left out.
2. **Effects whose behaviour IS a LegenDoom sound** (Agitating's screams, Renegade's scream, Imaginary's "EEEE",
   NorthernStar's Kenshiro voice): (a) our nearest BD22 sound (taunts, saw idle, kick hits). (b) silent; mechanics only.
   (c) keep LegenDoom's for these four only.
3. **LegenDoom's non-weapon sounds** (legendary pickup jingles, the pickup screen, legendary-monster aura loops):
   (a) keep LegenDoom's (they are not gun sounds). (b) replace with BD22/our sounds. (c) silent.
4. **Effect visuals:** (a) our projectiles and BD22 visuals, plus LegenDoom's visuals only where the visual is the
   effect (rays, beam, radiation, stasis, shield). (b) pure BD22/our visuals everywhere. (c) LegenDoom's effect visuals.
5. **Effects that replace the gun's shot** (Plasmatic, Gyrojet, Accelerator, Beam, Blazing, Gauss, Arcing,
   Proximity): (a) LegenDoom's rule: the gun fires that attack from our drawn muzzle, at our damage ratio, our sounds.
   (b) keep the gun's own round and add the effect on top where possible. (c) leave them out (re-roll).
6. **Fire-rate effects vs hand actions** (Rapid, Burst, Doubletap, Trailblazing, WindUp, Battlerage, Perfect's jam;
   pump, break action, bolt, magazine): (a) only the trigger cycle gets faster; hand actions stay at hand speed.
   (b) everything the gun draws gets faster, reload rows included. (c) the effect applies only to guns without a hand
   action between shots.
7. **"Ammo" with magazines** (Unknown, Optional, Illegal, Nuclear, Unfathomable, Transmogrifier, PointBlank, Overkill,
   Unlikely/Improbable/Efficient/Impossible): (a) the effect acts on the magazine; you still reload by hand.
   (b) it acts on the reserve; the magazine works as now. (c) "no ammo" means no reload either (the gun never empties).
8. **Off-hand copies of a legendary gun:** (a) both hands carry the legendary. (b) main hand only. (c) the copy is its
   own gun and needs its own legendary.
9. **Passives ([PASSIVE]/[STACKS]: Sustained, Survivor, Hoarder, Scrounger, ...):** LegenDoom counts every legendary
   you own, held or not. (a) LegenDoom's rule (any owned, stacking). (b) only while that gun is held.
10. **BD22 guns with no LegenDoom counterpart** (SMG, MP40, Revolver, Assault Shotgun, Sniper, MG42, Railgun, Grenade
    and Incendiary Launchers, Devastator, Nuke, BFG10k, Unmaker, Flamethrowers, Axe, Dragonslayer): (a) stay
    non-legendary. (b) join the nearest LegenDoom slot (SMG/MP40/MG42 -> Chaingun, Assault Shotgun -> Shotgun, ...).
    (c) a later, separate scope.
11. **Effects that move the player or need a "hold"** (Lunging, Hunting's push, Facekicking's jump kick, RazorEdge,
    Chronostrike; OnePunch's charge, Blaster's hold, Shielding's placement): (a) LegenDoom's behaviour; charge/hold =
    the trigger held on the fist hand; shield in front of the gun. (b) the same, with a comfort option that turns off
    locomotion pushes. (c) re-roll the locomotion ones away.
12. **Collisions with BD22 VR's own features** (Slug alt fire vs Slug, RL lock-on vs Seeker, the pistol's burst mode
    vs Burst, the plasma charge alt vs Chargeup): (a) the legendary changes primary fire only; alt fires stay as they
    ship. (b) the legendary wins where they overlap. (c) the BD22 VR feature wins; the effect is re-rolled.
13. **Marksman / Decaying on fixed-damage guns** (BD22 bullets use FBF_NORANDOM): (a) literal: Marksman does nothing
    on fixed-damage guns, Decaying randomises around our fixed value. (b) LegenDoom's average gain as a ratio
    (Marksman x1.5 = 15 vs an average 10).
14. **Counting effects built for LegenDoom's 9 weapons and 4 ammo types** (Favoured: 50 - 5 per weapon owned;
    Overflowing: per maxed ammo type; Transmogrifier: which ammo feeds which gun): (a) count only the nine LegenDoom
    families and their four ammo kinds. (b) count every BD22 weapon / ammo type (Favoured weakens fast). (c) re-roll them.
15. **Multiplayer-only effects and bosses** (Quartermaster, Armorer, Medic, Shaman, Comrade do nothing in single
    player; Heroic's bosses): (a) carry exactly; do nothing solo. (b) re-roll them in single player; Heroic also counts
    RSQ Miniboss's minibosses.
16. **Build order:** (a) the order in section 3. (b) first the groups that bring the most effects with no hand-code
    risk (G0, G2, G3), then the rest. (c) the owner picks the order.


## 8. The owner's answers (2026-11-06)

- **Q1 Where:** inside BD22 VR (an LD mode that switches on when LegenDoom is loaded).
- **Q6 Fire rate vs hand actions:** the trigger cycle gets faster; the gun's own shot counter decides, and the hand
  action stays where it is in the cycle. "A burst pump shotgun isn't unreasonable, and a break-action burst super
  shotgun should still work": a burst fires its shots from what's loaded, then the pump / break waits for the hand
  as now. Any gun that misbehaves gets its own patch (the weapon code is ours).
- **Q7 Ammo effects:** they act on the magazine. A free shot takes no round from it: "say my gun holds 15 shots
  before reload, but i get four free shots. well now it holds 19 before i reload." Hand reload as normal after.
- Checked for the owner: no LegenDoom effect raises magazine capacity (LegenDoom's guns have no magazines; only the
  pistol's Advanced has its own magazine, which maps onto ours).
