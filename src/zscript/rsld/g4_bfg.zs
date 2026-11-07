// LD mode, G4: LegenDoom's BFG family on BD22's BFG 9000 (round 3, agent R3a). Framework: g3_core.zs.
// BD22's ball (brutal22test6 BFG.dec SuperBFGBall, replaces BFGBall): 1500 direct, Death: A_Explode(200,400), 2 tics
// later A_BFGSpray("SuperBFGExtra", 50) (50 rays of 15 x random(1,8)). LegenDoom's ball: 100 x random(1,8), 40 rays.
// Rays are A_BFGSpray's: traced from the player along the ball's angle, inflictor the player (weaponbfg.zs).

class RSLD_G4 play
{
	const OUR_RAYS = 50;		// BFG.dec SuperBFGBall A_BFGSpray("SuperBFGExtra", 50)
	const OUR_BLAST = 200;		// BFG.dec SuperBFGBall A_Explode(200,400)
	const OUR_BLAST_RAD = 400;

	// a spray of BD22's rays from `from` (its angle; traced from its target, the player), optionally a blast of
	// ours at every target a ray hits: caught as its SuperBFGExtra flash is first seen (WorldThingSpawned comes on an
	// actor's first think, later this same tic: handler.zs -> RSLD_G3Reg.SpraySpawned; the catch ends with the tic)
	static void Spray(RSLD_Shot s, Actor from, int rays, int dmgcnt = 15, double fov = 90, int blastDmg = 0, double blastRad = 0, int blastFlags = 0, string who = "")
	{
		let c = RSLD.AC("SuperBFGExtra");
		if (!from || !c) return;
		let g = RSLD_G3.Reg();
		if (blastDmg > 0) { g.catchS = s; g.catchDmg = blastDmg; g.catchRad = blastRad; g.catchFlags = blastFlags; g.catchN = 0; g.catchTic = level.maptime; g.catchWho = who; }
		from.A_BFGSpray(c, rays, dmgcnt, fov);
	}
}

class RSLD_G4Fx : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_BFG; }
}

// Annihilating (E: BF): "Dangerous explosion on impact, rays also explode": A_Explode(256, 256, 0) at the ball and
// every ray target hit by A_Explode(64, 64, 1) (LDAnnihilatingBFGFlash). LegenDoom's ball has no blast of its own, so
// these are LegenDoom's numbers (E), on top of our ball's own blast; our rays take LegenDoom's flash blast.
class RSLD_Fx_Annihilating : RSLD_G4Fx
{
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky || !r.m) return;
		double rad = RSLD_G3.N("Annihilating", "rad");
		RSLD_G3.BoomAt(r.s, r.last, int(RSLD_G3.N("Annihilating", "expl")), rad, 0, 0, 0, 'Desintegrate');
		// its own rays (this tic or the next): a blast where each one lands (caught as its flash is first seen)
		let g = RSLD_G3.Reg();
		g.catchS = r.s; g.catchDmg = int(RSLD_G3.N("Annihilating", "rayexpl")); g.catchRad = RSLD_G3.N("Annihilating", "rayrad");
		g.catchFlags = XF_HURTSOURCE; g.catchN = 0; g.catchTic = level.maptime + 1; g.catchWho = "Annihilating";
		RSLD_G3.Log(r, String.Format("dangerous blast %d over %.0f (no self); its rays explode %d over %.0f", int(RSLD_G3.N("Annihilating", "expl")), rad, g.catchDmg, g.catchRad));
	}
}

// Energetic (U: BF): "Emits twice as many BFG rays" (A_BFGSpray("LDBFGFlash", 80) = 2 x 40): our 50, then 50 more
class RSLD_Fx_Energetic : RSLD_G4Fx
{
	override void RiderAfter(RSLD_Rider r)
	{
		if (r.sky || r.deadAge != 2 || !r.m) return;
		int extra = int(RSLD_G4.OUR_RAYS * (RSLD_G3.N("Energetic", "rays") / RSLD_G3.N("Base3", "bfg_rays") - 1) + 0.5);
		RSLD_G4.Spray(r.s, r.m, extra);
		RSLD_G3.Log(r, String.Format("%d more rays (x%.0f)", extra, RSLD_G3.N("Energetic", "rays") / RSLD_G3.N("Base3", "bfg_rays")));
	}
}

// Energizing (C: BF): the ball does Damage (20) (its base 100 x random(1,8)), no rays, slows x0.9 a tic; once still
// it is an anomaly: 21 pulses 16 tics apart, each giving LegenDoom's LDEnergizingHealing (a health bonus) to every
// player within 256, then it goes off. Ours: direct and blast x 20 / 450, no rays; BFG/Charge when it deploys
// (effects/energizingstart), our health bonus pickup sound per heal (scope 4).
class RSLD_Fx_Energizing : RSLD_G4Fx
{
	override void RiderSpawn(RSLD_Rider r)
	{
		double f = RSLD_G3.N("Energizing", "dmg") / (RSLD_G3.LDBase(RSLD_G3.K_BFG) * RSLD_G3.RndMean());
		r.dmgMul = f; r.explDmgMul = f; r.noRays = true;
	}
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		let m = r.m;
		if (r.i1 == 0)
		{
			m.A_ScaleVelocity(RSLD_G3.N("Energizing", "decel"));
			if (RSLD_G3Util.Still(m, 1))
			{
				m.A_Stop(); r.i1 = 1; r.i2 = int(RSLD_G3.N("Energizing", "pulses")); r.i3 = 0;
				m.A_StartSound("BFG/Charge", CHAN_AUTO, CHANF_OVERLAP);
				RSLD_G3.Log(r, String.Format("anomaly after %d tics: %d pulses", r.age, r.i2 + 1));
			}
			return;
		}
		m.vel = (0, 0, 0);
		if (r.i3-- > 0) return;
		r.i3 = int(RSLD_G3.N("Energizing", "period")) - 1;
		RSLD.LDVisual("LDEnergizingBFGShockwave", m.pos, "Spawn", 0, r.s.mo);
		double rad = RSLD_G3.N("Energizing", "radius");
		int healed = 0;
		for (int pn = 0; pn < MAXPLAYERS; pn++)
		{
			if (!playeringame[pn] || !players[pn].mo) continue;
			let p = players[pn].mo;
			if (p.health <= 0 || m.Distance3D(p) > rad) continue;	// RGF_PLAYERS | RGF_NOSIGHT
			RSLD.Give(p, "LDEnergizingHealing");
			let hb = RSLD_B.HealthBonusCls();
			let d = hb ? GetDefaultByType(hb) : null;
			if (d) p.A_StartSound(d.PickupSound, CHAN_AUTO, CHANF_OVERLAP);
			healed++;
		}
		if (r.i2 == int(RSLD_G3.N("Energizing", "pulses")) || RSLD.DebugLevel() > 1) RSLD_G3.Log(r, String.Format("pulse: %d players healed", healed));
		if (r.i2-- <= 0) { m.bNOCLIP = true; m.bTHRUACTORS = true; m.ExplodeMissile(); RSLD_G3.Log(r, "anomaly ends"); }
	}
	override void RiderDeath(RSLD_Rider r) { RSLD_G3.SkipSpray(r.m, r); }
}

// Nova (C: BF): no rays; a cascade from the blast: LegenDoom's LDNovaBFGBall2 (fast ripper, Damage 3, speed 50) every
// 15 degrees around, pitch -50 to 50 in steps of 10, plus its lightning sparks (LegenDoom's projectiles: E)
class RSLD_Fx_Nova : RSLD_G4Fx
{
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky || !r.m) return;
		RSLD_G3.SkipSpray(r.m, r);
		let c = RSLD.AC("LDNovaBFGBall2");
		if (!c) return;
		double ofs = 0;
		if (r.m.ceilingz - r.last.z < 16) ofs = -8; else if (r.last.z - r.m.floorz < 16) ofs = 8;
		Vector3 at = r.last + (0, 0, ofs);
		let sp = RSLD.AC("LDNovaLightningSparks");
		if (sp) Actor.Spawn(sp, r.last, NO_REPLACE);
		int n = 0, st = int(RSLD_G3.N("Nova", "astep")), pm = int(RSLD_G3.N("Nova", "pitch")), ps = int(RSLD_G3.N("Nova", "pstep"));
		for (int p = -pm; p <= pm; p += ps)
			for (int a = 0; a < 360; a += st)
			{
				let b = Actor.Spawn(c, at, NO_REPLACE);
				if (!b) continue;
				b.target = r.s.mo;
				b.angle = r.m.angle + a; b.pitch = p;
				b.Vel3DFromAngle(b.Speed, b.angle, -p);
				n++;
			}
		RSLD_G3.Log(r, String.Format("nova cascade: %d", n));
	}
}

// Prototype (E: BF): "Sprays huge amounts of plasma projectiles": LegenDoom's BFG streams LDPrototypeBFGBallGreen
// pairs (one straight, one +-2 degrees), one pair a tic, one cell a pair. Ours: the ball becomes a stream of those
// pairs from the drawn muzzle, as many pairs as the cells the shot took, damage at our BFG's ratio (our 1500 over its
// 100 x random(1,8) mean); LegenDoom's balls are silenced when they burst (Plasma/Impact in their place).
class RSLD_Fx_Prototype : RSLD_G4Fx
{
	override void RiderStart(RSLD_Rider r)
	{
		if (r.child || !r.m) return;
		r.m.Destroy();
		let st = new("RSLD_ProtoStream");
		st.s = r.s; st.fx = self;
		st.ratio = r.ourDirect / (RSLD_G3.LDBase(RSLD_G3.K_BFG) * RSLD_G3.RndMean());
		RSLD_G3.Log(r, "ball -> plasma stream");
	}
	override void RiderDeath(RSLD_Rider r)
	{
		if (!r.child || !r.m) return;
		RSLD_G3.Silence(r.m, 4);
		r.m.A_StartSound("Plasma/Impact", CHAN_AUTO, CHANF_OVERLAP);
	}
}

class RSLD_ProtoStream : Thinker
{
	RSLD_Shot s;
	RSLD_Fx_Prototype fx;
	double ratio;
	int left, age;
	override void Tick()
	{
		age++;
		if (!s || !s.mo || s.mo.health <= 0) { Destroy(); return; }
		if (age == 1) return;	// AfterPull (the next WorldTick) knows what the shot took
		if (age == 2) { left = max(1, s.ammoTaken); if (RSLD.Debug()) s.Log(String.Format("Prototype stream: %d pairs (cells taken %d)", left, s.ammoTaken)); return; }
		if (left-- <= 0) { Destroy(); return; }
		let c = RSLD.AC("LDPrototypeBFGBallGreen"), c2 = RSLD.AC("LDPrototypeBFGBallGreen2");
		if (!c || !c2) { Destroy(); return; }
		Vector3 at; double a, p;
		[at, a, p] = RSLD_G2.Muzzle(s.mo, s.hand, s.mo.angle, s.mo.pitch);
		Ball(c, at, a, p);
		Ball(c2, at, a + frandom(-2, 2), p + frandom(-2, 2));
	}
	void Ball(class<Actor> c, Vector3 at, double a, double p)
	{
		let b = Actor.Spawn(c, at, NO_REPLACE);
		if (!b) return;
		b.target = s.mo; b.angle = a; b.pitch = p;
		b.Vel3DFromAngle(b.Speed, a, p);
		b.SetDamage(max(1, int(b.GetMissileDamage(0, 1) * ratio + 0.5)));	// x random(1,8) in flight, as LegenDoom's
		s.TagMissile(b);
		let r = RSLD_G3.Ride(s, b, fx, true);
	}
}

// Raycaster (E: RL): rockets emit BFG rays: A_BFGSpray("LDRaycasterRocketFlash", 20) at the blast, each ray target hit by
// A_Explode(64, 128) (half LegenDoom's rocket blast, its radius). Ours: 20 of BD22's BFG rays from our rocket, each
// target a blast of half our rocket blast over its radius (50 / 150), BFG/Fire (scope 4 effects/raycaster).
class RSLD_Fx_Raycaster : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky || !r.m) return;
		int d = int(RSLD_G3.BLAST_DMG * RSLD_G3.N("Raycaster", "expl") / RSLD_G3.N("Base3", "rk_expl") + 0.5);
		double rad = RSLD_G3.BLAST_RAD * RSLD_G3.N("Raycaster", "rad") / RSLD_G3.N("Base3", "rk_rad");
		r.m.A_StartSound("BFG/Fire", CHAN_AUTO, CHANF_OVERLAP);
		RSLD_G4.Spray(r.s, r.m, int(RSLD_G3.N("Raycaster", "rays")), 15, 90, d, rad, XF_HURTSOURCE, "Raycaster");
		RSLD_G3.Log(r, String.Format("%d rays, each target a blast of %d over %.0f", int(RSLD_G3.N("Raycaster", "rays")), d, rad));
	}
}

// Scattering (U: BF): "Fires BFG rays directly for less ammo": the ball (speed 0, damage 0) sprays at once from the gun
// and the shot takes 20 cells instead of 40. Ours: our ball is gone, BD22's 50 rays fly from the gun along the drawn
// barrel, and the shot gives back what LegenDoom saves (20 of 40: half of what ours took).
class RSLD_Fx_Scattering : RSLD_G4Fx
{
	override void RiderStart(RSLD_Rider r)
	{
		if (r.child || !r.m) return;
		double a, p;
		[a, p] = RSLD_G3.Dir(r.m);
		let b = RSLD_G3.BoomAt(r.s, r.m.pos, 0, 0, 0, 0, 1);	// a carrier for the spray: its angle, the player as target
		r.m.Destroy();
		if (!b) return;
		b.angle = a;
		RSLD_G4.Spray(r.s, b, RSLD_G4.OUR_RAYS);
		RSLD_G3.Log(r, String.Format("rays straight from the gun at %.1f", a));
	}
	override void AfterPull(RSLD_Shot s)
	{
		if (s.missiles <= 0 || s.ammoTaken <= 0) return;
		int back = s.ammoTaken - int(s.ammoTaken * RSLD_G3.N("Scattering", "cost") / RSLD_G3.N("Base3", "bfg_ammo") + 0.5);
		if (back > 0) s.Refund(back);
		s.Log(String.Format("Scattering: took %d, %d given back (LegenDoom %d of %d)", s.ammoTaken, back, int(RSLD_G3.N("Scattering", "cost")), int(RSLD_G3.N("Base3", "bfg_ammo"))));
	}
}

// Shockwave (U: BF): "Explodes instead of emitting BFG rays": A_Explode(600 x random(1,8), 256, 0) in place of 40 rays
// of 15 x random(1,8) (600 = 15 x 40). Ours: no rays; a blast of 15 x 50 x random(1,8) (our 50 rays) over 256, no self
class RSLD_Fx_Shockwave : RSLD_G4Fx
{
	override void RiderSpawn(RSLD_Rider r) { r.noRays = true; }
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky || !r.m) return;
		RSLD_G3.SkipSpray(r.m, r);
		int d = int(RSLD_G3.N("Shockwave", "dmg") * RSLD_G4.OUR_RAYS / RSLD_G3.N("Base3", "bfg_rays")) * random(1, 8);
		double rad = RSLD_G3.N("Shockwave", "rad");
		RSLD_G3.BoomAt(r.s, r.last, d, rad, 0, 0, 0, 'Desintegrate');
		RSLD_G3.Log(r, String.Format("shockwave %d over %.0f in place of the rays", d, rad));
	}
}

// Stasis (C: BF): "Does no damage, stuns enemies forever, bosses for a short time": the ball does Damage (0), no rays;
// LegenDoom's LDStasisEffect (LDStasisEffectBoss for bosses) on the enemy it hit (E). Ours: no damage at all, no
// rays; LegenDoom's stasis actor, its own sounds stopped, SLOWON on the enemy (scope 4 effects/stasis).
class RSLD_Fx_Stasis : RSLD_G4Fx
{
	override void RiderSpawn(RSLD_Rider r) { r.dmgMul = 0; r.noExpl = true; r.noRays = true; r.m.bHITTRACER = true; }
	override void RiderDeath(RSLD_Rider r)
	{
		if (!r.m) return;
		RSLD_G3.SkipSpray(r.m, r);
		let t = r.m.tracer;
		if (r.sky || !t || !t.bISMONSTER || t.health <= 0) { RSLD_G3.Log(r, "no enemy hit"); return; }
		let c = RSLD.AC(t.bBOSS ? "LDStasisEffectBoss" : "LDStasisEffect");
		if (!c) return;
		let e = Actor.Spawn(c, t.pos, NO_REPLACE);
		if (!e) return;
		e.target = r.s.mo; e.tracer = t;
		RSLD_G3.Silence(e, 12);
		t.A_StartSound("SLOWON", CHAN_AUTO, CHANF_OVERLAP);
		RSLD_G3.Log(r, String.Format("stasis on %s%s", t.GetClassName(), t.bBOSS ? " (boss: short)" : ""));
	}
}
