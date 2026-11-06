// LD mode handler (LegenDoom 3.0 x BD22 VR). Moved in from ldl_patch (LD_BD22VR_Patch) on 2026-11-06 and rebuilt:
//  1. Replacements: LegenDoom replaces 56 classes; CheckReplacement hands each back to the class it had before
//     LegenDoom (tables.zs, measured on the rig), not final, so a skill's ReplaceActor still applies.
//  2. LegenDoom's own weapons that reach a player leave (their tokens stay); unlock tokens for BD22 guns owned.
//  3. THE EFFECT REGISTRY: one RSLD_Effect per RSLD_Fx_<Name> class (core.zs), found with AllClasses.
//  4. THE SHOT CONTEXT: a trigger pull = every shot event of one hand in one tic, seen from WorldHitscanPreFired
//     (pellets), WorldThingSpawned (missiles, melee strikes); never from ammo diffs. Damage is matched to its pull by
//     the inflictor (missiles, rounds, strikes are tagged) or by the tic.
//  5. Drops (pickup.zs), death spots, Bossfight-only drops, the drop-legendary menu action, the rig probe, HUD name.
// Everything returns at once when LegenDoom is not loaded (ldOn false): BD22 VR alone is unchanged.

class RSLD_Handler : EventHandler
{
	bool ldOn;

	// ---- registry
	Array<RSLD_Effect> fx;
	Map<String, double> numVal;
	Map<String, String> numSrcs;
	Array<String> numMissing;

	// ---- families
	Array<class<Weapon> > famCls;
	Array<int> famSlot;

	// ---- per player x slot cache (refreshed every 17 tics and on pickup / drop / probe)
	string slotEff[MAXPLAYERS * 9];
	int slotRar[MAXPLAYERS * 9];
	RSLD_Effect slotFx[MAXPLAYERS * 9];
	int slotCacheTic[MAXPLAYERS];
	RSLD_Effect probeFx[MAXPLAYERS * 9];	// rig probe only: an effect LegenDoom has no token for on that slot

	// ---- shots (index pn * 2 + hand)
	RSLD_Shot cur[MAXPLAYERS * 2];
	RSLD_Shot none[MAXPLAYERS];
	int lastPullTic[MAXPLAYERS * 2];
	int heldSince[MAXPLAYERS * 2];
	Weapon heldW[MAXPLAYERS * 2];
	int snapMag[MAXPLAYERS * 2], snapRes[MAXPLAYERS * 2];
	Weapon snapW[MAXPLAYERS * 2];
	int prevMag[MAXPLAYERS * 2], prevRes[MAXPLAYERS * 2];	// the snapshot one tic earlier (round 2: the rocket
	Weapon prevW[MAXPLAYERS * 2];							// launcher takes its round a tic before the rocket: rig r2_rlamm)
	int pulls;
	Array<RSLD_Shot> pend;
	Array<Actor> tagA;
	Array<RSLD_Shot> tagS;
	Array<RSLD_PelletRec> tagR;
	Array<RSLD_Shot> open;		// pulls whose OnPullEnd has not run
	RSLD_PelletRec pendRec[MAXPLAYERS];	// the pellet whose trace is running now (hitscan mode)
	Array<RSLD_PelletRec> roundQ;		// True Bullets: pellets waiting for their round (spawned in pellet order)
	RSLD_Shot deliv;
	RSLD_PelletRec delivRec;
	int delivTic;
	bool refiring;
	RSLD_Pellet pel, pelX;		// pelX: FirePellet / FireRail's own (NEEDS_C 3: never the pellet OnPellet holds)
	RSLD_PelletRec railRec;
	bool railPuff;
	Vector3 railAt;
	RSLD_Hit hit;
	RSLD_Held held;
	bool inDamage;
	Array<Actor> probeTargets;	// rig probe: monsters spawned by rsld_target

	// ---- replacements, drops
	bool inRepl;
	Array<string> rcFrom;
	Array<class<Actor> > rcTo;
	Array<double> deathX, deathY, deathZ;
	Array<int> deathT, deathBF;
	vector3 spot;

	// ---- monster groups (class -> bit mask, computed once per class)
	Array<class<Actor> > grpCls;
	Array<int> grpMask;
	static const string GroupNames[] = { "Exorcist", "Extinguishing", "Wrangler", "Antiair", "Scrapper", "Blessed", "Heroic", "DemonSlayer" };

	// ================================================================ registry
	override void OnRegister()
	{
		SetOrder(-1000);	// sees every shot event BEFORE RSQ_Muzzle / Recoil / Flash / PlayerRounds (they may cancel it)
		ldOn = RSLD.On();
		if (!ldOn) return;
		for (int i = 0; i < RSLD_Data.Family.Size(); i++)
		{
			Array<string> p; RSLD_Data.Family[i].Split(p, "|");
			class<Weapon> c = p[1];
			if (c) { famCls.Push(c); famSlot.Push(p[0].ToInt()); }
		}
		for (int i = 0; i < AllClasses.Size(); i++)
		{
			class<RSLD_NumberTable> nt = (class<RSLD_NumberTable>)(AllClasses[i]);
			if (nt && nt != "RSLD_NumberTable")
			{
				let t = RSLD_NumberTable(new(nt));
				for (int r = 0; r < t.Count(); r++)
				{
					Array<string> f; t.Row(r).Split(f, "|");
					if (f.Size() < 4) continue;
					string k = f[0] .. "." .. f[1];
					numVal.Insert(k, f[2].ToDouble());
					numSrcs.Insert(k, f[3]);
				}
			}
			class<RSLD_Effect> ec = (class<RSLD_Effect>)(AllClasses[i]);
			if (!ec || ec == "RSLD_Effect") continue;
			string cn = ec.GetClassName();
			if (cn.Left(8) != "RSLD_Fx_") continue;
			string en = cn.Mid(8);
			bool known = false;
			for (int s = 0; s < 9 && !known; s++) { class<Inventory> tk = "LD" .. RSLD_Data.Slots[s] .. "Effect_" .. en; if (tk) known = true; }
			if (!known) { Console.Printf("RSLD: %s is not a LegenDoom effect name (no LD<Slot>Effect_%s token): ignored", cn, en); continue; }
			bool dup = false;
			for (int k = 0; k < fx.Size(); k++) if (fx[k].name ~== en) dup = true;
			if (dup) { Console.Printf("RSLD: two classes for effect %s: %s ignored", en, cn); continue; }
			let e = RSLD_Effect(new(ec));
			e.name = en; e.h = self;
			e.Init();
			fx.Push(e);
		}
		pel = new("RSLD_Pellet");
		pelX = new("RSLD_Pellet");
		hit = new("RSLD_Hit");
		held = new("RSLD_Held");
		for (int i = 0; i < MAXPLAYERS; i++) slotCacheTic[i] = -1000;
		if (RSLD.Debug()) Console.Printf("RSLD: LD mode on: %d effects registered, %d numbers", fx.Size(), numVal.CountUsed());
	}

	// owner 2026-11-06 round 2: LegenDoom's own visuals come with its effects, but NO quakes or anything that moves the VR
	// camera. Every LegenDoom A_Quake is behind its own option LD_quakes (decorate/*.dec: each QuakeTime state starts
	// A_JumpIf(CallACS("LD_quakes") == 0, ...); source/LEGENDVAR.acs:94 reads CVARINFO's server bool LD_quakes): the LD
	// mode turns it off on every map.
	override void WorldLoaded(WorldEvent e)
	{
		if (!ldOn) return;
		cvar q = cvar.FindCvar("LD_quakes");
		if (q && q.GetBool())
		{
			q.SetBool(false);
			Console.Printf("RSLD: LegenDoom's LD_quakes turned off (no camera quakes in VR)");
		}
	}

	RSLD_Effect FindFx(string n)
	{
		if (n == "") return null;
		for (int i = 0; i < fx.Size(); i++) if (fx[i].name ~== n) return fx[i];
		return null;
	}

	double Num(string eff, string key)
	{
		string k = eff .. "." .. key;
		if (numVal.CheckKey(k)) return numVal.Get(k);
		if (numMissing.Find(k) == numMissing.Size()) { numMissing.Push(k); Console.Printf("RSLD missing number %s", k); }
		return 0;
	}

	string NumSrc(string eff, string key)
	{
		string k = eff .. "." .. key;
		return numSrcs.CheckKey(k) ? numSrcs.Get(k) : "";
	}

	// ================================================================ families and slots
	int SlotOf(Weapon w)
	{
		if (!w) return -1;
		class<Actor> c = w.GetClass();
		string cn = c.GetClassName();
		if (cn.Left(8) == "RSQ_Off_") c = (class<Actor>)(c.GetParentClass());	// an off-hand copy is a subclass of its gun (DECORATE.rsqdual)
		for (int i = 0; i < famCls.Size(); i++) if (famCls[i] == c) return famSlot[i];
		return -1;
	}

	void RefreshSlots(int pn, Actor mo)
	{
		slotCacheTic[pn] = level.maptime;
		for (int s = 0; s < 9; s++) { slotEff[pn * 9 + s] = ""; slotRar[pn * 9 + s] = -1; slotFx[pn * 9 + s] = null; }
		for (let i = mo.Inv; i; i = i.Inv)
		{
			string c = i.GetClassName();
			if (c.Left(2) != "LD") continue;
			for (int s = 0; s < 9; s++)
			{
				string sl = RSLD_Data.Slots[s];
				string pe = "LD" .. sl .. "Effect_";
				if (c.Left(pe.Length()) ~== pe) { slotEff[pn * 9 + s] = c.Mid(pe.Length()); slotFx[pn * 9 + s] = FindFx(c.Mid(pe.Length())); break; }
				string pr = "LD" .. sl .. "Legendary";
				if (c.Left(pr.Length()) ~== pr)
				{
					string r = c.Mid(pr.Length());
					for (int k = 0; k < 4; k++) if (r ~== RSLD_Data.Rarities[k]) slotRar[pn * 9 + s] = k;
					break;
				}
			}
		}
		ApplyProbe(pn);
	}

	void ApplyProbe(int pn)
	{
		for (int s = 0; s < 9; s++) if (probeFx[pn * 9 + s]) { slotFx[pn * 9 + s] = probeFx[pn * 9 + s]; slotEff[pn * 9 + s] = probeFx[pn * 9 + s].name; }
	}

	string EffName(int pn, int s) { return (s >= 0 && s < 9) ? slotEff[pn * 9 + s] : ""; }

	// the effect a hand's gun carries (Q8: rsld_offhand_legendary)
	RSLD_Effect FxFor(int pn, int hand, Weapon w, out int slot)
	{
		slot = SlotOf(w);
		if (slot < 0) return null;
		if (hand == RSLD.OFF)
		{
			cvar c = cvar.FindCvar("rsld_offhand_legendary");
			if (c && !c.GetBool()) return null;
		}
		return slotFx[pn * 9 + slot];
	}

	static bool OwnsFamily(Actor a, int s)
	{
		for (int i = 0; i < RSLD_Data.Family.Size(); i++)
		{
			Array<string> p; RSLD_Data.Family[i].Split(p, "|");
			if (p[0].ToInt() != s) continue;
			class<Inventory> c = p[1];
			if (c && a.CountInv(c) > 0) return true;
		}
		return false;
	}

	static bool OwnsGun(Actor a, int s, class<Weapon> give)
	{
		if (!give || a.CountInv(give) > 0) return true;
		if (give.GetClassName() == "BrutalRevolver") return false;
		Array<string> l; RSLD_Data.Same[s].Split(l, "|");
		for (int i = 0; i < l.Size(); i++) { class<Inventory> c = l[i]; if (c && a.CountInv(c) > 0) return true; }
		return false;
	}

	static class<Weapon> GiveClassFor(int s, Actor who)
	{
		if (s == 2)	// BD22 VR "Silvergun Replaces Pistol"
		{
			cvar ml = cvar.FindCvar("rsq_moonlight_pistol");
			class<Weapon> m = (class<Weapon>)(RSLD.AC("BrutalRevolver"));
			if (ml && ml.GetBool() && m) return m;
		}
		class<Weapon> c = RSLD_Data.Give[s];
		return c;
	}

	// ================================================================ 1. replacements
	class<Actor> ResolveRepl(string replacee, string ldcls, out bool found)
	{
		found = false;
		for (int i = 0; i < rcFrom.Size(); i++) if (rcFrom[i] ~== replacee) { found = true; return rcTo[i]; }
		for (int i = 0; i < RSLD_Tables.Repl.Size(); i++)
		{
			Array<string> f; RSLD_Tables.Repl[i].Split(f, "|");
			if (!(f[0] ~== replacee) || !(f[1] ~== ldcls)) continue;
			class<Actor> to = FindClassLoose(f[2]);
			if (!to) to = FindClassLoose(f[3]);
			if (to && to.GetClassName() == replacee) to = null;
			found = true;
			rcFrom.Push(replacee); rcTo.Push(to);
			if (RSLD.Debug()) { string tn = replacee; if (to) tn = to.GetClassName(); Console.Printf("RSLD replace: %s was %s under LegenDoom, back to %s", replacee, ldcls, tn); }
			return to;
		}
		return null;
	}

	static class<Actor> FindClassLoose(string n)
	{
		class<Actor> c = n;
		if (c) return c;
		int at = n.IndexOf("@");
		if (at < 0) return null;
		string base = n.Left(at + 1);
		class<Actor> last;
		for (int i = 0; i < AllActorClasses.Size(); i++)
		{
			string cn = AllActorClasses[i].GetClassName();
			if (cn.Left(base.Length()) ~== base) last = AllActorClasses[i];
		}
		return last;
	}

	override void CheckReplacement(ReplaceEvent e)
	{
		if (!ldOn || !e.Replacement || inRepl) return;
		string rn = e.Replacement.GetClassName();
		if (rn.Left(2) != "LD") return;
		inRepl = true;
		bool found;
		class<Actor> to = ResolveRepl(e.Replacee.GetClassName(), rn, found);
		inRepl = false;
		if (found) e.Replacement = to;
	}

	// ================================================================ 4. shots
	RSLD_Shot NewPull(PlayerPawn mo, int hand, Weapon w, bool melee)
	{
		int pn = mo.PlayerNumber();
		int k = pn * 2 + hand;
		bool firedLastTic = lastPullTic[k] == level.maptime - 1;
		lastPullTic[k] = level.maptime;
		int slot;
		let e = FxFor(pn, hand, w, slot);
		if (!e) { cur[k] = null; return null; }
		let s = new("RSLD_Shot");
		s.mo = mo; s.pn = pn; s.hand = hand; s.weapon = w; s.slot = slot; s.rarity = slotRar[pn * 9 + slot];
		s.fx = e; s.effName = e.name; s.tic = level.maptime; s.lastTic = s.tic; s.pull = ++pulls; s.melee = melee;
		open.Push(s);
		if (!firedLastTic && prevW[k] == w && snapW[k] == w) { s.preMag = max(prevMag[k], snapMag[k]); s.preRes = max(prevRes[k], snapRes[k]); }
		else if (snapW[k] == w) { s.preMag = snapMag[k]; s.preRes = snapRes[k]; }
		else { s.preMag = MagOf(w); s.preRes = ResOf(w); }
		cur[k] = s;
		pend.Push(s);
		if (RSLD.DebugLevel() > 1) s.Log("pull");
		e.OnPull(s);
		return s;
	}

	// Agent C (NEEDS_C 1): BD22 VR's pump fires its volleys over two tics (Shotgun.dec:479 A 1, :480 B 1, :482 the
	// Tactical third volley at A 0 of T+1), the Revolver too (Revolver.dec:268-271): a shot at T+1 continues the pull
	static bool TwoTicVolley(Weapon w)
	{
		if (!w) return false;
		class<Actor> sg = RSLD.AC("Shot_Gun"), rv = RSLD.AC("Revolver");
		return (sg && w is sg) || (rv && w is rv);
	}

	RSLD_Shot PullOf(PlayerPawn mo, int hand, Weapon w, bool melee)
	{
		int k = mo.PlayerNumber() * 2 + hand;
		let c = cur[k];
		if (lastPullTic[k] == level.maptime && (c == null || c.weapon == w)) return c;
		if (c && c.weapon == w && c.tic == level.maptime - 1 && c.lastTic == c.tic && TwoTicVolley(w))
		{
			c.lastTic = level.maptime;
			lastPullTic[k] = level.maptime;
			return c;
		}
		return NewPull(mo, hand, w, melee);
	}

	static int MagOf(Weapon w) { return (w && w.Ammo2 && w.Ammo2 != w.Ammo1) ? w.Ammo2.Amount : 0; }
	static int ResOf(Weapon w) { return (w && w.Ammo1) ? w.Ammo1.Amount : 0; }

	void Tag(Actor a, RSLD_Shot s, RSLD_PelletRec r = null)
	{
		if (!a || !s) return;
		tagA.Push(a); tagS.Push(s); tagR.Push(r);
		if (r) r.carried = true;
		if (tagA.Size() > 512) { tagA.Delete(0, 128); tagS.Delete(0, 128); tagR.Delete(0, 128); }
	}

	RSLD_PelletRec TagRec(Actor a)
	{
		if (!a) return null;
		for (int i = tagA.Size() - 1; i >= 0; i--) if (tagA[i] == a) return tagR[i];
		return null;
	}

	RSLD_PelletRec NewRec(RSLD_Shot s, RSLD_Pellet from)
	{
		let r = new("RSLD_PelletRec");
		r.s = s;
		let q = new("RSLD_Pellet");
		q.angle = from.angle; q.pitch = from.pitch; q.aimAngle = from.aimAngle; q.aimPitch = from.aimPitch; q.spreadMul = from.spreadMul;
		q.range = from.range; q.damage = from.damage; q.flags = from.flags; q.puff = from.puff; q.damageType = from.damageType;
		q.index = from.index; q.rail = from.rail;
		r.p = q;
		s.recsOpen++; s.recsTotal++;
		// the previous pellet of this player that never raised WorldHitscanFired and is not riding a round: nothing hit
		let old = pendRec[s.pn];
		if (old && !old.ended && !old.carried)
		{
			if (RoundEligible(old)) { old.carried = true; roundQ.Push(old); }
			else EndRec(old, RSLD.RES_NONE, (0, 0, 0));
		}
		pendRec[s.pn] = r;
		return r;
	}

	// playerrounds.zs turns a pellet into a round when True Bullets is on and its range is MISSILERANGE or more
	static bool RoundEligible(RSLD_PelletRec r)
	{
		if (r.p.rail || (r.p.flags & LAF_ISMELEEATTACK) || r.p.range < MISSILERANGE || !r.p.puff) return false;
		cvar c = cvar.FindCvar("sv_rsq_true_bullets");
		return c && c.GetBool();
	}

	// the pellet a new round carries: the oldest one waiting, else the one being fired now
	RSLD_PelletRec RoundRec(int pn)
	{
		for (int i = 0; i < roundQ.Size(); i++)
			if (roundQ[i].s.pn == pn) { let r = roundQ[i]; roundQ.Delete(i); return r; }
		let r = pendRec[pn];
		if (r && !r.ended && !r.carried && RoundEligible(r)) { r.carried = true; return r; }
		return null;
	}

	void EndRec(RSLD_PelletRec r, int res, Vector3 at)
	{
		if (!r || r.ended) return;
		r.ended = true;
		let s = r.s;
		s.recsOpen--;
		if (res == RSLD.RES_WALL && r.thing) res = r.monster ? RSLD.RES_MONSTER : RSLD.RES_THING;
		if (RSLD.DebugLevel() > 1) s.Log(String.Format("pellet %d end: %s at (%.0f %.0f %.0f)", r.p.index, res == 1 ? "monster" : res == 2 ? "thing" : res == 3 ? "wall" : "none", at.x, at.y, at.z));
		if (s.fx) s.fx.OnPelletEnd(s, r.p, res, at, r.thing);
	}

	RSLD_Shot TagOf(Actor a)
	{
		if (!a) return null;
		for (int i = tagA.Size() - 1; i >= 0; i--) if (tagA[i] == a) return tagS[i];
		return null;
	}

	override bool WorldHitscanPreFired(WorldEvent e)
	{
		if (!ldOn || refiring) return false;
		let th = e.Thing;
		if (!th) return false;
		let mo = PlayerPawn(th);
		if (!mo || !mo.player)
		{	// a True Bullets round delivering its hitscan (playerrounds.zs Arrive): its damage belongs to its pull
			let ts = TagOf(th);
			if (ts) { deliv = ts; delivRec = TagRec(th); delivTic = level.maptime; }
			return false;
		}
		int hand = (e.AttackLineFlags & LAF_ISOFFHAND) ? RSLD.OFF : RSLD.MAIN;
		let w = hand == RSLD.OFF ? mo.player.OffhandWeapon : mo.player.ReadyWeapon;
		bool mel = (e.AttackLineFlags & LAF_ISMELEEATTACK) != 0;
		let s = PullOf(mo, hand, w, mel);
		if (!s) return false;
		if (e.AttackLineFlags & LAF_ABSPOSITION) return false;	// muzzle.zs / playerrounds re-fire of a pellet already seen
		if (!s.aimSet)
		{
			s.aimSet = true; s.aimAngle = mo.angle;
			s.aimPitch = mo.BulletSlope(null, hand == RSLD.OFF ? ALF_ISOFFHAND : 0);	// A_FireBullets' own bslope
		}
		pel.angle = e.AttackAngle; pel.pitch = e.AttackPitch; pel.aimAngle = s.aimAngle; pel.aimPitch = s.aimPitch;
		pel.spreadMul = 1; pel.range = e.AttackDistance; pel.damage = e.Damage; pel.flags = e.AttackLineFlags;
		pel.puff = e.AttackPuffType; pel.damageType = e.DamageType; pel.index = s.pellets; pel.rail = false;
		s.pellets++;
		bool drop = s.fx.OnPellet(s, pel);
		if (drop) { s.Log(String.Format("pellet %d dropped", pel.index)); return true; }
		double na = pel.angle, np = pel.pitch;
		if (pel.spreadMul != 1)
		{
			na = pel.aimAngle + Actor.DeltaAngle(pel.aimAngle, pel.angle) * pel.spreadMul;
			np = pel.aimPitch + (pel.pitch - pel.aimPitch) * pel.spreadMul;
		}
		pel.angle = na; pel.pitch = np;
		let r = NewRec(s, pel);
		if (na == e.AttackAngle && np == e.AttackPitch && pel.damage == e.Damage && pel.puff == e.AttackPuffType && pel.range == e.AttackDistance)
			return false;
		if (RSLD.DebugLevel() > 1 || (RSLD.Debug() && pel.index == 0)) s.Log(String.Format("pellet %d reshaped: angle %.2f -> %.2f pitch %.2f -> %.2f dmg %d -> %d range %.0f", pel.index, e.AttackAngle, na, e.AttackPitch, np, e.Damage, pel.damage, pel.range));
		refiring = true;
		mo.LineAttack(na, pel.range, np, pel.damage, pel.damageType, pel.puff, e.AttackLineFlags, null, e.AttackZ, e.AttackOffsetForward, e.AttackOffsetSide);
		refiring = false;
		s.d2 = Actor.DeltaAngle(s.aimAngle, na);
		return true;
	}

	// the trace that ran (hitscan mode: inside the pellet's own call chain; True Bullets: the round's delivery)
	override void WorldHitscanFired(WorldEvent e)
	{
		if (!ldOn) return;
		let th = e.Thing;
		if (!th) return;
		RSLD_PelletRec r;
		let mo = PlayerPawn(th);
		if (mo && mo.player) { r = pendRec[mo.PlayerNumber()]; if (r && r.carried) r = null; }
		else r = TagRec(th);
		if (!r || r.ended) return;
		EndRec(r, e.Inflictor || r.thing ? RSLD.RES_WALL : RSLD.RES_NONE, e.DamagePosition);
	}

	override void WorldThingDestroyed(WorldEvent e)
	{
		if (!ldOn || !e.Thing || !(e.Thing is "RSQ_PlayerRound")) return;
		let r = TagRec(e.Thing);
		if (r && !r.ended) EndRec(r, RSLD.RES_NONE, e.Thing.pos);	// a round that used up its range / life
	}

	// an extra pellet (RSLD_Shot.FirePellet): it goes through muzzle / rounds / recoil as an ordinary shot event, but
	// not through this handler's pull logic again
	void Refire(RSLD_Shot s, double angle, double pitch, int damage, class<Actor> puff, int flags, double range)
	{
		if (!s || !s.mo) return;
		int f = flags | (s.hand == RSLD.OFF ? LAF_ISOFFHAND : 0);
		pelX.angle = angle; pelX.pitch = pitch; pelX.aimAngle = s.aimAngle; pelX.aimPitch = s.aimPitch; pelX.spreadMul = 1;
		pelX.range = range; pelX.damage = damage; pelX.flags = f; pelX.puff = puff; pelX.damageType = 'Hitscan'; pelX.index = -1; pelX.rail = false;
		NewRec(s, pelX);
		refiring = true;
		s.mo.LineAttack(angle, range, pitch, damage, 'Hitscan', puff, f);
		refiring = false;
	}

	void FireRail(RSLD_Shot s, double angle, double pitch, int damage, class<Actor> puff, double range, int color1 = -1, int color2 = -1,
		int duration = 0, double sparsity = 1.0, double drift = 1.0)
	{
		if (!s || !s.mo) return;
		if (range <= 0) range = PLAYERMISSILERANGE;	// NEEDS_C 6: RailAttack takes the distance as given (0 = a zero-length rail)
		pelX.angle = angle; pelX.pitch = pitch; pelX.aimAngle = s.aimAngle; pelX.aimPitch = s.aimPitch; pelX.spreadMul = 1;
		pelX.range = range; pelX.damage = damage; pelX.flags = 0; pelX.puff = puff; pelX.damageType = 'Hitscan'; pelX.index = -1; pelX.rail = true;
		let r = NewRec(s, pelX);
		FRailParams q;
		q.damage = damage; q.offset_xy = 0; q.offset_z = 0; q.color1 = color1; q.color2 = color2; q.maxdiff = 0;
		q.flags = RGF_SILENT | (s.hand == RSLD.OFF ? RGF_ISOFFHAND : 0); q.puff = puff;
		q.angleoffset = Actor.DeltaAngle(s.mo.angle, angle); q.pitchoffset = pitch - s.mo.pitch;
		q.distance = range; q.duration = duration; q.sparsity = sparsity; q.drift = drift; q.spawnclass = null; q.SpiralOffset = 270; q.limit = 0;
		refiring = true;
		railRec = r; railPuff = false; railAt = (0, 0, 0);
		s.mo.RailAttack(q);
		refiring = false;
		railRec = null;
		EndRec(r, railPuff ? RSLD.RES_WALL : RSLD.RES_NONE, railAt);	// NEEDS_C 4: no puff = nothing hit; round 2: where it ended
	}

	override void WorldRailgunFired(WorldEvent e)
	{
		if (railRec && e.Thing == railRec.s.mo) { if (e.Inflictor) railPuff = true; railAt = e.DamagePosition; }
	}

	static bool NotAShot(string n)
	{
		n = n.MakeLower();
		static const string words[] = { "case", "casing", "clip", "ammospawn", "flashlight", "alerter", "taunter", "shakeyourass",
			"distantfiresound", "links", "tracer", "smoke", "muzzle", "spark", "shell", "mag", "puff" };
		for (int i = 0; i < words.Size(); i++) if (n.IndexOf(words[i]) >= 0) return true;
		return false;
	}

	// a BD22 helper missile, never a shot (round 2, NEEDS_B v2): its class or any ancestor is named like one (BD22's
	// RocketGlassBreaker is an Alerter), or it carries no damage (Rifle: EmptyBrass at T+1; rocket: RedFlareSpawn,
	// BackblastFlames*, LiquidExplosionEffectSpawner 4 tics later: rig r2_pull0). Helpers never start a pull.
	static bool Helper(Actor a)
	{
		if (!a) return false;
		for (class<Actor> c = a.GetClass(); c && c != "Actor"; c = (class<Actor>)(c.GetParentClass()))
			if (NotAShot(c.GetClassName())) return true;
		return a.GetMissileDamage(0, 1) <= 0;
	}

	static bool IsStrike(Actor a)
	{
		for (class<Actor> c = a.GetClass(); c; c = (class<Actor>)(c.GetParentClass()))
		{
			Name n = c.GetClassName();
			if (n == 'MeleeStrike1' || n == 'KickAttack') return true;
		}
		string s = a.GetClassName();
		return s.IndexOf("MeleeStrike") >= 0 || s.IndexOf("KickAttack") >= 0;
	}

	// which controller a player's projectile came from (nearest)
	static int HandOf(PlayerPawn mo, Actor a)
	{
		if (!mo.OverrideAttackPosDir || !mo.player.OffhandWeapon) return RSLD.MAIN;
		double dm = (a.pos - mo.AttackPos).Length(), dof = (a.pos - mo.OffhandPos).Length();
		return dof < dm ? RSLD.OFF : RSLD.MAIN;
	}

	override void WorldThingSpawned(WorldEvent e)
	{
		if (!ldOn) return;
		let a = e.Thing;
		if (!a) return;
		let it = Inventory(a);
		if (it)
		{
			if (it.Owner) return;
			string n = it.GetClassName();
			if (n.Left(2) != "LD" || n.IndexOf("Legendary") < 0) return;
			for (int s = 0; s < 9; s++)
			{
				string pa = "LD" .. RSLD_Data.Slots[s] .. "PickupLegendary";
				string pb = "LD" .. RSLD_Data.Slots[s] .. "PickupDroppedLegendary";
				if (n ~== pa || n ~== pb) { RSLD_Converter.Watch(it, s, n ~== pb); return; }
			}
			return;
		}
		string an = a.GetClassName();
		if (an.Left(2) == "LD" && !a.bMISSILE && RSLD_StartVisuals.Check(a)) return;
		if (a is "RSQ_PlayerRound")	// a True Bullets round: it carries the oldest pellet still waiting for one
		{
			let ro = PlayerPawn(a.target);
			for (int pn = 0; pn < MAXPLAYERS; pn++)
			{
				if (!playeringame[pn] || (ro && players[pn].mo != ro)) continue;
				let r = RoundRec(pn);
				if (r) { Tag(a, r.s, r); return; }
			}
			return;
		}
		if (!a.bMISSILE || !a.target) return;
		let mo = PlayerPawn(a.target);
		if (!mo || !mo.player) return;
		string cn = a.GetClassName();
		if (cn.Left(2) == "LD") return;	// LegenDoom's own effect actors
		int hand = HandOf(mo, a);
		let w = hand == RSLD.OFF ? mo.player.OffhandWeapon : mo.player.ReadyWeapon;
		if (TagOf(a)) return;	// already met at its first hit (FindShot)
		if (IsStrike(a))
		{
			int sl = SlotOf(w);
			if (sl != 0 && sl != 1) return;	// a kick / gun bash is not a LegenDoom attack (it gets the held effect, no pull)
			let s = PullOf(mo, hand, w, true);
			if (!s) return;
			Tag(a, s);
			s.fx.OnMelee(s, a);
			return;
		}
		if (Helper(a))
		{	// NEEDS_B 4b: BD22's alert helpers of a pull already under way this tic (Stealth)
			string lc = cn.MakeLower();
			int k = mo.PlayerNumber() * 2 + hand;
			if (RSLD.DebugLevel() > 2) RSLD.Log(String.Format("helper %s (dmg %d): not a shot", cn, a.GetMissileDamage(0, 1)));
			if ((lc.IndexOf("alerter") >= 0 || lc.IndexOf("distantfiresound") >= 0) && lastPullTic[k] == level.maptime && cur[k])
				if (cur[k].fx.OnAlerter(cur[k], a)) { cur[k].Log("alerter " .. cn .. " removed"); a.Destroy(); }
			return;
		}
		let s = PullOf(mo, hand, w, false);
		if (!s) return;
		s.missiles++;
		if (RSLD.DebugLevel() > 1) s.Log(String.Format("missile %s (dmg %d) %.0f from the player", cn, a.GetMissileDamage(0, 1), a.Distance3D(mo)));
		Tag(a, s);
		s.fx.OnMissile(s, a);
	}

	// the pull a damage event belongs to; a no-pull context (s.pull 0) of the main hand's effect otherwise
	RSLD_Shot FindShot(PlayerPawn mo, Actor inflictor)
	{
		int pn = mo.PlayerNumber();
		if (inflictor && inflictor != mo)
		{
			let t = TagOf(inflictor);
			if (t) return t;
			// a strike or missile that hit at its spawn (P_CheckMissileSpawn: a punch thrown into an enemy's face, a
			// rocket fired into a wall) damages before its WorldThingSpawned: its pull starts here
			if (inflictor.bMISSILE && inflictor.target == mo)
			{
				string icn = inflictor.GetClassName();
				int hand = HandOf(mo, inflictor);
				let w = hand == RSLD.OFF ? mo.player.OffhandWeapon : mo.player.ReadyWeapon;
				bool strike = IsStrike(inflictor);
				int sl = SlotOf(w);
				if ((strike && (sl == 0 || sl == 1)) || (!strike && !Helper(inflictor)))
				{
					let s = PullOf(mo, hand, w, strike);
					if (s)
					{
						Tag(inflictor, s);
						if (strike) s.fx.OnMelee(s, inflictor); else { s.missiles++; s.fx.OnMissile(s, inflictor); }
						return s;
					}
				}
			}
		}
		if (deliv && delivTic == level.maptime) return deliv;
		int k = pn * 2;
		if (cur[k] && lastPullTic[k] == level.maptime) return cur[k];
		if (cur[k + 1] && lastPullTic[k + 1] == level.maptime) return cur[k + 1];
		let w = mo.player.ReadyWeapon;
		int slot;
		let e = FxFor(pn, RSLD.MAIN, w, slot);
		if (!e) return null;
		let s = none[pn];
		if (!s) { s = new("RSLD_Shot"); none[pn] = s; }
		s.mo = mo; s.pn = pn; s.hand = RSLD.MAIN; s.weapon = w; s.slot = slot; s.rarity = slotRar[pn * 9 + slot];
		s.fx = e; s.effName = e.name; s.pull = 0; s.tic = level.maptime; s.b1 = false; s.b2 = false; s.d1 = 0; s.i1 = 0;
		return s;
	}

	// outgoing damage (RSLD_Amp.ModifyDamage)
	int Outgoing(PlayerPawn mo, int damage, Name type, Actor inflictor, Actor victim, int flags)
	{
		if (!ldOn || inDamage) return damage;
		if (inflictor) { string ic = inflictor.GetClassName(); if (ic.Left(2) == "LD" && !TagOf(inflictor)) return damage; }	// LegenDoom's own effect damage (not a projectile a pull fired: s.TagMissile)
		if (inflictor && inflictor.bMISSILE && inflictor.target == mo && !IsStrike(inflictor) && Helper(inflictor)) return damage;	// RocketGlassBreaker's 1
		let s = FindShot(mo, inflictor);
		if (!s || !s.fx) return damage;
		hit.target = victim; hit.inflictor = inflictor; hit.damage = damage; hit.setDamage = -1; hit.flags = flags;
		hit.damageType = type; hit.mult = 1.0; hit.killed = false;
		s.fx.ModifyDamage(s, hit);
		int nd = hit.setDamage >= 0 ? hit.setDamage : int(damage * hit.mult);
		if (nd != damage && RSLD.Debug())
			s.Log(String.Format("damage %d -> %d (x%.2f) on %s", damage, nd, hit.mult, victim ? victim.GetClassName() : 'none'));
		return nd;
	}

	bool Pickup(PlayerPawn mo, Inventory item)
	{
		if (!ldOn || !item) return false;
		int pn = mo.PlayerNumber();
		bool block = false;
		for (int s = 0; s < 9; s++)
		{
			let e = slotFx[pn * 9 + s];
			if (!e || FirstSlotOf(pn, e) != s) continue;
			if (e.OnPickup(mo, item, CopiesOf(pn, e))) block = true;
		}
		for (int i = 0; i < fx.Size(); i++)	// NEEDS_B 4a: shared effects also for a picker who owns none
			if (fx[i].anyPickup && FirstSlotOf(pn, fx[i]) < 0 && fx[i].OnPickup(mo, item, 0)) block = true;
		string icn = item.GetClassName();
		if (icn.Left(2) == "LD") slotCacheTic[pn] = -1000;	// a legendary token: refresh next tic
		return block;
	}

	int CopiesOf(int pn, RSLD_Effect e)
	{
		int n = 0;
		for (int s = 0; s < 9; s++) if (slotFx[pn * 9 + s] == e) n++;
		return n;
	}

	int FirstSlotOf(int pn, RSLD_Effect e)
	{
		for (int s = 0; s < 9; s++) if (slotFx[pn * 9 + s] == e) return s;
		return -1;
	}

	// ================================================================ hits and kills
	override void WorldThingDamaged(WorldEvent e)
	{
		if (!ldOn || inDamage) return;
		let mo = PlayerPawn(e.DamageSource);
		let t = e.Thing;
		if (mo && mo.player && t && t != mo)
		{	// the pellet whose trace is running gets what it damaged (its OnPelletEnd)
			RSLD_PelletRec r = (delivRec && delivTic == level.maptime) ? delivRec : pendRec[mo.PlayerNumber()];
			if (r && !r.ended && !r.thing) { r.thing = t; r.monster = t.bIsMonster; }
		}
		if (!mo || !mo.player || !t || t == mo || !t.bIsMonster) return;
		if (e.Inflictor) { string ic = e.Inflictor.GetClassName(); if (ic.Left(2) == "LD" && !TagOf(e.Inflictor)) return; }
		if (e.Inflictor && e.Inflictor.bMISSILE && e.Inflictor.target == mo && !IsStrike(e.Inflictor) && Helper(e.Inflictor)) return;
		let s = FindShot(mo, e.Inflictor);
		if (!s || !s.fx) return;
		hit.target = t; hit.inflictor = e.Inflictor; hit.damage = e.Damage; hit.setDamage = -1; hit.flags = e.DamageFlags;
		hit.damageType = e.DamageType; hit.mult = 1.0; hit.killed = t.health <= 0;
		s.hits++;
		if (hit.killed) s.kills++;
		if (RSLD.DebugLevel() > 1) s.Log(String.Format("hit %s dmg %d hp %d%s", t.GetClassName(), e.Damage, t.health, hit.killed ? " killed" : ""));
		inDamage = true;
		s.fx.OnHit(s, hit);
		// a kill is an enemy's death: BD22's dying-body actors (DyingBaron1 ...: +ISMONSTER, +SHOOTABLE, no COUNTKILL) that
		// take the rest of a blast are not a second kill (rig 11-06: WarmUp counted 2 kills for one Baron)
		if (hit.killed && (t.bCOUNTKILL || RSLD.Has(t, "LDLegendaryMonsterToken") > 0)) s.fx.OnKill(s, hit);
		inDamage = false;
	}

	// LegenDoom's TossItem drops at the dying monster's position, read after BD22/XMVE deaths may have removed it
	override void WorldThingDied(WorldEvent e)
	{
		if (!ldOn) return;
		let t = e.Thing;
		if (!t || !t.bIsMonster) return;
		class<Inventory> tok = RSLD.IC("LDLegendaryMonsterToken");
		if (!tok || t.CountInv(tok) == 0) return;
		let mb = ServiceIterator.Find("RSQMB_Service").Next();
		int bf = (mb && mb.GetInt("bossfight", "", 0, 0, t) == 1) ? 1 : 0;
		deathX.Push(t.pos.x); deathY.Push(t.pos.y); deathZ.Push(t.pos.z); deathT.Push(level.maptime); deathBF.Push(bf);
		if (deathT.Size() > 16) { deathX.Delete(0); deathY.Delete(0); deathZ.Delete(0); deathT.Delete(0); deathBF.Delete(0); }
		if (RSLD.Debug() && bf) Console.Printf("RSLD legendary died: %s came with a Bossfight", t.GetClassName());
	}

	bool DeathSpot()
	{
		for (int i = deathT.Size() - 1; i >= 0; i--)
		{
			if (level.maptime - deathT[i] > 105) break;
			spot = (deathX[i], deathY[i], deathZ[i] + 24);
			return true;
		}
		return false;
	}

	static bool BossfightOnly()
	{
		cvar c = cvar.FindCvar("rsld_bossfight_only");
		if (c && !c.GetBool()) return false;
		if (!RSLD.AC("champion_Token")) return false;
		let mb = ServiceIterator.Find("RSQMB_Service").Next();
		return mb && mb.GetInt("bossfights", "", 0, 0, null) == 1;
	}

	int DropFromBossfight(vector3 at)
	{
		bool origin = abs(at.x) < 64 && abs(at.y) < 64;
		int best = -1; double bd = 1e12;
		for (int i = deathT.Size() - 1; i >= 0; i--)
		{
			if (level.maptime - deathT[i] > 105) break;
			if (origin) return i < deathBF.Size() ? deathBF[i] : -1;
			double dx = deathX[i] - at.x, dy = deathY[i] - at.y, d = dx * dx + dy * dy;
			if (d < bd) { bd = d; best = i; }
		}
		if (best < 0 || bd > 256.0 * 256.0 || best >= deathBF.Size()) return -1;
		return deathBF[best];
	}

	// ================================================================ per tic
	override void WorldTick()
	{
		if (!ldOn) return;
		// the pulls of the last tic: ammo taken is known now
		for (int i = 0; i < pend.Size(); i++)
		{
			let s = pend[i];
			if (!s.mo || s.afterDone) continue;
			s.afterDone = true;
			int k = s.pn * 2 + s.hand;
			if (snapW[k] == s.weapon || s.weapon)
			{
				s.magTaken = max(0, s.preMag - MagOf(s.weapon));
				s.resTaken = max(0, s.preRes - ResOf(s.weapon));
				s.ammoTaken = s.magTaken + s.resTaken;
			}
			if (RSLD.DebugLevel() > 1) s.Log(String.Format("after pull: pellets %d missiles %d hits %d kills %d ammo taken %d (mag %d) [mag %d -> %d, res %d -> %d]", s.pellets, s.missiles, s.hits, s.kills, s.ammoTaken, s.magTaken, s.preMag, MagOf(s.weapon), s.preRes, ResOf(s.weapon)));
			s.fx.AfterPull(s);
		}
		pend.Clear();
		deliv = null; delivRec = null;
		for (int i = roundQ.Size() - 1; i >= 0; i--)	// a pellet that never got its round (a handler took it)
			if (level.maptime - roundQ[i].s.lastTic > 2) { let r = roundQ[i]; roundQ.Delete(i); r.carried = false; EndRec(r, RSLD.RES_NONE, (0, 0, 0)); }
		for (int i = open.Size() - 1; i >= 0; i--)
		{
			let s = open[i];
			if (!s.mo) { open.Delete(i); continue; }
			if (s.lastTic >= level.maptime - 1) continue;	// a pump volley may still continue
			bool timeout = level.maptime - s.tic > 128;
			if (s.recsOpen > 0 && !timeout) continue;
			if (timeout)
				for (int k = tagR.Size() - 1; k >= 0; k--) if (tagR[k] && tagR[k].s == s && !tagR[k].ended) EndRec(tagR[k], RSLD.RES_NONE, (0, 0, 0));
			let pr = pendRec[s.pn];
			if (pr && pr.s == s && !pr.ended) EndRec(pr, RSLD.RES_NONE, (0, 0, 0));
			s.endDone = true;
			open.Delete(i);
			if (RSLD.DebugLevel() > 1) s.Log(String.Format("pull end: %d pellets, %d recs", s.pellets, s.recsTotal));
			if (s.fx) s.fx.OnPullEnd(s);
		}
		if (level.maptime % 35 == 0)
			for (int i = tagA.Size() - 1; i >= 0; i--) if (!tagA[i]) { tagA.Delete(i); tagS.Delete(i); tagR.Delete(i); }
		for (int pn = 0; pn < MAXPLAYERS; pn++)
		{
			if (!playeringame[pn] || !players[pn].mo) continue;
			TickPlayer(pn, players[pn].mo);
		}
	}

	void TickPlayer(int pn, PlayerPawn p)
	{
		let amp = p.FindInventory("RSLD_Amp");
		if (!amp) { p.GiveInventory("RSLD_Amp", 1); amp = p.FindInventory("RSLD_Amp"); }
		// NEEDS_B 3a: first in the inventory chain, or an owned ammo's HandlePickup (true for its own class) ends
		// the chain before RSLD_Amp sees the pickup (inventory.zs TryPickup; AddInventory puts new items first)
		if (amp && p.Inv != amp) { p.RemoveInventory(amp); p.AddInventory(amp); }
		let pl = p.player;
		// LegenDoom's own weapons leave; their tokens stay
		for (int s = 0; s < 9; s++)
		{
			class<Inventory> lc = RSLD_Data.LDWeapons[s];
			if (!lc) continue;
			let w = p.FindInventory(lc);
			if (!w) continue;
			bool hw = (pl.ReadyWeapon == w || pl.PendingWeapon == w);
			class<Inventory> act = "LD" .. RSLD_Data.Slots[s] .. "EffectActive";
			if (act && p.CountInv(act) > 0)
			{
				class<Weapon> g = GiveClassFor(s, p);
				if (g && !OwnsGun(p, s, g)) p.GiveInventory(g, 1);
			}
			if (RSLD.Debug()) Console.Printf("RSLD: took LegenDoom's %s from player %d", w.GetClassName(), pn);
			p.RemoveInventory(w);
			w.Destroy();
			if (hw) { pl.PendingWeapon = WP_NOCHANGE; p.PickNewWeapon(null); }
			slotCacheTic[pn] = -1000;
		}
		if (level.maptime % 35 == pn)
		{
			for (int s = 0; s < 9; s++)
			{
				class<Inventory> u = "LD" .. RSLD_Data.Slots[s] .. "_Unlock";
				if (u && p.CountInv(u) == 0 && OwnsFamily(p, s)) p.GiveInventory(u, 1);
			}
		}
		if (level.maptime - slotCacheTic[pn] >= 17) RefreshSlots(pn, p);
		if (level.maptime == 6) MapStart(pn, p);
		Battlerage(p);

		// passives
		for (int s = 0; s < 9; s++)
		{
			let e = slotFx[pn * 9 + s];
			if (e && e.passive && FirstSlotOf(pn, e) == s) e.Owned(p, CopiesOf(pn, e));
		}
		for (int i = 0; i < fx.Size(); i++)
			if (fx[i].anyPickup && fx[i].passive && FirstSlotOf(pn, fx[i]) < 0) fx[i].Owned(p, 0);
		// Perfect's jam (round 2, item 7): LegenDoom's LDPerfectJammed is per player (owner: a miss jams both hands); the
		// gun in a hand is blocked while it carries Perfect. BD22 VR's fire states read these two tokens (their first
		// line: A_JumpIf(... CountInv("RSLD_JamMain" / "RSLD_JamOff") ..., "RSLD_Jammed")).
		for (int hand = 0; hand < 2; hand++)
		{
			bool jam = RSLD_G2.Jammed(p, hand);
			class<Inventory> tok = "RSLD_JamMain";
			if (hand == RSLD.OFF) tok = "RSLD_JamOff";
			bool had = p.CountInv(tok) > 0;
			if (jam && !had) { p.GiveInventory(tok, 1); if (RSLD.Debug()) Console.Printf("RSLD %d Perfect: %s hand JAMMED (trigger blocked)", level.maptime, RSLD.HandName(hand)); }
			else if (!jam && had) { p.TakeInventory(tok, 1); if (RSLD.Debug()) Console.Printf("RSLD %d Perfect: %s hand jam cleared", level.maptime, RSLD.HandName(hand)); }
		}
		// the guns in the hands
		for (int hand = 0; hand < 2; hand++)
		{
			int k = pn * 2 + hand;
			let w = hand == RSLD.OFF ? pl.OffhandWeapon : pl.ReadyWeapon;
			if (w != heldW[k])
			{
				heldW[k] = w; heldSince[k] = level.maptime;
				class<Inventory> pc = RSLD.IC("LDPatientCounter");	// LegenDoom empties it on select and deselect
				if (pc && hand == RSLD.MAIN) p.TakeInventory(pc, 999);
			}
			prevW[k] = snapW[k]; prevMag[k] = snapMag[k]; prevRes[k] = snapRes[k];
			snapW[k] = w; snapMag[k] = MagOf(w); snapRes[k] = ResOf(w);
			if (!w) continue;
			int slot;
			let e = FxFor(pn, hand, w, slot);
			if (!e) continue;
			held.mo = p; held.pn = pn; held.hand = hand; held.slot = slot; held.rarity = slotRar[pn * 9 + slot];
			held.weapon = w; held.fx = e;
			held.attacking = (pl.cmd.buttons & (hand == RSLD.OFF ? BT_OFFHANDATTACK : (BT_ATTACK | BT_ALTATTACK))) != 0;
			held.idle = level.maptime - max(lastPullTic[k], heldSince[k]);
			e.WhileHeld(held);
		}
	}

	int LastPull(int pn, int hand) { return lastPullTic[pn * 2 + hand]; }

	// LegenDoom's start buffs run from its own ENTER/RESPAWN script (LD_ApplyStartBuffs); OnMapStart is ours
	void MapStart(int pn, PlayerPawn p)
	{
		RefreshSlots(pn, p);
		for (int s = 0; s < 9; s++)
		{
			let e = slotFx[pn * 9 + s];
			if (e && FirstSlotOf(pn, e) == s) e.OnMapStart(p, CopiesOf(pn, e));
		}
	}

	override void PlayerRespawned(PlayerEvent e)
	{
		if (!ldOn) return;
		let p = players[e.PlayerNumber].mo;
		if (p) MapStart(e.PlayerNumber, p);
	}

	// Battlerage: LegenDoom's LDBattlerageSpeedBoost timer -> the engine's double firing speed for as long
	static void Battlerage(PlayerPawn p)
	{
		class<Inventory> bc = RSLD.IC("LDBattlerageSpeedBoost");
		let ld = bc ? Powerup(p.FindInventory(bc)) : null;
		let mine = Powerup(p.FindInventory("RSLD_Haste"));
		if (ld && ld.EffectTics > 0)
		{
			if (!mine) { p.GiveInventory("RSLD_Haste", 1); mine = Powerup(p.FindInventory("RSLD_Haste")); }
			if (mine) mine.EffectTics = ld.EffectTics;
		}
		else if (mine) mine.Destroy();
	}

	// ================================================================ monster groups
	bool InGroup(Actor t, string e)
	{
		int bit = -1;
		for (int i = 0; i < GroupNames.Size(); i++) if (GroupNames[i] ~== e) bit = i;
		if (bit < 0) return false;
		if (bit == 7) { class<Inventory> tok = RSLD.IC("LDLegendaryMonsterToken"); return tok && t.CountInv(tok) > 0; }
		if (bit == 6 && t.bBOSS) return true;
		class<Actor> c = t.GetClass();
		int m = -1;
		for (int i = 0; i < grpCls.Size(); i++) if (grpCls[i] == c) { m = grpMask[i]; break; }
		if (m < 0)
		{
			m = 0;
			string n = t.GetClassName();
			class<Actor> root = Actor.GetReplacee(c);
			if (IsAny(t, root, "Zombieman|ShotgunGuy|ChaingunGuy|WolfensteinSS") || Has(n, "Zombie|Sergeant|Commando|Former|Trooper")) m |= 1;
			if (IsAny(t, root, "DoomImp|Archvile") || Has(n, "Imp|Vile")) m |= 2;
			if (IsAny(t, root, "Demon|Spectre") || (Has(n, "Demon|Spectre|Spectro|Pinky") && !Has(n, "Cyber|Caco"))) m |= 4;
			if (IsAny(t, root, "LostSoul|Cacodemon|PainElemental") || Has(n, "Caco|LostSoul|PainElemental")) m |= 8;
			if (IsAny(t, root, "Arachnotron|Revenant|Fatso") || Has(n, "Arachno|Revenant|Mancub|Fatso")) m |= 16;
			if (IsAny(t, root, "HellKnight|BaronOfHell") || Has(n, "Knight|Baron")) m |= 32;
			if (IsAny(t, root, "Cyberdemon|SpiderMastermind") || Has(n, "Cyberdemon|Mastermind")) m |= 64;
			grpCls.Push(c); grpMask.Push(m);
		}
		return (m & (1 << bit)) != 0;
	}

	static bool IsAny(Actor t, class<Actor> root, string list)
	{
		Array<string> l; list.Split(l, "|");
		for (int i = 0; i < l.Size(); i++)
		{
			class<Actor> c = l[i];
			if (c && (t is c || root == c)) return true;
		}
		return false;
	}

	static bool Has(string n, string list)
	{
		Array<string> l; list.Split(l, "|");
		n = n.MakeLower();
		for (int i = 0; i < l.Size(); i++) if (n.IndexOf(l[i].MakeLower()) >= 0) return true;
		return false;
	}

	// ================================================================ menu actions and the rig probe
	void SetSlotLegendary(PlayerPawn p, int s, string eff, int rar)
	{
		string sn = RSLD_Data.Slots[s];
		for (let i = p.Inv; i; )
		{
			let nx = i.Inv;
			string cn = i.GetClassName();
			string pa = "LD" .. sn .. "EffectActive", pl = "LD" .. sn .. "Legendary", pe = "LD" .. sn .. "Effect_";
			if (cn ~== pa || cn.Left(pl.Length()) ~== pl || cn.Left(pe.Length()) ~== pe) { p.RemoveInventory(i); i.Destroy(); }
			i = nx;
		}
		probeFx[p.PlayerNumber() * 9 + s] = null;
		class<Inventory> tok = "LD" .. sn .. "Effect_" .. eff;
		if (eff != "" && !tok)
		{	// rig probe: LegenDoom has no token for this effect on this slot (it never rolls it there)
			probeFx[p.PlayerNumber() * 9 + s] = FindFx(eff);
			Console.Printf("RSLD probe: LegenDoom has no LD%sEffect_%s token: the effect is forced for the probe only", sn, eff);
		}
		else if (eff != "")
		{
			RSLD.Give(p, "LD" .. sn .. "EffectActive");
			RSLD.Give(p, "LD" .. sn .. "Legendary" .. RSLD_Data.Rarities[clamp(rar, 0, 3)]);
			RSLD.Give(p, "LD" .. sn .. "Effect_" .. eff);
		}
		RefreshSlots(p.PlayerNumber(), p);
	}

	static int RarityFromRolls(int s, string eff)
	{
		for (int i = 0; i < RSLD_Tables.Rolls.Size(); i++)
		{
			Array<string> f; RSLD_Tables.Rolls[i].Split(f, "|");
			if (f.Size() == 3 && f[0] ~== RSLD_Data.Slots[s] && f[2] ~== eff)
				for (int r = 0; r < 4; r++) if (f[1] ~== RSLD_Data.Rarities[r]) return r;
		}
		return -1;
	}

	override void NetworkProcess(ConsoleEvent e)
	{
		if (!ldOn) return;
		int pn = e.Player;
		if (pn < 0 || pn >= MAXPLAYERS || !playeringame[pn]) return;
		let p = players[pn].mo;
		if (!p) return;
		string n = e.Name;
		if (n == "rsld_drop" || n == "rsldp_drop") { DropHeld(pn, p); return; }
		if (n.Left(7) == "rsld_fx")
		{
			int s = SlotOf(p.player.ReadyWeapon);
			if (s < 0) { Console.Printf("RSLD probe: %s is not a legendary gun", p.player.ReadyWeapon ? p.player.ReadyWeapon.GetClassName() : 'nothing'); return; }
			if (n == "rsld_fx_clear") { SetSlotLegendary(p, s, "", 0); Console.Printf("RSLD probe: cleared slot %s", RSLD_Data.Slots[s]); return; }
			string eff = n.Mid(8);
			let x = FindFx(eff);
			int rr = RarityFromRolls(s, eff);
			int rar = e.Args[0] > 0 ? e.Args[0] - 1 : max(rr, 0);
			SetSlotLegendary(p, s, eff, rar);
			Console.Printf("RSLD probe: %s on %s slot %s rarity %s%s%s", eff, p.player.ReadyWeapon.GetClassName(), RSLD_Data.Slots[s],
				RSLD_Data.Rarities[clamp(rar, 0, 3)], x ? "" : " (NO RSLD_Fx class: not carried)", rr < 0 ? " (LegenDoom never rolls it on this slot)" : "");
			if (x)
			{
				let s0 = FindShot(p, null);
				if (s0) x.OnProbe(s0);
			}
			return;
		}
		if (n.Left(11) == "rsld_target")
		{
			string cls = n.Mid(12);
			double d = e.Args[0] > 0 ? e.Args[0] : 160;
			class<Actor> c = cls;
			if (!c) { Console.Printf("RSLD probe: no class %s", cls); return; }
			// where the gun in the main hand points (VR: the controller's AttackDir), on the floor
			Vector3 at = p.Vec3Angle(d, p.angle);
			if (p.OverrideAttackPosDir)
			{
				Vector3 ad = p.AttackDir(p, p.angle, p.pitch);
				at = p.Vec3Angle(d, ad.x);
			}
			let m = Actor.Spawn(c, at, NO_REPLACE);	// the class asked for (BD22 class names: RifleZombie, Imp, BullDemon...)
			if (!m) return;
			m.angle = m.AngleTo(p);
			if (e.Args[2] > 0) { m.bFRIENDLY = true; m.speed = 0; m.vel = (0, 0, 0); m.bDONTTHRUST = true; }	// arg 3 > 0: a still dummy (speed 0: it does not walk; friendly: it does not fight)
			probeTargets.Push(m);
			if (e.Args[1] > 0) m.health = e.Args[1];
			Vector3 gd = p.OverrideAttackPosDir ? p.AttackDir(p, p.angle, p.pitch) : (p.angle, p.pitch, 0);
			Console.Printf("RSLD probe: target %s (%s) at %.0f (%.0f %.0f), health %d; player at (%.0f %.0f) angle %.1f pitch %.1f, gun angle %.1f pitch %.1f",
				m.GetClassName(), cls, d, m.pos.x, m.pos.y, m.health, p.pos.x, p.pos.y, p.angle, p.pitch, gd.x, gd.y);
			return;
		}
		// rig probe helpers (TEST: never in a menu): player health, inventory checks on the player / last target
		if (n.Left(12) == "rsld_health:") { p.A_SetHealth(n.Mid(12).ToInt()); Console.Printf("RSLD probe: health %d", p.health); return; }
		if (n.Left(9) == "rsld_has:" || n.Left(10) == "rsld_thas:")
		{
			bool tg = n.Left(10) == "rsld_thas:";
			string cls = n.Mid(tg ? 10 : 9);
			Actor who = p;
			if (tg) { who = null; for (int i = probeTargets.Size() - 1; i >= 0 && !who; i--) who = probeTargets[i]; }
			if (!who) { Console.Printf("RSLD probe: no target"); return; }
			class<Inventory> c = cls;
			let it = c ? who.FindInventory(c, true) : null;
			let pw = Powerup(it);
			Console.Printf("RSLD probe: %s %s has %s x%d%s health %d speed %.1f%s", tg ? "target" : "player", who.GetClassName(), cls, it ? it.Amount : 0,
				pw ? String.Format(" (%d tics)", pw.EffectTics) : "", who.health, who.speed, who.bFRIGHTENED ? " frightened" : "");
			return;
		}
		if (n.Left(11) == "rsld_count:")	// actors whose class name starts with the prefix
		{
			string pre = n.Mid(11);
			int k = 0;
			let it = ThinkerIterator.Create("Actor");
			Actor a;
			while (a = Actor(it.Next())) { string cn = a.GetClassName(); if (cn.Left(pre.Length()) ~== pre) k++; }
			Console.Printf("RSLD probe: %d actors %s*", k, pre);
			return;
		}
		if (n == "rsld_cleartargets")
		{
			int k = 0;
			for (int i = 0; i < probeTargets.Size(); i++) if (probeTargets[i]) { probeTargets[i].Destroy(); k++; }
			probeTargets.Clear();
			Console.Printf("RSLD probe: %d targets removed", k);
			return;
		}
		if (n == "rsld_legtarget")	// make the last target a LegenDoom legendary (its token, as LDMonsterInit gives)
		{
			for (int i = probeTargets.Size() - 1; i >= 0; i--) if (probeTargets[i]) { RSLD.Give(probeTargets[i], "LDLegendaryMonsterToken"); Console.Printf("RSLD probe: %s is legendary", probeTargets[i].GetClassName()); break; }
			return;
		}
		if (n.Left(9) == "rsld_amm:")	// the held gun's magazine / reserve
		{
			let w = p.player.ReadyWeapon;
			Console.Printf("RSLD probe: %s magazine %d reserve %d", w ? w.GetClassName() : 'none', MagOf(w), ResOf(w));
			return;
		}
		if (n == "rsld_mapstart")	// rig probe: what the map start / respawn does (OnMapStart of every owned effect)
		{
			MapStart(pn, p);
			return;
		}
		if (n == "rsld_owned")
		{
			RefreshSlots(pn, p);
			for (int s = 0; s < 9; s++)
			{
				string en = slotEff[pn * 9 + s];
				if (en == "") continue;
				let x = slotFx[pn * 9 + s];
				Console.Printf("RSLD owned: %s %s %s copies %d%s", RSLD_Data.Slots[s], slotRar[pn * 9 + s] >= 0 ? RSLD_Data.Rarities[slotRar[pn * 9 + s]] : "?", en,
					RSLD.Count(p, en), x ? "" : " (not carried)");
			}
			Console.Printf("RSLD owned: %d effects registered", fx.Size());
			return;
		}
		if (n.Left(12) == "rsld_reroll:")	// rig probe (round 2): what a drop of <effect> on the held gun's slot becomes
		{
			int s = SlotOf(p.player.ReadyWeapon);
			string eff = n.Mid(12);
			if (s < 0) return;
			int r = max(RarityFromRolls(s, eff), 0);
			string l = "";
			for (int i = 0; i < 4; i++) l = l .. " " .. RSLD_Reroll.Reroll(s, r, eff);
			Console.Printf("RSLD probe: a %s %s %s drop rolls as:%s (dropped by the owner: %s)", RSLD_Data.Slots[s], RSLD_Data.Rarities[r], eff, l, RSLD_Reroll.IsDropped(eff) ? "yes" : "no");
			return;
		}
		if (n == "rsld_loadorder")	// rig probe (round 2, item 2): whose title map, HUD and sound definitions win
		{	// (Wads.GetLumpFullPath crashed QZD 17.3 on the rig: container index + length only; the tool maps them to files)
			let li = LevelInfo.FindLevelInfo("TITLEMAP");
			Console.Printf("RSLD loadorder: TITLEMAP's MAPINFO name \"%s\"", li ? li.LevelName : "none");
			string ll = "maps/titlemap.wad|SBARINFO|SNDINFO|MAPINFO";	// never a method call on a literal (VM crash, rig round 2)
			Array<string> lumps; ll.Split(lumps, "|");
			for (int k = 0; k < lumps.Size(); k++)
			{
				string l = "";
				bool full = lumps[k].IndexOf("/") >= 0;
				int i = full ? Wads.FindLumpFullName(lumps[k], 0) : Wads.FindLump(lumps[k], 0);
				while (i >= 0)
				{
					l = l .. String.Format(" [container %d, %d bytes]", Wads.GetLumpContainer(i), Wads.GetLumpLength(i));
					i = full ? Wads.FindLumpFullName(lumps[k], i + 1) : Wads.FindLump(lumps[k], i + 1);
				}
				Console.Printf("RSLD loadorder: %s in load order (the last read last):%s", lumps[k], l);
			}
			return;
		}
		if (n == "rsld_list")
		{
			string l = "";
			for (int i = 0; i < fx.Size(); i++) l = l .. fx[i].name .. " ";
			Console.Printf("RSLD registered %d: %s", fx.Size(), l);
			return;
		}
	}

	void DropHeld(int pn, PlayerPawn p)
	{
		int s = SlotOf(p.player.ReadyWeapon);
		class<Inventory> act = s >= 0 ? RSLD.IC("LD" .. RSLD_Data.Slots[s] .. "EffectActive") : null;
		if (s < 0 || !act || p.CountInv(act) == 0) { p.A_Print("This gun has no legendary power."); return; }
		string sn = RSLD_Data.Slots[s];
		let lp = RSLD_LegendaryPickup(Actor.Spawn("RSLD_LegendaryPickup", p.Vec3Angle(24, p.angle, p.height * 0.5)));
		if (!lp) return;
		RefreshSlots(pn, p);
		lp.SetupKeep(s, slotRar[pn * 9 + s], slotEff[pn * 9 + s]);
		lp.vel = p.Vec3Angle(6, p.angle, 3) - p.pos;
		SetSlotLegendary(p, s, "", 0);
		if (RSLD.Debug()) Console.Printf("RSLD drop: player %d dropped the %s legendary %s", pn, sn, lp.effect);
	}

	// ================================================================ HUD
	override void RenderOverlay(RenderEvent e)
	{
		if (!ldOn) return;
		cvar on = cvar.FindCvar("rsld_screen_name");
		if (!on || !on.GetBool() || automapactive) return;
		int pn = consoleplayer;
		let w = players[pn].ReadyWeapon;
		int s = SlotOfUI(w);
		if (s < 0) return;
		string eff = slotEff[pn * 9 + s];
		if (eff == "") return;
		int r = slotRar[pn * 9 + s];
		string title = StringTable.Localize("$LD_FX_TITLE_" .. eff);
		if (title.Left(1) == "L" && title.IndexOf("_FX_") >= 0) title = eff;
		string line = String.Format("%s %s", title, w ? w.GetTag() : "");
		int col = r >= 0 ? RSLD_Data.RarityColor[r] : Font.CR_WHITE;
		int x = (320 - smallfont.StringWidth(line)) / 2;
		Screen.DrawText(smallfont, col, x, 3, line, DTA_VirtualWidth, 320, DTA_VirtualHeight, 200, DTA_KeepRatio, true);
	}

	ui int SlotOfUI(Weapon w)
	{
		if (!w) return -1;
		class<Actor> c = w.GetClass();
		string cn = c.GetClassName();
		if (cn.Left(8) == "RSQ_Off_") c = (class<Actor>)(c.GetParentClass());
		for (int i = 0; i < famCls.Size(); i++) if (famCls[i] == c) return famSlot[i];
		return -1;
	}
}

// Perfect's jam tokens (handler TickPlayer): read by BD22 VR's fire states; never given without LegenDoom
class RSLD_JamMain : Inventory { Default { +INVENTORY.UNDROPPABLE +INVENTORY.UNTOSSABLE +INVENTORY.UNCLEARABLE Inventory.MaxAmount 1; } }
class RSLD_JamOff : Inventory { Default { +INVENTORY.UNDROPPABLE +INVENTORY.UNTOSSABLE +INVENTORY.UNCLEARABLE Inventory.MaxAmount 1; } }

// Battlerage's attack speed on BD22 guns (handler.zs Battlerage keeps it as long as LegenDoom's own timer)
class RSLD_Haste : PowerDoubleFiringSpeed
{
	Default { Powerup.Duration 0x7FFFFFFD; +INVENTORY.NOSCREENBLINK }
}

// RSQ Wheel's LegenDoom reader asks for "RSLDP_Service" by name (docs/WHEEL_LEGENDARY_PROPOSAL.md): the name stays.
//   GetString[UI|Data]("ld_prefix", "<weapon class>")  -> "LDShotgun" (the token prefix for that gun), "" if none
class RSLDP_Service : Service
{
	static string Prefix(string weaponClass)
	{
		if (!RSLD.On()) return "";
		string wc = weaponClass;
		if (wc.Left(8) == "RSQ_Off_") wc = wc.Mid(8);
		for (int i = 0; i < RSLD_Data.Family.Size(); i++)
		{
			Array<string> p; RSLD_Data.Family[i].Split(p, "|");
			if (p[1] ~== wc) return "LD" .. RSLD_Data.Slots[p[0].ToInt()];
		}
		return "";
	}
	override String GetString(String request, string stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{ return request ~== "ld_prefix" ? Prefix(stringArg) : ""; }
	override String GetStringUI(String request, string stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{ return request ~== "ld_prefix" ? Prefix(stringArg) : ""; }
	override String GetStringData(String request, string stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{ return request ~== "ld_prefix" ? Prefix(stringArg) : ""; }
}
