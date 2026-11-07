# LD mode effect interface (Agent A, v3, 2026-11-06 ~09:40)

Everything lives in BD22 VR's `src/` (repo `/home/claude/rs_brutal22weaponsq`). Class prefix `RSLD_`.
The LD mode is on only when LegenDoom 3.0 is loaded (`RSLD.On()`: its classes `LDPlayer` and
`LDLegendaryMonsterToken` exist at run time). Without LegenDoom every hook below is never called.

## 1. How you add an effect (no registration call)

Write a class named `RSLD_Fx_<LegenDoomName>` that extends `RSLD_Effect`, in YOUR file
`src/zscript/rsld/<group>_*.zs` (e.g. `src/zscript/rsld/g2_bullets.zs`). `<LegenDoomName>` is the effect's
name exactly as in LegenDoom's tokens (`LD<Slot>Effect_<Name>`, LANGUAGE.effectname keys), e.g. `RSLD_Fx_Renegade`,
`RSLD_Fx_TripleThreat`, `RSLD_Fx_Antiair` (LegenDoom spells it `Antiair`).
The handler finds every `RSLD_Effect` subclass at start (AllClasses) and makes one instance of each: that IS the
registry. Then tell A the include line (`#include "zscript/rsld/<your file>.zs"`) in NEEDS_B.md / NEEDS_C.md.
A class whose name is not an LD effect is ignored with a log line. Two classes for one name: the boot log says so.

```
class RSLD_Fx_Lucky : RSLD_Effect
{
	override void OnPull(RSLD_Shot s)
	{
		s.b1 = random(0, 255) < RSLD.Num("Lucky", "chance");	// one roll per trigger pull
		if (s.b1) { s.Log("lucky pull"); s.Sound("Plasma/BeepBeep"); }
	}
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.b1) h.mult *= RSLD.Num("Lucky", "mult");
	}
}
```

## 2. Hooks (all virtual, all no-op by default; override only what you need)

Held-gun hooks are called for the effect of the gun that FIRED (its hand, see 4). `copies` = how many of that effect
the player owns over all nine slots (LegenDoom's `LD_CountEffect`).

| hook | when | notes |
|---|---|---|
| `void Init()` | once, at registration | set `passive = true` if you need `Owned` every tic |
| `void OnPull(RSLD_Shot s)` | once per trigger pull, at its first shot event | roll chances HERE (one roll per pull, not per pellet) |
| `bool OnPellet(RSLD_Shot s, RSLD_Pellet p)` | every player hitscan pellet of the pull, BEFORE muzzle/rounds/recoil/flash | change `p.*` to reshape; return true to drop it. Extra pellets: `s.FirePellet(angle, pitch, damage, puff)` (marked as ours: no new pull, no OnPellet) |
| `void OnMissile(RSLD_Shot s, Actor m)` | each player projectile of the pull (rocket, plasma, BFG ball...) | casings/alerters/tracers/strikes are filtered out. m's sounds are BD22's: keep them |
| `void OnMelee(RSLD_Shot s, Actor strike)` | a melee strike actor of the pull (VR punch, kick, bash: BD22's MeleeStrike*/KickAttack*) | the saw/fist hitscans come as pellets with `s.melee = true` |
| `void ModifyDamage(RSLD_Shot s, RSLD_Hit h)` | outgoing damage of this player, before it lands | `h.mult *= x`, or `h.setDamage = n`. Multipliers from ALL steps multiply. One damage event (no second hit) |
| `void OnHit(RSLD_Shot s, RSLD_Hit h)` | after the damage landed on a monster (`WorldThingDamaged`) | `h.killed`, `h.damage` (final) |
| `void OnKill(RSLD_Shot s, RSLD_Hit h)` | the hit killed it | after OnHit |
| `void AfterPull(RSLD_Shot s)` | the tic after the pull | `s.ammoTaken`, `s.magTaken` are known; `s.Refund(n)` gives n back to the pool the pull took from (the magazine first: owner Q7) |
| `void WhileHeld(RSLD_Held c)` | every tic a gun of this effect is in a hand | `c.idle` tics since that hand last fired, `c.attacking`, `c.hand`, `c.weapon` |
| `void Owned(PlayerPawn p, int copies)` | every tic, if `passive` and owned (any slot) | passives that do not depend on the gun in hand |
| `void OnMapStart(PlayerPawn p, int copies)` | map start (tic 6) and respawn, for every owned effect | G9 style start buffs |
| `bool OnPickup(PlayerPawn p, Inventory item, int copies)` | the player touches an item (HandlePickup, BEFORE it is given) | owned effects only; change `item.Amount` etc; return true = item refused |
| `void OnProbe(RSLD_Shot s)` | right after the rig probe forced this effect | optional: set up state for a proof |

`s == null` never happens in pull hooks. In ModifyDamage/OnHit/OnKill `s` can be a "no pull" context
(`s.pull == 0`) for damage that came from no shot we saw (a burn tick from LD's own items is filtered before you).

## 3. RSLD_Shot (one per trigger pull)

Fields: `PlayerPawn mo; int pn; int hand (RSLD.MAIN 0 / RSLD.OFF 1); Weapon weapon; int slot (0..8, LD order
Fists..BFG9000); int rarity (0..3); RSLD_Effect fx; string effName; int tic; int pull (counter, 0 = none);
bool melee; int pellets; int missiles; int hits; int kills; int ammoTaken; int magTaken;`
Effect scratch: `bool b1, b2; int i1, i2; double d1, d2;` (free for the effect that owns the pull).
Methods: `Log(string)` (prints `RSLD <tic> <effect> p<pull> <hand>: ...` when rsld_debug is on);
`Sound(string)` (a BD22 / BD22 VR sound on the shooter, never a LegenDoom one); `Refund(int n)`;
`FirePellet(double angle, double pitch, int damage, class<Actor> puff)` (hitscan, same hand, same flags).

A pull = all shot events of one hand in one tic. One shotgun blast (9 pellets, 14 Tactical, each re-fired by
muzzle.zs) is one pull; a minigun fires one pull per shot tic, as LegenDoom's Fire state runs once per shot.

## 4. Hands (scope Q8 is open)

`s.hand` is the hand that fired (`LAF_ISOFFHAND` / `BT_OFFHANDATTACK` / the controller the missile was born at).
`s.weapon` is that hand's gun (an off-hand copy `RSQ_Off_<Gun>` is a subclass of its gun, so it is in the same
LegenDoom slot). The effect is looked up for `s.weapon`'s slot. Cvar `rsld_offhand_legendary` (server, default 1):
1 = an off-hand copy carries its slot's legendary too (Q8 a); 0 = main hand only (Q8 b). Q8 c (the copy is its own
legendary) is possible later: the context already carries the hand and the weapon.

## 5. RSLD_Pellet, RSLD_Hit, RSLD_Held

- `RSLD_Pellet`: `double angle, pitch` (the event's, with spread rolled in), `double aimAngle, aimPitch` (where the
  gun points: the pull's first pellet's aim, spread 0), `double spreadMul` (1: multiplies the deviation from the
  aim, 0 = perfect accuracy, 3 = CQC), `int damage`, `class<Actor> puff`, `int flags` (LAF_*), `double range`.
- `RSLD_Hit`: `Actor target, inflictor; int damage; Name damageType; double mult; int setDamage (-1 none);
  bool killed; int flags`.
- `RSLD_Held`: `PlayerPawn mo; int pn, hand, slot, rarity, idle; bool attacking; Weapon weapon; RSLD_Effect fx`.

## 6. LegenDoom numbers (every number names its source line)

`RSLD.Num(effect, key)` -> double, `RSLD.NumSrc(effect, key)` -> "decorate/Shotgun/Shotgun.dec:1440". A missing
number logs `RSLD missing number <effect>.<key>` once and returns 0.
Numbers are GENERATED, never typed: `python3 ldl_patch/tools/gen_ld_numbers.py` reads every rules file
`ldl_patch/tools/numbers/*.rules` and writes one table per rules file, `src/zscript/rsld/numbers_<file>.zs`
(class `RSLD_Numbers_<file>` : `RSLD_NumberTable`; all tables are found at run time). Your group writes ITS OWN
rules file (`numbers/g2.rules`) and include line for its generated .zs. Rule lines:

```
# effect    key     file (in the LegenDoom pk3)       state label   call          arg  [scale]
Lucky       chance  decorate/Shotgun/Shotgun.dec      FireLucky     A_Jump        0
Lucky       dmg     decorate/Shotgun/Shotgun.dec      FireLucky     A_FireBullets#2 3
# or a regex over a file, group 1 = the number:
Wildfire    tics    source/LEGENDPLY.acs              re  "PowerInvulnerable.*?(\d+)"
```
`A_FireBullets#2` = the 2nd A_FireBullets call inside that state block. LegenDoom is read from
`$LD_PK3` (default `/mnt/user-data/uploads/1f3eb79e-LegenDoom_3.0.pk3`).

## 7. Helpers (class RSLD, static)

`RSLD.On()`, `RSLD.Debug()`, `RSLD.AC("ClassName")` (class by name at run time; LegenDoom/BD22 classes are
DECORATE), `RSLD.Give(actor, "LDClass", n=1)`, `RSLD.Count(mo, "Effect")` (copies owned, LD_CountEffect),
`RSLD.SlotOf(weapon)`, `RSLD.EffectOf(mo, slot)`, `RSLD.Log(string)`, `RSLD.AddAmmo(inv, n)`,
`RSLD.InGroup(target, "Exorcist")` (LegenDoom's monster groups on BD22/XMVE monsters).

## 8. Rig probe (proof per effect)

Console / rig script (needs `rsld_debug 1` for the log lines):
- `netevent rsld_fx:<Effect> [rarity 0-3]`: takes the held gun's slot legendary away and forces `<Effect>` on it
  (LegenDoom's own tokens, so LegenDoom's HUD/info screen agree). Logs `RSLD probe: <Effect> on <gun> slot <s>`.
  Calls the effect's `OnProbe`.
- `netevent rsld_fx_clear`: removes the held slot's legendary.
- `netevent rsld_target:<MonsterClass> [distance]`: spawns that monster in front of the player, facing it
  (default 160 units), logs its health.
- `netevent rsld_owned`: logs every legendary the player owns and `copies` per effect.
Every hook call logs when `rsld_debug 2` (`RSLD <tic> <effect> <hook> ...`). Your effect logs what it DID with
`s.Log(...)` at `rsld_debug 1`: that line is the proof (scope: "a rig log line per effect").
Rig runner: `ldl_patch/tools/ldrig.sh <name> <secs> "<console script>"` (holds /home/claude/rig.lock, restores
qzdoom.ini, full load order by default; ORDER=nold for BD22 VR alone; log in /tmp/ldrig/<name>.log; prints
script errors). Example:
```
ldl_patch/tools/ldrig.sh lucky1 60 "rsld_debug 1; give Shot_Gun; wait 150; netevent rsld_fx:Lucky; \
  netevent rsld_target:ZombieMan 200; wait 20; +attack; wait 2; -attack; wait 40; +attack; wait 2; -attack"
```

## 9. Files (who owns what)
A owns: `src/ZSCRIPT.rsld`, `src/zscript/rsld/core.zs, handler.zs, data.zs, tables.zs, pickup.zs, menu.zs,
fx_g0.zs, fx_g9.zs, numbers_g0.zs`, `src/CVARINFO.rsld`, `src/MENUDEF.rsld`, `src/MAPINFO.rsld`,
`ldl_patch/tools/*`. B and C: only their own `src/zscript/rsld/<group>*.zs` and `ldl_patch/tools/numbers/<group>.rules`
(+ the generated `numbers_<group>.zs`). Needs (include lines, cvars, menu rows) go in /home/claude/ldmerge/NEEDS_B.md
/ NEEDS_C.md.

Status: v2. BUILT: core.zs/handler.zs/fx_g0.zs/fx_g9.zs compile on the rig (QZD 17.3, full order with LegenDoom,
08:4x: "RSLD: LD mode on: 61 effects registered, 178 numbers"). B's and C's include lines are in src/ZSCRIPT.rsz
(renamed from ZSCRIPT.rsld so it compiles after ZSCRIPT.rsvr / .rsx: RSQ_Muzzle, RSVR_VRHand are visible).

## 10. v2 changes (taken from NEEDS_B v1 / NEEDS_C v1-v3)
- A pull continues over two tics on BD22 VR's pump (`Shot_Gun` and subclasses) and the `Revolver`: a shot at T+1 of the
  same hand's same gun continues the pull begun at T (`s.lastTic`). All other guns: one tic.
- `RSLD_Pellet.index` (0-based original pellet index; -1 for FirePellet/FireRail), `RSLD_Pellet.rail`.
- Aim: `s.aimAngle = mo.angle`, `s.aimPitch = mo.BulletSlope(null, ALF_ISOFFHAND for the off hand)` at the pull's first
  pellet (A_FireBullets' own bslope: autoaim when the gun has it).
- `s.FirePellet(angle, pitch, damage, puff, range = 0 /*PLAYERMISSILERANGE*/, flags = 0)`; `p.range` set in OnPellet is
  honoured by the re-fire. FirePellet/FireRail use their own pellet object (never the `p` OnPellet holds).
- `s.FireRail(angle, pitch, damage, puff, range = 0)`: mo.RailAttack, angle/pitch as offsets, no trail, RGF_SILENT,
  RGF_ISOFFHAND on the off hand; same pull; one OnPelletEnd per rail: MONSTER/THING if it damaged one, else WALL if
  WorldRailgunFired had a puff, else NONE.
- `virtual void OnPelletEnd(RSLD_Shot s, RSLD_Pellet p, int res, Vector3 at, Actor thing)` with RSLD.RES_NONE 0,
  RES_MONSTER 1, RES_THING 2, RES_WALL 3; `virtual void OnPullEnd(RSLD_Shot s)` (all pellets ended, or 128 tics).
  Hitscan mode: from WorldHitscanFired inside the pellet's own call chain; True Bullets: rounds carry their pellet
  (spawned in pellet order: a FIFO), result at the round's delivery, RES_NONE if it dies without arriving.
- `s.Refund(n)` is legal any time after the pull; `s.Take(n)` (same pool, magazine first, never below 0).
- `bool anyPickup` on RSLD_Effect (set in Init): OnPickup(mo, item, 0) / Owned(p, 0) also for players who own none.
- `virtual bool OnAlerter(RSLD_Shot s, Actor a)`: BD22's Alerter / DistantFireSound* missiles of a pull already under
  way this tic; return true = destroyed.
- RSLD_Amp is moved to the head of the player's inventory chain every tic (HandlePickup sees every pickup).
- Cvars + LD page rows added: rsld_slug_primary (C), rsld_q13 / rsld_q14 + OptionValues RSLD_Q13 / RSLD_Q14 (B).
  BD22 VR has no "Reset All" list: none added.
- NOT done (listed for the coordinator): C's FIRE hook in the guns' .dec fire states for Perfect's jam (G5 territory,
  `A_JumpIf(RSLD_G2.Jammed(self, hand), "<dry fire>")` in ~9 guns + copies).

## 11. v3 changes (09:40)
- FireRail: range <= 0 = PLAYERMISSILERANGE (NEEDS_C 6).
- Kills: OnKill only for bCOUNTKILL monsters or LegenDoom legendaries (BD22's dying-body actors are not kills).
- A strike / missile that damages before its WorldThingSpawned (point blank) starts its pull at that damage.
- Rig probe: `rsld_fx:<Effect>` on a slot where LegenDoom has no LD<Slot>Effect_<Effect> token forces the effect for
  the probe only (logged). Probe helpers: rsld_target (arg 3 = still dummy), rsld_cleartargets, rsld_health:<n>,
  rsld_has:<Class>, rsld_thas:<Class>, rsld_amm:, rsld_count:<Prefix>, rsld_legtarget, rsld_mapstart, rsld_owned,
  rsld_list. Driver: `python3 -I ldl_patch/tools/ldprove.py <batch> [effects]` (ORDER=full|ldfirst, DBG=1|2).
- NEVER write a LegenDoom (or BD22/XMVE) class name as a literal (`"LDX"` assigned to a class<> variable, passed to
  FindInventory/Spawn, `is "LDX"`): it is a script error when LegenDoom is not loaded. Use RSLD.IC/AC/Has/Give.
- ldrig.sh counts real errors only (`[1-9]+ errors`, `FATAL:`, script error, VM abort); BD22/XMVE's own
  "Unknown class name ...Fatality" lines are warnings (they matched "FATAL" case-insensitively before).
- G0 (56) and G9 (5): rig-proven, one log each in ldl_patch/evidence/ldmode/ (rig only, not headset-confirmed).

## 12. v4 (round 2, 2026-11-06 afternoon; one agent)
- A missile starts a pull only if it carries damage and no ancestor class is named like a helper (`Helper()`: BD22's
  RocketGlassBreaker is an Alerter; EmptyBrass, RedFlareSpawn, BackblastFlames*, LiquidExplosionEffectSpawner carry 0).
  A helper's damage is no shot's (Outgoing / WorldThingDamaged skip it).
- A pull's "before" ammo is the snapshot one tic earlier when the hand did not fire the tic before (the rocket launcher
  takes its round a tic before the rocket).
- `RSLD.LDVisual(cls, at, statelabel, skip, owner)`: LegenDoom's own visual actor by name, put straight into a visual
  state (its Spawn/A_Explode never run). `RSLD.AllyCount(p)` / `RSLD.Allies(p, out list)`: BD22's friendly marines
  (Marine_Rifle family) within RSLD.ALLY_RADIUS 1024. `s.TagMissile(m)`: a projectile a pull fires itself (an LD class
  tagged this way is ours, not LegenDoom's effect damage). `s.FireRail(..., color1, color2, duration, sparsity, drift)`.
- LD mode turns LegenDoom's LD_quakes off on every map (no camera quakes).
- Perfect's jam: tokens RSLD_JamMain / RSLD_JamOff, read by the fire states of BrutalPistol, Rifle, MiniGun (and each
  shot of its 3-shot loops), BrutalRevolver, RSQ_Off_BrutalRevolver, RSQ_Off_BrutalPistol, RSQ_Off_Rifle (Purist
  variants inherit). NOT hooked: BD22's DualPistols / DualRifles (their .dec are not in BD22 VR's src).
- NEVER call a method on a string literal (`"a|b".Split(...)`): it crashes the VM on QZD 17.3 (rig, round 2).
- Removed: rsld_q13, rsld_q14 (fixed behaviour), RSLD_Fx_Favoured (never rolls: RSLD_Reroll.IsDropped).

## 13. v5 (round 3, agent R3a, 2026-11-06 evening)
- PASSIVES COUNTER (owner Q9, round 3): `RSLD.Count(mo, eff)` now counts only the slots of the guns IN HAND (main, and
  off hand with rsld_offhand_legendary; a slot once). LegenDoom's every-owned count is `RSLD.CountOwned` (Thematic,
  Upgrading's meter use it). `RSLD.HeldSlot(mo, slot)`. Hoarder's per-slot loop checks HeldSlot. LegenDoom's own
  start-buff script (LD_ApplyStartBuffs: Restoring, Vanguard, Resupplying, Wildfire, Chronostrike, Scrambling) still
  counts owned legendaries (LegenDoom's ACS): open question in R3a's report.
- MISSILE RIDERS (g3_core.zs): an effect that extends `RSLD_G3Fx` gets a rider (`RSLD_Rider`) on each of our
  projectiles of its pulls (Rides(kind): K_ROCKET/K_PLASMA/K_BFG/K_GRENADE). Hooks: RiderSpawn (in the spawn, before
  the muzzle moves it), RiderStart (first tic, at the muzzle), RiderTick(r, bounced), RiderDeath (r.sky: vanished),
  RiderAfter (40 tics after death), RiderBlast (BD22's RocketExplosion / UGBLExplosion of that projectile: by default
  the rider's explDmgMul / explRadMul / explFull / explNoSelf / noExpl are applied through RSLD_Boom), RiderDamage.
  r.dmgMul / r.directAdd change its direct hit. `RSLD_G3.Child(r, at, angle, pitch, speed, dmgMul, scale)` spawns
  one more of OUR projectile class for the pull. `RSLD_G3.SkipSpray(ball)` skips a BFG ball's own ray spray;
  `RSLD_G4.Spray(s, from, rays, dmg, fov, blastDmg, blastRad, flags)` fires BD22's rays (optionally a blast per
  target). `RSLD_G3.BoomAt(s, at, dmg, rad, full, flags, delay, dtype, vis, snd)`: a blast of the pull.
- Handler: a BD22 helper missile that a rider claimed (its blast) is TAGGED and its damage now counts for the pull
  (Outgoing / WorldThingDamaged skip only untagged helpers). WorldThingDied feeds TORGUE's chain.
- ALT-FIRE STAND-DOWN (owner Q12, round 3): tokens `RSLD_AltDown` / `RSLD_AltDownOff` (g6_ammo.zs) while the hand's gun
  carries Seeker (RL), Burst (pistol family), Chargeup (plasma rifle) or Slug (pump shotgun). alts.zs stops giving
  RSA_Opt_RLLock / RSA_Opt_Slug, rlock.zs stops painting, PistolBurstFire is taken. Fire states (R3b) read the tokens
  in the pistol's and plasma rifle's AltFire.
- SOUND OPTION: `rsld_mute_ld_sounds` (server, off) + SNDINFO.rsld + ldsounds.zs: LegenDoom's pickup jingles and
  legendary aura are silenced by name and replayed from LegenDoom's lumps (rsld/ld/*) unless muted. Probes:
  rsld_aura [1 = boss], rsld_auras, rsld_jingle:<effect> <rarity>.
- Numbers: ldl_patch/tools/numbers/g3.rules -> numbers_g3.zs (G3, G4, G6: 256 numbers). Round-3 batched check:
  `python3 -I ldl_patch/tools/ldprove.py round3` (R3b's sections from /home/claude/ldmerge/R3B_SECTIONS.py:
  `SECTIONS = [(name, gun, console body, effect or None), ...]`, helpers fire/shots/tgt/amm/taps available).

## 14. v6 (round 4, one agent, 2026-11-06 late evening): the owner's round-4 answers
- FISTS ON BOTH HANDS: `RSLD_Handler.HandWeapon(mo, hand, strike)`: the off hand's free fist (RSQ_Hands) is BD22's fists
  weapon (Melee_Attacks, slot 0) for the LD mode: WhileHeld runs for it, its punches start pulls of `hand == OFF`,
  `RSLD.Count` / `HeldSlot` count it. `RSLD_Handler.StrikeHand(mo, strike)`: the hand from rsq/fists.zs's punch record
  (`RSQ_Fists.Record(strike, hand, mps)` / `RSQ_Fists.Lookup(strike)`), else the nearest controller. G7's per-player state
  is per hand (index pn * 2 + hand). `RSLD_G7Effect.Fist(s)` is any fist.
- SWING SPEED: after the effect's ModifyDamage, a fist pull's strike damage is x(1 + clamp((m/s - 2) / 5, 0, 1))
  (`RSLD_G7.Swing`, RSQ Melee's rule; set damage too). Only punches with a recorded speed (real arm punches, the rig's
  `netevent rsld_punch:<0|1> <m/s x 100>` test punch).
- STREAMS (ld_g11_stream.zs `RSLD_StreamFx`): Beam (PR BF), Blazing (RL PR BF), Prototype (BF, moved out of g4_bfg.zs).
  While the gun carries one, its own Fire is held off (`RSLD_G5.Block`) and the stream fires every tic the hand's trigger
  is down after LegenDoom's lead, from the drawn muzzle; one pull per press (`s.lastTic` kept current). Damage of every
  LegenDoom actor of the stream x (our projectile's direct / LegenDoom's mean); ammo a tic x (our shot's cost / its).
- DUALWIELD: `RSLD_Fx_DualWield` registers (179 = all but Favoured); the gate is `RSLD_Handler.DualWieldGate` (every 5
  tics): BD22's DualPistols given while the pistol slot's legendary is DualWield, taken otherwise (the single pistol given
  back if none is left). Probe: `netevent rsld_keepdual 1` (rig only) leaves a given DualPistols be.
- G5: SixShooter is an `RSLD_G5Speed` at x0.5. Chargeup on the fists stores punches (`fi_wind` 4, `fi_step` 17, `fi_max` 20)
  while the fist's trigger is held; the next punch of that fist is x the count.
- G7: NorthernStar's closing blow at the stun's end (`RSLD_G7Stun.Blow`: LegenDoom's A_RadiusThrust numbers, monsters only).
- G3: Arcing (gravity x k^2, fuse / k) and Proximity (launch, drift, pull x k), k = our projectile's speed / LegenDoom's
  class's (`RSLD_G3Util.SpeedRatio`, run-time class defaults). `RSLD_Rider.from` = its first-tic position.
- G6: `RSLD_G6.KindAmmo / MaxedBy / KindOfAmmo`: every BD22 reserve of a LegenDoom kind (Upgrading's OnlyKind mapping):
  Transmogrifier takes from any of them, Overflowing's kind is maxed by any of them.
- SOUNDS: MAPINFO.rsld `MenuDelegateClass = "RSLD_MenuDelegate"` (ldsounds.zs): with LegenDoom and rsld_mute_ld_sounds on,
  the engine's menu sounds play QuestZDoom's lumps (rsld/qz/*); LegenDoom's info screen open/close (LDWeaponInfoScreenActive)
  plays LegenDoom's lumps or, muted, QuestZDoom's menu open / back. Not covered: the quit sounds.
- Numbers: ldl_patch/tools/numbers/g11.rules -> numbers_g11.zs (37). Probes: `rsld_target ... 2` (hostile still target:
  RSLD_ProbeHold), `rsld_cleartargets` (also every other monster), `rsld_home <x> <y>`, `rsld_punch:`, `rsld_menusnd`,
  `rsld_keepdual`. The batched check: `python3 -I ldl_patch/tools/ldprove.py round4` (open arena make_ldarena.py, loaded
  last). Registry: "LD mode on: 179 effects registered, 647 numbers".
