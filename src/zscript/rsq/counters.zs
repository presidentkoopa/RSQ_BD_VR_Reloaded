// counters.zs (1.97) -- magazine COUNTERS for guns Brutal Doom never reloads (MG42 belt drum,
// Flamethrower2 canister, Unmaker skull). BD22's firing and ammo are untouched: the counter
// mirrors the reserve going down shot by shot, and when it is empty the gun's Reload runs
// (actors/Weapons/*.dec, "posefix rsr"). The real VR reload (vreload.zs) swaps the part; on
// the seat the counter takes the reserve's count up to its capacity. Idle unless VR reloading
// is on (RSR.WantsHands), so with it off the guns are Brutal Doom's exactly.

class RSQ_Counters : EventHandler
{
	static const Name GUN[] = { 'MG42', 'Flamethrower2', 'IncendiaryLauncher', 'Machinegun', 'Unmaker', 'Devastator', 'NukeLauncher', 'HellishMissileLauncher', 'Minigun' };
	static const Name MAG[] = { 'RSQ_Mag_MG42', 'RSQ_Mag_Flamethrower2', 'RSQ_Mag_IncendiaryLauncher', 'RSQ_Mag_Machinegun', 'RSQ_Mag_Unmaker', 'RSQ_Mag_Devastator', 'RSQ_Mag_NukeLauncher', 'RSQ_Mag_HellishMissileLauncher', 'RSQ_Mag_Minigun' };
	static const Name RES[] = { 'Clip2', 'Gas', 'AmmoM202', 'Clip2', 'SoulAmmo', 'DevastatorAmmo', 'Nuke', 'MiniHellRocketAmmo', 'RSQ_MinigunAmmo' };	// 2.0 (owner 2026-10-28): the Minigun's own pool (Minigun.dec)
	static const int CAP[] = { 100, 100, 6, 100, 200, 50, 1, 6, 200 };
	// r6 (owner item 13, 2026-10-27): Flamethrower 100, Machinegun 100, Unmaker 200, chaingun (Minigun) 200, and
	// those four are REAL magazines (RealTick), not counters: a counter is a share of the reserve, so a
	// 200 box over Clip2's 200 could never run dry before the reserve did and never asked for a reload.
	// r5 lane rev-unmaker (owner 2026-10-27 20:47, "on top": the loaded rounds do not count toward the max carry):
	// all nine are REAL magazines now. A counter was a share of the reserve, so its loaded rounds ate the carry.
	static const int REAL[] = { 1, 1, 1, 1, 1, 1, 1, 1, 1 };
	// rounds of the magazine lent into the reserve item, so BD22's own fire code (A_JumpIfNoAmmo, DepleteAmmo)
	// finds ammo to spend. At most LEND; the reserve the HUD shows is the pouch plus these.
	const LEND = 10;
	int lastRes[MAXPLAYERS][9];
	bool inited[MAXPLAYERS][9];

	override void WorldTick()
	{
		for (int pn = 0; pn < MAXPLAYERS; pn++)
		{
			if (!playeringame[pn]) continue;
			PlayerPawn mo = players[pn].mo;
			if (!mo) continue;
			M202Carry(mo);
			heldRes = null; heldBonus = 0;
			let w = players[pn].ReadyWeapon;
			for (int g = 0; g < GUN.Size(); g++)
			{
				class<Inventory> mag = MAG[g]; class<Inventory> res = RES[g];
				class<Inventory> empty = "RSQ_Empty_" .. GUN[g]; class<Inventory> fill = "RSQ_Fill_" .. GUN[g];
				class<Inventory> nomag = "RSQ_NoMag_" .. GUN[g];
				if (!mag || !res || !empty || !fill || !nomag) continue;
				bool held = w && w.GetClassName() == GUN[g];
				if (REAL[g] != 0)
				{
					RealTick(mo, pn, g, mag, res, empty, fill, nomag, held);
					continue;
				}
				int r = mo.CountInv(res);
				if (!held || !RSR_ReloadHandler.WantsHands(mo) || !NonStdOn(mo))
				{
					mo.TakeInventory(empty, 1);
					// 1.99x "Reload Non-Standard Guns" off: no magazine left out of the gun either
					// (a reload switched off half way), and the counter starts again from the
					// reserve when it is switched back on
					if (held && !NonStdOn(mo))
					{
						mo.TakeInventory(nomag, 1);
						inited[pn][g] = false;
					}
					lastRes[pn][g] = r;
					continue;
				}
				if (!inited[pn][g])
				{
					inited[pn][g] = true;
					SetCount(mo, mag, min(CAP[g], r));
					mo.TakeInventory(nomag, 1);
				}
				int d = lastRes[pn][g] - r;
				if (d > 0)
					SetCount(mo, mag, max(0, mo.CountInv(mag) - d));
				if (mo.CountInv(fill) > 0)
				{
					mo.TakeInventory(fill, 1);
					SetCount(mo, mag, min(CAP[g], r));
					mo.TakeInventory(nomag, 1);
				}
				bool e = mo.CountInv(mag) <= 0 && r > 0;
				if (e) mo.GiveInventory(empty, 1); else mo.TakeInventory(empty, 1);
				lastRes[pn][g] = r;
			}
			// r5 lane rev-unmaker: every gun's "reserve last tic" is read AFTER all nine ran. Guns share a reserve (Clip2:
			// MG42, Machinegun; the Minigun has its own since 2.0), and one gun handing its lent rounds back must not read as another one firing
			// (seen on the rig: MG42 drawn 100 -> 90 the tic after the Minigun was put away).
			for (int g = 0; g < GUN.Size(); g++)
			{
				class<Inventory> rc = RES[g];
				if (rc)
					lastRes[pn][g] = mo.CountInv(rc);
			}
			CapPass(mo);
			Hud(mo);
		}
	}

	// r5 lane rev-unmaker (owner 20:47, "on top"): the max carry is the reserve's alone. A REAL gun lends up to LEND
	// rounds of its magazine into the reserve item (BD22's fire code needs to find them there), so while it is held
	// that item's cap is raised by exactly the lent rounds: a pickup still fills the pouch to its cap, never less.
	// Base cap: BD22's MaxAmount, or its BackpackMaxAmount with a backpack, AmmoM202 48 (M202Carry). Every other
	// reserve of the nine guns is put back to its base the same tic.
	class<Inventory> heldRes;
	int heldBonus;
	static int CapBase(PlayerPawn mo, Inventory am)
	{
		let a = Ammo(am);
		if (!a)
			return am.MaxAmount;
		int b = a.Default.MaxAmount;
		if (mo.FindInventory('BackpackItem', true))
			b = max(b, a.BackpackMaxAmount);
		if (a.GetClassName() == 'AmmoM202')
			b = max(b, M202_CARRY);
		// 2.0 (owner, 2026-10-28): a full magazine plus two more magazines' worth in reserve for the guns whose
		// magazine was the whole reserve. Magazines from CAP[]: NukeLauncher 1 -> Nuke 2 (BD22 gives Nuke no backpack
		// bonus, 1/1, so the backpack still adds nothing: 2 either way). IncendiaryLauncher 6 is covered by the 48 above.
		// The Minigun has its OWN pool now (RSQ_MinigunAmmo, Minigun.dec: 400 / 800 by its own MaxAmount and
		// BackpackMaxAmount), so BD22's Clip2 (Rifle, Sniper, MG42, Machinegun) is back at BD22's 200 / 400 (owner
		// 2026-10-28 05:0x: the earlier shared Clip2 400 / 800 is reverted). The loaded magazine stays ON TOP (RealTick).
		if (a.GetClassName() == 'Nuke')
			b = max(b, NUKE_CARRY);
		return b;
	}
	void CapPass(PlayerPawn mo)
	{
		for (int g = 0; g < RES.Size(); g++)
		{
			class<Inventory> rc = RES[g];
			let am = rc ? mo.FindInventory(rc) : null;
			if (!am || (heldRes && rc == heldRes))
				continue;
			int b = CapBase(mo, am);
			if (am.MaxAmount != b)
				am.MaxAmount = b;
		}
	}

	// r5 lane rev-unmaker (owner 20:47): the HUD's ammo (SBARINFO.rsq). Magazine + Reserve (rsq_hud_ammo 0, default) or
	// Reserve Only (1). The magazine: a REAL gun's RSQ_Mag_<gun> while its magazine is live, else the gun's AmmoType2
	// when it has one; the reserve: the gun's AmmoType1 minus the rounds lent from the magazine. A dual gun in the off
	// hand (RSQ_Dual copy) shows its own magazine too (its AmmoType2; the reserve is shared).
	int, int GunAmmo(PlayerPawn mo, Weapon w)
	{
		if (!w)
			return -1, 0;
		int resv = w.Ammo1 ? w.Ammo1.Amount : 0;
		Name n = w.GetClassName();	// (ZScript names are case-insensitive: a local "res" would hide RES[])
		for (int g = 0; g < GUN.Size(); g++)
		{
			if (n != GUN[g])
				continue;
			class<Inventory> mag = MAG[g]; class<Inventory> lent = "RSQ_Lent_" .. GUN[g]; class<Inventory> rc = RES[g];
			if (!mag || !lent || !rc || !RSR_ReloadHandler.WantsHands(mo) || !NonStdOn(mo))
				return -1, resv;
			return mo.CountInv(mag), max(0, mo.CountInv(rc) - mo.CountInv(lent));
		}
		if (w.Ammo2 && w.Ammo2 != w.Ammo1)
			return w.Ammo2.Amount, resv;
		return -1, resv;
	}
	// `netevent rsq_ontop` (test and debug): the held gun's reserve item against its cap, its magazine, the lent rounds
	// and the HUD's items
	override void NetworkProcess(ConsoleEvent e)
	{
		if (e.Name != "rsq_ontop" || e.Player < 0 || !players[e.Player].mo)
			return;
		let mo = players[e.Player].mo;
		let w = mo.player.ReadyWeapon;
		if (!w)
			return;
		let a1 = w.Ammo1;
		int m, r;
		[m, r] = GunAmmo(mo, w);
		String lentS = "";
		class<Inventory> lc = "RSQ_Lent_" .. w.GetClassName();
		if (lc)
			lentS = String.Format(", lent %d", mo.CountInv(lc));
		int world = 0;		// that reserve's pickups lying within 256 units (a refused pickup stays)
		if (a1)
		{
			let it = BlockThingsIterator.Create(mo, 256);
			while (it.Next())
				if (it.thing && it.thing.GetClass() == a1.GetClass() && !Inventory(it.thing).Owner)
					world++;
		}
		Console.Printf("RSQ ontop t%d %s: reserve item %s %d / cap %d%s; magazine %d; pouch %d; %d %s pickups within 256; HUD: mag %d (shown %d), reserve %d; off-hand mag %d (shown %d); rsq_hud_ammo %d",
			Level.maptime, w.GetClassName(), a1 ? a1.GetClassName() : 'None', a1 ? a1.Amount : 0, a1 ? a1.MaxAmount : 0, lentS, m, r,
			world, a1 ? a1.GetClassName() : 'None',
			mo.CountInv('RSQ_HudMag'), mo.CountInv('RSQ_HudHasMag'), mo.CountInv('RSQ_HudRes'), mo.CountInv('RSQ_HudMagOff'),
			mo.CountInv('RSQ_HudHasMagOff'), RSQ.PlayerInt(mo, 'rsq_hud_ammo', 0));
	}

	void Hud(PlayerPawn mo)
	{
		let p = mo.player;
		bool magMode = RSQ.PlayerInt(mo, 'rsq_hud_ammo', 0) == 0;
		int m, r;
		[m, r] = GunAmmo(mo, p.ReadyWeapon);
		// 2.0.4s (owner 11-12 21:36, "0 axes but still an axe in hand"): the main hand with nothing to count (its fist) read
		// "0" here whatever the off hand held -- the off hand's axe too. Then the number is the off hand's count.
		if ((!p.ReadyWeapon || !p.ReadyWeapon.Ammo1) && p.OffhandWeapon && p.OffhandWeapon.Ammo1)
		{
			int m2;
			[m2, r] = GunAmmo(mo, p.OffhandWeapon);
		}
		SetCount(mo, 'RSQ_HudRes', r);
		SetCount(mo, 'RSQ_HudMag', max(m, 0));
		SetCount(mo, 'RSQ_HudHasMag', magMode && m >= 0 ? 1 : 0);
		int mo2 = -1, r2;
		if (RSQ_Dual.IsCopy(p.OffhandWeapon))
			[mo2, r2] = GunAmmo(mo, p.OffhandWeapon);
		SetCount(mo, 'RSQ_HudMagOff', max(mo2, 0));
		SetCount(mo, 'RSQ_HudHasMagOff', magMode && mo2 >= 0 ? 1 : 0);
	}

	// r6: a REAL magazine. M = RSQ_Mag_<gun> (rounds in the gun), P = the pouch (BD22's reserve item minus the
	// rounds lent to it), L = RSQ_Lent_<gun> (inventory, so it survives a map change and a save). BD22 fires as
	// it always did and takes its ammo from the reserve item; each round it took is charged to the magazine and
	// what the lent rounds did not cover is given back to the pouch. Seated (RSQ_Fill): min(CAP - M, P) moves
	// from the pouch into the magazine. Out (RSQ_NoMag): nothing is lent, so the gun cannot fire, and its
	// rounds stay in the magazine for the top-up. Not held / option off / not VR: the lent rounds are taken
	// back and the magazine keeps its rounds, so another gun on the same ammo never spends them.
	void RealTick(PlayerPawn mo, int pn, int g, class<Inventory> mag, class<Inventory> res, class<Inventory> empty,
		class<Inventory> fill, class<Inventory> nomag, bool held)
	{
		class<Inventory> lent = "RSQ_Lent_" .. GUN[g];
		class<Inventory> pouchTok = "RSQ_Pouch_" .. GUN[g];	// the gun's Reload starts only with rounds in the pouch
		if (!lent || !pouchTok)
			return;
		int L = mo.CountInv(lent);
		int r = mo.CountInv(res);
		bool on = held && RSR_ReloadHandler.WantsHands(mo) && NonStdOn(mo);
		if (!on)
		{
			mo.TakeInventory(empty, 1);
			if (L > 0)
			{
				mo.TakeInventory(res, min(L, r));
				mo.TakeInventory(lent, L);
			}
			if (held)
			{
				// VR reloading off for this gun (option off, or not in VR): Brutal Doom's gun, so the rounds in
				// the magazine go back to the reserve, as far as it holds them (the rest wait in the magazine)
				int inMag = mo.CountInv(mag);
				if (inMag > 0)
				{
					int before = mo.CountInv(res);
					mo.GiveInventory(res, inMag);
					SetCount(mo, mag, inMag - (mo.CountInv(res) - before));
				}
				mo.TakeInventory(nomag, 1);
				inited[pn][g] = false;
			}
			mo.TakeInventory(pouchTok, 1);
			lastRes[pn][g] = mo.CountInv(res);
			return;
		}
		int M = mo.CountInv(mag);
		int M0 = M;
		int d = lastRes[pn][g] - r;
		if (inited[pn][g] && d > 0)
		{
			// (ZScript names are case-insensitive: a local "m" would be "M")
			int fromMag = min(d, M), fromLent = min(d, L);
			M -= fromMag;
			L -= fromLent;
			if (fromMag > fromLent)
				mo.GiveInventory(res, fromMag - fromLent);	// BD22's code took it from the pouch, but it was a magazine round
		}
		bool top = !inited[pn][g] || mo.CountInv(fill) > 0;
		inited[pn][g] = true;
		if (top)
		{
			mo.TakeInventory(fill, 1);
			mo.TakeInventory(nomag, 1);
			int p = mo.CountInv(res) - L;
			int n = clamp(min(CAP[g] - M, p), 0, CAP[g]);
			mo.TakeInventory(res, n);
			M += n;
			if (RSR.Debug(mo.player))
				Console.Printf("rsq t%d %s: RELOAD magazine %d -> %d, %d from the pouch, pouch %d -> %d", level.maptime, GUN[g], M - n, M, n, p, p - n);
		}
		bool magOut = mo.CountInv(nomag) > 0;
		int want = magOut ? 0 : min(M, LEND);
		let resItem = mo.FindInventory(res);
		if (resItem)
		{
			// r5 "on top": the cap is the pouch's; room for the lent rounds on top of it (CapPass leaves this one alone)
			resItem.MaxAmount = CapBase(mo, resItem) + max(want, L);
			heldRes = res;
		}
		if (L > want)
		{
			mo.TakeInventory(res, min(L - want, mo.CountInv(res)));
			L = want;
		}
		else if (L < want)
		{
			int b = mo.CountInv(res);
			mo.GiveInventory(res, want - L);
			L += mo.CountInv(res) - b;
		}
		SetCount(mo, mag, M);
		SetCount(mo, lent, L);
		if (resItem)
			resItem.MaxAmount = CapBase(mo, resItem) + L;
		int pouch = mo.CountInv(res) - L;
		bool e = magOut || (M <= 0 && pouch > 0);
		if (e) mo.GiveInventory(empty, 1); else mo.TakeInventory(empty, 1);
		if (pouch > 0) mo.GiveInventory(pouchTok, 1); else mo.TakeInventory(pouchTok, 1);
		if (M != M0 && RSR.Debug(mo.player))
			Console.Printf("rsq t%d %s: mag %d pouch %d lent %d%s", level.maptime, GUN[g], M, pouch, L, e ? " EMPTY" : "");
		lastRes[pn][g] = mo.CountInv(res);
	}

	// 1.99x (owner): "Reload Non-Standard Guns" (rsq_reload_nonstd). Non-standard = the guns in GUN[]:
	// Brutal Doom gives them no reload (parsed from brutal22test6: MG42, MiniGun, IncendiaryLauncher,
	// Unmaker, Devastator, NukeLauncher, HellishMissileLauncher have no Reload state; Flamethrower2's
	// "Reload" is only its dry-ready loop; the BD21 Machinegun's reloads only its grenade). Off: these
	// guns are Brutal Doom's -- no counter, no empty guard, and RSR_Start refuses them (vreload.zs).
	static bool IsNonStd(Weapon w)
	{
		if (!w)
			return false;
		// the same nine as GUN[] (a static function cannot read the handler's static array on 17.3)
		Name n = w.GetClassName();
		return n == 'MG42' || n == 'Flamethrower2' || n == 'IncendiaryLauncher' || n == 'Machinegun' || n == 'Unmaker'
			|| n == 'Devastator' || n == 'NukeLauncher' || n == 'HellishMissileLauncher' || n == 'Minigun';
	}

	// 1.99x (owner, 2026-10-26): "a player can carry 48 incendiary rockets". BD22 declares AmmoM202 with
	// Inventory.MaxAmount 4 and Ammo.BackpackMaxAmount 4 (brutal22test6 actors/Weapons/IncendiaryLauncher.dec),
	// and a pack cannot redefine BD22's actor. But the engine caps a pickup at the OWNED item's MaxAmount
	// (Ammo.HandlePickup), and a backpack only ever raises it (BackpackItem.CreateCopy: MaxAmount <
	// BackpackMaxAmount), so the owned item's field is the whole carry limit. It is set every tic, so it
	// holds after a backpack, a level change and a saved game (MaxAmount is saved; this repairs a save from
	// an older build). Always on, VR reloading or not: it is the carry limit, not the reload.
	// BackpackMaxAmount is LEFT AT BD22's 4 on purpose: BackpackItem.DetachFromOwner drops any ammo whose
	// MaxAmount EQUALS its BackpackMaxAmount back to the default (4) and cuts the rockets to 4, so 48/48
	// would lose 44 rockets whenever a backpack leaves the inventory. With 48/4 a backpack changes nothing,
	// so the carry is 48 with or without one. The cylinder stays 6 (CAP[]).
	const M202_CARRY = 48;
	const NUKE_CARRY = 2;		// 2.0: 2 x NukeLauncher's magazine (1)
	static void M202Carry(PlayerPawn mo)
	{
		let am = Inventory(mo.FindInventory('AmmoM202'));
		if (am && am.MaxAmount < M202_CARRY)
			am.MaxAmount = M202_CARRY;
	}

	static bool NonStdOn(PlayerPawn mo)
	{
		return RSQ.PlayerInt(mo, 'rsq_reload_nonstd', 1) != 0;
	}

	static void SetCount(PlayerPawn mo, class<Inventory> it, int n)
	{
		int c = mo.CountInv(it);
		if (n > c) mo.GiveInventory(it, n - c);
		else if (n < c) mo.TakeInventory(it, c - n);
	}
}

class RSQ_Mag_MG42 : Inventory { Default { Inventory.MaxAmount 100; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_MG42 : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_MG42 : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_MG42 : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Mag_Flamethrower2 : Inventory { Default { Inventory.MaxAmount 100; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_Flamethrower2 : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_Flamethrower2 : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_Flamethrower2 : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Mag_IncendiaryLauncher : Inventory { Default { Inventory.MaxAmount 6; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_IncendiaryLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_IncendiaryLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_IncendiaryLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Mag_Machinegun : Inventory { Default { Inventory.MaxAmount 100; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_Machinegun : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_Machinegun : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_Machinegun : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Mag_Unmaker : Inventory { Default { Inventory.MaxAmount 200; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_Unmaker : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_Unmaker : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_Unmaker : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Mag_Devastator : Inventory { Default { Inventory.MaxAmount 50; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_Devastator : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_Devastator : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_Devastator : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Mag_NukeLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_NukeLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_NukeLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_NukeLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Mag_HellishMissileLauncher : Inventory { Default { Inventory.MaxAmount 6; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_HellishMissileLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_HellishMissileLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_HellishMissileLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Mag_Minigun : Inventory { Default { Inventory.MaxAmount 200; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_NoMag_Minigun : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Empty_Minigun : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Fill_Minigun : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_Flamethrower2 : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_Machinegun : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_Unmaker : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_Minigun : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_Flamethrower2 : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_Machinegun : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_Unmaker : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_Minigun : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_MG42 : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_MG42 : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_IncendiaryLauncher : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_IncendiaryLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_Devastator : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_Devastator : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_NukeLauncher : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_NukeLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Lent_HellishMissileLauncher : Inventory { Default { Inventory.MaxAmount 999; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_Pouch_HellishMissileLauncher : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }

// r5 lane rev-unmaker (owner 20:47): what the HUD shows (SBARINFO.rsq, tools/hud/make_sbarinfo.py), set by RSQ_Counters.Hud
class RSQ_HudMag : Inventory { Default { Inventory.MaxAmount 0x7fffffff; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_HudRes : Inventory { Default { Inventory.MaxAmount 0x7fffffff; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_HudHasMag : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_HudMagOff : Inventory { Default { Inventory.MaxAmount 0x7fffffff; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
class RSQ_HudHasMagOff : Inventory { Default { Inventory.MaxAmount 1; +INVENTORY.UNDROPPABLE; +INVENTORY.UNTOSSABLE; +INVENTORY.QUIET } }
