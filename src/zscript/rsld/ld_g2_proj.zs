// ld_g2_proj.zs -- LD mode round 2 (2026-11-06): Plasmatic and Gyrojet on BD22 VR's bullet guns (Pi, Sg, SS, Cg).
//
// Owner, round 2: "our True Bullets rounds are projectiles already; these effects swap the round for a plasma ball /
// mini-rocket from the drawn muzzle, our sounds (True Bullets off: the gun fires that projectile)".
// LegenDoom: FirePlasmatic / FireGyrojet fire ONE projectile per pellet instead of the bullets (Pistol / Chaingun 1,
// Shotgun 1 + 6 = its 7, SuperShotgun 1 + 19 = its 20: decorate/<Gun>/<Gun>.dec), each with the spread of the bullets.
// Ours: every pattern pellet of the pull (range MISSILERANGE or more: not the SSG's 300-unit blast, not melee) is taken
// before muzzle.zs / playerrounds.zs see it (no hitscan, no True Bullets round) and LegenDoom's own projectile class,
// from the loaded LegenDoom pk3 by name, flies from the hand's drawn muzzle along the pellet's own angle (our spread),
// at its own Speed. Damage at our ratio: LegenDoom's projectile does Damage x random(1,8) where its bullet did
// 5 x random(1,3) (Base|sg_dmg, Base|rnd_max): its DamageVal is set to our pellet x its Damage / 10 (LegenDoom's
// bullet mean), so the projectile's mean over our pellet is LegenDoom's (plasma 22.5 / 10, gyrojet 45 / 10).
// The silent variants are used (LDPlasmaticShotgunBall2: no SeeSound, no impact sound; LDGyrojetShotgunProjectile2: no
// death sound): their look and flight are LegenDoom's. Our sounds: Plasma/Fire and Weapons/GrenadeFire once per pull
// (scope 4), BD22's Plasma/Impact (Plasma_Ball's DeathSound) and Explosion at LegenDoom's 0.6 (Rocket2's) on impact.
// LegenDoom's quakes are off in LD mode (handler.zs WorldLoaded).

class RSLD_G2_ProjFx : RSLD_G2_Effect
{
	virtual string LDClass() { return ""; }
	virtual string FireSound() { return ""; }
	virtual string HitSound() { return ""; }
	virtual double HitVol() { return 1.0; }

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (s.melee || p.range < MISSILERANGE || (p.flags & LAF_ISMELEEATTACK) || RSLD_G2.Key(s.slot) == "") return false;
		class<Actor> c = RSLD.AC(LDClass());
		if (!c || !s.mo) return false;
		Seq(s, p);
		double bulletMean = RSLD.Num("Base", "sg_dmg") * (1 + RSLD.Num("Base", "rnd_max")) / 2.0;	// 5 x random(1,3) = 10
		if (bulletMean <= 0) return false;
		Vector3 at;
		double a, pt;
		[at, a, pt] = RSLD_G2.Muzzle(s.mo, s.hand, p.angle, p.pitch);
		let m = Actor.Spawn(c, at, NO_REPLACE);
		if (!m) return false;
		int ldDmg = m.GetMissileDamage(0, 1);		// its Damage (x random(1,8) in flight)
		if (ldDmg <= 0) { m.Destroy(); return false; }
		m.target = s.mo;
		m.angle = a;
		m.pitch = pt;
		m.Vel3DFromAngle(m.Speed, a, pt);
		int dv = max(1, int(p.damage * ldDmg / bulletMean + 0.5));
		m.SetDamage(dv);
		s.TagMissile(m);
		let r = RSLD_G2_ProjRider(new("RSLD_G2_ProjRider"));
		r.m = m; r.snd = HitSound(); r.vol = HitVol(); r.s = s;
		if (!s.b1)
		{
			s.b1 = true;
			s.Sound(FireSound());
		}
		// the pellet's event was taken before BD22 VR's recoil and muzzle flash saw it (they listen to the same event):
		// they get the shot here, as they would from the pellet
		let rc = RSQ_Recoil(EventHandler.Find("RSQ_Recoil"));
		if (rc) rc.Kick(s.mo);
		let fl = RSQ_FlashHandler(EventHandler.Find("RSQ_FlashHandler"));
		if (fl) fl.Shot(s.mo);
		s.i1++;
		if (s.i1 == 1 || RSLD.DebugLevel() > 1)
			s.Log(String.Format("pellet %d (%d dmg) -> %s from the %s muzzle (%.0f %.0f %.0f) at %.1f / %.1f, speed %g, damage %d x random(1,8) (mean %.1f = %d x %.2f)",
				p.index, p.damage, c.GetClassName(), RSLD.HandName(s.hand), at.x, at.y, at.z, a, pt, m.Speed, dv, dv * 4.5, p.damage, dv * 4.5 / p.damage));
		return true;	// no hitscan, no True Bullets round
	}

	override void OnPullEnd(RSLD_Shot s)
	{
		if (s.i1 > 0) s.Log(String.Format("%d pellets became %d %s; hits %d kills %d", s.pellets, s.i1, LDClass(), s.hits, s.kills));
	}

	override void OnHit(RSLD_Shot s, RSLD_Hit h)
	{
		let inf = h.inflictor;
		if (inf && inf.GetClass() == RSLD.AC(LDClass()))
			s.Log(String.Format("%s hit %s for %d", inf.GetClassName(), h.target ? h.target.GetClassName() : 'none', h.damage));
	}
}

// the projectile's impact: our sound where it burst (LegenDoom's own death state plays none in these silent variants)
class RSLD_G2_ProjRider : Thinker
{
	Actor m;
	RSLD_Shot s;
	string snd;
	double vol;
	int life;

	override void Tick()
	{
		if (++life > 35 * 20) { Destroy(); return; }
		if (m && m.bMISSILE) return;
		if (m && snd != "") m.A_StartSound(snd, CHAN_AUTO, CHANF_OVERLAP, vol);
		if (m && s && RSLD.DebugLevel() > 1) s.Log(String.Format("%s burst at %.0f %.0f %.0f (%s)", m.GetClassName(), m.pos.x, m.pos.y, m.pos.z, snd));
		Destroy();
	}
}

// Plasmatic (Epic: Pi, Sg, SS, Cg; round 3: the rocket launcher too, our rocket swapped for LegenDoom's plasma rocket:
// RSLD_G3Plasmatic in g3_fx.zs): "Fires powerful plasma projectiles"
class RSLD_Fx_Plasmatic : RSLD_G2_ProjFx
{
	override void OnMissile(RSLD_Shot s, Actor m) { if (s.slot == 6) RSLD_G3Plasmatic.Rocket(s, m); }
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h) { RSLD_G3Plasmatic.Dmg(s, h); }
	override string LDClass() { return "LDPlasmaticShotgunBall2"; }
	override string FireSound() { return "Plasma/Fire"; }
	override string HitSound() { return "Plasma/Impact"; }
}

// Gyrojet (Epic: Pi, Sg, SS, Cg): "Fires mini-missiles"
class RSLD_Fx_Gyrojet : RSLD_G2_ProjFx
{
	override string LDClass() { return "LDGyrojetShotgunProjectile2"; }
	override string FireSound() { return "Weapons/GrenadeFire"; }
	override string HitSound() { return "Explosion"; }
	override double HitVol() { return 0.6; }	// LegenDoom's effects/gyrojet volume (EpicSpecialEffects.dec Death)
}
