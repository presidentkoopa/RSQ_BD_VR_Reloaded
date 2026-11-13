// LDL x BD22 VR patch: legendary drops.
// LegenDoom 3.0 drops LD<Slot>PickupLegendary; its own randomizer (LD<Slot>RandomLegendary, LegenDoom's balance and
// compat checks) rolls the rarity and the effect into the pickup's inventory within two tics. RSLDP_Converter waits for
// those tokens, then swaps the LegenDoom sprite pickup for RSLDP_LegendaryPickup, which looks like the BD22 VR gun
// (its own spawn sprite, so BD_VoxelPack's voxel when there is one), glows in LegenDoom's rarity effect, carries the
// same tokens, and on touch hands over the BD22 VR gun it shows (unless the player has that gun) plus the tokens.

class RSLDP_Converter : Thinker
{
	Inventory src;
	int slot, tics;
	bool dropped;	// the player's own legendary, let go (never suppressed)

	static void Watch(Inventory ldPickup, int slot, bool dropped = false)
	{
		let c = new("RSLDP_Converter");
		c.src = ldPickup; c.slot = slot; c.tics = 0; c.dropped = dropped;
	}

	override void Tick()
	{
		if (!src || src.Owner) { Destroy(); return; }
		tics++;
		string s = RSLDP_Data.Slots[slot];
		int rarity = -1;
		for (int r = 0; r < 4; r++)
		{
			class<Inventory> rc = "LD" .. s .. "Legendary" .. RSLDP_Data.Rarities[r];
			if (rc && src.CountInv(rc) > 0) rarity = r;
		}
		string eff = RSLDP_Effects.EffectOf(src, slot);
		if ((rarity < 0 || eff == "") && tics < 12) return;	// LegenDoom rolls in 1-2 tics
		vector3 at = src.pos, v = src.vel;
		// Bossfights the only source (handler.zs BossfightOnly): a monster's legendary weapon from outside one drops nothing
		if (!dropped && RSLDP_Handler.BossfightOnly())
		{
			let hb = RSLDP_Handler(EventHandler.Find("RSLDP_Handler"));
			int from = hb ? hb.DropFromBossfight(at) : -1;
			if (from == 0)
			{
				if (RSLDP_Handler.Debug()) Console.Printf("RSLDP drop: %s suppressed (not from a miniboss fight; LegenDoom + Champions + RSQ Miniboss)", src.GetClassName());
				src.Destroy();
				Destroy();
				return;
			}
			if (RSLDP_Handler.Debug()) Console.Printf("RSLDP drop: %s kept (%s)", src.GetClassName(), from == 1 ? "from a miniboss fight" : "no legendary death matched");
		}
		// LegenDoom tossed it from (0,0) + 4 because the monster actor was gone (handler.zs WorldThingDied)
		if (abs(src.pos.x) < 64 && abs(src.pos.y) < 64)
		{
			let h = RSLDP_Handler(EventHandler.Find("RSLDP_Handler"));
			if (h && h.DeathSpot())
			{
				vector3 d = h.spot;
				if (RSLDP_Handler.Debug()) Console.Printf("RSLDP drop: %s was at the map origin (%.0f,%.0f), moved to the legendary's death spot (%.0f,%.0f)", src.GetClassName(), src.pos.x, src.pos.y, d.x, d.y);
				at = d; v = (frandom(-2, 2), frandom(-2, 2), 4);
			}
		}
		let p = RSLDP_LegendaryPickup(Actor.Spawn("RSLDP_LegendaryPickup", at));
		if (p)
		{
			p.vel = v; p.angle = src.angle;
			p.Setup(slot, rarity, eff);
			if (RSLDP_Handler.Debug()) Console.Printf("RSLDP drop: %s -> RSLDP_LegendaryPickup slot %s rarity %s effect %s", src.GetClassName(), s, rarity >= 0 ? RSLDP_Data.Rarities[rarity] : "none", p.effect);
		}
		src.Destroy();
		Destroy();
	}
}

class RSLDP_LegendaryPickup : Inventory
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
		effect = keep ? eff : RSLDP_Effects.Reroll(s, r, eff);
		string sn = RSLDP_Data.Slots[s];
		GiveTok("LD" .. sn .. "EffectActive");
		if (r >= 0) GiveTok("LD" .. sn .. "Legendary" .. RSLDP_Data.Rarities[r]);
		if (effect != "") GiveTok("LD" .. sn .. "Effect_" .. effect);
		look = RSLDP_Handler.GiveClassFor(s, null);
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
		class<Actor> fx = "LDLegendary" .. RSLDP_Data.Rarities[rarity] .. "PickupEffect";
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
		string sn = RSLDP_Data.Slots[slot];
		class<Inventory> active = "LD" .. sn .. "EffectActive";
		if (active && toucher.CountInv(active) > 0)
		{
			// LegenDoom: one legendary per weapon; it shows the name and leaves the pickup ($LD_WEP_PICKUP_NAME_FAIL_<slot>)
			class<Inventory> cd = (class<Inventory>)(RSLDP_Data.AC("LDWeaponDisplayCooldown"));
			if (!cd || toucher.CountInv(cd) == 0)
			{
				if (cd) toucher.GiveInventory(cd, 1);
				toucher.A_Print(StringTable.Localize("$LD_WEP_PICKUP_NAME_FAIL_" .. sn), 2, "CONFONT");
			}
			return false;
		}
		// the gun it shows, unless the player has that gun already (or its Purist/Dual copy); the power then works on
		// every gun of the slot's family. Owning only a stand-in (the Rifle for the Minigun) no longer withholds it.
		class<Weapon> give = RSLDP_Handler.GiveClassFor(slot, toucher);
		if (give && !RSLDP_Handler.OwnsGun(toucher, slot, give)) toucher.GiveInventory(give, 1);
		for (let i = Inv; i; i = i.Inv) toucher.GiveInventory(i.GetClass(), 1);
		class<Inventory> unlock = "LD" .. sn .. "_Unlock";
		if (unlock) toucher.GiveInventory(unlock, 1);
		// LegenDoom's pickup screen (EffectScreen: name, icons, description) and its delayed effects (Scrambling)
		class<Inventory> disp = "LD" .. sn .. "LegendaryEffectDisplay";
		if (disp) toucher.GiveInventory(disp, 1);
		toucher.ACS_NamedExecuteAlways("LDWeaponPickupEffectActivation", 0);
		toucher.A_StartSound("misc/w_pkup", CHAN_ITEM);
		if (RSLDP_Handler.Debug()) Console.Printf("RSLDP pickup: %s took legendary %s %s (%s)", toucher.GetClassName(), sn, effect, rarity >= 0 ? RSLDP_Data.Rarities[rarity] : "none");
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
