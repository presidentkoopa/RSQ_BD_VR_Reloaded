// ld_g7_fx.zs -- G7 (R3b, round 3, 2026-11-06): LegenDoom 3.0's melee effects on BD22 VR's real VR punches and BD22's
// chainsaw. Numbers: numbers_g7.zs (ldl_patch/tools/numbers/g7.rules, each with its LegenDoom file:line).
//
// The fists. A real punch (rsq/fists.zs RSQ_FistHand: a fast, forward blow of the controller) lands BD22's own strike
// (MeleeStrikeNormal, MeleeStrike1Berserked with berserk) from the hand; the foundation hands it to the main fist's
// effect (OnMelee) and its damage to ModifyDamage / OnHit. Only the MAIN fist (Melee_Attacks) is LegenDoom's Fists
// slot: the free off hand (RSQ_Hands) punches as BD22 VR's, without the legendary (owner question in R3B_DONE.md).
// Owner, round 3 (Q11): NO pushes on the player (Lunging's launch, Facekicking's jump kick velocity, Hunting's recoil
// push): their damage parts are kept. "Charge" and "hold" with real arms, from RSQ Melee's ideas, built HERE (RSQ Melee
// need not be loaded): RSQ Melee's Star Punch reads "a punch thrown with that hand's trigger squeezed" (gloves.zs
// STAR PUNCH); BD22 VR's own No Trigger Punch leaves the fists' trigger free in VR. So the fist hand's TRIGGER HELD is
// LegenDoom's "fire held": OnePunch charges while it is held and the next real punch thrown with it still held is the
// One Punch; Blaster fires its plasma balls while it is held. Not taken (owner's call, R3B_DONE.md): RSQ Melee's punch
// kinds (jab / hook / uppercut) and its swing-speed damage (10 at 2 m/s to 20 at 7 m/s): LegenDoom's numbers are fixed.
// The chainsaw: its A_Saw / A_CustomPunch hitscans come as pellets of a melee pull (s.melee, slot 1).
// Silent effects (owner: voice / scream effects mechanics only): Imaginary, NorthernStar.

class RSLD_G7Effect : RSLD_Effect
{
	int hold[MAXPLAYERS];		// tics the main fist's trigger has been down
	int tic1[MAXPLAYERS], tic2[MAXPLAYERS];
	bool f1[MAXPLAYERS], f2[MAXPLAYERS];

	static bool Fist(RSLD_Shot s) { return s && s.melee && s.slot == 0 && s.hand == RSLD.MAIN; }
	static bool Saw(RSLD_Shot s) { return s && s.melee && s.slot == 1; }
	static bool Berserk(Actor mo) { return mo && mo.FindInventory("PowerStrength", true) != null; }
	static bool StrikeHit(RSLD_Hit h) { return h && h.inflictor && RSLD_Handler.IsStrike(h.inflictor); }

	// the fist's reach: BD22 VR's strike flies REACH a tic for its life (fists.zs); LegenDoom's ratio of ranges on it
	static void Reach(Actor strike, double ratio)
	{
		if (strike && ratio > 0) strike.vel *= ratio;
	}

	// a test punch for the rig probe (no controller swing on the rig): BD22's own strike from the main hand along the
	// aim, the way fists.zs throws a real one
	static Actor ProbePunch(PlayerPawn mo)
	{
		if (!mo) return null;
		Name sn = Berserk(mo) ? 'MeleeStrike1Berserked' : 'MeleeStrikeNormal';
		class<Actor> sc = RSLD.AC(sn);
		if (!sc) return null;
		Vector3 at = RSVR_VRHand.InVR(mo) ? RSVR_VRHand.HandPos(mo) : mo.pos + (0, 0, mo.Height * 0.6);
		let a = Actor.Spawn(sc, at, ALLOW_REPLACE);
		if (!a) return null;
		a.target = mo;
		a.angle = mo.angle;
		a.pitch = mo.pitch;
		a.Vel3DFromAngle(16, a.angle, a.pitch);
		mo.A_StartSound("Melee/Swing", CHAN_AUTO, CHANF_OVERLAP);
		RSLD.Log(String.Format("G7 probe: a test punch (%s) from the main hand", sn));
		return a;
	}

	override void OnProbe(RSLD_Shot s)
	{
		if (s && s.mo && s.slot == 0) ProbePunch(s.mo);
	}

	// the main fist's trigger, every tic the fists are in the main hand
	void Trigger(RSLD_Held c)
	{
		if (c.hand != RSLD.MAIN || c.slot != 0) return;
		if (RSLD_G5.Pressed(c.mo, RSLD.MAIN)) hold[c.pn]++;
		else hold[c.pn] = 0;
	}
}

// the chainsaw's "doesn't move the player" (RazorEdge; Extended's and Imaginary's SF_NOPULLIN | SF_NOTURN): token read
// by our Saw.dec's A_Saw / A_CustomPunch flags; renewed every tic the saw is held (it runs out by itself: RSLD_G5Token)
class RSLD_G7NoTurn : RSLD_G5Token {}

class RSLD_G7 play
{
	static void NoTurn(RSLD_Held c)
	{
		if (!c || c.slot != 1 || !c.mo) return;
		let it = RSLD_G5Token(c.mo.FindInventory("RSLD_G7NoTurn"));
		if (!it) { c.mo.GiveInventory("RSLD_G7NoTurn", 1); it = RSLD_G5Token(c.mo.FindInventory("RSLD_G7NoTurn")); }
		if (it) { it.Amount = 1; it.refreshed = level.maptime; }
	}

	// BD22's own strike damage of a class (brutal22test6 Melee.dec: MeleeStrikeNormal 10, MeleeStrike1Berserked 60),
	// read from the class itself at run time (a dummy that never ticks)
	static int StrikeDamage(string cls)
	{
		class<Actor> c = RSLD.AC(cls);
		if (!c) return 0;
		let a = Actor.Spawn(c, (0, 0, 0), NO_REPLACE);
		if (!a) return 0;
		int d = a.GetMissileDamage(0, 1);
		a.Destroy();
		return d;
	}
}

// ---- ColdBlooded (C: Fi), "Damage starts off at Berserk levels, Berserk reduces it": LegenDoom's FireColdBlooded punches
// 20 x random(1,10) without berserk (its berserk level) and 2 x with it (its normal level). Ours (scope "R"): BD22's own
// two fist strikes: without berserk the punch does what BD22's berserk punch does (x60/10), with berserk what its
// normal punch does (x10/60).
class RSLD_Fx_ColdBlooded : RSLD_G7Effect
{
	int dn, db;

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (!Fist(s) || !StrikeHit(h)) return;
		if (dn <= 0) { dn = RSLD_G7.StrikeDamage("MeleeStrikeNormal"); db = RSLD_G7.StrikeDamage("MeleeStrike1Berserked"); }
		if (dn <= 0 || db <= 0) return;
		bool b = Berserk(s.mo);
		h.mult *= b ? double(dn) / db : double(db) / dn;
		s.Log(String.Format("cold-blooded: %s: BD22's %s punch level (x%.2f)", b ? "berserk lowers it" : "no berserk", b ? "normal" : "berserk", b ? double(dn) / db : double(db) / dn));
	}
}

// ---- Extended (R: Fi Cs), "Has longer range": LegenDoom's fist reaches 256 where it reaches 64 (x4), its chainsaw 256
// where 65, both without turning or pulling the player. Ours: the strike reaches 4x as far; the saw's hitscan range
// x256/65 and our saw never turns or pulls you while it carries Extended (Saw.dec reads RSLD_G7NoTurn).
class RSLD_Fx_Extended : RSLD_G7Effect
{
	override void WhileHeld(RSLD_Held c) { RSLD_G7.NoTurn(c); }

	override void OnMelee(RSLD_Shot s, Actor strike)
	{
		if (!Fist(s)) return;
		double r = Num("fi_range") / max(1, RSLD.Num("Base", "fi_range"));
		Reach(strike, r);
		s.Log(String.Format("extended: the punch reaches x%.2f", r));
	}

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (!Saw(s)) return false;
		double r = Num("cs_range") / max(1, RSLD.Num("Base", "cs_range"));
		p.range *= r;
		if (p.index == 0) s.Log(String.Format("extended: saw range %.0f (x%.2f), no turn / pull", p.range, r));
		return false;
	}
}

// ---- RazorEdge (C: Fi Cs), "Doesn't move the player when attacking enemies": LegenDoom's CPF_NOTURN / SF_NOPULLIN |
// SF_NOTURN. Ours: the VR fists never turn or pull the player already (fists.zs); the chainsaw stops turning and pulling
// you while it carries RazorEdge (Saw.dec reads RSLD_G7NoTurn).
class RSLD_Fx_RazorEdge : RSLD_G7Effect
{
	override void WhileHeld(RSLD_Held c) { RSLD_G7.NoTurn(c); }
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (Saw(s) && p.index == 0) s.Log("razor edge: the saw neither turns nor pulls you (SF_NOTURN | SF_NOPULLIN)");
		return false;
	}
	override void OnMelee(RSLD_Shot s, Actor strike)
	{
		if (Fist(s)) s.Log("razor edge: the VR punch never turns or moves you (as LegenDoom's CPF_NOTURN)");
	}
}

// ---- Lunging (U: Fi), "Launches you fist extended in the direction you are looking": owner round 3: NO launch. Its
// damage part: the lunge's punch 4 x random(1,10) where the fist does 2 x (x2), reaching 96 where 64 (x1.5).
class RSLD_Fx_Lunging : RSLD_G7Effect
{
	override void OnMelee(RSLD_Shot s, Actor strike)
	{
		if (!Fist(s)) return;
		Reach(strike, Num("range") / max(1, RSLD.Num("Base", "fi_range")));
		s.Log(String.Format("lunging (no launch: owner): punch x%.1f, reach x%.2f", Num("dmg") / max(1, RSLD.Num("Base", "fi_dmg")), Num("range") / max(1, RSLD.Num("Base", "fi_range"))));
	}
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (Fist(s) && StrikeHit(h)) h.mult *= Num("dmg") / max(1, RSLD.Num("Base", "fi_dmg"));
	}
}

// ---- Facekicking (E: Fi), "Kicks enemies, can do jump kicks in midair": LegenDoom's kick does 20 (berserk 200) at 120
// and leaves its LDFacekickingReflector 32 ahead (bounces shots back); in the air, if its LDFacekickingCooldown (40 tics)
// is not running, the jump kick does 40 (400) at 100 and starts the cooldown. Owner round 3: NO jump-kick launch.
// Ours: every real punch is that kick (LegenDoom's damage, E), reaching LegenDoom's ratio of its range; off the ground
// it is the jump kick. The reflector is LegenDoom's own actor; its pain sound (LegenDoom's fists/hitwall) is off.
class RSLD_Fx_Facekicking : RSLD_G7Effect
{
	override void OnMelee(RSLD_Shot s, Actor strike)
	{
		if (!Fist(s) || !s.mo || !strike) return;
		bool air = s.mo.pos.z > s.mo.floorz + 1 && !s.mo.bONMOBJ;
		bool cool = RSLD.Has(s.mo, "LDFacekickingCooldown") > 0;
		bool b = Berserk(s.mo);
		bool jump = air && !cool;
		s.i1 = int(jump ? Num(b ? "jump_bers" : "jump") : Num(b ? "kick_bers" : "kick"));
		Reach(strike, Num(jump ? "jump_range" : "kick_range") / max(1, RSLD.Num("Base", "fi_range")));
		if (jump) RSLD.Give(s.mo, "LDFacekickingCooldown");
		class<Actor> rc = RSLD.AC("LDFacekickingReflector");
		if (rc)
		{
			Vector3 dir = strike.vel.Length() > 0 ? strike.vel.Unit() : (cos(s.mo.angle), sin(s.mo.angle), 0);
			let r = Actor.Spawn(rc, strike.pos + dir * Num("ahead"), NO_REPLACE);
			if (r) { r.PainChance = 0; r.target = s.mo; }
		}
		s.Log(String.Format("facekicking: %s, %d damage (LegenDoom's), reflector ahead", jump ? "jump kick (cooldown on)" : "kick", s.i1));
	}
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (Fist(s) && StrikeHit(h) && s.i1 > 0) h.setDamage = s.i1;
	}
}

// ---- OnePunch (E: Fi), "Attack has a huge cooldown, unleashes a line of destruction": LegenDoom: fire held 4 tics
// charges; let go: a punch of 10000 at 96 and its LDOnePunchProjectile (speed 80, ripping 50 x random(1,8), every tic
// an explosion of 32 x its scale over 200 while its scale grows 0.04 from 0.6; on impact x1.5 and over 256), then
// LDOnePunchCooldown (60 s); in the cooldown it punches normally. Ours (RSQ Melee's Star Punch seam: the hand's trigger
// squeezed through a real punch): hold the fist's trigger 4 tics to charge (Plasma/Charge), then throw a real punch
// with it still held: that punch is the One Punch (10000) and the line flies from the fist along the blow. The line is
// built here with LegenDoom's numbers and LegenDoom's own visuals (shockwave, ground smoke); its sounds are ours (scope
// 4: Kick/Swing, BFG/Explosion), never LegenDoom's. LegenDoom's own cooldown powerup is given.
class RSLD_G7OnePunchLine : FastProjectile
{
	double grow, rad, dist, dscale, ddist, high;
	Default
	{
		Radius 6; Height 4; Speed 80; Damage 50;
		Projectile;
		+THRUSPECIES +RIPPER +BLOODLESSIMPACT +FORCERADIUSDMG +FORCEPAIN
		Species "Player";
		RenderStyle "None";
	}
	States
	{
	Spawn:
		TNT1 A 1 Fly();
		Loop;
	Death:
		TNT1 A 1 Boom();
		Stop;
	}
	void Visual(string cls, double vx, double ang)
	{
		class<Actor> c = RSLD.AC(cls);
		if (!c) return;
		let v = Spawn(c, pos, NO_REPLACE);
		if (!v) return;
		v.target = target;
		v.Scale = Scale;
		v.angle = angle + ang;
		v.VelFromAngle(vx, v.angle);
	}
	void Fly()
	{
		Visual("LDOnePunchShockwave", 0, 0);
		if (pos.z <= floorz + high) { Visual("LDOnePunchGroundSmoke", -10, 90); Visual("LDOnePunchGroundSmoke", -10, -90); }
		A_Explode(int(rad * Scale.X), int(dist), 0);
		Scale += (grow, grow);
	}
	void Boom()
	{
		Scale *= dscale;
		A_Explode(int(rad * Scale.X), int(ddist), 0);
		A_StartSound("BFG/Explosion", CHAN_AUTO);
		Visual("LDOnePunchShockwave", 0, 0);
		for (int a = 0; a < 360; a += 15) Visual("LDOnePunchGroundSmoke", 20, a);
	}
}

class RSLD_Fx_OnePunch : RSLD_G7Effect
{
	override void WhileHeld(RSLD_Held c)
	{
		Trigger(c);
		int pn = c.pn;
		bool cool = RSLD.Has(c.mo, "LDOnePunchCooldown") > 0;
		bool charged = !cool && hold[pn] >= Num("charge");
		if (charged && !f1[pn]) { c.mo.A_StartSound("Plasma/Charge", CHAN_AUTO, CHANF_OVERLAP); RSLD.Log(String.Format("OnePunch: charged (%d tics held): throw a punch with the trigger held", hold[pn])); }
		f1[pn] = charged;
		if (f2[pn] && level.maptime >= tic2[pn]) { f2[pn] = false; ProbePunch(c.mo); }	// the rig probe's punch
	}

	override void OnProbe(RSLD_Shot s)
	{
		if (!s || !s.mo) return;
		f2[s.pn] = true;		// the test punch comes 10 tics later: hold +attack over it to charge
		tic2[s.pn] = level.maptime + 10;
	}

	override void OnMelee(RSLD_Shot s, Actor strike)
	{
		if (!Fist(s) || !strike) return;
		if (!f1[s.pn] || !RSLD_G5.Pressed(s.mo, RSLD.MAIN))
		{
			if (RSLD.Has(s.mo, "LDOnePunchCooldown") > 0) s.Log("one punch: cooling down (LegenDoom's LDOnePunchCooldown): a normal punch");
			return;
		}
		s.b1 = true;
		f1[s.pn] = false;
		hold[s.pn] = 0;
		Reach(strike, Num("range") / max(1, RSLD.Num("Base", "fi_range")));
		let l = RSLD_G7OnePunchLine(Actor.Spawn("RSLD_G7OnePunchLine", strike.pos, NO_REPLACE));
		if (l)
		{
			l.target = s.mo;
			l.angle = strike.angle;
			l.pitch = strike.pitch;
			l.SetDamage(int(Num("p_dmg")));
			l.Scale = (Num("p_scale"), Num("p_scale"));
			l.grow = Num("p_grow"); l.rad = Num("p_rad"); l.dist = Num("p_dist");
			l.dscale = Num("p_dscale"); l.ddist = Num("p_ddist"); l.high = Num("p_high");
			l.Vel3DFromAngle(Num("p_speed"), l.angle, l.pitch);
			s.TagMissile(l);
		}
		RSLD.Give(s.mo, "LDOnePunchCooldownGiver");
		s.mo.A_StartSound("Kick/Swing", CHAN_AUTO, CHANF_OVERLAP);
		s.Log(String.Format("ONE PUNCH: %d at reach x%.1f, the line of destruction flies, cooldown %d s", int(Num("dmg")), Num("range") / max(1, RSLD.Num("Base", "fi_range")), int(abs(Num("cooldown")))));
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.b1 && StrikeHit(h)) h.setDamage = int(Num("dmg"));
	}
}

// ---- Blaster (R: Fi), "Holding fire will cause you to fire plasma balls slowly": LegenDoom: after its punch (4 tics),
// 6 and 6 more, a plasma ball every 14 tics while fire is held (LDBlasterProjectile: 30, speed 35; berserk
// LDBlasterBerserkProjectile 90, speed 30). Ours: the main fist's trigger held (BD22 VR's No Trigger Punch leaves it
// free) fires BD22's own plasma ball (Plasma_Ball: our look, our impact sound; Plasma/Fire) from the fist where the
// controller points, at LegenDoom's damage (exact) and speed, first one 16 tics after the press, then every 14.
class RSLD_Fx_Blaster : RSLD_G7Effect
{
	Array<Actor> balls;
	Array<int> ballDmg;

	override void WhileHeld(RSLD_Held c)
	{
		Trigger(c);
		int pn = c.pn;
		int lead = int(Num("lead1") + Num("lead2") + Num("lead3"));
		int every = int(Num("loop") - Num("loop_rf"));
		if (hold[pn] < lead || every <= 0 || (hold[pn] - lead) % every != 0) return;
		class<Actor> bc = RSLD.AC("Plasma_Ball");
		if (!bc) return;
		bool b = Berserk(c.mo);
		Vector3 at;
		double a, pt;
		[at, a, pt] = RSLD_G2.Muzzle(c.mo, RSLD.MAIN, c.mo.angle, c.mo.pitch);
		a += frandom[rsld_g7](-0.25, 0.25);
		let m = Actor.Spawn(bc, at, ALLOW_REPLACE);
		if (!m) return;
		m.target = c.mo;
		m.angle = a;
		m.pitch = pt;
		m.Vel3DFromAngle(Num(b ? "speed_bers" : "speed"), a, pt);
		balls.Push(m);
		ballDmg.Push(int(Num(b ? "dmg_bers" : "dmg")));
		if (balls.Size() > 32) { balls.Delete(0); ballDmg.Delete(0); }
		c.mo.A_StartSound("Plasma/Fire", CHAN_AUTO, CHANF_OVERLAP);
		RSLD.Log(String.Format("Blaster: plasma ball from the fist (%d damage, speed %.0f), trigger held %d tics", ballDmg[ballDmg.Size() - 1], Num(b ? "speed_bers" : "speed"), hold[pn]));
	}

	override void OnMissile(RSLD_Shot s, Actor m)
	{
		int i = balls.Find(m);
		if (i < balls.Size()) { s.i1 = ballDmg[i]; s.Log(String.Format("blaster ball: %d damage on what it hits", s.i1)); }
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.i1 > 0 && h.inflictor && balls.Find(h.inflictor) < balls.Size()) h.setDamage = s.i1;
	}
}

// ---- NorthernStar (E: Fi; SILENT: owner, the Kenshiro voice is not carried), "Rapid punching that stuns and delays
// damage": LegenDoom's punches do 0 on the hit; each one (re)starts LDNorthernStarStunActive (60 tics) on the enemy,
// which is kept in pain (a 0-damage FORCEPAIN hit every tic) for as long as it lasts, and leaves one
// LDNorthernStarDamager (35, exact) that lands when the stun runs out: the more punches, the more lands at once.
// Ours: every real punch that lands is such a hit (LegenDoom's own stun item and damager, E); the stun-lock is ours
// (TriggerPainChance every tic, no sound). LegenDoom's closing radius thrust (the end of its held-fire combo) has no
// moment in real punching: not carried (owner question).
class RSLD_G7Stun : Thinker
{
	Actor t;
	override void Tick()
	{
		if (!t || t.health <= 0 || RSLD.Has(t, "LDNorthernStarStunActive") <= 0) { Destroy(); return; }
		t.TriggerPainChance('Melee', true);
	}
}

class RSLD_Fx_NorthernStar : RSLD_G7Effect
{
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		let t = h.target;
		if (!Fist(s) || !StrikeHit(h) || !t || !t.bISMONSTER || t.health <= 0) return;
		h.setDamage = 0;
		class<Inventory> st = RSLD.IC("LDNorthernStarStunActive");
		class<Actor> dc = RSLD.AC("LDNorthernStarDamager");
		if (!st || !dc) return;
		t.TakeInventory(st, 1);
		t.GiveInventory(st, 1);
		let d = Actor.Spawn(dc, t.pos, NO_REPLACE);
		if (d) { d.target = s.mo; d.tracer = t; }
		bool running = false;
		let it = ThinkerIterator.Create("RSLD_G7Stun", Thinker.STAT_DEFAULT);
		RSLD_G7Stun k;
		while ((k = RSLD_G7Stun(it.Next()))) if (k.t == t) { running = true; break; }
		if (!running) { let n = new("RSLD_G7Stun"); n.t = t; }
		s.Log(String.Format("northern star: %s stunned %d tics, %d more damage waits for the stun's end (LegenDoom's damager)",
			t.GetClassName(), int(Num("stun")), int(Num("dmg"))));
	}
}

// ---- Lacerating (E: Cs), "Does more damage the longer you saw enemies": LegenDoom's saw does x(count + 4) / 4, count
// (LDLaceratingCounter, max 40) going up by one on each hit that comes within 10 tics of the last (LDLaceratingTimer),
// back to 1 otherwise. Ours: the same count on our saw's hits, its multiplier on our saw's damage.
class RSLD_Fx_Lacerating : RSLD_G7Effect
{
	int count[MAXPLAYERS], last[MAXPLAYERS];

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (!Saw(s) || !h.target || !h.target.bISMONSTER) return;
		double div = max(1, Num("div"));
		h.mult *= (count[s.pn] + Num("add")) / div;
	}

	override void OnHit(RSLD_Shot s, RSLD_Hit h)
	{
		if (!Saw(s) || !h.target || !h.target.bISMONSTER) return;
		int pn = s.pn;
		if (level.maptime - last[pn] <= Num("timer")) count[pn] = min(count[pn] + 1, int(Num("max")));
		else count[pn] = 1;
		last[pn] = level.maptime;
		s.Log(String.Format("lacerating: count %d, next hit x%.2f", count[pn], (count[pn] + Num("add")) / max(1, Num("div"))));
	}
}

// ---- Imaginary (E: Cs; SILENT: owner, LegenDoom's "EEEE" voice is not carried), "Uses the power of your mind":
// LegenDoom's saw reaches 512 (where 65), never turns or pulls you, and throws its "EEEE" letters
// (LDImaginaryEEEEAttackSpawner: LegenDoom's own visual, no damage) with each attack. Ours: the same on our saw.
class RSLD_Fx_Imaginary : RSLD_G7Effect
{
	override void WhileHeld(RSLD_Held c) { RSLD_G7.NoTurn(c); }

	override void OnPull(RSLD_Shot s)
	{
		if (!Saw(s) || !s.mo) return;
		class<Actor> c = RSLD.AC("LDImaginaryEEEEAttackSpawner");
		if (!c) return;
		Vector3 at;
		double a, pt;
		[at, a, pt] = RSLD_G2.Muzzle(s.mo, s.hand, s.mo.angle, s.mo.pitch);
		let v = Actor.Spawn(c, at, NO_REPLACE);
		if (v) { v.angle = a; v.target = s.mo; }
	}

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (!Saw(s)) return false;
		double r = Num("range") / max(1, RSLD.Num("Base", "cs_range"));
		p.range *= r;
		if (p.index == 0) s.Log(String.Format("imaginary (silent): saw range %.0f (x%.2f), no turn / pull, LegenDoom's EEEE", p.range, r));
		return false;
	}
}
