// LD mode, G3: LegenDoom's per-missile effects on OUR projectiles (round 3, agent R3a). Framework: g3_core.zs.
// Each class: what LegenDoom's projectile does (its class in decorate/*SpecialEffects.dec), and how it rides ours.
// Numbers: RSLD_G3.N(<effect>, <key>) from numbers_g3.zs (ldl_patch/tools/numbers/g3.rules: file:line each).
// Sounds: never LegenDoom's (scope section 4): Grenade/Bounce for bounces, our projectile's own sounds otherwise.

class RSLD_G3Util play
{
	// LegenDoom's ratio for a kind: <effect>.<rk|pl|bfg>_dmg (its fixed or x random(1,8) number) over its base attack
	static double FixedRatio(string eff, int kind)
	{
		return RSLD_G3.N(eff, RSLD_G3.KindKey(kind) .. "_dmg") / (RSLD_G3.LDBase(kind) * RSLD_G3.RndMean());
	}
	static double RandRatio(string eff, int kind)	// both x random(1,8): the plain ratio
	{
		return RSLD_G3.N(eff, RSLD_G3.KindKey(kind) .. "_dmg") / RSLD_G3.LDBase(kind);
	}
	// LegenDoom's Hexen bounce (BounceType "Hexen": walls, floors, ceilings, water) with our bounce sound
	static void HexenBounce(Actor m, int count, double factor, double wall)
	{
		m.bBOUNCEONWALLS = true; m.bBOUNCEONFLOORS = true; m.bBOUNCEONCEILINGS = true; m.bCANBOUNCEWATER = true;
		m.bouncecount = count; m.bouncefactor = factor; m.wallbouncefactor = wall;
		m.BounceSound = "Grenade/Bounce"; m.WallBounceSound = "Grenade/Bounce";	// scope 4: effects/bouncy* -> Grenade/Bounce
	}
	// a FastProjectile (our plasma) cannot bounce (fastprojectile.zs: a blocked move explodes it): it becomes an
	// RSLD_ProjProxy (an ordinary projectile drawn with the plasma's own frames, our damage, our death and sound)
	static Actor Bounceable(RSLD_Rider r)
	{
		if (!r.m || !(r.m is "FastProjectile")) return r.m;
		let p = RSLD_ProjProxy.Make(r.m);
		if (!p) return r.m;
		r.m = p;
		r.prevBounce = p.bouncecount;
		let h = RSLD.H();
		if (h && r.s) h.Tag(p, r.s);
		RSLD_G3.Log(r, "plasma ball -> bounce-capable copy (FastProjectile cannot bounce)");
		return p;
	}
	static bool Still(Actor m, double lim) { return abs(m.vel.x) < lim && abs(m.vel.y) < lim && abs(m.vel.z) < lim; }
	// round 4 (owner: "speeds scaled to our rocket"): our projectile's speed over LegenDoom's class's (both read at run time)
	static double SpeedRatio(RSLD_Rider r, string ldCls)
	{
		class<Actor> lc = RSLD.AC(ldCls);
		if (!r || !r.cls || !lc) return 1;
		double ours = GetDefaultByType(r.cls).Speed, ld = GetDefaultByType(lc).Speed;
		return (ours > 0 && ld > 0) ? ours / ld : 1;
	}
}

// a plasma ball that can bounce: the same frames, size, damage (DoSpecialDamage: our ball's fixed number), death and sound
class RSLD_ProjProxy : Actor
{
	State ost;
	int otics, fixedDmg;
	class<Actor> orig;
	bool done;

	Default
	{
		Projectile;
		Radius 10;
		Height 2;
		Damage 1;
		RenderStyle "Add";
		Alpha 0.99;
		+FORCEXYBILLBOARD
		+BRIGHT
		+NOBLOOD
		+SPECTRAL
	}

	static RSLD_ProjProxy Make(Actor o)
	{
		let p = RSLD_ProjProxy(Actor.Spawn("RSLD_ProjProxy", o.pos, NO_REPLACE));
		if (!p) return null;
		p.target = o.target; p.angle = o.angle; p.pitch = o.pitch; p.vel = o.vel; p.Speed = o.Speed;
		p.scale = o.scale; p.Alpha = o.Alpha; p.DamageType = o.DamageType; p.Species = o.Species;
		p.bTHRUSPECIES = o.bTHRUSPECIES; p.bMTHRUSPECIES = o.bMTHRUSPECIES; p.bRIPPER = o.bRIPPER;
		p.fixedDmg = o.GetMissileDamage(0, 1);
		p.orig = o.GetClass();
		p.ost = o.SpawnState; p.otics = p.ost ? max(1, p.ost.tics) : 1;
		p.DeathSound = "";
		o.Destroy();
		return p;
	}

	override int DoSpecialDamage(Actor victim, int damage, Name damagetype) { return fixedDmg > 0 ? fixedDmg : damage; }

	override void Tick()
	{
		Super.Tick();
		if (bMISSILE && ost)
		{
			if (--otics <= 0) { ost = ost.NextState ? ost.NextState : ost; otics = max(1, ost.tics); }
			sprite = ost.sprite; frame = ost.Frame;
		}
		else if (!bMISSILE && !done)
		{	// its death: our ball's own death (frames, Plasma/Impact) where it burst
			done = true;
			if (orig)
			{
				let d = Actor.Spawn(orig, pos, NO_REPLACE);
				if (d) { d.target = target; d.vel = (0, 0, 0); d.ExplodeMissile(); }
			}
			bINVISIBLE = true;
		}
	}

	States
	{
	Spawn:
		TNT1 A 1;
		Loop;
	Death:
		TNT1 A 2;
		Stop;
	}
}

// ------------------------------------------------------------------ Common

// Kinetic (C: RL, BF): "Projectiles do not explode, instead do all impact damage". LegenDoom: LDKineticRocket
// Damage (20 x random(1,8)) + 128 with no A_Explode; LDKineticBFGBall 100 x random(1,8) + random(1,8) x 15 x 40 and no rays.
// Ours: our blast (rocket: BD22's RocketExplosion 100/150; BFG: the ball's A_Explode(200,400)) and our rays (50 x
// 15 x random(1,8)) moved onto the direct hit; no splash, no rays.
class RSLD_Fx_Kinetic : RSLD_G3Fx
{
	const BFG_BLAST = 200;		// brutal22test6 BFG.dec SuperBFGBall Death A_Explode(200,400)
	const BFG_RAYS = 50;		// BFG.dec A_BFGSpray("SuperBFGExtra", 50)
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE || k == RSLD_G3.K_BFG; }
	override void RiderSpawn(RSLD_Rider r)
	{
		r.noExpl = true;
		if (r.kind == RSLD_G3.K_BFG) { r.noRays = true; r.directAdd = BFG_BLAST; }
		else r.directAdd = RSLD_G3.BLAST_DMG;	// LegenDoom's +128 = its own blast (Kinetic.rk_add): ours is 100
		RSLD_G3.Log(r, String.Format("no splash; +%d onto the direct hit (LegenDoom +%d)", r.directAdd, int(RSLD_G3.N("Kinetic", "rk_add"))));
	}
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.kind == RSLD_G3.K_BFG && RSLD_G3.SkipSpray(r.m, r)) RSLD_G3.Log(r, "rays skipped (moved onto the hit)");
	}
	override void RiderDamage(RSLD_Shot s, RSLD_Hit h, RSLD_Rider r)
	{
		if (!r || r.kind != RSLD_G3.K_BFG || (h.flags & DMG_EXPLOSION) || h.inflictor != r.m || h.damage <= 0) return;
		int rays = random(1, 8) * int(RSLD_G3.N("Base3", "bfg_raydmg")) * BFG_RAYS;	// LegenDoom: random(1,8) x 15 x 40 (its 40 rays)
		h.mult *= (h.damage * h.mult + rays) / max(1.0, h.damage * h.mult);
		s.Log(String.Format("Kinetic BFG direct hit +%d (the rays)", rays));
	}
}

// Penetrating (C: RL, PR, BF): +RIPPER, fixed Damage (20) / (5) / (100) where its base is that x random(1,8):
// ours x 20 / 90 on every rip; the rocket keeps its blast (LDPenetratingRocket Death A_Explode(128,128)), the BFG its rays.
class RSLD_Fx_Penetrating : RSLD_G3Fx
{
	override void RiderSpawn(RSLD_Rider r)
	{
		r.m.bRIPPER = true;
		r.dmgMul = RSLD_G3Util.FixedRatio("Penetrating", r.kind);
		RSLD_G3.Log(r, String.Format("RIPPER, direct x%.3f (%d -> %d a rip)", r.dmgMul, r.ourDirect, int(r.ourDirect * r.dmgMul)));
	}
}

// Tricky (C: RL, PR, BF): bounces off surfaces (BounceType Hexen, 4 bounces, factor 1.0 / 1.0)
class RSLD_Fx_Tricky : RSLD_G3Fx
{
	override void RiderStart(RSLD_Rider r)
	{
		let m = RSLD_G3Util.Bounceable(r);
		RSLD_G3Util.HexenBounce(m, int(RSLD_G3.N("Tricky", "count")), RSLD_G3.N("Tricky", "factor"), RSLD_G3.N("Tricky", "wall"));
		r.prevBounce = m.bouncecount;
		RSLD_G3.Log(r, String.Format("bounces %d", m.bouncecount));
	}
	override void RiderTick(RSLD_Rider r, bool bounced) { if (bounced) RSLD_G3.Log(r, String.Format("bounce %d", r.bounces)); }
}

// Spreadfire (C: RL, PR, BF): three smaller projectiles (scale 0.33, damage / 3, blast 42/42), +-5 degrees, flat and
// upright in turn (LDSpreadfireMode). Ours: our projectile becomes the middle one, two of our class at its side.
// The BFG's side balls fire no rays (LDSpreadfireBFGBall2 PraySprayRay: nothing).
class RSLD_Fx_Spreadfire : RSLD_G3Fx
{
	override void RiderStart(RSLD_Rider r)
	{
		if (r.child || !r.m) return;
		double div = RSLD_G3.N("Spreadfire", "div"), sc = RSLD_G3.N("Spreadfire", "scale"), off = RSLD_G3.N("Spreadfire", "angle");
		double bm = RSLD_G3.N("Spreadfire", "expl") / RSLD_G3.N("Base3", "rk_expl");
		r.dmgMul = 1 / div; r.explDmgMul = bm; r.explRadMul = bm;
		r.m.scale *= sc;
		let g = RSLD_G3.Reg();
		int pn = r.s.pn;
		if (!r.s.b2) { r.s.b2 = true; g.spreadMode[pn] = !g.spreadMode[pn]; }	// once per pull
		bool upright = !g.spreadMode[pn];
		double a, p;
		[a, p] = RSLD_G3.Dir(r.m);
		double sp = r.m.vel.Length();
		for (int i = -1; i <= 1; i += 2)
		{
			let c = RSLD_G3.Child(r, r.m.pos, upright ? a : a + i * off, upright ? p + i * off : p, sp, 1 / div, sc);
			let cr = RSLD_G3.RiderOf(c);
			if (cr) { cr.explDmgMul = bm; cr.explRadMul = bm; cr.noRays = true; }
		}
		RSLD_G3.Log(r, String.Format("%s spread of 3, each x%.2f, blast x%.2f", upright ? "upright" : "flat", 1 / div, bm));
	}
	override void RiderDeath(RSLD_Rider r) { if (r.child && r.noRays && r.kind == RSLD_G3.K_BFG) RSLD_G3.SkipSpray(r.m, r); }
}

// ------------------------------------------------------------------ Uncommon

// Cluster (U: RL, PR, BF): bursts into six minis (30 + 60k degrees, 20 a tic: LDClusterRocket Death). Minis: rocket
// Damage 10 + A_Explode(64,64), plasma 2, BFG 40 with 20 rays of 7 over 360 degrees. Ours: our class, those ratios,
// speed 20 x our speed / LegenDoom's (vanilla Rocket 20, PlasmaBall 25, BFGBall 25: gzdoom.pk3 doom weapons).
class RSLD_Fx_Cluster : RSLD_G3Fx
{
	static double LDSpeed(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE ? 20 : 25; }
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.child)
		{
			if (r.kind == RSLD_G3.K_BFG && RSLD_G3.SkipSpray(r.m, r)) r.b1 = true;	// its own small spray, 2 tics on
			return;
		}
		if (r.sky) return;
		string kk = RSLD_G3.KindKey(r.kind);
		double mul = RSLD_G3.N("Cluster", kk .. "_dmg") / RSLD_G3.LDBase(r.kind);
		double bm = RSLD_G3.N("Cluster", "rk_expl") / RSLD_G3.N("Base3", "rk_expl");
		let def = GetDefaultByType(r.cls);
		double sp = RSLD_G3.N("Cluster", "vel") * def.Speed / LDSpeed(r.kind);
		double a0 = r.m ? r.m.angle : 0, first = RSLD_G3.N("Cluster", "first"), step = RSLD_G3.N("Cluster", "second") - first;
		Vector3 at = r.last;
		for (int i = 0; i < 6; i++)
		{
			let c = RSLD_G3.Child(r, at, a0 + first + step * i, 0, sp, mul, RSLD_G3.N("Cluster", "scale"));
			let cr = RSLD_G3.RiderOf(c);
			if (cr) { cr.explDmgMul = bm; cr.explRadMul = bm; }
		}
		RSLD_G3.Log(r, String.Format("burst into 6 minis (x%.2f, blast x%.2f, speed %.0f)", mul, bm, sp));
	}
	override void RiderAfter(RSLD_Rider r)
	{
		if (!r.child || !r.b1 || r.deadAge != 2 || !r.m) return;
		r.b1 = false;
		let c = RSLD.AC("SuperBFGExtra");
		int rays = int(RSLD_G3.N("Cluster", "bfg_rays") * RSLD_G4.OUR_RAYS / RSLD_G3.N("Base3", "bfg_rays") + 0.5);
		if (c) r.m.A_BFGSpray(c, rays, int(RSLD_G3.N("Cluster", "bfg_raydmg")), RSLD_G3.N("Cluster", "bfg_fov"));
		RSLD_G3.Log(r, String.Format("mini ball: %d rays of %d over %d degrees", rays, int(RSLD_G3.N("Cluster", "bfg_raydmg")), int(RSLD_G3.N("Cluster", "bfg_fov"))));
	}
}

// Redirecting (U: RL, PR, BF): two Hexen bounces (factor 1); the first one turns it toward an enemy
// (A_SeekerMissile(90, 90, SMF_LOOK | SMF_PRECISE, 256) x4)
class RSLD_Fx_Redirecting : RSLD_G3Fx
{
	override void RiderStart(RSLD_Rider r)
	{
		let m = RSLD_G3Util.Bounceable(r);
		RSLD_G3Util.HexenBounce(m, int(RSLD_G3.N("Redirecting", "count")), 1.0, 1.0);
		r.prevBounce = m.bouncecount;
	}
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		if (!bounced || r.bounces != 1 || !r.m) return;
		int t = int(RSLD_G3.N("Redirecting", "turn")), ch = int(RSLD_G3.N("Redirecting", "chance"));
		r.m.bSEEKERMISSILE = true;
		r.m.tracer = null;
		for (int i = 0; i < 4; i++) r.m.A_SeekerMissile(t, t, SMF_LOOK | SMF_PRECISE, ch);
		RSLD_G3.Log(r, String.Format("bounced: turned toward %s", r.m.tracer ? r.m.tracer.GetClassName() : 'nothing'));
	}
}

// Mysterious (U: RL, PR, BF): "It is a mystery": a random jump of +-32 on each axis every 13 tics (A_Warp), the first
// after 2 to 12. The flight direction is kept (LegenDoom's angle change only turns a billboard sprite).
class RSLD_Fx_Mysterious : RSLD_G3Fx
{
	override void RiderSpawn(RSLD_Rider r) { r.i1 = random(2, 12); }
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		if (r.age < r.i1 || !r.m) return;
		r.i1 = r.age + int(RSLD_G3.N("Mysterious", "period"));
		double d = RSLD_G3.N("Mysterious", "dist");
		bool ok = r.m.Warp(r.m, frandom(-d, d), frandom(-d, d), frandom(-d, d), 0, WARPF_INTERPOLATE);
		if (RSLD.DebugLevel() > 1 || r.age < 20) RSLD_G3.Log(r, ok ? "jumped" : "jump blocked");
	}
}

// Bouncy (U: RL, PR, BF): starts bouncing on impact (Hexen, factor 0.7 / 0.75, 4 bounces); gravity after the first
class RSLD_Fx_Bouncy : RSLD_G3Fx
{
	override void RiderStart(RSLD_Rider r)
	{
		let m = RSLD_G3Util.Bounceable(r);
		RSLD_G3Util.HexenBounce(m, int(RSLD_G3.N("Bouncy", "count")), RSLD_G3.N("Bouncy", "factor"), RSLD_G3.N("Bouncy", "wall"));
		r.prevBounce = m.bouncecount;
	}
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		if (!bounced || !r.m) return;
		r.m.bNOGRAVITY = false;
		RSLD_G3.Log(r, String.Format("bounce %d: falls now", r.bounces));
	}
}

// Sluggish (U: RL, PR, BF): x0.98 a tic, RIPPER, damage (20) x clamp(speed / 8, 0.05, 1) (LEGNDLIB.acs
// LDSluggishDamageScaling_*), detonates when every axis is under 1 a tic. Ours: our direct x 20 / 90 x that factor.
class RSLD_Fx_Sluggish : RSLD_G3Fx
{
	override void RiderSpawn(RSLD_Rider r)
	{
		r.m.bRIPPER = true;
		r.dmgMul = RSLD_G3.LDBase(r.kind) / (RSLD_G3.LDBase(r.kind) * RSLD_G3.RndMean());	// its fixed base / the random base
	}
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		r.m.A_ScaleVelocity(RSLD_G3.N("Sluggish", "scale"));
		if (RSLD_G3Util.Still(r.m, RSLD_G3.N("Sluggish", "stop")))
		{
			RSLD_G3.Log(r, String.Format("stopped after %d tics: detonates", r.age));
			r.m.bTHRUACTORS = true; r.m.bNOCLIP = true; r.m.A_Stop();
			r.m.ExplodeMissile();
		}
	}
	override void RiderDamage(RSLD_Shot s, RSLD_Hit h, RSLD_Rider r)
	{
		if (!r || h.inflictor != r.m || (h.flags & DMG_EXPLOSION)) return;
		double f = clamp(r.m.vel.Length() / RSLD_G3.N("Sluggish", "vfull"), RSLD_G3.N("Sluggish", "vmin"), 1.0);
		h.mult *= f;
		if (RSLD.DebugLevel() > 1) s.Log(String.Format("Sluggish speed %.1f: damage x%.2f", r.m.vel.Length(), f));
	}
}

// Hyper (U: RL, PR, BF): A_ScaleVelocity(1.05) every tic
class RSLD_Fx_Hyper : RSLD_G3Fx
{
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		r.m.A_ScaleVelocity(RSLD_G3.N("Hyper", "scale"));
		if (r.age == 10 || r.age == 30) RSLD_G3.Log(r, String.Format("speed %.0f after %d tics", r.m.vel.Length(), r.age));
	}
}

// Arcing (U: RL): a bouncing grenade: gravity 0.15, BounceType Doom (0.4 / 0.8, 5 bounces), goes off after 139 tics.
// Owner, round 4: "Arcing / Proximity: speeds scaled to our rocket". LegenDoom's arc is its LDArcingRocket's (speed 20,
// read at run time from its class) under gravity 0.15 for 139 tics; our rocket flies k = our speed / its speed as fast
// (Rocket2 50: k 2.5), so the same arc at our speed: gravity x k^2, the fuse / k (the path is LegenDoom's, flown k
// times faster; bounces as LegenDoom's).
class RSLD_Fx_Arcing : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	override void RiderStart(RSLD_Rider r)
	{
		let m = r.m;
		double k = RSLD_G3Util.SpeedRatio(r, "LDArcingRocket");
		r.d1 = k;
		m.bNOGRAVITY = false; m.Gravity = RSLD_G3.N("Arcing", "gravity") * k * k;
		m.bBOUNCEONWALLS = true; m.bBOUNCEONFLOORS = true; m.bBOUNCEONCEILINGS = true; m.bBOUNCEAUTOOFF = true;
		m.bouncecount = int(RSLD_G3.N("Arcing", "count")); m.bouncefactor = RSLD_G3.N("Arcing", "factor"); m.wallbouncefactor = RSLD_G3.N("Arcing", "wall");
		m.BounceSound = "Grenade/Bounce"; m.WallBounceSound = "Grenade/Bounce";
		r.prevBounce = m.bouncecount;
		RSLD_G3.Log(r, String.Format("grenade at our speed (x%.2f LegenDoom's): gravity %.2f (LegenDoom's %.2f x %.2f^2), %d bounces, fuse %d tics (%d / %.2f)",
			k, m.Gravity, RSLD_G3.N("Arcing", "gravity"), k, m.bouncecount, Fuse(r), int(RSLD_G3.N("Arcing", "life")), k));
	}
	static int Fuse(RSLD_Rider r) { return max(1, int(RSLD_G3.N("Arcing", "life") / max(0.01, r.d1) + 0.5)); }
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		if (bounced) RSLD_G3.Log(r, String.Format("bounce %d at tic %d", r.bounces, r.age));
		if (r.age >= Fuse(r)) { RSLD_G3.Log(r, String.Format("fuse: goes off after %d tics, %.0f from where it left", r.age, (r.m.pos - r.from).Length())); r.m.ExplodeMissile(); }
	}
}

// GroupTherapy (U: RL): no splash, its blast moved onto the hit ((20 x random(1,8)) + 128); a kill makes every enemy
// within 512 (in sight of it) explode: LDGroupTherapyExplosion, 20 x random(1,8) on it + A_Explode(128,128, no self).
// Ours: direct + our 100, no splash; each chained enemy: our direct x random(1,8) / 4.5 on it + our blast 100/150 (no
// self), LegenDoom's explosion visual, Barrel/explode (scope 4).
class RSLD_Fx_GroupTherapy : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	override void RiderSpawn(RSLD_Rider r) { r.noExpl = true; r.directAdd = RSLD_G3.BLAST_DMG; }
	override void OnKill(RSLD_Shot s, RSLD_Hit h)
	{
		let r = RSLD_G3.RiderOf(h.inflictor);
		if (!r || h.inflictor != r.m || !h.target) return;
		double rad = RSLD_G3.N("GroupTherapy", "radius");
		Array<Actor> l;
		let it = BlockThingsIterator.Create(h.target, rad);
		while (it.Next())
		{
			let a = it.thing;
			if (!a || a == h.target || !a.bISMONSTER || !a.bSHOOTABLE || a.health <= 0 || h.target.Distance3D(a) > rad) continue;	// RGF_MONSTERS: any monster
			if (!h.target.CheckSight(a)) continue;
			l.Push(a);
		}
		double ratio = r.ourDirect / (RSLD_G3.LDBase(RSLD_G3.K_ROCKET) * RSLD_G3.RndMean());
		for (int i = 0; i < l.Size(); i++)
		{
			let a = l[i];
			Vector3 at = a.pos + (0, 0, a.Height * 0.5);
			let b = RSLD_G3.BoomAt(s, at, RSLD_G3.BLAST_DMG, RSLD_G3.BLAST_RAD, 0, 0, 0, 'ExplosiveImpact', 0, "Barrel/explode");
			if (b) a.DamageMobj(b, s.mo, int(RSLD_G3.N("GroupTherapy", "hit") * ratio * random(1, 8)), 'ExplosiveImpact');
			RSLD.LDVisual("LDGroupTherapyExplosion", at, "XDeath", 5, s.mo);
		}
		s.Log(String.Format("kill: %d enemies within %d explode", l.Size(), int(rad)));
	}
}

// Proximity (U: RL, PR, BF): "stationary projectiles that float towards nearby enemies": speed 40, x0.9 a tic until
// still, then speed 2 (plasma 5, BFG 1): looks for an enemy (A_SeekerMissile(90,90, SMF_LOOK|SMF_CURSPEED, 256, 4)),
// drifts to it within 256 (A_Recoil(-0.5) + 3 tics of seeking), else brakes (x0.5 x3) and stops. Owner, round 4: "speeds
// scaled to our rocket": its launch speed, drift and pull x k = our projectile's speed / LegenDoom's for that kind
// (LDRocket / LDPlasmaBall / LDBFGBall, read at run time: Rocket2 50 / 20, Plasma_Ball 60 / 25); its slowing ratios, its
// look and reach (distances) as LegenDoom's.
class RSLD_Fx_Proximity : RSLD_G3Fx
{
	static string LDKind(int kind) { return kind == RSLD_G3.K_PLASMA ? "LDPlasmaBall" : (kind == RSLD_G3.K_BFG ? "LDBFGBall" : "LDRocket"); }
	static double Drift(int kind) { return kind == RSLD_G3.K_PLASMA ? RSLD_G3.N("Proximity", "drift_pl") : (kind == RSLD_G3.K_BFG ? RSLD_G3.N("Proximity", "drift_bf") : RSLD_G3.N("Proximity", "drift")); }
	override void RiderStart(RSLD_Rider r)
	{
		let m = r.m;
		m.bSEEKERMISSILE = true; m.bFLOATBOB = true;
		double a, p;
		[a, p] = RSLD_G3.Dir(m);
		r.d1 = RSLD_G3Util.SpeedRatio(r, LDKind(r.kind));
		m.Vel3DFromAngle(RSLD_G3.N("Proximity", "speed") * r.d1, a, p);
		RSLD_G3.Log(r, String.Format("launched at %.0f (LegenDoom's %.0f x %.2f, our speed over its %s's), drift %.1f", RSLD_G3.N("Proximity", "speed") * r.d1, RSLD_G3.N("Proximity", "speed"), r.d1, LDKind(r.kind), Drift(r.kind) * r.d1));
	}
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		let m = r.m;
		if (r.i1 == 0)
		{
			m.A_ScaleVelocity(RSLD_G3.N("Proximity", "decel"));
			if (RSLD_G3Util.Still(m, max(1.0, r.d1))) { m.A_Stop(); m.Speed = Drift(r.kind) * r.d1; r.i1 = 1; RSLD_G3.Log(r, String.Format("deployed after %d tics, %.0f from the muzzle", r.age, (m.pos - r.from).Length())); }
			return;
		}
		int look = int(RSLD_G3.N("Proximity", "look"));
		if (r.i2 > 0)
		{	// drifting toward its target (Follow: 3 tics of seeking)
			m.A_SeekerMissile(90, 90, SMF_LOOK | SMF_CURSPEED, 256, look);
			r.i2--;
			return;
		}
		if (r.i3 > 0)
		{	// braking (3 tics x0.5), then a stop
			m.A_ScaleVelocity(RSLD_G3.N("Proximity", "brake"));
			if (--r.i3 == 0) m.A_Stop();
			return;
		}
		m.tracer = null;
		m.A_SeekerMissile(90, 90, SMF_LOOK | SMF_CURSPEED, 256, look);
		if (m.tracer && m.Distance3D(m.tracer) < RSLD_G3.N("Proximity", "reach"))
		{
			m.angle = m.AngleTo(m.tracer);
			m.A_Recoil(RSLD_G3.N("Proximity", "pull") * r.d1);
			r.i2 = 3;
			if (!r.b1) { r.b1 = true; RSLD_G3.Log(r, String.Format("drifts to %s", m.tracer.GetClassName())); }
		}
		else r.i3 = 3;
	}
}

// Illuminating (U: RL, PR, BF): LegenDoom's big lights on the projectile (LDROCK_ILLUM flicker 96/144, LDPLASMABALL1_ILLUM
// 192, LDBFGBALL1_ILLUM 800: lights/*.light) and an idle glow on the player while the gun is held
// (LDIlluminatingIdle_<kind> pulse 120/180). Dynamic lights cost on the Quest (scope 5): one light a projectile.
class RSLD_Fx_Illuminating : RSLD_G3Fx
{
	static Color Col(string k) { return Color(255, int(255 * RSLD_G3.N("Illuminating", k .. "_r")), int(255 * RSLD_G3.N("Illuminating", k .. "_g")), int(255 * RSLD_G3.N("Illuminating", k .. "_b"))); }
	override void RiderSpawn(RSLD_Rider r)
	{
		let m = r.m;
		if (r.kind == RSLD_G3.K_PLASMA)
			m.A_AttachLight('rsld_illum', DynamicLight.PointLight, Col("pl"), int(RSLD_G3.N("Illuminating", "pl_size")), 0);
		else if (r.kind == RSLD_G3.K_BFG)
			m.A_AttachLight('rsld_illum', DynamicLight.PointLight, Col("bfg"), int(RSLD_G3.N("Illuminating", "bfg_size")), 0);
		else
			m.A_AttachLight('rsld_illum', DynamicLight.FlickerLight, Col("rk"), int(RSLD_G3.N("Illuminating", "rk_size")), int(RSLD_G3.N("Illuminating", "rk_size2")), 0, (0, 0, 0), RSLD_G3.N("Illuminating", "rk_chance"));
		RSLD_G3.Log(r, "lit");
	}
	override void WhileHeld(RSLD_Held c)
	{
		string k = c.slot == 7 ? "idlePlasma" : (c.slot == 8 ? "idleBFG" : "idleRocket");
		RSLD_G3.Reg().Glow(c.mo, Col(k), int(RSLD_G3.N("Illuminating", k .. "_size")), int(RSLD_G3.N("Illuminating", k .. "_size2")), RSLD_G3.N("Illuminating", k .. "_interval"));
	}
}

// ------------------------------------------------------------------ Rare

// Seeker (R: RL, PR, BF): A_SeekerMissile(5, 5, SMF_LOOK | SMF_PRECISE, 256, 20) every tic. BD22 VR's lock-on alt
// fire stands down on a Seeker rocket launcher (owner round 3, Q12: g6_ammo.zs RSLD_AltDown).
class RSLD_Fx_Seeker : RSLD_G3Fx
{
	override void RiderSpawn(RSLD_Rider r) { r.m.bSEEKERMISSILE = true; }
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		int t = int(RSLD_G3.N("Seeker", "turn"));
		Actor before = r.m.tracer;
		r.m.A_SeekerMissile(t, t, SMF_LOOK | SMF_PRECISE, 256, int(RSLD_G3.N("Seeker", "look")));
		if (r.m && r.m.tracer && r.m.tracer != before) RSLD_G3.Log(r, String.Format("seeks %s", r.m.tracer.GetClassName()));
	}
}

// Accelerator (R: RL, PR, BF): "Fires instant hitting attacks": LegenDoom's rocket fires a hitscan of the rocket's
// 20 x random(1,8) whose puff explodes 128/128 (the rocket's own blast). Ours, all in ZScript (no fire-state change):
// on its first tic our projectile hits at once along its flight line: its own direct damage on what the line meets,
// then it is put at the impact point and goes off there (our blast, our visuals and sounds). Nothing met: it is gone.
class RSLD_Fx_Accelerator : RSLD_G3Fx
{
	override void RiderStart(RSLD_Rider r)
	{
		let m = r.m;
		if (!m || r.child) return;
		double a, p;
		[a, p] = RSLD_G3.Dir(m);
		FLineTraceData t;
		Vector3 from = m.pos - m.vel;	// where it was spawned (it moved one step this tic)
		m.SetOrigin(from, false);
		bool hit = m.LineTrace(a, 8192, p, TRF_THRUSPECIES, 0, 0, 0, t);
		if (!hit || t.HitType == TRACE_HitNone || t.HitType == TRACE_HasHitSky)
		{
			RSLD_G3.Log(r, "instant: nothing in line");
			m.Destroy();
			return;
		}
		Vector3 dir = (cos(a) * cos(p), sin(a) * cos(p), -sin(p));
		m.SetOrigin(t.HitLocation - dir * 2, false);
		m.vel = (0, 0, 0);
		Actor v = t.HitType == TRACE_HitActor ? t.HitActor : null;
		if (v && v.bSHOOTABLE) v.DamageMobj(m, m.target, m.GetMissileDamage(7, 1), m.DamageType);
		RSLD_G3.Log(r, String.Format("instant hit %s at %.0f", v ? v.GetClassName() : 'wall', t.Distance));
		if (m) m.ExplodeMissile(t.HitLine, v);
	}
}

// Vidmaster (R: RL): full damage over the whole radius (A_Explode(128, 128, 1, 0, 128), +FORCERADIUSDMG);
// LegenDoom's vidmasterexplode -> Devastator/explode (scope 4)
class RSLD_Fx_Vidmaster : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	override void RiderSpawn(RSLD_Rider r) { r.explFull = true; }
	override void RiderBlast(RSLD_Rider r, Actor a)
	{
		Vector3 at = a.pos;
		Super.RiderBlast(r, a);
		let b = RSLD_Boom(Actor.Spawn("RSLD_Boom", at, NO_REPLACE));
		if (b) { b.vis = 0; b.delay = RSLD_G3.BLAST_DELAY; b.snd = "Devastator/explode"; }
	}
}

// HighExplosive (R: RL): "Explosions are twice as big": radius 128 -> 256
class RSLD_Fx_HighExplosive : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	override void RiderSpawn(RSLD_Rider r) { r.explRadMul = RSLD_G3.N("HighExplosive", "rad") / RSLD_G3.N("Base3", "rk_rad"); }
}

// ShapedCharge (R: RL): "Explosions won't harm owner": A_Explode(128, 128, 0)
class RSLD_Fx_ShapedCharge : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	override void RiderSpawn(RSLD_Rider r) { r.explNoSelf = RSLD_G3.N("ShapedCharge", "flags") == 0; }
}

// Spamtastic (R: RL, PR, BF): each tic a 26-in-256 chance (A_Jump(230) skips it) of a third-damage mini (scale 0.33,
// blast 42/42) at a random angle (0..359 off its own) and pitch (-90..90)
class RSLD_Fx_Spamtastic : RSLD_G3Fx
{
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		if (r.child || random(0, 255) < int(RSLD_G3.N("Spamtastic", "skip"))) return;
		double div = RSLD_G3.N("Spamtastic", "div");
		double bm = RSLD_G3.N("Spamtastic", "expl") / RSLD_G3.N("Base3", "rk_expl");
		let def = GetDefaultByType(r.cls);
		let c = RSLD_G3.Child(r, r.m.pos, r.m.angle + random(0, 359), random(-90, 90), def.Speed, 1 / div, RSLD_G3.N("Spamtastic", "scale"));
		let cr = RSLD_G3.RiderOf(c);
		if (cr) { cr.explDmgMul = bm; cr.explRadMul = bm; cr.noRays = true; }
		r.i1++;
		if (r.i1 == 1 || RSLD.DebugLevel() > 1) RSLD_G3.Log(r, String.Format("mini %d (x%.2f)", r.i1, 1 / div));
	}
	override void RiderDeath(RSLD_Rider r) { if (r.child && r.kind == RSLD_G3.K_BFG) RSLD_G3.SkipSpray(r.m, r); }
}

// Concentrating (R: RL, PR, BF): +1 a tic (up to 1000), damage x (count + 100) / 100, the blast + that factor
class RSLD_Fx_Concentrating : RSLD_G3Fx
{
	override void RiderTick(RSLD_Rider r, bool bounced) { r.i1 = min(r.i1 + 1, int(RSLD_G3.N("Concentrating", "max"))); }
	override void RiderDeath(RSLD_Rider r)
	{
		double f = (r.i1 + RSLD_G3.N("Concentrating", "base")) / RSLD_G3.N("Concentrating", "base");
		r.explAdd = int(f);
		RSLD_G3.Log(r, String.Format("flew %d tics: x%.2f", r.i1, f));
	}
	override void RiderDamage(RSLD_Shot s, RSLD_Hit h, RSLD_Rider r)
	{
		if (!r || h.inflictor != r.m || (h.flags & DMG_EXPLOSION)) return;
		h.mult *= (r.i1 + RSLD_G3.N("Concentrating", "base")) / RSLD_G3.N("Concentrating", "base");
	}
}

// Vacuum (R: RL, PR, BF): A_RadiusThrust(-160, 1024, 0) every tic (pulls enemies in; not the shooter)
class RSLD_Fx_Vacuum : RSLD_G3Fx
{
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		r.m.A_RadiusThrust(int(RSLD_G3.N("Vacuum", "force")), RSLD_G3.N("Vacuum", "range"), 0);
		if (r.age == 1) RSLD_G3.Log(r, "pulling");
	}
}

// TORGUE (R: RL): blast x2 (256/256); the hit enemy and every enemy within 300 (in sight) explode when they die
// (LDTORGUEExplosion: A_Explode(128,128, no self)). Ours: our blast x2 / x2; the chain blast our 100/150, LegenDoom's
// explosion visual, Explode1 (scope 4).
class RSLD_Fx_TORGUE : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	override void RiderSpawn(RSLD_Rider r)
	{
		r.explDmgMul = RSLD_G3.N("TORGUE", "expl") / RSLD_G3.N("Base3", "rk_expl");
		r.explRadMul = RSLD_G3.N("TORGUE", "rad") / RSLD_G3.N("Base3", "rk_rad");
		r.m.bHITTRACER = true;
	}
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky) return;
		let g = RSLD_G3.Reg();
		int n = 0;
		if (r.m && r.m.tracer && r.m.tracer.bISMONSTER && r.m.tracer.health > 0) { g.Mark(r.m.tracer, r.s); n++; }
		double rad = RSLD_G3.N("TORGUE", "give");
		let it = BlockThingsIterator.CreateFromPos(r.last.x, r.last.y, r.last.z, r.last.z + 64, rad, false);
		while (it.Next())
		{
			let a = it.thing;
			if (!a || !a.bISMONSTER || a.health <= 0 || (a.pos - r.last).Length() > rad) continue;	// RGF_MONSTERS: any monster
			if (r.m && !r.m.CheckSight(a)) continue;
			if (g.Mark(a, r.s)) n++;
		}
		RSLD_G3.Log(r, String.Format("%d enemies marked to explode on death", n));
	}
}

// Irradiated (E: RL, PR, BF): a pulse of its base x random(1,8) over 256 (full damage, not the shooter) at 0 and 17 of
// every 35 tics, radiation particles (LegenDoom's visual). Ours: our direct x random(1,8) / 4.5 a pulse;
// effects/irradiated -> rsb/impact/electric1-5 (scope 4 proposal) with every second pulse, as LegenDoom.
class RSLD_Fx_Irradiated : RSLD_G3Fx
{
	override void RiderTick(RSLD_Rider r, bool bounced)
	{
		int t = (r.age - 1) % int(RSLD_G3.N("Irradiated", "period"));
		if (t % 5 == 0) Particle(r.m, 1);
		if (t != 0 && t != 17) return;
		double rad = RSLD_G3.N("Irradiated", "rad");
		int dmg = int(r.ourDirect * random(1, 8) / RSLD_G3.RndMean() + 0.5);
		string snd = t == 17 ? String.Format("rsb/impact/electric%d", random(1, 5)) : "";
		RSLD_G3.BoomAt(r.s, r.m.pos, dmg, rad, rad, 0, 0, r.m.DamageType, 0, snd);
		if (t == 17) Particle(r.m, 10);
		r.i1++;
		if (r.i1 <= 2 || RSLD.DebugLevel() > 1) RSLD_G3.Log(r, String.Format("pulse %d: %d over %.0f", r.i1, dmg, rad));
	}
	static void Particle(Actor m, int n)
	{
		let c = RSLD.AC("LDRadiationParticle");
		if (!c || !m) return;
		for (int i = 0; i < n; i++) Actor.Spawn(c, m.pos + (frandom(-32, 32), frandom(-32, 32), frandom(-32, 32)), NO_REPLACE);
	}
}

// Suppression (R: PR): five mini plasma balls (scale 0.2) of a fifth each, +-15 degrees across and +-5 up/down, for
// the one cell (LegenDoom fires them with one A_FireCustomMissile taking ammo and four that do not)
class RSLD_Fx_Suppression : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_PLASMA; }
	override void RiderStart(RSLD_Rider r)
	{
		if (r.child || !r.m) return;
		double hs = RSLD_G3.N("Suppression", "spread"), vs = RSLD_G3.N("Suppression", "vspread"), div = RSLD_G3.N("Suppression", "div");
		double sc = RSLD_G3.N("Suppression", "scale");
		double a, p;
		[a, p] = RSLD_G3.Dir(r.m);
		double sp = r.m.vel.Length();
		r.dmgMul = 1 / div;
		r.m.scale *= sc;
		r.m.Vel3DFromAngle(sp, a + frandom(-hs, hs), p + frandom(-vs, vs));
		for (int i = 0; i < 4; i++) RSLD_G3.Child(r, r.m.pos, a + frandom(-hs, hs), p + frandom(-vs, vs), sp, 1 / div, sc);
		RSLD_G3.Log(r, String.Format("5 mini balls x%.2f", 1 / div));
	}
}

// Waveform (R: PR): two balls weaving (A_Weave(1, 0, 3.0, 0)), the second half a cycle on (WeaveIndexXY 32)
class RSLD_Fx_Waveform : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_PLASMA; }
	override void RiderStart(RSLD_Rider r)
	{
		if (r.child || !r.m) return;
		double a, p;
		[a, p] = RSLD_G3.Dir(r.m);
		let c = RSLD_G3.Child(r, r.m.pos, a, p, r.m.vel.Length(), 1, 1);
		if (c) c.WeaveIndexXY = int(RSLD_G3.N("Waveform", "index"));
		RSLD_G3.Log(r, "two weaving balls");
	}
	override void RiderTick(RSLD_Rider r, bool bounced) { r.m.A_Weave(int(RSLD_G3.N("Waveform", "xspeed")), 0, RSLD_G3.N("Waveform", "xdist"), 0); }
}

// ------------------------------------------------------------------ Epic

// Overkill (E: RL): the giga missile (LDOverkillRocket: Damage 200, A_Explode(1280, 640), LegenDoom's ring of
// LDOverkillBoomer visuals). Ours: direct x 200 / 90, our blast x10 damage x5 radius, LegenDoom's visual ring.
// Its 5x ammo and cooldown are the fire states' (agent R3b, G5).
class RSLD_Fx_Overkill : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	// the fire-state part is R3b's (ld_g5_core.zs RSLD_G5Fire): the trigger held on cooldown / under 5 loaded, 4 more rockets out
	override void WhileHeld(RSLD_Held c) { RSLD_G5Fire.OverkillHeld(c); }
	override void AfterPull(RSLD_Shot s) { RSLD_G5Fire.OverkillPull(s); }
	override void RiderSpawn(RSLD_Rider r)
	{
		r.dmgMul = RSLD_G3.N("Overkill", "dmg") / (RSLD_G3.LDBase(r.kind) * RSLD_G3.RndMean());
		r.explDmgMul = RSLD_G3.N("Overkill", "expl") / RSLD_G3.N("Base3", "rk_expl");
		r.explRadMul = RSLD_G3.N("Overkill", "rad") / RSLD_G3.N("Base3", "rk_rad");
		RSLD_G3.Log(r, String.Format("giga missile: direct x%.2f, blast x%.0f over x%.0f", r.dmgMul, r.explDmgMul, r.explRadMul));
	}
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky) return;
		let c = RSLD.AC("LDOverkillBoomer");
		if (!c) return;
		int n = 0;
		double ofs = 0;
		if (r.m) { if (r.m.ceilingz - r.last.z < 16) ofs = -8; else if (r.last.z - r.m.floorz < 16) ofs = 8; }
		Vector3 at = r.last + (0, 0, ofs);
		double a0 = r.m ? r.m.angle : 0;
		n += Ring(c, at, a0, 90, r) + Ring(c, at, a0, -90, r);
		for (int p = -80; p <= 80; p += 10) for (int a = 0; a < 360; a += 15) n += Ring(c, at, a0 + a, p, r);
		RSLD_G3.Log(r, String.Format("LegenDoom's giga ring: %d visuals", n));
	}
	static int Ring(class<Actor> c, Vector3 at, double a, double p, RSLD_Rider r)
	{
		let b = Actor.Spawn(c, at, NO_REPLACE);
		if (!b) return 0;
		b.target = r.s ? r.s.mo : null;
		b.angle = a; b.pitch = p;
		b.Vel3DFromAngle(b.Speed, a, -p);
		return 1;
	}
}

// Goldeneye (E: RL): a direct hit keeps exploding around that enemy (LDGoldeneyeDamage: random(18,30) blasts of
// random(16,32) over 128, random(3,6) tics apart, until it dies); LegenDoom's numbers (E), its explosion visual
// (LDGoldeneyeEffectExplosionMaker), effects/goldeneyeexplode -> Explode6 (scope 4) at the start, 16 and 8 left
class RSLD_Fx_Goldeneye : RSLD_G3Fx
{
	override bool Rides(int k) { return k == RSLD_G3.K_ROCKET || k == RSLD_G3.K_GRENADE; }
	override void RiderSpawn(RSLD_Rider r) { r.m.bHITTRACER = true; }
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky || !r.m || !r.m.tracer || !r.m.tracer.bSHOOTABLE || r.m.tracer.health <= 0) return;
		let g = new("RSLD_GoldenEye");
		g.t = r.m.tracer; g.s = r.s;
		g.timer = random(int(RSLD_G3.N("Goldeneye", "tmin")), int(RSLD_G3.N("Goldeneye", "tmax")));
		g.A_Snd();
		RSLD_G3.Log(r, String.Format("direct hit %s: %d blasts", g.t.GetClassName(), g.timer));
	}
}

class RSLD_GoldenEye : Thinker
{
	Actor t;
	RSLD_Shot s;
	int timer, wait;
	void A_Snd() { if (t) t.A_StartSound("Explode6", CHAN_AUTO, CHANF_OVERLAP, 0.7); }
	override void Tick()
	{
		if (!t || t.health <= 0 || timer <= 0) { Destroy(); return; }
		if (wait-- > 0) return;
		int d = random(int(RSLD_G3.N("Goldeneye", "dmin")), int(RSLD_G3.N("Goldeneye", "dmax")));
		let b = RSLD_G3.BoomAt(s, t.pos, d, RSLD_G3.N("Goldeneye", "rad"), 0, XF_HURTSOURCE, 0);
		if (b) b.bFORCERADIUSDMG = true;	// LDGoldeneyeDamage +FORCERADIUSDMG
		RSLD.Give(t, "LDGoldeneyeEffectExplosionMaker");
		timer--;
		if (timer == 16 || timer == 8) A_Snd();
		wait = random(int(RSLD_G3.N("Goldeneye", "imin")), int(RSLD_G3.N("Goldeneye", "imax"))) - 1;
	}
}

// Plasmatic on the rocket launcher (owner round 3): our rocket is swapped for LegenDoom's plasma rocket
// (LDPlasmaticRocket: its look, Damage 20 x random(6,13), A_Explode(128,128)) at our ratio: direct = our direct x
// random(6,13) / 4.5, our blast 100/150 in place of its 128/128; our sounds: Plasma/AltFire on the shot (scope 4
// effects/plasmarocket), Explosion (Rocket2's DeathSound) where it bursts; LegenDoom's own sounds on it are stopped.
// Called from RSLD_Fx_Plasmatic (ld_g2_proj.zs), whose pellet half is G2's.
class RSLD_G3Plasmatic : RSLD_G3Fx
{
	static RSLD_G3Plasmatic Get()
	{
		let g = RSLD_G3.Reg();
		if (!g.plasmatic) { g.plasmatic = new("RSLD_G3Plasmatic"); g.plasmatic.name = "Plasmatic"; g.plasmatic.h = RSLD.H(); }
		return g.plasmatic;
	}
	static void Rocket(RSLD_Shot s, Actor m)
	{
		int k = RSLD_G3.Kind(m);
		if (k != RSLD_G3.K_ROCKET && k != RSLD_G3.K_GRENADE) return;
		RSLD_G3.Ride(s, m, Get());
	}
	override void RiderStart(RSLD_Rider r)
	{
		let c = RSLD.AC("LDPlasmaticRocket");
		if (!c || !r.m || r.child) return;
		let p = Actor.Spawn(c, r.m.pos, NO_REPLACE);
		if (!p) return;
		p.target = r.m.target; p.angle = r.m.angle; p.pitch = r.m.pitch; p.vel = r.m.vel;
		r.m.Destroy();
		r.m = p;
		r.s.TagMissile(p);
		r.s.Sound("Plasma/AltFire");
		RSLD_G3.Log(r, "our rocket -> LegenDoom's plasma rocket");
	}
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky || !r.m) return;
		RSLD_G3.Silence(r.m, 6);
		RSLD_G3.BoomAt(r.s, r.last, RSLD_G3.BLAST_DMG, RSLD_G3.BLAST_RAD, 0, XF_HURTSOURCE, 0, 'ExplosiveImpact', 0, "Explosion");
		RSLD_G3.Log(r, "burst: our blast 100/150");
	}
	// called from RSLD_Fx_Plasmatic.ModifyDamage
	static bool Dmg(RSLD_Shot s, RSLD_Hit h)
	{
		let r = RSLD_G3.RiderOf(h.inflictor);
		if (!r || r.fx != Get()) return false;
		if (h.flags & DMG_EXPLOSION) { h.mult = 0; return true; }	// its own 128/128: ours is the RSLD_Boom above
		h.setDamage = int(r.ourDirect * random(int(RSLD_G3.N("Plasmatic", "rk_min")), int(RSLD_G3.N("Plasmatic", "rk_max"))) / RSLD_G3.RndMean() + 0.5);
		s.Log(String.Format("plasma rocket direct hit %d (ours %d x random(6,13) / 4.5)", h.setDamage, r.ourDirect));
		return true;
	}
}
