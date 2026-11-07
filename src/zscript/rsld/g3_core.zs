// LD mode, round 3 (agent R3a, 2026-11-06 evening): the per-missile rider used by G3 (missile effects) and G4 (BFG).
//
// Our guns keep THEIR projectiles (BD22's Rocket2 / Rocket2Fast / RocketDM, Plasma_Ball / PlasmaBall75 / PlasmaBallDM,
// SuperBFGBall / BFGBallDM, the Rifle's ShortGrenade), their models, sounds and explosions. A LegenDoom missile effect
// rides on that projectile (RSLD_Rider, one Thinker per projectile): LegenDoom's per-tic rule (x1.05 a tic, seeking,
// warps, pulses...), its flags (RIPPER, bounces) and its death rule (clusters, chains), with LegenDoom's numbers
// (numbers_g3.zs, from ldl_patch/tools/numbers/g3.rules). Where LegenDoom's number is gun-relative (its rocket's
// 20 x random(1,8) + 128/128 blast), LegenDoom's ratio is applied to our projectile's own number (scope section 0, R).
//
// Explosions: BD22's rocket / grenade blast is a separate actor (RocketExplosion / UGBLExplosion, Explosives.dec:265 /
// :395) spawned by the projectile's Death state, which explodes 3 tics later with A_Explode(100, 150). When an
// effect changes the blast (HighExplosive, Vidmaster, ShapedCharge, Kinetic, Spreadfire minis ...), the rider takes
// that actor the moment it spawns (handler.zs WorldThingSpawned -> RSLD_G3.HelperSpawned) and puts RSLD_Boom in its
// place: the same visuals (WhiteShockwave, the air bursts), the same delay, the same damage type, with the changed
// A_Explode. A blast the rider claims is tagged to the pull, so its damage is that pull's (OnHit, OnKill...).
// The BFG ball explodes and sprays rays itself (BFG.dec SuperBFGBall Death: A_Explode(200,400), 2 tics later
// A_BFGSpray("SuperBFGExtra", 50)): its blast is changed in ModifyDamage (DMG_EXPLOSION from the ball), its rays are
// muted (SkipSpray: no damage, flashes removed, the death tic and the next) or caught / re-fired by the effect.
// Children (Spreadfire, Cluster, Spamtastic, Suppression, Waveform) are OUR projectile class, spawned with no target
// at first (the LD handler and BD22 VR's muzzle never see them as a new shot), then tagged to the pull.
// Debug: rsld_debug 1 logs what each effect did ("rider ..."), 2 also every rider tick event.

class RSLD_G3 play
{
	const K_NONE = 0;
	const K_ROCKET = 1;
	const K_PLASMA = 2;
	const K_BFG = 3;
	const K_GRENADE = 4;

	// our projectile kinds (by class ancestry; LegenDoom's own LD* projectiles never come here: handler.zs)
	static int Kind(Actor m)
	{
		if (!m) return K_NONE;
		for (class<Actor> c = m.GetClass(); c && c != "Actor"; c = (class<Actor>)(c.GetParentClass()))
		{
			Name n = c.GetClassName();
			if (n == 'Rocket2') return K_ROCKET;
			if (n == 'Plasma_Ball') return K_PLASMA;
			if (n == 'SuperBFGBall' || n == 'BFGBall') return K_BFG;
			if (n == 'ShortGrenade' || n == 'GrenadeMissile') return K_GRENADE;
		}
		return K_NONE;
	}
	static string KindName(int k) { switch (k) { case K_ROCKET: return "rocket"; case K_PLASMA: return "plasma"; case K_BFG: return "bfg"; case K_GRENADE: return "grenade"; } return "none"; }

	static double N(string eff, string key) { return RSLD.Num(eff, key); }
	// a number that may not exist for every gun (no "missing number" log)
	static double NOr(string eff, string key, double def = 0)
	{
		let h = RSLD.H();
		if (!h || h.NumSrc(eff, key) == "") return def;
		return h.Num(eff, key);
	}
	static double RndMean() { return (1 + N("Base3", "rnd_max")) / 2.0; }		// random(1,8): 4.5

	// LegenDoom's own direct-hit number for a kind (its projectile's Damage, before x random(1,8)); grenades count as rockets
	static double LDBase(int k)
	{
		if (k == K_PLASMA) return N("Base3", "pl_dmg");
		if (k == K_BFG) return N("Base3", "bfg_dmg");
		return N("Base3", "rk_dmg");
	}
	static string KindKey(int k) { if (k == K_PLASMA) return "pl"; if (k == K_BFG) return "bfg"; return "rk"; }

	// BD22's blast actors for our projectiles (Explosives.dec:265 RocketExplosion, :395 UGBLExplosion: both A_Explode(100,150))
	static bool IsBlast(Actor a)
	{
		if (!a) return false;
		Name n = a.GetClassName();
		return n == 'RocketExplosion' || n == 'UGBLExplosion';
	}
	const BLAST_DMG = 100;		// brutal22test6 actors/Weapons/Explosives.dec:282 / :405 A_Explode(100,150)
	const BLAST_RAD = 150;
	const BLAST_DELAY = 3;		// Explosives.dec:280 "TNT1 A 3" before the A_Explode (UGBL :404 too)

	// the level's registry, cached on the LD handler (a ThinkerIterator per call would cost on every spawn)
	static RSLD_G3Reg Reg()
	{
		let h = RSLD.H();
		if (!h) return RSLD_G3Reg.Get();
		if (!h.g3reg) h.g3reg = RSLD_G3Reg.Get();
		return h.g3reg;
	}

	static RSLD_Rider RiderOf(Actor m)
	{
		if (!m) return null;
		let g = Reg();
		for (int i = g.riders.Size() - 1; i >= 0; i--) if (g.riders[i] && g.riders[i].m == m) return g.riders[i];
		return null;
	}

	// a rider on m for effect fx (one per projectile; a second effect on the same projectile gets the same rider)
	static RSLD_Rider Ride(RSLD_Shot s, Actor m, RSLD_G3Fx fx, bool child = false)
	{
		if (!s || !m || !fx) return null;
		let r = RiderOf(m);
		if (r) return r;
		r = new("RSLD_Rider");
		r.m = m; r.s = s; r.fx = fx; r.kind = Kind(m); r.cls = m.GetClass(); r.child = child;
		r.dmgMul = 1; r.explDmgMul = 1; r.explRadMul = 1; r.rayMul = 1;
		r.last = m.pos; r.prevBounce = m.bouncecount; r.ourDirect = m.GetMissileDamage(0, 1);
		r.spawnTic = level.maptime;
		Reg().riders.Push(r);
		return r;
	}

	// handler.zs: a BD22 helper missile spawned (RocketExplosion / UGBLExplosion: the blast of a projectile that just died)
	static bool HelperSpawned(Actor a, PlayerPawn mo)
	{
		if (!IsBlast(a)) return false;
		let g = Reg();
		RSLD_Rider best = null;
		double bd = 96;
		for (int i = g.riders.Size() - 1; i >= 0; i--)
		{
			let r = g.riders[i];
			if (!r || r.claimed || !r.s || r.s.mo != mo) continue;
			if (r.m && r.m.bMISSILE) continue;		// still flying: not its blast
			Vector3 at = r.m ? r.m.pos : r.last;
			double d = (a.pos - at).Length();
			if (d < bd) { bd = d; best = r; }
		}
		if (!best) return false;
		best.claimed = true;
		best.blastPos = a.pos;
		if (best.fx) best.fx.RiderBlast(best, a);
		return true;
	}

	// the projectile's blast, changed: RSLD_Boom in place of BD22's blast actor (same visuals, delay, damage type)
	static RSLD_Boom Boom(RSLD_Rider r, Actor orig, Vector3 at, int dmg, double rad, double full = 0, int flags = XF_HURTSOURCE, int delay = BLAST_DELAY)
	{
		let b = RSLD_Boom(Actor.Spawn("RSLD_Boom", at, NO_REPLACE));
		if (!b) return null;
		if (r && r.s) b.target = r.s.mo; else if (orig) b.target = orig.target;
		b.dmg = dmg; b.rad = rad; b.full = full; b.flagsX = flags; b.delay = delay;
		b.vis = orig && orig.GetClassName() == 'UGBLExplosion' ? 2 : 1;
		if (orig)
		{
			b.DamageType = orig.DamageType;
			b.bFORCERADIUSDMG = orig.bFORCERADIUSDMG;
			orig.Destroy();
		}
		else b.DamageType = 'ExplosiveImpact';	// RocketExplosion's (Explosives.dec:270)
		if (r && r.s) { let h = RSLD.H(); if (h) h.Tag(b, r.s); }
		return b;
	}

	// a blast of our own at a point (no BD22 actor to replace: chains, ray targets, pulses)
	static RSLD_Boom BoomAt(RSLD_Shot s, Vector3 at, int dmg, double rad, double full = 0, int flags = XF_HURTSOURCE, int delay = 0, Name dtype = 'ExplosiveImpact', int vis = 0, string snd = "")
	{
		let b = RSLD_Boom(Actor.Spawn("RSLD_Boom", at, NO_REPLACE));
		if (!b) return null;
		b.target = s ? s.mo : null;
		b.dmg = dmg; b.rad = rad; b.full = full; b.flagsX = flags; b.delay = delay; b.vis = vis; b.snd = snd;
		b.DamageType = dtype;
		if (s) { let h = RSLD.H(); if (h) h.Tag(b, s); }
		return b;
	}

	// a child projectile of OUR class (Spreadfire, Cluster, Spamtastic, Suppression, Waveform): no target while it spawns
	// (so neither the LD handler nor BD22 VR's muzzle take it for a new shot), then the shooter's, tagged to the pull
	static Actor Child(RSLD_Rider r, Vector3 at, double ang, double pit, double speed, double dmgMul, double scaleMul, RSLD_G3Fx fx = null)
	{
		if (!r || !r.cls || !r.s) return null;
		let c = Actor.Spawn(r.cls, at, NO_REPLACE);
		if (!c) return null;
		if (r.kind == K_ROCKET)
		{	// past Rocket2's Spawn state (its backblast / backblast flames and the fly sound: RocketLauncher's own launch)
			State lv = c.FindState("Live");
			if (lv) c.SetState(lv);
		}
		c.target = r.s.mo;
		c.angle = ang; c.pitch = pit;
		c.Vel3DFromAngle(speed, ang, pit);
		c.scale *= scaleMul;
		r.s.TagMissile(c);
		let cr = Ride(r.s, c, fx ? fx : r.fx, true);
		// its damage: our projectile's own (fixed in BD22: SetDamage would make it x random(1,8)) x dmgMul in ModifyDamage
		if (cr) { cr.ourDirect = r.ourDirect; cr.dmgMul = dmgMul; }
		return c;
	}

	// the flight direction of a projectile
	static double, double Dir(Actor m)
	{
		Vector3 v = m.vel;
		double l = v.xy.Length();
		if (l < 0.001 && abs(v.z) < 0.001) return m.angle, m.pitch;
		return VectorAngle(v.x, v.y), -atan2(v.z, l);
	}

	// the BFG ball's own ray spray, muted: its rays do no damage and their flashes are removed. SuperBFGBall Death:
	// "BFGB A 2" then "TNT1 A 0 A_BFGSpray"; P_ExplodeMissile shortens that first frame at random (tics -= random & 3,
	// at least 1), so the spray runs in the death tic itself (3 in 4) or the next one (round 3 batched run: a state skip
	// came too late). The rays are A_BFGSpray's (inflictor the player, 'Desintegrate'): RayWindow x0 for those two tics;
	// the flashes (SuperBFGExtra) first seen in those tics are removed. A spray of ours comes later (RiderAfter 2).
	static bool SkipSpray(Actor m, RSLD_Rider r = null)
	{
		if (!m) return false;
		let mo = PlayerPawn(m.target);
		if (!mo) return false;
		RayWindow(mo, 0, 1);
		Reg().flashMuteUntil = level.maptime + 1;
		if (r) Log(r, "its own rays muted (death tic and the next)");
		return true;
	}

	// LegenDoom actors that do their job with LegenDoom's sound: their sound channels are stopped for a few tics
	static void Silence(Actor a, int tics = 4)
	{
		if (!a) return;
		for (int c = 1; c <= 7; c++) a.A_StopSound(c);
		Reg().AddHush(a, tics);
	}

	// BFG rays (A_BFGSpray: inflictor and source both the player, the spray's DamageType 'Desintegrate' for BD22's
	// SuperBFGExtra): a window after a ridden ball died, with a damage multiplier
	static void RayWindow(PlayerPawn mo, double mul, int tics = 6) { Reg().SetRays(mo, mul, tics); }
	static bool IsRay(RSLD_Shot s, RSLD_Hit h) { return h && s && h.inflictor == s.mo && h.damageType == 'Desintegrate'; }
	static double RayMul(PlayerPawn mo) { return Reg().GetRayMul(mo); }

	static void Log(RSLD_Rider r, string msg)
	{
		if (!RSLD.Debug() || !r) return;
		Console.Printf("RSLD %d %s rider %s%s p%d: %s", level.maptime, r.fx ? r.fx.name : "?", KindName(r.kind), r.child ? " child" : "", r.s ? r.s.pull : 0, msg);
	}
}

// per-level registry: riders, LegenDoom actors being silenced, BFG ray windows, Spreadfire's alternating pattern
class RSLD_G3Reg : Thinker
{
	Array<RSLD_Rider> riders;
	Array<Actor> hush;
	Array<int> hushTics;
	int rayUntil[MAXPLAYERS];
	double rayMul[MAXPLAYERS];
	bool spreadMode[MAXPLAYERS];

	// a thinking thinker (STAT_DEFAULT: a STAT_INFO thinker never ticks)
	static RSLD_G3Reg Get()
	{
		let it = ThinkerIterator.Create("RSLD_G3Reg");
		let g = RSLD_G3Reg(it.Next());
		if (!g) g = new("RSLD_G3Reg");
		return g;
	}

	RSLD_G3Plasmatic plasmatic;
	// TORGUE: enemies that explode when they die (and the pull that marked them)
	Array<Actor> marked;
	Array<RSLD_Shot> markedBy;
	// Illuminating: the idle glow on a player while the gun is held
	Array<Actor> glowOn;
	Array<int> glowTic;
	// a ray spray of ours being fired now (Raycaster, Annihilating): a blast at every target it spawns its flash on
	int flashMuteUntil;			// BD22's ray flashes (SuperBFGExtra) first seen up to this tic are removed (SkipSpray)
	RSLD_Shot catchS;
	int catchDmg, catchFlags;
	double catchRad;
	int catchN, catchTic;
	string catchWho;

	bool Mark(Actor a, RSLD_Shot s)
	{
		if (!a || marked.Find(a) < marked.Size()) return false;
		marked.Push(a); markedBy.Push(s);
		return true;
	}

	void Glow(Actor p, Color c, int s1, int s2, double interval)
	{
		if (!p) return;
		int k = glowOn.Find(p);
		if (k >= glowOn.Size())
		{
			p.A_AttachLight('rsld_illum_idle', DynamicLight.PulseLight, c, s1, s2, 0, (0, 0, p.Height * 0.5), interval);
			glowOn.Push(p); glowTic.Push(level.maptime);
			if (RSLD.Debug()) Console.Printf("RSLD %d Illuminating: idle glow on", level.maptime);
			return;
		}
		glowTic[k] = level.maptime;
	}

	// handler.zs WorldThingDied: a TORGUE-marked enemy died: LegenDoom's death blast (LDTORGUEExplosion 128/128 no self)
	void Died(Actor t)
	{
		int k = marked.Find(t);
		if (k >= marked.Size()) return;
		let s = markedBy[k];
		marked.Delete(k); markedBy.Delete(k);
		Vector3 at = t.pos + (0, 0, t.Height * 0.5);
		double r = RSLD_G3.BLAST_RAD * RSLD_G3.N("TORGUE", "chain") / RSLD_G3.N("Base3", "rk_rad");
		int d = int(RSLD_G3.BLAST_DMG * RSLD_G3.N("TORGUE", "chain") / RSLD_G3.N("Base3", "rk_expl") + 0.5);
		RSLD_G3.BoomAt(s, at, d, r, 0, 0, 0, 'ExplosiveImpact', 0, "Explode1");
		RSLD.LDVisual("LDTORGUEExplosion", at, "Death", 4, s ? s.mo : null);
		if (RSLD.Debug()) Console.Printf("RSLD %d TORGUE: %s died: explodes (%d over %.0f)", level.maptime, t.GetClassName(), d, r);
	}

	// handler.zs WorldThingSpawned: BD22's ray flash (SuperBFGExtra) while a spray of ours runs
	void SpraySpawned(Actor a)
	{
		if (!a) return;
		Name n = a.GetClassName();
		if (n != 'SuperBFGExtra') return;
		if (level.maptime <= flashMuteUntil && !catchS) { a.Destroy(); return; }
		if (!catchS) return;
		RSLD_G3.BoomAt(catchS, a.pos, catchDmg, catchRad, 0, catchFlags, 0, 'Desintegrate');
		catchN++;
	}

	void AddHush(Actor a, int tics) { hush.Push(a); hushTics.Push(tics); }

	void SetRays(PlayerPawn mo, double mul, int tics)
	{
		if (!mo) return;
		int pn = mo.PlayerNumber();
		rayUntil[pn] = level.maptime + tics;
		rayMul[pn] = mul;
	}

	double GetRayMul(PlayerPawn mo)
	{
		if (!mo) return 1;
		int pn = mo.PlayerNumber();
		return level.maptime <= rayUntil[pn] ? rayMul[pn] : 1;
	}

	override void Tick()
	{
		if (catchS && level.maptime > catchTic)
		{
			if (RSLD.Debug()) Console.Printf("RSLD %d %s: %d ray targets, a blast on each", level.maptime, catchWho, catchN);
			catchS = null; catchN = 0;
		}
		for (int i = riders.Size() - 1; i >= 0; i--) if (!riders[i]) riders.Delete(i);
		for (int i = marked.Size() - 1; i >= 0; i--) if (!marked[i] || marked[i].health <= 0 && !marked[i].bISMONSTER) { marked.Delete(i); markedBy.Delete(i); }
		for (int i = glowOn.Size() - 1; i >= 0; i--)
			if (!glowOn[i] || glowTic[i] < level.maptime - 1)
			{
				if (glowOn[i]) glowOn[i].A_RemoveLight('rsld_illum_idle');
				if (RSLD.Debug()) Console.Printf("RSLD %d Illuminating: idle glow off", level.maptime);
				glowOn.Delete(i); glowTic.Delete(i);
			}
		for (int i = hush.Size() - 1; i >= 0; i--)
		{
			let a = hush[i];
			if (a) for (int c = 1; c <= 7; c++) a.A_StopSound(c);
			if (!a || --hushTics[i] <= 0) { hush.Delete(i); hushTics.Delete(i); }
		}
	}
}

// one projectile's rider
class RSLD_Rider : Thinker
{
	Actor m;
	class<Actor> cls;
	RSLD_Shot s;
	RSLD_G3Fx fx;
	int kind, age, deadAge, prevBounce, bounces, spawnTic, ourDirect;
	bool dead, child, claimed, sky, started;
	Vector3 last, blastPos;
	// what the rider changes (multipliers on our projectile's own numbers)
	double dmgMul;			// direct hit
	double explDmgMul, explRadMul, rayMul;
	int directAdd;			// added to the direct hit (Kinetic, GroupTherapy: the blast moved onto the hit)
	int explAdd;			// added to the blast damage (Concentrating)
	bool explFull, explNoSelf, noExpl, noRays;
	// effect scratch
	int i1, i2, i3;
	double d1, d2;
	bool b1, b2;
	Actor a1;

	bool BlastChanged() { return noExpl || explFull || explNoSelf || explDmgMul != 1 || explRadMul != 1 || explAdd != 0; }

	override void Tick()
	{
		if (dead)
		{
			deadAge++;
			if (fx) fx.RiderAfter(self);
			if (deadAge > 40) Destroy();
			return;
		}
		if (!m || !m.bMISSILE)
		{
			dead = true;
			sky = (m == null);
			if (m) last = m.pos;
			if (fx) fx.RiderDeath(self);
			return;
		}
		if (!started)
		{	// the first tic: BD22 VR's muzzle.zs has put the projectile at the drawn muzzle by now
			started = true;
			if (fx) fx.RiderStart(self);
			if (!m) return;
		}
		age++;
		bool bounced = m.bouncecount < prevBounce;
		if (bounced) bounces++;
		last = m.pos;
		if (fx) fx.RiderTick(self, bounced);
		if (m) prevBounce = m.bouncecount;
	}
}

// a blast in place of BD22's blast actor (or one of our own): RocketExplosion's visuals at the start, A_Explode after delay
class RSLD_Boom : Actor
{
	int dmg, flagsX, delay, age, vis;
	double rad, full;
	string snd;

	Default
	{
		+NOINTERACTION
		+NOBLOCKMAP
		+NOGRAVITY
		RenderStyle "None";
		Radius 2;
		Height 2;
	}

	override void Tick()
	{
		if (age == 0 && vis == 1) { let c = RSLD.AC("WhiteShockwave"); if (c) Spawn(c, pos, ALLOW_REPLACE); }	// Explosives.dec:280
		if (age >= delay)
		{
			if (dmg > 0 && rad > 0) A_Explode(dmg, rad, flagsX, false, full);
			string ab = vis == 2 ? "ExplosionAirBurstEffect" : "ExplosionAirBurstEffectSmall";	// Explosives.dec:281 / :406
			let c = vis > 0 ? RSLD.AC(ab) : null;
			if (c) for (int i = 0; i < 7; i++) A_SpawnProjectile(c, 2, 0, random(0, 360), CMF_AIMDIRECTION, random(-45, 45));
			if (vis == 2) { let w = RSLD.AC("WhiteShockwaveBig"); if (w) Spawn(w, pos, ALLOW_REPLACE); }	// Explosives.dec:407
			if (snd != "") A_StartSound(snd, CHAN_AUTO, CHANF_OVERLAP);
			Destroy();
			return;
		}
		age++;
	}
}

// base of the G3 / G4 effects: OnMissile puts a rider on each of our projectiles of the pull
class RSLD_G3Fx : RSLD_Effect
{
	// which projectile kinds this effect rides (LegenDoom's slots: RL rockets, PR plasma, BF ball; grenades as rockets)
	virtual bool Rides(int kind) { return kind != RSLD_G3.K_NONE; }

	override void OnMissile(RSLD_Shot s, Actor m)
	{
		int k = RSLD_G3.Kind(m);
		if (!Rides(k)) { if (RSLD.DebugLevel() > 1) s.Log(String.Format("%s: not a projectile this effect rides", m.GetClassName())); return; }
		let r = RSLD_G3.Ride(s, m, self);
		if (r) RiderSpawn(r);
	}

	// at once, inside the projectile's spawn (before BD22 VR's muzzle moves it): flags and multipliers
	virtual void RiderSpawn(RSLD_Rider r) {}
	// its first tic (it is at the drawn muzzle now): children, conversions
	virtual void RiderStart(RSLD_Rider r) {}
	// every tic in flight (after it moved); bounced: it bounced this tic
	virtual void RiderTick(RSLD_Rider r, bool bounced) {}
	// it died (exploded, or vanished in the sky: r.sky); r.m is the dead projectile (its death state), r.last its spot
	virtual void RiderDeath(RSLD_Rider r) {}
	// every tic for 40 tics after it died
	virtual void RiderAfter(RSLD_Rider r) {}

	// BD22's blast actor of this projectile just spawned: by default the rider's blast multipliers are applied
	virtual void RiderBlast(RSLD_Rider r, Actor a)
	{
		if (!r.BlastChanged())
		{
			let h = RSLD.H();
			if (h) h.Tag(a, r.s);		// unchanged: still this pull's damage
			return;
		}
		if (r.noExpl)
		{
			RSLD_G3.Log(r, String.Format("blast %s removed (no splash)", a.GetClassName()));
			a.Destroy();
			return;
		}
		int dmg = int(RSLD_G3.BLAST_DMG * r.explDmgMul + 0.5) + r.explAdd;
		double rad = RSLD_G3.BLAST_RAD * r.explRadMul;
		int fl = r.explNoSelf ? 0 : XF_HURTSOURCE;
		RSLD_G3.Log(r, String.Format("blast %s -> %d over %.0f%s%s (BD22's %d / %d)", a.GetClassName(), dmg, rad, r.explFull ? ", full damage over the radius" : "",
			r.explNoSelf ? ", does not hurt the shooter" : "", RSLD_G3.BLAST_DMG, RSLD_G3.BLAST_RAD));
		RSLD_G3.Boom(r, a, a.pos, dmg, rad, r.explFull ? rad : 0, fl);
	}

	// direct hits, the BFG ball's own blast and its rays: the rider's multipliers; then RiderDamage
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		let r = RSLD_G3.RiderOf(h.inflictor);
		if (r)
		{
			if (h.flags & DMG_EXPLOSION)
			{
				if (r.kind == RSLD_G3.K_BFG)
				{
					if (r.noExpl) h.mult = 0;
					else h.mult *= r.explDmgMul;
				}
			}
			else
			{
				h.mult *= r.dmgMul;
				if (r.directAdd > 0 && h.damage > 0) h.mult *= (h.damage * r.dmgMul + r.directAdd) / max(1.0, h.damage * r.dmgMul);
			}
		}
		else if (RSLD_G3.IsRay(s, h))
		{
			double rm = RSLD_G3.RayMul(s.mo);
			if (rm != 1) h.mult *= rm;
		}
		RiderDamage(s, h, r);
	}
	virtual void RiderDamage(RSLD_Shot s, RSLD_Hit h, RSLD_Rider r) {}
}
