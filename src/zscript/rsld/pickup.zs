// LD mode: legendary drops (moved in from ldl_patch pickup.zs).
// LegenDoom 3.0 drops LD<Slot>PickupLegendary; its own randomizer (LD<Slot>RandomLegendary, LegenDoom's balance and
// compat checks) rolls the rarity and the effect into the pickup's inventory within two tics. RSLD_Converter waits for
// those tokens, then swaps the LegenDoom sprite pickup for RSLD_LegendaryPickup, which looks like the BD22 VR gun
// (its own spawn sprite, so BD_VoxelPack's voxel when there is one), glows in LegenDoom's rarity effect, carries the
// same tokens, and on touch hands over the BD22 VR gun it shows (unless the player has that gun) plus the tokens.

class RSLD_Converter : Thinker
{
	Inventory src;
	int slot, tics;
	bool dropped;	// the player's own legendary, let go (never suppressed)

	static void Watch(Inventory ldPickup, int slot, bool dropped = false)
	{
		let c = new("RSLD_Converter");
		c.src = ldPickup; c.slot = slot; c.tics = 0; c.dropped = dropped;
	}

	override void Tick()
	{
		if (!src || src.Owner) { Destroy(); return; }
		tics++;
		string s = RSLD_Data.Slots[slot];
		int rarity = -1;
		for (int r = 0; r < 4; r++)
		{
			class<Inventory> rc = "LD" .. s .. "Legendary" .. RSLD_Data.Rarities[r];
			if (rc && src.CountInv(rc) > 0) rarity = r;
		}
		string eff = RSLD_Reroll.EffectOf(src, slot);
		if ((rarity < 0 || eff == "") && tics < 12) return;	// LegenDoom rolls in 1-2 tics
		vector3 at = src.pos, v = src.vel;
		// Bossfights the only source (handler.zs BossfightOnly): a monster's legendary weapon from outside one drops nothing
		if (!dropped && RSLD_Handler.BossfightOnly())
		{
			let hb = RSLD_Handler(EventHandler.Find("RSLD_Handler"));
			int from = hb ? hb.DropFromBossfight(at) : -1;
			if (from == 0)
			{
				if (RSLD.Debug()) Console.Printf("RSLD drop: %s suppressed (not from a Bossfight; LegenDoom + Champions + RSQ Miniboss)", src.GetClassName());
				src.Destroy();
				Destroy();
				return;
			}
			if (RSLD.Debug()) Console.Printf("RSLD drop: %s kept (%s)", src.GetClassName(), from == 1 ? "from a Bossfight" : "no legendary death matched");
		}
		// LegenDoom tossed it from (0,0) + 4 because the monster actor was gone (handler.zs WorldThingDied)
		if (abs(src.pos.x) < 64 && abs(src.pos.y) < 64)
		{
			let h = RSLD_Handler(EventHandler.Find("RSLD_Handler"));
			if (h && h.DeathSpot())
			{
				vector3 d = h.spot;
				if (RSLD.Debug()) Console.Printf("RSLD drop: %s was at the map origin (%.0f,%.0f), moved to the legendary's death spot (%.0f,%.0f)", src.GetClassName(), src.pos.x, src.pos.y, d.x, d.y);
				at = d; v = (frandom(-2, 2), frandom(-2, 2), 4);
			}
		}
		let p = RSLD_LegendaryPickup(Actor.Spawn("RSLD_LegendaryPickup", at));
		if (p)
		{
			p.vel = v; p.angle = src.angle;
			p.Setup(slot, rarity, eff);
			if (RSLD.Debug()) Console.Printf("RSLD drop: %s -> RSLD_LegendaryPickup slot %s rarity %s effect %s", src.GetClassName(), s, rarity >= 0 ? RSLD_Data.Rarities[rarity] : "none", p.effect);
		}
		src.Destroy();
		Destroy();
	}
}

class RSLD_LegendaryPickup : Inventory
{
	int slot, rarity, glow, pickupDelay;
	string effect;
	class<Weapon> look;
	bool landed;

	Default
	{
		Radius 16;
		Height 16;
		Inventory.PickupMessage "";
		+INVENTORY.NEVERRESPAWN
		+DROPPED
		+NOTIMEFREEZE
		+DONTGIB
		Tag "Legendary weapon";
	}

	// effect "" = keep what the source carried; the tokens go into this pickup's own inventory, as LegenDoom's do
	void Setup(int s, int r, string eff, bool keep = false)
	{
		slot = s; rarity = r;
		effect = keep ? eff : RSLD_Reroll.Reroll(s, r, eff);
		string sn = RSLD_Data.Slots[s];
		GiveTok("LD" .. sn .. "EffectActive");
		if (r >= 0) GiveTok("LD" .. sn .. "Legendary" .. RSLD_Data.Rarities[r]);
		if (effect != "") GiveTok("LD" .. sn .. "Effect_" .. effect);
		look = RSLD_Handler.GiveClassFor(s, null);
		if (look)
		{
			let d = GetDefaultByType(look);
			if (d.SpawnState) { sprite = d.SpawnState.sprite; frame = d.SpawnState.frame; }
			scale = d.scale;
		}
		bSPECIAL = pickupDelay <= 0;
	}

	// a legendary the player dropped: kept as it was, and not picked straight back up
	void SetupKeep(int s, int r, string eff)
	{
		pickupDelay = 35;
		Setup(s, r, eff, true);
	}

	void GiveTok(string n)
	{
		class<Inventory> c = n;
		if (!c) return;
		let i = Inventory(Spawn(c));
		if (!i) return;
		i.Amount = 1;
		i.AttachToOwner(self);	// held by the pickup like LegenDoom's +INVENTORY.TRANSFER pickups hold theirs
	}

	override void Tick()
	{
		Super.Tick();
		if (pickupDelay > 0 && --pickupDelay == 0) bSPECIAL = true;
		if (!look || rarity < 0) return;
		// LegenDoom's glow: LDLegendary<Rarity>PickupEffect spawned with this pickup's sprite frame (BaseWeaponPickups.dec)
		if (++glow % 3) return;
		cvar gp = cvar.FindCvar("LD_glowingpickups");
		if (gp && gp.GetInt() == 0) return;
		class<Actor> fx = "LDLegendary" .. RSLD_Data.Rarities[rarity] .. "PickupEffect";
		if (!fx) return;
		// LegenDoom spawns it with A_SpawnItemEx, which gives it the pickup's angle; a voxel (BD_VoxelPack) is drawn turned
		// by its actor's angle, so without the angle the ghost lay at angle 0 across a pickup dropped at any other angle
		// (owner 11-05 00:23: "the ghost voxel is perpendicular with the real pickup voxel")
		let g = Spawn(fx, pos);
		if (g) { g.sprite = sprite; g.frame = frame; g.scale = scale; g.angle = angle; g.pitch = pitch; g.roll = roll; }
	}

	override bool TryPickup(in out Actor toucher)
	{
		if (!toucher || !toucher.player) return false;
		string sn = RSLD_Data.Slots[slot];
		class<Inventory> active = "LD" .. sn .. "EffectActive";
		if (active && toucher.CountInv(active) > 0)
		{
			// LegenDoom: one legendary per weapon; it shows the name and leaves the pickup ($LD_WEP_PICKUP_NAME_FAIL_<slot>)
			class<Inventory> cd = (class<Inventory>)(RSLD.AC("LDWeaponDisplayCooldown"));
			if (!cd || toucher.CountInv(cd) == 0)
			{
				if (cd) toucher.GiveInventory(cd, 1);
				toucher.A_Print(StringTable.Localize("$LD_WEP_PICKUP_NAME_FAIL_" .. sn), 2, "CONFONT");
			}
			return false;
		}
		// the gun it shows, unless the player has that gun already (or its Purist/Dual copy); the power then works on
		// every gun of the slot's family. Owning only a stand-in (the Rifle for the Minigun) no longer withholds it.
		class<Weapon> give = RSLD_Handler.GiveClassFor(slot, toucher);
		if (give && !RSLD_Handler.OwnsGun(toucher, slot, give)) toucher.GiveInventory(give, 1);
		for (let i = Inv; i; i = i.Inv) toucher.GiveInventory(i.GetClass(), 1);
		class<Inventory> unlock = "LD" .. sn .. "_Unlock";
		if (unlock) toucher.GiveInventory(unlock, 1);
		// LegenDoom's pickup screen (EffectScreen: name, icons, description) and its delayed effects (Scrambling)
		class<Inventory> disp = "LD" .. sn .. "LegendaryEffectDisplay";
		if (disp) toucher.GiveInventory(disp, 1);
		toucher.ACS_NamedExecuteAlways("LDWeaponPickupEffectActivation", 0);
		toucher.A_StartSound("misc/w_pkup", CHAN_ITEM);
		if (RSLD.Debug()) Console.Printf("RSLD pickup: %s took legendary %s %s (%s)", toucher.GetClassName(), sn, effect, rarity >= 0 ? RSLD_Data.Rarities[rarity] : "none");
		let hh = RSLD.H();
		if (hh && toucher.player) hh.RefreshSlots(toucher.PlayerNumber(), toucher);
		GoAwayAndDie();
		return true;
	}

	States
	{
	Spawn:
		TNT1 A -1;	// Setup() sets the BD22 gun's sprite/frame; a -1 state never resets it
		Stop;
	}
}

// the effect a LegenDoom pickup carries, and the re-roll of effects the LD mode does not carry yet
class RSLD_Reroll play
{
	static string EffectOf(Actor a, int s)
	{
		if (!a || s < 0) return "";
		string pre = "LD" .. RSLD_Data.Slots[s] .. "Effect_";
		int n = pre.Length();
		for (let i = a.Inv; i; i = i.Inv)
		{
			string c = i.GetClassName();
			if (int(c.Length()) > n && c.Left(n) ~== pre) return c.Mid(n);
		}
		return "";
	}

	static bool Carried(string e)
	{
		let h = RSLD.H();
		return h && h.FindFx(e) != null;
	}

	// keep e if the LD mode carries it (an RSLD_Fx_<e> class exists); else one it carries from LegenDoom's own roll
	// list for that slot and rarity (tables.zs Rolls, parsed from LD<Slot>RandomLegendary). Option rsld_reroll.
	static string Reroll(int s, int r, string e)
	{
		if (Carried(e) || r < 0) return e;
		cvar cv = cvar.FindCvar("rsld_reroll");
		if (cv && !cv.GetBool()) return e;
		Array<string> pool;
		string key = RSLD_Data.Slots[s] .. "|" .. RSLD_Data.Rarities[r] .. "|";
		for (int i = 0; i < RSLD_Tables.Rolls.Size(); i++)
		{
			string row = RSLD_Tables.Rolls[i];
			if (row.Left(key.Length()) != key) continue;
			string eff = row.Mid(key.Length());
			if (Carried(eff)) pool.Push(eff);
		}
		if (pool.Size() == 0) return e;
		string pick = pool[random(0, pool.Size() - 1)];
		if (RSLD.Debug()) Console.Printf("RSLD reroll: %s %s %s -> %s", RSLD_Data.Slots[s], RSLD_Data.Rarities[r], e, pick);
		return pick;
	}
}
