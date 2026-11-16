// 2.0.4y: THE BOSS KIOSK'S LEGENDARIES (RSQ UBQ Series design/KIOSK.md, owner 2026-11-16 04:47-04:52).
// A Boss win in the RSQ UBQ Series (RSQ Miniboss) can drop a kiosk in place of the Boss's one legendary weapon. The kiosk
// offers legendaries rolled HERE, the way the Boss's single drop is rolled (RSLD_Reroll.TierRarity at the fight's tier, an
// effect LegenDoom rolls at that rarity on that slot that the LD mode carries: RSLD_Reroll.PickAt), and a bought one is
// made HERE as the real legendary (RSLD_LegendaryPickup, the same pickup the Boss drops). Asked by name, nothing links:
//
//   ServiceIterator.Find("RSLD_KioskService") -> the class name checked
//   GetInt("ready")                          1 when the LD mode is on (LegenDoom 3.0 loaded), else 0
//   GetString("roll", "", n, tier)           n offers (1..6) at a Boss of that tier (1 = the first tier, as RSLD_Handler
//                                            counts it: RSQ Miniboss's tier + 1), on n different slots (melee left out):
//                                            "slot|rarity|effect;slot|rarity|effect;..." ("" none). rarity 0 Common ..
//                                            3 Epic (RSLD_Data.Rarities), effect a LegenDoom effect name
//   GetString("raise", "<offer>")            the offer one rarity step up, with an effect LegenDoom rolls at the new
//                                            rarity on that slot (the same one when it rolls there too); "" at Epic or none
//   GetString("gun", "<offer>")              the gun's name (LegenDoom's LD_WEP_NAME_<Slot>), upper case
//   GetString("rarity", "<offer>")           COMMON / UNCOMMON / RARE / EPIC
//   GetString("effect", "<offer>")           the effect's title (LegenDoom's LD_FX_TITLE_<Effect>), upper case
//   GetString("desc", "<offer>")             the first line of its description (LD_FX_DESCR_<Effect>, colour codes out)
//   GetString("class", "<offer>")            the BD22 VR gun the pickup shows and hands over (its class name)
//   GetString("yours", "<offer>", 0, 0, player)  what the player holds on that slot, for the compare card:
//                                            "<rarity>|<effect title>|<owns the gun 0/1>" (rarity -1 and "" when he has no
//                                            legendary on that slot)
//   GetInt("give", "<offer>", 0, 0, player)  makes the real legendary pickup at the player and hands it over: 1 taken,
//                                            2 left lying there (he already carries a legendary of that slot: LegenDoom's
//                                            one per slot; it stays for later), 0 could not be made
//   GetInt("kiosk.take", "", 0, 0, boss)     RSQ Miniboss: this Boss's death drops a kiosk, so its one legendary weapon
//                                            drop (RSLD_Converter, the miniboss's) is not made. Remembered for 105 tics
//                                            within 256 units of where it died. Only this call suppresses anything;
//                                            without it every drop is as before.
// rsld_debug 1 logs every roll, raise, give and suppressed drop ("RSLD kiosk: ...").
class RSLD_KioskService : Service
{
	static play int SlotOf(string offer, out int r, out string e)
	{
		Array<string> f; offer.Split(f, "|");
		r = -1; e = "";
		if (f.Size() < 3) return -1;
		int s = f[0].ToInt();
		r = f[1].ToInt();
		e = f[2];
		if (s < 0 || s > 8 || r < 0 || r > 3) return -1;
		return s;
	}

	static play string Roll(int n, int tier)
	{
		if (!RSLD.On()) return "";
		n = clamp(n, 1, 6);
		Array<int> slots;
		for (int s = 1; s <= 8; s++) slots.Push(s);	// every gun's slot; melee (LDFists) is not sold
		string res = "";
		int made = 0;
		while (made < n && slots.Size() > 0)
		{
			int k = random(0, slots.Size() - 1);
			int s = slots[k];
			slots.Delete(k);
			int r = RSLD_Reroll.TierRarity(tier, true);
			string e = RSLD_Reroll.PickAt(s, r);
			// nothing the LD mode carries at that rarity on that slot: the nearest rarity below, then above, that has one
			for (int d = 1; e == "" && d < 4; d++)
			{
				if (r - d >= 0) { e = RSLD_Reroll.PickAt(s, r - d); if (e != "") { r -= d; break; } }
				if (r + d <= 3) { e = RSLD_Reroll.PickAt(s, r + d); if (e != "") { r += d; break; } }
			}
			if (e == "") continue;
			res = res .. (made ? ";" : "") .. String.Format("%d|%d|%s", s, r, e);
			made++;
		}
		if (RSLD.Debug()) Console.Printf("RSLD kiosk: rolled %d offer(s) at tier %d: %s", made, tier, res);
		return res;
	}

	static play string Raise(string offer)
	{
		int r; string e;
		int s = SlotOf(offer, r, e);
		if (s < 0 || r >= 3) return "";
		int nr = r + 1;
		// the same effect when LegenDoom rolls it at the new rarity on this slot, else one it does
		bool keeps = false;
		string key = RSLD_Data.Slots[s] .. "|" .. RSLD_Data.Rarities[nr] .. "|" .. e;
		for (int i = 0; i < RSLD_Tables.Rolls.Size() && !keeps; i++) if (RSLD_Tables.Rolls[i] ~== key) keeps = true;
		string ne = keeps ? e : RSLD_Reroll.PickAt(s, nr);
		if (ne == "") return "";
		string res = String.Format("%d|%d|%s", s, nr, ne);
		if (RSLD.Debug()) Console.Printf("RSLD kiosk: raised %s -> %s", offer, res);
		return res;
	}

	static play string Clean(string t)
	{
		// LegenDoom's descriptions carry \c colour codes (the escape byte 28 and one letter, or [name]) and line breaks
		string o = "";
		int i = 0, l = t.Length();
		while (i < l)
		{
			int c = t.ByteAt(i);
			if (c == 28)
			{
				i++;
				if (i < l && t.ByteAt(i) == 91) { while (i < l && t.ByteAt(i) != 93) i++; }
				i++;
				continue;
			}
			if (c == 10) break;
			o.AppendCharacter(c);
			i++;
		}
		return o;
	}

	static play string Text(string what, string offer)
	{
		int r; string e;
		int s = SlotOf(offer, r, e);
		if (s < 0) return "";
		string sn = RSLD_Data.Slots[s];
		if (what ~== "gun") { string g = StringTable.Localize("$LD_WEP_NAME_" .. sn); g = g.MakeUpper(); return g; }
		if (what ~== "rarity") { string rr = RSLD_Data.Rarities[r]; rr = rr.MakeUpper(); return rr; }
		if (what ~== "effect")
		{
			string k = "LD_FX_TITLE_" .. e;
			string t = StringTable.Localize("$" .. k);
			if (t == k || t == "$" .. k || t == "") t = e;
			t = t.MakeUpper();
			return t;
		}
		if (what ~== "desc")
		{
			string k = "LD_FX_DESCR_" .. e;
			string t = StringTable.Localize("$" .. k);
			if (t == k || t == "$" .. k) return "";
			t = Clean(t);
			t = t.MakeUpper();
			return t;
		}
		if (what ~== "class")
		{
			class<Weapon> c = RSLD_Handler.GiveClassFor(s, null);
			if (!c) return "";
			string cn = c.GetClassName();
			return cn;
		}
		return "";
	}

	// the real legendary, made at the player and offered to him the way touching it would
	static play int Give(string offer, Actor who)
	{
		if (!RSLD.On() || !who || !who.player) return 0;
		int r; string e;
		int s = SlotOf(offer, r, e);
		if (s < 0) return 0;
		let p = RSLD_LegendaryPickup(Actor.Spawn("RSLD_LegendaryPickup", who.pos + (0, 0, 8)));
		if (!p) return 0;
		p.angle = who.angle;
		p.Setup(s, r, e, true);
		bool ok; Actor dummy;
		[ok, dummy] = p.CallTryPickup(who);
		if (RSLD.Debug()) Console.Printf("RSLD kiosk: gave %s %s %s to player %d: %s", RSLD_Data.Slots[s], RSLD_Data.Rarities[r], e,
			who.PlayerNumber(), ok ? "taken" : "left lying (he carries a legendary of that slot)");
		if (ok) return 1;
		// left lying: it waits a moment before it can be touched (not taken straight back when he steps off)
		if (p && !p.bDestroyed) { p.pickupDelay = 35; p.bSPECIAL = false; }
		return 2;
	}

	override int GetInt(String request, String stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{
		if (request ~== "ready") return RSLD.On() ? 1 : 0;
		if (request ~== "give") return Give(stringArg, Actor(objectArg));
		if (request ~== "kiosk.take")
		{
			let a = Actor(objectArg);
			let h = RSLD.H();
			if (!a || !h) return 0;
			h.kioskX.Push(a.pos.x); h.kioskY.Push(a.pos.y); h.kioskT.Push(level.maptime);
			if (RSLD.Debug()) Console.Printf("RSLD kiosk: %s's legendary drop is the kiosk's (%.0f %.0f, t%d)", a.GetClassName(), a.pos.x, a.pos.y, level.maptime);
			return 1;
		}
		return -1;
	}
	static play string Yours(string offer, Actor who)
	{
		int r; string e;
		int s = SlotOf(offer, r, e);
		if (s < 0 || !who) return "";
		string sn = RSLD_Data.Slots[s];
		int hr = -1;
		for (int k = 0; k < 4; k++)
		{
			class<Inventory> rc = "LD" .. sn .. "Legendary" .. RSLD_Data.Rarities[k];
			if (rc && who.CountInv(rc) > 0) hr = k;
		}
		string he = RSLD_Reroll.EffectOf(who, s);
		string title = "";
		if (he != "")
		{
			string k2 = "LD_FX_TITLE_" .. he;
			title = StringTable.Localize("$" .. k2);
			if (title == k2 || title == "$" .. k2 || title == "") title = he;
			title = title.MakeUpper();
		}
		class<Weapon> g = RSLD_Handler.GiveClassFor(s, who);
		return String.Format("%d|%s|%d", he == "" ? -1 : hr, title, RSLD_Handler.OwnsGun(who, s, g) ? 1 : 0);
	}

	override String GetString(String request, String stringArg, int intArg, double doubleArg, Object objectArg, Name nameArg)
	{
		if (request ~== "roll") return Roll(intArg, int(doubleArg));
		if (request ~== "yours") return Yours(stringArg, Actor(objectArg));
		if (request ~== "raise") return Raise(stringArg);
		return Text(request, stringArg);
	}
}

extend class RSLD_Handler
{
	Array<double> kioskX, kioskY;	// 2.0.4y: Boss deaths whose legendary drop a kiosk takes (RSLD_KioskService "kiosk.take")
	Array<int> kioskT;
	double dropX, dropY;		// the death DropFromBossfight matched last

	// a kiosk took this drop (one record each, used up)
	bool KioskTook(double x, double y)
	{
		for (int i = kioskT.Size() - 1; i >= 0; i--)
		{
			if (level.maptime - kioskT[i] > 105) { kioskX.Delete(i); kioskY.Delete(i); kioskT.Delete(i); continue; }
			double dx = kioskX[i] - x, dy = kioskY[i] - y;
			if (dx * dx + dy * dy > 256.0 * 256.0) continue;
			kioskX.Delete(i); kioskY.Delete(i); kioskT.Delete(i);
			return true;
		}
		return false;
	}
}
