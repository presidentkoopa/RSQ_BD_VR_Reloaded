// LD mode, G8 pickup passives (Agent B, 2026-11-06): LegenDoom 3.0's item rules on BD22's own items.
//
// LegenDoom applies these rules in its item scripts (source/LEGENDITM.acs, LD_<Item>Activate, run from its own
// pickups). In LD mode BD22's items are restored (LegenDoom's 56 replacements undone), so those scripts never run:
// this file applies the same rules when a BD22 item is picked up. The numbers are LegenDoom's
// (numbers_g8.zs, generated from ldl_patch/tools/numbers/g8.rules: every number names its LegenDoom file:line).
// Where LegenDoom gives one of its OWN invisible items (powerup givers, LDActionHeroEffectGiver, LDScannerActive,
// LDAugmented*Giver, LDGhostlyProtection, LDIntimidatingDamage), that item is given: LegenDoom's numbers, no sound.
// Where LegenDoom gives a vanilla item (HealthBonus, ArmorBonus, BlueArmor, Clip...), BD22's own item stands in.
//
// How a pickup is seen (engine 4.14 / QZD 17.3, zscript/actors/inventory):
// - Ammo, BackpackItem, armor, PowerupGiver, CustomInventory: Inventory.TryPickup runs the holder's HandlePickup
//   chain first (inventory.zs:512) -> RSLD_Amp.HandlePickup -> RSLD_Handler.Pickup -> OnPickup of every owned effect.
//   A CustomInventory has already run its Pickup state then (stateprovider.zs CustomInventory.TryPickup).
// - Health (Stimpack2, Medikit2, HealthPlus) and MapRevealer (Allmap) override TryPickup and never call HandlePickup
//   (health.zs:76, inv_misc.zs:86): they are watched near each player and counted the tic they vanish (Watch()).
// Powerup lengths (Sustained, Ghostly, Intimidating) are measured, not assumed: the player's powerups are snapshot
// every tic and a pickup's gain is the difference on the next tic (PowerDiff()).

class RSLD_BPlr play
{
	Array<Powerup> snapPow;
	Array<int> snapTics;
	int snapTic;
	// pickups to finish on the next tick (the item has been given by then)
	Array<int> pendKind;
	Array<String> pendCls;
	Array<Inventory> pendItem;
	// items that never reach HandlePickup, near this player
	Array<Inventory> near;
	Array<String> nearCls;
	Array<double> nearX, nearY, nearZ;
	int lastHealth;
	int tickTic;
}

// Agent B's per-level state (one thinker): G8 pickups, G1 Convincing once-per-missile, G10 nothing.
class RSLD_BState : Thinker
{
	Array<RSLD_BPlr> plr;
	Inventory lastItem;
	int lastTic, lastPn;
	bool lastRet;
	bool giving;		// our own gives (bonuses, givers): no rules run on them
	bool sharing;		// a share to another player: their own rules run, no re-share (LegenDoom's "shared" arg 1)
	Array<Actor> doneInfl;	// G1 Convincing: missiles that already made their radius give
	Array<String> resCls;	// BD22 reserve ammo of the nine LegenDoom families (Weapon.AmmoType1), and its slot
	Array<int> resSlot;
	bool resBuilt;

	static RSLD_BState Get()
	{
		let it = ThinkerIterator.Create("RSLD_BState", Thinker.STAT_INFO);
		let st = RSLD_BState(it.Next());
		if (!st)
		{
			st = new("RSLD_BState");
			st.ChangeStatNum(Thinker.STAT_INFO);
			st.lastTic = -1;
		}
		return st;
	}

	RSLD_BPlr P(int pn)
	{
		while (plr.Size() <= pn) plr.Push(null);
		if (!plr[pn]) { plr[pn] = new("RSLD_BPlr"); plr[pn].tickTic = -1; }
		return plr[pn];
	}

	void BuildRes()
	{
		if (resBuilt) return;
		resBuilt = true;
		for (int i = 0; i < RSLD_Data.Family.Size(); i++)
		{
			Array<string> f; RSLD_Data.Family[i].Split(f, "|");
			class<Weapon> wc = f[1];
			if (!wc) continue;
			let d = GetDefaultByType(wc);
			if (!d.AmmoType1) continue;
			String n = d.AmmoType1.GetClassName();
			int s = f[0].ToInt();
			bool dup = false;
			for (int k = 0; k < resCls.Size(); k++) if (resCls[k] == n && resSlot[k] == s) dup = true;
			if (!dup) { resCls.Push(n); resSlot.Push(s); }
		}
	}
}

class RSLD_B play
{
	// pending kinds
	const K_POWER = 1;		// a powerup item: diff the powerups next tic (Sustained, Ghostly, Intimidating)
	const K_BERSERK = 2;		// Champion
	const K_SOUL = 3;		// Soulstorm on a soulsphere
	const K_MEGA = 4;		// Soulstorm on a megasphere
	const K_BACKPACK = 5;		// backpack extras after the backpack raised the maximums
	const K_ARMOR = 6;		// Armorer share if the armor was taken
	const K_SHAREPOW = 7;		// Shaman share of a powerup item

	// LegenDoom's ammo kinds (its four ammo types) by the slots that use them: Clip (pistol, chaingun),
	// Shell (shotgun, SSG), RocketAmmo (rocket launcher), Cell (plasma rifle, BFG)
	// (functions, not static const arrays: a static function cannot read a static array on QZD 17.3)
	static string KindKey(int k) { switch (k) { case 0: return "clip"; case 1: return "shell"; case 2: return "rocket"; } return "cell"; }
	static string KindBox(int k) { switch (k) { case 0: return "clipbox"; case 1: return "shellbox"; case 2: return "rocketbox"; } return "cellpack"; }
	static int SlotKind(int s) { switch (s) { case 2: case 5: return 0; case 3: case 4: return 1; case 6: return 2; case 7: case 8: return 3; } return -1; }

	static double N(string eff, string key) { return RSLD.Num(eff, key); }

	static void Log(PlayerPawn p, string eff, string msg)
	{
		if (RSLD.Debug()) Console.Printf("RSLD %d %s pickup p%d: %s", level.maptime, eff, p ? p.PlayerNumber() : -1, msg);
	}

	static bool IsA(readonly<Actor> a, string cls)
	{
		class<Actor> c = cls;
		return a && c && a is c;
	}

	static bool AnyPlayerHas(string eff)	// LegenDoom's LD_AnyPlayerHasEffect (LEGENDFNC.acs:79)
	{
		for (int i = 0; i < MAXPLAYERS; i++)
			if (playeringame[i] && players[i].mo && RSLD.Count(players[i].mo, eff) > 0) return true;
		return false;
	}

	static int OtherPlayers(PlayerPawn p)
	{
		int n = 0;
		for (int i = 0; i < MAXPLAYERS; i++) if (playeringame[i] && players[i].mo && players[i].mo != p) n++;
		return n;
	}

	// give one of LegenDoom's own invisible items n times (each LegenDoom giver is ADDITIVETIME)
	static void GiveLD(RSLD_BState st, PlayerPawn p, string cls, int n)
	{
		bool g = st.giving;
		st.giving = true;
		for (int i = 0; i < n; i++) RSLD.Give(p, cls, 1);
		st.giving = g;
	}

	// a powerup for exactly t tics, added to one already running (LegenDoom's givers are +ADDITIVETIME)
	static void GivePower(RSLD_BState st, PlayerPawn p, string cls, int t)
	{
		class<Inventory> c = cls;
		if (!c || t <= 0) return;
		let pw = Powerup(p.FindInventory(c));
		if (pw) { pw.EffectTics += t; return; }
		bool g = st.giving;
		st.giving = true;
		let np = Powerup(Actor.Spawn(c));
		if (np)
		{
			np.EffectTics = t;
			np.bAlwaysPickup = true;
			if (!np.CallTryPickup(p)) np.Destroy();
		}
		st.giving = g;
	}

	// ================================================================ entry points (from every G8 effect)
	static bool OnPickup(PlayerPawn p, Inventory item)
	{
		if (!p || !item) return false;
		let st = RSLD_BState.Get();
		if (st.giving) return false;
		int pn = p.PlayerNumber();
		if (st.lastItem == item && st.lastTic == level.maptime && st.lastPn == pn) return st.lastRet;
		st.lastItem = item; st.lastTic = level.maptime; st.lastPn = pn;
		bool ret = Handle(st, p, item);
		st.lastRet = ret;
		return ret;
	}

	static void Tick(PlayerPawn p)
	{
		if (!p) return;
		let st = RSLD_BState.Get();
		let d = st.P(p.PlayerNumber());
		if (d.tickTic == level.maptime) return;
		d.tickTic = level.maptime;
		Watch(st, p, d);
		Pending(st, p, d);
		Snapshot(p, d);
		d.lastHealth = p.health;
	}

	static bool Handle(RSLD_BState st, PlayerPawn p, Inventory item)
	{
		if (item is "Powerup") return false;		// a bare powerup: ours or LegenDoom's own givers' product
		string cn = item.GetClassName();
		if (cn.Left(2) == "LD" || cn.Left(4) == "RSLD") return false;	// LegenDoom's own items run its own rules
		let d = st.P(p.PlayerNumber());
		// LegenDoom's rules run on its world pickups only. BD22 and BD22 VR also move ammo/armor with GiveInventory
		// (magazine/reserve bookkeeping, fatality armor): those are not pickups and get no rule.
		if (!FromWorld(p, d, item))
		{
			if (RSLD.DebugLevel() > 1) Log(p, "pickup", String.Format("%s x%d not a world pickup: no rule", cn, item.Amount));
			return false;
		}
		if (item is "Ammo") return AmmoRule(st, p, Ammo(item));
		if (item is "BackpackItem") { Pend(d, K_BACKPACK, cn, item); return false; }
		if (item is "BasicArmorPickup") { ArmorRule(st, p, BasicArmorPickup(item)); Pend(d, K_ARMOR, cn, item); return false; }
		if (item is "BasicArmorBonus") { ArmorBonusRule(st, p, BasicArmorBonus(item)); return false; }
		// a powerup giver given by an item's Pickup state (RadSuits -> Radsuit3): diff the powerups next tic. The
		// world item itself (and every CustomInventory without a Use state, which never reaches HandlePickup:
		// stateprovider.zs:572-583) is counted by Watch(), which also runs Champion / Soulstorm / Shaman.
		if (item is "PowerupGiver" || item is "CustomInventory") Pend(d, K_POWER, cn, item);
		return false;
	}

	// the item is a world pickup touched by p, or was given by the Pickup state of a world CustomInventory p is
	// touching now (BD22's Clip1Drop gives Clip1, RadSuits gives Radsuit3): Touch only happens on contact
	static bool FromWorld(PlayerPawn p, RSLD_BPlr d, Inventory item)
	{
		double reach = p.radius + 32 + p.vel.Length();
		if (item.pos != (0, 0, 0) && (p.pos.xy - item.pos.xy).Length() <= reach + item.radius
			&& item.pos.z <= p.pos.z + p.height + 32 && item.pos.z + item.height >= p.pos.z - 32) return true;
		for (int i = 0; i < d.near.Size(); i++)
		{
			let n = d.near[i];
			if (!n || n == item || !(n is "CustomInventory")) continue;
			if ((p.pos.xy - n.pos.xy).Length() <= reach + n.radius && n.pos.z <= p.pos.z + p.height + 32 && n.pos.z + n.height >= p.pos.z - 32) return true;
		}
		return false;
	}

	// a world powerup item was taken (seen by Watch())
	static void PowerItemTaken(RSLD_BState st, PlayerPawn p, RSLD_BPlr d, string cn)
	{
		class<Actor> c = cn;
		let def = c ? GetDefaultByType(c) : null;
		Pend(d, K_POWER, cn, null);
		if (def && IsA(def, "BerserkPack")) Pend(d, K_BERSERK, cn, null);
		if (def && (IsA(def, "LifeSphere") || IsA(def, "LifeSphere_Vox"))) Pend(d, K_SOUL, cn, null);
		if (def && (IsA(def, "EnergySphere") || IsA(def, "EnergySphere_Vox"))) Pend(d, K_MEGA, cn, null);
		// Shaman shares LegenDoom's powerup items (LEGENDITM.acs: berserk, soulsphere, megasphere, computer map, light amp,
		// invulnerability, radsuit, blursphere): BD22's powerup givers and its CustomInventory stand-ins for those
		bool pow = def is "PowerupGiver";
		Array<string> l;
		string list = "BerserkPack|LifeSphere|LifeSphere_Vox|EnergySphere|EnergySphere_Vox|RadSuits|NightVision|SuperBlurSphere|SuperBlurSphere_Vox";
		list.Split(l, "|");
		for (int i = 0; i < l.Size() && !pow; i++) if (IsA(def, l[i])) pow = true;
		if (!st.sharing && pow) Pend(d, K_SHAREPOW, cn, null);
	}

	static void Pend(RSLD_BPlr d, int kind, string cn, Inventory item)
	{
		d.pendKind.Push(kind); d.pendCls.Push(cn); d.pendItem.Push(item);
	}

	// ================================================================ ammo (LD_ClipActivate ... LD_CellPackActivate)
	static int KindOf(RSLD_BState st, class<Ammo> parent)
	{
		st.BuildRes();
		if (!parent) return -1;
		String n = parent.GetClassName();
		for (int k = 0; k < st.resCls.Size(); k++)
			if (st.resCls[k] == n) return SlotKind(st.resSlot[k]);
		return -1;
	}

	static bool SlotUses(RSLD_BState st, int slot, String ammo)
	{
		st.BuildRes();
		for (int k = 0; k < st.resCls.Size(); k++) if (st.resSlot[k] == slot && st.resCls[k] == ammo) return true;
		return false;
	}

	// LegenDoom's Upgrading points for a pickup of `amount` of kind k: the rate of its small or big pickup
	// (clip 38 per 10, clip box 188 per 50, ...: DECORATE consts + LD_<Item>Activate amounts)
	static int UpgradePoints(int k, int amount)
	{
		double sa = N("Upgrading", KindKey(k) .. "_amt"), sp = N("Upgrading", KindKey(k) .. "_pts");
		double ba = N("Upgrading", KindBox(k) .. "_amt"), bp = N("Upgrading", KindBox(k) .. "_pts");
		if (sa <= 0 || ba <= 0) return 0;
		double rate = amount >= ba ? bp / ba : sp / sa;
		return int(amount * rate + 0.5);
	}

	static bool AmmoRule(RSLD_BState st, PlayerPawn p, Ammo item)
	{
		class<Ammo> parent = item.GetParentAmmo();
		if (RSLD.DebugLevel() > 1) Log(p, "ammo", String.Format("%s amount %d at (%.0f %.0f %.0f) dist %.0f dropped %d", item.GetClassName(), item.Amount, item.pos.x, item.pos.y, item.pos.z, p.Distance3D(item), item.bDropped));
		int k = KindOf(st, parent);
		if (k < 0) return false;	// not one of LegenDoom's four ammo kinds (BD22's gas, grenades...): Q14 note
		let owned = p.FindInventory(parent);
		cvar ul = cvar.FindCvar("sv_unlimited_pickup");
		bool full = owned && owned.Amount >= owned.MaxAmount && !(ul && ul.GetBool());
		int base = item.Amount;
		if (full)
		{
			// LegenDoom: a pickup of maxed ammo only feeds Upgrading (Items/Clip.dec NoPickup -> LD_UpgradingUpgrader);
			// it is taken if any Upgrading weapon can still level, else it stays on the floor
			int pts = UpgradePoints(k, base);
			if (RSLD.Count(p, "Upgrading") > 0 && Upgrade(st, p, pts, parent.GetClassName()))
			{
				item.bPickupGood = true;
				return true;
			}
			return false;
		}
		int extra = 0;
		int sc = RSLD.Count(p, "Scrounger");
		if (sc > 0)
		{
			// +20% per copy, ceil (clip 10 -> 2, shell 4 -> 1, rocket 1 -> 1: LEGENDITM.acs:601/671/741)
			double r = N("Scrounger", "clip_add") / max(1.0, N("Scrounger", "clip_base"));
			int add = sc * int(ceil(base * r - 0.0001));
			extra += add;
			Log(p, "Scrounger", String.Format("%s %d +%d (%d copies, +%.0f%% each, ceil)", item.GetClassName(), base, add, sc, r * 100));
		}
		for (int s = 0; s < 9; s++)
		{
			if (!(RSLD.EffectOf(p, s) ~== "Hoarder") || !SlotUses(st, s, parent.GetClassName())) continue;
			// +100% for each Hoarder slot whose gun uses this ammo (LD_ClipActivate: pistol and chaingun slots)
			double hr = N("Hoarder", "clip_add") / max(1.0, N("Scrounger", "clip_base"));
			int add = int(base * hr + 0.5);
			extra += add;
			Log(p, "Hoarder", String.Format("%s %d +%d (slot %s uses %s)", item.GetClassName(), base, add, RSLD_Data.Slots[s], parent.GetClassName()));
		}
		item.Amount = base + extra;
		AmmoTaken(st, p, item.GetClassName(), base);
		// Quartermaster (multiplayer): every other player gets the same pickup, with their own passives
		if (!st.sharing && multiplayer && AnyPlayerHas("Quartermaster")) ShareItem(st, p, item.GetClassName(), base, "Quartermaster");
		else if (RSLD.Count(p, "Quartermaster") > 0) Log(p, "Quartermaster", String.Format("%s: %d other players (shared in multiplayer only)", item.GetClassName(), OtherPlayers(p)));
		return false;
	}

	// ActionHero + Collector: an ammo pickup that is taken (LD_ClipActivate tail)
	static void AmmoTaken(RSLD_BState st, PlayerPawn p, string what, int base)
	{
		int ah = RSLD.Count(p, "ActionHero");
		if (ah > 0)
		{
			int su = RSLD.Count(p, "Sustained");
			let pw = Powerup(p.FindInventory("PowerInfiniteAmmo", true));
			int before = pw ? pw.EffectTics : 0;
			GiveLD(st, p, "LDActionHeroEffectGiver", ah + su);	// 1 s each, additive (UncommonSpecialEffects.dec:4174)
			pw = Powerup(p.FindInventory("PowerInfiniteAmmo", true));
			Log(p, "ActionHero", String.Format("%s: +%d x LDActionHeroEffectGiver (ActionHero %d + Sustained %d): infinite ammo %d -> %d tics", what, ah + su, ah, su, before, pw ? pw.EffectTics : 0));
		}
		int co = RSLD.Count(p, "Collector");
		if (co > 0)
		{
			int h0 = p.health;
			for (int i = 0; i < co; i++) HealthBonusRule(st, p, false);
			Log(p, "Collector", String.Format("%s: %d health bonus(es): health %d -> %d", what, co, h0, p.health));
		}
	}

	// Upgrading meter (LEGNDLIB.acs:217 LD_UpgradingUpgrader): every Upgrading weapon below its max level gets the
	// points; a full meter empties and the level rises. LegenDoom's own level/meter items hold it (their MaxAmounts).
	static bool Upgrade(RSLD_BState st, PlayerPawn p, int pts, string what)
	{
		bool ok = false;
		bool g = st.giving;
		st.giving = true;
		for (int s = 0; s < 9; s++)
		{
			if (!(RSLD.EffectOf(p, s) ~== "Upgrading")) continue;
			class<Inventory> lv = "LD" .. RSLD_Data.Slots[s] .. "UpgradeLevel";
			class<Inventory> mt = "LD" .. RSLD_Data.Slots[s] .. "UpgradeMeter";
			if (!lv || !mt) continue;
			int lvMax = GetDefaultByType(lv).MaxAmount, mtMax = GetDefaultByType(mt).MaxAmount;
			if (p.CountInv(lv) >= lvMax) continue;
			ok = true;
			int m0 = p.CountInv(mt);
			p.GiveInventory(mt, pts);
			if (p.CountInv(mt) >= mtMax)
			{
				p.TakeInventory(mt, p.CountInv(mt));
				p.GiveInventory(lv, 1);
				p.A_Print(StringTable.Localize("$LD_WEP_UPGRADE_MESSAGE_" .. RSLD_Data.Slots[s]));
				p.A_StartSound("Plasma/FullyCharged", CHAN_AUTO, CHANF_OVERLAP);	// scope 4: ours for effects/upgradinglevel
				Log(p, "Upgrading", String.Format("%s: +%d -> %s LEVEL %d/%d (meter %d/%d reset)", what, pts, RSLD_Data.Slots[s], p.CountInv(lv), lvMax, m0 + pts, mtMax));
			}
			else
			{
				p.A_StartSound("Plasma/Beep", CHAN_AUTO, CHANF_OVERLAP);		// scope 4: ours for effects/upgradingmeter
				Log(p, "Upgrading", String.Format("%s: +%d -> %s meter %d -> %d/%d (level %d)", what, pts, RSLD_Data.Slots[s], m0, p.CountInv(mt), mtMax, p.CountInv(lv)));
			}
		}
		st.giving = g;
		return ok;
	}

	// ================================================================ health / armor bonuses (LD_HealthBonusActivate, LD_ArmorBonusActivate)
	static class<Inventory> HealthBonusCls() { let c = RSLD.IC("HealthPlus"); return c ? c : RSLD.IC("HealthBonus"); }
	static class<Inventory> ArmorBonusCls() { let c = RSLD.IC("ArmorShard"); return c ? c : RSLD.IC("ArmorBonus"); }

	static void GiveHealthBonuses(PlayerPawn p, int n)
	{
		let hb = Health(GetDefaultByType(HealthBonusCls()));
		if (n > 0 && hb) p.GiveBody(hb.Amount * n, hb.MaxAmount);	// BD22 HealthPlus: +2 each, up to 300 (Health2.dec)
	}

	static void GiveArmorBonuses(RSLD_BState st, PlayerPawn p, int n)
	{
		bool g = st.giving;
		st.giving = true;
		for (int i = 0; i < n; i++) p.GiveInventory(ArmorBonusCls(), 1);	// BD22 ArmorShard: +2 each, up to 300
		st.giving = g;
	}

	// a health bonus (a picked HealthPlus: baseGiven; Collector / NanoCircuit: not)
	static void HealthBonusRule(RSLD_BState st, PlayerPawn p, bool baseGiven)
	{
		int spi = RSLD.Count(p, "Spiritual");
		int one = int(N("Spiritual", "base"));		// GiveInventory("HealthBonus", 1+Spiritual)
		int n = (baseGiven ? 0 : one) + spi;
		int h0 = p.health;
		GiveHealthBonuses(p, n);
		if (spi > 0 && baseGiven) Log(p, "Spiritual", String.Format("health bonus +%d more (%d copies): health %d -> %d", spi, spi, h0, p.health));
		int su = RSLD.Count(p, "Sustained");
		bool aug = RSLD.Count(p, "Augmented") > 0;
		int ag = int(N("Augmented", "givers"));
		if (aug)
		{
			GiveLD(st, p, "LDAugmentedDamageGiver", ag + su);
			let pw = Powerup(p.FindInventory(RSLD.IC("LDAugmentedDamage"), true));
			Log(p, "Augmented", String.Format("health bonus: %d x LDAugmentedDamageGiver (x1.5 damage): %d tics", ag + su, pw ? pw.EffectTics : 0));
		}
		if (RSLD.Count(p, "Resourceful") > 0)
		{
			int a0 = p.CountInv("BasicArmor");
			GiveArmorBonuses(st, p, one + spi);
			Log(p, "Resourceful", String.Format("health bonus also gives %d armor bonus(es): armor %d -> %d", one + spi, a0, p.CountInv("BasicArmor")));
			if (aug) GiveLD(st, p, "LDAugmentedDamageResistanceGiver", ag + su);
		}
	}

	// an armor bonus being picked up (item: before it is used) or given (item null)
	static void ArmorBonusRule(RSLD_BState st, PlayerPawn p, BasicArmorBonus item)
	{
		int spi = RSLD.Count(p, "Spiritual");
		int one = int(N("Spiritual", "base"));
		if (item)
		{
			if (spi > 0)
			{
				int s0 = item.SaveAmount;
				let dd = BasicArmorBonus(GetDefaultByType((class<Actor>)(item.GetClass())));
				item.SaveAmount += spi * (dd ? dd.SaveAmount : 0);
				Log(p, "Spiritual", String.Format("%s armor %d -> %d (%d more bonus(es))", item.GetClassName(), s0, item.SaveAmount, spi));
			}
		}
		else GiveArmorBonuses(st, p, one + spi);
		int su = RSLD.Count(p, "Sustained");
		bool aug = RSLD.Count(p, "Augmented") > 0;
		int ag = int(N("Augmented", "givers"));
		if (aug)
		{
			GiveLD(st, p, "LDAugmentedDamageResistanceGiver", ag + su);
			let pw = Powerup(p.FindInventory(RSLD.IC("LDAugmentedDamageResistance"), true));
			Log(p, "Augmented", String.Format("armor bonus: %d x LDAugmentedDamageResistanceGiver (x0.5 damage taken): %d tics", ag + su, pw ? pw.EffectTics : 0));
		}
		if (RSLD.Count(p, "Resourceful") > 0)
		{
			int h0 = p.health;
			GiveHealthBonuses(p, one + spi);
			Log(p, "Resourceful", String.Format("armor bonus also gives %d health bonus(es): health %d -> %d", one + spi, h0, p.health));
			if (aug) GiveLD(st, p, "LDAugmentedDamageGiver", ag + su);
		}
	}

	// ================================================================ armor (LD_GreenArmorActivate / LD_BlueArmorActivate)
	static void ArmorRule(RSLD_BState st, PlayerPawn p, BasicArmorPickup item)
	{
		// Hardened: green armor counts as blue (BD22: LightArmor takes HeavyArmor's numbers, icon and sound)
		if (RSLD.Count(p, "Hardened") > 0 && IsA(item, "LightArmor"))
		{
			let hc = RSLD.IC("HeavyArmor");
			let hv = hc ? BasicArmorPickup(GetDefaultByType(hc)) : null;
			if (hv)
			{
				int s0 = item.SaveAmount;
				item.SaveAmount = hv.SaveAmount;
				item.SavePercent = hv.SavePercent;
				item.MaxAbsorb = hv.MaxAbsorb;
				item.MaxFullAbsorb = hv.MaxFullAbsorb;
				item.Icon = hv.Icon;
				item.PickupSound = hv.PickupSound;
				Log(p, "Hardened", String.Format("%s counts as HeavyArmor: %d -> %d armor (armor now %d)", item.GetClassName(), s0, item.SaveAmount, p.CountInv("BasicArmor")));
			}
		}
	}

	// ================================================================ the next tick
	static void Pending(RSLD_BState st, PlayerPawn p, RSLD_BPlr d)
	{
		if (d.pendKind.Size() == 0) return;
		bool power = false;
		for (int i = 0; i < d.pendKind.Size(); i++) if (d.pendKind[i] == K_POWER) power = true;
		if (power) PowerDiff(st, p, d);
		for (int i = 0; i < d.pendKind.Size(); i++)
		{
			int k = d.pendKind[i];
			string cn = d.pendCls[i];
			let item = d.pendItem[i];
			bool taken = !item || !item.bSpecial || item.Owner == p;
			if (k == K_BERSERK) Champion(st, p, cn);
			else if (k == K_SOUL) SoulstormSoul(st, p, cn);
			else if (k == K_MEGA) SoulstormMega(st, p, cn);
			else if (k == K_BACKPACK) Backpack(st, p, cn);
			else if (k == K_ARMOR && taken)
			{
				if (!st.sharing && multiplayer && AnyPlayerHas("Armorer")) ShareItem(st, p, cn, 0, "Armorer");
				else if (RSLD.Count(p, "Armorer") > 0) Log(p, "Armorer", String.Format("%s: %d other players (shared in multiplayer only)", cn, OtherPlayers(p)));
			}
			else if (k == K_SHAREPOW)
			{
				if (multiplayer && AnyPlayerHas("Shaman")) ShareItem(st, p, cn, 0, "Shaman");
				else if (RSLD.Count(p, "Shaman") > 0) Log(p, "Shaman", String.Format("%s: %d other players (shared in multiplayer only)", cn, OtherPlayers(p)));
			}
		}
		d.pendKind.Clear(); d.pendCls.Clear(); d.pendItem.Clear();
	}

	static bool PowerExcluded(Powerup pw)
	{
		string n = pw.GetClassName();
		return n.Left(2) == "LD" || n.Left(4) == "RSLD" || pw is "PowerStrength" || pw.EffectTics >= 0x7000000 || pw.EffectTics < 0;
	}

	static void Snapshot(PlayerPawn p, RSLD_BPlr d)
	{
		d.snapPow.Clear(); d.snapTics.Clear();
		for (let i = p.Inv; i; i = i.Inv)
		{
			let pw = Powerup(i);
			if (pw) { d.snapPow.Push(pw); d.snapTics.Push(pw.EffectTics); }
		}
		d.snapTic = level.maptime;
	}

	// powerups a pickup gave (or lengthened) since the last snapshot: Sustained, then Ghostly / Intimidating
	static void PowerDiff(RSLD_BState st, PlayerPawn p, RSLD_BPlr d)
	{
		int el = level.maptime - d.snapTic;
		int su = RSLD.Count(p, "Sustained");
		double halves = max(1.0, N("Sustained", "halves"));
		bool gh = RSLD.Count(p, "Ghostly") > 0, im = RSLD.Count(p, "Intimidating") > 0;
		Array<Powerup> got; Array<int> gain;
		for (let i = p.Inv; i; i = i.Inv)
		{
			let pw = Powerup(i);
			if (!pw || PowerExcluded(pw)) continue;
			int old = -1;
			for (int k = 0; k < d.snapPow.Size(); k++) if (d.snapPow[k] == pw) old = d.snapTics[k];
			int expect = old < 0 ? 0 : max(0, old - el);
			int g = pw.EffectTics - expect;
			if (g > 3) { got.Push(pw); gain.Push(g); }
		}
		for (int k = 0; k < got.Size(); k++)
		{
			let pw = got[k];
			int g = gain[k];
			if (su > 0)
			{
				// LegenDoom gives item powerups as (2 + Sustained) half-length givers: +1/2 of the item's length per copy
				int add = int(g * su / halves);
				pw.EffectTics += add;
				Log(p, "Sustained", String.Format("%s +%d tics -> +%d more (%d copies): %d tics", pw.GetClassName(), g, add, su, pw.EffectTics));
				g += add;
			}
			if (gh && pw is "PowerInvisibility")
			{
				// Ghostly: LDGhostlyProtection (90% resist, +NORADIUSDMG) for as long as the invisibility (RareSpecialEffects.dec:3780)
				GivePower(st, p, "LDGhostlyProtection", g);
				let gp = Powerup(p.FindInventory(RSLD.IC("LDGhostlyProtection"), true));
				Log(p, "Ghostly", String.Format("%s %d tics -> LDGhostlyProtection %d tics", pw.GetClassName(), g, gp ? gp.EffectTics : 0));
			}
			if (im && pw is "PowerInvulnerable")
			{
				// Intimidating: LDIntimidatingDamage (x1.5) + PowerFrightener for as long as the invulnerability (:3660)
				GivePower(st, p, "LDIntimidatingDamage", g);
				GivePower(st, p, "PowerFrightener", g);
				let a = Powerup(p.FindInventory(RSLD.IC("LDIntimidatingDamage"), true)), b = Powerup(p.FindInventory("PowerFrightener", true));
				Log(p, "Intimidating", String.Format("%s %d tics -> LDIntimidatingDamage %d, PowerFrightener %d tics", pw.GetClassName(), g, a ? a.EffectTics : 0, b ? b.EffectTics : 0));
			}
		}
	}

	// Champion (LD_BerserkActivate): a berserk also gives (2 + Sustained) of each of LegenDoom's five givers
	static void Champion(RSLD_BState st, PlayerPawn p, string cn)
	{
		if (RSLD.Count(p, "Champion") == 0) return;
		int n = int(N("Champion", "givers")) + RSLD.Count(p, "Sustained");
		GiveLD(st, p, "LDLightAmpGiver", n);
		GiveLD(st, p, "LDInvulnerabilitySphereGiver", n);
		GiveLD(st, p, "LDRadsuitGiver", n);
		GiveLD(st, p, "LDBlurSphereGiver", n);
		GiveLD(st, p, "LDArtifactEffectInfiniteAmmoGiver", n);
		if (RSLD.Count(p, "Ghostly") > 0) GiveLD(st, p, "LDGhostlyEffectGiver", n);
		if (RSLD.Count(p, "Intimidating") > 0) GiveLD(st, p, "LDIntimidatingEffect", n);
		Log(p, "Champion", String.Format("%s: %d x LightAmp/Invulnerability/Radsuit/BlurSphere/InfiniteAmmo givers: %s", cn, n, PowerList(p)));
	}

	// Soulstorm on a soulsphere (LD_SoulsphereActivate): it acts as a megasphere (BD22's: HeavyArmor + health to 200)
	static void SoulstormSoul(RSLD_BState st, PlayerPawn p, string cn)
	{
		if (RSLD.Count(p, "Soulstorm") == 0) return;
		int h0 = p.health, a0 = p.CountInv("BasicArmor");
		bool g = st.giving;
		st.giving = true;
		p.GiveInventory(RSLD.IC("HeavyArmor"), 1);
		let sh = RSLD.IC("SoulSphereHealth");
		let shd = sh ? Health(GetDefaultByType(sh)) : null;
		if (shd) p.GiveBody(shd.Amount, shd.MaxAmount);	// BD22's megasphere: A_GiveInventory("SoulsphereHealth") twice (+100, to 200)
		st.giving = g;
		Log(p, "Soulstorm", String.Format("%s acts as a megasphere: health %d -> %d, armor %d -> %d", cn, h0, p.health, a0, p.CountInv("BasicArmor")));
	}

	// Soulstorm on a megasphere (LD_MegasphereActivate): (2 + Sustained) LDInvulnerabilitySphereGiver, + Intimidating
	static void SoulstormMega(RSLD_BState st, PlayerPawn p, string cn)
	{
		if (RSLD.Count(p, "Soulstorm") == 0) return;
		int n = int(N("Soulstorm", "givers")) + RSLD.Count(p, "Sustained");
		GiveLD(st, p, "LDInvulnerabilitySphereGiver", n);
		if (RSLD.Count(p, "Intimidating") > 0) GiveLD(st, p, "LDIntimidatingEffect", n);
		Log(p, "Soulstorm", String.Format("%s: %d x LDInvulnerabilitySphereGiver: %s", cn, n, PowerList(p)));
	}

	// a backpack (LD_BackpackActivate), after BD22's backpack raised the maximums: Scrounger, Hoarder, ActionHero,
	// Collector, and Upgrading's backpack points (always, Items/Backpack.dec)
	static void Backpack(RSLD_BState st, PlayerPawn p, string cn)
	{
		st.BuildRes();
		int sc = RSLD.Count(p, "Scrounger");
		double r = N("Scrounger", "clip_add") / max(1.0, N("Scrounger", "clip_base"));
		string done = "";
		for (int k = 0; k < st.resCls.Size(); k++)
		{
			String n = st.resCls[k];
			bool seen = false;
			for (int j = 0; j < k; j++) if (st.resCls[j] == n) seen = true;
			if (seen) continue;
			let am = Ammo(p.FindInventory(RSLD.IC(n)));
			if (!am) continue;
			int ba = am.BackpackAmount;
			int add = sc * int(ceil(ba * r - 0.0001));
			for (int s = 0; s < 9; s++) if (RSLD.EffectOf(p, s) ~== "Hoarder" && SlotUses(st, s, n)) add += ba;
			if (add <= 0) continue;
			int a0 = am.Amount;
			RSLD.AddAmmo(am, add);
			done = done .. String.Format(" %s %d->%d", n, a0, am.Amount);
		}
		if (done != "") Log(p, sc > 0 ? "Scrounger" : "Hoarder", cn .. ":" .. done);
		AmmoTaken(st, p, cn, 0);
		if (RSLD.Count(p, "Upgrading") > 0) Upgrade(st, p, int(N("Upgrading", "backpack_pts")), cn);
		if (!st.sharing && multiplayer && (AnyPlayerHas("Shaman") || AnyPlayerHas("Quartermaster"))) ShareItem(st, p, cn, 0, "Quartermaster");
		else if (RSLD.Count(p, "Quartermaster") + RSLD.Count(p, "Shaman") > 0) Log(p, "Quartermaster", String.Format("%s: %d other players (shared in multiplayer only)", cn, OtherPlayers(p)));
	}

	// Quartermaster / Armorer / Medic / Shaman: every other player gets the same BD22 item, with their own passives
	// (LegenDoom's LD_<Item>_Shared gives LD_<Item>_Shared2 to players 1-8; the picker already has it)
	static void ShareItem(RSLD_BState st, PlayerPawn p, string cls, int amount, string eff)
	{
		class<Inventory> c = cls;
		if (!c) return;
		bool sh = st.sharing;
		st.sharing = true;
		int n = 0;
		for (int i = 0; i < MAXPLAYERS; i++)
		{
			if (!playeringame[i] || !players[i].mo || players[i].mo == p) continue;
			let o = players[i].mo;
			let it = Inventory(Actor.Spawn(c, o.pos));	// at the receiver: a pickup there (FromWorld), with its own passives
			if (!it) continue;
			it.ClearCounters();
			if (amount > 0) it.Amount = amount;
			int h0 = o.health;
			bool isHealth = it is "Health";
			if (it.CallTryPickup(o)) n++; else { it.Destroy(); continue; }
			if (isHealth && o.health > h0) HealthTaken(st, o, cls);	// Medic: the receiver's own Survivor
		}
		st.sharing = sh;
		Log(p, eff, String.Format("%s shared with %d other player(s)", cls, n));
	}

	// ================================================================ items with no HandlePickup (watched)
	static bool Watched(Inventory it)
	{
		return it is "MapRevealer" || it is "CustomInventory" || it is "PowerupGiver"
			|| IsA(it, "HealthPlus") || IsA(it, "Stimpack2") || IsA(it, "Medikit2");
	}

	static void Watch(RSLD_BState st, PlayerPawn p, RSLD_BPlr d)
	{
		// the items seen last tic that are gone or taken now, touched by this player
		for (int i = 0; i < d.near.Size(); i++)
		{
			let it = d.near[i];
			if (it && it.bSpecial && !it.Owner) continue;
			Vector3 at = (d.nearX[i], d.nearY[i], d.nearZ[i]);
			if (it) at = it.pos;
			double reach = p.radius + 24 + p.vel.Length() + 16;
			if ((p.pos.xy - at.xy).Length() > reach || at.z > p.pos.z + p.height + 8 || at.z + 24 < p.pos.z - 8) continue;
			string cn = d.nearCls[i];
			class<Actor> c = cn;
			let di = c ? Inventory(GetDefaultByType(c)) : null;
			if (!di) continue;
			if (di is "Health" && p.health <= d.lastHealth && !di.bAlwaysPickup) continue;	// not ours: the health did not rise
			if (di is "MapRevealer") MapTaken(st, p, cn);
			else if (di is "Health") HealthTaken(st, p, cn);
			else PowerItemTaken(st, p, d, cn);
		}
		d.near.Clear(); d.nearCls.Clear(); d.nearX.Clear(); d.nearY.Clear(); d.nearZ.Clear();
		let bi = BlockThingsIterator.Create(p, 128);
		while (bi.Next())
		{
			let it = Inventory(bi.thing);
			if (!it || !it.bSpecial || it.Owner || !Watched(it)) continue;
			d.near.Push(it); d.nearCls.Push(it.GetClassName());
			d.nearX.Push(it.pos.x); d.nearY.Push(it.pos.y); d.nearZ.Push(it.pos.z);
		}
	}

	// a health item was taken (LD_StimpackActivate / LD_MedikitActivate / LD_HealthBonusActivate)
	static void HealthTaken(RSLD_BState st, PlayerPawn p, string cn)
	{
		class<Actor> c = cn;
		if (!c) return;
		let def = Health(GetDefaultByType(c));
		let hp = RSLD.IC("HealthPlus");
		if (hp && def is hp) { HealthBonusRule(st, p, true); return; }
		if (!def) return;
		int sv = RSLD.Count(p, "Survivor");
		if (sv > 0)
		{
			// Survivor: (1 + Survivor) heals of the item, each up to max health (LD_Stimpack_Health HealThing(10, 0))
			int h0 = p.health;
			p.GiveBody(def.Amount * sv, def.MaxAmount);
			Log(p, "Survivor", String.Format("%s +%d x %d more (%d copies): health %d -> %d", cn, def.Amount, sv, sv, h0, p.health));
		}
		if (!st.sharing && multiplayer && AnyPlayerHas("Medic")) ShareItem(st, p, cn, 0, "Medic");
		else if (RSLD.Count(p, "Medic") > 0) Log(p, "Medic", String.Format("%s: %d other players (shared in multiplayer only)", cn, OtherPlayers(p)));
	}

	// a computer map was taken (LD_AllMapActivate): Scanner gives LegenDoom's LDScannerActive (PowerScanner)
	static void MapTaken(RSLD_BState st, PlayerPawn p, string cn)
	{
		if (RSLD.Count(p, "Scanner") > 0)
		{
			GiveLD(st, p, "LDScannerActive", 1);
			Log(p, "Scanner", String.Format("%s: LDScannerActive given: PowerScanner %s", cn, p.FindInventory("PowerScanner", true) ? "on" : "MISSING"));
		}
		if (!st.sharing && multiplayer && AnyPlayerHas("Shaman")) ShareItem(st, p, cn, 0, "Shaman");
		else if (RSLD.Count(p, "Shaman") > 0) Log(p, "Shaman", String.Format("%s: %d other players (shared in multiplayer only)", cn, OtherPlayers(p)));
	}

	static string PowerList(PlayerPawn p)
	{
		string s = "";
		for (let i = p.Inv; i; i = i.Inv)
		{
			let pw = Powerup(i);
			if (pw) s = s .. String.Format("%s%s %d", s == "" ? "" : ", ", pw.GetClassName(), pw.EffectTics);
		}
		return s;
	}
}
