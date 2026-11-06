// G0: the 56 LegenDoom effects the old patch carried, rebuilt on the registry and the shot context (Agent A).
// Numbers: RSLD.Num / Num(key) from numbers_g0.zs (ldl_patch/tools/numbers/g0.rules -> LegenDoom's own lines).
// "E" = LegenDoom's own item / number unchanged; "R" = LegenDoom's ratio on our gun's own damage (base = the LD gun's
// plain shot, e.g. the shotgun's 5 per pellet). Sounds: BD22 / BD22 VR names only (scope section 4).

// ---------------------------------------------------------------- shared bases (names not RSLD_Fx_*: not effects)

// x(dmg / base) when Active() (Pristine, Raging, Rampaging, Serious, ProStrat, SteadyShot, Machine, CQC)
class RSLD_DamageRatio : RSLD_Effect
{
	virtual bool Active(RSLD_Shot s) { return true; }
	override void OnPull(RSLD_Shot s) { s.b2 = Active(s); }
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit hit)
	{
		bool on = s.pull > 0 ? s.b2 : Active(s);
		double b = Num("base");
		if (on && b > 0) hit.mult *= Num("dmg") / b;
	}
}

// x3 (x4) against LegenDoom's monster group of the effect: one damage event (Champions' resistances see one hit)
class RSLD_GroupFx : RSLD_Effect
{
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit hit)
	{
		if (hit.target && RSLD.InGroup(hit.target, name)) hit.mult *= Num("mult");
	}
}

// on kill: LegenDoom's own LD<Effect>EffectDeath item, given to the dead monster with the player as its target,
// as LegenDoom's checkers do (LD<Effect>EffectChecker: A_GiveInventory("LD<Effect>EffectDeath", 1, AAPTR_MASTER))
class RSLD_KillReward : RSLD_Effect
{
	override void OnKill(RSLD_Shot s, RSLD_Hit hit)
	{
		let t = hit.target;
		class<Inventory> c = "LD" .. name .. "EffectDeath" .. RSLD_Data.DeathVariant[max(s.slot, 0)];
		if (!c) c = "LD" .. name .. "EffectDeath";
		if (!c || !t) return;
		t.target = s.mo;
		t.GiveInventory(c, 1);
		s.Log(String.Format("kill %s: gave %s", t.GetClassName(), c.GetClassName()));
	}
}

// a free shot: the rounds the pull took go back (owner Q7: to the magazine; 15 + 4 free = 19 before reload)
class RSLD_AmmoFx : RSLD_Effect
{
	virtual bool Free(RSLD_Shot s) { return false; }
	override void OnPull(RSLD_Shot s) { s.b1 = Free(s); }
	override void AfterPull(RSLD_Shot s)
	{
		int taken = s.magTaken > 0 ? s.magTaken : s.resTaken;
		if (s.b1 && taken > 0) { s.Log(String.Format("free shot (%d)", taken)); s.Refund(taken); }
		else if (taken > 0) s.Log(String.Format("paid shot (%d)", taken));
	}
}

// LegenDoom's Ready loops: every Num("every") tics of not firing (Shotgun.dec ReadyReplicating ...)
class RSLD_ReadyBeat : RSLD_Effect
{
	virtual void Beat(RSLD_Held c) {}
	override void WhileHeld(RSLD_Held c)
	{
		int every = int(Num("every"));
		if (every > 0 && !c.attacking && c.idle > 0 && c.idle % every == 0) Beat(c);
	}
}

// debuffs LegenDoom's <Effect>BulletPuff gives the monster it hits (Common/Uncommon/Rare/EpicSpecialEffects.dec)
class RSLD_MonsterDebuff : RSLD_Effect
{
	virtual bool Apply(Actor t, RSLD_Shot s) { return false; }
	override void OnHit(RSLD_Shot s, RSLD_Hit hit)
	{
		let t = hit.target;
		if (!t || hit.killed) return;
		if (!t.target) t.target = s.mo;
		if (Apply(t, s)) s.Log(String.Format("%s on %s", name, t.GetClassName()));
	}
}

// ---------------------------------------------------------------- on kill (E: LegenDoom's own items)
class RSLD_Fx_Artifact : RSLD_KillReward {}
class RSLD_Fx_Bloodthirsty : RSLD_KillReward {}
class RSLD_Fx_Divine : RSLD_KillReward {}
class RSLD_Fx_Endless : RSLD_KillReward {}
class RSLD_Fx_Hopeful : RSLD_KillReward {}
class RSLD_Fx_Infiltrator : RSLD_KillReward {}
class RSLD_Fx_Killstreaker : RSLD_KillReward {}
class RSLD_Fx_Murderous : RSLD_KillReward {}
class RSLD_Fx_Unstoppable : RSLD_KillReward {}
// Battlerage: LegenDoom's LDBattlerageSpeedBoost timer -> the engine's double firing speed (handler Battlerage)
class RSLD_Fx_Battlerage : RSLD_KillReward {}

// Bloody (Chainsaw): owner 2026-11-06 round 2: as LegenDoom's description says, "Every 5 enemies killed with this
// increases damage" (LANGUAGE.effectdesc, Bloody|every): +20% (LegenDoom's step 1 / Bloody|div = 1/5, LEGNDLIB.acs
// LDBloodyCount) for every 5 kills. LegenDoom's own code adds the step on every kill; the kills are still counted in
// LegenDoom's own LDBloodyCounter (its death item, its level reset): damage x (1 + floor(counter / 5) / 5).
class RSLD_Fx_Bloody : RSLD_KillReward
{
	double Mult(PlayerPawn p, out int kills)
	{
		double d = Num("div"), every = Num("every");
		kills = RSLD.Has(p, "LDBloodyCounter");
		if (d <= 0 || every <= 0) return 1.0;
		return 1.0 + int(kills / every) / d;
	}
	override void OnPull(RSLD_Shot s)
	{
		int k;
		double m = Mult(s.mo, k);
		s.Log(String.Format("%d kills counted: damage x%.2f (+%g%% per %d kills)", k, m, 100.0 / Num("div"), int(Num("every"))));
	}
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit hit)
	{
		int k;
		hit.mult *= Mult(s.mo, k);
	}
}

// WarmUp: LegenDoom's LDWarmUpPlayerChecker rule (UncommonSpecialEffects.dec:3019), played with BD22's berserk sound
// instead of LegenDoom's items/berserkpickup: no effect while berserk is full; LDWarmUpCounter fills to its max (4),
// the next kill gives LegenDoom's LDBerserkWarmUpActivation (the 5th kill) and empties it. Once per corpse
// (LegenDoom's LDEffectStackingCooldown on the monster).
class RSLD_Fx_WarmUp : RSLD_Effect
{
	override void OnKill(RSLD_Shot s, RSLD_Hit hit)
	{
		let t = hit.target, p = s.mo;
		if (!t || RSLD.Has(t, "LDEffectStackingCooldown") > 0) return;
		RSLD.Give(t, "LDEffectStackingCooldown");
		let ps = p.FindInventory("PowerStrength", true);
		if (ps && ps.Amount >= ps.MaxAmount) return;
		int n = RSLD.Has(p, "LDWarmUpCounter");
		if (n >= int(Num("kills")))
		{
			p.A_StartSound("BERSPKUP", CHAN_ITEM);
			RSLD.Give(p, "LDBerserkWarmUpActivation");
			p.TakeInventory(RSLD.IC("LDWarmUpCounter"), 999);
			s.Log("5th kill: berserk");
		}
		else { RSLD.Give(p, "LDWarmUpCounter"); s.Log(String.Format("kill %d of %d", n + 1, int(Num("kills")) + 1)); }
	}
}

// Violent: on the kill, LegenDoom's LDViolentEffectChecker (CommonSpecialEffects.dec:282): A_Explode(64, 128, 0) from
// the corpse, LDViolentFearEffect to monsters within 256, LegenDoom's blood blast. Its explosion visual plays
// LegenDoom's rocketlauncher/explode: that one is silenced and BD22's Explode1 plays instead.
class RSLD_Fx_Violent : RSLD_Effect
{
	override void OnKill(RSLD_Shot s, RSLD_Hit hit)
	{
		let t = hit.target;
		if (!t || RSLD.Has(t, "LDEffectStackingCooldown") > 0) return;
		RSLD.Give(t, "LDEffectStackingCooldown");
		let b = RSLD_ViolentBlast(Actor.Spawn("RSLD_ViolentBlast", t.pos + (0, 0, t.height * 0.5)));
		if (!b) return;
		b.target = s.mo;
		b.dmg = int(Num("dmg")); b.rad = int(Num("radius")); b.fear = int(Num("fear"));
		b.corpse = t;
		s.Log(String.Format("kill %s: blast %d r%d, fear r%d", t.GetClassName(), b.dmg, b.rad, b.fear));
	}
}

class RSLD_ViolentBlast : Actor
{
	int dmg, rad, fear;
	Actor corpse;
	Default { +NOINTERACTION; +NOBLOCKMAP; +NOGRAVITY; RenderStyle "None"; }
	override void PostBeginPlay()
	{
		Super.PostBeginPlay();
		A_StartSound("Explode1", CHAN_AUTO);
		A_Explode(dmg, rad, 0);
		class<Inventory> fe = RSLD.IC("LDViolentFearEffect");
		if (fe) A_RadiusGive(fe, fear, RGF_MONSTERS, 1);
		class<Actor> bb = RSLD.AC("LDViolentBloodblast"), vv = RSLD.AC("LDViolentExplosionVisual");
		if (corpse && !corpse.bNOBLOOD && bb) Spawn(bb, pos);	// its misc/gibbed is BD22's sound
		let v = vv ? Spawn(vv, pos) : null;
		if (v) RSLD_Silencer.Watch(v);
		Destroy();
	}
}

// stops a LegenDoom effect actor's own sounds the tic it plays them (its visuals stay)
class RSLD_Silencer : Thinker
{
	Actor a;
	int life, max;
	static void Watch(Actor a, int tics = 3) { let s = new("RSLD_Silencer"); s.a = a; s.max = tics; if (a) a.A_StopAllSounds(); }
	override void Tick()
	{
		if (!a || ++life > max) { Destroy(); return; }
		a.A_StopAllSounds();
	}
}

// ---------------------------------------------------------------- monster debuffs (E: LegenDoom's items)
class RSLD_Fx_Crippling : RSLD_MonsterDebuff
{
	override bool Apply(Actor t, RSLD_Shot s)
	{
		RSLD.Give(t, "LD" .. name .. "Effect");
		if (RSLD.Has(t, "LD" .. name .. "EffectVisualActive") == 0) { RSLD.Give(t, "LD" .. name .. "EffectVisualActive"); RSLD.Give(t, "LD" .. name .. "EffectCheckerSpawner"); }
		return true;
	}
}
class RSLD_Fx_Whittling : RSLD_Fx_Crippling {}

class RSLD_Fx_Freezing : RSLD_MonsterDebuff
{
	override bool Apply(Actor t, RSLD_Shot s)
	{
		if (RSLD.Has(t, "LD" .. name .. "SpeedDebuff") > 0) return false;
		RSLD.Give(t, "LD" .. name .. "Effect"); RSLD.Give(t, "LD" .. name .. "EffectCheckerSpawner");
		return true;
	}
}
class RSLD_Fx_Gravitic : RSLD_Fx_Freezing {}

class RSLD_Fx_Incinerating : RSLD_MonsterDebuff
{
	override bool Apply(Actor t, RSLD_Shot s) { if (t.bNOBLOOD) return false; RSLD.Give(t, "LDIncineratingEffect"); return true; }
	override void OnKill(RSLD_Shot s, RSLD_Hit hit) { if (hit.target && !hit.target.bNOBLOOD) { RSLD.Give(hit.target, "LDIncineratingEffect"); s.Log("corpse " .. hit.target.GetClassName()); } }
}

// Persistent: every pellet hit starts LegenDoom's bleed (EpicSpecialEffects.dec LDPersistentBulletPuff ->
// LDPersistentBleedingEffectDamage): 8 bleeds, one every 35 tics, each Damage (5), painless and thrustless, with its
// LDPersistentBlood visual. The bleeds stack (one per hit). The patch only gave the blood visual: no damage (fixed).
// Cheaper than LegenDoom's: a thinker per bleed instead of a tracking actor plus a missile per tick (scope section 5).
class RSLD_Fx_Persistent : RSLD_MonsterDebuff
{
	override bool Apply(Actor t, RSLD_Shot s)
	{
		RSLD_Bleed.Start(t, s.mo, int(Num("bleeds")), int(Num("every")), int(Num("dmg")));
		RSLD.Give(t, "LDPersistentBlood");
		return true;
	}
}

class RSLD_Bleed : Thinker
{
	Actor t, src;
	int left, timer, every, dmg;

	static void Start(Actor t, Actor src, int n, int every, int dmg)
	{
		let b = new("RSLD_Bleed");
		b.t = t; b.src = src; b.left = n; b.every = max(1, every); b.timer = b.every; b.dmg = dmg;
	}

	override void Tick()
	{
		if (!t || t.health <= 0 || left <= 0) { Destroy(); return; }
		if (t.isFrozen() || --timer > 0) return;
		timer = every;
		left--;
		let h = RSLD.H();
		if (h) h.inDamage = true;
		int was = t.health;
		t.DamageMobj(null, src, dmg, 'None', DMG_THRUSTLESS | DMG_NO_PAIN);
		if (h) h.inDamage = false;
		RSLD.Give(t, "LDPersistentBlood");
		if (RSLD.DebugLevel() > 0 && left % 4 == 0) Console.Printf("RSLD %d Persistent: bleed %s %d -> %d (%d left)", level.maptime, t.GetClassName(), was, t ? t.health : 0, left);
	}
}

class RSLD_Fx_Igniting : RSLD_MonsterDebuff
{
	override bool Apply(Actor t, RSLD_Shot s)
	{
		if (t.bNOBLOOD || RSLD.Has(t, "LDIgnitingActive") > 0) return false;
		RSLD.Give(t, "LDIgnitingPowerGiver");
		return true;
	}
}

// ---------------------------------------------------------------- on hit, for the player
// Vampiric (Fists/Chainsaw): A_CustomPunch lifesteal 0.5, 0.1 while berserk (Fist.dec FireVampiric)
class RSLD_Fx_Vampiric : RSLD_Effect
{
	override void OnHit(RSLD_Shot s, RSLD_Hit hit)
	{
		double f = s.mo.FindInventory("PowerStrength", true) ? Num("stealberserk") : Num("steal");
		int hp = int(hit.damage * f);
		if (hp > 0) { s.mo.GiveBody(hp); s.Log(String.Format("+%d health (%d x %.1f)", hp, hit.damage, f)); }
	}
}

// Scavenging (Fists/Chainsaw): CPF_STEALARMOR with lifesteal 0.5 (0.1 berserk), as LegenDoom's LDScavengingEffect
// armor bonuses (Fist.dec FireScavenging)
class RSLD_Fx_Scavenging : RSLD_Effect
{
	override void OnHit(RSLD_Shot s, RSLD_Hit hit)
	{
		double f = s.mo.FindInventory("PowerStrength", true) ? Num("stealberserk") : Num("steal");
		int n = min(int(hit.damage * f), 100);
		class<Inventory> sc = RSLD.IC("LDScavengingEffect");
		for (int i = 0; sc && i < n; i++) s.mo.GiveInventory(sc, 1);
		if (n > 0) s.Log(String.Format("+%d armor", n));
	}
}

// Sadistic: a hit that does not kill gives a health bonus (LDSadisticBulletPuff)
class RSLD_Fx_Sadistic : RSLD_Effect
{
	override void OnHit(RSLD_Shot s, RSLD_Hit hit) { if (!hit.killed) { RSLD.Give(s.mo, "LDHealthBonus"); s.Log("health bonus"); } }
}

// Painful: "Attacks always flinch enemies" (its puff is +FORCEPAIN)
class RSLD_Fx_Painful : RSLD_Effect
{
	override void OnHit(RSLD_Shot s, RSLD_Hit hit)
	{
		if (!hit.killed && hit.target) { hit.target.TriggerPainChance(hit.damageType, true); s.Log("flinch " .. hit.target.GetClassName()); }
	}
}

// Thieving (Fists/Chainsaw): LegenDoom's LDThievingEffect (UncommonSpecialEffects.dec:1887): 192/256, then
// LDThievingCooldown, then down the chain Clip (96/256 skips it) -> Shell (64) -> Rocket (128) -> Cell, a type that is
// full is skipped. Each LegenDoom ammo type is the BD22 item that replaces it (tables.zs Repl: Clip2, AmmoShell,
// AmmoRocket, AmmoCell), one pickup's worth, with that item's own pickup sound.
class RSLD_Fx_Thieving : RSLD_Effect
{
	static const string LDAmmo[] = { "Clip", "Shell", "RocketAmmo", "Cell" };
	static const string Skip[] = { "skipclip", "skipshell", "skiprocket", "" };

	class<Inventory> BD22For(string ld)
	{
		for (int i = 0; i < RSLD_Tables.Repl.Size(); i++)
		{
			Array<string> f; RSLD_Tables.Repl[i].Split(f, "|");
			if (f[0] ~== ld) { class<Inventory> c = f[3]; return c; }
		}
		return null;
	}

	override void OnHit(RSLD_Shot s, RSLD_Hit hit)
	{
		let p = s.mo;
		if (RSLD.Has(p, "LDThievingCooldown") > 0) return;
		if (random(0, 255) >= Num("chance")) return;
		RSLD.Give(p, "LDThievingCooldown");
		for (int i = 0; i < 4; i++)
		{
			let c = BD22For(LDAmmo[i]);
			if (!c) continue;
			let have = p.FindInventory(c);
			let d = GetDefaultByType(c);
			if (have && have.Amount >= have.MaxAmount) continue;	// A_JumpIfInventory(<ammo>, 0, ...): full
			if (Skip[i] != "" && random(0, 255) < Num(Skip[i])) continue;
			int amt = max(1, d.Amount);
			if (have) RSLD.AddAmmo(have, amt); else p.GiveInventory(c, amt);
			p.A_StartSound(d.PickupSound, CHAN_ITEM);
			s.Log(String.Format("+%d %s (LegenDoom %s)", amt, c.GetClassName(), LDAmmo[i]));
			return;
		}
	}
}

// ---------------------------------------------------------------- damage x (R: LegenDoom's ratio on our damage)
// Pristine: A_JumpIfHealthLower(100) -> 10 instead of 5 (Shotgun.dec FirePristine / PristineStronk)
class RSLD_Fx_Pristine : RSLD_DamageRatio { override bool Active(RSLD_Shot s) { return s.mo.health >= Num("hp"); } }
// Raging: PowerStrength -> 15 instead of 5 (FireRagingActive)
class RSLD_Fx_Raging : RSLD_DamageRatio { override bool Active(RSLD_Shot s) { return s.mo.FindInventory("PowerStrength", true) != null; } }
// Rampaging / Serious / ProStrat: LegenDoom's LDForwards / LDBackwards / LDStrafe tokens are set from BT_FORWARD etc.
// (LEGENDPLY.acs:232-249), which VR's thumbstick never presses; the stick's own forward/side move is read here too
class RSLD_Fx_Rampaging : RSLD_DamageRatio { override bool Active(RSLD_Shot s) { return s.mo.player.cmd.forwardmove > 0 || RSLD.Has(s.mo, "LDForwards") > 0; } }
class RSLD_Fx_Serious : RSLD_DamageRatio { override bool Active(RSLD_Shot s) { return s.mo.player.cmd.forwardmove < 0 || RSLD.Has(s.mo, "LDBackwards") > 0; } }
class RSLD_Fx_ProStrat : RSLD_DamageRatio
{
	override bool Active(RSLD_Shot s) { return s.mo.player.cmd.sidemove != 0 || RSLD.Has(s.mo, "LDStrafeLeft") > 0 || RSLD.Has(s.mo, "LDStrafeRight") > 0; }
}

// SteadyShot (Pistol): view height <= 30 (LEGNDLIB.acs LDSteadyShotCrouchCheck) -> 15 instead of 5 AND spread 0
// (Pistol.dec FireSteadyShot: A_FireBullets(0, 0, 1, 15...))
class RSLD_Fx_SteadyShot : RSLD_DamageRatio
{
	override bool Active(RSLD_Shot s)
	{
		let pl = s.mo.player;
		return pl.viewheight <= Num("viewheight") || pl.crouchfactor < 1.0 || (pl.cmd.buttons & BT_CROUCH);
	}
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (s.b2) { p.spreadMul = 0; s.Log("crouched: spread 0"); }
		return false;
	}
}

// CQC: spread 16.8 instead of 5.6 (x3) and 15 instead of 5 (x3) (Shotgun.dec FireCQC vs NormalFire)
class RSLD_Fx_CQC : RSLD_DamageRatio
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		double b = Num("spreadbase");
		if (b > 0) p.spreadMul = Num("spread") / b;
		return false;
	}
}

// Machine (Pistol): 10 instead of 5 (x2), and "fires extremely rapidly": LegenDoom's machine pistol fires every 2 tics
// (FireMachineAttack: MACP B 1, C 1, A_Refire): 35 / 2 = 17.5 shots a second. Owner 2026-11-06 round 2: LegenDoom's own
// 17.5 a second on our gun: while the trigger is held, the gun's Fire state is re-entered every Machine|shottics (2)
// tics (owner Q6: the trigger cycle gets faster, the gun's own shot counter decides). Fire does its own magazine and
// reload checks, so an empty magazine stops it and the hand reload is unchanged. The gun's own first gap is still
// measured (logged) before the fast cycle starts, as the first shot of a hold is the gun's own.
class RSLD_Fx_Machine : RSLD_DamageRatio
{
	int gap[MAXPLAYERS * 2], first[MAXPLAYERS * 2], second[MAXPLAYERS * 2];
	Weapon gw[MAXPLAYERS * 2];

	override void OnPull(RSLD_Shot s)
	{
		Super.OnPull(s);
		int k = s.pn * 2 + s.hand;
		if (gw[k] != s.weapon) { gw[k] = s.weapon; gap[k] = 0; first[k] = 0; }
		if (gap[k] == 0)
		{
			if (first[k] == 0 || s.tic - first[k] > 35) first[k] = s.tic;
			else { gap[k] = s.tic - first[k]; s.Log(String.Format("the gun's own gap: %d tics", gap[k])); }
		}
	}

	override void WhileHeld(RSLD_Held c)
	{
		int k = c.pn * 2 + c.hand;
		if (!c.attacking || gap[k] <= 0 || gw[k] != c.weapon) return;
		int every = max(1, int(Num("shottics")));	// LegenDoom's own cycle: 2 tics = 17.5 shots a second
		int last = h.LastPull(c.pn, c.hand);
		if (level.maptime - last < every) return;
		let w = c.weapon;
		let pl = c.mo.player;
		if (RSLD.Has(c.mo, "Reloading") > 0) return;
		int mag = RSLD_Handler.MagOf(w), res = RSLD_Handler.ResOf(w);
		if (mag <= 0 && (w.Ammo2 && w.Ammo2 != w.Ammo1)) return;	// the magazine is empty: the hand reloads
		if (mag <= 0 && res <= 0) return;
		State f = w.FindState("Fire");
		if (!f) return;
		pl.SetPsprite(c.hand == RSLD.OFF ? PSP_OFFHANDWEAPON : PSP_WEAPON, f);
		if (RSLD.Debug()) Console.Printf("RSLD %d Machine: refire %s every %d tics = %.1f a second (its own gap %d)", level.maptime, w.GetClassName(), every, 35.0 / every, gap[k]);
	}
}

// Lucky: ONE roll per trigger pull, A_Jump(58/256) to a 75 NORANDOM shot: 5x the max of 5*random(1,3) (FireLucky).
// Our guns' damage is fixed (FBF_NORANDOM), so their max is their damage: x5. Sound: BD22's Plasma/BeepBeep.
class RSLD_Fx_Lucky : RSLD_Effect
{
	override void OnPull(RSLD_Shot s)
	{
		s.b1 = random(0, 255) < Num("chance");
		if (s.b1) { s.Sound("Plasma/BeepBeep"); s.Log("lucky pull: x5"); }
		else s.Log("plain pull");
	}
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit hit)
	{
		double b = Num("base") * 3;
		if (s.b1 && b > 0) hit.mult *= Num("dmg") / b;
	}
}

// Berserker: 5 at 100+ health, +1 per 10 below, to 15 (Shotgun.dec FireBerserker's A_JumpIfHealthLower chain)
class RSLD_Fx_Berserker : RSLD_Effect
{
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit hit)
	{
		double base = Num("base"), top = Num("top"), hp1 = Num("hp1"), step = Num("hp1") - Num("hp2");
		if (base <= 0 || step <= 0) return;
		int steps = clamp(int(ceil((hp1 - s.mo.health) / step)), 0, int(top - base));
		hit.mult *= (base + steps) / base;
	}
}

// AntiTree: LegenDoom's LDTreesDamageDisplay holds its tree damage percent (LEGENDWRD.acs:17)
class RSLD_Fx_AntiTree : RSLD_Effect
{
	override void OnPull(RSLD_Shot s) { s.Log(String.Format("LegenDoom's tree damage on this map: %d%%", RSLD.Has(s.mo, "LDTreesDamageDisplay"))); }
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit hit)
	{
		int pc = RSLD.Has(s.mo, "LDTreesDamageDisplay");
		if (pc > 0) hit.mult *= pc / 100.0;
	}
}

// Annoying: "only does 1 damage" (FireAnnoying: 1 NORANDOM), its puff +FORCEPAIN flinches, and no ammo is used
class RSLD_Fx_Annoying : RSLD_AmmoFx
{
	override bool Free(RSLD_Shot s) { return true; }
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit hit) { hit.setDamage = int(Num("dmg")); }
	override void OnHit(RSLD_Shot s, RSLD_Hit hit)
	{
		if (!hit.killed && hit.target) { hit.target.TriggerPainChance(hit.damageType, true); s.Log("flinch " .. hit.target.GetClassName()); }
	}
}

// Patient: every 35 idle tics +1 LDPatientCounter (to 50) with BD22's Plasma/Beep; the shot does x(counter + 10) / 10
// and empties it (Shotgun.dec ReadyPatient / FirePatient, LEGNDLIB.acs LDPatientCount). One value per pull, so a
// True Bullets round arriving later still carries it.
class RSLD_Fx_Patient : RSLD_ReadyBeat
{
	override void Beat(RSLD_Held c)
	{
		if (c.hand != RSLD.MAIN) return;
		if (RSLD.Has(c.mo, "LDPatientCounter") >= Num("max")) return;
		RSLD.Give(c.mo, "LDPatientCounter");
		c.mo.A_StartSound("Plasma/Beep", CHAN_AUTO, CHANF_OVERLAP);
		Log(String.Format("counter %d", RSLD.Has(c.mo, "LDPatientCounter")));
	}
	override void OnPull(RSLD_Shot s)
	{
		double d = Num("div");
		int n = RSLD.Has(s.mo, "LDPatientCounter");
		s.d1 = d > 0 ? (n + d) / d : 1;
		if (n > 0) { s.mo.TakeInventory(RSLD.IC("LDPatientCounter"), 999); s.Log(String.Format("counter %d: x%.1f", n, s.d1)); }
	}
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit hit) { if (s.pull > 0 && s.d1 > 0) hit.mult *= s.d1; }
}

// ---------------------------------------------------------------- monster groups (x3, DemonSlayer x4 on legendaries)
class RSLD_Fx_Exorcist : RSLD_GroupFx {}
class RSLD_Fx_Extinguishing : RSLD_GroupFx {}
class RSLD_Fx_Wrangler : RSLD_GroupFx {}
class RSLD_Fx_Antiair : RSLD_GroupFx {}
class RSLD_Fx_Scrapper : RSLD_GroupFx {}
class RSLD_Fx_Blessed : RSLD_GroupFx {}
class RSLD_Fx_Heroic : RSLD_GroupFx {}
class RSLD_Fx_DemonSlayer : RSLD_GroupFx {}

// ---------------------------------------------------------------- ammo (owner Q7: the magazine)
class RSLD_Fx_Unlikely : RSLD_AmmoFx { override bool Free(RSLD_Shot s) { return random(0, 255) < Num("chance"); } }
class RSLD_Fx_Improbable : RSLD_AmmoFx { override bool Free(RSLD_Shot s) { return random(0, 255) < Num("chance"); } }

// Impossible: 128/256 the shot uses no ammo AND gives one (LD_<Ammo>Single, Shotgun.dec FireImpossible): the free
// round goes back to the magazine, the generated one into the magazine if it has room, else the reserve
class RSLD_Fx_Impossible : RSLD_AmmoFx
{
	override bool Free(RSLD_Shot s) { return random(0, 255) < Num("chance"); }
	override void AfterPull(RSLD_Shot s)
	{
		Super.AfterPull(s);
		if (!s.b1 || !s.weapon) return;
		int g = int(Num("gen"));
		let w = s.weapon;
		Inventory mag = (w.Ammo2 && w.Ammo2 != w.Ammo1) ? w.Ammo2 : null;
		if (mag && mag.Amount + g <= mag.MaxAmount) RSLD.AddAmmo(mag, g);
		else RSLD.AddAmmo(w.Ammo1, g);
		s.Log(String.Format("+%d generated", g));
	}
}

// Efficient (SSG, BFG): LegenDoom's SSG takes 1 shell instead of its AmmoUse 2 (SuperShotgun.dec FireEfficient): every
// pull gives back (use - take) / use of what it took, the remainder carried to the next pull
class RSLD_Fx_Efficient : RSLD_Effect
{
	int carry[MAXPLAYERS * 2];
	override void AfterPull(RSLD_Shot s)
	{
		int taken = s.magTaken > 0 ? s.magTaken : s.resTaken;
		double use = Num("use"), take = Num("take");
		if (taken <= 0 || use <= 0) return;
		int k = s.pn * 2 + s.hand;
		carry[k] += int(taken * (use - take));
		int back = carry[k] / int(use);
		carry[k] -= back * int(use);
		if (back > 0) { s.Log(String.Format("half ammo: %d of %d back", back, taken)); s.Refund(back); }
	}
}

// ---------------------------------------------------------------- while held
// Replicating: +1 reserve every 35 idle tics (LegenDoom gives one LD_<Ammo>Single, Shotgun.dec ReadyReplicating)
class RSLD_Fx_Replicating : RSLD_ReadyBeat
{
	override void Beat(RSLD_Held c)
	{
		if (!c.weapon.Ammo1) return;
		RSLD.AddAmmo(c.weapon.Ammo1, int(Num("amount")));
		Log(String.Format("+%d %s", int(Num("amount")), c.weapon.Ammo1.GetClassName()));
	}
}

// Regenerating: LegenDoom's LDHealthBonus every 35 idle tics (ReadyRegenerating)
class RSLD_Fx_Regenerating : RSLD_ReadyBeat
{
	override void Beat(RSLD_Held c) { RSLD.Give(c.mo, "LDHealthBonus"); Log(String.Format("health bonus, %d", c.mo.health)); }
}

// Sensing: every 35 idle tics LegenDoom's LDSensingEffect to everything within 1024 (map markers), BD22's
// Plasma/BeepQuiet instead of LegenDoom's effects/sensing (ReadySensing)
class RSLD_Fx_Sensing : RSLD_ReadyBeat
{
	override void Beat(RSLD_Held c)
	{
		c.mo.A_StartSound("Plasma/BeepQuiet", CHAN_AUTO, CHANF_OVERLAP);
		class<Inventory> se = RSLD.IC("LDSensingEffect");
		if (se) c.mo.A_RadiusGive(se, Num("radius"), RGF_MONSTERS | RGF_OBJECTS | RGF_ITEMS | RGF_NOSIGHT, 1);
		Log("pulse");
	}
}

// Determined: while not attacking, LegenDoom's LDDeterminedResistance (50%) with its cooldown (Shotgun.dec Ready /
// ReadyDetermined); firing takes it away (AmmoCheckDone: A_TakeInventory("LDDeterminedResistance"))
class RSLD_Fx_Determined : RSLD_Effect
{
	override void WhileHeld(RSLD_Held c)
	{
		if (c.attacking || RSLD.Has(c.mo, "LDDeterminedResistanceCooldown") > 0) return;
		RSLD.Give(c.mo, "LDDeterminedResistance"); RSLD.Give(c.mo, "LDDeterminedResistanceCooldown");
		if (RSLD.DebugLevel() > 1) Log("resistance");
	}
	override void OnPull(RSLD_Shot s)
	{
		if (RSLD.Has(s.mo, "LDDeterminedResistance") > 0) { s.mo.TakeInventory(RSLD.IC("LDDeterminedResistance"), 1); s.Log("resistance taken (fired)"); }
	}
}

// Desperate: firing below 26 health without the cooldown gives LegenDoom's LDDesperateInvulnerabilityChecker
class RSLD_Fx_Desperate : RSLD_Effect
{
	override void OnPull(RSLD_Shot s)
	{
		if (s.mo.health < Num("hp") && RSLD.Has(s.mo, "LDDesperateInvulnerabilityCooldown") == 0)
		{
			RSLD.Give(s.mo, "LDDesperateInvulnerabilityChecker");
			s.Log(String.Format("health %d: invulnerability", s.mo.health));
		}
	}
}

// ---------------------------------------------------------------- map start
// Resupplying: LegenDoom's LD_ApplyStartBuffs fills its own vanilla ammo; every BD22 gun's reserve is filled here
class RSLD_Fx_Resupplying : RSLD_Effect
{
	override void OnMapStart(PlayerPawn p, int copies)
	{
		int n = 0;
		for (let i = p.Inv; i; i = i.Inv)
		{
			let w = Weapon(i);
			if (w && w.Ammo1 && w.Ammo1.Amount < w.Ammo1.MaxAmount) { w.Ammo1.Amount = w.Ammo1.MaxAmount; n++; }
		}
		Log(String.Format("filled %d BD22 reserves", n));
	}
}
