// LDL x BD22 VR patch: the handler.
//  1. Replacements: LegenDoom 3.0 replaces 56 classes (its weapons, items, monsters, the player). Loaded after BD22 VR
//     and XMVE it takes those over, so BD22's guns, ammo and health and XMVE's monsters would never spawn.
//     CheckReplacement hands each one back to the class it had before LegenDoom (tables.zs, measured on the rig), not
//     final, so a skill's ReplaceActor still applies as it did. LegenDoom's legendary-monster system does not depend
//     on those classes (its OPEN script gives every monster the chance), so it keeps working on BD22/XMVE monsters.
//  2. LegenDoom's own weapons that reach a player (its start items) are taken away; their tokens stay.
//  3. The legendary effect of the gun in hand (effects.zs), and LegenDoom's unlock tokens for the guns you own.
//  4. HUD line for the gun in hand; "drop legendary" (netevent rsldp_drop) from the menu.

class RSLDP_Handler : EventHandler
{
	string curEffect[MAXPLAYERS];
	int curSlot[MAXPLAYERS];
	int curRarity[MAXPLAYERS];
	double patientMult[MAXPLAYERS];
	int patientWin[MAXPLAYERS];
	Weapon lastWeap[MAXPLAYERS];
	int lastA1[MAXPLAYERS], lastA2[MAXPLAYERS];
	int idle[MAXPLAYERS], atkRecent[MAXPLAYERS], effShots[MAXPLAYERS];
	bool wasAttacking[MAXPLAYERS];
	bool debugHits, guard, inRepl;

	Array<double> deathX, deathY, deathZ;
	Array<int> deathT;
	Array<int> deathBF;	// 1: the legendary came with an RSQ Miniboss Bossfight (RSQMB_Service "bossfight")
	Array<class<Weapon> > famCls;
	Array<int> famSlot;
	Array<string> rcFrom;
	Array<class<Actor> > rcTo;

	clearscope static bool Debug() { cvar c = cvar.FindCvar("rsldp_debug"); return c && c.GetInt() > 0; }

	override void OnRegister()
	{
		for (int i = 0; i < RSLDP_Data.Family.Size(); i++)
		{
			Array<string> p; RSLDP_Data.Family[i].Split(p, "|");
			class<Weapon> c = p[1];
			if (c) { famCls.Push(c); famSlot.Push(p[0].ToInt()); }
		}
		for (int i = 0; i < MAXPLAYERS; i++) { curSlot[i] = -1; curRarity[i] = -1; patientMult[i] = 1.0; }
	}

	// ---------------------------------------------------------------- 1. replacements
	class<Actor> ResolveRepl(string replacee, string ldcls, out bool found)
	{
		found = false;
		for (int i = 0; i < rcFrom.Size(); i++) if (rcFrom[i] ~== replacee) { found = true; return rcTo[i]; }
		for (int i = 0; i < RSLDP_Tables.Repl.Size(); i++)
		{
			Array<string> f; RSLDP_Tables.Repl[i].Split(f, "|");
			if (!(f[0] ~== replacee) || !(f[1] ~== ldcls)) continue;
			class<Actor> to = FindClassLoose(f[2]);
			if (!to) to = FindClassLoose(f[3]);
			if (to && to.GetClassName() == replacee) to = null;	// it had no replacement before LegenDoom
			found = true;
			rcFrom.Push(replacee); rcTo.Push(to);
			if (Debug()) { string tn = replacee; if (to) tn = to.GetClassName(); Console.Printf("RSLDP replace: %s was %s under LegenDoom, back to %s", replacee, ldcls, tn); }
			return to;
		}
		return null;
	}

	// a measured name; a class renamed for a duplicate (Name@file.pk3@lump) is found again if the file was renamed
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
		if (!e.Replacement || inRepl) return;
		string rn = e.Replacement.GetClassName();
		if (rn.Left(2) != "LD") return;
		inRepl = true;
		bool found;
		class<Actor> to = ResolveRepl(e.Replacee.GetClassName(), rn, found);
		inRepl = false;
		if (found) e.Replacement = to;	// not final: a skill ReplaceActor and the rest of the chain still apply
	}

	// ---------------------------------------------------------------- weapons and families
	int SlotOf(Weapon w)
	{
		if (!w) return -1;
		let c = w.GetClass();
		for (int i = 0; i < famCls.Size(); i++) if (famCls[i] == c) return famSlot[i];
		return -1;
	}

	static bool OwnsFamily(Actor a, int s)
	{
		for (int i = 0; i < RSLDP_Data.Family.Size(); i++)
		{
			Array<string> p; RSLDP_Data.Family[i].Split(p, "|");
			if (p[0].ToInt() != s) continue;
			class<Inventory> c = p[1];
			if (c && a.CountInv(c) > 0) return true;
		}
		return false;
	}

	// the player already has the gun a legendary pickup of slot s shows (give), or one of its own copies (Data.Same)
	static bool OwnsGun(Actor a, int s, class<Weapon> give)
	{
		if (!give || a.CountInv(give) > 0) return true;
		if (give.GetClassName() == "BrutalRevolver") return false;	// the Moonlight: only itself
		Array<string> l; RSLDP_Data.Same[s].Split(l, "|");
		for (int i = 0; i < l.Size(); i++) { class<Inventory> c = l[i]; if (c && a.CountInv(c) > 0) return true; }
		return false;
	}

	static class<Weapon> GiveClassFor(int s, Actor who)
	{
		if (s == 2)	// BD22 VR "Moonlight Replaces Pistol": the Moonlight stands in for the pistol
		{
			cvar ml = cvar.FindCvar("rsq_moonlight_pistol");
			class<Weapon> m = (class<Weapon>)(RSLDP_Data.AC("BrutalRevolver"));
			if (ml && ml.GetBool() && m) return m;
		}
		class<Weapon> c = RSLDP_Data.Give[s];
		return c;
	}

	// ---------------------------------------------------------------- 2./3. per tic
	override void WorldThingSpawned(WorldEvent e)
	{
		let it = Inventory(e.Thing);
		if (!it || it.Owner) return;
		string n = it.GetClassName();
		if (n.Left(2) != "LD" || n.IndexOf("Legendary") < 0) return;
		for (int s = 0; s < 9; s++)
		{
			string a = "LD" .. RSLDP_Data.Slots[s] .. "PickupLegendary";
			string b = "LD" .. RSLDP_Data.Slots[s] .. "PickupDroppedLegendary";
			if (n ~== a || n ~== b) { RSLDP_Converter.Watch(it, s, n ~== b); return; }
		}
	}

	override void WorldTick()
	{
		debugHits = Debug();
		for (int pn = 0; pn < MAXPLAYERS; pn++)
		{
			if (!playeringame[pn] || !players[pn].mo) continue;
			TickPlayer(pn, players[pn].mo);
		}
	}

	void TickPlayer(int pn, PlayerPawn p)
	{
		if (!p.FindInventory("RSLDP_Amp")) p.GiveInventory("RSLDP_Amp", 1);
		let pl = p.player;
		// LegenDoom's own weapons (its start items, or anything else that gives one) leave; their tokens stay
		for (int s = 0; s < 9; s++)
		{
			class<Inventory> lc = RSLDP_Data.LDWeapons[s];
			if (!lc) continue;
			let w = p.FindInventory(lc);
			if (!w) continue;
			bool held = (pl.ReadyWeapon == w || pl.PendingWeapon == w);
			class<Inventory> act = "LD" .. RSLDP_Data.Slots[s] .. "EffectActive";
			if (act && p.CountInv(act) > 0)
			{
				class<Weapon> g = GiveClassFor(s, p);
				if (g && !OwnsGun(p, s, g)) p.GiveInventory(g, 1);
			}
			if (Debug()) Console.Printf("RSLDP: took LegenDoom's %s from player %d", w.GetClassName(), pn);
			p.RemoveInventory(w);
			w.Destroy();
			if (held) { pl.PendingWeapon = WP_NOCHANGE; p.PickNewWeapon(null); }
		}
		// LegenDoom's Unlock Mode (its default) drops legendaries only for weapons whose LD<Slot>_Unlock you hold;
		// owning a BD22 gun of that family unlocks it, as picking up LegenDoom's gun would
		if (level.maptime % 35 == pn)
		{
			for (int s = 0; s < 9; s++)
			{
				class<Inventory> u = "LD" .. RSLDP_Data.Slots[s] .. "_Unlock";
				if (u && p.CountInv(u) == 0 && OwnsFamily(p, s)) p.GiveInventory(u, 1);
			}
		}
		if (level.maptime == 6) StartOfMap(pn, p);
		Battlerage(p);

		let w = pl.ReadyWeapon;
		if (w != lastWeap[pn] || level.maptime % 8 == 0)
		{
			int s = SlotOf(w);
			curSlot[pn] = s;
			curEffect[pn] = RSLDP_Effects.EffectOf(p, s);
			curRarity[pn] = RSLDP_Effects.RarityOf(p, s);
		}
		if (w != lastWeap[pn])
		{
			lastWeap[pn] = w;
			idle[pn] = 0;
			class<Inventory> pc = (class<Inventory>)(RSLDP_Data.AC("LDPatientCounter"));	// LegenDoom empties it on select and deselect
			if (pc) p.TakeInventory(pc, 999);
			lastA1[pn] = AmmoOf(w, 1); lastA2[pn] = AmmoOf(w, 2);
			return;
		}
		if (patientWin[pn] > 0 && --patientWin[pn] == 0) patientMult[pn] = 1.0;
		string e = curEffect[pn];
		bool attacking = (pl.cmd.buttons & (BT_ATTACK | BT_ALTATTACK)) != 0;
		if (attacking) atkRecent[pn] = 4; else if (atkRecent[pn] > 0) atkRecent[pn]--;
		int a1 = AmmoOf(w, 1), a2 = AmmoOf(w, 2);
		int shots = 0;
		int drop = (lastA1[pn] + lastA2[pn]) - (a1 + a2);
		if (drop > 0 && atkRecent[pn] > 0) shots = min(drop, 30);
		bool magShot = lastA2[pn] - a2 > 0;
		if (w && !w.Ammo1 && attacking && !wasAttacking[pn]) shots = 1;	// melee: a swing
		wasAttacking[pn] = attacking;
		if (e != "" && w)
		{
			if (shots > 0) OnShots(pn, p, w, e, shots, magShot);
			if (attacking) idle[pn] = 0; else idle[pn]++;
			WhileHeld(pn, p, w, e, attacking);
		}
		lastA1[pn] = AmmoOf(w, 1); lastA2[pn] = AmmoOf(w, 2);
	}

	// "Battlerage": killing gives LegenDoom's LDBattlerageSpeedBoost (its HUD timer); LegenDoom's guns read it to fire
	// faster. BD22 guns get the engine's double firing speed for exactly as long.
	static void Battlerage(PlayerPawn p)
	{
		class<Inventory> bc = (class<Inventory>)(RSLDP_Data.AC("LDBattlerageSpeedBoost"));
		let ld = bc ? Powerup(p.FindInventory(bc)) : null;
		let mine = Powerup(p.FindInventory("RSLDP_Haste"));
		if (ld && ld.EffectTics > 0)
		{
			if (!mine) { p.GiveInventory("RSLDP_Haste", 1); mine = Powerup(p.FindInventory("RSLDP_Haste")); }
			if (mine) mine.EffectTics = ld.EffectTics;
		}
		else if (mine) mine.Destroy();
	}

	static int AmmoOf(Weapon w, int which)
	{
		if (!w) return 0;
		if (which == 1) return w.Ammo1 ? w.Ammo1.Amount : 0;
		return (w.Ammo2 && w.Ammo2 != w.Ammo1) ? w.Ammo2.Amount : 0;
	}

	static void AddAmmo(Inventory a, int n)
	{
		if (a && n > 0) a.Amount = min(a.Amount + n, max(a.MaxAmount, a.Amount));
	}

	void OnShots(int pn, PlayerPawn p, Weapon w, string e, int shots, bool magShot)
	{
		Inventory back = magShot ? w.Ammo2 : w.Ammo1;
		int refund = 0;
		for (int i = 0; i < shots; i++)
		{
			if (e ~== "Unlikely" && random(1, 100) <= 33) refund++;	// "33% chance of not consuming ammo"
			else if (e ~== "Improbable" && random(1, 100) <= 66) refund++;	// "66% chance"
			else if (e ~== "Efficient" && (++effShots[pn] % 2) == 0) refund++;	// "Uses only half ammo per attack"
			else if (e ~== "Impossible" && random(0, 1)) refund += 2;	// "50% chance of generating ammo instead of using"
			else if (e ~== "Annoying") refund++;	// "doesn't use ammo"
		}
		if (refund > 0 && back)
		{
			AddAmmo(back, refund);
			if (debugHits) Console.Printf("RSLDP ammo: %s refunds %d %s", e, refund, back.GetClassName());
		}
		if (e ~== "Patient")	// consumed on firing; kept as a short window for shots still in flight
		{
			class<Inventory> pc = (class<Inventory>)(RSLDP_Data.AC("LDPatientCounter"));
			if (pc && p.CountInv(pc) > 0)
			{
				patientMult[pn] = (p.CountInv(pc) + 10) / 10.0; patientWin[pn] = 18;
				p.TakeInventory(pc, 999);
			}
		}
		if (e ~== "Desperate" && p.health < 26) Give(p, "LDDesperateInvulnerabilityChecker");	// "below 26% health"
	}

	void WhileHeld(int pn, PlayerPawn p, Weapon w, string e, bool attacking)
	{
		// LegenDoom's ready loops run 35 tics of A_WeaponReady between gifts (Shotgun.dec ReadyReplicating etc.)
		bool beat = !attacking && idle[pn] > 0 && (idle[pn] % 35) == 0;
		if (e ~== "Determined" && !attacking)
		{
			class<Inventory> cd = (class<Inventory>)(RSLDP_Data.AC("LDDeterminedResistanceCooldown"));
			if (cd && p.CountInv(cd) == 0) { Give(p, "LDDeterminedResistance"); p.GiveInventory(cd, 1); }
		}
		if (!beat) return;
		if (e ~== "Replicating") { AddAmmo(w.Ammo1, 1); if (debugHits) Console.Printf("RSLDP: Replicating +1 %s", w.Ammo1 ? w.Ammo1.GetClassName() : 'none'); }
		else if (e ~== "Regenerating") Give(p, "LDHealthBonus");
		else if (e ~== "Patient")
		{
			Give(p, "LDPatientCounter");
			p.A_StartSound("effects/patient", 7, CHANF_DEFAULT, 1.0, 2.0);
		}
		else if (e ~== "Sensing")
		{
			p.A_StartSound("effects/sensing", 7, CHANF_DEFAULT, 1.0, 2.0);
			class<Inventory> se = (class<Inventory>)(RSLDP_Data.AC("LDSensingEffect"));
			if (se) p.A_RadiusGive(se, 1024, RGF_MONSTERS | RGF_OBJECTS | RGF_ITEMS | RGF_NOSIGHT, 1);
		}
	}

	// LegenDoom's own start buffs (LD_ApplyStartBuffs) run from its ENTER script; Resupplying fills LegenDoom's vanilla
	// ammo there, so the bridge fills the ammo of every BD22 gun you carry.
	void StartOfMap(int pn, PlayerPawn p)
	{
		bool any = false;
		string res = "Resupplying";
		for (int s = 0; s < 9 && !any; s++)
		{
			class<Inventory> t = "LD" .. RSLDP_Data.Slots[s] .. "Effect_" .. res;
			if (t && p.CountInv(t) > 0) any = true;
		}
		if (!any) return;
		for (let i = p.Inv; i; i = i.Inv)
		{
			let w = Weapon(i);
			if (w && w.Ammo1) w.Ammo1.Amount = max(w.Ammo1.Amount, w.Ammo1.MaxAmount);
		}
		if (Debug()) Console.Printf("RSLDP: Resupplying filled player %d's BD22 ammo", pn);
	}

	// ---------------------------------------------------------------- hits and kills
	override void WorldThingDamaged(WorldEvent e)
	{
		if (guard) return;
		let src = e.DamageSource;
		let t = e.Thing;
		if (!src || !src.player || !t || t == src || !t.bIsMonster) return;
		if (e.Inflictor) { string ic = e.Inflictor.GetClassName(); if (ic.Left(2) == "LD") return; }	// LegenDoom's own effect damage
		int pn = src.PlayerNumber();
		string eff = curEffect[pn];
		if (eff == "") return;
		int s = curSlot[pn];
		int dmg = e.Damage;
		bool killed = t.health <= 0;
		if (debugHits) Console.Printf("RSLDP hit: %s %s dmg %d hp %d", eff, t.GetClassName(), dmg, t.health);

		// x3 / x4 against the effect's monsters (a second hit of damage x2 / x3, LegenDoom's multipliers on top of the shot)
		if (!killed && RSLDP_Effects.InGroup(t, eff))
		{
			int mult = (eff ~== "DemonSlayer") ? 4 : 3;
			int bonus = dmg * (mult - 1);
			guard = true;
			t.DamageMobj(null, src, bonus, e.DamageType, DMG_NO_ENHANCE | DMG_THRUSTLESS);
			guard = false;
			if (debugHits) Console.Printf("RSLDP group: %s x%d on %s (+%d) hp now %d", eff, mult, t.GetClassName(), bonus, t.health);
			killed = t.health <= 0;
		}
		if (eff ~== "Vampiric") src.GiveBody(dmg / 2);	// A_CustomPunch lifesteal 0.5 (Fist.dec FireVampiric)
		else if (eff ~== "Scavenging")	// CPF_STEALARMOR, lifesteal 0.5, LDScavengingEffect armor bonuses
		{
			class<Inventory> sc = (class<Inventory>)(RSLDP_Data.AC("LDScavengingEffect"));
			for (int i = 0; sc && i < min(dmg / 2, 100); i++) src.GiveInventory(sc, 1);
		}
		else if (eff ~== "Sadistic" && !killed) Give(src, "LDHealthBonus");	// "hits without killing give a health bonus"
		else if (eff ~== "Painful" && !killed) t.TriggerPainChance(e.DamageType, true);	// "Attacks always flinch enemies"
		else if (eff ~== "Thieving") Thieve(src);
		else if (!killed) MonsterSide(t, src, eff);
		if (killed) OnKill(t, src, eff, s);
	}

	// LDThievingEffect: 75% chance, LDThievingCooldown; a pickup of BD22 ammo for the gun in hand
	void Thieve(Actor p)
	{
		class<Inventory> cd = (class<Inventory>)(RSLDP_Data.AC("LDThievingCooldown"));
		if (cd && p.CountInv(cd) > 0) return;
		if (random(0, 255) < 64) return;
		if (cd) p.GiveInventory(cd, 1);
		let w = p.player.ReadyWeapon;
		if (!w || !w.Ammo1) return;
		int amt = max(1, GetDefaultByType(w.Ammo1.GetClass()).Amount);
		AddAmmo(w.Ammo1, amt);
		p.A_StartSound("items/clippickup", CHAN_ITEM);
		if (debugHits) Console.Printf("RSLDP: Thieving +%d %s", amt, w.Ammo1.GetClassName());
	}

	// what LegenDoom's <Effect>BulletPuff gives the monster it hits (Common/Uncommon/Rare/EpicSpecialEffects.dec)
	void MonsterSide(Actor t, Actor src, string eff)
	{
		bool give = false;
		if (!t.target) t.target = src;
		if (eff ~== "Crippling" || eff ~== "Whittling")
		{
			Give(t, "LD" .. eff .. "Effect");
			class<Inventory> va = "LD" .. eff .. "EffectVisualActive";
			if (va && t.CountInv(va) == 0) { Give(t, "LD" .. eff .. "EffectVisualActive"); Give(t, "LD" .. eff .. "EffectCheckerSpawner"); }
			give = true;
		}
		else if (eff ~== "Freezing" || eff ~== "Gravitic")
		{
			class<Inventory> deb = "LD" .. eff .. "SpeedDebuff";
			if (!deb || t.CountInv(deb) == 0) { Give(t, "LD" .. eff .. "Effect"); Give(t, "LD" .. eff .. "EffectCheckerSpawner"); give = true; }
		}
		else if (eff ~== "Incinerating") { if (!t.bNOBLOOD) { Give(t, "LDIncineratingEffect"); give = true; } }
		else if (eff ~== "Violent") { Give(t, "LDViolentEffect"); give = true; }
		else if (eff ~== "Persistent") { Give(t, "LDPersistentBlood"); give = true; }
		else if (eff ~== "Igniting")
		{
			class<Inventory> ia = (class<Inventory>)(RSLDP_Data.AC("LDIgnitingActive"));
			if (!t.bNOBLOOD && (!ia || t.CountInv(ia) == 0)) { Give(t, "LDIgnitingPowerGiver"); give = true; }
		}
		if (give && debugHits) Console.Printf("RSLDP monster: %s on %s", eff, t.GetClassName());
	}

	static void Give(Actor a, string n)
	{
		class<Inventory> c = n;
		if (c) a.GiveInventory(c, 1);
	}

	// LegenDoom's <Effect>EffectDeath item, given to the dead monster with the killer as its target, as LegenDoom's
	// own checkers do (LD<Effect>EffectChecker: A_GiveInventory("LD<Effect>EffectDeath", 1, AAPTR_MASTER))
	static const string KillEffects[] = { "Artifact", "Battlerage", "Bloodthirsty", "Bloody", "Divine", "Endless", "Hopeful", "Infiltrator", "Killstreaker", "Murderous", "Unstoppable", "WarmUp" };

	void OnKill(Actor t, Actor src, string eff, int s)
	{
		if (eff ~== "Incinerating" || eff ~== "Violent") MonsterSide(t, src, eff);	// both act on the corpse too
		bool listed = false;
		for (int i = 0; i < KillEffects.Size(); i++) if (KillEffects[i] ~== eff) listed = true;
		if (!listed) return;
		class<Inventory> c = "LD" .. eff .. "EffectDeath" .. RSLDP_Data.DeathVariant[max(s, 0)];
		if (!c) c = "LD" .. eff .. "EffectDeath";
		if (!c) return;
		t.target = src;
		t.GiveInventory(c, 1);
		if (debugHits) Console.Printf("RSLDP kill: %s gave %s (killer %s)", t.GetClassName(), c.GetClassName(), src.GetClassName());
	}

	// LegenDoom's TossItem (LEGENDFNC.acs) spawns the drop at the dying monster's GetActorX/Y(0) + 4. When BD22/XMVE's
	// death removes the monster actor (gibs, death replacement actors), that reads 0 and the drop lands at the map's
	// origin, (4, 4, 24). The patch remembers where legendary monsters died, for RSLDP_Converter to put drops back.
	override void WorldThingDied(WorldEvent e)
	{
		let t = e.Thing;
		if (!t || !t.bIsMonster) return;
		class<Inventory> tok = (class<Inventory>)(RSLDP_Data.AC("LDLegendaryMonsterToken"));
		if (!tok || t.CountInv(tok) == 0) return;
		let mb = ServiceIterator.Find("RSQMB_Service").Next();
		int bf = (mb && mb.GetInt("bossfight", "", 0, 0, t) == 1) ? 1 : 0;
		while (deathBF.Size() < deathT.Size()) deathBF.Insert(0, -1);	// a save from before deathBF
		deathX.Push(t.pos.x); deathY.Push(t.pos.y); deathZ.Push(t.pos.z); deathT.Push(level.maptime); deathBF.Push(bf);
		if (deathT.Size() > 16) { deathX.Delete(0); deathY.Delete(0); deathZ.Delete(0); deathT.Delete(0); deathBF.Delete(0); }
		if (Debug() && bf) Console.Printf("RSLDP legendary died: %s came with a Bossfight", t.GetClassName());
	}

	// a drop that landed at the map origin -> the most recent legendary death within 3 seconds
	// (no "out vector3": QuestZDoom 17.3's VM aborts on it, "REGT_ADDROF not implemented for vectors")
	vector3 spot;
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

	// BOSSFIGHTS ARE THE ONLY SOURCE (owner 11-05): with LegenDoom AND Champions loaded and RSQ Miniboss's Bossfights on
	// (asked by name: RSQMB_Service "bossfights"), a legendary weapon drops only from a monster that came with a
	// Bossfight (its miniboss or thralls). rsldp_bossfight_only, on. LegenDoom without Champions, or without RSQ
	// Miniboss: unchanged. A drop the player let go of (LD<Slot>PickupDroppedLegendary) is never touched.
	static bool BossfightOnly()
	{
		cvar c = cvar.FindCvar("rsldp_bossfight_only");
		if (c && !c.GetBool()) return false;
		if (!RSLDP_Data.AC("champion_Token")) return false;
		let mb = ServiceIterator.Find("RSQMB_Service").Next();
		return mb && mb.GetInt("bossfights", "", 0, 0, null) == 1;
	}

	// the legendary death this drop came from: within 3 s, the nearest to where it landed (LegenDoom tosses it from the
	// body, + 4); at the map's origin (the body was gone), the newest. -1: none found (not ours to judge), else 0 / 1.
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

	// ---------------------------------------------------------------- 4. menu actions
	override void NetworkProcess(ConsoleEvent e)
	{
		if (e.Name != "rsldp_drop") return;
		int pn = e.Player;
		if (pn < 0 || pn >= MAXPLAYERS || !playeringame[pn]) return;
		let p = players[pn].mo;
		if (!p) return;
		int s = SlotOf(p.player.ReadyWeapon);
		class<Inventory> act = s >= 0 ? (class<Inventory>)("LD" .. RSLDP_Data.Slots[s] .. "EffectActive") : null;
		if (s < 0 || !act || p.CountInv(act) == 0) { p.A_Print("This gun has no legendary power."); return; }
		string sn = RSLDP_Data.Slots[s];
		let lp = RSLDP_LegendaryPickup(Actor.Spawn("RSLDP_LegendaryPickup", p.Vec3Angle(24, p.angle, p.height * 0.5)));
		if (!lp) return;
		lp.SetupKeep(s, RSLDP_Effects.RarityOf(p, s), RSLDP_Effects.EffectOf(p, s));
		lp.vel = p.Vec3Angle(6, p.angle, 3) - p.pos;
		// take the slot's tokens from the player (LegenDoom's drop moves them to the pickup the same way)
		for (let i = p.Inv; i; )
		{
			let nx = i.Inv;
			string cn = i.GetClassName();
			string pa = "LD" .. sn .. "EffectActive", pl = "LD" .. sn .. "Legendary", pe = "LD" .. sn .. "Effect_";
			if (cn ~== pa || cn.Left(pl.Length()) ~== pl || cn.Left(pe.Length()) ~== pe)
			{
				p.RemoveInventory(i); i.Destroy();
			}
			i = nx;
		}
		curEffect[pn] = ""; curRarity[pn] = -1;
		if (Debug()) Console.Printf("RSLDP drop: player %d dropped the %s legendary %s", pn, sn, lp.effect);
	}

	// ---------------------------------------------------------------- HUD
	override void RenderOverlay(RenderEvent e)
	{
		cvar on = cvar.FindCvar("rsldp_screen_name");	// off by default (owner 11-05 00:54); Wheel's card still names the gun
		if (!on || !on.GetBool()) return;
		int pn = consoleplayer;
		string eff = curEffect[pn];
		if (eff == "" || automapactive) return;
		int r = curRarity[pn];
		let w = players[pn].ReadyWeapon;
		string title = StringTable.Localize("$LD_FX_TITLE_" .. eff);
		if (title.Left(1) == "L" && title.IndexOf("_FX_") >= 0) title = eff;
		string line = String.Format("%s %s", title, w ? w.GetTag() : "");
		int col = r >= 0 ? RSLDP_Data.RarityColor[r] : Font.CR_WHITE;
		int vw = 320, vh = 200;
		int x = (vw - smallfont.StringWidth(line)) / 2;
		Screen.DrawText(smallfont, col, x, 3, line, DTA_VirtualWidth, vw, DTA_VirtualHeight, vh, DTA_KeepRatio, true);
	}
}
