// ld_g2_fx.zs -- G2 (Agent C): LegenDoom 3.0's shot-shape effects on BD22 VR's bullet guns.
//
// Slots: pi = LegenDoom's Pistol (BrutalPistol, DualPistols, PuristPistol, BrutalRevolver), sg = Shotgun (Shot_Gun,
// PuristShot_Gun), ss = Super Shotgun (SSG, PuristSSG), cg = Chaingun (MiniGun, PuristMiniGun, Rifle, DualRifles,
// PuristRifle), and their off-hand copies (the foundation gives the hand's own gun). Every LegenDoom number is Num() /
// RSLD.Num() (numbers_g2.zs, generated from LegenDoom's own DECORATE by ldl_patch/tools/numbers/g2.rules: each row
// names its file:line). Our guns' numbers come from ld_g2_spread.zs (parsed from our .dec). Where LegenDoom's number is
// gun-relative, LegenDoom's RATIO goes onto our gun's own number (owner 11-06): x pellets, x damage, x spread.
// "Pattern pellets": the gun's spread volleys (ld_g2_core.zs); the SSG's 300-unit point-blank blast stays as it is.
// Sounds: BD22 / BD22 VR sounds only (scope section 4); Renegade's scream: mechanics only, silent (owner 11-06).
// Visuals (owner 2026-11-06 round 2): LegenDoom's own, from the loaded LegenDoom pk3 by name (RSLD.LDVisual), never its
// quakes (the LD mode turns LegenDoom's LD_quakes off). The rocket / plasma / BFG / melee halves of the all-slot effects here (Blastwave, Explosive, Heavy, Cursed,
// TripleThreat, TwinShot, ShortRange) belong to G3 / G4 / G7: they add OnMissile / OnMelee to these same classes.

// ---------------------------------------------------------------------------------------------------------------
// Renegade (C: Sg, SS): "Fires 50% more pellets". LD Shotgun 11 for 7 (Shotgun.dec FireRenegade), SuperShotgun 30 for
// 20. Ours: pump 9 -> 14 (Tactical 14 -> 22), SSG 18 -> 27 (Tactical 28 -> 42). The added pellets are our pellets: the
// same damage, puff and range, a fresh roll of their volley's spread. LD's scream (A_Jump 32: effects/renegade): silent.
class RSLD_Fx_Renegade : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		int n = PatternIndex(s, p);
		if (n < 0) return false;
		string k = RSLD_G2.Key(s.slot) == "ss" ? "ss_n" : "sg_n";
		int ldN = int(Num(k)), ldBase = int(RSLD.Num("Base", k));
		if (ldN <= ldBase || ldBase <= 0) return false;
		// after n+1 pattern pellets the pull has floor((n+1) * (ldN - ldBase) / ldBase) added ones (pump 9 -> 5)
		int want = ((n + 1) * (ldN - ldBase)) / ldBase;
		while (s.i1 < want)
		{
			double a, pt;
			[a, pt] = Fresh(s, p.index);
			Extra(s, p, a, pt, p.damage, p.puff, p.range);
		}
		if (n + 1 == PatternPellets(s))
			s.Log(String.Format("%s: %d pattern pellets + %d added = %d (LD %d for %d)", SeqName(s), n + 1, s.i1, n + 1 + s.i1, ldN, ldBase));
		return false;
	}
}

// ---------------------------------------------------------------------------------------------------------------
// TwinShot (E: all slots; G2 = Pi, Sg, SS, Cg): "Fires two shots for the price of one". LD Shotgun 14 pellets for 7
// (FireTwinShot), Pistol / Chaingun a second bullet without USEAMMO. Ours: every pattern pellet gets a twin, a fresh
// roll of its own volley's spread; the twin takes no ammo.
class RSLD_Fx_TwinShot : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		int n = PatternIndex(s, p);
		if (n < 0) return false;
		int ratio = int(Num("sg_n") / RSLD.Num("Base", "sg_n"));	// 14 / 7 = 2
		for (int i = 1; i < ratio; i++)
		{
			double a, pt;
			[a, pt] = Fresh(s, p.index);
			Extra(s, p, a, pt, p.damage, p.puff, p.range);
		}
		if (n + 1 == PatternPellets(s) || PatternPellets(s) == 0)
			s.Log(String.Format("%s: %d pattern pellets + %d twins (x%d)", SeqName(s), n + 1, s.i1, ratio));
		return false;
	}
}

// ---------------------------------------------------------------------------------------------------------------
// TripleThreat (E): "Fires a spread of three shots". LD: the shot, then its pellets again at +15 and -15 deg rolled
// with frandom(-spread, spread) (Shotgun.dec FireTripleThreat: 15+frandom(-5.6,5.6)). Ours: every pattern pellet gets
// two copies at aim +-15 deg, rolled uniformly (frandom, as LD) inside our volley's spread.
class RSLD_Fx_TripleThreat : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		int n = PatternIndex(s, p);
		if (n < 0) return false;
		double off = Num("offset");
		double h, v, rg;
		[h, v, rg] = Volley(s, p.index);
		for (int side = -1; side <= 1; side += 2)
			Extra(s, p, s.aimAngle + side * off + frandom[rsld_g2](-h, h), s.aimPitch + frandom[rsld_g2](-v, v), p.damage, p.puff, p.range);
		if (n + 1 == PatternPellets(s) || PatternPellets(s) == 0)
			s.Log(String.Format("%s: %d pattern pellets + %d copies at +-%g deg", SeqName(s), n + 1, s.i1, off));
		return false;
	}
}

// ---------------------------------------------------------------------------------------------------------------
// ShortRange (E): "Fires multiple attacks that disappear very quickly". LD: the whole shot three times, ranges 200,
// 150, 100 (Shotgun.dec FireShortRange). Ours: every pattern pellet flies 200, plus two fresh ones of 150 and 100.
// Under MISSILERANGE they stay hitscans in True Bullets mode, as LD's do (playerrounds.zs:233).
class RSLD_Fx_ShortRange : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		int n = PatternIndex(s, p);
		if (n < 0) return false;
		double r1 = Num("r1"), r2 = Num("r2"), r3 = Num("r3");
		double was = p.range;
		double a, pt;
		[a, pt] = Fresh(s, p.index);
		Extra(s, p, a, pt, p.damage, p.puff, r2);
		[a, pt] = Fresh(s, p.index);
		Extra(s, p, a, pt, p.damage, p.puff, r3);
		p.range = r1;
		if (n + 1 == PatternPellets(s) || PatternPellets(s) == 0)
			s.Log(String.Format("%s: %d pattern pellets at range %g (was %g) + %d at %g / %g", SeqName(s), n + 1, r1, was, s.i1, r2, r3));
		return false;
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Sniper (R: Pi, Sg, SS, Cg): "100% accurate": LD spread 0 (A_FireBullets(0, 0, ...)). Ours: every pellet on the gun's
// aim (A_FireBullets' own base angle and autoaim slope, the foundation's s.aim*). In VR the aim is the controller:
// only the cone goes.
class RSLD_Fx_Sniper : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		Seq(s, p);
		double k = Num("spread");	// 0
		double da = Actor.DeltaAngle(s.aimAngle, p.angle), dp = p.pitch - s.aimPitch;
		p.spreadMul = k;
		s.Log(String.Format("%s pellet %d: off the aim %.2f / %.2f deg -> x%g", SeqName(s), p.index, da, dp, k));
		return false;
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Choked (Sg, SS): "Shotguns have fixed spread instead of random shots". Owner 2026-11-06 round 2: our OWN tight pattern
// for each of our pellet counts (pump 9 / Tactical 14, SSG 18 / 28, SSG one barrel 9 / 14), built the way LegenDoom built
// its Shotgun 7 / SuperShotgun 20 (ldl_patch/tools/g2_choked.py -> ld_g2_choked.zs: fixed mirror-symmetric points on a
// square grid, centre for an odd count, LegenDoom's own points first). Grid step = LegenDoom's step (Choked|sg_h3 1.5,
// Choked|ss_h0 2.0) x our widest pattern volley's horizontal spread / LegenDoom's (Base|sg_spread 5.6, ss_spread 11.2),
// so the pattern keeps LegenDoom's share of the spread. Pattern pellet j of the pull goes on point j, around the aim.
class RSLD_Fx_Choked : RSLD_G2_Effect
{
	RSLD_G2_Choked pat;

	override void Init()
	{
		Super.Init();
		pat = new("RSLD_G2_Choked");
		pat.Fill();
	}

	// our pull's widest pattern volley (Tactical / "Pump Shotgun Spread" as the player has them)
	double OurSpread(RSLD_Shot s)
	{
		int q = s.i2 - 2;
		if (q < 0) return 0;
		bool tac = Tactical(s.mo), en = Enhanced(s.mo);
		double w = 0;
		for (int i = 0; i < tab.vSeq.Size(); i++)
			if (tab.vSeq[i] == tab.sName[q] && (!tab.vTac[i] || tac) && tab.vRange[i] == 0)
				w = max(w, en ? tab.vHe[i] : tab.vH[i]);
		return w;
	}

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		int n = PatternIndex(s, p);
		if (n < 0) return false;
		string k = RSLD_G2.Key(s.slot) == "ss" ? "ss" : "sg";
		int total = PatternPellets(s);
		int row = pat.Find(k, total);
		if (row < 0 || n >= pat.count[row]) { s.Log(String.Format("%s: no pattern for %d pellets: left as fired", SeqName(s), total)); return false; }
		double ldStep = abs(Num(k == "ss" ? "ss_h0" : "sg_h3")), ldSpread = RSLD.Num("Base", k .. "_spread");
		double ours = OurSpread(s);
		if (ldStep <= 0 || ldSpread <= 0 || ours <= 0) return false;
		double step = ldStep * ours / ldSpread;
		int gx = pat.px[pat.first[row] + n], gy = pat.py[pat.first[row] + n];
		p.angle = s.aimAngle + gx * step;
		p.pitch = s.aimPitch + gy * step;
		if (n == 0)
			s.Log(String.Format("%s: %d pellets on our pattern %s|%d, grid %.3f deg (LegenDoom %g x our spread %g / %g)", SeqName(s), total, k, total, step, ldStep, ours, ldSpread));
		if (RSLD.DebugLevel() > 1 || n + 1 == total)
			s.Log(String.Format("pellet %d -> grid (%d, %d) = (%.2f, %.2f) deg", n + 1, gx, gy, gx * step, gy * step));
		return false;
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Slug (C: Sg, SS): "Fire accurate single shots with strong knockback". LD Shotgun: ONE bullet, spread 1.6, damage
// 7*random(5,15) for its 7 pellets of 5*random(1,3) (the same mean, +-50%). SuperShotgun: TWO bullets, 10*random(5,15)
// each, at frandom(1.6,3.2) and frandom(-3.2,-1.6). Ours: the pull's pattern pellets become one slug (two on the SSG)
// of (pattern pellets x our pellet damage) x random(5,15) / 10 (halved per SSG slug), at LD's spread. The knockback is
// the engine's for that damage, as in LD (its slug uses the plain LDBulletPuff).
// Scope Q12 is open (BD22 VR's own Slug ALT fire, Shotgun.dec:703-711 RSA_SlugShot, 150 on one point): this changes
// PRIMARY fire only (cvar rsld_slug_primary, default on; off = LD's Slug does nothing on our guns). The pump's slug alt
// fire and the SSG's one-barrel alt (SSG.dec ResumeFire2Frame) stay as they ship.
class RSLD_Fx_Slug : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		int n = PatternIndex(s, p);
		if (n < 0) return false;
		let cv = CVar.FindCVar('rsld_slug_primary');
		if (cv && !cv.GetBool()) return false;
		string sq = SeqName(s);
		if (sq != "pump" && sq != "ssg") return false;	// primary fire only (Q12)
		if (s.b1) return true;							// the slug already went: the rest of the buckshot does not
		s.b1 = true;
		int pellets = PatternPellets(s);
		int lo = int(Num("lo")), hi = int(Num("hi"));
		double mean = (lo + hi) / 2.;
		Hold(p);
		if (sq == "pump")
		{
			int dmg = int(pellets * keep.damage * random[rsld_g2](lo, hi) / mean);
			s.FirePellet(s.aimAngle + RSLD_G2.RollH(Num("sg_spread")), s.aimPitch, dmg, keep.puff, keep.range);
			s.Log(String.Format("pump: one slug of %d (= %d pellets x %d x random(%d,%d) / %g), spread %g; buckshot dropped", dmg, pellets, keep.damage, lo, hi, mean, Num("sg_spread")));
		}
		else
		{
			double alo = Num("ss_alo"), ahi = Num("ss_ahi");
			for (int side = 1; side >= -1; side -= 2)
			{
				int dmg = int(pellets * keep.damage / 2. * random[rsld_g2](lo, hi) / mean);
				s.FirePellet(s.aimAngle + side * frandom[rsld_g2](alo, ahi), s.aimPitch, dmg, keep.puff, keep.range);
				s.Log(String.Format("ssg: %s slug of %d (= %d / 2 pellets x %d x random(%d,%d) / %g); buckshot dropped", side > 0 ? "left" : "right", dmg, pellets, keep.damage, lo, hi, mean));
			}
		}
		Restore(p);
		return true;
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Gauss (E: Pi, Sg, SS, Cg): "Shots pierce through enemies". LD: every pellet an A_RailAttack (RGF_SILENT, its own
// spread, LDGaussBulletPuff). Ours: every pellet (pattern and blast) a piercing rail with our damage, our puff, the
// pellet's own angle and range; no trail (Q4 open); BD22's Railgun/Fire once per pull (scope section 4, effects/gauss).
class RSLD_Fx_Gauss : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		Seq(s, p);
		if (!s.b1)
		{
			s.b1 = true;
			s.Sound("Railgun/Fire", 0.6);
		}
		Hold(p);
		// round 2 (owner: LegenDoom's own visuals): LegenDoom's rail look, no outer spiral ("None"), a white inner trail
		// ("White"), its duration / sparsity / drift (numbers_g2 Gauss|*)
		s.FireRail(keep.angle, keep.pitch, keep.damage, keep.puff, keep.range > 0 ? keep.range : PLAYERMISSILERANGE,	// RailAttack takes distance as given: 0 is a zero-length rail (rig agC_b2)
			-1, 0xFFFFFF, int(Num("duration")), Num("sparsity"), Num("drift"));
		Restore(p);
		return true;
	}

	override void OnPelletEnd(RSLD_Shot s, RSLD_Pellet p, int res, Vector3 at, Actor thing)
	{
		if (!p.rail) return;
		// LegenDoom's LDGaussBulletPuff visual where the rail ended (EpicSpecialEffects.dec: GAUX B-E; our puff did the damage)
		Actor v = res != RSLD.RES_NONE ? RSLD.LDVisual("LDGaussBulletPuff", at, "Spawn", 0, s.mo) : null;
		s.Log(String.Format("rail (%d dmg): %s%s, LegenDoom trail (white, %d tic) %s", p.damage, RSLD_G2.ResName(res), thing ? " " .. thing.GetClassName() : "",
			int(Num("duration")), v ? String.Format("+ LDGaussBulletPuff at %.0f %.0f %.0f", at.x, at.y, at.z) : "(no end puff)"));
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Heavy (U): "Greatly increased knockback". LD: the bullet puff's ProjectileKickBack 4000 (UncommonSpecialEffects.dec
// LDHeavyBulletPuff). Ours: BD22's puffs stay (their damage types, blood, decals); a bullet hit gets the extra thrust
// the engine would have given for kickback 4000 instead of the one it used (gzdoom interaction.zs ApplyKickback: the
// puff's ProjectileKickBack, else the weapon's Kickback; x the skill factor; damage * 0.125 * kickback / mass, max 32).
class RSLD_Fx_Heavy : RSLD_G2_Effect
{
	override void OnHit(RSLD_Shot s, RSLD_Hit h)
	{
		let t = h.target;
		if (!t || !s || s.pull == 0 || s.melee || !s.mo || h.damage <= 0 || RSLD_G2.Ours(h.inflictor)) return;
		if (t.bNOCLIP || t.bDONTTHRUST || (h.inflictor && h.inflictor.bNODAMAGETHRUST) || t.Mass <= 0) return;
		int used = (h.inflictor && h.inflictor.ProjectileKickBack) ? h.inflictor.ProjectileKickBack
			: ((s.mo.player && s.mo.player.ReadyWeapon) ? s.mo.player.ReadyWeapon.Kickback : gameinfo.defKickback);
		double f = G_SkillPropertyFloat(SKILLP_KickbackFactor);
		double kick = Num("kick");
		double was = clamp(h.damage * 0.125 * used * f / t.Mass, 0., 32.);
		double now = clamp(h.damage * 0.125 * kick * f / t.Mass, 0., 32.);
		if (now <= was) return;
		t.Thrust(now - was, s.mo.AngleTo(t));
		s.Log(String.Format("%s hit for %d: thrust %.2f -> %.2f (kickback %d -> %g, mass %d)", t.GetClassName(), h.damage, was, now, used, kick, t.Mass));
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Explosive (R): "Shots explode for small radius damage". LD: every bullet's puff A_Explode(15, 64, 0, alert, 64) on
// Spawn / XDeath / Crash (RareSpecialEffects.dec LDExplosiveBulletPuff); the first pellet's puff plays the sound, the
// rest are LDSilentExplosiveBulletPuff. Ours: that explosion where each of our pellets ends (a wall, a monster or a
// thing; not the sky), credited to you, never hurting you; BD22's rocket DeathSound "Explosion" (Explosives.dec Rocket2)
// for LD's rocketlauncher/explode, once per pull. No LegenDoom sprites or quakes (Q4).
class RSLD_G2_Boom : Actor
{
	int dmg, rad, full;
	Default { +NOINTERACTION; +NOBLOCKMAP; +NOGRAVITY; +DONTSPLASH; RenderStyle "None"; }
	States
	{
	Spawn:
		TNT1 A 0 NoDelay { A_Explode(dmg, rad, 0, true, full); }
		TNT1 A 1;
		Stop;
	}
}

class RSLD_Fx_Explosive : RSLD_G2_Effect
{
	override void OnPelletEnd(RSLD_Shot s, RSLD_Pellet p, int res, Vector3 at, Actor thing)
	{
		if (res == RSLD.RES_NONE || !s.mo || s.melee) return;
		let b = RSLD_G2_Boom(Actor.Spawn("RSLD_G2_Boom", at));
		if (!b) return;
		b.target = s.mo;
		b.dmg = int(Num("dmg"));
		b.rad = int(Num("radius"));
		b.full = int(Num("full"));
		if (!s.b2)
		{
			s.b2 = true;
			b.A_StartSound("Explosion", CHAN_AUTO);
		}
		// round 2: LegenDoom's own visual (LDExplosiveBulletPuff's particles and MEXP explosion, from its Pahticools state:
		// past its A_Explode and its sounds; its quake is off)
		let v = RSLD.LDVisual("LDExplosiveBulletPuff", at, "Pahticools", 0, s.mo);
		s.Log(String.Format("pellet %d on %s: explosion %d r%d (full %d) at %.0f %.0f %.0f%s", p.index, RSLD_G2.ResName(res), b.dmg, b.rad, b.full, at.x, at.y, at.z,
			v ? ", LegenDoom visual LDExplosiveBulletPuff" : ""));
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Flak (U: Pi, Cg): "Aerial enemies are surrounded by explosions on hit". LD: a bullet hitting a NOGRAVITY thing that
// is not an ExplosiveBarrel spawns LDFlakDamage: 5 x A_Explode(random(16,32), 128) at the target +32 z, random(1,4)
// tics apart (UncommonSpecialEffects.dec:1750; default flags: it CAN hurt you, as in LD). Ours: the same from a hit of
// our bullets; BD22's "Explosion" at LD's 0.4 for each (LD: rocketlauncher/uncommonexplode 0.4). No sprites (Q4).
class RSLD_G2_Flak : Actor
{
	int left, lo, hi, rad, wait, gaplo, gaphi, shown;
	double z;
	Default { +NOINTERACTION; +NOBLOCKMAP; +NOGRAVITY; +DONTSPLASH; +FORCERADIUSDMG; +NODAMAGETHRUST; +BLOODLESSIMPACT; RenderStyle "None"; }
	States { Spawn: TNT1 A -1; Stop; }
	override void Tick()
	{
		if (isFrozen()) return;
		if (wait-- > 0) return;
		if (left <= 0 || !tracer) { Destroy(); return; }
		SetOrigin(tracer.pos + (0, 0, z), false);
		A_Explode(random[rsld_g2](lo, hi), rad);
		A_StartSound("Explosion", CHAN_AUTO, CHANF_OVERLAP, 0.4);
		// round 2: LegenDoom's own LDFlakEffectExplosion, where its LDFlakEffectExplosionMaker puts it (around the target:
		// x/y within 0.8 radius, z 8 .. 0.8 height), past its two sound calls (UncommonSpecialEffects.dec:1786-1815)
		if (tracer)
		{
			double r = tracer.radius * 0.8;
			Vector3 at = tracer.pos + (frandom[rsld_g2](-r, r), frandom[rsld_g2](-r, r), frandom[rsld_g2](8, max(8., tracer.height * 0.8)));
			if (RSLD.LDVisual("LDFlakEffectExplosion", at, "Spawn", 3, target)) shown++;
		}
		left--;
		wait = random[rsld_g2](gaplo, gaphi) - 1;
	}
}

class RSLD_Fx_Flak : RSLD_G2_Effect
{
	override void OnHit(RSLD_Shot s, RSLD_Hit h)
	{
		let t = h.target;
		if (!t || !s || s.pull == 0 || s.melee || !s.mo || !t.bNOGRAVITY || t is "ExplosiveBarrel") return;
		if (!h.inflictor || RSLD_G2.Ours(h.inflictor)) return;
		let f = RSLD_G2_Flak(Actor.Spawn("RSLD_G2_Flak", t.pos));
		if (!f) return;
		f.target = s.mo;
		f.tracer = t;
		f.left = 5;
		f.lo = int(Num("lo"));
		f.hi = int(Num("hi"));
		f.rad = int(Num("radius"));
		f.z = Num("z");
		f.gaplo = int(Num("gaplo"));
		f.gaphi = int(Num("gaphi"));
		s.Log(String.Format("flak on %s: 5 x %d-%d r%d at +%g z, %d-%d tics apart", t.GetClassName(), f.lo, f.hi, f.rad, f.z, f.gaplo, f.gaphi));
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Cursed (E: Pi, Sg, SS, Cg here): "Does 4x damage, but any missed shot hurts you". LD: 20 for 5 (x4); a puff that hits
// no monster gives LDCursedEffect (stacking cooldown LDEffectStackingCooldown, 2 tics), whose delayer a tic later deals
// A_DamageSelf(5, "Suicide", NOFACTOR|NOPROTECT) unless LDCursedEffectHit (2 tics, from a monster hit) is held
// (EpicSpecialEffects.dec:3815-3940). Ours: x4 on every pellet; a pull that missed (a wall or a non-monster) and hit no
// monster costs 5, with LegenDoom's own cooldown and hit items on the player. A sky shot: no puff in LD, no cost here.
class RSLD_Fx_Cursed : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		int mult = int(Num("dmg") / RSLD.Num("Base", "sg_dmg"));	// 20 / 5
		p.damage *= mult;
		return false;
	}

	override void OnPelletEnd(RSLD_Shot s, RSLD_Pellet p, int res, Vector3 at, Actor thing)
	{
		if (res == RSLD.RES_MONSTER) { s.b1 = true; RSLD.Give(s.mo, "LDCursedEffectHit"); }
		else if (res == RSLD.RES_WALL || res == RSLD.RES_THING) s.b2 = true;
	}

	override void OnPullEnd(RSLD_Shot s)
	{
		if (!s.mo) return;
		string why;
		if (s.b1) why = "a monster was hit: no cost";
		else if (!s.b2) why = "no puff (the sky): no cost";
		else if (RSLD.Has(s.mo, "LDCursedEffectHit")) why = "a monster hit within LD's 2 tics: no cost";
		else if (RSLD.Has(s.mo, "LDEffectStackingCooldown")) why = "LD's stacking cooldown: no cost";
		else
		{
			RSLD.Give(s.mo, "LDEffectStackingCooldown");
			int hp = s.mo.health;
			s.mo.A_DamageSelf(int(Num("self")), 'Suicide', DMSS_NOFACTOR | DMSS_NOPROTECT);
			why = String.Format("missed: self damage %d (health %d -> %d)", int(Num("self")), hp, s.mo.health);
		}
		s.Log(String.Format("x%d pull (%d pellets): %s", int(Num("dmg") / RSLD.Num("Base", "sg_dmg")), s.pellets, why));
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Suspenseful (R: Pi, Sg, SS, Cg): "Each missed shot gives you a damage boost for your next shot". LD: damage x
// (LDSuspensefulCounter + 5) / 5 (LEGNDLIB.acs:80); the counter (LegenDoom's own item on the player, max 20) +1 when a
// puff Crashes (a wall), with the 2-tic stacking cooldown; a puff on any thing (Spawn / XDeath) empties it
// (RareSpecialEffects.dec:2884). Ours: LegenDoom's own counter and cooldown items, read at the pull's first pellet;
// a pull that hit anything empties it, else a wall miss adds 1.
class RSLD_Fx_Suspenseful : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (!s.b1)
		{
			s.b1 = true;
			s.i1 = RSLD.Has(s.mo, "LDSuspensefulCounter");
			s.d1 = (s.i1 + Num("base")) / Num("base");
		}
		p.damage = int(p.damage * s.d1);
		return false;
	}

	override void OnPelletEnd(RSLD_Shot s, RSLD_Pellet p, int res, Vector3 at, Actor thing)
	{
		if (res == RSLD.RES_MONSTER || res == RSLD.RES_THING) s.i2 = s.i2 | 0x10000;	// a hit (i2's low bits: Seq)
		else if (res == RSLD.RES_WALL) s.b2 = true;
	}

	override void OnPullEnd(RSLD_Shot s)
	{
		if (!s.mo) return;
		class<Inventory> cc = RSLD.IC("LDSuspensefulCounter");	// by name at run time: a literal is resolved at compile time and fails without LegenDoom (rig agC_after_nold)
		if (s.i2 & 0x10000)
		{
			if (cc) s.mo.TakeInventory(cc, 0x7fffffff);
		}
		else if (s.b2 && !RSLD.Has(s.mo, "LDEffectStackingCooldown"))
		{
			RSLD.Give(s.mo, "LDSuspensefulCounter");
			RSLD.Give(s.mo, "LDEffectStackingCooldown");
		}
		int now = RSLD.Has(s.mo, "LDSuspensefulCounter");
		s.Log(String.Format("pull at x%.2f (count %d): %s -> count %d (next x%.2f)", s.d1, s.i1,
			(s.i2 & 0x10000) ? "hit" : (s.b2 ? "missed (wall)" : "nothing"), now, (now + Num("base")) / Num("base")));
	}
}

// ---------------------------------------------------------------------------------------------------------------
// PointBlank (R: Pi, Cg): "Decreased accuracy, but any shots that hit don't consume ammo". LD: the bullet fires without
// USEAMMO; a puff that Crashes (a wall) takes 1 Clip (RareSpecialEffects.dec:1393); spread Pistol 5.6 (its normal),
// Chaingun 16.8 (3x). Ours (owner Q7: the magazine): the pull's rounds are given back, each wall miss takes one;
// spread x (LD's PointBlank spread / LD's normal spread) on our gun's own spread: pistol family x1, chaingun family x3.
class RSLD_Fx_PointBlank : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		string k = RSLD_G2.Key(s.slot) == "cg" ? "cg" : "pi";
		double mul = Num(k .. "_spread") / RSLD.Num("Base", k .. "_spread");
		p.spreadMul = mul;
		s.d1 = mul;
		return false;
	}

	// one round per shot: LD's Pistol / Chaingun fire one bullet per Fire (Pistol.dec:1434, Chaingun.dec:1257), and so do
	// ours (one A_FireBullets per pull). A pull with no pellet (a tracer, a spin tic) gives nothing back; the per-tic ammo
	// diff can hold a neighbour's round (rig agC_b3: the minigun's diff once read 2), so at most one.
	override void AfterPull(RSLD_Shot s)
	{
		int n = s.pellets > 0 ? min(s.ammoTaken, 1) : 0;
		if (n > 0) s.Refund(n);
		if (s.pellets > 0) s.Log(String.Format("spread x%g; free shot: %d round back", s.d1, n));
	}

	override void OnPelletEnd(RSLD_Shot s, RSLD_Pellet p, int res, Vector3 at, Actor thing)
	{
		if (res != RSLD.RES_WALL) { s.Log(String.Format("pellet %s: free", RSLD_G2.ResName(res))); return; }
		s.Take(int(Num("take")));
		s.Log("miss (wall): one round taken");
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Perfect (R: Pi, Cg): "Shots do max double damage, 100% accuracy, misses jam the gun". LD: 30 = 2 x its max (5*3),
// spread 0; a Crash puff (a wall) gives LDPerfectJammed (Powerup.Duration -1 = 1 second) unless LDPerfectHit (6 tics)
// from a hit is held; jammed, Fire jumps to NoAmmo (Pistol.dec:1439). Ours: 2 x our fixed damage, on the aim; the same
// LegenDoom items on the player; jammed = the trigger is blocked (owner Q6: never the hands). The block needs the FIRE
// hook in our guns' fire states (NEEDS_C.md 7, RSLD_G2.Jammed); until it exists a jammed pull's pellets are dropped and
// its rounds given back (GAP: the gun still draws its fire, sound and flash).
class RSLD_Fx_Perfect : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (RSLD.Has(s.mo, "LDPerfectJammed"))
		{	// the fire states' hook (RSLD_JamMain / RSLD_JamOff) stops the trigger first; a pellet that still comes (a gun
			// without the hook) is dropped and its round given back
			s.b2 = true;
			return true;
		}
		int mult = int(Num("dmg") / (RSLD.Num("Base", "pi_dmg") * RSLD.Num("Base", "rnd_max")));	// 30 / 15 = 2
		p.damage *= mult;
		p.spreadMul = Num("spread");	// 0
		s.d1 = mult;
		return false;
	}

	override void AfterPull(RSLD_Shot s)
	{
		if (!s.b2) return;
		int n = s.pellets > 0 ? min(s.ammoTaken, 1) : 0;	// one round per shot (see PointBlank)
		if (n > 0) s.Refund(n);
		s.Log(String.Format("JAMMED: a pellet came past the fire hook (a gun without it): dropped, %d round back", n));
	}

	override void OnPelletEnd(RSLD_Shot s, RSLD_Pellet p, int res, Vector3 at, Actor thing)
	{
		if (res == RSLD.RES_MONSTER || res == RSLD.RES_THING)
		{
			RSLD.Give(s.mo, "LDPerfectHit");
			s.Log(String.Format("hit %s for %d (x%g, on the aim)", thing ? thing.GetClassName() : 'none', p.damage, s.d1));
		}
		else if (res == RSLD.RES_WALL)
		{
			if (RSLD.Has(s.mo, "LDPerfectHit")) { s.Log("miss within LD's 6 tics of a hit: no jam"); return; }
			RSLD.Give(s.mo, "LDPerfectJammed");
			// the hands' trigger tokens at once (the handler's WorldTick runs after the players' tic: a shot in this tic
			// would come past the fire hook; rig prove_round2 #2 tics 2472, 3272)
			if (RSLD_G2.Jammed(s.mo, RSLD.MAIN)) s.mo.GiveInventory("RSLD_JamMain", 1);
			if (RSLD_G2.Jammed(s.mo, RSLD.OFF)) s.mo.GiveInventory("RSLD_JamOff", 1);
			s.Log(String.Format("miss (wall): JAMMED (LegenDoom's LDPerfectJammed, %d s)", int(Num("jam_s"))));
		}
	}
}

// ---------------------------------------------------------------------------------------------------------------
// Blastwave (C: all slots; G2 = Pi, Sg, SS, Cg): "Does additional damage at close range". LD: with the shot, an
// invisible missile (Speed 30, NOCLIP, THRUACTORS) lives 1 tic and explodes: A_Explode(N, 96, 0) with FORCERADIUSDMG
// (CommonSpecialEffects.dec:1582; N = Pistol 15, Shotgun 105, SuperShotgun 240, the Chaingun fires the Pistol's 15).
// Ours: the same, one per pull, from our drawn muzzle down the drawn barrel (muzzle.zs), credited to you, never
// hurting you; BD22's Explode2 (scope section 4 for effects/blastwave). No LegenDoom sprite, no quake (Q4; VR camera).
class RSLD_G2_Blastwave : Actor
{
	int dmg, rad;
	Vector3 step;
	string ldCls;
	// round 2: LegenDoom's own blastwave visual (LDBlastwave<Gun>'s SHOK shock ring), from its DeathAnimation past its two
	// effects/blastwave sound calls (CommonSpecialEffects.dec:1614-1618); its quake is off
	void ShowLD()
	{
		let v = RSLD.LDVisual(ldCls, pos, "DeathAnimation", 2, target);
		if (RSLD.Debug()) Console.Printf("RSLD %d Blastwave: exploded %d r%d at %.0f %.0f %.0f%s", level.maptime, dmg, rad, pos.x, pos.y, pos.z, v ? ", LegenDoom visual " .. ldCls : "");
	}
	Default { +NOINTERACTION; +NOBLOCKMAP; +NOGRAVITY; +DONTSPLASH; +FORCERADIUSDMG; RenderStyle "None"; }
	States
	{
	Spawn:
		TNT1 A 1;
		TNT1 A 0 { SetOrigin(pos + step, false); A_Explode(dmg, rad, 0); A_StartSound("Explode2", CHAN_AUTO); ShowLD(); }
		TNT1 A 1;
		Stop;
	}
}

class RSLD_Fx_Blastwave : RSLD_G2_Effect
{
	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (s.b1) return false;
		s.b1 = true;
		string k = RSLD_G2.Key(s.slot);
		if (k == "" || !s.mo) return false;
		Vector3 at;
		double a, pt;
		[at, a, pt] = RSLD_G2.Muzzle(s.mo, s.hand, s.aimAngle, s.aimPitch);
		let b = RSLD_G2_Blastwave(Actor.Spawn("RSLD_G2_Blastwave", at));
		if (!b) return false;
		double spd = Num("speed") * Num("tics");
		b.target = s.mo;
		b.dmg = int(Num(k .. "_dmg"));
		b.rad = int(Num("radius"));
		b.step = (cos(pt) * cos(a), cos(pt) * sin(a), -sin(pt)) * spd;
		b.ldCls = k == "sg" ? "LDBlastwaveShotgun" : (k == "ss" ? "LDBlastwaveSuperShotgun" : (k == "cg" ? "LDBlastwaveChaingun" : "LDBlastwavePistol"));
		s.Log(String.Format("blastwave %d r%d, %g units ahead of the muzzle (%.0f %.0f %.0f), next tic", b.dmg, b.rad, spd, at.x, at.y, at.z));
		return false;
	}
}
