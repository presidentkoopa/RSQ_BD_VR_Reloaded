// ld_g11_stream.zs -- LD mode, round 4 (2026-11-06): LegenDoom 3.0's STREAM effects on BD22 VR's guns.
// Owner, round 4: "Beam / Blazing: LegenDoom's stream from our drawn muzzle, our sounds." "Prototype: a stream while the
// trigger is held." Numbers: numbers_g11.zs (ldl_patch/tools/numbers/g11.rules, each with its LegenDoom file:line).
//
// The gun's own shot is REPLACED (LegenDoom's Fire jumps to FireBeam / FireBlazing / FirePrototype): while the hand's gun
// carries the effect its trigger is held off (ld_g5_core.zs RSLD_G5.Block: the gun's Fire goes to its RSLD_Jammed state)
// and the stream fires instead, every tic the hand's trigger is down, from the DRAWN muzzle along the barrel
// (RSLD_G2.Muzzle: the controller in VR), after LegenDoom's own charge (its FireBeam / FireBlazing / FirePrototype frames).
//   Beam      (R: PR BF)     a hitscan a tic: LegenDoom's 5 x random(1,8), its beam model (LD_PlasmaBeamPuff /
//                            LD_BFGBeamPuff: beam.md3 stretched from the muzzle to the hit, as LEGENDBEM.acs LD_3DBeam
//                            does it from LegenDoom's view point), its impact and emitter; let go: one last shot
//                            (LD_FinalBeamPuff, PR 5 / BFG 15 x random(1,8)). Sounds: Unmaker/Start, Unmaker/Loop, Unmaker/Stop.
//   Blazing   (R: RL PR BF)  a flame a tic (LegenDoom's LDBlazingRocket / LDBlazingPlasmaBall / LDBlazingBFGBall: its
//                            short-range burning projectiles, their damage and visuals), the BFG three a tic. Sounds:
//                            Flamer/loop, Flamer/stop (BD22's flamethrower). LegenDoom's flame death sound is cleared.
//   Prototype (E: BF)        charge (LegenDoom's 15 tics), then a pair of LegenDoom's Prototype plasma balls a tic,
//                            green and red pairs in turn. Sounds: BFG/Charge, Plasma/Fire a pair, Plasma/Impact on burst
//                            (LegenDoom's plasmarifle/impact in their Death state is silenced: RSLD_G3.Silence).
// Ratios (scope section 0 "R"): damage x (our projectile's direct hit / LegenDoom's: Rocket2 150 / 20 x 4.5, Plasma_Ball
// 40 / 5 x 4.5, SuperBFGBall 1500 / 100 x 4.5); ammo a tic x (our shot's cost / LegenDoom's: the magazine's one round /
// the PR's 1 cell, our BFG's 50 cells / its 40). The rocket launcher's Blazing burns LegenDoom's fuel: a rocket out of the
// magazine gives 10 tics (the first of a press) or 25 (LDBlazingRocketFuel's max). Ammo comes out of the MAGAZINE (owner
// Q7), the reserve on guns without one; nothing loaded: the stream ends. Never without LegenDoom (no hook is called).

class RSLD_StreamHand play
{
	int phase;			// 0 idle, 1 charging (LegenDoom's lead), 2 streaming
	int lead, tics, used, seen, fuel, alt;
	double acc;
	bool prev;
	RSLD_Shot s;
	Weapon w;
}

// a stream left behind (the gun left the hand mid-stream): its loop sound stops, its pull ends
class RSLD_StreamGuard : Thinker
{
	RSLD_StreamFx fx;
	RSLD_StreamHand h;
	PlayerPawn mo;
	int hand;
	override void Tick()
	{
		if (!h || !fx || h.phase == 0) { Destroy(); return; }
		if (level.maptime - h.seen > 1) { fx.EndStream(h, mo, hand, false); Destroy(); }
	}
}

class RSLD_StreamFx : RSLD_Effect
{
	RSLD_StreamHand handSt[MAXPLAYERS * 2];
	Array<Actor> balls;		// projectiles of ours in flight (their LegenDoom sounds are silenced when they burst)
	Array<double> ourDirect;	// cache: our projectile's direct hit per slot (6 RL, 7 PR, 8 BF)

	const SND_CH = 9301;		// the loop sound's channel (+ hand)

	RSLD_StreamHand HS(int pn, int hand)
	{
		int k = clamp(pn * 2 + hand, 0, MAXPLAYERS * 2 - 1);
		if (!handSt[k]) handSt[k] = new("RSLD_StreamHand");
		return handSt[k];
	}

	virtual bool Streams(int slot) { return false; }
	virtual int LeadTics(int slot) { return 0; }
	virtual double LDCost(int slot) { return 1; }	// LegenDoom's units a tic (cells; rockets: see Blazing)
	virtual int LDMin(int slot) { return 1; }		// LegenDoom's units needed to keep going
	virtual void OnStart(RSLD_StreamHand h, PlayerPawn mo, int hand) {}
	virtual void Emit(RSLD_StreamHand h, PlayerPawn mo, int hand, int slot, Vector3 at, double a, double p) {}
	virtual void OnEnd(RSLD_StreamHand h, PlayerPawn mo, int hand, int slot, bool released) {}
	virtual string LoopSound() { return ""; }

	// ---- our numbers
	static int Kind(int slot) { return slot == 6 ? RSLD_G3.K_ROCKET : (slot == 7 ? RSLD_G3.K_PLASMA : RSLD_G3.K_BFG); }
	static string OurProjectile(int slot) { return slot == 6 ? "Rocket2" : (slot == 7 ? "Plasma_Ball" : "SuperBFGBall"); }
	double DamageRatio(int slot)
	{
		if (slot < 6 || slot > 8) return 1;
		while (ourDirect.Size() < 9) ourDirect.Push(0);
		if (ourDirect[slot] <= 0)
		{
			class<Actor> c = RSLD.AC(OurProjectile(slot));
			if (c)
			{
				let a = Actor.Spawn(c, (0, 0, 0), NO_REPLACE);	// a dummy that never ticks (as RSLD_G7.StrikeDamage)
				if (a) { ourDirect[slot] = a.GetMissileDamage(0, 1); a.Destroy(); }
			}
		}
		double ld = RSLD_G3.LDBase(Kind(slot)) * RSLD_G3.RndMean();
		return (ourDirect[slot] > 0 && ld > 0) ? ourDirect[slot] / ld : 1;
	}
	// what one of our shots costs over what one of LegenDoom's costs (its Weapon.AmmoUse1)
	static double AmmoRatio(Weapon w, PlayerPawn mo, int slot)
	{
		if (!w) return 1;
		bool mag = w.Ammo2 && w.Ammo2 != w.Ammo1 && Pool(w, mo) == w.Ammo2;
		double ours = mag ? 1 : max(1, w.AmmoUse1);	// the magazine: one round a shot (Plasma.dec, RocketLauncher.dec); else Weapon.AmmoUse (BFG.dec 50)
		double lds = slot == 8 ? RSLD.Num("Stream", "bf_ammo") : (slot == 7 ? RSLD.Num("Stream", "pr_ammo") : 1);
		return lds > 0 ? ours / lds : 1;
	}
	// the pool the gun's shot comes out of (the magazine; the reserve without one: BD22's Purist / no-reload play)
	static Inventory Pool(Weapon w, PlayerPawn mo)
	{
		if (!w) return null;
		bool noMag = !w.Ammo2 || w.Ammo2 == w.Ammo1 || RSLD.Has(mo, "IsPlayingAsPurist") > 0 || RSLD.Has(mo, "NoReloading") > 0;
		return noMag ? w.Ammo1 : w.Ammo2;
	}
	static bool Infinite(PlayerPawn mo)
	{
		cvar c = cvar.FindCvar("sv_infiniteammo");
		return (c && c.GetBool()) || mo.FindInventory("PowerInfiniteAmmo", true) != null;
	}

	// n of our rounds out of the pool for this tic (fractions carried); false: not enough
	bool Pay(RSLD_StreamHand h, PlayerPawn mo, Weapon w, double need)
	{
		if (Infinite(mo)) return true;
		let pool = Pool(w, mo);
		if (!pool) return true;
		h.acc += need;
		int n = int(h.acc);
		if (n <= 0) return true;
		if (pool.Amount < n) return false;
		pool.Amount -= n;
		h.acc -= n;
		h.used += n;
		return true;
	}
	bool CanStart(PlayerPawn mo, Weapon w, int slot)
	{
		if (Infinite(mo)) return true;
		let pool = Pool(w, mo);
		if (!pool) return true;
		return pool.Amount >= int(ceil(LDMin(slot) * AmmoRatio(w, mo, slot)));
	}

	override void WhileHeld(RSLD_Held c)
	{
		Silence();
		if (!Streams(c.slot)) return;
		RSLD_G5.Block(c.mo, c.hand, true);	// LegenDoom replaces the gun's shot: ours never fires while it carries this
		let h = HS(c.pn, c.hand);
		h.seen = level.maptime;
		bool p = RSLD_G5.Pressed(c.mo, c.hand);
		if (h.w != c.weapon && h.phase) EndStream(h, c.mo, c.hand, false);
		h.w = c.weapon;
		bool edge = p && !h.prev;
		h.prev = p;
		if (h.phase == 0)
		{
			if (!edge || RSLD_G5.HandBusy(c.mo)) return;
			if (!CanStart(c.mo, c.weapon, c.slot)) { RSLD.Log(String.Format("%s: %s hand: not enough loaded to start", name, RSLD.HandName(c.hand))); return; }
			let hh = RSLD.H();
			h.s = hh ? hh.NewPull(c.mo, c.hand, c.weapon, false) : null;
			if (!h.s) return;
			h.phase = 1; h.lead = LeadTics(c.slot); h.tics = 0; h.used = 0; h.acc = 0;
			let g = new("RSLD_StreamGuard");
			g.fx = self; g.h = h; g.mo = c.mo; g.hand = c.hand;
			OnStart(h, c.mo, c.hand);
			h.s.Log(String.Format("%s: %s stream starts (LegenDoom's charge %d tics), damage x%.2f, ammo x%.2f a tic", name, c.weapon.GetClassName(), h.lead, DamageRatio(c.slot), AmmoRatio(c.weapon, c.mo, c.slot)));
		}
		if (h.phase == 1)
		{
			if (h.lead-- > 0) { Keep(h, c); return; }
			if (!p) { EndStream(h, c.mo, c.hand, true); return; }	// let go during the charge: LegenDoom's final shot only
			h.phase = 2;
			string ls = LoopSound();
			if (ls != "") c.mo.A_StartSound(ls, SND_CH + c.hand, CHANF_LOOPING, 1.0);
		}
		if (h.phase == 2)
		{
			if (!p || RSLD_G5.HandBusy(c.mo)) { EndStream(h, c.mo, c.hand, true); return; }
			if (!Pay(h, c.mo, c.weapon, LDCost(c.slot) * AmmoRatio(c.weapon, c.mo, c.slot))) { h.s.Log(String.Format("%s: nothing left loaded", name)); EndStream(h, c.mo, c.hand, true); return; }
			Keep(h, c);
			Vector3 at;
			double a, pt;
			[at, a, pt] = RSLD_G2.Muzzle(c.mo, c.hand, c.mo.angle, c.mo.pitch);
			Emit(h, c.mo, c.hand, c.slot, at, a, pt);
			if (h.phase != 2 || !h.s) return;	// the stream ended inside (no rocket left for fuel)
			h.tics++;
			if (h.tics == 1 || h.tics % 35 == 0) h.s.Log(String.Format("%s: streaming %d tics, %d rounds used (%s %d left)", name, h.tics, h.used, Pool(c.weapon, c.mo) ? Pool(c.weapon, c.mo).GetClassName() : 'none', Pool(c.weapon, c.mo) ? Pool(c.weapon, c.mo).Amount : 0));
			if (h.tics % 10 == 1) c.mo.SoundAlert(c.mo);	// LegenDoom's A_AlertMonsters every tic: a tenth of the cost
		}
	}

	// the pull stays this stream's: its tic, the hand's last pull
	void Keep(RSLD_StreamHand h, RSLD_Held c)
	{
		if (!h.s) return;
		h.s.lastTic = level.maptime;
		let hh = RSLD.H();
		if (hh) hh.lastPullTic[c.pn * 2 + c.hand] = level.maptime;
	}

	void EndStream(RSLD_StreamHand h, PlayerPawn mo, int hand, bool released)
	{
		if (!h || h.phase == 0) return;
		int slot = h.s ? h.s.slot : -1;
		if (mo)
		{
			string ls = LoopSound();
			if (ls != "") mo.A_StopSound(SND_CH + hand);
			OnEnd(h, mo, hand, slot, released);
		}
		if (h.s) h.s.Log(String.Format("%s: stream ends (%s) after %d tics, %d rounds used", name, released ? "let go / empty" : "the gun left the hand", h.tics, h.used));
		h.phase = 0;
		h.s = null;
	}

	// a projectile of the stream: tagged to the pull (its damage is the pull's: x the damage ratio below)
	Actor Shoot(RSLD_StreamHand h, PlayerPawn mo, string cls, Vector3 at, double a, double p, bool track = false)
	{
		class<Actor> c = RSLD.AC(cls);
		if (!c || !h.s) return null;
		let b = Actor.Spawn(c, at, NO_REPLACE);
		if (!b) return null;
		b.target = mo;
		b.angle = a; b.pitch = p;
		b.Vel3DFromAngle(b.Speed, a, p);
		b.DeathSound = "";		// LegenDoom's impact sound (scope 4: never LegenDoom's gun / effect sounds)
		h.s.TagMissile(b);
		if (track) { balls.Push(b); if (balls.Size() > 128) balls.Delete(0, 32); }
		return b;
	}

	// LegenDoom's Prototype balls call their impact sound in their Death state: stopped, ours instead
	void Silence()
	{
		for (int i = balls.Size() - 1; i >= 0; i--)
		{
			let b = balls[i];
			if (!b) { balls.Delete(i); continue; }
			if (b.bMISSILE) continue;
			RSLD_G3.Silence(b, 4);
			b.A_StartSound("Plasma/Impact", CHAN_AUTO, CHANF_OVERLAP, 0.6);
			balls.Delete(i);
		}
	}

	// LegenDoom's number on our gun: x our projectile's direct hit over LegenDoom's (every LegenDoom actor of the stream)
	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		if (s.pull <= 0 || !h.inflictor) return;
		string ic = h.inflictor.GetClassName();
		if (ic.Left(2) != "LD") return;
		h.mult *= DamageRatio(s.slot);
	}
}

// ---- Beam (R: PR BF), "Fires a constant, high damage energy beam"
class RSLD_Fx_Beam : RSLD_StreamFx
{
	override bool Streams(int slot) { return slot == 7 || slot == 8; }
	override int LeadTics(int slot) { return int(Num(slot == 8 ? "bf_lead" : "pr_lead")); }
	override double LDCost(int slot) { return Num(slot == 8 ? "bf_cell" : "pr_cell"); }
	override int LDMin(int slot) { return int(Num(slot == 8 ? "bf_min" : "pr_min")); }
	override string LoopSound() { return "Unmaker/Loop"; }
	override void OnStart(RSLD_StreamHand h, PlayerPawn mo, int hand) { mo.A_StartSound(h.s && h.s.slot == 8 ? "BFG/Charge" : "Unmaker/Start", CHAN_AUTO, CHANF_OVERLAP); }

	override void Emit(RSLD_StreamHand h, PlayerPawn mo, int hand, int slot, Vector3 at, double a, double p)
	{
		Ray(h, mo, slot, at, a, p, int(Num(slot == 8 ? "bf_dmg" : "pr_dmg")), slot == 8 ? "LD_BFGBeamPuff" : "LD_PlasmaBeamPuff",
			slot == 8 ? "LD_BFGBeamImpact" : "LD_PlasmaBeamImpact", slot == 8 ? "LDBFGBeamEmitter" : "LDPlasmaBeamEmitter");
	}

	override void OnEnd(RSLD_StreamHand h, PlayerPawn mo, int hand, int slot, bool released)
	{
		mo.A_StartSound("Unmaker/Stop", CHAN_AUTO, CHANF_OVERLAP);
		if (!released || !h.s || !h.w) return;
		// FireBeamFinal: one more cell, LD_FinalBeamPuff's shot and its rail look
		if (!Pay(h, mo, h.w, Num(slot == 8 ? "bf_cell" : "pr_cell") * AmmoRatio(h.w, mo, slot))) return;
		Vector3 at;
		double a, p;
		[at, a, p] = RSLD_G2.Muzzle(mo, hand, mo.angle, mo.pitch);
		Ray(h, mo, slot, at, a, p, int(Num(slot == 8 ? "bf_fdmg" : "pr_fdmg")), "LD_FinalBeamPuff", "", "LDFinalBeamEmitter");
		h.s.Log("beam: the last shot (LegenDoom's FireBeamFinal)");
	}

	// LegenDoom's A_FireBullets(0, 0, -1, dmg x random(1,8)) along the barrel from the drawn muzzle: the first thing or wall
	void Ray(RSLD_StreamHand h, PlayerPawn mo, int slot, Vector3 at, double a, double p, int dmg, string beamCls, string impCls, string emitCls)
	{
		FLineTraceData d;
		mo.LineTrace(a, PLAYERMISSILERANGE, p, TRF_ABSPOSITION, at.z, at.x, at.y, d);
		Vector3 hit = d.HitLocation;
		if (d.HitType == TRACE_HitNone) hit = at + (cos(a) * cos(p), sin(a) * cos(p), -sin(p)) * PLAYERMISSILERANGE;
		// the beam model from the muzzle to the hit (LEGENDBEM.acs LD_3DBeam: angle + 180, pitch -(90 - elevation), length / 77)
		Vector3 dv = hit - at;
		double hd = dv.xy.Length(), len = dv.Length();
		let bm = RSLD.LDVisual(beamCls, at, "Spawn", 2, mo);
		if (bm)
		{
			bm.angle = VectorAngle(dv.x, dv.y) + 180;
			bm.pitch = -(90 - atan2(dv.z, max(hd, 0.001)));
			bm.Scale.Y = len / max(1.0, Num("len"));
			let hh = RSLD.H();
			if (hh && h.s) hh.Tag(bm, h.s);
		}
		if (emitCls != "") { class<Actor> ec = RSLD.AC(emitCls); if (ec) Actor.Spawn(ec, at, NO_REPLACE); }
		if (impCls != "" && d.HitType != TRACE_HitNone) { class<Actor> ic = RSLD.AC(impCls); if (ic) Actor.Spawn(ic, hit, NO_REPLACE); }
		let t = d.HitActor;
		if (d.HitType == TRACE_HitActor && t && t.bSHOOTABLE && t != mo)
		{
			int n = dmg * random[rsld_beam](1, int(Num(slot == 8 ? "bf_rnd" : "pr_rnd")));
			t.DamageMobj(bm ? bm : Actor(mo), mo, n, 'Plasma');	// the beam model is the inflictor (tagged: this pull's damage)
		}
	}
}

// ---- Blazing (R: RL PR BF), "Fires a constant, short range, flamethrower"
class RSLD_Fx_Blazing : RSLD_StreamFx
{
	override bool Streams(int slot) { return slot == 6 || slot == 7 || slot == 8; }
	override int LeadTics(int slot) { return int(Num(slot == 6 ? "rl_lead" : (slot == 7 ? "pr_lead" : "bf_lead"))); }
	override double LDCost(int slot) { return slot == 8 ? Num("bf_cell") : (slot == 7 ? RSLD.Num("Stream", "pr_ammo") : 0); }
	override string LoopSound() { return "Flamer/loop"; }
	override void OnStart(RSLD_StreamHand h, PlayerPawn mo, int hand) { mo.A_StartSound(h.s && h.s.slot == 8 ? "BFG/Charge" : "Flamer/Select", CHAN_AUTO, CHANF_OVERLAP); }
	override void OnEnd(RSLD_StreamHand h, PlayerPawn mo, int hand, int slot, bool released) { mo.A_StartSound("Flamer/stop", CHAN_AUTO, CHANF_OVERLAP); }

	override void Emit(RSLD_StreamHand h, PlayerPawn mo, int hand, int slot, Vector3 at, double a, double p)
	{
		double sp = Num("spread");
		h.alt = (h.alt + 1) % 4;	// LegenDoom's LDBeamBFGFrame: frame 1 of 4 fires the first class, the rest the "2"
		if (slot == 6)
		{	// LegenDoom's rocket fuel: a rocket out of the magazine for 10 tics (the first of a press) or 25
			if (h.fuel <= 0)
			{
				let pool = Pool(h.w, mo);
				if (pool && !Infinite(mo))
				{
					if (pool.Amount <= 0) { h.s.Log("blazing: no rocket left for fuel"); EndStream(h, mo, hand, true); return; }
					pool.Amount--; h.used++;
				}
				h.fuel = int(h.tics == 0 ? Num("rl_first") : Num("rl_refill"));
				h.s.Log(String.Format("blazing: a rocket burnt for %d tics of fuel (LegenDoom's LDBlazingRocketFuel)", h.fuel));
			}
			h.fuel -= int(Num("rl_fuel"));
			Shoot(h, mo, h.alt == 0 ? "LDBlazingRocket" : "LDBlazingRocket2", at, a + frandom[rsld_blz](-sp, sp), p);
		}
		else if (slot == 7) Shoot(h, mo, h.alt == 0 ? "LDBlazingPlasmaBall" : "LDBlazingPlasmaBall2", at, a + frandom[rsld_blz](-sp, sp), p);
		else
		{
			double side = Num("bf_side");
			Shoot(h, mo, h.alt == 0 ? "LDBlazingBFGBall" : "LDBlazingBFGBall2", at, a + frandom[rsld_blz](-sp, sp), p);
			Shoot(h, mo, "LDBlazingBFGBall2", at, a + side + frandom[rsld_blz](-sp, sp), p);
			Shoot(h, mo, "LDBlazingBFGBall2", at, a - side + frandom[rsld_blz](-sp, sp), p);
		}
	}
}

// ---- Prototype (E: BF), "Sprays huge amounts of plasma projectiles"
class RSLD_Fx_Prototype : RSLD_StreamFx
{
	override bool Streams(int slot) { return slot == 8; }
	override int LeadTics(int slot) { return int(Num("lead")); }
	override double LDCost(int slot) { return Num("cell"); }
	override void OnStart(RSLD_StreamHand h, PlayerPawn mo, int hand) { mo.A_StartSound("BFG/Charge", CHAN_AUTO, CHANF_OVERLAP); }

	override void Emit(RSLD_StreamHand h, PlayerPawn mo, int hand, int slot, Vector3 at, double a, double p)
	{
		double sp = Num("spread");
		h.alt = (h.alt + 1) % 4;
		if (h.alt % 2 == 0)
		{	// FirePrototypeGreen: one straight, one +-2
			Shoot(h, mo, "LDPrototypeBFGBallGreen", at, a, p, true);
			Shoot(h, mo, "LDPrototypeBFGBallGreen2", at, a + frandom[rsld_pro](-sp, sp), p + frandom[rsld_pro](-sp, sp), true);
		}
		else
		{	// FirePrototypeRed: two, side by side (2 / 4 units: LegenDoom's spawn offsets), +-2
			double side = Num("side") * (h.alt == 1 ? 1 : 2);
			Vector3 r = (sin(a), -cos(a), 0) * side;
			Shoot(h, mo, "LDPrototypeBFGBallRed", at - r, a + frandom[rsld_pro](-sp, sp), p + frandom[rsld_pro](-sp, sp), true);
			Shoot(h, mo, "LDPrototypeBFGBallRed2", at + r, a + frandom[rsld_pro](-sp, sp), p + frandom[rsld_pro](-sp, sp), true);
		}
		mo.A_StartSound("Plasma/Fire", CHAN_WEAPON, 0, 0.6);
	}
}
