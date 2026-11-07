// ld_g5_fx.zs -- G5 (R3b, round 3, 2026-11-06): LegenDoom 3.0's fire cadence and trigger effects on BD22 VR's guns.
// The shared machinery (the cadence, the trigger hold, the hand-action guards): ld_g5_core.zs. Every number:
// numbers_g5.zs (generated from LegenDoom's pk3 by ldl_patch/tools/numbers/g5.rules; each names its file:line).
// A cadence ratio is LegenDoom's own tics of its normal shot cycle over the effect's cycle, put on OUR gun's own cycle
// (scope section 0 "R"); our hand actions (pump by hand, break action, magazine, flick) are never sped (owner Q6).
// Proof lines (rsld_debug 1): every pull of a cadence effect logs "cadence xS: N tics since the last shot, the gun's
// own M" (M = N plus the tics the effect took off / minus those it added), so one held-trigger run shows the change.
// NOT built here (owner questions, R3B_DONE.md): Beam, Blazing (Q5 for these two is open), DualWield (which "twin
// pistols"), SixShooter's rate (LegenDoom's code fires faster, its text says slower: only its damage is built).

// ---- a cadence effect: a speed factor on the hand's trigger cycle, logged per pull
class RSLD_G5Speed : RSLD_G5Effect
{
	virtual double Speed(RSLD_Held c) { return 1.0; }

	override void WhileHeld(RSLD_Held c)
	{
		let h = HSc(c);
		h.v1 = Speed(c);
		RSLD_G5.Cadence(h, c, h.v1);
	}

	override void OnPull(RSLD_Shot s)
	{
		if (s.melee) return;
		LogPull(s);
	}

	void LogPull(RSLD_Shot s)
	{
		let h = HSs(s);
		int iv = h.prevPull > 0 ? s.tic - h.prevPull : -1;
		if (iv > 0 && iv <= 70)
			s.Log(String.Format("cadence x%.2f: %d tics since the last shot, the gun's own %d (%+d by the effect)", h.v1, iv, iv + h.saved, -h.saved));
		else
			s.Log(String.Format("cadence x%.2f: first shot", h.v1));
		h.prevPull = s.tic;
		h.saved = 0;
	}
}

// ---- Rapid (R: Fi Cs Pi Sg SS Cg RL PR BF), "Fires twice as fast": LegenDoom's pistol NormalFire cycle (4 + 15 - 5 =
// 14 tics) over its FireRapid (12 - 5 = 7): x2 on our gun's own cycle. Hand actions at hand speed.
class RSLD_Fx_Rapid : RSLD_G5Speed
{
	override double Speed(RSLD_Held c)
	{
		double r = Num("pi_cyc") - Num("pi_rf");
		return r > 0 ? RSLD_G5.BaseCycle() / r : 1.0;
	}
}

// ---- Trailblazing (C: all slots), "Fires faster the lower your health is": LegenDoom's FireTrailblazing skips one of
// its four 1-tic prefire frames at health <= 75, two at <= 50, three at <= 25 (14 -> 13 / 12 / 11 tics a shot).
class RSLD_Fx_Trailblazing : RSLD_G5Speed
{
	override double Speed(RSLD_Held c)
	{
		double base = Num("pre") + Num("end") - Num("end_rf");
		int hp = c.mo.health;
		int k = (hp <= Num("hp1") ? 1 : 0) + (hp <= Num("hp2") ? 1 : 0) + (hp <= Num("hp3") ? 1 : 0);
		return base - k > 0 ? base / (base - k) : 1.0;
	}
}

// ---- Hunting (U: Fi Pi Sg SS Cg RL PR BF), "Slower firerate, but higher damage and knockback": LegenDoom's pistol
// cycle 14 over FireHunting's 23 - 5 = 18 (x0.78), damage 15 over 5 (x3), its puff's ProjectileKickBack 160 (the
// engine's default 100: +60% knockback on what it hits). Owner (round 3): NO push on the player (LegenDoom's
// A_ChangeVelocity backwards is not carried).
class RSLD_Fx_Hunting : RSLD_G5Speed
{
	override double Speed(RSLD_Held c)
	{
		if (c.slot == 0) return 1.0;	// the VR fists: the arm is the cycle
		double r = Num("pi_cyc") - Num("pi_rf");
		return r > 0 ? RSLD_G5.BaseCycle() / r : 1.0;
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.pull == 0) return;
		double b = RSLD.Num("Base", "pi_dmg");
		if (b > 0) h.mult *= Num("pi_dmg") / b;
	}

	override void OnHit(RSLD_Shot s, RSLD_Hit h)
	{
		let t = h.target;
		if (s.pull == 0 || !t || t.health <= 0 || t.bDONTTHRUST || !s.mo || h.damage <= 0) return;
		// the engine's thrust is damage x 0.125 x kickback / mass (gzdoom p_interaction.cpp); the extra 60 of 160
		double extra = h.damage * 0.125 * (Num("kick") - 100.0) / max(t.Mass, 1);
		extra = clamp(extra, 0.0, 10.0);
		if (extra <= 0) return;
		t.Thrust(extra, s.mo.AngleTo(t));
		s.Log(String.Format("knockback +%.2f (ProjectileKickBack %d) on %s", extra, int(Num("kick")), t.GetClassName()));
	}
}

// ---- Advanced (R: Pi), "Fires rapidly, does more damage, but needs reloading": LegenDoom's FireAdvanced: random(18,21)
// (FBF_NORANDOM) where its pistol does 5 x random(1,3) (mean 10): x1.8..x2.1 rolled per pull; spread 2.2 of 5.6;
// its cycle FireAdvancedEnd 4 + the 1-tic refire loop = 5 tics (x2.8). Its magazine (LDAdvancedPistolAmmo) is OUR
// pistol's own magazine and hand reload (scope: "maps onto ours").
class RSLD_Fx_Advanced : RSLD_G5Speed
{
	override double Speed(RSLD_Held c)
	{
		double r = Num("cyc") + Num("loop");
		return r > 0 ? RSLD_G5.BaseCycle() / r : 1.0;
	}

	override void OnPull(RSLD_Shot s)
	{
		Super.OnPull(s);
		double mean = RSLD.Num("Base", "pi_dmg") * (1 + RSLD.Num("Base", "rnd_max")) / 2.0;
		s.d1 = mean > 0 ? random[rsld_g5](int(Num("dmg_lo")), int(Num("dmg_hi"))) / mean : 1.0;
	}

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		double b = RSLD.Num("Base", "pi_spread");
		if (b > 0 && !s.melee) p.spreadMul *= Num("spread") / b;
		return false;
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.pull > 0 && s.d1 > 0) h.mult *= s.d1;
	}
}

// ---- SixShooter (E: Pi), "Does 10x damage, slower fire rate": LegenDoom's FireSixShooterAttack: randompick(50, 60, ...
// 150) (FBF_NORANDOM, spread 0) where its pistol does 5 x random(1,3) (mean 10): x5..x15 rolled per pull in LegenDoom's
// steps of 10, perfect accuracy. The RATE is an owner question (LegenDoom's code fires every 7 tics, faster than its
// pistol's 14; its text says slower): the cycle is left as our gun's.
class RSLD_Fx_SixShooter : RSLD_G5Effect
{
	override void OnPull(RSLD_Shot s)
	{
		if (s.melee) return;
		double mean = RSLD.Num("Base", "pi_dmg") * (1 + RSLD.Num("Base", "rnd_max")) / 2.0;
		int lo = int(Num("dmg_lo")), hi = int(Num("dmg_hi"));
		int pick = lo + 10 * random[rsld_g5](0, max(0, (hi - lo) / 10));
		s.d1 = mean > 0 ? pick / mean : 1.0;
		s.Log(String.Format("six-shooter: randompick %d over LegenDoom's mean %.0f: x%.1f, spread 0", pick, mean, s.d1));
	}

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (!s.melee) p.spreadMul = Num("spread");	// 0
		return false;
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.pull > 0 && s.d1 > 0) h.mult *= s.d1;
	}
}

// ---- WindUp (R: Cg PR), "Starts slowly, winds up to 1 tic firing speed": LegenDoom counts shots (LDWindUpCounter, max
// 70) while the trigger stays down; its chaingun is 4 tics a shot (RCHG E 1 + FireWindUp0 3) until 20 shots, 3 until
// 50, 2 until 70, then 1 (FireWindUp3); let go and it starts again. Ours: the gun's own cycle for the first 20 shots,
// then LegenDoom's ratios (x4/3, x2), and at the top ONE SHOT A TIC (LegenDoom's "1 tic"), never faster.
class RSLD_Fx_WindUp : RSLD_G5Speed
{
	override double Speed(RSLD_Held c)
	{
		let h = HSc(c);
		double c0 = RSLD.Num("Base", "cg_cyc0") + Num("c0");	// 4
		int n = h.n1;
		double cyc = n >= Num("max") ? RSLD.Num("Base", "cg_cyc0") : (n >= Num("t2") ? RSLD.Num("Base", "cg_cyc0") + Num("c2") : (n >= Num("t1") ? RSLD.Num("Base", "cg_cyc0") + Num("c1") : c0));
		double sp = cyc > 0 ? c0 / cyc : 1.0;
		if (h.baseCyc > 0) sp = min(sp, double(h.baseCyc));	// one shot a tic at most
		return sp;
	}

	override void WhileHeld(RSLD_Held c)
	{
		let h = HSc(c);
		if (!RSLD_G5.Pressed(c.mo, c.hand) && c.idle > 1 && h.n1 > 0)
		{
			RSLD.Log(String.Format("WindUp: %s hand let go after %d shots: the count starts again", RSLD.HandName(c.hand), h.n1));
			h.n1 = 0;
		}
		Super.WhileHeld(c);
	}

	override void OnPull(RSLD_Shot s)
	{
		if (s.melee) return;
		let h = HSs(s);
		int iv = h.prevPull > 0 ? s.tic - h.prevPull : -1;
		if (h.n1 > 0 && h.n1 < Num("t1") && iv > 0 && iv <= 20) h.baseCyc = iv;	// the gun's own cycle, from its first (unchanged) shots
		h.n1 = min(h.n1 + 1, int(Num("max")));
		LogPull(s);
		s.Log(String.Format("wind-up count %d of %d (gun's own cycle %d tics)", h.n1, int(Num("max")), h.baseCyc));
	}
}

// ---- Focusing (U: Cg PR), "Increases in damage and accuracy the longer you shoot": LegenDoom's LDFocusingCounter (max
// 100) counts shots while the trigger stays down; tiers at 20 / 40 / 60 / 80 / 100: spread 5.6 4.5 3.4 2.3 1.2 0.1 and
// damage 5 6 7 8 9 10 (its chaingun's FireFocusing0..5). Ours: those ratios on our spread and damage; let go: 0.
class RSLD_Fx_Focusing : RSLD_G5Effect
{
	int Tier(int n)
	{
		if (n >= Num("max")) return 5;
		if (n >= Num("t4")) return 4;
		if (n >= Num("t3")) return 3;
		if (n >= Num("t2")) return 2;
		if (n >= Num("t1")) return 1;
		return 0;
	}

	override void OnPull(RSLD_Shot s)
	{
		if (s.melee) return;
		let h = HSs(s);
		int t = Tier(h.n1);
		double d0 = Num("d0"), s0 = Num("s0");
		s.d1 = d0 > 0 ? Num("d" .. t) / d0 : 1.0;
		s.d2 = s0 > 0 ? Num("s" .. t) / s0 : 1.0;
		h.n1 = min(h.n1 + 1, int(Num("max")));
		s.Log(String.Format("focusing: shot %d, tier %d: damage x%.2f, spread x%.2f", h.n1, t, s.d1, s.d2));
	}

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (!s.melee && s.d2 > 0) p.spreadMul *= s.d2;
		return false;
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.pull > 0 && s.d1 > 0) h.mult *= s.d1;
	}

	override void WhileHeld(RSLD_Held c)
	{
		let h = HSc(c);
		if (!RSLD_G5.Pressed(c.mo, c.hand) && c.idle > 1 && h.n1 > 0)
		{
			RSLD.Log(String.Format("Focusing: %s hand let go after %d shots: the count starts again", RSLD.HandName(c.hand), h.n1));
			h.n1 = 0;
		}
	}
}

// ---- Burst (U: Fi Pi Sg SS RL BF), "Fires three rapid attacks": one trigger pull = LegenDoom's 3 attacks (each its own
// round: its FireBurst takes 3 for the pull), 3 tics apart on the pistol (UPIS B C F, 1 tic each), 4 on the shotgun
// (USHT I J K L) and the other guns, the 2nd and 3rd with no second lead-in (its BFG charges once for its three balls).
// Ours: the gun's own Fire runs again for shots 2 and 3, on to the shot in that tic, from what is LOADED (owner Q6): the
// pump shotgun fires its burst from the tube, then waits for the hand's pump as now; the super shotgun fires what its
// barrels hold (a full one empties in its first blast: the burst ends there) and breaks open by hand as now. Nothing
// loaded, or the hand loading: the burst ends. The pistol's own burst mode (BD22's alt-fire PistolBurstFire) stands down
// while Burst powers the pistol (owner round 3, Q12: R3a's RSLD_AltDown, read by the pistols' AltFire). The VR fists:
// one real punch lands three strikes from the fist.
class RSLD_Fx_Burst : RSLD_G5Effect
{
	Array<Actor> mine;	// fist strikes this effect spawned (never a burst of their own)
	class<Actor> strikeCls[MAXPLAYERS];
	double strikeAng[MAXPLAYERS], strikePit[MAXPLAYERS], strikeSpd[MAXPLAYERS];
	int injTic[MAXPLAYERS * 2];		// the tic this effect started a burst shot (a hitscan pull comes inside ShootNow, a
									// projectile's pull with its WorldThingSpawned a tic later)

	int Shots() { return int(Num("shots")); }
	int Gap(int slot) { return slot == 2 ? 3 * int(Num("pi_frames")) : 4 * int(Num("sg_frames")); }

	override void OnPull(RSLD_Shot s)
	{
		if (s.melee) return;
		let h = HSs(s);
		int k = s.pn * 2 + s.hand;
		if (injTic[k] > 0 && s.tic - injTic[k] <= 1)
		{
			injTic[k] = 0;
			s.Log(String.Format("burst shot %d of %d", Shots() - h.n1, Shots()));
			h.tic1 = s.tic + Gap(s.slot);
			return;
		}
		h.n1 = Shots() - 1;
		h.w = s.weapon;
		h.tic1 = s.tic + Gap(s.slot);
		s.Log(String.Format("burst shot 1 of %d (the next %d tics apart, from what is loaded)", Shots(), Gap(s.slot)));
	}

	override void WhileHeld(RSLD_Held c)
	{
		let h = HSc(c);
		if (c.slot == 0) { FistBurst(c, h); return; }
		if (h.n1 <= 0 || level.maptime < h.tic1) return;
		if (c.weapon != h.w || RSLD_G5.Loading(c.mo) || !RSLD_G5.CanShoot(c.weapon, c.mo))
		{
			RSLD.Log(String.Format("Burst: %s: nothing loaded (or the hand is loading): the burst ends with %d left", c.weapon.GetClassName(), h.n1));
			h.n1 = 0;
			return;
		}
		Chamber(c.mo, c.weapon);
		h.n1--;
		int k = c.pn * 2 + c.hand;
		injTic[k] = level.maptime;
		bool ok = RSLD_G5.ShootNow(c.mo, c.hand, c.weapon);
		if (!ok) { RSLD.Log(String.Format("Burst: %s gave no shot: the burst ends with %d left", c.weapon.GetClassName(), h.n1)); h.n1 = 0; injTic[k] = 0; }
	}

	// BD22's pump shotgun keeps a spent shell chambered after a shot (ShotgunWasEmpty: its Fire then pumps instead):
	// a burst / second tap fires the next shell from the tube, the pump comes after
	static void Chamber(PlayerPawn mo, Weapon w)
	{
		if (!w) return;
		string cn = w.GetClassName();
		if (cn.IndexOf("Shot_Gun") < 0) return;
		class<Inventory> we = RSLD.IC("ShotgunWasEmpty");
		if (we) mo.TakeInventory(we, 999);
	}

	// the VR fists: a real punch (OnMelee) lands two more strikes of the same kind from the fist, Gap tics apart
	override void OnMelee(RSLD_Shot s, Actor strike)
	{
		if (!strike || mine.Find(strike) < mine.Size()) return;
		let h = HSs(s);
		h.n2 = Shots() - 1;
		h.tic1 = level.maptime + Gap(3);
		h.f2 = true;
		strikeCls[s.pn] = strike.GetClass();
		strikeAng[s.pn] = strike.angle;
		strikePit[s.pn] = strike.pitch;
		strikeSpd[s.pn] = strike.Vel.Length();
		s.Log(String.Format("burst: punch 1 of %d (%s)", Shots(), strike.GetClassName()));
	}

	void FistBurst(RSLD_Held c, RSLD_G5Hand h)
	{
		if (!h.f2 || h.n2 <= 0 || level.maptime < h.tic1) return;
		class<Actor> sc = strikeCls[c.pn];
		if (!sc) { h.n2 = 0; h.f2 = false; return; }
		let a = Actor.Spawn(sc, RSVR_VRHand.HandPos(c.mo), ALLOW_REPLACE);
		if (!a) { h.n2 = 0; h.f2 = false; return; }
		mine.Push(a);
		if (mine.Size() > 32) mine.Delete(0);
		a.target = c.mo;
		a.angle = strikeAng[c.pn];
		a.pitch = strikePit[c.pn];
		a.Vel3DFromAngle(strikeSpd[c.pn], a.angle, a.pitch);
		c.mo.A_StartSound("Melee/Swing", CHAN_AUTO, CHANF_OVERLAP);
		h.n2--;
		h.tic1 = level.maptime + Gap(3);
		RSLD.Log(String.Format("Burst: punch %d of %d from the fist", Shots() - h.n2, Shots()));
		if (h.n2 <= 0) h.f2 = false;
	}
}

// ---- Doubletap (R: Sg SS), "Attack twice before reloading, costs only 1 shot": LegenDoom's FireDoubletap: the first
// tap fires with no ammo used (A_FireBullets without FBF_USEAMMO) and no pump, the second takes the shell and pumps
// (LD<Gun>DoubleTap token). Ours: the first tap's rounds go back into the magazine (owner Q7: a free shot takes no round
// from it); while the gun then waits for the hand's pump (or runs BD22's own pump) a new trigger press fires the second
// tap from the tube, then the pump. Pumped in between: the next shot is the second tap.
// The super shotgun: its first blast is free (its shells stay in the barrels), the second empties them: break by hand.
class RSLD_Fx_Doubletap : RSLD_G5Effect
{
	override void OnPull(RSLD_Shot s)
	{
		if (s.melee) return;
		let h = HSs(s);
		if (!h.f2) { h.f2 = true; h.f1 = true; }
		s.b1 = h.f1;
		h.f1 = !h.f1;
		h.f3 = s.b1;
		h.tic1 = s.tic;
		s.Log(s.b1 ? "doubletap: first tap, free (its rounds go back); the second may come before the pump"
			: "doubletap: second tap, takes its rounds; then the pump / reload by hand");
	}

	override void AfterPull(RSLD_Shot s)
	{
		if (!s.b1) return;
		int n = s.magTaken > 0 ? s.magTaken : s.ammoTaken;
		if (n > 0) s.Refund(n);
	}

	override void WhileHeld(RSLD_Held c)
	{
		let h = HSc(c);
		bool p = RSLD_G5.Pressed(c.mo, c.hand);
		bool edge = p && !h.pressPrev;
		h.pressPrev = p;
		if (!h.f3) return;
		let psp = RSLD_G5.Psp(c.mo, c.hand);
		if (!psp || psp.Caller != c.weapon) { h.f3 = false; return; }
		if (level.maptime - h.tic1 < 2) return;
		if (RSLD_G5.InReady(c.weapon, psp.CurState)) { h.f3 = false; return; }	// pumped: the next shot is the second tap
		if (!edge || RSLD_G5.Loading(c.mo) || !RSLD_G5.CanShoot(c.weapon, c.mo)) return;
		h.f3 = false;
		RSLD_Fx_Burst.Chamber(c.mo, c.weapon);
		RSLD.Log(String.Format("Doubletap: %s hand: the second tap before the pump", RSLD.HandName(c.hand)));
		RSLD_G5.ShootNow(c.mo, c.hand, c.weapon);
	}
}

// ---- Chargeup (U: Fi Pi Sg SS Cg RL PR BF), "Can store multiple attacks and unleash them at once": LegenDoom's
// FireChargeup (its pistol): the trigger winds up 4 tics, then while it stays down one more attack is stored every 14
// tics (LDPistolChargeMiniCounter) up to 10 (LDPistolChargeup), each taking its round; let go and every stored attack
// fires in one tic, one sound (FireChargeupReleaseLoop: A_FireBullets once per stored attack); a tap fires one.
// Ours: while Chargeup is on the gun its trigger is held (the guns' Fire hook, RSLD_G5Block*); stored attacks are
// counted against what is LOADED (owner Q7); let go and the gun's own Fire runs once (its sound, flash, casing, from
// the drawn muzzle) and every other stored attack goes out with it in the same pull: each of its pellets again (our
// damage, its own spread re-rolled), each projectile again; their rounds come out of the magazine after the pull.
// Sounds: ours (scope 4: effects/chargeup, chargeupdone -> Plasma/Charge, Plasma/FullyCharged). The plasma gun's own
// charge alt fire stands down for this gun (owner round 3, Q12: R3a's shared rule). The VR fists: not built.
class RSLD_Fx_Chargeup : RSLD_G5Effect
{
	int extraN[MAXPLAYERS * 2];		// stored attacks beyond the gun's own shot, for the release pull
	int extraTic[MAXPLAYERS * 2];
	int relUntil[MAXPLAYERS * 2];		// the trigger is free from a release until its shot (or this tic)

	override void WhileHeld(RSLD_Held c)
	{
		let h = HSc(c);
		if (c.slot == 0) return;
		bool p = RSLD_G5.Pressed(c.mo, c.hand);
		int now = level.maptime;
		int k = c.pn * 2 + c.hand;
		// held, except from a release until its shot is out (a minigun spins up before its first shot): 35 tics at most
		RSLD_G5.Block(c.mo, c.hand, now > relUntil[k]);
		if (h.f1 && (c.weapon != h.w || now - h.tic2 > 1)) h.f1 = false;	// the gun left the hand mid-charge
		h.tic2 = now;
		if (p && !h.f1)
		{
			bool edge = !h.pressPrev;
			h.pressPrev = true;
			if (!edge || RSLD_G5.HandBusy(c.mo)) return;	// one charge per press; a hand reload or pump has the gun
			h.f1 = true; h.f2 = false; h.n1 = 0; h.tic1 = now + int(Num("pi_wind")); h.w = c.weapon;
			c.mo.A_StartSound("Plasma/Charge", CHAN_AUTO, CHANF_OVERLAP);
			RSLD.Log(String.Format("Chargeup: %s hand winds up (%d tics)", RSLD.HandName(c.hand), int(Num("pi_wind"))));
			return;
		}
		h.pressPrev = p;
		if (!h.f1) return;
		int loaded = RSLD_G5.Loaded(c.weapon, c.mo);
		int cap = int(Num("pi_max"));
		if (loaded >= 0) cap = min(cap, loaded);
		if (p)
		{
			if (now >= h.tic1 && h.n1 < cap)
			{
				h.n1++;
				h.tic1 = now + int(Num("pi_step"));
				RSLD.Log(String.Format("Chargeup: %d stored", h.n1));
				if (h.n1 >= cap && !h.f2) { h.f2 = true; c.mo.A_StartSound("Plasma/FullyCharged", CHAN_AUTO, CHANF_OVERLAP); }
			}
			return;
		}
		// let go: the stored attacks go out now (a tap: one, once the wind-up is over)
		if (now < h.tic1 && h.n1 == 0) { h.pressPrev = false; return; }
		h.f1 = false;
		int n = max(h.n1, 1);
		if (loaded >= 0) n = min(n, loaded);
		if (n <= 0) return;
		extraN[k] = n - 1;
		extraTic[k] = now;
		relUntil[k] = now + 35;
		RSLD_G5.Block(c.mo, c.hand, false);
		RSLD_Fx_Burst.Chamber(c.mo, c.weapon);
		bool ok = RSLD_G5.Shoot(c.mo, c.hand, c.weapon);
		RSLD.Log(String.Format("Chargeup: released %d stored attack%s in tic %d%s", n, n == 1 ? "" : "s", now, ok ? "" : " (the gun did not fire)"));
		if (!ok) { extraN[k] = 0; relUntil[k] = 0; }
	}

	int Extra(RSLD_Shot s)
	{
		int k = s.pn * 2 + s.hand;
		if (extraN[k] > 0 && level.maptime - extraTic[k] <= 70) return extraN[k];
		return 0;
	}

	override void OnPull(RSLD_Shot s)
	{
		if (s.melee) return;
		int k = s.pn * 2 + s.hand;
		s.i1 = Extra(s);
		extraN[k] = 0;
		relUntil[k] = 0;	// the release's shot is out: the trigger is held again
		if (s.i1 > 0) s.Log(String.Format("chargeup release: the gun's shot + %d stored", s.i1));
	}

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (s.i1 <= 0 || s.melee) return false;
		double da = Actor.DeltaAngle(p.aimAngle, p.angle), dp = p.pitch - p.aimPitch;
		for (int i = 0; i < s.i1; i++)
			s.FirePellet(p.aimAngle + da * frandom[rsld_g5](-1, 1), p.aimPitch + dp * frandom[rsld_g5](-1, 1), p.damage, p.puff, p.range, p.flags);
		return false;
	}

	override void OnMissile(RSLD_Shot s, Actor m)
	{
		if (s.i1 <= 0 || !m || s.i2 >= s.i1 * 8) return;
		for (int i = 0; i < s.i1; i++)
		{
			let c = Actor.Spawn(m.GetClass(), m.pos, ALLOW_REPLACE);
			if (!c) continue;
			c.target = s.mo;
			c.angle = m.angle + frandom[rsld_g5](-2, 2);
			c.pitch = m.pitch + frandom[rsld_g5](-1, 1);
			c.Vel3DFromAngle(m.Vel.Length(), c.angle, c.pitch);
			s.TagMissile(c);
			s.i2++;
		}
	}

	override void AfterPull(RSLD_Shot s)
	{
		if (s.i1 <= 0) return;
		int per = s.magTaken > 0 ? s.magTaken : s.ammoTaken;
		if (per <= 0) per = 1;
		s.Take(s.i1 * per);
		s.Log(String.Format("chargeup: %d more round%s out of the magazine for the stored attacks", s.i1 * per, s.i1 * per == 1 ? "" : "s"));
	}
}

// ---- Entrenched (R: Cg PR), "While firing, makes you immobile and gives you 50% resist and 2x damage": LegenDoom's
// FireEntrenched gives LDEntrenchedSpeedGiver and LDEntrenchedDamageResistanceGiver with every shot (its own items: 5 tics
// of speed 0 and DamageFactor 0.5) and fires 10 where its chaingun fires 5 (x2). The same items, our gun's damage x2.
class RSLD_Fx_Entrenched : RSLD_G5Effect
{
	override void OnPull(RSLD_Shot s)
	{
		if (s.melee) return;
		RSLD.Give(s.mo, "LDEntrenchedSpeedGiver");
		RSLD.Give(s.mo, "LDEntrenchedDamageResistanceGiver");
		s.Log(String.Format("entrenched: immobile + %.0f%% damage taken (LegenDoom's own powerups), damage x%.1f", Num("resist") * 100, Num("cg_dmg") / max(1, RSLD.Num("Base", "cg_dmg"))));
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		double b = RSLD.Num("Base", "cg_dmg");
		if (s.pull > 0 && b > 0) h.mult *= Num("cg_dmg") / b;
	}
}

// ---- Shielding (U: Cg PR), "While attacking, deploys an energy shield in front of you": LegenDoom's FireShielding
// spawns its LDShieldingShield (shootable, takes no damage, blocks shots, 9 tics) 32 units ahead with every shot.
// Ours: LegenDoom's own shield actor (round 2: its own visuals), 32 units ahead of the DRAWN muzzle along the barrel.
class RSLD_Fx_Shielding : RSLD_G5Effect
{
	override void OnPull(RSLD_Shot s)
	{
		if (s.melee || !s.mo) return;
		class<Actor> c = RSLD.AC("LDShieldingShield");
		if (!c) return;
		Vector3 at;
		double a, pt;
		[at, a, pt] = RSLD_G2.Muzzle(s.mo, s.hand, s.mo.angle, s.mo.pitch);
		double d = Num("ahead");
		Vector3 dir = (cos(a) * cos(pt), sin(a) * cos(pt), -sin(pt));
		let sh = Actor.Spawn(c, at + dir * d, NO_REPLACE);
		if (!sh) return;
		sh.angle = a;
		s.Log(String.Format("shield (LegenDoom's LDShieldingShield) %.0f units ahead of the muzzle", d));
	}
}

// ---- Quickdraw (C: Cs Pi Sg SS Cg RL PR BF), "Weapon switches instantly, has no prefire time": BD22 VR's own Instant
// Weapon Switch (rsq_instant_switch, on by default: rsq/switch.zs) already switches at once; with it off, a Quickdraw gun
// still comes up and goes down at once (its A_Raise / A_Lower find the gun at the top / bottom). No prefire: from the
// trigger to the shot the gun's own frames run in the same tic (BD22's charge-up frames on the BFG, the rocket
// launcher's lead-in), every state's action in order (as rsq/switch.zs runs the select frames).
class RSLD_Fx_Quickdraw : RSLD_G5Effect
{
	static bool InAny(Weapon w, State st, int which)
	{
		static const string SELECTS[] = { "Select", "SelectAnimation", "SelectAnimationEmpty", "FirstSelectAnimation", "SelectDual", "SelectDualEmpty" };
		static const string DESELECTS[] = { "Deselect", "DeselectEmpty", "DeselectContinue" };
		if (which)
		{
			for (int i = 0; i < DESELECTS.Size(); i++)
			{
				State b = w.FindStateByString(DESELECTS[i], true);
				if (b && Actor.InStateSequence(st, b)) return true;
			}
			return false;
		}
		for (int i = 0; i < SELECTS.Size(); i++)
		{
			State b = w.FindStateByString(SELECTS[i], true);
			if (b && Actor.InStateSequence(st, b)) return true;
		}
		return false;
	}

	override void WhileHeld(RSLD_Held c)
	{
		let h = HSc(c);
		let psp = RSLD_G5.Psp(c.mo, c.hand);
		if (!psp || !psp.CurState || psp.Caller != c.weapon) return;
		let p = c.mo.player;
		// switching: with BD22 VR's Instant Weapon Switch off, this gun still comes up / goes down at once
		cvar sw = CVar.GetCVar('rsq_instant_switch', p);
		if (c.hand == RSLD.MAIN && sw && !sw.GetBool())
		{
			if (psp.y < WEAPONBOTTOM && InAny(c.weapon, psp.CurState, 1)) psp.y = WEAPONBOTTOM;
			else if (psp.y > WEAPONTOP && InAny(c.weapon, psp.CurState, 0)) { psp.y = WEAPONTOP; psp.oldy = WEAPONTOP; }
		}
		// no prefire: the gun entered Fire and no shot came yet: run on to the shot now (once per Fire run)
		State f = c.weapon.FindState("Fire", true);
		bool inFire = f && Actor.InStateSequence(psp.CurState, f);
		if (!inFire) { h.f1 = false; return; }
		if (h.f1) return;
		h.f1 = true;
		let hh = RSLD.H();
		int lp = hh ? hh.LastPull(c.pn, c.hand) : -1000;
		if (level.maptime - lp <= 1) return;	// it shot on its first frame: no prefire
		int before = RSLD_G5.ShotCount(c.mo, c.hand);
		if (RSLD_G5.StepToShot(c.mo, c.hand, c.weapon, before, 48))
			RSLD.Log(String.Format("Quickdraw: %s: the prefire frames ran in tic %d (no prefire time)", c.weapon.GetClassName(), level.maptime));
	}
}

// ---- Recursive (C: Pi Sg SS Cg RL PR BF), "Fires more shots from their originally fired position for a short time":
// LegenDoom's LDRecursiveEffect<Gun> stays where the shot was fired and fires the same attack again 70 tics later and
// once more 70 after that (its pistol 1 bullet, shotgun 7, super shotgun 20; rockets / plasma / BFG their projectile).
// Ours: every pellet of the pull is fired again from the DRAWN muzzle's spot and the barrel's direction AT FIRE TIME
// (hitscan, our damage and puff; LAF_ABSPOSITION, so muzzle.zs and True Bullets leave it be), every projectile is
// launched again from where and how it left; our gun's own fire sound with each volley (scope 4).
class RSLD_G5Replay : Thinker
{
	RSLD_Fx_Recursive fx;
	PlayerPawn mo;
	int hand, due, left, gap, slot;
	string snd;
	Weapon w;
	Array<double> pAng, pPit, pRange, pX, pY, pZ;
	Array<int> pDmg, pFlags;
	Array<class<Actor> > pPuff;
	Array<class<Actor> > mCls;
	Array<double> mX, mY, mZ, mVX, mVY, mVZ, mAng, mPit;

	override void Tick()
	{
		if (!mo || mo.health <= 0 || !fx) { Destroy(); return; }
		if (level.maptime < due) return;
		Fire();
		left--;
		due = level.maptime + gap;
		if (left <= 0) Destroy();
	}

	void Fire()
	{
		fx.replaying = true;
		for (int i = 0; i < pAng.Size(); i++)
		{
			int fl = LAF_ABSPOSITION | (pFlags[i] & LAF_ISOFFHAND);
			mo.LineAttack(pAng[i], pRange[i], pPit[i], pDmg[i], 'Hitscan', pPuff[i], fl, null, pZ[i], pX[i], pY[i]);
		}
		for (int i = 0; i < mCls.Size(); i++)
		{
			if (!mCls[i]) continue;
			let m = Actor.Spawn(mCls[i], (mX[i], mY[i], mZ[i]), ALLOW_REPLACE);
			if (!m) continue;
			fx.mine.Push(m);
			if (fx.mine.Size() > 64) fx.mine.Delete(0);
			m.target = mo;
			m.angle = mAng[i];
			m.pitch = mPit[i];
			m.vel = (mVX[i], mVY[i], mVZ[i]);
		}
		fx.replaying = false;
		if (snd != "") mo.A_StartSound(snd, CHAN_AUTO, CHANF_OVERLAP);
		RSLD.Log(String.Format("Recursive: %d pellets and %d projectiles fired again from the spot of the shot (%d more to come)",
			pAng.Size(), mCls.Size(), left - 1));
	}
}

class RSLD_Fx_Recursive : RSLD_G5Effect
{
	bool replaying;
	Array<Actor> mine;
	RSLD_G5Replay recs[MAXPLAYERS * 2];

	RSLD_G5Replay Rec(RSLD_Shot s)
	{
		int k = s.pn * 2 + s.hand;
		let r = recs[k];
		if (r && r.due == s.tic + int(Num("delay"))) return r;	// this pull's
		r = new("RSLD_G5Replay");
		r.fx = self; r.mo = s.mo; r.hand = s.hand; r.slot = s.slot; r.w = s.weapon;
		r.due = s.tic + int(Num("delay"));
		r.gap = int(Num("delay2"));
		r.left = 2;
		r.snd = RSLD_G5.FireSound(s.weapon, s.slot);
		recs[k] = r;
		s.Log(String.Format("recursive: this shot comes again from here in %d and %d tics", int(Num("delay")), int(Num("delay") + Num("delay2"))));
		return r;
	}

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (replaying || s.melee || (p.flags & LAF_ISMELEEATTACK) || !s.mo) return false;
		let r = Rec(s);
		Vector3 at;
		double a, pt;
		[at, a, pt] = RSLD_G2.Muzzle(s.mo, s.hand, p.aimAngle + Actor.DeltaAngle(p.aimAngle, p.angle) * p.spreadMul,
			p.aimPitch + (p.pitch - p.aimPitch) * p.spreadMul);
		r.pAng.Push(a); r.pPit.Push(pt); r.pRange.Push(p.range > 0 ? p.range : PLAYERMISSILERANGE);
		r.pX.Push(at.x); r.pY.Push(at.y); r.pZ.Push(at.z);
		r.pDmg.Push(p.damage); r.pFlags.Push(p.flags); r.pPuff.Push(p.puff);
		return false;
	}

	override void OnMissile(RSLD_Shot s, Actor m)
	{
		if (replaying || !m || mine.Find(m) < mine.Size()) return;
		let r = Rec(s);
		r.mCls.Push(m.GetClass());
		r.mX.Push(m.pos.x); r.mY.Push(m.pos.y); r.mZ.Push(m.pos.z);
		r.mVX.Push(m.vel.x); r.mVY.Push(m.vel.y); r.mVZ.Push(m.vel.z);
		r.mAng.Push(m.angle); r.mPit.Push(m.pitch);
	}
}
