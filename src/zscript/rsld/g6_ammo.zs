// LD mode, G6: LegenDoom's ammo effects on BD22 VR's magazines (round 3, agent R3a), and BD22 VR's alt-fire stand-down.
//
// Owner Q7 (2026-11-06): ammo effects act on the MAGAZINE; a free shot takes no round from it; reload by hand as now.
// "Without ammo" (Illegal, Optional, Transmogrifier) is read as: on the magazine's last round. A shot fired with the
// last round(s) is LegenDoom's no-ammo shot and gives the round(s) back, so the magazine never runs dry while the
// gun carries the effect (the player still reloads by hand whenever he likes). Guns with no magazine (BD22's BFG,
// BD22 VR's MiniGun) use their one pool the same way. "Last round" = the pool before the shot was no more than one
// shot takes (learned per gun class from its last shot; 1 until it has fired).
// LegenDoom's four ammo kinds are BD22's items that replace them (tables.zs Repl): Clip -> Clip2, Shell -> AmmoShell,
// RocketAmmo -> AmmoRocket, Cell -> AmmoCell.

class RSLD_G6 play
{
	static string KindCls(string k)
	{
		if (k == "Clip") return "Clip2";
		if (k == "Shell") return "AmmoShell";
		if (k == "RocketAmmo" || k == "Rocket") return "AmmoRocket";
		if (k == "Cell") return "AmmoCell";
		return "";
	}
	// LegenDoom's per-gun key prefix (numbers_g3.zs) for a slot
	static string GunKey(int slot)
	{
		switch (slot) { case 2: return "pi"; case 3: return "sg"; case 4: return "ss"; case 5: return "cg"; case 6: return "rl"; case 7: return "pr"; case 8: return "bf"; }
		return "";
	}
	static bool HasMag(Weapon w) { return w && w.Ammo2 && w.Ammo2 != w.Ammo1; }
	static Inventory Pool(Weapon w) { return HasMag(w) ? w.Ammo2 : (w ? w.Ammo1 : null); }

	// the per-gun-class size of one shot, learned from the shots fired (RSLD_G6Reg)
	static int ShotSize(RSLD_Shot s)
	{
		let g = RSLD_G6Reg.Get();
		if (!s.weapon) return 1;
		int k = g.sizeCls.Find(s.weapon.GetClassName());
		if (k < g.sizeCls.Size()) return g.sizeN[k];
		int u = HasMag(s.weapon) ? s.weapon.AmmoUse2 : s.weapon.AmmoUse1;
		return max(1, u);
	}
	static void LearnSize(RSLD_Shot s, int taken)
	{
		if (!s.weapon || taken <= 0) return;
		let g = RSLD_G6Reg.Get();
		Name n = s.weapon.GetClassName();
		int k = g.sizeCls.Find(n);
		if (k < g.sizeCls.Size()) g.sizeN[k] = taken; else { g.sizeCls.Push(n); g.sizeN.Push(taken); }
	}
	// this pull fires the pool's last round(s): LegenDoom's "without ammo" shot
	static bool LastRound(RSLD_Shot s)
	{
		if (!s.weapon) return false;
		int pre = HasMag(s.weapon) ? s.preMag : s.preRes;
		return pre > 0 && pre <= ShotSize(s);
	}
	static int Taken(RSLD_Shot s) { return HasMag(s.weapon) ? s.magTaken : s.resTaken; }

	// owner, round 4: "Transmogrifier / Overflowing: all BD22 ammo counts (Upgrading's mapping)". Every BD22 reserve ammo
	// belongs to one of LegenDoom's four kinds: the kind's own item (Clip2 / AmmoShell / AmmoRocket / AmmoCell; BD22 VR's
	// RSQ_MinigunAmmo is the chaingun's clip ammo) and the ammo of BD22's guns outside LegenDoom's nine, as Upgrading
	// counts them (ld_g8_rules.zs RSLD_B.OnlyKind: Gas / SoulAmmo -> Cell, GrenadeAmmo / AmmoM202 / MiniHellRocketAmmo /
	// Nuke / DevastatorAmmo -> Rocket, Mauser9mm / SniperAmmo / Clip1 -> Clip). Magazines are not reserves.
	static int KindIndex(string k)
	{
		if (k == "Clip") return 0;
		if (k == "Shell") return 1;
		if (k == "RocketAmmo" || k == "Rocket") return 2;
		if (k == "Cell") return 3;
		return -1;
	}
	static int KindOfAmmo(Name n)
	{
		switch (n)
		{
			case 'Clip2': case 'RSQ_MinigunAmmo': return 0;
			case 'AmmoShell': return 1;
			case 'AmmoRocket': return 2;
			case 'AmmoCell': return 3;
		}
		return RSLD_B.OnlyKind(n);
	}
	// the player's BD22 reserves of a kind, the kind's own item first
	static void KindAmmo(Actor p, string kind, out Array<Inventory> l)
	{
		l.Clear();
		int ki = KindIndex(kind);
		if (!p || ki < 0) return;
		let own = RSLD.IC(KindCls(kind));
		let oi = own ? p.FindInventory(own) : null;
		if (oi) l.Push(oi);
		for (let i = p.Inv; i; i = i.Inv)
		{
			if (i == oi || !(i is "Ammo")) continue;
			let pa = Ammo(i).GetParentAmmo();
			if (pa && pa == i.GetClass() && KindOfAmmo(i.GetClassName()) == ki) l.Push(i);
		}
	}
	// a kind is at its maximum when any of its BD22 reserves is full (each BD22 ammo type counts: owner round 2 Q14b,
	// round 4); the full one's name for the log, "" if none
	static string MaxedBy(Actor p, string kind)
	{
		Array<Inventory> l;
		KindAmmo(p, kind, l);
		for (int i = 0; i < l.Size(); i++) if (l[i].MaxAmount > 0 && l[i].Amount >= l[i].MaxAmount) return l[i].GetClassName();
		return "";
	}
	static bool Maxed(Actor p, string kind) { return MaxedBy(p, kind) != ""; }

	// ---------------------------------------------------------------- alt-fire stand-down (owner round 3, Q12)
	// BD22 VR's toggleable secondaries stand down while the hand's gun carries the legendary power that uses that input:
	// Seeker on the rocket launcher (lock-on alt), Burst on the pistol family (burst toggle), Chargeup on the plasma
	// rifle (charge alt), Slug on the pump shotgun (slug alt). Tokens RSLD_AltDown / RSLD_AltDownOff (read by alts.zs,
	// rlock.zs and the guns' AltFire states); PistolBurstFire is taken while the pistol's stands down.
	static bool PowerUsesAlt(int slot, string eff)
	{
		return (slot == 6 && eff ~== "Seeker") || (slot == 2 && eff ~== "Burst") || (slot == 7 && eff ~== "Chargeup") || (slot == 3 && eff ~== "Slug");
	}
	static void StandDown(RSLD_Handler h, PlayerPawn p)
	{
		int pn = p.PlayerNumber();
		for (int hand = 0; hand < 2; hand++)
		{
			let w = hand == RSLD.OFF ? p.player.OffhandWeapon : p.player.ReadyWeapon;
			int slot;
			let e = w ? h.FxFor(pn, hand, w, slot) : null;
			string en = e ? e.name : h.EffName(pn, slot);
			if (hand == RSLD.OFF)
			{	// rsld_offhand_legendary off: the off hand carries no power
				cvar c = cvar.FindCvar("rsld_offhand_legendary");
				if (c && !c.GetBool()) en = "";
			}
			bool down = w && slot >= 0 && PowerUsesAlt(slot, en);
			class<Inventory> tok = "RSLD_AltDown";
			if (hand == RSLD.OFF) tok = "RSLD_AltDownOff";
			bool had = p.CountInv(tok) > 0;
			if (down && !had) { p.GiveInventory(tok, 1); if (RSLD.Debug()) Console.Printf("RSLD %d %s: %s hand's BD22 VR secondary stands down (%s)", level.maptime, en, RSLD.HandName(hand), w.GetClassName()); }
			else if (!down && had) { p.TakeInventory(tok, 1); if (RSLD.Debug()) Console.Printf("RSLD %d alt stand-down off: %s hand", level.maptime, RSLD.HandName(hand)); }
			if (down && slot == 2)
			{
				let bt = RSLD.IC("PistolBurstFire");
				if (bt && p.CountInv(bt) > 0) { p.TakeInventory(bt, 999); if (RSLD.Debug()) Console.Printf("RSLD %d Burst: BD22's pistol burst toggle stood down", level.maptime); }
			}
		}
	}
}

// the stand-down tokens (never given without LegenDoom)
class RSLD_AltDown : Inventory { Default { +INVENTORY.UNDROPPABLE +INVENTORY.UNTOSSABLE +INVENTORY.UNCLEARABLE Inventory.MaxAmount 1; } }
class RSLD_AltDownOff : Inventory { Default { +INVENTORY.UNDROPPABLE +INVENTORY.UNTOSSABLE +INVENTORY.UNCLEARABLE Inventory.MaxAmount 1; } }

// per level: learned shot sizes, Recycling's counters
class RSLD_G6Reg : Thinker
{
	Array<Name> sizeCls;
	Array<int> sizeN;
	int recyc[MAXPLAYERS * 4];

	static RSLD_G6Reg Get()
	{
		let it = ThinkerIterator.Create("RSLD_G6Reg", Thinker.STAT_INFO);
		let g = RSLD_G6Reg(it.Next());
		if (!g) { g = new("RSLD_G6Reg"); g.ChangeStatNum(Thinker.STAT_INFO); }
		return g;
	}
}

// base: riders on missiles (blast and ray ratios), the pellets of a pull recorded (Unfathomable, Overflowing)
class RSLD_G6Fx : RSLD_G3Fx
{
	bool wantPellets;
	Array<int> pPull;
	Array<double> pA, pP;
	Array<int> pDmg;
	Array<class<Actor> > pPuff;

	override bool OnPellet(RSLD_Shot s, RSLD_Pellet p)
	{
		if (wantPellets && p.index >= 0)
		{
			pPull.Push(s.pull); pA.Push(Actor.DeltaAngle(p.aimAngle, p.angle)); pP.Push(p.pitch - p.aimPitch); pDmg.Push(p.damage); pPuff.Push(p.puff);
			if (pPull.Size() > 256) { pPull.Delete(0, 64); pA.Delete(0, 64); pP.Delete(0, 64); pDmg.Delete(0, 64); pPuff.Delete(0, 64); }
		}
		return false;
	}

	// n more pellets in this pull's own pattern (offsets taken at random from its recorded pellets), free
	int Volley(RSLD_Shot s, int n)
	{
		Array<int> idx;
		for (int i = 0; i < pPull.Size(); i++) if (pPull[i] == s.pull) idx.Push(i);
		if (!idx.Size() || n <= 0) return 0;
		for (int k = 0; k < n; k++)
		{
			int i = idx[random(0, idx.Size() - 1)];
			s.FirePellet(s.aimAngle + pA[i], s.aimPitch + pP[i], pDmg[i], pPuff[i]);
		}
		return n;
	}

	// every pull's ammo goes back (Nuclear, Unknown, the no-ammo shots)
	void GiveBack(RSLD_Shot s, string why)
	{
		int t = RSLD_G6.Taken(s);
		if (t <= 0) t = s.ammoTaken;
		if (t > 0) s.Refund(t);
		s.Log(String.Format("%s: %d round(s) given back", why, t));
	}
}

// Nuclear (R: Pi..BF): "Does less damage, has infinite ammo": 3 of 5 a bullet, rocket 12 of 20 with A_Explode(77,77),
// plasma 3 of 5, BFG 60 of 100 with 30 rays of 10 (of 40 of 15); never uses ammo. Ours: x0.6 (rays x0.5, the blast
// x0.6 damage and radius); every shot's rounds go back to the magazine.
class RSLD_Fx_Nuclear : RSLD_G6Fx
{
	override void RiderSpawn(RSLD_Rider r)
	{
		r.dmgMul = RSLD_G3Util.RandRatio("Nuclear", r.kind);
		if (r.kind == RSLD_G3.K_BFG) r.explDmgMul = r.dmgMul;
		else { r.explDmgMul = RSLD_G3.N("Nuclear", "rk_expl") / RSLD_G3.N("Base3", "rk_expl"); r.explRadMul = RSLD_G3.N("Nuclear", "rk_rad") / RSLD_G3.N("Base3", "rk_rad"); }
	}
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.kind == RSLD_G3.K_BFG && r.s)
			RSLD_G3.RayWindow(r.s.mo, RSLD_G3.N("Nuclear", "bfg_rays") * RSLD_G3.N("Nuclear", "bfg_raydmg") / (RSLD_G3.N("Base3", "bfg_rays") * RSLD_G3.N("Base3", "bfg_raydmg")));
	}
	override void RiderDamage(RSLD_Shot s, RSLD_Hit h, RSLD_Rider r)
	{
		if (!r && !RSLD_G3.IsRay(s, h) && !(h.inflictor is "RSLD_Boom") && !(h.flags & DMG_EXPLOSION)) h.mult *= RSLD_G3.N("Nuclear", "sg_dmg") / RSLD_G3.N("Base3", "sg_dmg");
	}
	override void AfterPull(RSLD_Shot s) { if (s.ammoTaken > 0) GiveBack(s, "Nuclear (infinite ammo)"); }
}

// Unknown (C: Pi..BF): "Has unlimited ammo while invisibility is active" (PowerInvisibility, PowerGhost, PowerShadow,
// PowerInfiniteAmmo skip the ammo check); effects/unknown -> Pickup/Invis (scope 4) on such a shot
class RSLD_Fx_Unknown : RSLD_G6Fx
{
	override bool Rides(int k) { return false; }
	static bool Invisible(Actor p)
	{
		return p.FindInventory("PowerInvisibility", true) || p.FindInventory("PowerGhost", true) || p.FindInventory("PowerShadow", true) || p.FindInventory("PowerInfiniteAmmo", true);
	}
	override void OnPull(RSLD_Shot s) { s.b1 = Invisible(s.mo); if (s.b1) s.Sound("Pickup/Invis", 0.5); }
	override void AfterPull(RSLD_Shot s) { if (s.b1 && s.ammoTaken > 0) GiveBack(s, "Unknown (invisible: free)"); }
}

// Illegal (R: Pi..BF): "Can attack without ammo, but makes enemies angry": with ammo the shot is normal; without, it is
// free and every enemy it hits gets LegenDoom's LDIllegalizer (its anger and visual: E). Ours: the last-round shot.
class RSLD_Fx_Illegal : RSLD_G6Fx
{
	override void OnPull(RSLD_Shot s) { s.b1 = RSLD_G6.LastRound(s); if (s.b1) s.Log("last round: an illegal shot (free, enemies hit get angry)"); }
	override void OnHit(RSLD_Shot s, RSLD_Hit h)
	{
		if (!s.b1 || !h.target || !h.target.bISMONSTER || (h.flags & DMG_EXPLOSION) || RSLD.Has(h.target, "LDIllegalActive") > 0) return;
		let c = RSLD.AC("LDIllegalizer");
		if (!c) return;
		let z = Actor.Spawn(c, h.target.pos, NO_REPLACE);
		if (z) { z.tracer = h.target; z.target = s.mo; s.Log(String.Format("%s is angry (LDIllegalizer)", h.target.GetClassName())); }
	}
	override void AfterPull(RSLD_Shot s) { RSLD_G6.LearnSize(s, RSLD_G6.Taken(s)); if (s.b1 && s.ammoTaken > 0) GiveBack(s, "Illegal (no ammo used)"); }
}

// Optional (U: Pi..BF): "Can fire weaker shots without ammo": 2 of 5 a bullet, rocket 8 of 20 with A_Explode(51,51),
// plasma 2 of 5, BFG 40 of 100 with 20 rays of 7. Ours: the last-round shot is free at x0.4 (blast x0.4 / x0.4, rays
// x(20 x 7) / (40 x 15)).
class RSLD_Fx_Optional : RSLD_G6Fx
{
	override void OnPull(RSLD_Shot s) { s.b1 = RSLD_G6.LastRound(s); if (s.b1) s.Log("last round: a weaker free shot"); }
	override void RiderSpawn(RSLD_Rider r)
	{
		if (!r.s.b1) return;
		r.dmgMul = RSLD_G3Util.RandRatio("Optional", r.kind);
		if (r.kind == RSLD_G3.K_BFG) r.explDmgMul = r.dmgMul;
		else { r.explDmgMul = RSLD_G3.N("Optional", "rk_expl") / RSLD_G3.N("Base3", "rk_expl"); r.explRadMul = RSLD_G3.N("Optional", "rk_rad") / RSLD_G3.N("Base3", "rk_rad"); }
	}
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.s && r.s.b1 && r.kind == RSLD_G3.K_BFG)
			RSLD_G3.RayWindow(r.s.mo, RSLD_G3.N("Optional", "bfg_rays") * RSLD_G3.N("Optional", "bfg_raydmg") / (RSLD_G3.N("Base3", "bfg_rays") * RSLD_G3.N("Base3", "bfg_raydmg")));
	}
	override void RiderDamage(RSLD_Shot s, RSLD_Hit h, RSLD_Rider r)
	{
		if (s.b1 && !r && !RSLD_G3.IsRay(s, h) && !(h.inflictor is "RSLD_Boom") && !(h.flags & DMG_EXPLOSION)) h.mult *= RSLD_G3.N("Optional", "sg_dmg") / RSLD_G3.N("Base3", "sg_dmg");
	}
	override void AfterPull(RSLD_Shot s) { RSLD_G6.LearnSize(s, RSLD_G6.Taken(s)); if (s.b1 && s.ammoTaken > 0) GiveBack(s, "Optional (weak shot, no ammo used)"); }
}

// Transmogrifier (U: Pi..BF): "Uses other ammo types when it runs out of main ammo type": out of its own, the shot takes
// the next of LegenDoom's kinds that has enough, at LegenDoom's cost for that gun (numbers_g3.zs Transmogrifier.<gun>_<kind>,
// the order of <Gun>.dec FireTransmogrifierAmmoCheck: g3.rules "# order"). Ours: the last-round shot takes that instead
// (the round goes back to the magazine); nothing left of any kind: the shot is an ordinary one and the gun empties.
class RSLD_Fx_Transmogrifier : RSLD_G6Fx
{
	override bool Rides(int k) { return false; }
	static string Order(int slot)
	{
		switch (slot)
		{
			case 2: return "Clip|Shell|Cell|RocketAmmo";
			case 3: case 4: return "Shell|Clip|Cell|RocketAmmo";
			case 5: return "Clip|Shell|Cell|RocketAmmo";
			case 6: return "RocketAmmo|Clip|Shell|Cell";
			case 7: case 8: return "Cell|Clip|Shell|RocketAmmo";
		}
		return "";
	}
	override void OnPull(RSLD_Shot s) { s.b1 = RSLD_G6.LastRound(s); }
	override void AfterPull(RSLD_Shot s)
	{
		RSLD_G6.LearnSize(s, RSLD_G6.Taken(s));
		if (!s.b1 || s.ammoTaken <= 0) return;
		string gk = RSLD_G6.GunKey(s.slot), ord = Order(s.slot);
		if (gk == "" || ord == "") return;
		Array<string> l;
		ord.Split(l, "|");
		for (int i = 1; i < l.Size(); i++)	// [0] is its own kind (the normal path)
		{
			int cost = int(RSLD_G3.NOr("Transmogrifier", gk .. "_" .. l[i], 0));
			if (cost <= 0) continue;
			Array<Inventory> pools;
			RSLD_G6.KindAmmo(s.mo, l[i], pools);	// round 4: every BD22 ammo of that kind (the kind's own first)
			for (int j = 0; j < pools.Size(); j++)
			{
				let inv = pools[j];
				if (inv.Amount < cost) continue;
				inv.Amount -= cost;
				GiveBack(s, String.Format("Transmogrifier: out of its own ammo, took %d %s (LegenDoom's %s kind) instead", cost, inv.GetClassName(), l[i]));
				return;
			}
		}
		s.Log("Transmogrifier: no other ammo kind has enough: the gun empties");
	}
}

// Unfathomable (E: Pi..BF): "Fires all your ammo in one shot": LegenDoom loops the shot (FBF_USEAMMO) while ammo lasts.
// Ours: the pull fires the rest of the magazine at once: as many more volleys as rounds are left over what one shot
// takes, each volley the pull's own pellets (offsets taken from its pattern) or its projectiles; the magazine is empty.
class RSLD_Fx_Unfathomable : RSLD_G6Fx
{
	override void Init() { wantPellets = true; }
	override bool Rides(int k) { return k != RSLD_G3.K_NONE; }
	// at the pull's end (all its pellets seen: BD22 VR's pump fires its volley over two tics); the rounds it took are
	// known from AfterPull
	override void AfterPull(RSLD_Shot s) { s.i2 = RSLD_G6.Taken(s); }
	override void OnPullEnd(RSLD_Shot s)
	{
		int per = s.i2;
		let pool = RSLD_G6.Pool(s.weapon);
		if (per <= 0 || !pool || pool.Amount < per) return;
		int volleys = pool.Amount / per;
		pool.Amount -= volleys * per;
		int n = 0;
		if (s.pellets > 0) n = Volley(s, volleys * s.pellets);
		else
		{
			let g = RSLD_G3.Reg();
			for (int i = g.riders.Size() - 1; i >= 0 && n < volleys * max(1, s.missiles); i--)
			{
				let r = g.riders[i];
				if (!r || r.s != s || r.child || !r.m) continue;
				double a, p;
				[a, p] = RSLD_G3.Dir(r.m);
				for (int v = 0; v < volleys; v++) { RSLD_G3.Child(r, r.m.pos - r.m.vel * (v % 3) * 0.3, a + frandom(-1, 1), p + frandom(-1, 1), r.m.vel.Length(), 1, 1); n++; }
			}
		}
		s.Log(String.Format("Unfathomable: %d more volleys (%d rounds) in the same shot: %d %s", volleys, volleys * per, n, s.pellets > 0 ? "pellets" : "projectiles"));
	}
}

// Recycling (U: Pi..BF): "Gives small amounts of all other ammo types when fired": per shot LegenDoom gives some ammo at
// once and counters toward each kind (100 = one round: LDRecyclingAmmoGeneration -> LD_<Kind>Single), per gun
// (numbers_g3.zs Recycling.<gun>_<Kind> / _<Kind>C). Ours: the same, into BD22's reserves.
class RSLD_Fx_Recycling : RSLD_G6Fx
{
	override bool Rides(int k) { return false; }
	override void AfterPull(RSLD_Shot s)
	{
		if (s.ammoTaken <= 0) return;
		string gk = RSLD_G6.GunKey(s.slot);
		if (gk == "") return;
		let g = RSLD_G6Reg.Get();
		int max = int(RSLD_G3.N("Recycling", "max"));
		string got = "";
		for (int k = 0; k < 4; k++)
		{
			string kind = k == 0 ? "Clip" : (k == 1 ? "Shell" : (k == 2 ? "Rocket" : "Cell"));
			let c = RSLD.IC(RSLD_G6.KindCls(kind));
			if (!c) continue;
			int give = int(RSLD_G3.NOr("Recycling", gk .. "_" .. kind, 0));
			int ctr = int(RSLD_G3.NOr("Recycling", gk .. "_" .. kind .. "C", 0));
			int ix = s.pn * 4 + k;
			g.recyc[ix] = min(max, g.recyc[ix] + ctr);
			if (g.recyc[ix] >= max) { give++; g.recyc[ix] = 0; }
			if (give > 0) { s.mo.GiveInventory(c, give); got = got .. String.Format(" +%d %s", give, c.GetClassName()); }
		}
		if (got != "" || RSLD.DebugLevel() > 1) s.Log(String.Format("Recycling:%s (counters %d %d %d %d)", got, g.recyc[s.pn * 4], g.recyc[s.pn * 4 + 1], g.recyc[s.pn * 4 + 2], g.recyc[s.pn * 4 + 3]));
	}
}

// Overflowing (E: all nine): a bonus for each of LegenDoom's ammo kinds at its maximum: Rocket -> a small blast where
// each shot lands (bullet puff A_Explode(5,15, no self), rocket +A_Explode(20,160), plasma (5,40), BFG (100,800)),
// Cell -> x1.5 (bullets (5 x random(1,3)) x 1.5, rocket 30 of 20, plasma 8 of 5, BFG 150 of 100), Shell -> a free
// extra volley (shotgun 4 of 7 pellets, SSG 10 of 20, one more bullet / projectile on the others), Clip -> a faster
// cycle (fire-state cadence: G5, not here). Ours: those ratios on our numbers, BD22's reserves (Clip2, AmmoShell,
// AmmoRocket, AmmoCell) counted. Fists / chainsaw: the Cell x1.5 only (their extra punch and faster swing are G7's).
class RSLD_Fx_Overflowing : RSLD_G6Fx
{
	override void Init() { wantPellets = true; }
	override void OnPull(RSLD_Shot s)
	{
		string mr = RSLD_G6.MaxedBy(s.mo, "RocketAmmo"), mc = RSLD_G6.MaxedBy(s.mo, "Cell"), ms = RSLD_G6.MaxedBy(s.mo, "Shell"), ml = RSLD_G6.MaxedBy(s.mo, "Clip");
		s.i1 = (mr != "" ? 1 : 0) | (mc != "" ? 2 : 0) | (ms != "" ? 4 : 0) | (ml != "" ? 8 : 0);
		if (s.i1) s.Log(String.Format("maxed:%s%s%s%s", mr != "" ? " rockets by " .. mr .. " (small blasts)" : "", mc != "" ? " cells by " .. mc .. " (x1.5)" : "",
			ms != "" ? " shells by " .. ms .. " (free extra volley)" : "", ml != "" ? " clips by " .. ml .. " (faster cycle: left out, owner round 4)" : ""));
	}
	static double CellMul(int kind)
	{
		if (kind == RSLD_G3.K_NONE) return RSLD_G3.N("Overflowing", "bul_cell");
		return RSLD_G3.N("Overflowing", RSLD_G3.KindKey(kind) .. "_cell") / RSLD_G3.LDBase(kind);
	}
	override void RiderSpawn(RSLD_Rider r) { if (r.s.i1 & 2) r.dmgMul *= CellMul(r.kind); }
	override void RiderStart(RSLD_Rider r)
	{
		if (r.child || !(r.s.i1 & 4) || !r.m) return;
		double a, p;
		[a, p] = RSLD_G3.Dir(r.m);
		RSLD_G3.Child(r, r.m.pos - r.m.vel * 0.5, a, p, r.m.vel.Length(), r.dmgMul, 1);
		RSLD_G3.Log(r, "shells maxed: one more, free");
	}
	override void RiderDeath(RSLD_Rider r)
	{
		if (r.sky || !(r.s.i1 & 1)) return;
		string kk = RSLD_G3.KindKey(r.kind);
		int d = int(r.ourDirect * RSLD_G3.N("Overflowing", kk .. "_aoe") / (RSLD_G3.LDBase(r.kind) * RSLD_G3.RndMean()) + 0.5);
		double rad = RSLD_G3.N("Overflowing", kk .. "_aoerad");
		RSLD_G3.BoomAt(r.s, r.last, d, rad, 0, 0, 0);
		RSLD_G3.Log(r, String.Format("rockets maxed: +blast %d over %.0f", d, rad));
	}
	override void RiderDamage(RSLD_Shot s, RSLD_Hit h, RSLD_Rider r)
	{
		if (!r && (s.i1 & 2) && !(h.inflictor is "RSLD_Boom") && !(h.flags & DMG_EXPLOSION)) h.mult *= CellMul(RSLD_G3.K_NONE);
	}
	override void OnPelletEnd(RSLD_Shot s, RSLD_Pellet p, int res, Vector3 at, Actor thing)
	{
		if (!(s.i1 & 1) || res == RSLD.RES_NONE) return;
		double mean = RSLD_G3.N("Base3", "sg_dmg") * (1 + RSLD.Num("Base", "rnd_max")) / 2.0;	// 5 x random(1,3): 10
		int d = max(1, int(p.damage * RSLD_G3.N("Overflowing", "bul_aoe") / max(1.0, mean) + 0.5));
		RSLD_G3.BoomAt(s, at, d, RSLD_G3.N("Overflowing", "bul_aoerad"), 0, 0, 0);
	}
	override void OnPullEnd(RSLD_Shot s)
	{
		if (!(s.i1 & 4) || s.pellets <= 0 || s.melee) return;
		double f = 1;
		if (s.slot == 3) f = RSLD_G3.N("Overflowing", "sg_extra") / RSLD_G3.N("Overflowing", "sg_n");
		else if (s.slot == 4) f = RSLD_G3.N("Overflowing", "ss_extra") / RSLD_G3.N("Overflowing", "ss_n");
		int n = Volley(s, max(1, int(s.pellets * f + 0.5)));
		s.Log(String.Format("shells maxed: %d free extra pellets", n));
	}
}
