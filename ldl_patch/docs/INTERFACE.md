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
