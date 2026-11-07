// LD mode, G8 pickup passives (Agent B): the 20 effects. Their rules live in ld_g8_rules.zs (RSLD_B): one rules
// pass per pickup applies every owned passive at once, as LegenDoom's item scripts do (LEGENDITM.acs). Round 3 (owner Q9):
// a passive counts only the legendary guns in the player's hands (RSLD.Count, core.zs); Upgrading's meter counts owned.

class RSLD_G8Passive : RSLD_Effect
{
	override void Init() { passive = true; }
	override bool OnPickup(PlayerPawn p, Inventory item, int copies) { return RSLD_B.OnPickup(p, item); }
	override void Owned(PlayerPawn p, int copies) { RSLD_B.Tick(p); }

	// rig probe set-up: what each proof needs (a pickup that can be taken)
	override void OnProbe(RSLD_Shot s)
	{
		let p = s.mo;
		if (!p) return;
		if (name ~== "Survivor" || name ~== "Medic") { p.A_SetHealth(40); Log("probe: health set to 40"); }
		if (name ~== "Spiritual" || name ~== "Resourceful" || name ~== "Augmented" || name ~== "Collector") { p.A_SetHealth(100); Log("probe: health set to 100"); }
	}
}

// the registry instantiates every RSLD_Effect subclass: the base above is not an LD effect name (A logs and skips it)
class RSLD_Fx_ActionHero : RSLD_G8Passive {}
// LegenDoom's sharing passives act when ANY player owns them (LD_AnyPlayerHasEffect, LEGENDFNC.acs:79): in a
// multiplayer game every player's pickups are seen (anyPickup); single player: no other player, nothing to share
class RSLD_G8Share : RSLD_G8Passive
{
	override void Init() { passive = true; anyPickup = multiplayer; }
}
class RSLD_Fx_Armorer : RSLD_G8Share {}
class RSLD_Fx_Augmented : RSLD_G8Passive {}
class RSLD_Fx_Champion : RSLD_G8Passive {}
class RSLD_Fx_Collector : RSLD_G8Passive {}
class RSLD_Fx_Ghostly : RSLD_G8Passive {}
class RSLD_Fx_Hardened : RSLD_G8Passive {}
class RSLD_Fx_Hoarder : RSLD_G8Passive {}
class RSLD_Fx_Intimidating : RSLD_G8Passive {}
class RSLD_Fx_Medic : RSLD_G8Share {}
class RSLD_Fx_Quartermaster : RSLD_G8Share {}
class RSLD_Fx_Resourceful : RSLD_G8Passive {}
class RSLD_Fx_Scanner : RSLD_G8Passive {}
class RSLD_Fx_Scrounger : RSLD_G8Passive {}
class RSLD_Fx_Shaman : RSLD_G8Share {}
class RSLD_Fx_Soulstorm : RSLD_G8Passive {}
class RSLD_Fx_Spiritual : RSLD_G8Passive {}
class RSLD_Fx_Survivor : RSLD_G8Passive {}
class RSLD_Fx_Sustained : RSLD_G8Passive {}

// Upgrading: the meter is a pickup rule (RSLD_B.AmmoRule / Backpack / Upgrade); the levels act on the gun's shots.
// Per level, LegenDoom's damage step on that slot's gun (bullets 5 -> 6 = +20%, plasma ball 5 -> 6 = +20%,
// rocket 20 -> 22 and BFG ball 100 -> 110 = +10%, saw and fists x1.1 = +10%), applied to our gun's damage (R).
// Levels 3-4: a shot is free with chance 32/256, level 5: 64/256 (Shotgun.dec FireUpgradingDamage30/50 A_Jump):
// the round goes back to the magazine (owner Q7). LegenDoom's faster fire cycle at levels 2 and 4 needs the fire-rate
// hook (G5) and is not carried here.
class RSLD_Fx_Upgrading : RSLD_G8Passive
{
	int Level(RSLD_Shot s)
	{
		if (!s.mo || s.slot < 0) return 0;
		return RSLD.Has(s.mo, "LD" .. RSLD_Data.Slots[s.slot] .. "UpgradeLevel");
	}

	static string Bul(int s) { switch (s) { case 2: return "pi"; case 3: return "sg"; case 4: return "ss"; } return "cg"; }

	double Step(int slot)
	{
		if (slot == 0) return Num("fi_mult1") - 1.0;
		if (slot == 1) return Num("cs_mult1") - 1.0;
		if (slot >= 2 && slot <= 5)
		{
			double d0 = Num(Bul(slot) .. "_d0"), d1 = Num(Bul(slot) .. "_d1");
			return d0 > 0 ? (d1 - d0) / d0 : 0;
		}
		string k = slot == 6 ? "rl" : (slot == 7 ? "pr" : "bf");
		double a = Num(k .. "_d1"), b = Num(k .. "_d2");	// level 1 and 2: the step, and level 0 = level 1 - step
		double st = b - a, base = a - st;
		return base > 0 ? st / base : 0;
	}

	override void OnPull(RSLD_Shot s)
	{
		int lv = Level(s);
		int ch = lv >= 5 ? int(Num("free5")) : (lv >= 3 ? int(Num("free34")) : 0);
		s.b1 = ch > 0 && random(0, 255) < ch;
		if (lv > 0) s.Log(String.Format("level %d: damage x%.2f, free shot chance %d/256%s", lv, 1.0 + Step(s.slot) * lv, ch, s.b1 ? ": FREE" : ""));
	}

	override void ModifyDamage(RSLD_Shot s, RSLD_Hit h)
	{
		int lv = Level(s);
		if (lv > 0) h.mult *= 1.0 + Step(s.slot) * lv;
	}

	override void AfterPull(RSLD_Shot s)
	{
		if (s.b1 && s.ammoTaken > 0) s.Refund(s.ammoTaken);
	}

	override void OnProbe(RSLD_Shot s)
	{
		// fill the held gun's reserve so the next pickup of its ammo is a maxed one
		let w = s.weapon;
		if (w && w.Ammo1) { w.Ammo1.Amount = w.Ammo1.MaxAmount; Log(String.Format("probe: %s filled to %d", w.Ammo1.GetClassName(), w.Ammo1.Amount)); }
	}
}
